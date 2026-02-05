"""
Base News Scraper
Abstract base class for all news scrapers with common functionality
"""

import asyncio
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin

from scraping.browser.playwright import PlaywrightBrowser
from scraping.news.schemas import NewsArticle, NewsBatchResult
from etl.logging_config import get_logger

logger = get_logger(__name__)


class BaseNewsScraper(ABC):
    """
    Abstract base class for news scrapers.
    Provides common functionality for rate limiting, error handling, and extraction.
    """
    
    SOURCE_NAME: str = "unknown"
    BASE_URL: str = ""
    
    # Rate limiting
    REQUEST_DELAY_SECONDS: float = 2.0
    MAX_RETRIES: int = 3
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[PlaywrightBrowser] = None
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
        
    async def start(self):
        """Initialize browser session"""
        self.browser = PlaywrightBrowser()
        await self.browser.launch(headless=self.headless)
        await self.browser.create_context(
            record_video=False,
            viewport={"width": 1280, "height": 720},
            block_resources=True,  # Block images/fonts for speed
        )
        logger.info(f"[{self.SOURCE_NAME}] Browser started")
        
    async def stop(self):
        """Close browser session"""
        if self.browser and self.browser.browser:
            await self.browser.browser.close()
            logger.info(f"[{self.SOURCE_NAME}] Browser stopped")
    
    async def scrape_batch(
        self,
        max_articles: int = 50,
        company_filters: Optional[List[str]] = None,
        days_back: int = 7,
    ) -> NewsBatchResult:
        """
        Scrape a batch of news articles.
        
        Args:
            max_articles: Maximum number of articles to scrape
            company_filters: Optional list of company names to filter by
            days_back: How many days back to scrape
            
        Returns:
            NewsBatchResult with scraped articles
        """
        started_at = datetime.utcnow()
        articles = []
        errors = []
        
        try:
            # Get article URLs from listing page
            article_urls = await self._get_article_urls(max_articles)
            logger.info(f"[{self.SOURCE_NAME}] Found {len(article_urls)} article URLs")
            
            # Scrape each article
            for idx, url in enumerate(article_urls):
                try:
                    await asyncio.sleep(self.REQUEST_DELAY_SECONDS)
                    article = await self._scrape_article(url)
                    
                    if article:
                        # Apply company filter if specified
                        if company_filters:
                            if self._matches_company_filter(article, company_filters):
                                articles.append(article)
                        else:
                            articles.append(article)
                            
                    logger.info(f"[{self.SOURCE_NAME}] Scraped {idx + 1}/{len(article_urls)}")
                    
                except Exception as e:
                    error_msg = f"Error scraping {url}: {str(e)}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
                    
        except Exception as e:
            error_msg = f"Batch scraping error: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            
        return NewsBatchResult(
            source=self.SOURCE_NAME,
            articles=articles,
            total_scraped=len(articles),
            errors=errors,
            started_at=started_at,
            completed_at=datetime.utcnow(),
        )
    
    def _matches_company_filter(
        self, 
        article: NewsArticle, 
        company_filters: List[str]
    ) -> bool:
        """Check if article mentions any of the filtered companies"""
        content_lower = (article.title + " " + article.content).lower()
        for company in company_filters:
            if company.lower() in content_lower:
                return True
        return False
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text"""
        # Extract capitalized words and common financial terms
        words = re.findall(r'\b[A-Z][a-z]+\b|\b[A-Z]{2,}\b', text)
        return list(set(words))[:max_keywords]
    
    def _extract_companies(self, text: str) -> List[str]:
        """Extract company names mentioned in text"""
        # Common Malaysian company patterns: ends with Bhd, Berhad, etc.
        patterns = [
            r'\b[A-Z][a-zA-Z\s]+(?:Bhd|Berhad|Holdings|Group)\b',
            r'\b[A-Z]{2,}(?:\s+[A-Z]+)*\b',  # Stock codes like MAYBANK, CIMB
        ]
        companies = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            companies.extend(matches)
        return list(set(companies))[:20]
    
    def _generate_article_id(self, url: str) -> str:
        """Generate unique article ID from URL"""
        # Extract path components and create ID
        clean_url = re.sub(r'https?://', '', url)
        clean_url = re.sub(r'[^\w\-]', '_', clean_url)
        return f"{self.SOURCE_NAME}_{clean_url[:100]}"
    
    @abstractmethod
    async def _get_article_urls(self, max_articles: int) -> List[str]:
        """Get list of article URLs from listing page (implement in subclass)"""
        pass
    
    @abstractmethod
    async def _scrape_article(self, url: str) -> Optional[NewsArticle]:
        """Scrape single article (implement in subclass)"""
        pass
