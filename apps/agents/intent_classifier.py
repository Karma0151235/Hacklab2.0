"""
Intent Classifier for query analysis and agent routing
Determines which agents should be executed based on query intent
"""

import re
from typing import Dict, List, Optional
import openai

from agents.schemas import IntentClassification
from agents.config import AgentConfig
from etl.logging_config import get_logger

logger = get_logger(__name__)


class IntentClassifier:
    """Classify user queries to determine intent and required agents"""

    # Intent keywords for pattern matching
    FINANCIAL_KEYWORDS = {
        'financial': ['financial', 'finance', 'accounting', 'accounts'],
        'metrics': ['ratio', 'metric', 'metrics', 'kpi', 'kpis', 'indicator', 'indicators'],
        'performance': ['performance', 'performance', 'earnings', 'profit', 'revenue', 'sales'],
        'profitability': ['profitability', 'profitable', 'margin', 'margins', 'profit margin'],
        'liquidity': ['liquidity', 'liquid', 'current ratio', 'quick ratio', 'working capital'],
        'solvency': ['solvency', 'debt', 'leverage', 'equity', 'capital structure'],
        'growth': ['growth', 'growing', 'expansion', 'yoy', 'year-over-year', 'cagr'],
        'valuation': ['valuation', 'pe ratio', 'price-to-earnings', 'book value', 'enterprise value']
    }

    RISK_KEYWORDS = {
        'risk': ['risk', 'risks', 'risky', 'vulnerable'],
        'concern': ['concern', 'concerns', 'concern', 'worried', 'warning'],
        'alert': ['alert', 'alerts', 'alarming', 'alarm'],
        'adverse': ['adverse', 'negative', 'decline', 'declining', 'downturn'],
        'breach': ['breach', 'violation', 'violate', 'violated', 'breached'],
        'legal': ['legal', 'litigation', 'lawsuit', 'investigation', 'regulatory'],
        'health': ['health', 'healthy', 'unhealthy', 'wellbeing', 'condition'],
        'weakness': ['weakness', 'weak', 'fragile', 'vulnerable', 'exposed']
    }

    TREND_KEYWORDS = {
        'trend': ['trend', 'trends', 'trending', 'trajectory', 'direction'],
        'comparison': ['compare', 'comparison', 'vs', 'versus', 'relative', 'relative'],
        'analysis': ['analysis', 'analyze', 'analytical', 'breakdown'],
        'historical': ['historical', 'history', 'past', 'previous', 'prior'],
        'forecast': ['forecast', 'predict', 'prediction', 'outlook', 'projections']
    }

    SENTIMENT_KEYWORDS = {
        'sentiment': ['sentiment', 'sentiments', 'market sentiment', 'investor sentiment'],
        'perception': ['perception', 'opinion', 'public opinion', 'market opinion'],
        'news': ['news', 'headlines', 'articles', 'media', 'press', 'coverage'],
        'scrape': ['scrap', 'scrape', 'scraping', 'fetch news', 'latest news', 'web search'],
        'mood': ['mood', 'feeling', 'outlook', 'bullish', 'bearish'],
    }

    INFORMATION_KEYWORDS = {
        'summary': ['summary', 'summarize', 'overview', 'overview', 'brief'],
        'details': ['details', 'detail', 'information', 'data', 'facts'],
        'list': ['list', 'listing', 'enumerate', 'what are', 'which'],
        'company': ['company', 'companies', 'corporation', 'organization']
    }

    def __init__(self):
        """Initialize intent classifier with OpenRouter client"""
        self.client = openai.OpenAI(
            api_key=AgentConfig.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = AgentConfig.GLM_4_5_MODEL

    def classify(self, query: str) -> IntentClassification:
        """
        Classify user query intent and determine required agents.

        Args:
            query: User query string

        Returns:
            IntentClassification with intent analysis and agent requirements
        """
        try:
            # Step 1: Keyword-based classification (fast, deterministic)
            keyword_scores = self._extract_intent_patterns(query)

            # Step 2: LLM-based classification (accurate, handles nuance)
            llm_classification = self._classify_with_llm(query, keyword_scores)

            logger.info(f"Query classified as: {llm_classification.primary_intent} (confidence: {llm_classification.confidence:.2f})")

            return llm_classification

        except Exception as e:
            logger.error(f"Intent classification failed: {str(e)}")
            # Fallback to conservative classification
            return self._fallback_classification(query)

    def _extract_intent_patterns(self, query: str) -> Dict[str, float]:
        """
        Extract intent signals using keyword and pattern matching.

        Returns:
            Dict mapping intent types to confidence scores (0-1)
        """
        query_lower = query.lower()
        scores = {
            'financial_analysis': 0.0,
            'risk_assessment': 0.0,
            'trend_analysis': 0.0,
            'information_retrieval': 0.0,
            'sentiment_analysis': 0.0,
        }

        # Count keyword matches for each intent
        financial_matches = sum(1 for keywords in self.FINANCIAL_KEYWORDS.values() for kw in keywords if kw in query_lower)
        risk_matches = sum(1 for keywords in self.RISK_KEYWORDS.values() for kw in keywords if kw in query_lower)
        trend_matches = sum(1 for keywords in self.TREND_KEYWORDS.values() for kw in keywords if kw in query_lower)
        info_matches = sum(1 for keywords in self.INFORMATION_KEYWORDS.values() for kw in keywords if kw in query_lower)
        sentiment_matches = sum(1 for keywords in self.SENTIMENT_KEYWORDS.values() for kw in keywords if kw in query_lower)

        # Normalize scores
        total_matches = financial_matches + risk_matches + trend_matches + info_matches + sentiment_matches
        if total_matches > 0:
            scores['financial_analysis'] = min(financial_matches / total_matches, 1.0)
            scores['risk_assessment'] = min(risk_matches / total_matches, 1.0)
            scores['trend_analysis'] = min(trend_matches / total_matches, 1.0)
            scores['information_retrieval'] = min(info_matches / total_matches, 1.0)
            scores['sentiment_analysis'] = min(sentiment_matches / total_matches, 1.0)

        logger.debug(f"Keyword pattern scores: {scores}")
        return scores

    def _classify_with_llm(self, query: str, keyword_scores: Dict[str, float]) -> IntentClassification:
        """
        Use LLM for nuanced intent classification with structured output.

        Args:
            query: User query
            keyword_scores: Pre-calculated keyword scores for context

        Returns:
            IntentClassification with LLM-based analysis
        """
        system_prompt = """You are an expert query analyzer for financial intelligence systems.

Your task: Analyze the user's query and determine:
1. Primary intent (one of: financial_analysis, risk_assessment, trend_analysis, information_retrieval, sentiment_analysis)
2. Secondary intents (if any)
3. Required agents to answer this query (rag=context retrieval, financial=metrics calculation, alert=risk evaluation, sentiment=news sentiment analysis)
4. The company name mentioned in the query (if any)
5. Data quality requirements

Return ONLY a JSON object (no markdown, no explanation, no code fences):
{
  "primary_intent": "string",
  "secondary_intents": ["string"],
  "required_agents": ["rag", "financial", "alert", "sentiment"],
  "optional_agents": ["string"],
  "company_name": "string or null",
  "data_quality_requirements": {"min_confidence": 0.0, "min_chunks": 2},
  "priority_level": "critical|high|normal|low",
  "confidence": 0.8,
  "reasoning": "string"
}

Intent definitions:
- financial_analysis: Query asks for financial metrics, ratios, calculations, performance analysis
- risk_assessment: Query asks for risks, concerns, warnings, alerts, adverse conditions
- trend_analysis: Query asks for comparisons, changes over time, forecasts
- information_retrieval: Query asks for summaries, facts, listings, general information
- sentiment_analysis: Query asks about sentiment, news, media perception, market mood, or requests scraping/fetching news

Agent requirements:
- rag: Always needed for context. Required for all queries.
- financial: Needed if query involves financial metrics, calculations, or analysis
- alert: Needed if query involves risk assessment, concerns, or alerting conditions
- sentiment: Needed if query mentions sentiment, news, media, market mood, scraping, or public perception

Company extraction:
- Extract the company name from the query if mentioned (e.g. "Sunway", "Maybank", "Foodie Media Berhad")
- Return null if no specific company is mentioned"""

        user_prompt = f"""Analyze this query and determine the required agents and data requirements:

Query: "{query}"

Keyword pattern scores (for reference):
- Financial analysis: {keyword_scores.get('financial_analysis', 0):.2f}
- Risk assessment: {keyword_scores.get('risk_assessment', 0):.2f}
- Trend analysis: {keyword_scores.get('trend_analysis', 0):.2f}
- Information retrieval: {keyword_scores.get('information_retrieval', 0):.2f}
- Sentiment analysis: {keyword_scores.get('sentiment_analysis', 0):.2f}

Return ONLY a valid JSON object, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=1000,
            )

            response_text = response.choices[0].message.content or ""

            # If content is empty, the model may have put everything in reasoning
            if not response_text.strip():
                logger.warning("LLM returned empty content for intent classification, using fallback")
                return self._fallback_classification(query)

            # Parse JSON response - try multiple strategies
            import json
            import re

            classification_dict = None

            # Strategy 1: Try parsing the whole response as JSON
            try:
                classification_dict = json.loads(response_text.strip())
            except (json.JSONDecodeError, TypeError):
                pass

            # Strategy 2: Extract JSON from code fences
            if classification_dict is None:
                code_fence_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if code_fence_match:
                    try:
                        classification_dict = json.loads(code_fence_match.group(1))
                    except json.JSONDecodeError:
                        pass

            # Strategy 3: Find the outermost balanced braces
            if classification_dict is None:
                brace_start = response_text.find('{')
                if brace_start != -1:
                    depth = 0
                    for i in range(brace_start, len(response_text)):
                        if response_text[i] == '{':
                            depth += 1
                        elif response_text[i] == '}':
                            depth -= 1
                            if depth == 0:
                                try:
                                    classification_dict = json.loads(response_text[brace_start:i+1])
                                except json.JSONDecodeError:
                                    pass
                                break

            # Strategy 4: Extract key fields from truncated/partial JSON via regex
            if classification_dict is None:
                logger.warning(f"JSON parsing failed, attempting partial field extraction from: {response_text[:200]}")
                partial = {}
                # Extract company_name
                cn_match = re.search(r'"company_name"\s*:\s*"([^"]+)"', response_text)
                if cn_match:
                    partial['company_name'] = cn_match.group(1)
                # Extract primary_intent
                pi_match = re.search(r'"primary_intent"\s*:\s*"([^"]+)"', response_text)
                if pi_match:
                    partial['primary_intent'] = pi_match.group(1)
                # Extract required_agents
                ra_match = re.search(r'"required_agents"\s*:\s*\[([^\]]+)\]', response_text)
                if ra_match:
                    partial['required_agents'] = [a.strip().strip('"') for a in ra_match.group(1).split(',')]
                # Extract confidence
                conf_match = re.search(r'"confidence"\s*:\s*([\d.]+)', response_text)
                if conf_match:
                    partial['confidence'] = float(conf_match.group(1))

                if partial.get('primary_intent'):
                    classification_dict = partial
                    logger.info(f"Recovered partial classification: intent={partial.get('primary_intent')}, company={partial.get('company_name')}")

            if classification_dict is None:
                logger.warning(f"Could not extract any classification from LLM response")
                return self._fallback_classification(query)

            # Validate required fields
            primary_intent = classification_dict.get('primary_intent', 'information_retrieval')
            required_agents = classification_dict.get('required_agents', ['rag'])

            # Ensure RAG is always in required agents
            if 'rag' not in required_agents:
                required_agents.insert(0, 'rag')

            return IntentClassification(
                primary_intent=primary_intent,
                secondary_intents=classification_dict.get('secondary_intents', []),
                required_agents=required_agents,
                optional_agents=classification_dict.get('optional_agents', []),
                company_name=classification_dict.get('company_name'),
                data_quality_requirements=classification_dict.get('data_quality_requirements', {
                    'min_confidence': 0.3,
                    'min_chunks': 2
                }),
                priority_level=classification_dict.get('priority_level', 'normal'),
                confidence=float(classification_dict.get('confidence', 0.8)),
                reasoning=classification_dict.get('reasoning', 'LLM classification')
            )

        except Exception as e:
            logger.error(f"LLM classification failed: {str(e)}")
            return self._fallback_classification(query)

    def _extract_company_name(self, query: str) -> Optional[str]:
        """Extract company name from query using simple heuristics (case-insensitive)."""
        # Common stop words that are NOT company names
        stop_words = {
            'what', 'how', 'when', 'where', 'why', 'show', 'tell', 'give', 'any',
            'the', 'find', 'get', 'scrap', 'scrape', 'search', 'fetch', 'latest',
            'news', 'and', 'is', 'are', 'was', 'were', 'has', 'have', 'with',
            'from', 'that', 'this', 'about', 'me', 'on', 'for', 'of', 'create',
            'short', 'specific', 'chat', 'title', 'words', 'user', 'message',
            'return', 'only', 'text', 'sentiment', 'market', 'company', 'analysis',
            'including', 'include', 'includes', 'especially', 'particularly',
            'detailed', 'detail', 'details', 'also', 'please', 'can', 'could',
            'would', 'should', 'their', 'its', 'my', 'your', 'some', 'all',
            'do', 'does', 'did', 'will', 'shall', 'may', 'might',
            'financial', 'financials', 'alert', 'alerts', 'risk', 'risks',
            'performance', 'overview', 'summary', 'report', 'data',
        }

        # Pattern 1: "on/about/for <name> and ..."
        patterns = [
            r'(?:on|about|for|of|regarding)\s+(\w[\w\s]*?)(?:\s+and\s+|\s+tell\s+|\s+show\s+|\s+give\s+|$)',
            r'(?:news|sentiment|analysis|financials|alerts)\s+(?:on|of|for|about)\s+(\w[\w\s]*?)(?:\s+and\s+|\s+tell\s+|$)',
            r'(?:scrap|scrape|fetch)\s+(?:latest\s+)?(?:news\s+)?(?:on|for|about)\s+(\w[\w\s]*?)(?:\s+and\s+|\s+tell\s+|$)',
        ]
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Remove trailing stop words
                words = name.split()
                while words and words[-1].lower() in stop_words:
                    words.pop()
                # Remove leading stop words
                while words and words[0].lower() in stop_words:
                    words.pop(0)
                name = ' '.join(words)
                if name and name.lower() not in stop_words and len(name) > 1:
                    # Title-case the extracted name
                    return name.title()

        return None

    def _fallback_classification(self, query: str) -> IntentClassification:
        """
        Fallback classification when LLM fails.
        Conservative approach: include all agents unless clearly not needed.
        """
        keyword_scores = self._extract_intent_patterns(query)

        # Determine primary intent from keyword scores
        primary_intent = max(keyword_scores, key=keyword_scores.get) if keyword_scores else 'information_retrieval'

        # Conservative agent selection
        required_agents = ['rag']  # RAG always required
        optional_agents = []

        # Add financial agent if query mentions financial keywords
        if keyword_scores.get('financial_analysis', 0) > 0.2:
            required_agents.append('financial')

        # Add alert agent if query mentions risk keywords
        if keyword_scores.get('risk_assessment', 0) > 0.2:
            required_agents.append('alert')

        # Add sentiment agent if query mentions sentiment/news keywords
        if keyword_scores.get('sentiment_analysis', 0) > 0.2:
            required_agents.append('sentiment')

        # Extract company name
        company_name = self._extract_company_name(query)

        return IntentClassification(
            primary_intent=primary_intent,
            secondary_intents=[],
            required_agents=required_agents,
            optional_agents=optional_agents,
            company_name=company_name,
            data_quality_requirements={
                'min_confidence': 0.3,
                'min_chunks': 2
            },
            priority_level='normal',
            confidence=max(keyword_scores.values()) if keyword_scores else 0.5,
            reasoning='Fallback classification from keyword patterns'
        )

    def assess_data_quality_requirements(self, intent: IntentClassification) -> Dict[str, float]:
        """
        Determine data quality thresholds based on intent.

        Returns:
            Dict with quality requirements (min_confidence, min_chunks, etc.)
        """
        requirements = {
            'min_confidence': 0.3,  # Default minimum confidence score
            'min_chunks': 2,        # Minimum number of context chunks
            'min_summary_length': 50  # Minimum summary length in characters
        }

        # Adjust based on intent priority
        if intent.priority_level == 'critical':
            requirements['min_confidence'] = 0.7
            requirements['min_chunks'] = 3
            requirements['min_summary_length'] = 200

        elif intent.priority_level == 'high':
            requirements['min_confidence'] = 0.6
            requirements['min_chunks'] = 3
            requirements['min_summary_length'] = 150

        elif intent.priority_level == 'low':
            requirements['min_confidence'] = 0.2
            requirements['min_chunks'] = 1
            requirements['min_summary_length'] = 30

        # Adjust based on intent type
        if intent.primary_intent == 'financial_analysis':
            requirements['min_confidence'] = max(requirements['min_confidence'], 0.6)
            requirements['min_chunks'] = max(requirements['min_chunks'], 3)

        elif intent.primary_intent == 'risk_assessment':
            requirements['min_confidence'] = max(requirements['min_confidence'], 0.5)

        return requirements
