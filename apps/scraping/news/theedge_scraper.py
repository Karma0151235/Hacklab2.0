"""
The Edge Markets Malaysia Scraper
Scrapes financial news from theedgemarkets.com
"""

import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

from scraping.news.base_scraper import BaseNewsScraper
from scraping.news.schemas import NewsArticle
from etl.logging_config import get_logger

logger = get_logger(__name__)


class TheEdgeScraper(BaseNewsScraper):
    """
    Scraper for The Edge Malaysia (theedgemalaysia.com)
    Primary source for Malaysian financial and business news.
    """
    
    SOURCE_NAME = "theedge"
    BASE_URL = "https://theedgemalaysia.com"
    
    # Sections to scrape
    SECTIONS = [
        "/categories/malaysia",
        "/categories/corporate",
    ]
    
    # CSS Selectors for The Edge Malaysia
    SELECTORS = {
        "article_links": "a[href*='/node/'], a[href*='/article/'], h3 a, h2 a, .views-row a",
        "title": "div.news-detail_newsdetailsItemHead__zb6Ed span, h1, .article-title, .node-title",
        "content": ".newsTextDataWrapInner, article, .article-body, .field-name-body",
        "published_date": "time, .date, .submitted, span[class*='date']",
        "author": ".author, .byline, span[class*='author']",
        "category": ".category, .tags a, nav.breadcrumb a",
    }
    
    async def _get_article_urls(self, max_articles: int) -> List[str]:
        """Get article URLs from The Edge listing pages"""
        article_urls = []
        page = self.browser.page
        
        for section in self.SECTIONS:
            if len(article_urls) >= max_articles:
                break
                
            section_url = urljoin(self.BASE_URL, section)
            
            try:
                await page.goto(section_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
                
                # Get all article links
                links = await page.query_selector_all(self.SELECTORS["article_links"])
                
                for link in links:
                    if len(article_urls) >= max_articles:
                        break
                    href = await link.get_attribute("href")
                    if href and ("/article/" in href or "/node/" in href):
                        full_url = urljoin(self.BASE_URL, href)
                        if full_url not in article_urls:
                            article_urls.append(full_url)
                            
                logger.info(f"[{self.SOURCE_NAME}] Found {len(links)} links in {section}")
                
            except Exception as e:
                logger.warning(f"[{self.SOURCE_NAME}] Error fetching {section}: {str(e)}")
                continue
                
        return article_urls[:max_articles]
    
    async def _scrape_article(self, url: str) -> Optional[NewsArticle]:
        """Scrape a single article from The Edge"""
        page = self.browser.page
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1500)
            
            # Extract title
            title_el = await page.query_selector(self.SELECTORS["title"])
            title = await title_el.inner_text() if title_el else ""
            
            if not title:
                logger.warning(f"[{self.SOURCE_NAME}] No title found for {url}")
                return None
            
            # Extract content - all .newsTextDataWrapInner divs combined
            content_parts = []
            content_elements = await page.query_selector_all(".newsTextDataWrapInner")
            for el in content_elements:
                text = await el.inner_text()
                if text and text.strip():
                    content_parts.append(text.strip())
            content = "\n\n".join(content_parts)
            
            # Extract published date
            date_el = await page.query_selector(self.SELECTORS["published_date"])
            date_text = await date_el.inner_text() if date_el else ""
            published_date = self._parse_date(date_text)
            
            # Extract author
            author_el = await page.query_selector(self.SELECTORS["author"])
            author = await author_el.inner_text() if author_el else None
            
            # Extract category
            category_el = await page.query_selector(self.SELECTORS["category"])
            category = await category_el.inner_text() if category_el else ""
            
            # Generate article ID
            article_id = self._generate_article_id(url)
            
            # Extract keywords and companies
            full_text = f"{title} {content}"
            keywords = self._extract_keywords(full_text)
            companies = self._extract_companies(full_text)
            
            return NewsArticle(
                article_id=article_id,
                source=self.SOURCE_NAME,
                title=title.strip(),
                content=content.strip(),
                summary=content[:300].strip() + "..." if len(content) > 300 else content.strip(),
                url=url,
                published_date=published_date,
                author=author.strip() if author else None,
                category=category.strip(),
                companies_mentioned=companies,
                keywords=keywords,
            )
            
        except Exception as e:
            logger.error(f"[{self.SOURCE_NAME}] Error scraping {url}: {str(e)}")
            return None
    
    async def search_company(
        self, 
        company: str, 
        start_date: str = "2024-01-01",
        end_date: str = None,
        max_results: int = 20
    ) -> List[NewsArticle]:
        """
        Search for news articles about a specific company
        
        Args:
            company: Company name to search for
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (defaults to today)
            max_results: Maximum number of articles to return
            
        Returns:
            List of NewsArticle objects
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        articles = []
        offset = 0
        page = self.browser.page
        
        logger.info(f"[{self.SOURCE_NAME}] Searching for '{company}' from {start_date} to {end_date}")
        
        while len(articles) < max_results:
            # Build search URL
            search_url = (
                f"{self.BASE_URL}/news-search-results?"
                f"keywords={company}&"
                f"from={start_date}&"
                f"to={end_date}&"
                f"language=english&"
                f"offset={offset}"
            )
            
            try:
                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)
                
                # Extract article links from search results
                links = await page.eval_on_selector_all(
                    self.SELECTORS["article_links"],
                    "elements => elements.map(e => e.href)"
                )
                
                if not links:
                    logger.info(f"[{self.SOURCE_NAME}] No more search results at offset {offset}")
                    break
                
                # Remove duplicates and filter valid article URLs
                unique_links = []
                for link in links:
                    full_url = urljoin(self.BASE_URL, link)
                    if full_url not in unique_links and "/node/" in full_url:
                        unique_links.append(full_url)
                
                logger.info(f"[{self.SOURCE_NAME}] Found {len(unique_links)} unique links at offset {offset}")
                
                # Scrape each article
                for url in unique_links:
                    if len(articles) >= max_results:
                        break
                    
                    article = await self._scrape_article(url)
                    if article:
                        articles.append(article)
                        logger.info(f"[{self.SOURCE_NAME}] Scraped {len(articles)}/{max_results}: {article.title[:50]}...")
                
                # Move to next page
                offset += len(unique_links)
                
                # If we got fewer links than expected, we've reached the end
                if len(unique_links) < 10:
                    break
                    
            except Exception as e:
                logger.error(f"[{self.SOURCE_NAME}] Error in search at offset {offset}: {e}")
                break
        
        logger.info(f"[{self.SOURCE_NAME}] Search complete: {len(articles)} articles found")
        return articles
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from various formats used by The Edge"""
        if not date_text:
            return None
            
        date_text = date_text.strip()
        
        # Common formats used by The Edge
        formats = [
            "%d %b %Y, %I:%M %p",  # "25 Jan 2025, 10:30 AM"
            "%B %d, %Y",           # "January 25, 2025"
            "%d/%m/%Y",            # "25/01/2025"
            "%Y-%m-%d",            # "2025-01-25"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue
                
        return None

