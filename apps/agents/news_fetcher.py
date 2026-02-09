"""
News Fetcher for Sentiment Agent
Supabase-first strategy with scraper fallback for companies not yet in the database.
Handles async/sync bridge via ThreadPoolExecutor for Playwright-based scrapers.
"""

import asyncio
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scraping.news.schemas import NewsArticle
from scraping.news.supabase_client import (
    get_articles_by_company,
    store_articles,
    test_connection,
)
from scraping.news.theedge_scraper import TheEdgeScraper
from scraping.news.bernama_scraper import BernamaScraper
from etl.logging_config import get_logger

logger = get_logger(__name__)


def _parse_supabase_articles(raw_articles: List[dict]) -> List[NewsArticle]:
    """Parse raw Supabase dicts back into NewsArticle objects"""
    articles = []
    for raw in raw_articles:
        try:
            article = NewsArticle(
                article_id=raw.get("article_id", ""),
                source=raw.get("source", ""),
                title=raw.get("title", ""),
                content=raw.get("content", ""),
                summary=raw.get("summary"),
                url=raw.get("url", ""),
                published_date=raw.get("published_date"),
                author=raw.get("author"),
                category=raw.get("category", ""),
                companies_mentioned=raw.get("companies_mentioned", []),
                tickers_mentioned=raw.get("tickers_mentioned", []),
                keywords=raw.get("keywords", []),
            )
            articles.append(article)
        except Exception as e:
            logger.warning(f"Failed to parse Supabase article: {e}")
            continue
    return articles


def _scrape_articles_sync(company: str, max_per_source: int = 10) -> List[NewsArticle]:
    """
    Scrape articles synchronously in its own event loop.
    Called from within a ThreadPoolExecutor to avoid nested loop issues.

    Args:
        company: Company name to search for
        max_per_source: Max articles per source

    Returns:
        List of scraped NewsArticle objects, stored to Supabase
    """
    try:
        logger.info(f"[news_fetcher] Scraping articles for '{company}'")

        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            all_articles = loop.run_until_complete(
                _run_scrapers_async(company, max_per_source)
            )

            # Store to Supabase for future cache hits
            if all_articles:
                try:
                    stored = store_articles(all_articles)
                    logger.info(f"[news_fetcher] Stored {stored}/{len(all_articles)} articles in Supabase")
                except Exception as e:
                    logger.warning(f"[news_fetcher] Failed to store scraped articles: {e}")

            return all_articles
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"[news_fetcher] Scraping error: {e}")
        return []


async def _run_scrapers_async(company: str, max_per_source: int) -> List[NewsArticle]:
    """
    Run both scrapers concurrently (async).
    """
    all_articles = []

    # TheEdge scraper
    try:
        scraper = TheEdgeScraper()
        await scraper.start()
        try:
            articles = await scraper.search_company(
                company=company,
                max_results=max_per_source
            )
            all_articles.extend(articles)
            logger.info(f"[news_fetcher] TheEdge: scraped {len(articles)} articles")
        finally:
            try:
                await scraper.stop()
            except:
                pass
    except Exception as e:
        logger.warning(f"[news_fetcher] TheEdge scraper error: {e}")

    # Bernama scraper
    try:
        scraper = BernamaScraper()
        await scraper.start()
        try:
            articles = await scraper.search_company(
                company=company,
                max_results=max_per_source
            )
            all_articles.extend(articles)
            logger.info(f"[news_fetcher] Bernama: scraped {len(articles)} articles")
        finally:
            try:
                await scraper.stop()
            except:
                pass
    except Exception as e:
        logger.warning(f"[news_fetcher] Bernama scraper error: {e}")

    return all_articles


def fetch_news_for_company(
    company_name: Optional[str],
    limit: int = 10,
    scrape_timeout_seconds: int = 60
) -> List[NewsArticle]:
    """
    Fetch news articles for a company.

    Strategy:
    1. Try Supabase (cached, <1s) — returns immediately if found
    2. Fallback to scraping (10-30s) — if DB empty or connection fails
    3. Timeout after scrape_timeout_seconds

    Args:
        company_name: Company name to fetch news for (if None, returns empty list)
        limit: Max articles to return
        scrape_timeout_seconds: Max time to spend scraping (default 60s)

    Returns:
        List of NewsArticle objects
    """
    if not company_name:
        logger.debug("[news_fetcher] No company name provided, returning empty list")
        return []

    logger.info(f"[news_fetcher] Fetching news for '{company_name}'")

    # Step 1: Try Supabase (fast path)
    try:
        raw_articles = get_articles_by_company(company_name, limit=limit)
        if raw_articles:
            articles = _parse_supabase_articles(raw_articles)
            logger.info(f"[news_fetcher] Found {len(articles)} articles in Supabase cache")
            return articles
    except Exception as e:
        logger.warning(f"[news_fetcher] Supabase query error: {e}")

    # Step 2: Fallback to scraping (slow path, with timeout)
    logger.info(f"[news_fetcher] Supabase cache miss, attempting to scrape...")

    try:
        # Use ThreadPoolExecutor to avoid event loop conflicts
        # (supervisor is sync, scrapers are async, FastAPI owns the loop)
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _scrape_articles_sync,
                company_name,
                limit
            )

            try:
                articles = future.result(timeout=scrape_timeout_seconds)
                logger.info(f"[news_fetcher] Scraped {len(articles)} articles for '{company_name}'")
                if articles:
                    return articles
            except FuturesTimeoutError:
                logger.warning(f"[news_fetcher] Scraping timeout after {scrape_timeout_seconds}s for '{company_name}'")

            # Scraping returned 0 or timed out — articles may have been stored during scraping,
            # so re-check Supabase cache
            try:
                raw_articles = get_articles_by_company(company_name, limit=limit)
                if raw_articles:
                    articles = _parse_supabase_articles(raw_articles)
                    logger.info(f"[news_fetcher] Post-scrape cache hit: {len(articles)} articles for '{company_name}'")
                    return articles
            except Exception as cache_err:
                logger.warning(f"[news_fetcher] Post-scrape cache read failed: {cache_err}")

            return []
    except Exception as e:
        logger.error(f"[news_fetcher] Scraping exception: {e}")
        return []
