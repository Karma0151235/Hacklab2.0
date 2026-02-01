"""
LangGraph Workflow for Market Intelligence
Orchestrates agent execution with state management
"""

from typing import TypedDict, Annotated, Sequence, Optional, Callable, Dict, Any
import sys
from pathlib import Path
import operator

sys.path.insert(0, str(Path(__file__).parent.parent))

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

from agents.schemas import (
    SupervisorInput,
    SupervisorOutput,
    WorkflowState,
)
from agents.supervisor import SupervisorAgent
from etl.logging_config import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict):
    """State passed through the workflow"""
    query: str
    supervisor_output: SupervisorOutput
    messages: Annotated[Sequence[BaseMessage], operator.add]
    error: str
    progress_callback: Optional[Callable[[Dict[str, Any]], None]]


class IntelligenceFlow:
    """
    LangGraph workflow for market intelligence

    Workflow:
    1. Input → Supervisor Agent
    2. Supervisor orchestrates:
       - RAG Agent (retrieval)
       - Financial Agent (metrics)
       - Alert Agent (alerts)
    3. Supervisor aggregates → Output
    4. Output structured for frontend/API
    """

    def __init__(self):
        """Initialize intelligence workflow"""
        logger.info("Initializing Intelligence Flow workflow")

        # Initialize supervisor (which initializes all sub-agents)
        self.supervisor = SupervisorAgent()

        # Build LangGraph workflow
        self.workflow = self._build_workflow()

        logger.info("Intelligence Flow workflow ready")

    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""

        # Define workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("process_output", self._process_output_node)
        workflow.add_node("handle_error", self._handle_error_node)

        # Define edges
        workflow.set_entry_point("supervisor")

        # Conditional routing based on supervisor output
        workflow.add_conditional_edges(
            "supervisor",
            self._should_continue,
            {
                "continue": "process_output",
                "error": "handle_error"
            }
        )

        workflow.add_edge("process_output", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    def _supervisor_node(self, state: AgentState) -> AgentState:
        """Execute supervisor agent"""
        try:
            logger.info("Executing supervisor node")

            query = state["query"]
            progress_callback = state.get("progress_callback")

            # Call supervisor
            supervisor_input = SupervisorInput(query=query)
            supervisor_output = self.supervisor.process(supervisor_input, progress_callback=progress_callback)

            state["supervisor_output"] = supervisor_output

            logger.info("Supervisor node completed")
            return state

        except Exception as e:
            logger.error(f"Error in supervisor node: {str(e)}")
            state["error"] = str(e)
            return state

    def _process_output_node(self, state: AgentState) -> AgentState:
        """Process and format output"""
        try:
            logger.info("Processing output")

            supervisor_output = state["supervisor_output"]

            # Output is already in structured format (Pydantic model)
            # Can add additional processing here if needed

            logger.info("Output processing completed")
            return state

        except Exception as e:
            logger.error(f"Error processing output: {str(e)}")
            state["error"] = str(e)
            return state

    def _handle_error_node(self, state: AgentState) -> AgentState:
        """Handle errors"""
        logger.error(f"Handling error: {state.get('error', 'Unknown error')}")

        # Create error response
        state["supervisor_output"] = SupervisorOutput(
            answer=f"Error processing query: {state.get('error', 'Unknown error')}",
            agents_used=[],
            citations=[],
            steps=["Error occurred during processing"],
            confidence_score=0.0
        )

        return state

    def _should_continue(self, state: AgentState) -> str:
        """Determine next step based on state"""
        if "error" in state and state["error"]:
            return "error"
        return "continue"

    def run(self, query: str, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> SupervisorOutput:
        """
        Run intelligence workflow for a query

        Args:
            query: User query string

        Returns:
            SupervisorOutput with comprehensive response
        """
        try:
            logger.info(f"Running intelligence workflow for query: {query}")

            # Initialize state
            initial_state = {
                "query": query,
                "supervisor_output": None,
                "messages": [],
                "error": "",
                "progress_callback": progress_callback,
            }

            # Execute workflow
            final_state = self.workflow.invoke(initial_state)

            # Extract output
            output = final_state["supervisor_output"]

            logger.info("Intelligence workflow completed successfully")
            return output

        except Exception as e:
            logger.error(f"Error running intelligence workflow: {str(e)}")

            # Return error response
            return SupervisorOutput(
                answer=f"Error processing query: {str(e)}",
                agents_used=[],
                citations=[],
                steps=["Workflow execution failed"],
                confidence_score=0.0
            )

    async def arun(self, query: str, progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> SupervisorOutput:
        """
        Async version of run

        Args:
            query: User query string

        Returns:
            SupervisorOutput with comprehensive response
        """
        try:
            logger.info(f"Running async intelligence workflow for query: {query}")

            # Initialize state
            initial_state = {
                "query": query,
                "supervisor_output": None,
                "messages": [],
                "error": "",
                "progress_callback": progress_callback,
            }

            # Execute workflow asynchronously
            final_state = await self.workflow.ainvoke(initial_state)

            # Extract output
            output = final_state["supervisor_output"]

            logger.info("Async intelligence workflow completed successfully")
            return output

        except Exception as e:
            logger.error(f"Error running async intelligence workflow: {str(e)}")

            # Return error response
            return SupervisorOutput(
                answer=f"Error processing query: {str(e)}",
                agents_used=[],
                citations=[],
                steps=["Async workflow execution failed"],
                confidence_score=0.0
            )


# Convenience function for direct usage
def run_intelligence_query(query: str) -> SupervisorOutput:
    """
    Run intelligence query directly

    Args:
        query: User query string

    Returns:
        SupervisorOutput with comprehensive response
    """
    flow = IntelligenceFlow()
    return flow.run(query)
