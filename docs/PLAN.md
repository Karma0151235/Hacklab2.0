
# Qualitative Market Intelligence Surveillance

**MVP – Context & System Flow**

---

## 0. System Goal (One Sentence)

Build an MVP system that  **ingests Bursa announcements and targeted news** , converts them into  **structured knowledge + financial ratios** , surfaces  **high-precision alerts** , and enables an **evidence-grounded GenAI Copilot** using  **RAG + SQL** , orchestrated by a supervisor agent.

---

## 1. Architectural Principles (Non-Negotiable)

1. **ETL is deterministic, not agentic**
2. **Agents reason; pipelines transform**
3. **All interfaces are schema-first (Pydantic)**
4. **Copilot answers must be evidence-backed**
5. **Structured ≠ Unstructured paths are separated**
6. **Supervisor controls flow, not logic duplication**

---

## 2. High-Level End-to-End Flow

```
Bursa Announcements
        ↓
Scraping Layer (Playwright web scraping + video)
        ↓
RawDocument (raw HTML, text, tables)
        ↓
ETL Layer (Ingestion + Transformation)
   ├─ Input: scraping/ outputs + frontend file uploads
   └─ Transform: OCR, PDF parsing, table extraction, normalization
        ↓
Structured Records + Document Objects
        ↓
Storage Layer (PostgreSQL + Vector DB)
        ↓
Intelligence Layer (Supervisor Agent + RAG/SQL/Financial/Alert Agents)
        ↓
API Layer (FastAPI REST endpoints)
        ↓
Frontend (Next.js Dashboard + Copilot)
```

---

## 3. Complete Project Structure & File Organization

```
project-root/
│
├── scraping/                       # HOW data is scraped (Playwright automation)
│   ├── __init__.py
│   │
│   ├── browser/                    # Playwright infrastructure
│   │   ├── playwright.py           # PlaywrightBrowser, BrowserSession
│   │   │   ├── launch()            # Browser startup (Phase 1)
│   │   │   ├── create_context()    # Video recording enabled (Phase 1)
│   │   │   ├── inject_bounding_box_helpers()  # JS injection (Phase 9)
│   │   │   └── finalize_video()    # Video encoding (Phase 10)
│   │   │
│   │   └── actions.py              # Page interactions
│   │       ├── scroll_natural()
│   │       ├── draw_bounding_boxes()  # Phase 6
│   │       ├── wait_for_selector()
│   │       └── get_page_content()
│   │
│   ├── bursa/                      # Bursa-specific scrapers (Phases 2-5)
│   │   ├── listing_crawler.py      # crawl yearly announcement listings (Phase 2)
│   │   ├── announcement_fetcher.py # visit announcement pages (Phase 3)
│   │   ├── html_parser.py          # extract tables + text (Phases 4-5)
│   │   ├── pdf_downloader.py       # download linked PDFs
│   │   └── selectors.py            # CSS/XPath selectors (SSOT)
│   │
│   ├── progress/                   # Real-time progress tracking
│   │   ├── redis_store.py          # store scraping progress
│   │   └── task_state.py           # manage task lifecycle
│   │
│   ├── common/                     # Shared utilities
│   │   ├── schemas.py              # RawDocument schema
│   │   ├── utils.py                # Helpers (normalize_date, clean_html)
│   │   ├── html_utils.py           # HTML parsing utilities
│   │   └── pdf_utils.py            # PDF handling utilities
│   │
│   └── scraper_runner.py           # entrypoint for scraping jobs
│                                    # Output: RawDocument files
│
├── etl/                            # DETERMINISTIC TRANSFORMATIONS + INGESTION
│   ├── __init__.py
│   │
│   ├── ingestion/                  # Input handling (from scraping/ + frontend)
│   │   ├── raw_document_loader.py  # Load RawDocument from scraping/
│   │   ├── file_uploader.py        # Handle frontend file uploads (PDF, CSV)
│   │   └── input_validator.py      # Validate input schemas
│   │
│   ├── preprocess.py               # clean HTML, normalize text
│   │
│   ├── ocr/
│   │   ├── paddle_runner.py        # PaddleOCR orchestration
│   │   └── image_utils.py          # image preprocessing
│   │
│   ├── pdf/
│   │   ├── docling_parser.py       # Docling layout-aware parsing
│   │   ├── mineru_adapter.py       # MinerU extraction adapter
│   │   └── table_extractor.py      # table detection & parsing
│   │
│   ├── html/
│   │   ├── table_parser.py         # Parse HTML tables into structured data
│   │   ├── text_extractor.py       # Extract + normalize text
│   │   └── link_extractor.py       # Extract references & citations
│   │
│   ├── financials/
│   │   ├── statement_mapper.py     # IS / BS / CF normalization
│   │   └── ratio_engine.py         # compute financial ratios
│   │
│   ├── chunking.py                 # generate RAG chunks from documents
│   └── etl_runner.py               # orchestrates all ETL steps
│                                    # Input: scraping/ outputs + file uploads
│                                    # Output: StructuredRecord + DocumentObject
│
├── storage/                        # PERSISTENCE LAYER
│   ├── __init__.py
│   │
│   ├── postgres/
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   ├── repositories.py         # CRUD operations
│   │   └── migrations/             # Alembic migration scripts
│   │
│   ├── vector/
│   │   ├── embeddings.py           # LLM embedding generation
│   │   └── vector_store.py         # Vector DB client (Pinecone/Weaviate)
│   │
│   └── raw/                        # archived raw HTML/PDFs
│       ├── html/                   # archived HTML dumps
│       └── pdfs/                   # downloaded PDF files
│
├── schemas/                        # Pydantic contracts (SSOT - Single Source of Truth)
│   ├── __init__.py
│   ├── raw_document.py             # RawDocument schema
│   ├── parsed_document.py          # ParsedDocument schema
│   ├── chunk.py                    # DocumentChunk schema
│   ├── financials.py               # FinancialStatement, Ratio schemas
│   ├── alerts.py                   # AlertRule, Alert schemas
│   ├── sql.py                      # SQL query result schemas
│   └── copilot.py                  # CopilotAnswer, Citation schemas
│
├── agents/                         # REASONING & INTELLIGENCE LAYER
│   ├── __init__.py
│   │
│   ├── supervisor.py               # Supervisor agent (decides RAG vs SQL vs Alerts)
│   ├── rag_agent.py                # RAG agent (semantic search + grounding)
│   ├── sql_agent.py                # SQL agent (NL → SQL translation)
│   ├── financial_agent.py          # Financial analysis agent
│   ├── alert_agent.py              # Risk & alert evaluation agent
│   └── nlp_agent.py                # NLP utilities (summarization, etc)
│
├── workflows/                      # LangGraph orchestration & state management
│   ├── __init__.py
│   └── intelligence_flow.py        # LangGraph workflow definition
│
├── api/                            # FASTAPI REST API
│   ├── main.py                     # FastAPI app instantiation
│   ├── deps.py                     # dependency injection (DB, Redis, etc)
│   │
│   └── routes/
│       ├── __init__.py
│       ├── ingest.py               # POST /ingest/* endpoints
│       ├── intelligence.py         # POST /intelligence/* (Copilot)
│       ├── sql.py                  # POST /sql (NL → SQL)
│       ├── alerts.py               # GET /alerts/* (alert management)
│       ├── documents.py            # GET /documents/* (retrieval)
│       └── health.py               # GET /health (status checks)
│
├── frontend/                       # NEXT.JS / REACT UI
│   ├── dashboard/
│   │   ├── pages/
│   │   │   ├── companies.tsx       # Company 360 view
│   │   │   ├── filings.tsx         # Filing timeline
│   │   │   ├── sentiment.tsx       # Sentiment trends
│   │   │   ├── financials.tsx      # Financial snapshot
│   │   │   └── alerts.tsx          # Alert history
│   │   └── components/
│   │
│   └── copilot/
│       ├── pages/
│       │   └── chat.tsx            # Copilot chat interface
│       └── components/
│           ├── ChatWindow.tsx
│           ├── CitationBlock.tsx
│           └── AlertHighlight.tsx
│
├── infra/                          # Docker & infrastructure
│   ├── docker-compose.yml          # Services: API, Redis, Postgres, Vector DB
│   ├── redis/
│   │   └── Dockerfile              # Redis for progress tracking
│   └── postgres/
│       ├── Dockerfile
│       └── init.sql                # database initialization
│
├── evaluation/                     # QUALITY METRICS & TESTING
│   ├── __init__.py
│   ├── ocr_accuracy.py             # OCR output accuracy measurement
│   ├── classifier_metrics.py       # Categorization accuracy
│   ├── alert_precision.py          # Alert precision & recall
│   ├── copilot_grounding.py        # Citation accuracy & hallucination checks
│   └── test_data/                  # sample documents for evaluation
│
├── docs/                           # DOCUMENTATION
│   ├── Architecture.md             # Detailed architecture diagrams
│   ├── Structure&Interface.md      # API & schema reference
│   ├── DemoScript.md               # Judge-friendly demo walkthrough
│   └── BursaWebScraper.md          # Bursa scraping methodology
│
├── scripts/                        # UTILITY SCRIPTS
│   ├── seed_demo_data.py           # populate demo data for testing
│   ├── run_local.sh                # local development runner
│   └── migrate_db.sh               # database migration helper
│
├── tests/                          # UNIT & INTEGRATION TESTS
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_ocr.py
│   │   ├── test_etl.py
│   │   └── test_schemas.py
│   └── integration/
│       ├── test_end_to_end.py
│       └── test_api.py
│
├── Dockerfile                      # Main application container
├── .env.example                    # Environment variables template
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Poetry configuration (optional)
└── README.md                       # Project overview & setup guide
```

### Directory Responsibilities (Quick Reference)

| Directory | Responsibility | Contains Agents? |
|-----------|-----------------|------------------|
| **scraping/** | Playwright-based web scraping (Bursa) | ❌ No |
| **etl/** | Deterministic transformations + input ingestion | ❌ No |
| **storage/** | Persistence & retrieval (PostgreSQL, Vector DB) | ❌ No |
| **schemas/** | Data contracts (Pydantic SSOT) | ❌ No |
| **agents/** | LLM-powered reasoning & intelligence | ✅ **Yes** |
| **workflows/** | LangGraph orchestration & state management | ✅ **Yes** |
| **api/** | FastAPI REST endpoints | ⚠️ Calls agents |
| **frontend/** | Next.js Dashboard + Copilot UI | ⚠️ Calls API |
| **infra/** | Docker containerization & services | ❌ No |
| **evaluation/** | Quality metrics & testing | ❌ No |
| **docs/** | Architecture & implementation guides | ❌ No |

---

## 4. Scraping Layer (Web Data Acquisition - NO AGENTS)

### Purpose

Pure Playwright-based web scraping. No reasoning. No LLMs. No transformation.

### Inputs

* Bursa Malaysia announcements listings (https://bursa-bm.listedcompany.com/newsroom.html)

### Responsibilities

* Crawl announcement listing pages (year-based)
* Navigate to each announcement detail page
* Extract raw data:
  * Raw HTML (full page dump)
  * Visible text content
  * HTML table structures (raw, not parsed)
  * Linked PDF URLs
* Record video of entire scraping session
* Draw bounding boxes on detected elements
* Track progress in real-time (Redis)

### Output (Schema-bound)

```json
RawDocument {
  source: "bursa",
  source_url: string,
  raw_html: string,           # Full page HTML dump (no transformation)
  raw_text: string,           # All visible text (no transformation)
  tables_html: [string],      # Raw table HTMLs (no parsing)
  pdf_urls: [string],
  announcement_date: string,  # Light extraction for routing only
  company_name: string,       # Light extraction for filtering only
  video_base64: string,       # Optional: full scraping video (WebM)
  created_at: datetime
}
```

---

## 5. ETL Layer (Deterministic Transformations + Input Ingestion - NO AGENTS)

### Purpose

Transform raw data into structured knowledge. Parse, normalize, chunk. Also handles input from frontend file uploads.

### Inputs

* **Primary**: RawDocument from scraping/ (Bursa announcements)
* **Secondary**: File uploads from frontend dashboard (PDFs, CSVs)

### Responsibilities

**Ingestion Phase** (from scraping/ + uploads):
* Load RawDocument from scraping/ outputs
* Handle frontend file uploads
* Validate input schemas

**Transformation Pipeline**:
* Clean & preprocess HTML
* Extract tables → parse into structured rows
* Extract + normalize text
* Process PDFs: OCR (PaddleOCR), layout parsing (Docling)
* Parse financial statements (Income Statement, Balance Sheet, Cash Flow)
* Calculate financial ratios
* Generate RAG chunks with metadata

### Output (Schema-bound)

```json
StructuredRecord {
  announcement_id: string,
  company_code: string,
  announcement_date: date,
  category: string,
  title: string,
  pdf_urls: [string],
  parsed_fields: {
    dividend_per_share: number,
    ex_date: date,
    holdings_percent: number,
    ...
  },
  created_at: datetime
}

DocumentObject {
  doc_id: string,
  source: "bursa",
  doc_type: string,
  company_code: string,
  title: string,
  raw_text: string,           # Full text for embeddings
  tables: [table_structure],  # Parsed table data
  metadata: {...},            # Extracted key-value pairs
  keywords: [string],
  summary: string,
  created_at: datetime
}
```

---

## 6. Storage Layer

### 6.1 PostgreSQL (Structured Truth)

Stores:

* Companies
* Bursa filings
* Parsed tables
* Financial statements
* Ratios
* Alerts

---

### 6.2 Vector DB (Semantic Retrieval)

Stores:

* Document chunks
* News paragraphs
* Filing explanations

```json
EmbeddingRecord {
  chunk_id: string
  embedding: vector
  metadata: {...}
}
```

---

## 7. Intelligence Layer (AGENTS ONLY HERE - LLM Reasoning)

Agents  **never touch raw data** .
They operate only on  **Postgres + Vector DB outputs** .

---

## 8. Supervisor Agent (Core Brain)

### Responsibilities

* Classify user intent
* Decide execution path
* Invoke correct agent(s)
* Merge outputs into one response

### Decision Logic (MVP)

```
IF query asks for numbers / counts / dates
    → SQL Agent
ELSE
    → RAG Agent

IF query implies risk / flag / warning
    → ALSO invoke Alert Agent

IF financial explanation required
    → ALSO invoke Financial Agent
```

---

## 9. Agent Responsibilities (Strict)

### 9.1 RAG Agent

* Retrieve document chunks
* Generate grounded answers
* Attach citations

### 9.2 SQL Agent

* Text → SQL over Postgres
* Return tabular or scalar results

### 9.3 Financial Agent

* Explain ratios
* Interpret financial trends

### 9.4 Alert Agent

* Evaluate alert rules
* Surface triggered risks + evidence

---

## 10. Copilot Execution Flow

```
User Question
      ↓
Supervisor Agent
      ↓
[RAG | SQL | Financial | Alert]
      ↓
Supervisor Merge
      ↓
CopilotAnswer JSON
```

### Output Contract

```json
CopilotAnswer {
  answer_text: string
  citations: [ { source, link, page } ]
  tables?: [...]
  alerts?: [...]
}
```

---

## 11. API Surface (MVP Only)

| Endpoint                     | Purpose                 |
| ---------------------------- | ----------------------- |
| POST `/ingest/bursa`       | Trigger Bursa ingestion |
| POST `/ingest/news`        | Trigger news scraping   |
| POST `/intelligence/query` | Copilot chat            |
| POST `/sql`                | NL → SQL               |
| GET `/alerts`              | Active alerts           |
| GET `/documents/{id}`      | Evidence inspection     |
| GET `/health`              | System status           |

---

## 12. Dashboard (Read-Only Intelligence Surface)

### Views

* Company 360
* Filing timeline
* Sentiment trend
* Financial snapshot
* Alert history

---

## 13. MVP Demo Flow (Judge-Friendly)

1. Trigger Bursa ingestion
2. Open one announcement → extracted table
3. Show sentiment + rationale
4. Parse financial PDF → ratios
5. Trigger alert
6. Ask Copilot “Why is this risky?”
7. Show citations

---

## 14. What This MVP Is (and Is Not)

✅ Evidence-grounded
✅ Explainable
✅ Modular
✅ Hackathon-feasible

❌ Not real-time trading
❌ Not predictive modeling
❌ Not black-box AI

---

## 15. Final Instruction

> **Do not invent logic outside schemas.
> ETL transforms data.
> Agents reason on stored outputs.
> Supervisor decides flow.
> Copilot answers must cite evidence.**
