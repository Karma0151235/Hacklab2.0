"""
News Article Schema
Data models for news scraping and sentiment analysis
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    """
    News article from external sources (The Edge, Bernama, etc.)
    Used for sentiment analysis and market intelligence.
    """
    # Identifiers
    article_id: str = Field(..., description="Unique article identifier")
    source: str = Field(..., description="News source: theedge, bernama, etc.")
    
    # Content
    title: str
    content: str
    summary: Optional[str] = None
    
    # Metadata
    url: str
    published_date: Optional[datetime] = None
    author: Optional[str] = None
    
    # Classification
    category: str = ""  # business, markets, economy, etc.
    companies_mentioned: List[str] = Field(default_factory=list)
    tickers_mentioned: List[str] = Field(default_factory=list)
    
    # Keywords for filtering
    keywords: List[str] = Field(default_factory=list)
    
    # Extraction metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class NewsSentiment(BaseModel):
    """
    Sentiment analysis result for a news article
    """
    article_id: str
    sentiment: str  # positive, neutral, negative
    score: float = Field(..., ge=-1.0, le=1.0)  # -1.0 to 1.0
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Key factors
    key_phrases: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    
    # For company-specific analysis
    company_sentiments: Dict[str, float] = Field(default_factory=dict)
    
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


class NewsBatchResult(BaseModel):
    """
    Result of a batch news scraping operation
    """
    source: str
    articles: List[NewsArticle] = Field(default_factory=list)
    total_scraped: int = 0
    errors: List[str] = Field(default_factory=list)
    started_at: datetime
    completed_at: Optional[datetime] = None
