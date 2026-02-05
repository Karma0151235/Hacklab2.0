"""
Supabase client for news articles storage using postgrest directly
"""

import os
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from postgrest import SyncPostgrestClient
from scraping.news.schemas import NewsArticle
from etl.logging_config import get_logger

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__name__)


def get_supabase_client() -> Optional[SyncPostgrestClient]:
    """Get Postgrest client from environment variables"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        logger.warning("SUPABASE_URL or SUPABASE_KEY not set")
        return None
    
    # Postgrest endpoint is at /rest/v1
    postgrest_url = f"{url.rstrip('/')}/rest/v1"
    
    client = SyncPostgrestClient(postgrest_url)
    # Set authorization header
    client.session.headers.update({
        "apikey": key,
        "Authorization": f"Bearer {key}"
    })
    return client


def test_connection() -> bool:
    """Test if Supabase connection is active"""
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        # Simple query to test connection
        result = client.from_("news_articles").select("id").limit(1).execute()
        logger.info("✅ Supabase connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Supabase connection test failed: {e}")
        return False


def store_articles(articles: List[NewsArticle]) -> int:
    """
    Store articles in Supabase.
    Returns count of successfully stored articles.
    """
    client = get_supabase_client()
    if not client:
        logger.error("Cannot store articles: Supabase client not available")
        return 0
    
    stored_count = 0
    
    for article in articles:
        try:
            # Convert article to dict for Supabase
            data = {
                "article_id": article.article_id,
                "source": article.source,
                "title": article.title,
                "content": article.content,
                "summary": article.summary,
                "url": article.url,
                "published_date": article.published_date.isoformat() if article.published_date else None,
                "category": article.category,
                "companies_mentioned": article.companies_mentioned,
                "keywords": article.keywords,
                # sentiment_score and sentiment_label left null for later analysis
            }
            
            # Upsert to handle duplicates
            result = client.from_("news_articles").upsert(data).execute()
            
            stored_count += 1
            logger.debug(f"Stored article: {article.article_id}")
            
        except Exception as e:
            logger.error(f"Failed to store article {article.article_id}: {e}")
            continue
    
    logger.info(f"Stored {stored_count}/{len(articles)} articles in Supabase")
    return stored_count


def get_articles_by_company(company: str, limit: int = 10) -> List[dict]:
    """Get articles mentioning a specific company"""
    client = get_supabase_client()
    if not client:
        return []

    normalized = company.strip()
    if not normalized:
        return []

    normalized_upper = normalized.upper()
    like_pattern = f"*{normalized}*"

    or_filter = (
        f"companies_mentioned.cs.{{{normalized}}},"
        f"companies_mentioned.cs.{{{normalized_upper}}},"
        f"content.ilike.{like_pattern},"
        f"title.ilike.{like_pattern}"
    )

    result = (
        client.from_("news_articles")
        .select("*")
        .or_(or_filter)
        .order("published_date", desc=True)
        .limit(limit)
        .execute()
    )
    
    return result.data if result.data else []


def get_recent_articles(source: Optional[str] = None, limit: int = 20) -> List[dict]:
    """Get recent articles, optionally filtered by source"""
    client = get_supabase_client()
    if not client:
        return []
    
    query = client.from_("news_articles").select("*")
    
    if source:
        query = query.eq("source", source)
    
    result = query.order("published_date", desc=True).limit(limit).execute()
    
    return result.data if result.data else []


def get_articles_without_sentiment(limit: int = 50) -> List[dict]:
    """Get articles that haven't been analyzed for sentiment yet"""
    client = get_supabase_client()
    if not client:
        return []
    
    result = client.from_("news_articles")\
        .select("*")\
        .is_("sentiment_score", "null")\
        .order("published_date", desc=True)\
        .limit(limit)\
        .execute()
    
    return result.data if result.data else []


def update_article_sentiment(article_id: str, score: float, label: str) -> bool:
    """Update an article with sentiment analysis results"""
    client = get_supabase_client()
    if not client:
        return False
    
    try:
        client.from_("news_articles")\
            .update({
                "sentiment_score": score,
                "sentiment_label": label,
                "updated_at": "now()"
            })\
            .eq("article_id", article_id)\
            .execute()
        return True
    except Exception as e:
        logger.error(f"Failed to update sentiment for {article_id}: {e}")
        return False
