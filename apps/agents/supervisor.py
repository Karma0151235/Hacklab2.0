"""
Supervisor Agent for Market Intelligence
Orchestrates RAG, Financial, and Alert agents to provide comprehensive intelligence
"""

from typing import List, Dict, Any, Optional, Callable
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).parent.parent))

import openai

from agents.schemas import (
    SupervisorInput,
    SupervisorOutput,
    Citation,
    RAGQuery,
    FinancialAgentInput,
    AlertAgentInput,
    SentimentAgentInput,
)
from agents.config import AgentConfig
from agents.rag_agent import RAGAgent
from agents.financial_agent import FinancialAgent
from agents.alert_agent import AlertAgent
from agents.sentiment_agent import SentimentAgent
from agents.news_fetcher import fetch_news_for_company
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

    Provide concise, evidence-backed reasoning.

    Goal: produce explainable, actionable intelligence with evidence-based support.
    """

    SYSTEM_PROMPT = """You are the Supervisor Agent for market intelligence.

Your role:
1. Analyze user queries to determine which agents to invoke
2. Coordinate RAG, Financial, and Alert agents
3. Aggregate outputs into coherent, evidence-backed responses
4. Connect insights with concise reasoning
5. Provide clear, structured explanations
6. Include citations and source references
7. Surface actionable intelligence and alerts

Always:
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
        self.sentiment_agent = SentimentAgent()

        # Initialize OpenRouter client
        self.client = openai.OpenAI(
            api_key=self.config.OPENROUTER_API_KEY,
            base_url=self.config.OPENROUTER_BASE_URL,
            timeout=self.config.OPENROUTER_TIMEOUT_SECONDS,
            max_retries=self.config.OPENROUTER_MAX_RETRIES,
        )

        logger.info("Supervisor Agent initialized")

    def process(
        self,
        input_data: SupervisorInput,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> SupervisorOutput:
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
            overall_start = perf_counter()

            self._emit_progress(
                progress_callback,
                agent_id="supervisor",
                status="running",
                message="Analyzing query and orchestrating agents",
                step="Supervisor started"
            )

            # Step 1: Determine which agents to call
            steps.append("Analyzing query to determine required agents")
            agent_plan = self._plan_agent_execution(input_data.query)
            self._emit_progress(
                progress_callback,
                agent_id="supervisor",
                status="running",
                message="Agent plan created",
                step="Agent plan created"
            )
            if not agent_plan.get("use_financial"):
                self._emit_progress(
                    progress_callback,
                    agent_id="financial",
                    status="skipped",
                    message="Skipped: financial analysis not required",
                    step="Financial agent skipped"
                )
            if not agent_plan.get("use_alert"):
                self._emit_progress(
                    progress_callback,
                    agent_id="alert",
                    status="skipped",
                    message="Skipped: alert analysis not required",
                    step="Alert agent skipped"
                )

            # Step 2: Always call RAG agent for context
            steps.append("Retrieving relevant context from knowledge base")
            rag_start = perf_counter()
            self._emit_progress(
                progress_callback,
                agent_id="rag",
                status="running",
                message="Retrieving relevant context from knowledge base",
                step="RAG retrieval started"
            )
            rag_output = self.rag_agent.retrieve(RAGQuery(
                query=input_data.query,
                top_k_text=self.config.TOP_K_TEXT,
                top_k_table=self.config.TOP_K_TABLE,
                company_name=agent_plan.get("company_name")
            ))
            rag_duration = perf_counter() - rag_start
            agents_used.append("RAG")
            text_chunks = len([m for m in rag_output.metadata if m.collection == self.config.TEXT_COLLECTION])
            table_chunks = len([m for m in rag_output.metadata if m.collection == self.config.TABLE_COLLECTION])
            steps.append(f"Retrieved {len(rag_output.metadata)} chunks from knowledge base")
            self._emit_progress(
                progress_callback,
                agent_id="rag",
                status="completed",
                message=f"Retrieved {text_chunks} text + {table_chunks} table chunks in {rag_duration:.1f}s",
                step="RAG retrieval completed"
            )
            
            # Early-exit check: Skip expensive agent calls if RAG returns no/low-quality results
            # Note: Sentiment Agent still runs in this path (news-based, not RAG-dependent)
            rag_quality = self._assess_rag_quality(rag_output)
            sentiment_output = None

            if rag_quality["skip_expensive_agents"]:
                logger.warning(f"Low RAG quality detected ({rag_quality['reason']}), skipping Financial/Alert agents")
                steps.append(f"⚠ Low-quality RAG results detected: {rag_quality['reason']}")
                steps.append("Skipping expensive agent calls to optimize performance")
                self._emit_progress(
                    progress_callback,
                    agent_id="financial",
                    status="skipped",
                    message="Skipped due to low-quality RAG results",
                    step="Financial agent skipped"
                )
                self._emit_progress(
                    progress_callback,
                    agent_id="alert",
                    status="skipped",
                    message="Skipped due to low-quality RAG results",
                    step="Alert agent skipped"
                )

                # Try to run Sentiment Agent even with low RAG quality
                if self.config.USE_SENTIMENT_AGENT and agent_plan.get("use_sentiment"):
                    steps.append("Analyzing market sentiment from news sources (RAG-independent)")
                    sentiment_start = perf_counter()
                    company_name = agent_plan.get("company_name")

                    self._emit_progress(
                        progress_callback,
                        agent_id="sentiment",
                        status="running",
                        message="Fetching and analyzing news for sentiment analysis",
                        step="Sentiment agent started"
                    )

                    try:
                        news_articles = fetch_news_for_company(company_name, limit=10)
                        sentiment_output = self.sentiment_agent.analyze(SentimentAgentInput(
                            query=input_data.query,
                            company_name=company_name,
                            news_articles=news_articles,
                            rag_context=rag_output
                        ))

                        sentiment_duration = perf_counter() - sentiment_start
                        agents_used.append("Sentiment")
                        steps.append(f"Sentiment analysis: {sentiment_output.overall_sentiment} ({sentiment_output.sentiment_score:.2f})")

                        self._emit_progress(
                            progress_callback,
                            agent_id="sentiment",
                            status="completed",
                            message=f"Sentiment: {sentiment_output.overall_sentiment} in {sentiment_duration:.1f}s",
                            step="Sentiment agent completed"
                        )
                    except Exception as e:
                        logger.error(f"Sentiment agent error: {str(e)}")
                        self._emit_progress(
                            progress_callback,
                            agent_id="sentiment",
                            status="error",
                            message=f"Sentiment analysis failed: {str(e)}",
                            step="Sentiment agent error"
                        )

                # Return early with RAG + optional Sentiment results
                answer = self._synthesize_response_rag_only(
                    input_data.query,
                    rag_output,
                    rag_quality,
                    sentiment_output,
                    steps
                )

                citations = self._build_citations(rag_output)
                table_data = self._prepare_table_data(rag_output)
                confidence = rag_quality["confidence"]
                if sentiment_output and sentiment_output.confidence > 0:
                    confidence = (confidence * 0.7) + (sentiment_output.confidence * 0.3)

                total_duration = perf_counter() - overall_start
                self._emit_progress(
                    progress_callback,
                    agent_id="supervisor",
                    status="completed",
                    message=f"Completed with RAG-only response in {total_duration:.1f}s",
                    step="Supervisor completed"
                )

                return SupervisorOutput(
                    answer=answer,
                    agents_used=agents_used,
                    citations=citations,
                    steps=steps,
                    table_data=table_data,
                    sentiment=sentiment_output,
                    confidence_score=confidence
                )

            # Step 3: Call Financial Agent if needed
            financial_output = None
            if agent_plan.get("use_financial"):
                steps.append("Analyzing financial metrics and calculations")
                financial_start = perf_counter()
                self._emit_progress(
                    progress_callback,
                    agent_id="financial",
                    status="running",
                    message="Analyzing financial metrics and calculations",
                    step="Financial agent started"
                )
                financial_output = self.financial_agent.analyze(FinancialAgentInput(
                    query=input_data.query,
                    context={"rag_output": rag_output.dict()}
                ))
                financial_duration = perf_counter() - financial_start
                agents_used.append("Financial")
                metrics_count = sum(1 for v in financial_output.metrics.dict().values() if v is not None)
                steps.append(f"Calculated {metrics_count} financial metrics")
                self._emit_progress(
                    progress_callback,
                    agent_id="financial",
                    status="completed",
                    message=f"Calculated {metrics_count} metrics in {financial_duration:.1f}s",
                    step="Financial agent completed"
                )

            # Step 4: Call Alert Agent if needed
            alert_output = None
            if agent_plan.get("use_alert") or financial_output:
                steps.append("Evaluating alerts and risk indicators")
                alert_start = perf_counter()
                self._emit_progress(
                    progress_callback,
                    agent_id="alert",
                    status="running",
                    message="Evaluating alerts and risk indicators",
                    step="Alert agent started"
                )
                alert_output = self.alert_agent.evaluate(AlertAgentInput(
                    query=input_data.query,
                    financial_metrics=financial_output.metrics if financial_output else None,
                    rag_context=rag_output
                ))
                alert_duration = perf_counter() - alert_start
                agents_used.append("Alert")
                steps.append(f"Generated {len(alert_output.alerts)} alerts")
                self._emit_progress(
                    progress_callback,
                    agent_id="alert",
                    status="completed",
                    message=f"Generated {len(alert_output.alerts)} alerts in {alert_duration:.1f}s",
                    step="Alert agent completed"
                )

            # Step 4b: Call Sentiment Agent if needed
            sentiment_output = None
            if self.config.USE_SENTIMENT_AGENT and agent_plan.get("use_sentiment"):
                steps.append("Analyzing market sentiment from news sources")
                sentiment_start = perf_counter()
                company_name = agent_plan.get("company_name")

                self._emit_progress(
                    progress_callback,
                    agent_id="sentiment",
                    status="running",
                    message=f"Fetching and analyzing news for sentiment analysis",
                    step="Sentiment agent started"
                )

                try:
                    # Fetch news for company
                    news_articles = fetch_news_for_company(company_name, limit=10)

                    sentiment_output = self.sentiment_agent.analyze(SentimentAgentInput(
                        query=input_data.query,
                        company_name=company_name,
                        news_articles=news_articles,
                        rag_context=rag_output
                    ))

                    sentiment_duration = perf_counter() - sentiment_start
                    agents_used.append("Sentiment")
                    steps.append(f"Sentiment analysis: {sentiment_output.overall_sentiment} ({sentiment_output.sentiment_score:.2f})")

                    self._emit_progress(
                        progress_callback,
                        agent_id="sentiment",
                        status="completed",
                        message=f"Sentiment: {sentiment_output.overall_sentiment} ({sentiment_output.articles_analyzed} articles) in {sentiment_duration:.1f}s",
                        step="Sentiment agent completed"
                    )
                except Exception as e:
                    logger.error(f"Sentiment agent error: {str(e)}")
                    self._emit_progress(
                        progress_callback,
                        agent_id="sentiment",
                        status="error",
                        message=f"Sentiment analysis failed: {str(e)}",
                        step="Sentiment agent error"
                    )
            else:
                # Log why sentiment was skipped
                if not self.config.USE_SENTIMENT_AGENT:
                    self._emit_progress(
                        progress_callback,
                        agent_id="sentiment",
                        status="skipped",
                        message="Skipped: sentiment agent disabled in config",
                        step="Sentiment agent skipped"
                    )
                elif not agent_plan.get("use_sentiment"):
                    self._emit_progress(
                        progress_callback,
                        agent_id="sentiment",
                        status="skipped",
                        message="Skipped: sentiment analysis not required for this query",
                        step="Sentiment agent skipped"
                    )

            # Step 5: Aggregate outputs
            steps.append("Aggregating outputs and synthesizing final response")
            synthesis_start = perf_counter()
            self._emit_progress(
                progress_callback,
                agent_id="supervisor",
                status="running",
                message="Synthesizing final response",
                step="Response synthesis started"
            )
            answer = self._synthesize_response(
                input_data.query,
                rag_output,
                financial_output,
                alert_output,
                sentiment_output,
                steps
            )
            synthesis_duration = perf_counter() - synthesis_start

            # Step 6: Build citations
            citations = self._build_citations(rag_output)

            # Step 7: Prepare table data
            table_data = self._prepare_table_data(rag_output)

            # Step 8: Calculate confidence
            confidence = self._calculate_confidence(rag_output, financial_output, alert_output, sentiment_output)

            sentiment_confidence = None
            if sentiment_output and sentiment_output.confidence > 0:
                sentiment_confidence = sentiment_output.confidence

            answer_parts = [answer.strip()]
            answer_parts.append("")
            answer_parts.append("Confidence")
            answer_parts.append(f"Overall: {confidence:.0%}")
            if sentiment_confidence is not None:
                answer_parts.append(f"Sentiment: {sentiment_confidence:.0%}")
            answer = "\n".join(answer_parts)

            output = SupervisorOutput(
                answer=answer,
                agents_used=agents_used,
                citations=citations,
                steps=steps,
                table_data=table_data,
                sentiment=sentiment_output,
                confidence_score=confidence
            )

            total_duration = perf_counter() - overall_start
            logger.info(f"Supervisor completed: {len(agents_used)} agents used, {len(citations)} citations")
            self._emit_progress(
                progress_callback,
                agent_id="supervisor",
                status="completed",
                message=f"Synthesis in {synthesis_duration:.1f}s · Total {total_duration:.1f}s",
                step="Supervisor completed"
            )
            return output

        except Exception as e:
            logger.error(f"Supervisor Agent error: {str(e)}")
            self._emit_progress(
                progress_callback,
                agent_id="supervisor",
                status="error",
                message=f"Supervisor error: {str(e)}",
                step="Supervisor error"
            )
            return SupervisorOutput(
                answer=f"Error processing query: {str(e)}",
                agents_used=[],
                citations=[],
                steps=["Error occurred during processing"],
                confidence_score=0.0
            )

    def _emit_progress(
        self,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]],
        agent_id: str,
        status: str,
        message: str,
        step: Optional[str] = None
    ) -> None:
        if not progress_callback:
            return
        payload = {
            "agent_id": agent_id,
            "status": status,
            "message": message,
        }
        if step:
            payload["step"] = step
        progress_callback(payload)

    def _plan_agent_execution(self, query: str) -> Dict[str, Any]:
        """Determine which agents to call based on query"""
        try:
            prompt = f"""Analyze this query and determine which agents should be called.

Query: {query}

Available agents:
1. RAG Agent - retrieves context from PDF documents (always needed)
2. Financial Agent - calculates financial metrics (ratios, growth, profitability)
3. Alert Agent - evaluates alerts based on thresholds and keywords
4. Sentiment Agent - analyzes news sentiment and market mood

Respond with JSON indicating which agents to use and any company mentioned:
{{
  "use_rag": true,
  "use_financial": true/false,
  "use_alert": true/false,
  "use_sentiment": true/false,
  "company_name": "extracted company name or null",
  "reasoning": "brief explanation"
}}

Use Financial Agent for queries about:
- Financial metrics, ratios, calculations
- Performance analysis
- Profitability, liquidity, solvency

Use Alert Agent for queries about:
- Risks, concerns, warnings
- Threshold breaches
- Adverse conditions

Use Sentiment Agent for queries about:
- News sentiment, market sentiment
- Media coverage, press, headlines
- Public perception, investor sentiment

Extract the company name if mentioned (e.g., "MAYBANK", "Maybank Group", etc.)."""

            response = self.client.chat.completions.create(
                model=self.config.GLM_4_5_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500,
                extra_body={"reasoning": {"enabled": True}}
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
                return {
                    "use_rag": True,
                    "use_financial": True,
                    "use_alert": True,
                    "use_sentiment": False,
                    "company_name": None
                }

        except Exception as e:
            logger.warning(f"Error planning agent execution: {str(e)}")
            return {
                "use_rag": True,
                "use_financial": True,
                "use_alert": True,
                "use_sentiment": False,
                "company_name": None
            }


    def _synthesize_response(
        self,
        query: str,
        rag_output,
        financial_output,
        alert_output,
        sentiment_output,
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

            if sentiment_output:
                context_parts.append(f"\n=== Sentiment Analysis ===")
                context_parts.append(f"Overall Sentiment: {sentiment_output.overall_sentiment.upper()}")
                context_parts.append(f"Sentiment Score: {sentiment_output.sentiment_score:.2f}")
                context_parts.append(f"Confidence: {sentiment_output.confidence:.1%}")
                if sentiment_output.summary:
                    context_parts.append(f"\nSummary: {sentiment_output.summary}")
                if sentiment_output.articles_analyzed > 0:
                    context_parts.append(f"Articles Analyzed: {sentiment_output.articles_analyzed}")

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
5. Provides concise reasoning and actionable intelligence

Do not include Key Topics or Key Phrases sections. Do not include confidence statements; a standardized confidence block will be appended separately.

Be clear, concise, and specific. Include numbers and citations."""

            response = self.client.chat.completions.create(
                model=self.config.GLM_4_5_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.TEMPERATURE,
                max_tokens=self.config.MAX_TOKENS,
                extra_body={"reasoning": {"enabled": True}}
            )

            answer = response.choices[0].message.content
            return answer

        except Exception as e:
            logger.error(f"Error synthesizing response: {str(e)}")
            return f"Error synthesizing response: {str(e)}"

    def _build_citations(self, rag_output) -> List[Citation]:
        """Build citations from RAG metadata"""
        citations = []

        if getattr(rag_output, "text_chunks", None):
            for chunk in rag_output.text_chunks:
                excerpt = self._extract_excerpt(chunk.content)
                citation = Citation(
                    filename=chunk.filename,
                    company_name=chunk.company_name,
                    collection=chunk.collection,
                    page_number=chunk.page_number,
                    confidence_score=chunk.confidence_score,
                    excerpt=excerpt,
                    source_url=self._build_source_url(chunk.filename)
                )
                citations.append(citation)
        else:
            for metadata in rag_output.metadata:
                citation = Citation(
                    filename=metadata.filename,
                    company_name=metadata.company_name,
                    collection=metadata.collection,
                    page_number=metadata.page_number,
                    confidence_score=metadata.confidence_score,
                    excerpt=None,
                    source_url=self._build_source_url(metadata.filename)
                )
                citations.append(citation)

        return citations

    def _extract_excerpt(self, content: str, max_len: int = 240) -> str:
        """Extract a readable line excerpt from content"""
        if not content:
            return ""
        for line in content.splitlines():
            clean = line.strip()
            if clean:
                return clean[:max_len]
        return content.strip()[:max_len]

    def _build_source_url(self, filename: str) -> Optional[str]:
        """Build Bursa announcement URL from doc_id/filename if possible"""
        if not filename:
            return None
        # doc_id format: bursa_{ann_id}
        if filename.startswith("bursa_"):
            ann_id = filename.replace("bursa_", "").strip()
            if ann_id:
                return (
                    "https://www.bursamalaysia.com/market_information/"
                    "announcements/company_announcement/announcement_details"
                    f"?ann_id={ann_id}"
                )
        return None

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

    def _calculate_confidence(self, rag_output, financial_output, alert_output, sentiment_output) -> float:
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

        # Factor in sentiment confidence if available
        if sentiment_output and sentiment_output.confidence > 0:
            # Weight sentiment confidence (30%) with RAG confidence (70%)
            avg_confidence = (avg_confidence * 0.7) + (sentiment_output.confidence * 0.3)

        # Reduce confidence if high severity alerts
        if alert_output and alert_output.alerts:
            high_severity_count = sum(1 for a in alert_output.alerts if a.severity == "high")
            if high_severity_count > 0:
                avg_confidence = max(avg_confidence * 0.9, 0.3)

        return round(avg_confidence, 2)
    
    def _assess_rag_quality(self, rag_output) -> Dict[str, Any]:
        """
        Assess RAG output quality to determine if expensive agent calls should be skipped
        
        Returns:
            Dict with keys:
            - skip_expensive_agents: bool
            - reason: str (reason for skipping)
            - confidence: float
        """
        # Check 1: No chunks retrieved
        if not rag_output.metadata or len(rag_output.metadata) == 0:
            return {
                "skip_expensive_agents": True,
                "reason": "No relevant documents found",
                "confidence": 0.1
            }
        
        # Check 2: Very low confidence scores (average < 0.3)
        avg_confidence = sum(m.confidence_score for m in rag_output.metadata) / len(rag_output.metadata)
        if avg_confidence < 0.3:
            return {
                "skip_expensive_agents": True,
                "reason": f"Low relevance confidence ({avg_confidence:.2f})",
                "confidence": avg_confidence
            }
        
        # Check 3: Empty or very short summary (indicates no useful content)
        if not rag_output.summary or len(rag_output.summary.strip()) < 50:
            return {
                "skip_expensive_agents": True,
                "reason": "Insufficient context extracted",
                "confidence": 0.2
            }
        
        # Check 4: Summary contains error messages
        error_indicators = ["error", "failed", "unable to", "no information", "not found"]
        if any(indicator in rag_output.summary.lower() for indicator in error_indicators):
            return {
                "skip_expensive_agents": True,
                "reason": "RAG extraction encountered errors",
                "confidence": 0.2
            }
        
        # Good quality - proceed with full orchestration
        return {
            "skip_expensive_agents": False,
            "reason": "High-quality RAG results",
            "confidence": avg_confidence
        }
    
    def _synthesize_response_rag_only(
        self,
        query: str,
        rag_output,
        rag_quality: Dict[str, Any],
        sentiment_output,
        steps: List[str]
    ) -> str:
        """
        Synthesize response using RAG + optional Sentiment (fast path for low-quality RAG results)

        This is a lightweight alternative to full synthesis when RAG returns poor results.
        Sentiment can still provide value as it's news-based and independent of RAG quality.
        """
        try:
            response_parts = []

            # RAG context
            if rag_output.summary and len(rag_output.summary.strip()) >= 20:
                response_parts.append("Based on limited context retrieved from the knowledge base:")
                response_parts.append(rag_output.summary)
                response_parts.append(f"\n⚠ Note: {rag_quality['reason']}. The above information may not fully answer your query.")
            else:
                response_parts.append(
                    f"I couldn't find relevant document context to answer your query. "
                    f"Reason: {rag_quality['reason']}."
                )

            # Sentiment context (if available)
            if sentiment_output:
                response_parts.append(f"\nMarket Sentiment Analysis:")
                response_parts.append(f"- Overall: {sentiment_output.overall_sentiment.upper()} (score: {sentiment_output.sentiment_score:.2f})")
                if sentiment_output.summary:
                    response_parts.append(f"- Summary: {sentiment_output.summary}")

            response_parts.append("\nConfidence")
            response_parts.append(f"Overall: {rag_quality['confidence']:.0%}")
            if sentiment_output and sentiment_output.confidence > 0:
                response_parts.append(f"Sentiment: {sentiment_output.confidence:.0%}")

            if rag_output.entities:
                response_parts.append(f"Mentioned entities: {', '.join(rag_output.entities)}")

            return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"Error in RAG-only synthesis: {str(e)}")
            return f"Unable to process query due to low-quality results. Reason: {rag_quality['reason']}"
