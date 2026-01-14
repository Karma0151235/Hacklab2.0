"""
Alert Agent for Market Intelligence
Evaluates alerts based on keywords, sentiment, filing types, and financial thresholds
"""

from typing import List, Dict, Any
import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

import openai

from agents.schemas import (
    AlertAgentInput,
    AlertAgentOutput,
    Alert,
    AlertConfig,
    FinancialMetrics,
    RAGOutput,
)
from agents.config import AgentConfig
from etl.logging_config import get_logger

logger = get_logger(__name__)


class AlertAgent:
    """
    Alert Agent for evaluating market intelligence alerts

    System Prompt:
    You are the Alert Agent.

    Evaluate alerts based on:
    • Keywords in filings/news
    • Sentiment shifts (positive/adverse)
    • Filing type
    • Financial thresholds (≥10 key metrics from Financial Agent)

    Return only active alerts relevant to the query.
    """

    SYSTEM_PROMPT = """You are the Alert Agent for market intelligence.

Your role:
1. Evaluate financial thresholds against configured limits
2. Detect adverse keywords in content
3. Analyze sentiment shifts in text
4. Identify high-risk filing types
5. Generate prioritized alerts (high, medium, low severity)

Only return alerts that are:
- Actionable
- Evidence-based
- Relevant to the query

Be specific about what triggered each alert."""

    # Alert keywords
    ADVERSE_KEYWORDS = [
        "loss", "losses", "decline", "decreased", "impairment", "default",
        "breach", "violation", "investigation", "litigation", "lawsuit",
        "restructuring", "bankruptcy", "insolvency", "downgrade",
        "adverse", "negative", "concern", "risk", "material weakness"
    ]

    HIGH_RISK_FILING_TYPES = [
        "financial_results_adverse",
        "investigation",
        "default_notice",
        "material_weakness",
        "going_concern"
    ]

    def __init__(self):
        """Initialize Alert Agent"""
        self.config = AgentConfig

        # Initialize OpenRouter client
        self.client = openai.OpenAI(
            api_key=self.config.OPENROUTER_API_KEY,
            base_url=self.config.OPENROUTER_BASE_URL
        )

        logger.info("Alert Agent initialized")

    def evaluate(self, input_data: AlertAgentInput) -> AlertAgentOutput:
        """
        Evaluate alerts based on financial metrics and context

        Args:
            input_data: AlertAgentInput with query, metrics, context, and config

        Returns:
            AlertAgentOutput with triggered alerts and related metrics
        """
        try:
            logger.info(f"Alert Agent evaluating: {input_data.query}")

            alerts = []
            related_metrics = {}

            # Evaluate financial thresholds
            if input_data.financial_metrics:
                threshold_alerts, threshold_metrics = self._evaluate_thresholds(
                    input_data.financial_metrics,
                    input_data.config
                )
                alerts.extend(threshold_alerts)
                related_metrics.update(threshold_metrics)

            # Evaluate keywords and sentiment
            if input_data.rag_context:
                keyword_alerts = self._evaluate_keywords(input_data.rag_context)
                alerts.extend(keyword_alerts)

                sentiment_alerts = self._evaluate_sentiment(input_data.rag_context, input_data.query)
                alerts.extend(sentiment_alerts)

            # Sort alerts by severity
            severity_order = {"high": 0, "medium": 1, "low": 2}
            alerts.sort(key=lambda x: severity_order.get(x.severity, 3))

            output = AlertAgentOutput(
                alerts=alerts,
                related_metrics=related_metrics
            )

            logger.info(f"Alert Agent generated {len(alerts)} alerts")
            return output

        except Exception as e:
            logger.error(f"Alert Agent error: {str(e)}")
            return AlertAgentOutput(alerts=[], related_metrics={})

    def _evaluate_thresholds(
        self,
        metrics: FinancialMetrics,
        config: AlertConfig
    ) -> tuple[List[Alert], Dict[str, float]]:
        """Evaluate financial metric thresholds"""
        alerts = []
        related_metrics = {}

        # Current Ratio
        if metrics.current_ratio is not None:
            related_metrics["Current Ratio"] = metrics.current_ratio
            if metrics.current_ratio < config.current_ratio_min:
                alerts.append(Alert(
                    alert_type="threshold",
                    severity="high",
                    message=f"Current Ratio ({metrics.current_ratio}) below minimum threshold ({config.current_ratio_min})",
                    triggered_by=f"Current Ratio: {metrics.current_ratio}"
                ))

        # Debt-to-Equity
        if metrics.debt_to_equity is not None:
            related_metrics["Debt-to-Equity"] = metrics.debt_to_equity
            if metrics.debt_to_equity > config.debt_to_equity_max:
                alerts.append(Alert(
                    alert_type="threshold",
                    severity="high",
                    message=f"Debt-to-Equity ({metrics.debt_to_equity}) exceeds maximum threshold ({config.debt_to_equity_max})",
                    triggered_by=f"Debt-to-Equity: {metrics.debt_to_equity}"
                ))

        # Net Profit Margin
        if metrics.net_profit_margin is not None:
            related_metrics["Net Profit Margin"] = metrics.net_profit_margin
            if metrics.net_profit_margin < config.net_profit_margin_min:
                severity = "high" if metrics.net_profit_margin < 0 else "medium"
                alerts.append(Alert(
                    alert_type="threshold",
                    severity=severity,
                    message=f"Net Profit Margin ({metrics.net_profit_margin}%) below minimum threshold ({config.net_profit_margin_min}%)",
                    triggered_by=f"Net Profit Margin: {metrics.net_profit_margin}%"
                ))

        # Revenue Growth
        if metrics.revenue_growth_yoy is not None:
            related_metrics["Revenue Growth YoY"] = metrics.revenue_growth_yoy
            if metrics.revenue_growth_yoy < config.revenue_growth_min:
                alerts.append(Alert(
                    alert_type="threshold",
                    severity="medium",
                    message=f"Revenue Growth YoY ({metrics.revenue_growth_yoy}%) below threshold ({config.revenue_growth_min}%)",
                    triggered_by=f"Revenue Growth YoY: {metrics.revenue_growth_yoy}%"
                ))

        # ROA
        if metrics.return_on_assets is not None:
            related_metrics["Return on Assets"] = metrics.return_on_assets
            if metrics.return_on_assets < 0:
                alerts.append(Alert(
                    alert_type="threshold",
                    severity="medium",
                    message=f"Negative Return on Assets ({metrics.return_on_assets}%)",
                    triggered_by=f"ROA: {metrics.return_on_assets}%"
                ))

        # ROE
        if metrics.return_on_equity is not None:
            related_metrics["Return on Equity"] = metrics.return_on_equity
            if metrics.return_on_equity < 0:
                alerts.append(Alert(
                    alert_type="threshold",
                    severity="medium",
                    message=f"Negative Return on Equity ({metrics.return_on_equity}%)",
                    triggered_by=f"ROE: {metrics.return_on_equity}%"
                ))

        # Interest Coverage
        if metrics.interest_coverage is not None:
            related_metrics["Interest Coverage"] = metrics.interest_coverage
            if metrics.interest_coverage < 1.5:
                alerts.append(Alert(
                    alert_type="threshold",
                    severity="high",
                    message=f"Low Interest Coverage ({metrics.interest_coverage}x) - risk of debt servicing issues",
                    triggered_by=f"Interest Coverage: {metrics.interest_coverage}x"
                ))

        # EPS Growth
        if metrics.eps_growth is not None:
            related_metrics["EPS Growth"] = metrics.eps_growth
            if metrics.eps_growth < -10:
                alerts.append(Alert(
                    alert_type="threshold",
                    severity="medium",
                    message=f"Significant EPS decline ({metrics.eps_growth}%)",
                    triggered_by=f"EPS Growth: {metrics.eps_growth}%"
                ))

        return alerts, related_metrics

    def _evaluate_keywords(self, rag_context: RAGOutput) -> List[Alert]:
        """Evaluate adverse keywords in content"""
        alerts = []

        # Check summary for adverse keywords
        summary_lower = rag_context.summary.lower()
        found_keywords = []

        for keyword in self.ADVERSE_KEYWORDS:
            if keyword in summary_lower:
                found_keywords.append(keyword)

        if found_keywords:
            alerts.append(Alert(
                alert_type="keyword",
                severity="medium",
                message=f"Adverse keywords detected: {', '.join(found_keywords[:5])}",
                triggered_by=f"Keywords: {', '.join(found_keywords[:5])}"
            ))

        return alerts

    def _evaluate_sentiment(self, rag_context: RAGOutput, query: str) -> List[Alert]:
        """Evaluate sentiment using LLM"""
        try:
            prompt = f"""Analyze the sentiment of the following content in the context of the query.

Query: {query}

Content:
{rag_context.summary}

Determine:
1. Overall sentiment (positive, neutral, negative)
2. Sentiment score (-1.0 to 1.0)
3. Key factors influencing sentiment
4. Whether this represents a material adverse change

Format response as JSON:
{{
  "sentiment": "positive|neutral|negative",
  "score": -1.0 to 1.0,
  "factors": ["factor1", "factor2"],
  "is_adverse": true/false
}}"""

            response = self.client.chat.completions.create(
                model=self.config.GLM_4_5_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500
            )

            content = response.choices[0].message.content

            # Parse JSON response
            import json
            try:
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content.strip()

                sentiment_data = json.loads(json_str)

                if sentiment_data.get("is_adverse") and sentiment_data.get("score", 0) < -0.3:
                    alerts = [Alert(
                        alert_type="sentiment",
                        severity="high" if sentiment_data.get("score", 0) < -0.6 else "medium",
                        message=f"Adverse sentiment detected (score: {sentiment_data.get('score', 0):.2f})",
                        triggered_by=f"Factors: {', '.join(sentiment_data.get('factors', [])[:3])}"
                    )]
                    return alerts

            except Exception as e:
                logger.warning(f"Failed to parse sentiment response: {str(e)}")

        except Exception as e:
            logger.error(f"Error evaluating sentiment: {str(e)}")

        return []
