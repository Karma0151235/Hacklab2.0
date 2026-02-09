"""
Company-specific news search CLI
Searches for news articles about a specific company

Usage:
    uv run python -m scraping.news.search_company --company "MAYBANK" --max 20
    uv run python -m scraping.news.search_company --company "CIMB" --source theedge --from 2024-01-01
"""

import sys
import argparse
import asyncio
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scraping.news.theedge_scraper import TheEdgeScraper
from scraping.news.bernama_scraper import BernamaScraper
from scraping.news.supabase_client import store_articles, test_connection
from etl.logging_config import get_logger

logger = get_logger(__name__)


def save_articles_to_json(articles, filename):
    """Save articles to JSON file"""
    storage_dir = Path(__file__).parent.parent.parent / "storage" / "news"
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = storage_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump([article.dict() for article in articles], f, indent=2, default=str, ensure_ascii=False)
    
    return filepath


async def search_company_news(
    company: str,
    sources: list = None,
    start_date: str = "2025-01-01",
    end_date: str = None,
    max_per_source: int = 20
):
    """
    Search for company-specific news across sources
    
    Args:
        company: Company name to search for (e.g., "MAYBANK", "CIMB")
        sources: List of sources to search (default: ["theedge", "bernama"])
        start_date: Start date in YYYY-MM-DD format (The Edge only)
        end_date: End date in YYYY-MM-DD format (The Edge only, defaults to today)
        max_per_source: Maximum articles per source
    """
    if sources is None:
        sources = ["theedge", "bernama"]
    
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    all_articles = []
    
    logger.info("=" * 60)
    logger.info(f"COMPANY NEWS SEARCH: {company}")
    logger.info(f"Sources: {', '.join(sources)}")
    logger.info(f"Max per source: {max_per_source}")
    logger.info("=" * 60)
    
    # The Edge
    if "theedge" in sources:
        logger.info("\n[TheEdge] Starting company search...")
        scraper = TheEdgeScraper()
        try:
            await scraper.start()
            articles = await scraper.search_company(
                company=company,
                start_date=start_date,
                end_date=end_date,
                max_results=max_per_source
            )
            
            # Manually ensure the searched company is in companies_mentioned
            for article in articles:
                if company not in article.companies_mentioned:
                    article.companies_mentioned.append(company)
            
            all_articles.extend(articles)
            logger.info(f"[TheEdge] Found {len(articles)} articles")
        except Exception as e:
            logger.error(f"[TheEdge] Error: {e}")
        finally:
            try:
                await scraper.close()
            except:
                pass
    
    # Bernama
    if "bernama" in sources:
        logger.info("\n[Bernama] Starting company search...")
        scraper = BernamaScraper()
        try:
            await scraper.start()
            articles = await scraper.search_company(
                company=company,
                max_results=max_per_source
            )
            
            # Manually ensure the searched company is in companies_mentioned
            for article in articles:
                if company not in article.companies_mentioned:
                    article.companies_mentioned.append(company)
            
            all_articles.extend(articles)
            logger.info(f"[Bernama] Found {len(articles)} articles")
        except Exception as e:
            logger.error(f"[Bernama] Error: {e}")
        finally:
            try:
                await scraper.close()
            except:
                pass
    
    # Save results
    if all_articles:
        logger.info(f"\n{'=' * 60}")
        logger.info(f"TOTAL: {len(all_articles)} articles found")
        logger.info(f"{'=' * 60}")
        
        # Save to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = save_articles_to_json(
            all_articles,
            filename=f"company_{company.lower().replace(' ', '_')}_{timestamp}.json"
        )
        logger.info(f"\n✅ Saved to: {json_file}")
        
        # Store in Supabase
        if test_connection():
            stored = store_articles(all_articles)
            logger.info(f"✅ Stored {stored} articles in Supabase")
        else:
            logger.warning("⚠️  Supabase connection failed - skipping storage")
    else:
        logger.warning(f"\n⚠️  No articles found for '{company}'")
    
    return all_articles


def main():
    parser = argparse.ArgumentParser(
        description="Search for news articles about a specific company"
    )
    parser.add_argument(
        "--company",
        required=True,
        help="Company name to search for (e.g., 'MAYBANK', 'CIMB')"
    )
    parser.add_argument(
        "--source",
        nargs="+",
        choices=["theedge", "bernama"],
        default=["theedge", "bernama"],
        help="News sources to search (default: both)"
    )
    parser.add_argument(
        "--from",
        dest="start_date",
        default="2024-01-01",
        help="Start date in YYYY-MM-DD format (The Edge only, default: 2024-01-01)"
    )
    parser.add_argument(
        "--to",
        dest="end_date",
        default=None,
        help="End date in YYYY-MM-DD format (The Edge only, default: today)"
    )
    parser.add_argument(
        "--max",
        dest="max_results",
        type=int,
        default=20,
        help="Maximum articles per source (default: 20)"
    )
    
    args = parser.parse_args()
    
    # Run the search
    asyncio.run(search_company_news(
        company=args.company,
        sources=args.source,
        start_date=args.start_date,
        end_date=args.end_date,
        max_per_source=args.max_results
    ))


if __name__ == "__main__":
    main()
