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

from agents.schemas import (
    RAGOutput,
    SentimentAgentInput,
    SentimentAgentOutput
)
from agents.config import AgentConfig
from scraping.news.schemas import NewsArticle, NewsSentiment
from etl.logging_config import get_logger

logger = get_logger(__name__)


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

    # Sentiment keywords for fallback analysis (whole-word matched via regex)
    POSITIVE_KEYWORDS = [
        "growth", "profit", "profits", "profitable", "profitability",
        "surge", "surged", "surging", "gain", "gains", "gained",
        "beat", "beats", "exceed", "exceeded", "exceeds",
        "strong", "stronger", "strongest", "strength",
        "upgrade", "upgraded", "outperform", "outperformed",
        "record", "dividend", "dividends", "expansion", "expanding",
        "optimistic", "optimism", "bullish", "positive",
        "success", "successful", "improvement", "improved", "improving",
        "recovery", "recovering", "recovered", "rebound", "rebounded",
        "revenue", "earnings", "income", "acquisition", "acquire",
        "investment", "invest", "investing", "investor",
        "upside", "momentum", "boost", "boosted", "rally", "rallied",
        "outpace", "robust", "resilient", "resilience",
        "partnership", "collaboration", "innovation", "innovative",
        "milestone", "award", "awarded", "approve", "approved",
        "breakout", "breakthrough", "opportunity", "opportunities",
        "higher", "increase", "increased", "rising", "risen", "rise",
    ]

    NEGATIVE_KEYWORDS = [
        "loss", "losses", "losing",
        "decline", "declined", "declining", "decrease", "decreased",
        "fall", "falls", "fallen", "falling",
        "drop", "dropped", "dropping", "plunge", "plunged",
        "miss", "missed", "misses", "below",
        "weak", "weaker", "weakest", "weakness",
        "downgrade", "downgraded", "underperform", "underperformed",
        "concern", "concerns", "concerned",
        "risk", "risks", "risky",
        "warning", "warnings", "warned",
        "bearish", "negative", "pessimistic",
        "challenge", "challenges", "challenging",
        "struggle", "struggles", "struggling",
        "restructuring", "layoff", "layoffs", "retrenchment",
        "default", "defaults", "defaulted",
        "debt", "liabilities", "impairment", "impaired",
        "slowdown", "slowing", "slowed", "contraction",
        "lawsuit", "litigation", "penalty", "penalties", "fine", "fined",
        "fraud", "scandal", "investigation",
        "downside", "headwind", "headwinds", "volatility", "volatile",
        "lower", "lowest", "shrink", "shrinking", "deficit",
        "suspension", "suspended", "closure", "closed",
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

            # Always compute keyword-based sentiment per article as baseline
            article_scores = []
            sentiment_by_source = {}
            article_titles = []
            for article in input_data.news_articles:
                text = (article.title or "") + " " + (article.content or "")
                score = self._quick_sentiment(text)
                article_scores.append(score)
                sentiment_by_source[article.source] = score
                article_titles.append(article.title)
                logger.debug(f"[sentiment] Article '{article.title[:60]}' content_len={len(article.content)} keyword_score={score:.2f}")

            # Compute baseline keyword score from all articles
            if article_scores:
                keyword_avg_score = sum(article_scores) / len(article_scores)
            else:
                keyword_avg_score = 0.0

            logger.info(f"[sentiment] Keyword baseline: avg={keyword_avg_score:.3f}, per_article={[round(s, 2) for s in article_scores]}")

            # Prepare content for LLM analysis
            content = self._prepare_content(input_data)

            # Try LLM analysis
            sentiment_result = self._analyze_with_llm(
                query=input_data.query,
                content=content,
                company_name=input_data.company_name
            )

            llm_failed = sentiment_result.get("llm_failed", False)
            llm_score = float(sentiment_result.get("score", 0.0) or 0.0)
            llm_confidence = float(sentiment_result.get("confidence", 0.0) or 0.0)

            logger.info(f"[sentiment] LLM result: failed={llm_failed}, score={llm_score:.2f}, confidence={llm_confidence:.2f}")

            # Decision logic: prefer per-article keyword baseline when LLM is unreliable
            if llm_failed:
                # LLM returned empty/broken — use keyword baseline unconditionally
                final_score = keyword_avg_score
                final_confidence = 0.6 if keyword_avg_score != 0.0 else 0.3
                logger.info(f"[sentiment] LLM failed, using keyword baseline: score={final_score:.2f}")
            elif llm_score == 0.0 and abs(keyword_avg_score) > 0.2:
                # LLM says neutral but keyword baseline has a clear signal —
                # keyword baseline from actual article text is more trustworthy
                # than a model that often returns empty or "no references found"
                final_score = keyword_avg_score
                final_confidence = 0.6
                logger.info(f"[sentiment] LLM=0.0 but keywords={keyword_avg_score:.2f}, using keyword baseline")
            elif llm_confidence >= 0.5 and llm_score != 0.0:
                # LLM returned a meaningful score with decent confidence — trust it
                final_score = llm_score
                final_confidence = llm_confidence
            else:
                # Blend: average LLM and keyword scores when both are available
                if keyword_avg_score != 0.0 and llm_score != 0.0:
                    final_score = (llm_score + keyword_avg_score) / 2
                    final_confidence = max(llm_confidence, 0.5)
                elif keyword_avg_score != 0.0:
                    final_score = keyword_avg_score
                    final_confidence = 0.6
                else:
                    final_score = llm_score
                    final_confidence = llm_confidence if llm_confidence > 0 else 0.5

            # Determine sentiment label
            if final_score > 0.15:
                overall_sentiment = "positive"
            elif final_score < -0.15:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"

            # Clean company_sentiments
            raw_cs = sentiment_result.get("company_sentiments", {})
            company_sentiments = {}
            for k, v in (raw_cs or {}).items():
                if v is not None:
                    try:
                        company_sentiments[str(k)] = float(v)
                    except (ValueError, TypeError):
                        pass
            # Add company from keyword analysis if missing
            if input_data.company_name and input_data.company_name not in company_sentiments:
                company_sentiments[input_data.company_name] = final_score

            # Build summary if LLM didn't provide one
            summary = sentiment_result.get("summary", "") or ""
            if not summary and article_titles:
                summary = f"Analysis of {len(input_data.news_articles)} articles about {input_data.company_name or 'the company'}. Headlines include: {'; '.join(article_titles[:3])}."

            output = SentimentAgentOutput(
                overall_sentiment=overall_sentiment,
                sentiment_score=max(-1.0, min(1.0, final_score)),
                confidence=max(0.0, min(1.0, final_confidence)),
                sentiment_by_source=sentiment_by_source,
                key_topics=sentiment_result.get("key_topics", []) or [],
                key_phrases=sentiment_result.get("key_phrases", []) or [],
                trend=sentiment_result.get("trend", "stable") or "stable",
                trend_explanation=sentiment_result.get("trend_explanation", "") or "",
                company_sentiments=company_sentiments,
                summary=summary,
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
            )

            content = response.choices[0].message.content or ""

            logger.info(f"[sentiment_llm] Raw response length: {len(content)}, first 200 chars: {content[:200]}")

            if not content.strip():
                logger.warning("LLM returned empty content for sentiment analysis — signalling llm_failed")
                # Return a signal dict so analyze() knows to use per-article keyword baseline
                return {"llm_failed": True, "score": 0.0, "confidence": 0.0,
                        "key_topics": [], "key_phrases": [], "trend": "stable",
                        "trend_explanation": "", "company_sentiments": {}, "summary": ""}

            # Parse JSON response - try multiple strategies
            try:
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content.strip()

                return json.loads(json_str)

            except json.JSONDecodeError:
                # Try balanced brace extraction
                brace_start = content.find('{')
                if brace_start != -1:
                    depth = 0
                    for i in range(brace_start, len(content)):
                        if content[i] == '{':
                            depth += 1
                        elif content[i] == '}':
                            depth -= 1
                            if depth == 0:
                                try:
                                    return json.loads(content[brace_start:i+1])
                                except json.JSONDecodeError:
                                    break
                                break

                logger.warning(f"Failed to parse LLM sentiment response, using fallback")
                return self._fallback_analysis(content)
                
        except Exception as e:
            logger.error(f"LLM analysis error: {str(e)}")
            return {"llm_failed": True, "score": 0.0, "confidence": 0.0,
                    "key_topics": [], "key_phrases": [], "trend": "stable",
                    "trend_explanation": f"LLM error: {str(e)}", "company_sentiments": {}, "summary": ""}
    
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
        """Quick keyword-based sentiment scoring using whole-word matching"""
        if not text:
            return 0.0

        text_lower = text.lower()

        # Use word-boundary regex to avoid substring false positives
        # e.g. "risk" should not match inside "brisk"
        positive_count = sum(
            1 for word in self.POSITIVE_KEYWORDS
            if re.search(r'\b' + re.escape(word) + r'\b', text_lower)
        )
        negative_count = sum(
            1 for word in self.NEGATIVE_KEYWORDS
            if re.search(r'\b' + re.escape(word) + r'\b', text_lower)
        )

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
