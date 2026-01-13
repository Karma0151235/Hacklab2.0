from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RawDocument(BaseModel):
    """
    Raw data container regarding a single Bursa announcement.
    Output of the scraping layer, input to the ETL/Parser layer.
    """
    source: str = "bursa"
    source_url: str
    
    # Raw Content
    raw_html: str = ""       # Full page HTML
    raw_text: str = ""       # Extracted text content
    
    # Preserved Structure
    tables_html: List[str] = Field(default_factory=list) # Raw HTML of tables found
    pdf_urls: List[str] = Field(default_factory=list)    # Links to attachments
    
    # Metadata (Light Extraction)
    announcement_date: Optional[str] = None
    title: Optional[str] = None
    company_name: Optional[str] = None
    category: Optional[str] = None
    
    # Audit
    video_base64: Optional[str] = None  # Base64 encoded WebM video of the scraping session
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True

class StructuredRecord(BaseModel):
    """
    Structured record optimized for SQL/Dashboard ingestion.
    Contains parsed fields ready for relational database storage.
    """
    # Core identifiers
    announcement_id: str
    company_code: Optional[str] = None
    
    # Basic metadata
    announcement_date: Optional[str] = None
    category: str = ""
    title: str = ""
    
    # URLs
    detail_page_url: str
    pdf_urls: List[str] = Field(default_factory=list)
    
    # Table summaries
    tables_count: int = 0
    table_titles: List[str] = Field(default_factory=list)
    
    # Extracted numeric fields (dynamic)
    numeric_fields: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    extracted_at: str
    source: str = "bursa-bm"

class DocumentObject(BaseModel):
    """
    Document object optimized for NLP/RAG system ingestion.
    Contains full text and structured data for vector embeddings.
    """
    # Identifiers
    doc_id: str
    announcement_id: str
    company_code: Optional[str] = None
    
    # Classification
    source: str = "bursa-bm"
    doc_type: str = "announcement"
    category: str = ""
    
    # Content
    title: str = ""
    raw_text: str = ""
    
    # Structured data for embedding
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata (key-value pairs for filtering)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Temporal
    announcement_date: str = ""
    extracted_at: str
    
    # Source URLs
    source_url: str
    pdf_urls: List[str] = Field(default_factory=list)
    
    # For RAG/Vector search
    keywords: List[str] = Field(default_factory=list)
    summary: str = ""

