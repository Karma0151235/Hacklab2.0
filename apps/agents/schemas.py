"""
Pydantic schemas for agent inputs and outputs
Enforces strict typing across the entire agent system
"""

from typing import List, Optional, Dict, Any, Annotated
from pydantic import BaseModel, Field
from datetime import datetime
import pandas as pd
from scraping.news.schemas import NewsArticle
from operator import add

# Reducer function for list fields that may be updated concurrently
def _list_reducer(existing: List[str], new: List[str]) -> List[str]:
    """Combine lists from concurrent updates"""
    if not existing:
        return new
    if not new:
        return existing
    # Combine and deduplicate while preserving order
    seen = set(existing)
    combined = list(existing)
    for item in new:
        if item not in seen:
            combined.append(item)
            seen.add(item)
    return combined


# ============================================================================
# RAG Agent Schemas
# ============================================================================

class RAGQuery(BaseModel):
    """Input schema for RAG Agent"""
    query: str = Field(..., description="User query for semantic search")
    top_k_text: int = Field(default=2, description="Number of text chunks to retrieve")
    top_k_table: int = Field(default=1, description="Number of table chunks to retrieve")
    company_name: Optional[str] = Field(default=None, description="Company name filter for retrieval")


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


class TextChunk(BaseModel):
    """Retrieved text chunk with content"""
    chunk_id: str
    filename: str
    company_name: str
    content: str
    page_number: Optional[int] = None
    confidence_score: float
    collection: str


class RAGOutput(BaseModel):
    """Output schema for RAG Agent"""
    summary: str = Field(..., description="Summarized context from retrieved chunks")
    table_chunks: List[TableChunk] = Field(default_factory=list)
    text_chunks: List[TextChunk] = Field(default_factory=list)
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
# Sentiment Agent Schemas
# ============================================================================

class SentimentAgentInput(BaseModel):
    """Input schema for Sentiment Agent"""
    query: str = Field(..., description="Query for sentiment analysis")
    company_name: Optional[str] = Field(default=None, description="Company to focus analysis on")
    news_articles: List[NewsArticle] = Field(default_factory=list, description="News articles to analyze")
    rag_context: Optional[RAGOutput] = Field(default=None, description="Additional context from RAG")


class SentimentAgentOutput(BaseModel):
    """Output schema for Sentiment Agent"""
    overall_sentiment: str = Field(..., description="Overall sentiment: positive, neutral, negative")
    sentiment_score: float = Field(..., ge=-1.0, le=1.0, description="Sentiment score from -1.0 to 1.0")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in analysis")
    
    # Detailed breakdown
    sentiment_by_source: Dict[str, float] = Field(default_factory=dict, description="Sentiment by news source")
    key_topics: List[str] = Field(default_factory=list, description="Key topics identified")
    key_phrases: List[str] = Field(default_factory=list, description="Key phrases influencing sentiment")
    
    # Trend analysis
    trend: str = Field(default="stable", description="Sentiment trend: improving, stable, declining")
    trend_explanation: str = Field(default="", description="Explanation for trend")
    
    # Company-specific
    company_sentiments: Dict[str, float] = Field(default_factory=dict, description="Sentiment by company")
    
    # Summary
    summary: str = Field(..., description="Human-readable summary of sentiment analysis")
    articles_analyzed: int = Field(default=0, description="Number of articles analyzed")
    
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


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
    excerpt: Optional[str] = None
    source_url: Optional[str] = None


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
    sentiment: Optional[SentimentAgentOutput] = Field(default=None, description="Sentiment analysis results")
    confidence_score: float = Field(default=0.0, description="Overall confidence in response")


# ============================================================================
# Intent Classification Schemas (V2)
# ============================================================================

class IntentClassification(BaseModel):
    """Intent classification results from IntentClassifier"""
    primary_intent: str = Field(..., description="Main intent: financial_analysis, risk_assessment, trend_analysis, information_retrieval")
    secondary_intents: List[str] = Field(default_factory=list, description="Other detected intents")
    required_agents: List[str] = Field(..., description="Agents that must run: rag, financial, alert")
    optional_agents: List[str] = Field(default_factory=list, description="Agents that could enhance response")
    data_quality_requirements: Dict[str, float] = Field(default_factory=dict, description="Min confidence scores, chunk counts")
    priority_level: str = Field(default="normal", description="critical, high, normal, low")
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence")
    reasoning: str = Field(..., description="Why this classification was made")


class FinancialAgentRouting(BaseModel):
    """Routing decision from Financial Agent"""
    status: str = Field(..., description="complete, partial, or skip")
    reason: str = Field(..., description="Why this routing decision")
    should_continue_pipeline: bool = Field(..., description="Whether to proceed to Alert agent")
    metrics_available: int = Field(default=0, description="Number of calculated metrics")
    metrics_calculated: List[str] = Field(default_factory=list, description="Names of calculated metrics")
    metrics_missing: List[str] = Field(default_factory=list, description="Names of metrics that couldn't be calculated")
    recommended_next_step: str = Field(..., description="analyze_fully, partial_analysis, or skip_to_alerts_only")


class AlertAgentRouting(BaseModel):
    """Routing decision from Alert Agent"""
    status: str = Field(..., description="high_alerts, low_alerts, or no_alerts")
    alert_count: int = Field(default=0)
    high_severity_count: int = Field(default=0)
    low_severity_count: int = Field(default=0)
    recommendation: str = Field(..., description="escalate, monitor, or routine")
    requires_human_review: bool = Field(default=False)
    dominant_alert_type: Optional[str] = None


class ExtractedFinancialData(BaseModel):
    """Extracted financial data with validation metadata"""
    extracted_values: Dict[str, float] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    data_quality: float = Field(ge=0.0, le=1.0, description="Data quality score")
    extraction_confidence: float = Field(ge=0.0, le=1.0, description="LLM extraction confidence")
    extraction_status: str = Field(default="success", description="success or error")
    extraction_errors: List[str] = Field(default_factory=list)


class RAGQualityAssessment(BaseModel):
    """Assessment of RAG output quality"""
    quality_score: float = Field(ge=0.0, le=1.0)
    chunk_count: int
    avg_confidence: float = Field(ge=0.0, le=1.0)
    summary_length: int
    has_errors: bool = Field(default=False)
    error_indicators: List[str] = Field(default_factory=list)
    assessment: str = Field(..., description="high_quality, low_quality, insufficient")


# ============================================================================
# Workflow State Schema
# ============================================================================

class WorkflowState(BaseModel):
    """State passed through LangGraph workflow (V1)"""
    query: str
    supervisor_output: Optional[SupervisorOutput] = None
    rag_output: Optional[RAGOutput] = None
    financial_output: Optional[FinancialAgentOutput] = None
    alert_output: Optional[AlertAgentOutput] = None
    steps: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


class AgentStateV2(BaseModel):
    """Enhanced state for V2 workflow with intent classification and routing"""
    query: str

    # Intent classification
    intent: Optional[IntentClassification] = None

    # RAG results
    rag_output: Optional[RAGOutput] = None
    rag_quality: Optional[RAGQualityAssessment] = None

    # Extracted financial data
    extracted_financial_data: Optional[ExtractedFinancialData] = None

    # Agent outputs
    financial_output: Optional[FinancialAgentOutput] = None
    financial_routing: Optional[FinancialAgentRouting] = None

    alert_output: Optional[AlertAgentOutput] = None
    alert_routing: Optional[AlertAgentRouting] = None

    sentiment_output: Optional[SentimentAgentOutput] = None

    # Final output
    supervisor_output: Optional[SupervisorOutput] = None

    # Tracking and control
    steps: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    progress_callback: Optional[Any] = None  # Callable, but Any for serialization
    session_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
