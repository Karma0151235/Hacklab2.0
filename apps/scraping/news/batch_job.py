"""
Scheduled batch job for news scraping.
Run this script periodically (e.g., every 6 hours) using cron, Windows Task Scheduler,
or a job scheduler like APScheduler.

Usage:
    uv run python -m scraping.news.batch_job

Or configure in your scheduler to run:
    cd apps && uv run python -m scraping.news.batch_job
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add apps directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scraping.news import TheEdgeScraper, BernamaScraper
from etl.logging_config import get_logger

logger = get_logger(__name__)


# Configuration
DEFAULT_MAX_ARTICLES = int(os.getenv("NEWS_BATCH_MAX_ARTICLES", "30"))
DEFAULT_SOURCES = os.getenv("NEWS_BATCH_SOURCES", "theedge,bernama").split(",")

# Company filters for Malaysian market
COMPANY_FILTERS = os.getenv("NEWS_COMPANY_FILTERS", "").split(",") if os.getenv("NEWS_COMPANY_FILTERS") else None


async def run_batch_scraping():
    """
    Run batch scraping for all configured news sources.
    """
    logger.info("=" * 60)
    logger.info("Starting news batch scraping job")
    logger.info(f"Time: {datetime.utcnow().isoformat()}")
    logger.info(f"Sources: {DEFAULT_SOURCES}")
    logger.info(f"Max articles per source: {DEFAULT_MAX_ARTICLES}")
    logger.info(f"Company filters: {COMPANY_FILTERS}")
    logger.info("=" * 60)
    
    total_articles = 0
    results = []
    
    for source in DEFAULT_SOURCES:
        source = source.strip().lower()
        
        if source == "theedge":
            logger.info("[TheEdge] Starting scrape...")
            try:
                async with TheEdgeScraper(headless=True) as scraper:
                    result = await scraper.scrape_batch(
                        max_articles=DEFAULT_MAX_ARTICLES,
                        company_filters=COMPANY_FILTERS
                    )
                    results.append(result)
                    total_articles += result.total_scraped
                    logger.info(f"[TheEdge] Scraped {result.total_scraped} articles")
                    if result.errors:
                        logger.warning(f"[TheEdge] Errors: {result.errors[:5]}")
            except Exception as e:
                logger.error(f"[TheEdge] Failed: {str(e)}")
                
        elif source == "bernama":
            logger.info("[Bernama] Starting scrape...")
            try:
                async with BernamaScraper(headless=True) as scraper:
                    result = await scraper.scrape_batch(
                        max_articles=DEFAULT_MAX_ARTICLES,
                        company_filters=COMPANY_FILTERS
                    )
                    results.append(result)
                    total_articles += result.total_scraped
                    logger.info(f"[Bernama] Scraped {result.total_scraped} articles")
                    if result.errors:
                        logger.warning(f"[Bernama] Errors: {result.errors[:5]}")
            except Exception as e:
                logger.error(f"[Bernama] Failed: {str(e)}")
        else:
            logger.warning(f"Unknown source: {source}")
    
    logger.info("=" * 60)
    logger.info(f"Batch scraping completed")
    logger.info(f"Total articles scraped: {total_articles}")
    logger.info("=" * 60)
    
    # Collect all articles
    all_articles = []
    for result in results:
        all_articles.extend(result.articles)
    
    # Save to JSON file (backup)
    output_dir = Path(__file__).parent.parent.parent / "storage" / "news"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    
    import json
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump([article.dict() for article in all_articles], f, indent=2, default=str)
    
    logger.info(f"Saved {len(all_articles)} articles to {output_file}")
    
    # Store in Supabase
    if all_articles:
        try:
            from scraping.news.supabase_client import store_articles, test_connection
            
            # Test connection first
            if not test_connection():
                logger.warning("Supabase connection test failed - skipping storage")
            else:
                stored = store_articles(all_articles)
                logger.info(f"Stored {stored} articles in Supabase")
        except Exception as e:
            logger.error(f"Failed to store in Supabase: {e}")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_batch_scraping())
