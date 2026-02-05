"""
News Scraping and Sentiment Analysis API Routes
"""

import asyncio
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from scraping.news import TheEdgeScraper, BernamaScraper, NewsArticle, NewsBatchResult
from agents.sentiment_agent import SentimentAgent, SentimentAgentInput, SentimentAgentOutput
from etl.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/news", tags=["news"])


# ============================================================================
# Request/Response Models
# ============================================================================

class NewsScrapeRequest(BaseModel):
    """Request to scrape news from sources"""
    sources: List[str] = Field(
        default=["theedge", "bernama"],
        description="News sources to scrape: theedge, bernama"
    )
    max_articles_per_source: int = Field(default=20, ge=1, le=100)
    company_filters: Optional[List[str]] = Field(
        default=None,
        description="Optional company names to filter news"
    )


class NewsScrapeResponse(BaseModel):
    """Response from news scraping"""
    status: str
    message: str
    job_id: Optional[str] = None
    results: Optional[List[NewsBatchResult]] = None


class SentimentRequest(BaseModel):
    """Request for sentiment analysis"""
    query: str = Field(..., description="Query for sentiment analysis")
    company_name: Optional[str] = Field(default=None, description="Company to focus on")
    articles: Optional[List[NewsArticle]] = Field(
        default=None,
        description="Articles to analyze (if not provided, uses recent scraped articles)"
    )


class SentimentResponse(BaseModel):
    """Response from sentiment analysis"""
    status: str
    sentiment: SentimentAgentOutput


# ============================================================================
# In-memory storage for scraped articles (replace with DB in production)
# ============================================================================

_scraped_articles: List[NewsArticle] = []
_scrape_jobs: dict = {}


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/scrape", response_model=NewsScrapeResponse)
async def scrape_news(
    request: NewsScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger news scraping from specified sources.
    
    This initiates a background scraping job and returns immediately.
    """
    job_id = f"news_scrape_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    # Start scraping in background
    background_tasks.add_task(
        _run_scraping_job,
        job_id,
        request.sources,
        request.max_articles_per_source,
        request.company_filters
    )
    
    return NewsScrapeResponse(
        status="started",
        message=f"Scraping job started for sources: {', '.join(request.sources)}",
        job_id=job_id
    )


@router.post("/scrape/sync", response_model=NewsScrapeResponse)
async def scrape_news_sync(request: NewsScrapeRequest):
    """
    Scrape news synchronously (waits for completion).
    
    Use this for smaller scraping jobs where you need immediate results.
    """
    try:
        results = []
        
        for source in request.sources:
            if source == "theedge":
                async with TheEdgeScraper(headless=True) as scraper:
                    result = await scraper.scrape_batch(
                        max_articles=request.max_articles_per_source,
                        company_filters=request.company_filters
                    )
                    results.append(result)
                    _scraped_articles.extend(result.articles)
                    
            elif source == "bernama":
                async with BernamaScraper(headless=True) as scraper:
                    result = await scraper.scrape_batch(
                        max_articles=request.max_articles_per_source,
                        company_filters=request.company_filters
                    )
                    results.append(result)
                    _scraped_articles.extend(result.articles)
        
        total_articles = sum(r.total_scraped for r in results)
        
        return NewsScrapeResponse(
            status="completed",
            message=f"Scraped {total_articles} articles from {len(request.sources)} sources",
            results=results
        )
        
    except Exception as e:
        logger.error(f"News scraping error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles", response_model=List[NewsArticle])
async def get_scraped_articles(
    source: Optional[str] = None,
    company: Optional[str] = None,
    limit: int = 50
):
    """
    Get recently scraped articles with optional filters.
    """
    articles = _scraped_articles.copy()
    
    if source:
        articles = [a for a in articles if a.source == source]
    
    if company:
        company_lower = company.lower()
        articles = [
            a for a in articles 
            if company_lower in a.title.lower() or 
               company_lower in a.content.lower() or
               any(company_lower in c.lower() for c in a.companies_mentioned)
        ]
    
    return articles[:limit]


@router.post("/sentiment", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest):
    """
    Analyze sentiment of news articles.
    
    If no articles are provided, uses recently scraped articles.
    """
    try:
        agent = SentimentAgent()
        
        # Use provided articles or recent scraped articles
        articles = request.articles or _scraped_articles[-20:]
        
        if not articles:
            return SentimentResponse(
                status="no_data",
                sentiment=SentimentAgentOutput(
                    overall_sentiment="neutral",
                    sentiment_score=0.0,
                    confidence=0.0,
                    summary="No articles available for analysis. Please scrape news first."
                )
            )
        
        # Run sentiment analysis
        input_data = SentimentAgentInput(
            query=request.query,
            company_name=request.company_name,
            news_articles=articles
        )
        
        result = agent.analyze(input_data)
        
        return SentimentResponse(
            status="success",
            sentiment=result
        )
        
    except Exception as e:
        logger.error(f"Sentiment analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}")
async def get_scrape_job_status(job_id: str):
    """
    Get status of a background scraping job.
    """
    if job_id not in _scrape_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return _scrape_jobs[job_id]


# ============================================================================
# Background Job Runner
# ============================================================================

async def _run_scraping_job(
    job_id: str,
    sources: List[str],
    max_articles: int,
    company_filters: Optional[List[str]]
):
    """Run scraping job in background"""
    _scrape_jobs[job_id] = {
        "status": "running",
        "started_at": datetime.utcnow().isoformat(),
        "sources": sources,
        "articles_scraped": 0
    }
    
    try:
        total_articles = 0
        
        for source in sources:
            if source == "theedge":
                async with TheEdgeScraper(headless=True) as scraper:
                    result = await scraper.scrape_batch(
                        max_articles=max_articles,
                        company_filters=company_filters
                    )
                    _scraped_articles.extend(result.articles)
                    total_articles += result.total_scraped
                    
            elif source == "bernama":
                async with BernamaScraper(headless=True) as scraper:
                    result = await scraper.scrape_batch(
                        max_articles=max_articles,
                        company_filters=company_filters
                    )
                    _scraped_articles.extend(result.articles)
                    total_articles += result.total_scraped
            
            _scrape_jobs[job_id]["articles_scraped"] = total_articles
        
        _scrape_jobs[job_id].update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "articles_scraped": total_articles
        })
        
    except Exception as e:
        logger.error(f"Background scraping error: {str(e)}")
        _scrape_jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        })
