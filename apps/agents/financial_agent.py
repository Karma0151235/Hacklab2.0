"""
Financial Agent for Market Intelligence
Calculates 10+ key financial metrics from PDF data and provides CoT analysis
"""

from typing import Dict, Any, Optional
import sys
from pathlib import Path
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

import openai

from agents.schemas import (
    FinancialAgentInput,
    FinancialAgentOutput,
    FinancialMetrics,
)
from agents.config import AgentConfig
from etl.logging_config import get_logger

logger = get_logger(__name__)


class FinancialAgent:
    """
    Financial Agent for calculating and analyzing financial metrics

    System Prompt:
    You are the Financial Agent.

    Process PDFs or structured data from ETL/Postgres to calculate key financial metrics.

    Key metrics to extract and calculate (≥10):

    Liquidity Ratios:
    - Current Ratio
    - Quick Ratio

    Solvency Ratios:
    - Debt-to-Equity
    - Interest Coverage

    Profitability Ratios:
    - Net Profit Margin
    - Return on Assets (ROA)
    - Return on Equity (ROE)

    Efficiency Ratios:
    - Asset Turnover
    - Inventory Turnover

    Growth Indicators:
    - Revenue Growth YoY
    - EPS Growth

    Output feeds both Supervisor and Alert agents.
    """

    SYSTEM_PROMPT = """You are the Financial Agent for market intelligence.

Your role:
1. Extract financial data from context (tables, text)
2. Calculate key financial metrics:
   - Liquidity Ratios (Current Ratio, Quick Ratio)
   - Solvency Ratios (Debt-to-Equity, Interest Coverage)
   - Profitability Ratios (Net Profit Margin, ROA, ROE, Gross Profit Margin, Operating Profit Margin)
   - Efficiency Ratios (Asset Turnover, Inventory Turnover)
   - Growth Indicators (Revenue Growth YoY, EPS Growth)
3. Apply Chain-of-Thought reasoning to analyze trends
4. Provide evidence-based analysis with source references

Always show your calculation steps and assumptions."""

    def __init__(self):
        """Initialize Financial Agent"""
        self.config = AgentConfig

        # Initialize OpenRouter client
        self.client = openai.OpenAI(
            api_key=self.config.OPENROUTER_API_KEY,
            base_url=self.config.OPENROUTER_BASE_URL,
            timeout=self.config.OPENROUTER_TIMEOUT_SECONDS,
            max_retries=self.config.OPENROUTER_MAX_RETRIES,
        )

        logger.info("Financial Agent initialized")

    def analyze(self, input_data: FinancialAgentInput) -> FinancialAgentOutput:
        """
        Analyze financial data and calculate metrics

        Args:
            input_data: FinancialAgentInput with query and context

        Returns:
            FinancialAgentOutput with calculated metrics and analysis
        """
        try:
            logger.info(f"Financial Agent analyzing: {input_data.query}")

            # Extract financial data from context using LLM
            financial_data = self._extract_financial_data(input_data)

            # Calculate metrics
            metrics = self._calculate_metrics(financial_data)

            # Generate analysis with CoT reasoning
            analysis = self._generate_analysis(input_data.query, financial_data, metrics)

            # Determine source
            source = self._extract_source(input_data.context)

            output = FinancialAgentOutput(
                metrics=metrics,
                source=source,
                analysis=analysis
            )

            logger.info("Financial Agent completed analysis")
            return output

        except Exception as e:
            logger.error(f"Financial Agent error: {str(e)}")
            return FinancialAgentOutput(
                metrics=FinancialMetrics(),
                source="Unknown",
                analysis=f"Error analyzing financial data: {str(e)}"
            )

    def _extract_financial_data(self, input_data: FinancialAgentInput) -> Dict[str, Any]:
        """Extract financial data from context using LLM"""
        try:
            context_str = str(input_data.context) if input_data.context else "No context provided"

            prompt = f"""Extract financial data from the following context to calculate financial metrics.

Context:
{context_str}

Query: {input_data.query}

Extract the following data (if available):
1. Revenue (current period and previous period)
2. Net Profit / Profit for Period
3. Gross Profit
4. Operating Profit
5. Total Assets
6. Current Assets
7. Total Equity
8. Total Liabilities
9. Current Liabilities
10. Total Debt
11. Inventory
12. Interest Expense
13. Earnings Per Share (EPS) - current and previous
14. Number of shares outstanding

Format your response as JSON with these keys.
Use null for unavailable values.
Include the currency if mentioned."""

            response = self.client.chat.completions.create(
                model=self.config.GLM_4_5_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Deterministic for data extraction
                max_tokens=2000,
                extra_body={"reasoning": {"enabled": True}}
            )

            content = response.choices[0].message.content

            # Parse JSON response
            import json
            try:
                # Extract JSON from response (handle markdown code blocks)
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    json_str = content.split("```")[1].split("```")[0].strip()
                else:
                    json_str = content.strip()

                financial_data = json.loads(json_str)
                return financial_data
            except:
                logger.warning("Failed to parse financial data as JSON")
                return {}

        except Exception as e:
            logger.error(f"Error extracting financial data: {str(e)}")
            return {}

    def _calculate_metrics(self, data: Dict[str, Any]) -> FinancialMetrics:
        """Calculate financial metrics from extracted data"""
        metrics = FinancialMetrics()

        try:
            # Helper to safely get numeric value
            def get_num(key: str) -> Optional[float]:
                val = data.get(key)
                if val is None or val == "null":
                    return None
                try:
                    return float(val)
                except:
                    return None

            # Extract values
            revenue = get_num("Revenue")
            revenue_prev = get_num("Revenue_previous")
            net_profit = get_num("Net Profit")
            gross_profit = get_num("Gross Profit")
            operating_profit = get_num("Operating Profit")
            total_assets = get_num("Total Assets")
            current_assets = get_num("Current Assets")
            total_equity = get_num("Total Equity")
            total_liabilities = get_num("Total Liabilities")
            current_liabilities = get_num("Current Liabilities")
            total_debt = get_num("Total Debt")
            inventory = get_num("Inventory")
            interest_expense = get_num("Interest Expense")
            eps = get_num("Earnings Per Share")
            eps_prev = get_num("Earnings Per Share_previous")

            # Liquidity Ratios
            if current_assets and current_liabilities and current_liabilities != 0:
                metrics.current_ratio = round(current_assets / current_liabilities, 2)

            if current_assets and inventory and current_liabilities and current_liabilities != 0:
                metrics.quick_ratio = round((current_assets - inventory) / current_liabilities, 2)

            # Solvency Ratios
            if total_debt and total_equity and total_equity != 0:
                metrics.debt_to_equity = round(total_debt / total_equity, 2)

            if operating_profit and interest_expense and interest_expense != 0:
                metrics.interest_coverage = round(operating_profit / interest_expense, 2)

            # Profitability Ratios
            if net_profit and revenue and revenue != 0:
                metrics.net_profit_margin = round((net_profit / revenue) * 100, 2)

            if gross_profit and revenue and revenue != 0:
                metrics.gross_profit_margin = round((gross_profit / revenue) * 100, 2)

            if operating_profit and revenue and revenue != 0:
                metrics.operating_profit_margin = round((operating_profit / revenue) * 100, 2)

            if net_profit and total_assets and total_assets != 0:
                metrics.return_on_assets = round((net_profit / total_assets) * 100, 2)

            if net_profit and total_equity and total_equity != 0:
                metrics.return_on_equity = round((net_profit / total_equity) * 100, 2)

            # Efficiency Ratios
            if revenue and total_assets and total_assets != 0:
                metrics.asset_turnover = round(revenue / total_assets, 2)

            if revenue and inventory and inventory != 0:
                # Using revenue as proxy for COGS if not available
                metrics.inventory_turnover = round(revenue / inventory, 2)

            # Growth Indicators
            if revenue and revenue_prev and revenue_prev != 0:
                metrics.revenue_growth_yoy = round(((revenue - revenue_prev) / revenue_prev) * 100, 2)

            if eps and eps_prev and eps_prev != 0:
                metrics.eps_growth = round(((eps - eps_prev) / eps_prev) * 100, 2)

            # Additional Metrics
            if eps:
                metrics.earnings_per_share = round(eps, 2)

            logger.info(f"Calculated {sum(1 for k, v in metrics.dict().items() if v is not None)} metrics")

        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")

        return metrics

    def _generate_analysis(self, query: str, data: Dict, metrics: FinancialMetrics) -> str:
        """Generate financial analysis with CoT reasoning"""
        try:
            metrics_dict = {k: v for k, v in metrics.dict().items() if v is not None}

            prompt = f"""Based on the extracted financial data and calculated metrics, provide a comprehensive financial analysis using Chain-of-Thought reasoning.

Query: {query}

Extracted Financial Data:
{data}

Calculated Metrics:
{metrics_dict}

Provide:
1. Step-by-step analysis of key metrics
2. Assessment of financial health (liquidity, solvency, profitability)
3. Identification of trends or concerns
4. Actionable insights

Be specific and reference exact figures."""

            response = self.client.chat.completions.create(
                model=self.config.GLM_4_5_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.TEMPERATURE,
                max_tokens=2000,
                extra_body={"reasoning": {"enabled": True}}
            )

            analysis = response.choices[0].message.content
            return analysis

        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}")
            return f"Analysis generation failed: {str(e)}"

    def _extract_source(self, context: Optional[Dict[str, Any]]) -> str:
        """Extract source reference from context"""
        if not context:
            return "Unknown"

        # Try to extract filename from metadata
        if isinstance(context, dict):
            if "metadata" in context:
                metadata = context["metadata"]
                if isinstance(metadata, list) and len(metadata) > 0:
                    return metadata[0].get("filename", "Unknown")

        return "Context provided"
