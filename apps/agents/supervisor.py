"""
Supervisor Agent for Market Intelligence
Orchestrates RAG, Financial, and Alert agents to provide comprehensive intelligence
"""

from typing import List, Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import openai

from agents.schemas import (
    SupervisorInput,
    SupervisorOutput,
    Citation,
    RAGQuery,
    FinancialAgentInput,
    AlertAgentInput,
)
from agents.config import AgentConfig
from agents.rag_agent import RAGAgent
from agents.financial_agent import FinancialAgent
from agents.alert_agent import AlertAgent
from etl.logging_config import get_logger

logger = get_logger(__name__)


class SupervisorAgent:
    """
    Supervisor Agent - orchestrates all other agents

    System Prompt:
    You are the Supervisor Agent.

    Orchestrate queries to:
    • RAG agent (unstructured PDF/text retrieval)
    • Financial agent (key metrics extraction & calculation)
    • Alert agent (structured signals & rules)

    Decide which agents to call based on the user query.

    Aggregate outputs into a final, step-by-step, evidence-backed response.

    Include citations (filename, company name, collection) and reconstructed
    table chunks as Pandas DataFrame.

    Use Chain-of-Thought reasoning where necessary.

    Goal: produce explainable, actionable intelligence with evidence-based reasoning.
    """

    SYSTEM_PROMPT = """You are the Supervisor Agent for market intelligence.

Your role:
1. Analyze user queries to determine which agents to invoke
2. Coordinate RAG, Financial, and Alert agents
3. Aggregate outputs into coherent, evidence-backed responses
4. Apply Chain-of-Thought reasoning to connect insights
5. Provide step-by-step explanations
6. Include citations and source references
7. Surface actionable intelligence and alerts

Always:
- Show your reasoning process
- Reference specific sources and data points
- Prioritize accuracy over speculation
- Clearly indicate confidence levels"""

    def __init__(self):
        """Initialize Supervisor Agent and sub-agents"""
        self.config = AgentConfig

        # Initialize sub-agents
        logger.info("Initializing Supervisor Agent and sub-agents...")
        self.rag_agent = RAGAgent()
        self.financial_agent = FinancialAgent()
        self.alert_agent = AlertAgent()

        # Initialize OpenRouter client
        self.client = openai.OpenAI(
            api_key=self.config.OPENROUTER_API_KEY,
            base_url=self.config.OPENROUTER_BASE_URL
        )

        logger.info("Supervisor Agent initialized")

    def process(self, input_data: SupervisorInput) -> SupervisorOutput:
        """
        Process user query by orchestrating agents

        Args:
            input_data: SupervisorInput with query

        Returns:
            SupervisorOutput with aggregated response
        """
        try:
            logger.info(f"Supervisor processing query: {input_data.query}")

            steps = []
            agents_used = []

            # Step 1: Determine which agents to call
            steps.append("Analyzing query to determine required agents")
            agent_plan = self._plan_agent_execution(input_data.query)
            steps.append(f"Plan: {agent_plan}")

            # Step 2: Always call RAG agent for context
            steps.append("Retrieving relevant context from knowledge base")
            rag_output = self.rag_agent.retrieve(RAGQuery(
                query=input_data.query,
                top_k_text=self.config.TOP_K_TEXT,
                top_k_table=self.config.TOP_K_TABLE
            ))
            agents_used.append("RAG")
            steps.append(f"Retrieved {len(rag_output.metadata)} chunks from knowledge base")

            # Step 3: Call Financial Agent if needed
            financial_output = None
            if agent_plan.get("use_financial"):
                steps.append("Analyzing financial metrics and calculations")
                financial_output = self.financial_agent.analyze(FinancialAgentInput(
                    query=input_data.query,
                    context={"rag_output": rag_output.dict()}
                ))
                agents_used.append("Financial")
                metrics_count = sum(1 for v in financial_output.metrics.dict().values() if v is not None)
                steps.append(f"Calculated {metrics_count} financial metrics")

            # Step 4: Call Alert Agent if needed
            alert_output = None
            if agent_plan.get("use_alert") or financial_output:
                steps.append("Evaluating alerts and risk indicators")
                alert_output = self.alert_agent.evaluate(AlertAgentInput(
                    query=input_data.query,
                    financial_metrics=financial_output.metrics if financial_output else None,
                    rag_context=rag_output
                ))
                agents_used.append("Alert")
                steps.append(f"Generated {len(alert_output.alerts)} alerts")

            # Step 5: Aggregate outputs
            steps.append("Aggregating outputs and synthesizing final response")
            answer = self._synthesize_response(
                input_data.query,
                rag_output,
                financial_output,
                alert_output,
                steps
            )

            # Step 6: Build citations
            citations = self._build_citations(rag_output)

            # Step 7: Prepare table data
            table_data = self._prepare_table_data(rag_output)

            # Step 8: Calculate confidence
            confidence = self._calculate_confidence(rag_output, financial_output, alert_output)

            output = SupervisorOutput(
                answer=answer,
                agents_used=agents_used,
                citations=citations,
                steps=steps,
                table_data=table_data,
                confidence_score=confidence
            )

            logger.info(f"Supervisor completed: {len(agents_used)} agents used, {len(citations)} citations")
            return output

        except Exception as e:
            logger.error(f"Supervisor Agent error: {str(e)}")
            return SupervisorOutput(
                answer=f"Error processing query: {str(e)}",
                agents_used=[],
                citations=[],
                steps=["Error occurred during processing"],
                confidence_score=0.0
            )

    def _plan_agent_execution(self, query: str) -> Dict[str, bool]:
        """Determine which agents to call based on query"""
        try:
            prompt = f"""Analyze this query and determine which agents should be called.

Query: {query}

Available agents:
1. RAG Agent - retrieves context from PDF documents (always needed)
2. Financial Agent - calculates financial metrics (ratios, growth, profitability)
3. Alert Agent - evaluates alerts based on thresholds and keywords

Respond with JSON indicating which agents to use:
{{
  "use_rag": true,
  "use_financial": true/false,
  "use_alert": true/false,
  "reasoning": "brief explanation"
}}

Use Financial Agent for queries about:
- Financial metrics, ratios, calculations
- Performance analysis
- Profitability, liquidity, solvency

Use Alert Agent for queries about:
- Risks, concerns, warnings
- Threshold breaches
- Adverse conditions"""

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

                plan = json.loads(json_str)
                return plan
            except:
                # Default: use all agents
                return {"use_rag": True, "use_financial": True, "use_alert": True}

        except Exception as e:
            logger.warning(f"Error planning agent execution: {str(e)}")
            return {"use_rag": True, "use_financial": True, "use_alert": True}

    def _synthesize_response(
        self,
        query: str,
        rag_output,
        financial_output,
        alert_output,
        steps: List[str]
    ) -> str:
        """Synthesize final response from all agent outputs"""
        try:
            # Build context from agent outputs
            context_parts = [f"Query: {query}\n"]

            context_parts.append(f"\n=== RAG Context ===")
            context_parts.append(rag_output.summary)
            if rag_output.entities:
                context_parts.append(f"\nKey Entities: {', '.join(rag_output.entities)}")

            if financial_output:
                context_parts.append(f"\n=== Financial Analysis ===")
                context_parts.append(financial_output.analysis)
                metrics_dict = {k: v for k, v in financial_output.metrics.dict().items() if v is not None}
                if metrics_dict:
                    context_parts.append(f"\nKey Metrics: {metrics_dict}")

            if alert_output and alert_output.alerts:
                context_parts.append(f"\n=== Alerts ===")
                for alert in alert_output.alerts:
                    context_parts.append(f"- [{alert.severity.upper()}] {alert.message}")

            context = "\n".join(context_parts)

            # Generate synthesized response
            prompt = f"""Based on all agent outputs, provide a comprehensive, evidence-backed response to the user query.

{context}

Processing Steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(steps))}

Generate a response that:
1. Directly answers the user's question
2. Includes specific data points and evidence
3. References sources (filename, company)
4. Highlights key findings and alerts
5. Uses Chain-of-Thought reasoning to connect insights
6. Provides actionable intelligence

Be clear, concise, and specific. Include numbers and citations."""

            response = self.client.chat.completions.create(
                model=self.config.GLM_4_5_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.TEMPERATURE,
                max_tokens=self.config.MAX_TOKENS
            )

            answer = response.choices[0].message.content
            return answer

        except Exception as e:
            logger.error(f"Error synthesizing response: {str(e)}")
            return f"Error synthesizing response: {str(e)}"

    def _build_citations(self, rag_output) -> List[Citation]:
        """Build citations from RAG metadata"""
        citations = []

        for metadata in rag_output.metadata:
            citation = Citation(
                filename=metadata.filename,
                company_name=metadata.company_name,
                collection=metadata.collection,
                page_number=metadata.page_number,
                confidence_score=metadata.confidence_score
            )
            citations.append(citation)

        return citations

    def _prepare_table_data(self, rag_output) -> Dict[str, Any]:
        """Prepare table data for frontend"""
        if not rag_output.table_chunks:
            return None

        # Convert first table chunk to dict format suitable for Pandas
        table_chunk = rag_output.table_chunks[0]

        return {
            "table_id": table_chunk.table_id,
            "data": table_chunk.table_data,
            "filename": table_chunk.metadata.filename,
            "company_name": table_chunk.metadata.company_name,
            "table_index": table_chunk.metadata.table_index
        }

    def _calculate_confidence(self, rag_output, financial_output, alert_output) -> float:
        """Calculate overall confidence score"""
        if not rag_output.metadata:
            return 0.1

        # Average confidence from RAG retrieval
        avg_confidence = sum(m.confidence_score for m in rag_output.metadata) / len(rag_output.metadata)

        # Boost confidence if financial metrics were calculated
        if financial_output:
            metrics_count = sum(1 for v in financial_output.metrics.dict().values() if v is not None)
            if metrics_count > 5:
                avg_confidence = min(avg_confidence * 1.2, 1.0)

        # Reduce confidence if high severity alerts
        if alert_output and alert_output.alerts:
            high_severity_count = sum(1 for a in alert_output.alerts if a.severity == "high")
            if high_severity_count > 0:
                avg_confidence = max(avg_confidence * 0.9, 0.3)

        return round(avg_confidence, 2)
