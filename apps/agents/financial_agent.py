"""
Financial Agent V2 - Tool-Based Metric Calculation
Extracts financial data from context and uses deterministic tools for calculations
Never hallucinates values - only calculates from extracted data
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import json
import re

import openai

from agents.schemas import (
    FinancialAgentInput,
    FinancialAgentOutput,
    FinancialMetrics,
    FinancialAgentRouting,
    ExtractedFinancialData,
)
from agents.config import AgentConfig
from agents.tools.financial_metrics import FinancialMetricsCalculator, MetricStatus, MetricResult
from etl.logging_config import get_logger

logger = get_logger(__name__)


class FinancialAgent:
    """
    Financial Analysis Agent using Tool-Based Calculations

    Process:
    1. Extract financial figures from RAG context using LLM
    2. Validate extracted data
    3. Use FinancialMetricsCalculator tools for all metric calculations
    4. Skip metrics that cannot be calculated (never hallucinate)
    5. Generate structured analysis with extracted values and calculations
    6. Determine routing (complete/partial/skip)
    """

    SYSTEM_PROMPT = """You are extracting financial data from Malaysian Bursa company announcements.

PRIORITY EXTRACTION (look for these first - almost always present):
- Revenue / Operating Revenue (in RM millions)
- Profit for the period / Net Income / Profit after tax
- Earnings Per Share (EPS)
- Total Assets, Total Equity, Total Liabilities
- Current Assets, Current Liabilities (if available)

SECONDARY DATA (extract if clearly stated):
- Gross Profit
- Operating Profit / Operating Income
- Interest Expense
- Shares Outstanding
- Inventory (if applicable)
- Accounts Receivable (if applicable)

COMPARATIVE DATA (extract if this is a comparative period):
- Previous period revenue
- Previous period net income
- Previous period EPS

Return ONLY this JSON structure with explicitly stated values:
{
  "extracted_values": {
    "revenue": number or null,
    "net_income": number or null,
    "earnings_per_share": number or null,
    "total_assets": number or null,
    "equity": number or null,
    "current_assets": number or null,
    "current_liabilities": number or null,
    "total_debt": number or null,
    "gross_profit": number or null,
    "operating_profit": number or null,
    "interest_expense": number or null,
    "shares_outstanding": number or null,
    "inventory": number or null,
    "accounts_receivable": number or null,
    "previous_revenue": number or null,
    "previous_net_income": number or null,
    "previous_eps": number or null
  },
  "period": "string (e.g., 'Q1 2025', 'FY2024')",
  "currency": "RM",
  "confidence": number (0.0-1.0),
  "data_quality_issues": ["string", ...]
}

CRITICAL RULES:
- ONLY extract values explicitly shown in the document
- NEVER estimate, calculate, or infer values
- If uncertain about a value, return null
- Currency is assumed RM unless explicitly stated otherwise
- Mark low confidence if data is ambiguous or incomplete
- List all data quality concerns (missing periods, unit inconsistencies, etc.)"""

    def __init__(self):
        """Initialize Financial Agent with OpenRouter client and calculator"""
        self.client = openai.OpenAI(
            api_key=AgentConfig.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = AgentConfig.GLM_4_5_MODEL
        self.calculator = FinancialMetricsCalculator()

    def analyze(self, input_data: FinancialAgentInput) -> FinancialAgentOutput:
        """
        Analyze financial data using tool-based calculations.

        Process:
        1. Extract financial figures from context
        2. Validate extracted data
        3. Calculate metrics using tools
        4. Generate analysis
        5. Return output with routing decision
        """
        try:
            logger.info(f"Starting financial analysis for query: {input_data.query[:80]}...")

            # Step 1: Extract financial data from context
            extracted_data = self._extract_financial_data_with_validation(input_data)

            logger.debug(f"Extracted {len(extracted_data.extracted_values)} financial figures")

            # Step 2: Calculate metrics using tools
            metrics, metric_results = self.calculator.calculate_all_available(
                extracted_data.extracted_values
            )

            # Step 3: Generate analysis
            analysis = self._generate_structured_analysis(
                query=input_data.query,
                extracted_data=extracted_data,
                metrics=metrics,
                metric_results=metric_results
            )

            # Step 4: Create output
            output = FinancialAgentOutput(
                metrics=metrics,
                source=extracted_data.extraction_status,
                analysis=analysis
            )

            logger.info(f"Financial analysis complete - {len([m for m in metrics.dict().values() if m])} metrics calculated")

            return output

        except Exception as e:
            logger.error(f"Financial analysis failed: {str(e)}")
            # Return empty metrics with error message
            return FinancialAgentOutput(
                metrics=FinancialMetrics(),
                source="error",
                analysis=f"Financial analysis failed: {str(e)}"
            )

    def _extract_financial_data_with_validation(
        self, input_data: FinancialAgentInput
    ) -> ExtractedFinancialData:
        """
        Extract and validate financial data from RAG context.

        Uses LLM to identify explicit financial figures in the context.
        Never estimates or hallucинates values.

        Returns:
            ExtractedFinancialData with extracted values and quality assessment
        """
        try:
            # Prepare context for extraction
            context = input_data.context or {}
            rag_output = context.get('rag_output')

            if not rag_output:
                return ExtractedFinancialData(
                    extracted_values={},
                    missing_fields=[],
                    data_quality=0.0,
                    extraction_confidence=0.0,
                    extraction_status="error",
                    extraction_errors=["No RAG context provided"]
                )

            # Build extraction prompt with both text summary and tables
            if isinstance(rag_output, dict):
                context_text = rag_output.get('summary', '')
                table_chunks = rag_output.get('table_chunks', [])
            else:
                context_text = rag_output.summary
                table_chunks = rag_output.table_chunks or []

            # Format tables for extraction
            table_text = ""
            if table_chunks:
                table_text = "\n\n=== FINANCIAL TABLES ===\n"
                for i, table in enumerate(table_chunks):
                    if isinstance(table, dict):
                        table_data = table.get('table_data', [])
                    else:
                        table_data = table.table_data if hasattr(table, 'table_data') else []

                    if table_data:
                        table_text += f"\nTable {i+1}:\n"
                        for row in table_data:
                            if isinstance(row, list):
                                table_text += " | ".join(str(cell) for cell in row) + "\n"
                            else:
                                table_text += str(row) + "\n"

            extraction_prompt = f"""Extract financial figures from the following content:

NARRATIVE TEXT:
{context_text}

{table_text}

Return valid JSON only, no explanations."""

            # Call LLM for extraction
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.0,  # Deterministic extraction
                max_tokens=1000,
                extra_body={"reasoning": {"enabled": True}}
            )

            response_text = response.choices[0].message.content

            # Parse JSON response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                logger.warning(f"Could not extract JSON from LLM response: {response_text[:200]}")
                return ExtractedFinancialData(
                    extracted_values={},
                    extraction_status="error",
                    extraction_errors=["Failed to parse LLM response"]
                )

            extraction_result = json.loads(json_match.group())

            # Validate extracted values
            extracted_values = {}
            for key, value in extraction_result.get('extracted_values', {}).items():
                if value is not None and isinstance(value, (int, float)):
                    extracted_values[key] = float(value)

            # Determine missing fields
            expected_fields = [
                'revenue', 'net_profit', 'net_income', 'gross_profit',
                'operating_income', 'current_assets', 'total_assets',
                'current_liabilities', 'total_debt', 'equity',
                'inventory', 'interest_expense', 'shares_outstanding'
            ]
            missing_fields = [f for f in expected_fields if f not in extracted_values]

            # Calculate data quality
            completeness = (len(extracted_values) / len(expected_fields)) if expected_fields else 0
            confidence = float(extraction_result.get('confidence', 0.5))
            data_quality = (completeness * 0.6) + (confidence * 0.4)

            return ExtractedFinancialData(
                extracted_values=extracted_values,
                missing_fields=missing_fields,
                data_quality=data_quality,
                extraction_confidence=confidence,
                extraction_status="success",
                extraction_errors=extraction_result.get('data_quality_issues', [])
            )

        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            return ExtractedFinancialData(
                extracted_values={},
                extraction_status="error",
                extraction_errors=[str(e)]
            )

    def _generate_structured_analysis(
        self,
        query: str,
        extracted_data: ExtractedFinancialData,
        metrics: FinancialMetrics,
        metric_results: Dict[str, MetricResult]
    ) -> str:
        """
        Generate structured analysis using only extracted and calculated values.

        Shows:
        - Extracted figures with sources
        - Calculated metrics with formulas
        - Interpretations based on benchmarks
        - Missing data and limitations
        """
        try:
            analysis_parts = []

            # Header
            analysis_parts.append("## Financial Analysis Report\n")

            # Extracted Data Summary
            if extracted_data.extracted_values:
                analysis_parts.append("### Extracted Financial Data\n")
                for key, value in extracted_data.extracted_values.items():
                    analysis_parts.append(f"- {key}: RM {value:,.2f}")
                analysis_parts.append("")

            # Data Quality Notes
            if extracted_data.extraction_errors:
                analysis_parts.append("### Data Quality Notes\n")
                for error in extracted_data.extraction_errors:
                    analysis_parts.append(f"- {error}")
                analysis_parts.append("")

            # Calculated Metrics
            calculated_metrics = [k for k, v in metric_results.items() if v.status == MetricStatus.SUCCESS]
            if calculated_metrics:
                analysis_parts.append("### Calculated Metrics\n")
                for metric_name in calculated_metrics:
                    result = metric_results[metric_name]
                    if result.value is not None:
                        analysis_parts.append(f"- **{metric_name}**: {result.value:.2f}")
                        if result.interpretation:
                            analysis_parts.append(f"  - Interpretation: {result.interpretation}")
                        if result.benchmark:
                            analysis_parts.append(f"  - Benchmark: {result.benchmark:.2f}")
                analysis_parts.append("")

            # Missing Metrics
            skipped_metrics = [k for k, v in metric_results.items() if v.status == MetricStatus.INSUFFICIENT_DATA]
            if skipped_metrics:
                analysis_parts.append("### Metrics Not Calculated (Insufficient Data)\n")
                for metric_name in skipped_metrics:
                    analysis_parts.append(f"- {metric_name}")
                analysis_parts.append("")

            # Key Insights
            analysis_parts.append("### Key Insights\n")
            if len(calculated_metrics) > 0:
                analysis_parts.append(f"- Successfully calculated {len(calculated_metrics)} financial metrics")
            if extracted_data.missing_fields:
                analysis_parts.append(f"- {len(extracted_data.missing_fields)} data fields were not found in the source")
            if extracted_data.data_quality < 0.5:
                analysis_parts.append("- Data completeness is low; consider requesting full financial statements")

            analysis_parts.append("")

            # Limitations
            analysis_parts.append("### Limitations\n")
            analysis_parts.append("- Only metrics derived from explicitly extracted data are reported")
            analysis_parts.append("- No estimates or inferred values are included")
            if extracted_data.extraction_confidence < 0.8:
                analysis_parts.append("- Low extraction confidence; verify source data")

            return "\n".join(analysis_parts)

        except Exception as e:
            logger.error(f"Analysis generation failed: {str(e)}")
            return f"Error generating analysis: {str(e)}"

    def route(self, output: FinancialAgentOutput) -> FinancialAgentRouting:
        """
        Route financial analysis results based on metric QUALITY, not just count.

        Weights critical metrics (liquidity, leverage, profitability) higher than optional ones.

        Determines:
        - Status: complete, partial, skip
        - Whether to proceed with Alert Agent
        - Recommended next step
        """
        metrics_dict = output.metrics.dict()
        calculated_metrics = [k for k, v in metrics_dict.items() if v is not None]
        metrics_count = len(calculated_metrics)

        # Weight metrics by importance for financial health assessment
        critical_metrics = {
            'net_profit_margin': metrics_dict.get('net_profit_margin'),
            'current_ratio': metrics_dict.get('current_ratio'),
            'debt_to_equity': metrics_dict.get('debt_to_equity'),
        }

        growth_metrics = {
            'revenue_growth_yoy': metrics_dict.get('revenue_growth_yoy'),
            'eps_growth': metrics_dict.get('eps_growth'),
        }

        profitability_metrics = {
            'gross_profit_margin': metrics_dict.get('gross_profit_margin'),
            'operating_profit_margin': metrics_dict.get('operating_profit_margin'),
            'return_on_assets': metrics_dict.get('return_on_assets'),
            'return_on_equity': metrics_dict.get('return_on_equity'),
        }

        # Score calculation
        critical_count = sum(1 for v in critical_metrics.values() if v is not None)
        growth_count = sum(1 for v in growth_metrics.values() if v is not None)
        profitability_count = sum(1 for v in profitability_metrics.values() if v is not None)

        # Weighted score: critical=60%, profitability=30%, growth=10%
        critical_score = (critical_count / len(critical_metrics)) * 0.6 if critical_metrics else 0
        profitability_score = (profitability_count / len(profitability_metrics)) * 0.3 if profitability_metrics else 0
        growth_score = (growth_count / len(growth_metrics)) * 0.1 if growth_metrics else 0

        overall_score = critical_score + profitability_score + growth_score

        # Determine status based on weighted score
        if overall_score >= 0.75:  # At least 2 critical + some additional
            status = "complete"
            should_continue = True
            recommendation = "analyze_fully"
        elif overall_score >= 0.4 or critical_count >= 1:  # At least 1 critical metric
            status = "partial"
            should_continue = True
            recommendation = "partial_analysis"
        else:
            status = "skip"
            should_continue = False
            recommendation = "skip_to_alerts_only"

        # Identify which metrics were calculated
        metrics_calculated = [k for k, v in metrics_dict.items() if v is not None]
        metrics_missing = [k for k, v in metrics_dict.items() if v is None]

        return FinancialAgentRouting(
            status=status,
            reason=f"Calculated {metrics_count} metrics (critical: {critical_count}/3, profitability: {profitability_count}/4, growth: {growth_count}/2) - Score: {overall_score:.2f}",
            should_continue_pipeline=should_continue,
            metrics_available=metrics_count,
            metrics_calculated=metrics_calculated,
            metrics_missing=metrics_missing,
            recommended_next_step=recommendation
        )
