"""
Copilot API Routes
Exposes the Supervisor Multi-Agent workflow via REST API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Callable
import logging
from datetime import datetime
import os
from uuid import uuid4
import asyncio

from agents.schemas import SupervisorOutput, SupervisorInput
from agents.config import AgentConfig

# Initialize router
router = APIRouter()
logger = logging.getLogger(__name__)
_flow_instance = None
_copilot_jobs: Dict[str, Dict[str, Any]] = {}

DEFAULT_AGENT_IDS = ["supervisor", "rag", "financial", "alert", "sentiment"]

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


class CopilotAgentStatus(BaseModel):
    status: str
    logs: List[str]
    latest_message: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None


class CopilotJobStatus(BaseModel):
    job_id: str
    query: str
    status: str
    started_at: str
    updated_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    steps: List[str] = []
    agents: Dict[str, CopilotAgentStatus]


def _get_flow():
    """Get or create a cached IntelligenceFlowV2 instance."""
    global _flow_instance
    if _flow_instance is not None:
        return _flow_instance

    try:
        from workflows.intelligence_flow_v2 import IntelligenceFlowV2
    except ModuleNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"Workflow dependency missing: {str(e)}")

    try:
        _flow_instance = IntelligenceFlowV2()
    except (ModuleNotFoundError, ImportError) as e:
        _flow_instance = None
        raise HTTPException(status_code=503, detail=f"Workflow dependency missing: {str(e)}")
    return _flow_instance


def _init_job_status(job_id: str, query: str) -> None:
    now = datetime.now().isoformat()
    _copilot_jobs[job_id] = {
        "job_id": job_id,
        "query": query,
        "status": "running",
        "started_at": now,
        "updated_at": now,
        "completed_at": None,
        "error": None,
        "steps": [],
        "agents": {
            agent_id: {
                "status": "waiting",
                "logs": [],
                "latest_message": "",
                "started_at": None,
                "completed_at": None,
                "duration_ms": None,
            }
            for agent_id in DEFAULT_AGENT_IDS
        },
        "result": None,
    }


def _append_agent_log(job_id: str, agent_id: str, message: str, status: Optional[str] = None) -> None:
    job = _copilot_jobs.get(job_id)
    if not job:
        return

    timestamp = datetime.now().strftime("%H:%M:%S")
    log_line = f"{timestamp} - {message}"

    agent = job["agents"].setdefault(
        agent_id,
        {
            "status": "waiting",
            "logs": [],
            "latest_message": "",
            "started_at": None,
            "completed_at": None,
            "duration_ms": None,
        },
    )

    if status:
        agent["status"] = status
        if status == "running" and not agent["started_at"]:
            agent["started_at"] = datetime.now().isoformat()
        if status in {"completed", "error", "skipped"}:
            agent["completed_at"] = datetime.now().isoformat()
            if agent["started_at"]:
                started = datetime.fromisoformat(agent["started_at"])
                ended = datetime.fromisoformat(agent["completed_at"])
                agent["duration_ms"] = int((ended - started).total_seconds() * 1000)

    agent["logs"].append(log_line)
    agent["latest_message"] = message
    job["updated_at"] = datetime.now().isoformat()


def _append_step(job_id: str, step: str) -> None:
    job = _copilot_jobs.get(job_id)
    if not job:
        return
    job["steps"].append(step)
    job["updated_at"] = datetime.now().isoformat()


def _build_progress_callback(job_id: str) -> Callable[[Dict[str, Any]], None]:
    def _callback(event: Dict[str, Any]) -> None:
        agent_id = event.get("agent_id", "supervisor")
        status = event.get("status")
        message = event.get("message", "")
        step = event.get("step")
        if step:
            _append_step(job_id, step)
        if message:
            _append_agent_log(job_id, agent_id, message, status=status)
        elif status:
            _append_agent_log(job_id, agent_id, f"Status: {status}", status=status)
    return _callback

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
    global _flow_instance
    if not AgentConfig.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="OpenRouter API key not configured")

    try:
        logger.info(f"Received copilot query: {request.query}")

        # Run the v2 intelligence workflow
        flow = _get_flow()

        # Execute the workflow with v2 interface
        output = await flow.arun(
            query=request.query,
            session_id=request.session_id
        )

        logger.info(f"Query processed successfully. Agents used: {output.agents_used}")
        return output
        
    except HTTPException:
        raise
    except (ModuleNotFoundError, ImportError) as e:
        _flow_instance = None
        raise HTTPException(status_code=503, detail=f"Workflow dependency missing: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing copilot query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Copilot processing failed: {str(e)}")


@router.post("/copilot/start", response_model=CopilotJobStatus)
async def start_copilot_job(request: CopilotQueryRequest):
    """Start a copilot job and return a job id for progress tracking."""
    if not AgentConfig.OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="OpenRouter API key not configured")

    job_id = f"copilot_{uuid4().hex[:12]}"
    _init_job_status(job_id, request.query)

    async def _run_job():
        try:
            flow = _get_flow()
            progress_callback = _build_progress_callback(job_id)
            _append_agent_log(job_id, "supervisor", "Workflow started", status="running")
            output = await flow.arun(
                query=request.query,
                session_id=request.session_id,
                progress_callback=progress_callback
            )
            _copilot_jobs[job_id]["result"] = output.dict()
            _copilot_jobs[job_id]["status"] = "completed"
            _copilot_jobs[job_id]["completed_at"] = datetime.now().isoformat()
            _append_agent_log(job_id, "supervisor", "Workflow completed", status="completed")
        except Exception as e:
            _copilot_jobs[job_id]["status"] = "error"
            _copilot_jobs[job_id]["error"] = str(e)
            _copilot_jobs[job_id]["completed_at"] = datetime.now().isoformat()
            _append_agent_log(job_id, "supervisor", f"Workflow failed: {str(e)}", status="error")

    asyncio.create_task(_run_job())
    return CopilotJobStatus(**{k: v for k, v in _copilot_jobs[job_id].items() if k != "result"})


@router.get("/copilot/status/{job_id}", response_model=CopilotJobStatus)
async def get_copilot_status(job_id: str):
    job = _copilot_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Copilot job not found")
    return CopilotJobStatus(**{k: v for k, v in job.items() if k != "result"})


@router.get("/copilot/results/{job_id}", response_model=SupervisorOutput)
async def get_copilot_results(job_id: str):
    job = _copilot_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Copilot job not found")
    if job["status"] == "error":
        raise HTTPException(status_code=500, detail=job.get("error", "Copilot job failed"))
    if job["status"] != "completed":
        raise HTTPException(status_code=409, detail="Copilot job not completed yet")
    return SupervisorOutput(**job["result"])

@router.get("/copilot/health", response_model=CopilotHealthResponse)
async def health_check():
    """Check health of all agents and dependencies"""
    
    # Check Milvus connection
    milvus_status = "unknown"
    try:
        from pymilvus import connections, utility
        if not connections.has_connection("default"):
            milvus_host = os.getenv("MILVUS_HOST", AgentConfig.MILVUS_HOST)
            milvus_port = int(os.getenv("MILVUS_PORT", AgentConfig.MILVUS_PORT))
            connections.connect(host=milvus_host, port=milvus_port)
        
        if utility.get_server_version():
            milvus_status = "connected"
        else:
            milvus_status = "error"
    except Exception as e:
        milvus_status = f"disconnected: {str(e)}"
        
    # Check OpenRouter API key
    openrouter_status = "configured" if os.getenv("OPENROUTER_API_KEY") else "missing_key"
    
    return CopilotHealthResponse(
        status="healthy" if milvus_status == "connected" and openrouter_status == "configured" else "degraded",
        agents={
            "supervisor": "ready",
            "rag": "ready",
            "financial": "ready",
            "alert": "ready",
            "sentiment": "ready"
        },
        milvus=milvus_status,
        openrouter=openrouter_status,
        timestamp=datetime.now().isoformat()
    )
