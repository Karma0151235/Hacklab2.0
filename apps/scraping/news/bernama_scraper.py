"""
Bernama News Scraper
Scrapes financial news from bernama.com (Malaysian National News Agency)
"""

import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

from scraping.news.base_scraper import BaseNewsScraper
from scraping.news.schemas import NewsArticle
from etl.logging_config import get_logger

logger = get_logger(__name__)


class BernamaScraper(BaseNewsScraper):
    """
    Scraper for Bernama Biz (bernamabiz.com)
    Malaysian business and financial news.
    """
    
    SOURCE_NAME = "bernama"
    BASE_URL = "https://www.bernamabiz.com"
    
    # Sections to scrape - bernamabiz doesn't use /en/ prefix
    SECTIONS = [
        "/",  # Main business page
    ]
    
    # CSS Selectors for Bernama - uses news.php?id= pattern
    SELECTORS = {
        "article_links": "a[href*='news.php?id='], h6 a[href*='news.php'], .news-item a",
        "title": ".mb-2, h1, .article-title, .news-title, #news-title",
        "content": ".newsTextDataWrapInner, .article-body, .news-body, .content-text",
        "published_date": "time, .date, span[class*='date'], .news-date",
        "author": ".author, .byline, span[class*='author']",
        "category": ".category, .breadcrumb a, nav a",
    }
    
    async def _get_article_urls(self, max_articles: int) -> List[str]:
        """Get article URLs from Bernama listing pages"""
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
                    if href and "news.php?id=" in href:
                        full_url = urljoin(self.BASE_URL, href)
                        if full_url not in article_urls:
                            article_urls.append(full_url)
                            
                logger.info(f"[{self.SOURCE_NAME}] Found {len(links)} links in {section}")
                
            except Exception as e:
                logger.warning(f"[{self.SOURCE_NAME}] Error fetching {section}: {str(e)}")
                continue
                
        return article_urls[:max_articles]
    
    async def _scrape_article(self, url: str) -> Optional[NewsArticle]:
        """Scrape a single article from Bernama"""
        page = self.browser.page
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1500)
            
            # Extract title - h1 with mb-2 class
            title_el = await page.query_selector("h1.mb-2")
            title = await title_el.inner_text() if title_el else ""
            
            if not title:
                logger.warning(f"[{self.SOURCE_NAME}] No title found for {url}")
                return None
            
            # Extract content - all p tags within .single-post div combined
            content_parts = []
            content_elements = await page.query_selector_all(".single-post p")
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
    
    async def search_company(self, company: str, max_results: int = 20) -> List[NewsArticle]:
        """
        Search for news articles about a specific company on Bernama
        
        Args:
            company: Company name to search for
            max_results: Maximum number of articles to return
            
        Returns:
            List of NewsArticle objects
        """
        articles = []
        page = self.browser.page
        
        # Bernama search URL
        search_url = f"{self.BASE_URL}/search.php?terms={company}"
        
        logger.info(f"[{self.SOURCE_NAME}] Searching for '{company}'")
        
        try:
            await page.goto(search_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Extract article links from search results
            links = await page.eval_on_selector_all(
                self.SELECTORS["article_links"],
                "elements => elements.map(e => e.href)"
            )
            
            if not links:
                logger.info(f"[{self.SOURCE_NAME}] No search results found")
                return articles
            
            # Remove duplicates and filter valid article URLs
            unique_links = []
            for link in links:
                full_url = urljoin(self.BASE_URL, link)
                if full_url not in unique_links and "news.php?id=" in full_url:
                    unique_links.append(full_url)
            
            logger.info(f"[{self.SOURCE_NAME}] Found {len(unique_links)} unique article links")
            
            # Scrape each article up to max_results
            for url in unique_links[:max_results]:
                article = await self._scrape_article(url)
                if article:
                    articles.append(article)
                    logger.info(f"[{self.SOURCE_NAME}] Scraped {len(articles)}/{min(len(unique_links), max_results)}: {article.title[:50]}...")
                    
        except Exception as e:
            logger.error(f"[{self.SOURCE_NAME}] Error in search: {e}")
        
        logger.info(f"[{self.SOURCE_NAME}] Search complete: {len(articles)} articles found")
        return articles
    
    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date from various formats used by Bernama"""
        if not date_text:
            return None
            
        date_text = date_text.strip()
        
        # Common formats used by Bernama
        formats = [
            "%d %B %Y",            # "25 January 2025"
            "%d %b %Y",            # "25 Jan 2025"
            "%Y-%m-%d %H:%M:%S",   # "2025-01-25 10:30:00"
            "%d/%m/%Y",            # "25/01/2025"
            "%Y-%m-%d",            # "2025-01-25"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue
                
        return None
