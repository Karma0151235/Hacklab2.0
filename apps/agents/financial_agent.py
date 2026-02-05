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

    SYSTEM_PROMPT = """You are the Financial Data Extraction Agent.

Your role:
1. Extract specific financial figures from the provided context
2. Extract ONLY values that are explicitly stated in the text
3. NEVER estimate or infer financial figures
4. Identify the currency (RM, USD, etc.)
5. Extract dates/periods when available
6. Flag any inconsistencies in the data

Return a JSON object with:
{
  "extracted_values": {
    "revenue": number or null,
    "net_profit": number or null,
    "net_income": number or null,
    "gross_profit": number or null,
    "operating_income": number or null,
    "operating_profit": number or null,
    "cost_of_goods_sold": number or null,
    "current_assets": number or null,
    "total_assets": number or null,
    "current_liabilities": number or null,
    "total_debt": number or null,
    "equity": number or null,
    "inventory": number or null,
    "accounts_receivable": number or null,
    "interest_expense": number or null,
    "shares_outstanding": number or null,
    "previous_revenue": number or null,
    "previous_net_income": number or null,
    "previous_eps": number or null
  },
  "period": "string (e.g. 'Q1 2025', 'FY2024')",
  "currency": "string (e.g. 'RM', 'USD')",
  "confidence": number (0.0-1.0),
  "data_quality_issues": ["string", ...]
}

Important:
- If a value is not explicitly stated, return null (NOT zero)
- If you are uncertain about a value, mark confidence lower and note the issue
- Only include extracted_values that have explicit support in the text
- List any ambiguities or inconsistencies in data_quality_issues"""

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

            # Build extraction prompt
            context_text = rag_output.get('summary', '') if isinstance(rag_output, dict) else rag_output.summary

            extraction_prompt = f"""Extract financial figures from the following text:

{context_text}

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
        Route financial analysis results based on completeness.

        Determines:
        - Status: complete, partial, skip
        - Whether to proceed with Alert Agent
        - Recommended next step
        """
        # Count calculated metrics
        metrics_dict = output.metrics.dict()
        calculated_metrics = [k for k, v in metrics_dict.items() if v is not None]
        metrics_count = len(calculated_metrics)

        # Determine status
        if metrics_count >= 8:
            status = "complete"
            should_continue = True
            recommendation = "analyze_fully"
        elif metrics_count >= 3:
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
            reason=f"Calculated {metrics_count} out of {len(metrics_dict)} available metrics",
            should_continue_pipeline=should_continue,
            metrics_available=metrics_count,
            metrics_calculated=metrics_calculated,
            metrics_missing=metrics_missing,
            recommended_next_step=recommendation
        )
