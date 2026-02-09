"""
Enhanced LangGraph Workflow V2 with Intent Classification and Parallel Execution

Features:
- Intent-based agent routing
- Parallel execution of Financial + Alert agents
- Quality-gate based early exit optimization
- Structured financial metric calculation
- Individual agent routing/filtering
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END
from agents.intent_classifier import IntentClassifier
from agents.rag_agent import RAGAgent
from agents.financial_agent import FinancialAgent
from agents.alert_agent import AlertAgent
from agents.sentiment_agent import SentimentAgent
from agents.news_fetcher import fetch_news_for_company
from agents.schemas import (
    RAGQuery, AgentStateV2, RAGQualityAssessment,
    FinancialAgentInput, AlertAgentInput, SentimentAgentInput
)
from etl.logging_config import get_logger

logger = get_logger(__name__)


class IntelligenceFlowV2:
    """Enhanced workflow with intent classification and parallel execution"""

    def __init__(self):
        """Initialize v2 workflow with all required agents"""
        self.intent_classifier = IntentClassifier()
        self.supervisor = None  # Lazy init to avoid circular imports
        self.rag_agent = RAGAgent()
        self.financial_agent = FinancialAgent()
        self.alert_agent = AlertAgent()
        self.sentiment_agent = SentimentAgent()
        self.workflow = self._build_workflow_v2()

    def _build_workflow_v2(self) -> StateGraph:
        """Build enhanced LangGraph with new node structure"""
        workflow = StateGraph(AgentStateV2)

        # Add all nodes
        workflow.add_node("intent_classification", self._intent_classification_node)
        workflow.add_node("rag_retrieval", self._rag_retrieval_node)
        workflow.add_node("quality_assessment", self._quality_assessment_node)
        workflow.add_node("financial_analysis", self._financial_analysis_node)
        workflow.add_node("alert_evaluation", self._alert_evaluation_node)
        workflow.add_node("sentiment_analysis", self._sentiment_analysis_node)
        workflow.add_node("sentiment_analysis_low_quality", self._sentiment_analysis_node)
        workflow.add_node("response_synthesis", self._response_synthesis_node)
        workflow.add_node("rag_only_synthesis", self._rag_only_synthesis_node)

        # Define entry point
        workflow.set_entry_point("intent_classification")

        # Linear edges
        workflow.add_edge("intent_classification", "rag_retrieval")
        workflow.add_edge("rag_retrieval", "quality_assessment")

        # Conditional edge after quality assessment
        workflow.add_conditional_edges(
            "quality_assessment",
            self._route_after_quality_check,
            {
                "high_quality": "financial_analysis",
                "low_quality": "sentiment_analysis_low_quality"
            }
        )

        # High-quality path: financial → alert → sentiment → synthesis
        workflow.add_edge("financial_analysis", "alert_evaluation")
        workflow.add_edge("alert_evaluation", "sentiment_analysis")
        workflow.add_edge("sentiment_analysis", "response_synthesis")

        # Low-quality path: sentiment → rag_only_synthesis
        workflow.add_edge("sentiment_analysis_low_quality", "rag_only_synthesis")

        # Terminal edges
        workflow.add_edge("response_synthesis", END)
        workflow.add_edge("rag_only_synthesis", END)

        return workflow.compile()

    # ======================== NODE IMPLEMENTATIONS ========================

    def _intent_classification_node(self, state: AgentStateV2) -> AgentStateV2:
        """Step 1: Classify user intent"""
        try:
            # Emit progress
            if state.progress_callback:
                state.progress_callback({
                    "agent_id": "supervisor",
                    "status": "running",
                    "message": "Analyzing query intent...",
                    "step": "Intent classification started"
                })

            logger.info(f"Classifying intent for query: {state.query[:100]}...")
            intent = self.intent_classifier.classify(state.query)
            steps = list(state.steps) if state.steps else []
            steps.append(f"Intent: {intent.primary_intent} (confidence: {intent.confidence:.2f})")
            logger.info(f"Intent classified - Required agents: {intent.required_agents}")

            if state.progress_callback:
                state.progress_callback({
                    "agent_id": "supervisor",
                    "status": "running",
                    "message": f"Intent classified: {intent.primary_intent}",
                    "step": "Intent classification completed"
                })

            # Extract company_name from intent classification
            company_name = state.company_name or intent.company_name
            if company_name:
                logger.info(f"Extracted company name: {company_name}")

            return state.model_copy(update={"intent": intent, "steps": steps, "company_name": company_name})
        except Exception as e:
            logger.error(f"Intent classification failed: {str(e)}")
            steps = list(state.steps) if state.steps else []
            return state.model_copy(update={"error": f"Intent classification failed: {str(e)}", "steps": steps})

    def _rag_retrieval_node(self, state: AgentStateV2) -> AgentStateV2:
        """Step 2: Retrieve context from knowledge base"""
        try:
            if state.progress_callback:
                state.progress_callback({
                    "agent_id": "rag",
                    "status": "running",
                    "message": "Retrieving context from knowledge base..."
                })

            logger.info("Starting RAG retrieval...")
            rag_output = self.rag_agent.retrieve(RAGQuery(
                query=state.query,
                company_name=state.company_name,
            ))
            steps = list(state.steps) if state.steps else []
            steps.append(f"Retrieved {len(rag_output.text_chunks)} text chunks, {len(rag_output.table_chunks)} table chunks")
            logger.info(f"RAG retrieval complete - Found {len(rag_output.text_chunks)} text chunks")

            if state.progress_callback:
                state.progress_callback({
                    "agent_id": "rag",
                    "status": "completed",
                    "message": f"Retrieved {len(rag_output.text_chunks)} text chunks, {len(rag_output.table_chunks)} table chunks"
                })

            return state.model_copy(update={"rag_output": rag_output, "steps": steps})
        except Exception as e:
            logger.error(f"RAG retrieval failed: {str(e)}")
            steps = list(state.steps) if state.steps else []
            if state.progress_callback:
                state.progress_callback({
                    "agent_id": "rag",
                    "status": "error",
                    "message": f"RAG retrieval failed: {str(e)}"
                })
            return state.model_copy(update={"error": f"RAG retrieval failed: {str(e)}", "steps": steps})

    def _quality_assessment_node(self, state: AgentStateV2) -> AgentStateV2:
        """Step 3: Assess RAG quality"""
        try:
            logger.info("Assessing RAG output quality...")
            rag_output = state.rag_output

            chunk_count = len(rag_output.text_chunks) + len(rag_output.table_chunks) if rag_output else 0
            avg_confidence = sum(m.confidence_score for m in rag_output.metadata) / len(rag_output.metadata) if rag_output and rag_output.metadata else 0
            summary_length = len(rag_output.summary) if rag_output and rag_output.summary else 0
            has_errors = any(ind in (rag_output.summary or "").lower() for ind in ['error', 'failed', 'unable', 'not found'])

            quality_score = 0.0
            if chunk_count > 0:
                quality_score += 0.3
            if avg_confidence > 0.5:
                quality_score += 0.3
            if summary_length > 100:
                quality_score += 0.2
            if not has_errors:
                quality_score += 0.2

            assessment = "high_quality" if quality_score >= 0.6 else "low_quality"

            rag_quality = RAGQualityAssessment(
                quality_score=quality_score,
                chunk_count=chunk_count,
                avg_confidence=avg_confidence,
                summary_length=summary_length,
                has_errors=has_errors,
                assessment=assessment
            )

            steps = list(state.steps) if state.steps else []
            steps.append(f"RAG quality: {assessment} (score: {quality_score:.2f})")
            logger.info(f"RAG quality assessment: {assessment} (quality_score: {quality_score:.2f})")

            return state.model_copy(update={"rag_quality": rag_quality, "steps": steps})
        except Exception as e:
            logger.error(f"Quality assessment failed: {str(e)}")
            steps = list(state.steps) if state.steps else []
            return state.model_copy(update={"error": f"Quality assessment failed: {str(e)}", "steps": steps})

    def _route_after_quality_check(self, state: AgentStateV2) -> str:
        """Routing after quality assessment"""
        if state.rag_quality:
            return state.rag_quality.assessment
        return "low_quality"

    def _financial_analysis_node(self, state: AgentStateV2) -> AgentStateV2:
        """Step 4a: Financial analysis"""
        try:
            if not state.intent or 'financial' not in state.intent.required_agents:
                logger.info("Skipping financial analysis")
                if state.progress_callback:
                    state.progress_callback({"agent_id": "financial", "status": "skipped", "message": "Not required"})
                return state

            if state.progress_callback:
                state.progress_callback({"agent_id": "financial", "status": "running", "message": "Analyzing financial metrics..."})

            logger.info("Starting financial analysis...")
            financial_input = FinancialAgentInput(
                query=state.query,
                context={'rag_output': state.rag_output.dict() if state.rag_output else None}
            )

            financial_output = self.financial_agent.analyze(financial_input)
            financial_routing = self.financial_agent.route(financial_output)
            metrics_count = len([m for m in financial_output.metrics.dict().values() if m is not None])
            logger.info(f"Financial analysis complete - {metrics_count} metrics")

            if state.progress_callback:
                state.progress_callback({"agent_id": "financial", "status": "completed", "message": f"Calculated {metrics_count} metrics"})

            steps = list(state.steps) if state.steps else []
            steps.append(f"Financial analysis: {financial_routing.status} ({metrics_count} metrics)")
            return state.model_copy(update={"financial_output": financial_output, "financial_routing": financial_routing, "steps": steps})
        except Exception as e:
            logger.error(f"Financial analysis failed: {str(e)}")
            if state.progress_callback:
                state.progress_callback({"agent_id": "financial", "status": "error", "message": str(e)})
            steps = list(state.steps) if state.steps else []
            steps.append(f"Financial analysis: error - {str(e)}")
            return state.model_copy(update={"steps": steps})

    def _alert_evaluation_node(self, state: AgentStateV2) -> AgentStateV2:
        """Step 4b: Alert evaluation (sequential)"""
        try:
            if not state.intent or 'alert' not in state.intent.required_agents:
                logger.info("Skipping alert evaluation")
                if state.progress_callback:
                    state.progress_callback({"agent_id": "alert", "status": "skipped", "message": "Not required"})
                return state

            if state.progress_callback:
                state.progress_callback({"agent_id": "alert", "status": "running", "message": "Evaluating alerts and risks..."})

            logger.info("Starting alert evaluation...")
            alert_input = AlertAgentInput(
                query=state.query,
                financial_metrics=state.financial_output.metrics if state.financial_output else None,
                rag_context=state.rag_output
            )

            alert_output = self.alert_agent.evaluate(alert_input)
            alert_routing = self.alert_agent.route(alert_output)
            logger.info(f"Alert evaluation complete - {alert_routing.alert_count} alerts")

            if state.progress_callback:
                state.progress_callback({"agent_id": "alert", "status": "completed", "message": f"Found {alert_routing.alert_count} alerts"})

            steps = list(state.steps) if state.steps else []
            steps.append(f"Alert evaluation: {alert_routing.status} ({alert_routing.alert_count} alerts)")
            return state.model_copy(update={"alert_output": alert_output, "alert_routing": alert_routing, "steps": steps})
        except Exception as e:
            logger.error(f"Alert evaluation failed: {str(e)}")
            if state.progress_callback:
                state.progress_callback({"agent_id": "alert", "status": "error", "message": str(e)})
            steps = list(state.steps) if state.steps else []
            steps.append(f"Alert evaluation: error - {str(e)}")
            return state.model_copy(update={"steps": steps})

    def _sentiment_analysis_node(self, state: AgentStateV2) -> AgentStateV2:
        """Step 4c: Sentiment analysis (sequential)"""
        try:
            if state.progress_callback:
                state.progress_callback({"agent_id": "sentiment", "status": "running", "message": "Analyzing market sentiment..."})

            logger.info("Starting sentiment analysis...")

            company_name = state.company_name
            if not company_name:
                logger.warning("No company name extracted — skipping news fetch for sentiment")

            news_articles = []
            if company_name:
                if state.fetch_latest_news:
                    # User toggled web-search ON: scrape in background to populate DB, then read from cache
                    logger.info(f"[sentiment] fetch_latest_news=True, scraping fresh news for '{company_name}'")
                    try:
                        from agents.news_fetcher import _scrape_articles_sync
                        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(_scrape_articles_sync, company_name, 10)
                            try:
                                scraped = future.result(timeout=90)
                                if scraped:
                                    news_articles = scraped
                                    logger.info(f"[sentiment] Scraping returned {len(scraped)} articles")
                            except FuturesTimeoutError:
                                logger.warning(f"Scraping timed out for '{company_name}', checking cache")
                    except Exception as e:
                        logger.warning(f"Fresh scraping failed: {str(e)}")

                    # Always check Supabase cache (scraping stores there, so even after timeout articles may exist)
                    if not news_articles:
                        logger.info(f"[sentiment] Reading from Supabase cache for '{company_name}'")
                        try:
                            news_articles = fetch_news_for_company(company_name, limit=10)
                        except Exception as e2:
                            logger.warning(f"Cache read failed: {str(e2)}")
                            news_articles = []
                else:
                    # Normal path: Supabase cache first, scrape fallback
                    try:
                        news_articles = fetch_news_for_company(company_name, limit=10)
                    except Exception as e:
                        logger.warning(f"Could not fetch news: {str(e)}")
                        news_articles = []

            logger.info(f"[sentiment] Got {len(news_articles)} articles for '{company_name or 'N/A'}'")

            sentiment_input = SentimentAgentInput(
                query=state.query,
                company_name=company_name,
                news_articles=news_articles,
                rag_context=state.rag_output
            )

            sentiment_output = self.sentiment_agent.analyze(sentiment_input)
            logger.info(f"Sentiment analysis complete - {sentiment_output.overall_sentiment}")

            if state.progress_callback:
                state.progress_callback({"agent_id": "sentiment", "status": "completed", "message": f"Sentiment: {sentiment_output.overall_sentiment} ({sentiment_output.sentiment_score:.2f})"})

            steps = list(state.steps) if state.steps else []
            steps.append(f"Sentiment analysis: {sentiment_output.overall_sentiment} ({sentiment_output.sentiment_score:.2f})")
            return state.model_copy(update={"sentiment_output": sentiment_output, "steps": steps})
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            if state.progress_callback:
                state.progress_callback({"agent_id": "sentiment", "status": "error", "message": str(e)})
            steps = list(state.steps) if state.steps else []
            steps.append(f"Sentiment analysis: error - {str(e)}")
            return state.model_copy(update={"steps": steps})

    def _response_synthesis_node(self, state: AgentStateV2) -> AgentStateV2:
        """Step 5: Synthesize final response"""
        try:
            from agents.schemas import SupervisorOutput, Citation

            if state.progress_callback:
                state.progress_callback({"agent_id": "supervisor", "status": "running", "message": "Synthesizing response..."})

            logger.info("Starting response synthesis...")

            if self.supervisor is None:
                from agents.supervisor import SupervisorAgent
                self.supervisor = SupervisorAgent(use_v2_workflow=False)

            steps = list(state.steps) if state.steps else []
            answer_text = self.supervisor._synthesize_response(
                query=state.query,
                rag_output=state.rag_output,
                financial_output=state.financial_output,
                alert_output=state.alert_output,
                sentiment_output=state.sentiment_output,
                steps=steps
            )

            # Build agents_used list
            agents_used = []
            if state.rag_output:
                agents_used.append("RAG")
            if state.financial_output:
                agents_used.append("Financial")
            if state.alert_output:
                agents_used.append("Alert")
            if state.sentiment_output:
                agents_used.append("Sentiment")

            # Build citations from RAG
            citations = []
            if state.rag_output and state.rag_output.text_chunks:
                for chunk in state.rag_output.text_chunks:
                    citation = Citation(
                        filename=chunk.filename,
                        company_name=chunk.company_name,
                        collection=chunk.collection,
                        page_number=chunk.page_number,
                        confidence_score=chunk.confidence_score,
                        excerpt=None,
                        source_url=None
                    )
                    citations.append(citation)

            # Calculate confidence
            confidence = state.rag_quality.quality_score if state.rag_quality else 0.5

            # Extract HIGH severity alerts only (critical alerts)
            critical_alerts = []
            if state.alert_output and state.alert_output.alerts:
                critical_alerts = [
                    alert for alert in state.alert_output.alerts
                    if alert.severity == "high"
                ]

            # Create SupervisorOutput
            supervisor_output = SupervisorOutput(
                answer=answer_text,
                agents_used=agents_used,
                citations=citations,
                steps=steps,
                confidence_score=confidence,
                sentiment=state.sentiment_output,
                alerts=critical_alerts
            )

            steps.append("Response synthesis: complete")
            logger.info("Response synthesis complete")

            if state.progress_callback:
                state.progress_callback({"agent_id": "supervisor", "status": "completed", "message": "Response synthesis complete"})

            return state.model_copy(update={"supervisor_output": supervisor_output, "steps": steps})
        except Exception as e:
            logger.error(f"Response synthesis failed: {str(e)}")
            from agents.schemas import SupervisorOutput
            steps = list(state.steps) if state.steps else []
            steps.append(f"Response synthesis: error - {str(e)}")

            # Extract HIGH severity alerts even on error
            critical_alerts = []
            if state.alert_output and state.alert_output.alerts:
                critical_alerts = [
                    alert for alert in state.alert_output.alerts
                    if alert.severity == "high"
                ]

            # Return error output as SupervisorOutput
            supervisor_output = SupervisorOutput(
                answer=f"Response synthesis failed: {str(e)}",
                agents_used=[],
                citations=[],
                steps=steps,
                confidence_score=0.0,
                alerts=critical_alerts
            )
            return state.model_copy(update={"supervisor_output": supervisor_output, "steps": steps})

    def _rag_only_synthesis_node(self, state: AgentStateV2) -> AgentStateV2:
        """Alternative synthesis for low RAG quality"""
        try:
            from agents.schemas import SupervisorOutput, Citation
            logger.info("Using RAG-only synthesis path...")

            if self.supervisor is None:
                from agents.supervisor import SupervisorAgent
                self.supervisor = SupervisorAgent(use_v2_workflow=False)

            rag_quality = state.rag_quality
            rag_quality_dict = {
                'reason': rag_quality.assessment if rag_quality else 'Unknown',
                'confidence': rag_quality.quality_score if rag_quality else 0.0
            }

            steps = list(state.steps) if state.steps else []
            answer_text = self.supervisor._synthesize_response_rag_only(
                query=state.query,
                rag_output=state.rag_output,
                rag_quality=rag_quality_dict,
                sentiment_output=state.sentiment_output,
                steps=steps
            )

            # Build citations from RAG
            citations = []
            if state.rag_output and state.rag_output.text_chunks:
                for chunk in state.rag_output.text_chunks:
                    citation = Citation(
                        filename=chunk.filename,
                        company_name=chunk.company_name,
                        collection=chunk.collection,
                        page_number=chunk.page_number,
                        confidence_score=chunk.confidence_score,
                        excerpt=None,
                        source_url=None
                    )
                    citations.append(citation)

            # Extract HIGH severity alerts only (critical alerts)
            critical_alerts = []
            if state.alert_output and state.alert_output.alerts:
                critical_alerts = [
                    alert for alert in state.alert_output.alerts
                    if alert.severity == "high"
                ]

            # Create SupervisorOutput
            supervisor_output = SupervisorOutput(
                answer=answer_text,
                agents_used=["RAG"],
                citations=citations,
                steps=steps,
                confidence_score=rag_quality.quality_score if rag_quality else 0.5,
                sentiment=state.sentiment_output,
                alerts=critical_alerts
            )

            steps.append("RAG-only synthesis: complete (fast path)")
            logger.info("RAG-only synthesis complete")

            return state.model_copy(update={"supervisor_output": supervisor_output, "steps": steps})
        except Exception as e:
            logger.error(f"RAG-only synthesis failed: {str(e)}")
            from agents.schemas import SupervisorOutput
            steps = list(state.steps) if state.steps else []
            steps.append(f"RAG-only synthesis: error - {str(e)}")

            supervisor_output = SupervisorOutput(
                answer=f"RAG-only synthesis failed: {str(e)}",
                agents_used=["RAG"],
                citations=[],
                steps=steps,
                confidence_score=0.0
            )
            return state.model_copy(update={"supervisor_output": supervisor_output, "steps": steps})

    # ======================== PUBLIC INTERFACE ========================

    def run(self, query: str, session_id: Optional[str] = None, progress_callback=None, fetch_latest_news: bool = False) -> Any:
        """Run the v2 workflow synchronously"""
        try:
            from agents.schemas import SupervisorOutput
            logger.info(f"Running workflow: fetch_latest_news={fetch_latest_news}, query={query[:80]}...")
            initial_state = AgentStateV2(query=query, steps=[], session_id=session_id, progress_callback=progress_callback, fetch_latest_news=fetch_latest_news)
            final_state = self.workflow.invoke(initial_state)

            # Handle both dict and AgentStateV2 returns
            supervisor_output = None
            steps = []

            if isinstance(final_state, dict):
                supervisor_output = final_state.get('supervisor_output')
                steps = final_state.get('steps', [])
            else:
                supervisor_output = final_state.supervisor_output
                steps = final_state.steps

            if supervisor_output:
                return supervisor_output

            # Fallback SupervisorOutput
            return SupervisorOutput(
                answer="Unable to generate response",
                agents_used=[],
                steps=steps,
                confidence_score=0.0
            )
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            from agents.schemas import SupervisorOutput
            return SupervisorOutput(
                answer=f"Error during processing: {str(e)}",
                agents_used=[],
                steps=["Error occurred"],
                confidence_score=0.0
            )

    async def arun(self, query: str, session_id: Optional[str] = None, progress_callback=None, fetch_latest_news: bool = False) -> Any:
        """Run the v2 workflow asynchronously by executing in a thread pool"""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        from functools import partial

        # Use thread pool to allow async polling while workflow executes
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(
                executor,
                partial(self.run, query, session_id, progress_callback, fetch_latest_news),
            )
