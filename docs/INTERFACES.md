# Phase Interfaces & Data Contracts

## Phase 1: Scraping → ETL

### Output: RawDocument (JSON)

```python
class TableRow(BaseModel):
    headers: List[str]
    rows: List[List[str]]
    raw_html: str

class RawDocument(BaseModel):
    doc_id: str  # BURSA_{TICKER}_{YYYYMMDD}_{SEQ}
    source: str  # "bursa"
    source_url: str
    company_name: str
    company_code: str  # 4 digits
    ticker: str
    document_type: str  # DIVIDEND_ANNOUNCEMENT, SHAREHOLDING_NOTICE, etc
    published_at: datetime
    content: {
        text: str,           # visible text only
        raw_html: str,       # full page HTML
        tables: List[TableRow]
    }
    files: List[{
        file_type: str,      # pdf, xlsx, doc
        original_filename: str,
        local_path: str,
        download_url: str
    }]
    scrape_metadata: {
        scraped_at: datetime,
        scraper_version: str,
        phase_completed: int,
        confidence: float,   # 0.0-1.0
        errors: List[str]
    }
```

### Directory Structure
```
storage/raw/bursa/
├── 2025-01-10/
│   ├── BURSA_GLICO_20250110_001.json
│   ├── BURSA_MAYBANK_20250110_001.json
│   └── ...
└── 2025-01-11/
    └── ...

storage/raw/pdfs/
├── BURSA_GLICO_20250110_001.pdf
└── ...
```

### Scraper MUST
- Extract text, HTML, tables, PDFs
- Validate RawDocument before save
- One file per announcement

### Scraper MUST NOT
- NLP, OCR, parsing, classification
- Transform HTML tables
- Extract structured fields
- Import from etl/, agents/, storage/

---

## Phase 2: ETL Ingestion → Transformation

### Input: RawDocument (JSON from storage/raw/bursa/)

### Output: StructuredRecord + DocumentObject

```python
class StructuredRecord(BaseModel):
    doc_id: str
    source: str
    announcement_id: str
    company_code: str
    announcement_date: date
    document_type: str
    title: str
    parsed_fields: Dict[str, Any]  # dividend_per_share, ex_date, etc
    source_text: str
    created_at: datetime

class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    chunk_order: int

class DocumentObject(BaseModel):
    doc_id: str
    source: str
    company_code: str
    ticker: str
    document_type: str
    title: str
    raw_text: str
    tables: List[Dict[str, Any]]  # normalized
    metadata: Dict[str, Any]
    keywords: List[str]
    summary: str
    chunks: List[DocumentChunk]
    created_at: datetime
```

### Directory Structure
```
storage/processed/
├── structured_records/
│   ├── 2025-01-10/
│   │   ├── BURSA_GLICO_20250110_001.json
│   │   └── ...
│   └── ...
├── document_objects/
│   ├── 2025-01-10/
│   │   ├── BURSA_GLICO_20250110_001.json
│   │   └── ...
│   └── ...
└── chunks/
    ├── BURSA_GLICO_20250110_001_chunk_001.json
    ├── BURSA_GLICO_20250110_001_chunk_002.json
    └── ...
```

### ETL MUST
- Read RawDocument from storage/raw/bursa/
- Validate Pydantic models
- Generate StructuredRecord, DocumentObject, chunks
- Save to storage/processed/

### ETL MUST NOT
- Call agents, LLMs
- Import from scraping/ directly (only read files)
- Modify scraper output format

---

## Phase 3: Storage (PostgreSQL + Vector DB)

### Input: StructuredRecord + DocumentObject (JSON from storage/processed/)

### Output: Database Records + Vector Embeddings

```python
# PostgreSQL Models (SQLAlchemy)
class Company(Base):
    company_code: str  # PK
    company_name: str
    ticker: str

class Filing(Base):
    filing_id: str  # PK
    company_code: FK
    announcement_date: date
    document_type: str
    title: str
    raw_text: str

class ParsedTable(Base):
    table_id: str  # PK
    filing_id: FK
    table_data: JSON

class FinancialRatio(Base):
    ratio_id: str  # PK
    company_code: FK
    statement_date: date
    ratio_name: str
    ratio_value: float

# Vector DB
class Embedding(BaseModel):
    chunk_id: str
    embedding: List[float]  # 1536-dim OpenAI
    metadata: Dict[str, Any]
```

### Directory Structure
```
storage/
├── processed/        # ETL outputs
├── postgres_data/    # PostgreSQL data files
├── vector_db/        # Pinecone/Weaviate indexes
└── raw/             # Raw archives (RawDocument)
```

### Storage MUST
- Insert StructuredRecord → Filing
- Insert chunks → Vector DB
- Generate embeddings
- Maintain referential integrity

---

## Phase 4: Intelligence Layer (Agents)

### Input: PostgreSQL + Vector DB queries

### Output: Agent Responses

```python
class Citation(BaseModel):
    source: str
    link: str
    page: Optional[int]
    excerpt: str

class CopilotAnswer(BaseModel):
    answer_text: str
    citations: List[Citation]
    tables: Optional[List[Dict]]
    alerts: Optional[List[Dict]]
    confidence: float
    source_agents: List[str]  # "rag", "sql", "financial"
```

### Agents

```python
# Supervisor Agent
class SupervisorAgent:
    def decide_path(query: str) -> List[str]
        # Returns: ["rag"], ["sql"], ["rag", "financial"], etc

# RAG Agent
class RAGAgent:
    def search_and_ground(query: str) -> CopilotAnswer
        # Vector search → retrieve chunks → ground answer

# SQL Agent
class SQLAgent:
    def nl_to_sql(query: str) -> CopilotAnswer
        # NL → SQL → execute → tabular result

# Financial Agent
class FinancialAgent:
    def analyze_ratios(company_code: str) -> CopilotAnswer
        # Fetch ratios → interpret → explain

# Alert Agent
class AlertAgent:
    def evaluate_rules(company_code: str) -> CopilotAnswer
        # Check thresholds → surface risks
```

### Directory Structure
```
apps/agents/
├── supervisor.py      # Route queries
├── rag_agent.py       # Semantic search
├── sql_agent.py       # NL → SQL
├── financial_agent.py # Ratio analysis
└── alert_agent.py     # Risk evaluation

apps/workflows/
└── intelligence_flow.py  # LangGraph orchestration
```

### Agents MUST
- Query PostgreSQL + Vector DB only
- Return CopilotAnswer with citations
- Never modify data
- Handle missing data gracefully

---

## Phase 5: API Layer

### Input: User queries (HTTP POST)

### Output: JSON responses

```python
# POST /api/v1/copilot/chat
class ChatRequest(BaseModel):
    query: str
    company_code: Optional[str]
    filters: Optional[Dict]

class ChatResponse(BaseModel):
    success: bool
    data: CopilotAnswer
    execution_time_ms: float
    timestamp: datetime

# GET /api/v1/filings
class FilingsResponse(BaseModel):
    filings: List[Filing]
    total: int
    timestamp: datetime

# POST /api/v1/ingest/bursa
class IngestRequest(BaseModel):
    year: int
    max_announcements: int

class IngestResponse(BaseModel):
    job_id: str
    status: str  # "queued", "running", "complete"
    documents_processed: int
```

### Directory Structure
```
apps/api/
├── main.py                # FastAPI app
├── deps.py               # Dependency injection
├── routes/
│   ├── copilot.py       # Chat endpoints
│   ├── filings.py       # Filing retrieval
│   ├── ingest.py        # Ingestion trigger
│   ├── alerts.py        # Alert management
│   └── health.py        # Status checks
└── schemas/
    └── requests.py      # Request/Response models
```

### API MUST
- Validate inputs (Pydantic)
- Call agents via workflows
- Return CopilotAnswer with citations
- Handle errors gracefully

---

## Summary: Data Flow

```
RawDocument (Scraper)
    ↓ [storage/raw/bursa/]
StructuredRecord + DocumentObject (ETL)
    ↓ [storage/processed/]
PostgreSQL + Vector DB (Storage)
    ↓
Agents (Supervisor → RAG/SQL/Financial/Alert)
    ↓
CopilotAnswer (API)
    ↓
Frontend (Next.js Dashboard + Chat)
```

---

## Critical Rules

1. **Scraping** outputs JSON only (no transformation)
2. **ETL** reads JSON, writes to PostgreSQL + Vector DB
3. **Agents** query PostgreSQL + Vector DB only
4. **API** invokes agents, returns CopilotAnswer
5. **No layer** imports from previous layer's code (only reads output files)
