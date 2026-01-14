"""
Pydantic schemas for agent inputs and outputs
Enforces strict typing across the entire agent system
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import pandas as pd


# ============================================================================
# RAG Agent Schemas
# ============================================================================

class RAGQuery(BaseModel):
    """Input schema for RAG Agent"""
    query: str = Field(..., description="User query for semantic search")
    top_k_text: int = Field(default=2, description="Number of text chunks to retrieve")
    top_k_table: int = Field(default=1, description="Number of table chunks to retrieve")


class ChunkMetadata(BaseModel):
    """Metadata for retrieved chunks"""
    filename: str
    company_name: str
    page_number: Optional[int] = None
    table_index: Optional[int] = None
    confidence_score: float
    collection: str  # "pdf_text_chunks" or "pdf_table_chunks"


class TableChunk(BaseModel):
    """Reconstructed table chunk"""
    table_id: str
    table_data: List[List[str]]  # List of rows
    metadata: ChunkMetadata


class RAGOutput(BaseModel):
    """Output schema for RAG Agent"""
    summary: str = Field(..., description="Summarized context from retrieved chunks")
    table_chunks: List[TableChunk] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list, description="Extracted entities")
    metadata: List[ChunkMetadata] = Field(default_factory=list)


# ============================================================================
# Financial Agent Schemas
# ============================================================================

class FinancialMetrics(BaseModel):
    """Financial metrics calculated by Financial Agent"""
    # Liquidity Ratios
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None

    # Solvency Ratios
    debt_to_equity: Optional[float] = None
    interest_coverage: Optional[float] = None

    # Profitability Ratios
    net_profit_margin: Optional[float] = None
    return_on_assets: Optional[float] = None  # ROA
    return_on_equity: Optional[float] = None  # ROE
    gross_profit_margin: Optional[float] = None
    operating_profit_margin: Optional[float] = None

    # Efficiency Ratios
    asset_turnover: Optional[float] = None
    inventory_turnover: Optional[float] = None

    # Growth Indicators
    revenue_growth_yoy: Optional[float] = None
    eps_growth: Optional[float] = None

    # Additional Metrics
    earnings_per_share: Optional[float] = None
    price_to_earnings: Optional[float] = None


class FinancialAgentInput(BaseModel):
    """Input schema for Financial Agent"""
    query: str = Field(..., description="Financial analysis query")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context from RAG")


class FinancialAgentOutput(BaseModel):
    """Output schema for Financial Agent"""
    metrics: FinancialMetrics
    source: str = Field(..., description="Source filename or page reference")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    analysis: str = Field(..., description="Analysis summary with CoT reasoning")


# ============================================================================
# Alert Agent Schemas
# ============================================================================

class AlertConfig(BaseModel):
    """Alert configuration thresholds"""
    current_ratio_min: float = 1.0
    debt_to_equity_max: float = 2.0
    net_profit_margin_min: float = 0.0
    revenue_growth_min: float = -10.0  # -10% decline triggers alert
    sentiment_threshold: float = -0.5  # Negative sentiment threshold


class Alert(BaseModel):
    """Individual alert"""
    alert_type: str = Field(..., description="Type of alert: threshold, sentiment, keyword, filing_type")
    severity: str = Field(..., description="Severity: high, medium, low")
    message: str = Field(..., description="Alert message")
    triggered_by: str = Field(..., description="What triggered this alert")


class AlertAgentInput(BaseModel):
    """Input schema for Alert Agent"""
    query: str
    financial_metrics: Optional[FinancialMetrics] = None
    rag_context: Optional[RAGOutput] = None
    config: AlertConfig = Field(default_factory=AlertConfig)


class AlertAgentOutput(BaseModel):
    """Output schema for Alert Agent"""
    alerts: List[Alert] = Field(default_factory=list)
    related_metrics: Dict[str, float] = Field(default_factory=dict)


# ============================================================================
# Supervisor Agent Schemas
# ============================================================================

class Citation(BaseModel):
    """Citation for evidence-backed responses"""
    filename: str
    company_name: str
    collection: str  # pdf_text_chunks or pdf_table_chunks
    page_number: Optional[int] = None
    confidence_score: float


class SupervisorInput(BaseModel):
    """Input schema for Supervisor Agent"""
    query: str = Field(..., description="User query for market intelligence")
    session_id: Optional[str] = None


class SupervisorOutput(BaseModel):
    """Output schema for Supervisor Agent"""
    answer: str = Field(..., description="Final aggregated answer")
    agents_used: List[str] = Field(..., description="List of agents called")
    citations: List[Citation] = Field(default_factory=list)
    steps: List[str] = Field(..., description="Chain-of-Thought reasoning steps")
    table_data: Optional[Dict[str, Any]] = Field(default=None, description="Reconstructed table data")
    confidence_score: float = Field(default=0.0, description="Overall confidence in response")


# ============================================================================
# Workflow State Schema
# ============================================================================

class WorkflowState(BaseModel):
    """State passed through LangGraph workflow"""
    query: str
    supervisor_output: Optional[SupervisorOutput] = None
    rag_output: Optional[RAGOutput] = None
    financial_output: Optional[FinancialAgentOutput] = None
    alert_output: Optional[AlertAgentOutput] = None
    steps: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True
