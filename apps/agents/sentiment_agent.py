"""
Sentiment Agent for Market Intelligence
Analyzes news articles and documents for sentiment to inform investment decisions
"""

import json
import re
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import openai

from agents.schemas import RAGOutput
from agents.config import AgentConfig
from scraping.news.schemas import NewsArticle, NewsSentiment
from etl.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# Sentiment Agent Schemas
# ============================================================================

from pydantic import BaseModel, Field
from datetime import datetime


class SentimentAgentInput(BaseModel):
    """Input schema for Sentiment Agent"""
    query: str = Field(..., description="Query for sentiment analysis")
    company_name: Optional[str] = Field(default=None, description="Company to focus analysis on")
    news_articles: List[NewsArticle] = Field(default_factory=list, description="News articles to analyze")
    rag_context: Optional[RAGOutput] = Field(default=None, description="Additional context from RAG")


class SentimentAgentOutput(BaseModel):
    """Output schema for Sentiment Agent"""
    overall_sentiment: str = Field(..., description="Overall sentiment: positive, neutral, negative")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score from -1.0 to 1.0")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in analysis")
    
    # Detailed breakdown
    sentiment_by_source: Dict[str, float] = Field(default_factory=dict, description="Sentiment by news source")
    key_topics: List[str] = Field(default_factory=list, description="Key topics identified")
    key_phrases: List[str] = Field(default_factory=list, description="Key phrases influencing sentiment")
    
    # Trend analysis
    trend: str = Field(default="stable", description="Sentiment trend: improving, stable, declining")
    trend_explanation: str = Field(default="", description="Explanation for trend")
    
    # Company-specific
    company_sentiments: Dict[str, float] = Field(default_factory=dict, description="Sentiment by company")
    
    # Summary
    summary: str = Field(..., description="Human-readable summary of sentiment analysis")
    articles_analyzed: int = Field(default=0, description="Number of articles analyzed")
    
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Sentiment Agent Implementation
# ============================================================================

class SentimentAgent:
    """
    Sentiment Agent for analyzing market sentiment from news and documents.
    
    System Prompt:
    You are the Sentiment Agent for market intelligence.
    
    Analyze news articles and documents to determine:
    • Overall market sentiment (positive/neutral/negative)
    • Sentiment score (-1.0 to 1.0)
    • Key topics and phrases driving sentiment
    • Company-specific sentiment breakdown
    • Sentiment trends over time
    
    Focus on actionable insights for investment decisions.
    """
    
    SYSTEM_PROMPT = """You are the Sentiment Agent for market intelligence.

Your role is to analyze news articles and documents to determine market sentiment.

For each analysis, you must determine:
1. Overall sentiment: positive, neutral, or negative
2. Sentiment score: -1.0 (very negative) to 1.0 (very positive)
3. Key topics and phrases that drive the sentiment
4. Company-specific sentiment if multiple companies are mentioned
5. Actionable insights for investment decisions

Focus on:
- Financial implications (earnings, revenue, growth)
- Market signals (analyst ratings, price movements)
- Corporate actions (M&A, restructuring, management changes)
- Regulatory impacts
- Economic indicators

Be objective and evidence-based. Cite specific phrases or facts that support your sentiment assessment."""

    # Sentiment keywords for fallback analysis
    POSITIVE_KEYWORDS = [
        "growth", "profit", "surge", "gain", "beat", "exceed", "strong",
        "upgrade", "outperform", "record", "dividend", "expansion", "optimistic",
        "bullish", "positive", "success", "improvement", "recovery"
    ]
    
    NEGATIVE_KEYWORDS = [
        "loss", "decline", "fall", "drop", "miss", "below", "weak",
        "downgrade", "underperform", "concern", "risk", "warning", "cut",
        "bearish", "negative", "challenge", "struggle", "restructuring"
    ]
    
    def __init__(self):
        """Initialize Sentiment Agent"""
        self.config = AgentConfig
        
        # Initialize OpenRouter client
        self.client = openai.OpenAI(
            api_key=self.config.OPENROUTER_API_KEY,
            base_url=self.config.OPENROUTER_BASE_URL,
            timeout=self.config.OPENROUTER_TIMEOUT_SECONDS,
            max_retries=self.config.OPENROUTER_MAX_RETRIES,
        )
        
        logger.info("Sentiment Agent initialized")
    
    def analyze(self, input_data: SentimentAgentInput) -> SentimentAgentOutput:
        """
        Analyze sentiment from news articles and context.
        
        Args:
            input_data: SentimentAgentInput with articles and context
            
        Returns:
            SentimentAgentOutput with sentiment analysis results
        """
        try:
            logger.info(f"Sentiment Agent analyzing: {input_data.query}")
            
            if not input_data.news_articles and not input_data.rag_context:
                return self._empty_output("No content to analyze")
            
            # Prepare content for analysis
            content = self._prepare_content(input_data)
            
            # Analyze using LLM
            sentiment_result = self._analyze_with_llm(
                query=input_data.query,
                content=content,
                company_name=input_data.company_name
            )
            
            # Calculate sentiment by source
            sentiment_by_source = {}
            for article in input_data.news_articles:
                article_sentiment = self._quick_sentiment(article.content)
                sentiment_by_source[article.source] = article_sentiment
            
            output = SentimentAgentOutput(
                overall_sentiment=sentiment_result.get("sentiment", "neutral"),
                sentiment_score=sentiment_result.get("score", 0.0),
                confidence=sentiment_result.get("confidence", 0.5),
                sentiment_by_source=sentiment_by_source,
                key_topics=sentiment_result.get("key_topics", []),
                key_phrases=sentiment_result.get("key_phrases", []),
                trend=sentiment_result.get("trend", "stable"),
                trend_explanation=sentiment_result.get("trend_explanation", ""),
                company_sentiments=sentiment_result.get("company_sentiments", {}),
                summary=sentiment_result.get("summary", ""),
                articles_analyzed=len(input_data.news_articles),
            )
            
            logger.info(f"Sentiment Agent result: {output.overall_sentiment} ({output.sentiment_score:.2f})")
            return output
            
        except Exception as e:
            logger.error(f"Sentiment Agent error: {str(e)}")
            return self._empty_output(f"Analysis error: {str(e)}")
    
    def _prepare_content(self, input_data: SentimentAgentInput) -> str:
        """Prepare content string from articles and context"""
        parts = []
        
        # Add news articles
        for idx, article in enumerate(input_data.news_articles[:10], 1):  # Limit to 10 articles
            parts.append(f"Article {idx} ({article.source}):")
            parts.append(f"Title: {article.title}")
            parts.append(f"Content: {article.content[:1000]}...")  # Truncate long content
            parts.append("")
        
        # Add RAG context if available
        if input_data.rag_context:
            parts.append("Additional Context:")
            parts.append(input_data.rag_context.summary)
        
        return "\n".join(parts)
    
    def _analyze_with_llm(
        self, 
        query: str, 
        content: str, 
        company_name: Optional[str]
    ) -> Dict[str, Any]:
        """Analyze sentiment using LLM"""
        try:
            company_context = f" Focus on {company_name}." if company_name else ""
            
            prompt = f"""Analyze the sentiment of the following content.{company_context}

Query: {query}

Content:
{content[:4000]}

Provide your analysis as JSON:
{{
    "sentiment": "positive|neutral|negative",
    "score": -1.0 to 1.0,
    "confidence": 0.0 to 1.0,
    "key_topics": ["topic1", "topic2", "topic3"],
    "key_phrases": ["phrase that influenced sentiment", ...],
    "trend": "improving|stable|declining",
    "trend_explanation": "brief explanation of trend",
    "company_sentiments": {{"Company Name": score, ...}},
    "summary": "2-3 sentence summary of sentiment and implications"
}}"""

            response = self.client.chat.completions.create(
                model=self.config.GLM_4_5_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=1000,
                extra_body={"reasoning": {"enabled": True}}
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content.strip()
                
                return json.loads(json_str)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM response: {e}")
                return self._fallback_analysis(content)
                
        except Exception as e:
            logger.error(f"LLM analysis error: {str(e)}")
            return self._fallback_analysis(content if 'content' in locals() else "")
    
    def _fallback_analysis(self, content: str) -> Dict[str, Any]:
        """Fallback keyword-based sentiment analysis"""
        score = self._quick_sentiment(content)
        
        if score > 0.2:
            sentiment = "positive"
        elif score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": 0.5,
            "key_topics": [],
            "key_phrases": [],
            "trend": "stable",
            "trend_explanation": "Keyword-based analysis",
            "company_sentiments": {},
            "summary": f"Keyword analysis indicates {sentiment} sentiment (score: {score:.2f})"
        }
    
    def _quick_sentiment(self, text: str) -> float:
        """Quick keyword-based sentiment scoring"""
        if not text:
            return 0.0
            
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.POSITIVE_KEYWORDS if word in text_lower)
        negative_count = sum(1 for word in self.NEGATIVE_KEYWORDS if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
            
        # Score from -1 to 1
        score = (positive_count - negative_count) / total
        return max(-1.0, min(1.0, score))
    
    def _empty_output(self, message: str) -> SentimentAgentOutput:
        """Return empty output with message"""
        return SentimentAgentOutput(
            overall_sentiment="neutral",
            sentiment_score=0.0,
            confidence=0.0,
            summary=message,
        )
