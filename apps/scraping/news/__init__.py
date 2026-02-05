"""
News scraping module exports
"""

from scraping.news.schemas import NewsArticle, NewsSentiment, NewsBatchResult
from scraping.news.base_scraper import BaseNewsScraper
from scraping.news.theedge_scraper import TheEdgeScraper
from scraping.news.bernama_scraper import BernamaScraper

__all__ = [
    "NewsArticle",
    "NewsSentiment", 
    "NewsBatchResult",
    "BaseNewsScraper",
    "TheEdgeScraper",
    "BernamaScraper",
]

