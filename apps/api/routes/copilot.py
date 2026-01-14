"""
Copilot API Routes
Exposes the Supervisor Multi-Agent workflow via REST API
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from workflows.intelligence_flow import run_intelligence_query, IntelligenceFlow
from agents.schemas import SupervisorOutput, SupervisorInput
from agents.config import AgentConfig

# Initialize router
router = APIRouter()
logger = logging.getLogger(__name__)

class CopilotQueryRequest(BaseModel):
    """Request model for copilot query"""
    query: str
    session_id: Optional[str] = None
    stream: bool = False  # Future support for streaming

class CopilotHealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    agents: Dict[str, str]
    milvus: str
    openrouter: str
    timestamp: str

@router.post("/copilot/query", response_model=SupervisorOutput)
async def query_copilot(request: CopilotQueryRequest):
    """
    Process a user query through the Supervisor Multi-Agent System
    
    The workflow:
    1. Supervisor analyzes query
    2. Orchestrates RAG, Financial, and Alert agents
    3. RAG retrieves from Milvus
    4. Agents process data using OpenRouter LLMs
    5. Supervisor synthesizes final response with citations and tables
    """
    try:
        logger.info(f"Received copilot query: {request.query}")
        
        # Run the intelligence workflow
        # Note: We're using the sync wrapper run_intelligence_query for now
        # In a production high-load scenario, we'd use the async flow.arun()
        
        # Initialize workflow
        flow = IntelligenceFlow()
        
        # Execute (using async method if available in flow, else sync)
        # The flow.arun method is async, so we await it
        output = await flow.arun(request.query)
        
        logger.info(f"Query processed successfully. Agents used: {output.agents_used}")
        return output
        
    except Exception as e:
        logger.error(f"Error processing copilot query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Copilot processing failed: {str(e)}")

@router.get("/copilot/health", response_model=CopilotHealthResponse)
async def health_check():
    """Check health of all agents and dependencies"""
    
    # Check Milvus connection
    milvus_status = "unknown"
    try:
        from pymilvus import connections, utility
        if not connections.has_connection("default"):
            connections.connect(host=AgentConfig.MILVUS_HOST, port=AgentConfig.MILVUS_PORT)
        
        if utility.get_server_version():
            milvus_status = "connected"
        else:
            milvus_status = "error"
    except Exception as e:
        milvus_status = f"disconnected: {str(e)}"
        
    # Check OpenRouter API key
    openrouter_status = "configured" if AgentConfig.OPENROUTER_API_KEY else "missing_key"
    
    return CopilotHealthResponse(
        status="healthy" if milvus_status == "connected" and openrouter_status == "configured" else "degraded",
        agents={
            "supervisor": "ready",
            "rag": "ready",
            "financial": "ready",
            "alert": "ready"
        },
        milvus=milvus_status,
        openrouter=openrouter_status,
        timestamp=datetime.now().isoformat()
    )
