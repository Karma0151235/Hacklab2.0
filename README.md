# Market Intelligence Platform - System Architecture

A comprehensive qualitative market intelligence surveillance system designed for Malaysian capital markets, leveraging automated data acquisition, intelligent ETL processing, and multi-agent reasoning to deliver evidence-based financial insights.

**[📺 Demo Video](https://www.youtube.com/watch?v=ABiwPSwpz3g) | [📊 Presentation Slides](https://www.canva.com/design/DAG-XKMVhdc/BZiQ4aK3vpN9j_ww8upXAQ/edit?utm_content=DAG-XKMVhdc&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton)**

---

## System Overview

This platform automates the discovery, extraction, processing, and analysis of market intelligence data from multiple sources, transforming unstructured announcements and financial documents into actionable insights through a sophisticated multi-agent reasoning layer.

**Core Value Propositions:**

- **Transparent Data Acquisition** - Video-recorded, visually-annotated web scraping for auditability
- **Intelligent Document Processing** - Automated extraction and structuring of complex financial documents
- **Evidence-Based Reasoning** - AI agents that reason over retrieved data with traceable citations
- **Real-Time Monitoring** - Continuous surveillance with configurable alert rules

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface Layer                 │
│         (Dashboard, Copilot, Real-time Alerts)          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    API Layer                            │
│         (FastAPI REST Endpoints, WebSocket)             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│            Intelligence Layer (Agents)                  │
│  Supervisor → RAG | Financial | Alert | Web Scraper    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Data Storage & Retrieval                   │
│  PostgreSQL | Vector DB (Milvus) | Redis Cache         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│           Data Processing (ETL Pipeline)                │
│   Parsing | OCR | Chunking | Embedding | Normalization │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│            Data Acquisition Layer                       │
│    Web Scraping (Playwright) | Document Upload         │
└─────────────────────────────────────────────────────────┘
```

---

## 1. Data Acquisition Layer

### 1.1 Web Scraping with Playwright

The platform employs **Playwright browser automation** for transparent, auditable data collection from multiple financial information sources.

#### Data Sources

- **Bursa Malaysia Announcements** - Official stock exchange filings, corporate actions, price-sensitive information
- **News Outlets** - Financial news aggregators, market updates, company-specific coverage
- **Annual Reports & Disclosures** - Company websites, regulatory databases

#### Key Features

**Transparent Scraping with Video Recording**

```
Playwright Browser Session
├─ Video Recording (WebM format)
│  └─ Full scraping session captured for audit trail
├─ Bounding Box Visualization
│  └─ DOM elements highlighted & annotated during extraction
├─ Progress Tracking (Redis)
│  └─ Real-time status updates to frontend
└─ Error Recovery
   └─ Graceful handling & logging of failures
```

**Bounding Box Visualization**

- Visual highlighting of detected elements on live website
- Confidence scores for each detected element
- Manual verification interface for high-precision operations
- Screenshot capture at each extraction point

**Video Recording for Transparency**

- Complete scraping session recorded (audio optional)
- Timestamps aligned with logged events
- Stored in archive for compliance & debugging
- Enables human verification of scraped data

#### Implementation Details

**Scraper Architecture** (`apps/scraping/`)

```python
apps/scraping/
├── bursa_web_scraper.py          # Main orchestration
├── bursa/
│   ├── announcement_fetcher.py    # Fetch listings
│   ├── listing_crawler.py         # Browse announcements
│   ├── pdf_downloader.py          # Download PDFs
│   ├── html_parser.py             # Parse HTML content
│   └── selectors.py               # CSS/XPath selectors
├── browser/
│   ├── playwright.py              # Playwright wrapper
│   └── actions.py                 # Click, scroll, wait actions
├── progress/
│   └── redis_store.py             # Progress tracking
└── common/
    ├── schemas.py                 # Data contracts
    └── utils.py                   # Helpers
```

---

## 2. Data Processing (ETL Pipeline)

The ETL pipeline transforms raw, unstructured data into normalized, embedding-ready chunks with comprehensive metadata preservation.

### 2.1 ETL Pipeline Architecture

```
Input Data Sources
├─ PDF Documents (Announcements, Reports)
├─ HTML Tables (Bursa listings, news)
└─ Uploaded Financial Statements

        ↓

[PARSING LAYER]
├─ PDF Text Extraction (PyPDF, Docling)
├─ HTML Table Extraction & Normalization
├─ OCR for Scanned Documents (PaddleOCR)
└─ Document Structure Analysis

        ↓

[ENRICHMENT LAYER]
├─ Entity Recognition (Named entities)
├─ Financial Ratio Calculation
├─ Sentiment Analysis (Document-level)
├─ Metadata Tagging (Company, filing type, date)
└─ HTML Table Normalization to CSV/JSON

        ↓

[SEGMENTATION & CHUNKING]
├─ Text Chunks (512-token windows with overlap)
├─ Table Chunks (Preserve structural metadata)
├─ Hierarchical Structure (Section → Subsection → Chunk)
└─ Chunk-level Metadata (Type, confidence, source)

        ↓

[EMBEDDING GENERATION]
├─ Text Embedding (Sentence-Transformers)
├─ Table Embedding (Aggregate + Structural metadata)
└─ Metadata Indexing (for filtering)

        ↓

[STORAGE & INDEXING]
├─ PostgreSQL (Metadata, structured data)
├─ Milvus Vector DB (Text & table embeddings)
└─ Redis Cache (Frequently accessed chunks)

Output: Retrieved chunks ready for agent reasoning
```

### 2.2 Processing Pipeline Detail

**Current Implementation**

The ETL pipeline follows a modular, deterministic approach with clear responsibility separation:

```
1. EXTRACTION
   └─ pdf_extractor.py
      ├─ Text extraction (pdfplumber)
      ├─ Table extraction (tabula with multiple strategies)
      └─ Metadata: filename, page count, encoding handling

2. CHUNKING
   └─ chunker.py
      ├─ Text segmentation (500-char windows)
      ├─ Overlap preservation (50 chars = 10%)
      ├─ Page-aware boundaries
      └─ Chunk metadata: filename, company, doc_id, source

3. EMBEDDING
   └─ generator.py
      ├─ Model: Sentence-Transformers (all-MiniLM-L6-v2)
      ├─ Dimension: 384-bit vectors
      ├─ Batch processing (configurable batch size)
      └─ Single & batch encoding modes

4. STORAGE
   └─ db/
      ├─ Milvus: Vector embeddings + metadata
      ├─ PostgreSQL: Structured data & references
      └─ Redis: Query caching & progress tracking
```

**Chunking Strategy**

```
Text Documents:
  - Chunk Size: 500 characters (configurable)
  - Overlap: 50 characters between chunks
  - Page-aware: Respects page boundaries
  - Metadata per chunk: filename, company, doc_id, chunk_type, source

Table Data:
  - Extraction: Tabula (stream + lattice modes)
  - Format: Converted to list-of-lists with safe encoding
  - Storage: Native in Milvus with table-specific metadata
```

**Embedding Specification**

```
Model: Sentence-Transformers (all-MiniLM-L6-v2)
Dimension: 384
Batch Size: 32 (default, configurable)
Encoding: UTF-8 with error handling
Vector Output: Normalized float lists
```

### 2.3 Implementation Structure

```python
apps/etl/
├── processing/
│   ├── pdf_extractor.py          # PDF text & table extraction
│   └── __init__.py
│
├── chunking/
│   ├── chunker.py                # Text segmentation (500 chars, 50 overlap)
│   └── __init__.py
│
├── embeddings/
│   ├── generator.py              # Embedding generation via Sentence-Transformers
│   └── __init__.py
│
├── db/
│   ├── postgres.py               # PostgreSQL operations (SQLAlchemy)
│   ├── milvus.py                 # Milvus vector DB interface
│   ├── milvus_pdf_manager.py     # PDF-specific Milvus operations
│   ├── models.py                 # SQLAlchemy ORM models
│   ├── queries.py                # Prepared SQL queries
│   └── __init__.py
│
├── logging_config.py             # Centralized logging setup
└── __init__.py
```

**Actual Implementation Flow**

```python
# From pdf_etl_pipeline.py
raw_pdf = Path("storage/raw/pdfs/document.pdf")

# 1. Extract (pdf_extractor.py)
extractor = PDFExtractor()
content = extractor.extract_from_file(raw_pdf)
# → PDFContent(text_content, tables, pages, filename)

# 2. Chunk (chunker.py)
chunker = TextChunker(chunk_size=500, overlap=50)
text_chunks = chunker.chunk_text(
    text=content.text_content,
    filename=raw_pdf.name,
    company_name="Ambank",
    doc_id=str(uuid.uuid4())
)
# → List[TextChunk] with metadata

# 3. Embed (embeddings/generator.py)
embedder = EmbeddingGenerator(model="sentence-transformers/all-MiniLM-L6-v2")
embeddings = embedder.generate_batch([chunk.content for chunk in text_chunks])
# → List[List[float]] (384-dim vectors)

# 4. Store (db/milvus_pdf_manager.py)
milvus = MilvusPDFManager()
milvus.insert_text_chunks(
    collection="pdf_text_chunks",
    chunks=text_chunks,
    embeddings=embeddings
)
# → Inserted into Milvus with metadata indexing
```

**Note on Enrichment:**

- Entity recognition, sentiment analysis, and financial ratio calculation happen at **query time** via the Agent layer, not during ETL
- This enables flexible, context-aware analysis but means metrics are computed on-demand
- For batch pre-computation of financial metrics, see `apps/agents/financial_agent.py`

---

## 3. Multi-Agent Intelligence Layer

The intelligence layer employs a sophisticated multi-agent orchestration system where a Supervisor agent routes queries to specialized agents for retrieval, analysis, financial reasoning, and risk evaluation.

### 3.1 Agent Architecture

```
\User Query
    ↓
[SUPERVISOR AGENT] ◄─────────────────────┐
├─ Parse query intent                    │
├─ Decide agent routing                  │
├─ Orchestrate parallel execution        │
├─ Aggregate results                     │
└─ Format evidence-backed response       │
    ↓ ↓ ↓ ↓
    ├─→ [RAG AGENT]         ← retrieve semantic matches
    │      ├─ Query Milvus (k=2 text, k=1 table)
    │      ├─ Rank by relevance
    │      └─ Return: chunks + confidence
    │
    ├─→ [FINANCIAL AGENT]   ← analyze financial metrics
    │      ├─ Extract numbers from context
    │      ├─ Calculate ratios & trends
    │      └─ Return: analysis + supporting data
    │
    ├─→ [ALERT AGENT]       ← evaluate risk signals
    │      ├─ Check alert rules
    │      ├─ Score anomalies
    │      └─ Return: active alerts + severity

    ↓ ↓ ↓ ↓
    [EVIDENCE AGGREGATION]
    ├─ Merge retrieved chunks
    ├─ Consolidate metrics
    ├─ Combine alerts
    └─ Add citations

    ↓
[RESPONSE FORMATTING]
├─ Chain-of-thought reasoning
├─ Structured output with sources
└─ Visualization recommendations
    ↓
Final Output to User
```

### 3.2 Agent Specifications

#### **Supervisor Agent**

**Responsibility:** Query orchestration and response synthesis

```
Input: User question about company/market
Process:
1. Intent classification (search, analysis, monitoring, etc.)
2. Agent selection (which agents needed?)
3. Parallel execution of selected agents
4. Result aggregation & conflict resolution
5. Evidence compilation with citations

Output:
{
  "answer": "Comprehensive response with reasoning",
  "agents_used": ["RAG", "Financial"],
  "steps": [
    "Step 1: Retrieved 3 relevant announcements",
    "Step 2: Calculated liquidity ratios from latest balance sheet",
    "Step 3: Cross-referenced with historical trends"
  ],
  "citations": [
    {
      "type": "pdf_text_chunks",
      "filename": "2024_Annual_Report.pdf",
      "company": "Ambank",
      "confidence": 0.96
    }
  ],
  "table_data": <DataFrame if visualization>
}
```

#### **RAG Agent**

**Responsibility:** Semantic retrieval and context grounding

```
Input: Query + Supervisor instruction
Process:
1. Generate query embeddings
2. Search Milvus collections:
   - pdf_text_chunks: k=2 (top 2 matches)
   - pdf_table_chunks: k=1 (top 1 match)
3. Score & rank results
4. Apply chain-of-thought over context

Output:
{
  "summary": "Synthesized answer from retrieved chunks",
  "chunks": [
    {
      "content": "...",
      "metadata": {
        "filename": "...",
        "company_name": "...",
        "source_type": "text|table",
        "confidence": 0.94
      }
    }
  ],
  "table_chunks": [
    {
      "title": "Q3 Revenue by Segment",
      "rows": [
        {"segment": "Banking", "revenue": 5000, "currency": "MYR M"}
      ],
      "confidence": 0.92
    }
  ],
  "entities": ["Ambank", "CEO Dato' Ahmad"]
}
```

#### **Financial Agent**

**Responsibility:** Numerical analysis and ratio computation

```
Input: Company name + context chunks
Process:
1. Extract financial line items from chunks
2. Calculate key metrics:
   - Profitability: Net Margin, ROE, ROA
   - Liquidity: Current Ratio, Quick Ratio
   - Leverage: Debt/Equity, Interest Coverage
   - Efficiency: Asset Turnover, Days Sales Outstanding
3. Trend analysis (Y/Y, Q/Q comparisons)
4. Benchmarking vs industry
5. Risk scoring

Output:
{
  "company": "Ambank",
  "analysis_date": "2025-01-14",
  "metrics": {
    "profitability": {
      "net_profit_margin": 0.18,
      "roe": 0.12,
      "trend": "stable"
    },
    "liquidity": {
      "current_ratio": 1.45,
      "quick_ratio": 1.02,
      "trend": "improving"
    }
  },
  "risk_score": 0.35,  # 0-1, higher = riskier
  "recommendation": "Monitor"
}
```

#### **Alert Agent**

**Responsibility:** Risk evaluation and anomaly detection

```
Input: Company data + configured rules
Process:
1. Evaluate alert rules:
   ├─ Keyword matching (regulatory keywords, risk language)
   ├─ Sentiment shifts (comparing current vs historical)
   ├─ Filing type triggers (specific announcements)
   ├─ Financial thresholds (≥10 key metrics)
   └─ Anomaly detection (unusual patterns)
2. Score & prioritize
3. Aggregate related metrics

Output:
{
  "company": "Ambank",
  "alerts": [
    {
      "type": "liquidity_concern",
      "message": "Current ratio declined 5% Q/Q",
      "severity": "medium",
      "metrics_affected": ["current_ratio", "cash_position"]
    },
    {
      "type": "regulatory_filing",
      "message": "Notice of Material Change filed",
      "severity": "high",
      "keywords": ["director_resignation"]
    }
  ],
  "related_metrics": {
    "Liquidity": 1.2,
    "Leverage": 0.8,
    "Profitability": 5.3,
    "Risk": 0.65
  }
}
```

### 3.3 Agent Implementation

```python
apps/agents/
├── supervisor.py           # Orchestration & routing
├── rag_agent.py           # Semantic retrieval
├── financial_agent.py     # Ratio & analysis
├── alert_agent.py         # Risk evaluation
├── schemas.py             # Output contracts
└── config.py              # Agent configurations
```

---

## 4. Data Storage & Retrieval

### 4.1 Storage Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   PostgreSQL (Primary)                  │
├─────────────────────────────────────────────────────────┤
│ Tables:                                                  │
│  - companies (name, ticker, industry)                   │
│  - documents (filename, company_id, upload_date)        │
│  - chunks (content, document_id, chunk_type)            │
│  - financial_metrics (company_id, metric, value, date)  │
│  - alerts (company_id, alert_type, created_at)          │
│  - audit_log (action, timestamp, user_id)               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│        Milvus Vector Database (Similarity Search)       │
├─────────────────────────────────────────────────────────┤
│ Collections:                                             │
│  - pdf_text_chunks (embedding, chunk_id, metadata)      │
│  - pdf_table_chunks (embedding, chunk_id, table_title)  │
│  - news_chunks (embedding, chunk_id, source_url)        │
│                                                          │
│ Indexing: HNSW (fast approximate NN search)             │
│ Distance: Cosine similarity                             │
│ Dimension: 384 (MiniLM embeddings)                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│       Redis Cache (Session & Progress Tracking)         │
├─────────────────────────────────────────────────────────┤
│  - scraping_progress (real-time job status)             │
│  - query_cache (LRU cache for RAG results)              │
│  - session_tokens (user authentication)                 │
│  - rate_limits (API throttling)                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│     File Storage (Raw & Processed Documents)            │
├─────────────────────────────────────────────────────────┤
│  /storage/                                               │
│  ├─ raw/        (Original PDFs, videos)                │
│  ├─ processed/  (Extracted text, tables, metadata)      │
│  └─ embeddings/ (Serialized vector files)               │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Retrieval Optimization

**Vector Search Configuration**

```
Query:
  1. Embed user question (384-dim vector)
  2. Search pdf_text_chunks: k=2, threshold=0.7
  3. Search pdf_table_chunks: k=1, threshold=0.65
  4. Return top 3 results with metadata

Result Ranking:
  - Cosine similarity score (confidence)
  - Temporal relevance (recent > older)
  - Document type preference (tables for numerical queries)
```

**Caching Strategy**

```
Cache Key: hash(query_embedding + filter_params)
TTL: 24 hours
Invalidation: On new document ingestion
Hit Rate Target: >40% for repeated queries
```

---

## 5. User Interface & Dashboard

### 5.1 Dashboard Components

**Company 360 View**

```
┌────────────────────────────────────────────────────────┐
│ Company: Ambank | Ticker: AMBANK | Industry: Banking   │
├────────────────────────────────────────────────────────┤
│                                                        │
│ [Latest News] [Financial Metrics] [Alerts] [Timeline] │
│                                                        │
│ Key Metrics                        Last Filing         │
│ ├─ Stock Price: 4.50 MYR          2025-01-10          │
│ ├─ Market Cap: 18.2B MYR          Dividend            │
│ ├─ P/E Ratio: 8.5x                Announcement        │
│ └─ Debt/Equity: 0.45              "0.20 sen per share" │
│                                                        │
│ Liquidity Trend         Risk Indicators               │
│ [Line Chart 6M]        ├─ Credit News: Stable         │
│                        ├─ Leverage: Medium            │
│                        └─ Regulatory: Clear           │
│                                                        │
│ Recent Documents (Last 30 days)                        │
│ ├─ 2024 Annual Report (Oct 2024)                       │
│ ├─ Q3 2024 Results (Aug 2024)                          │
│ └─ Dividend Notice (Mar 2024)                          │
│                                                        │
│ Active Alerts                                          │
│ ├─ 🔴 Dividend Cut Announcement (HIGH)                 │
│ └─ 🟡 Q3 Profit Down 8% Y/Y (MEDIUM)                   │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**AI Copilot Interface**

```
┌────────────────────────────────────────────────────────┐
│                    AI Copilot                           │
├────────────────────────────────────────────────────────┤
│                                                        │
│ Q: "What were Ambank's latest dividend announcements?"│
│                                                        │
│ A: Based on Bursa Malaysia filings, Ambank announced   │
│    a dividend of 0.20 sen per share on 2025-01-10.    │
│    This represents a 20% increase from the previous    │
│    quarter.                                            │
│                                                        │
│    Evidence:                                           │
│    • Source: Ambank_Dividend_Notice_Jan2025.pdf       │
│      Confidence: 98%                                   │
│      Section: Corporate Actions                        │
│                                                        │
│    • Source: Bursa Malaysia Announcement 2025-01-10   │
│      Confidence: 95%                                   │
│                                                        │
│    Related Metrics:                                    │
│    ├─ Payout Ratio: 35%                                │
│    ├─ Free Cash Flow: 2.1B MYR                         │
│    └─ Historical Yield: 4.2%                           │
│                                                        │
│    [Show Timeline] [View Source PDFs] [Export Analysis]│
│                                                        │
│ ___________________________________________________     │
│ | Q: Ask about any company, metric, or announcement... │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Alert Dashboard**

```
┌────────────────────────────────────────────────────────┐
│                    System Alerts                        │
├────────────────────────────────────────────────────────┤
│                                                        │
│ Filter: All | High | Medium | Company: Ambank         │
│                                                        │
│ 🔴 HIGH: Dividend Cut Announced (Ambank)              │
│    Jan 14, 2025 | Detected: 2 hours ago               │
│    Keywords: "dividend reduction", "challenging mkt"  │
│    Action: Review Q3 results, check analyst reports   │
│                                                        │
│ 🟡 MEDIUM: Liquidity Ratio Decline (Ambank)           │
│    Jan 12, 2025 | Detected: 1 hour ago                │
│    Metric: Current Ratio 1.45 (was 1.68 in Q2)        │
│    Action: Monitor quarterly cash flow trends         │
│                                                        │
│ 🟢 LOW: Regulatory Filing (CIMB)                      │
│    Jan 10, 2025 | Filed: Directors' Report Update     │
│    Impact: No material business impact identified     │
│                                                        │
│ [Configure Rules] [View Alert History] [Export Report]│
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 5.2 Frontend Technology Stack

```
Framework:      Next.js 16 (App Router) + React 19
Styling:        Tailwind CSS 4
Components:     Shadcn/UI (Radix primitives)
State Mgmt:     Zustand
Forms:          React Hook Form + Zod validation
Data Tables:    TanStack Table v8
Charts:         Recharts
Animations:     Framer Motion
Icons:          Lucide React
Notifications:  Sonner
WebSocket:      Socket.io (real-time alerts)
```

---

## System Workflow Summary

### End-to-End Data Flow

```
┌─ ACQUISITION ──────────────────────────────────────┐
│                                                     │
│  Bursa Announcements → Playwright Browser Session   │
│  ├─ Video Recording: /storage/videos/...webm      │
│  ├─ Bounding Boxes: Annotated screenshots          │
│  └─ Progress: Redis tracking (real-time)           │
│                                                     │
│  News Outlets → REST API Scraping                  │
│  News Uploads → Manual File Upload UI              │
│                                                     │
└──────────┬────────────────────────────────────────┘
           │
           ▼
┌─ PROCESSING ──────────────────────────────────────┐
│                                                     │
│  Raw PDF/HTML                                      │
│  ├─ Parse: Extract text, tables, structure        │
│  ├─ OCR: PaddleOCR for scanned documents          │
│  ├─ Enrich: Entities, sentiment, ratios           │
│  ├─ Chunk: 512-token windows with overlap         │
│  └─ Embed: Sentence-Transformers (384-dim)        │
│                                                     │
│  Output: Normalized chunks with metadata           │
│                                                     │
└──────────┬────────────────────────────────────────┘
           │
           ▼
┌─ STORAGE ─────────────────────────────────────────┐
│                                                     │
│  PostgreSQL:        Metadata, company profiles     │
│  Milvus:           Text & table embeddings (VNN)  │
│  Redis:             Cache & session state          │
│  File Storage:      Raw PDFs, videos, extracts    │
│                                                     │
└──────────┬────────────────────────────────────────┘
           │
           ▼
┌─ INTELLIGENCE ─────────────────────────────────────┐
│                                                     │
│  User Query                                        │
│  ├─ Supervisor: Route to agents                   │
│  ├─ RAG: Semantic search (k=3 results)            │
│  ├─ Financial: Calculate metrics & trends         │
│  ├─ Alert: Evaluate rules & flag anomalies        │
│  └─ Synthesis: Merge + cite sources               │
│                                                     │
│  Output: Evidence-backed response                 │
│                                                     │
└──────────┬────────────────────────────────────────┘
           │
           ▼
┌─ DELIVERY ────────────────────────────────────────┐
│                                                     │
│  Dashboard:         Company 360, alerts, timeline  │
│  Copilot:           Question answering + evidence  │
│  Alerts:            Push notifications, email      │
│  API:               REST endpoints (JSON)          │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Quick Start Guide

### Prerequisites

- **Python:** 3.11+
- **Node.js:** 18+
- **Database:** PostgreSQL 15+, Redis 7+
- **Package Manager:** uv (Python), npm (Node)

### 1. Environment Setup

```bash
# Clone repository
git clone <repo>
cd HackLab2.0_Ambank

# Create environment file
cp .env.example .env
# Edit .env with your API keys & database URLs
```

**Required Environment Variables**

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/market_intel
REDIS_URL=redis://localhost:6379/0

# LLM (OpenAI/DeepSeek)
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini

# Vector Database (Milvus)
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Bursa Scraping
PLAYWRIGHT_HEADLESS=False
VIDEO_RECORDING_ENABLED=True
BOUNDING_BOX_VISUALIZATION=True

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. Docker Services

```bash
# Start PostgreSQL, Redis, Milvus
docker-compose up -d

# Verify services
docker ps
```

### 3. Backend Installation

```bash
cd apps
uv sync  # Install dependencies

# Run database migrations
uv run alembic upgrade head

# Start API server
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API available at: `http://localhost:8000`
Docs at: `http://localhost:8000/docs`

### 4. Frontend Installation

```bash
cd frontend
npm install
npm run dev  # Open http://localhost:3000
```

### 5. Run Data Acquisition

```bash
cd apps

# Scrape Bursa announcements
uv run python -m scraping.scraper_runner \
  --year 2025 \
  --max-announcements 10 \
  --record-video

# Upload & process financial documents
uv run python -m etl.document_processor \
  --input-dir /path/to/pdfs \
  --embed
```

---

## API Reference

### Copilot Endpoint

```bash
POST /api/v1/copilot/chat
Content-Type: application/json

{
  "query": "What are the latest dividend announcements?",
  "company_filter": "AMBANK",  # Optional
  "include_tables": true
}

Response:
{
  "answer": "...",
  "agents_used": ["RAG", "Financial"],
  "citations": [...],
  "processing_time_ms": 2340
}
```

### Company 360 Endpoint

```bash
GET /api/v1/companies/{company_id}

Response:
{
  "company": {
    "name": "Ambank",
    "ticker": "AMBANK",
    "industry": "Banking"
  },
  "latest_metrics": {...},
  "recent_documents": [...],
  "active_alerts": [...]
}
```

### Scraping Progress Endpoint

```bash
GET /api/v1/ingestion/progress/{job_id}

Response:
{
  "status": "in_progress",
  "progress_percent": 45,
  "companies_processed": 23,
  "documents_downloaded": 156,
  "video_uri": "/storage/videos/job_20250114.webm",
  "elapsed_seconds": 1203
}
```

See **ENDPOINTS.md** for complete API documentation.

---

## Project Structure

```
HackLab2.0_Ambank/
│
├── apps/                               # Backend (FastAPI + Agents)
│   ├── scraping/                      # Data acquisition layer
│   │   ├── bursa_web_scraper.py       # Main orchestrator
│   │   ├── bursa/                     # Bursa-specific modules
│   │   ├── browser/                   # Playwright wrapper
│   │   ├── progress/                  # Redis progress tracking
│   │   └── common/                    # Utilities & schemas
│   │
│   ├── etl/                           # Processing pipeline (PDF → Chunks → Vectors → DB)
│   │   ├── processing/
│   │   │   └── pdf_extractor.py       # PDF text & table extraction (pdfplumber, tabula)
│   │   ├── chunking/
│   │   │   └── chunker.py             # Text segmentation (500-char windows, 50-char overlap)
│   │   ├── embeddings/
│   │   │   └── generator.py           # Embedding generation (Sentence-Transformers, 384-dim)
│   │   ├── db/
│   │   │   ├── postgres.py            # PostgreSQL operations (SQLAlchemy ORM)
│   │   │   ├── milvus.py              # Milvus vector DB interface
│   │   │   ├── milvus_pdf_manager.py  # PDF-specific Milvus operations
│   │   │   ├── models.py              # SQLAlchemy data models
│   │   │   └── queries.py             # Prepared SQL queries
│   │   └── logging_config.py          # Centralized logging
│   │
│   ├── agents/                        # Intelligence layer
│   │   ├── supervisor.py              # Query orchestration
│   │   ├── rag_agent.py               # Semantic retrieval
│   │   ├── financial_agent.py         # Ratio analysis
│   │   ├── alert_agent.py             # Risk evaluation
│   │   └── schemas.py                 # Output contracts
│   │
│   ├── workflows/                     # LangGraph orchestration
│   │   └── intelligence_flow.py       # Multi-agent flow
│   │
│   ├── api/                           # FastAPI REST API
│   │   ├── main.py                    # App initialization
│   │   ├── routes/                    # Endpoint definitions
│   │   └── middleware/                # Auth, CORS, logging
│   │
│   ├── storage/                       # Data persistence
│   │   ├── postgres.py                # SQLAlchemy models
│   │   ├── milvus.py                  # Vector DB interface
│   │   └── redis.py                   # Cache operations
│   │
│   ├── schemas/                       # Pydantic contracts
│   │   └── *.py                       # Data models
│   │
│   ├── tests/                         # Unit & integration tests
│   ├── pyproject.toml                 # Dependencies (uv)
│   └── README.md                      # Backend docs
│
├── frontend/                          # Frontend (Next.js + React)
│   ├── app/                           # App Router pages
│   │   ├── page.tsx                   # Home/dashboard
│   │   ├── company/                   # Company detail pages
│   │   ├── copilot/                   # Chat interface
│   │   └── alerts/                    # Alert management
│   │
│   ├── components/                    # React components
│   │   ├── dashboard/                 # Dashboard widgets
│   │   ├── chat/                      # Copilot UI
│   │   ├── common/                    # Reusable components
│   │   └── layout/                    # App layout
│   │
│   ├── lib/                           # Utilities
│   │   ├── api.ts                     # API client
│   │   ├── hooks/                     # Custom React hooks
│   │   └── utils/                     # Helpers
│   │
│   ├── public/                        # Static assets
│   └── package.json                   # Dependencies (npm)
│
├── docs/                              # Documentation
│   ├── PLAN.md                        # Architecture & design
│   ├── ENDPOINTS.md                   # API reference
│   ├── BursaWebScraper.md             # Scraping guide
│   └── README.md                      # Overview
│
├── storage/                           # Persistent storage
│   ├── raw/                           # Original PDFs, videos
│   ├── processed/                     # Extracted data
│   └── embeddings/                    # Vector files
│
├── docker-compose.yml                 # Service orchestration
├── .env.example                       # Environment template
├── README.md                          # This file
└── QUICKSTART_PDF_ETL.md              # ETL quickstart
```

---

## Technology Stack

### Backend

| Layer                    | Technology                       | Purpose                                      |
| ------------------------ | -------------------------------- | -------------------------------------------- |
| **Framework**      | FastAPI, Uvicorn                 | REST API, async support                      |
| **Web Scraping**   | Playwright                       | Browser automation, recording, visualization |
| **PDF Extraction** | pdfplumber, tabula-py            | Text & table extraction from PDFs            |
| **Embeddings**     | Sentence-Transformers (MiniLM)   | 384-dim vector generation                    |
| **AI/LLM**         | OpenAI API, LangChain, LangGraph | Agent orchestration, reasoning               |
| **Vector DB**      | Milvus                           | Semantic search, similarity indexing (HNSW)  |
| **SQL DB**         | PostgreSQL, SQLAlchemy           | Metadata, structured data, ORM               |
| **Cache**          | Redis                            | Session, progress, query cache               |
| **Agent Layer**    | LangChain, LangGraph             | Financial, RAG, Alert, Supervisor agents     |
| **Testing**        | Pytest, pytest-cov               | Unit & integration tests                     |

### Frontend

| Layer                   | Technology                | Purpose                    |
| ----------------------- | ------------------------- | -------------------------- |
| **Framework**     | Next.js 16, React 19      | App router, SSR            |
| **Styling**       | Tailwind CSS 4, Shadcn/UI | Component styling, theming |
| **State**         | Zustand                   | Global state management    |
| **Forms**         | React Hook Form, Zod      | Form handling, validation  |
| **Data Tables**   | TanStack Table v8         | Complex table UI           |
| **Charts**        | Recharts                  | Data visualization         |
| **Communication** | Socket.io, fetch API      | WebSocket, REST            |
| **Type Safety**   | TypeScript                | Static typing              |

### Infrastructure

| Component                 | Technology                   |
| ------------------------- | ---------------------------- |
| **Containers**      | Docker, Docker Compose       |
| **Orchestration**   | Docker Compose (development) |
| **Package Manager** | uv (Python), npm (Node)      |
| **Version Control** | Git                          |

---

## Code Quality & Development

### Running Tests

```bash
cd apps

# Run all tests with coverage
uv run pytest tests/ -v --cov=. --cov-report=html

# Run specific test
uv run pytest tests/test_scraper.py -v
```

### Code Formatting & Linting

```bash
cd apps

# Format with Black
uv run black .

# Sort imports with isort
uv run isort .

# Lint with Flake8
uv run flake8 .

# Type checking with mypy
uv run mypy .
```

### Pre-commit Hooks

```bash
cd apps
uv run pre-commit install
uv run pre-commit run --all-files
```

---

## Troubleshooting

### Playwright Installation Issues

```bash
# Install browsers for Playwright
uv run playwright install chromium firefox
```

### PostgreSQL Connection Issues

```bash
# Verify connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT version();"

# View logs
docker logs <postgres_container>
```

### Vector DB Connection

```bash
# Test Milvus connection
python -c "from milvus import MilvusClient; c = MilvusClient(uri='http://localhost:19530')"
```

### Redis Issues

```bash
# Verify Redis is running
redis-cli ping  # Should return PONG

# Clear cache (if needed)
redis-cli FLUSHDB

# Monitor commands
redis-cli MONITOR
```

---

## Future Roadmap

- [ ] Additional news sources (Bloomberg, Reuters, NST, The Edge)
- [ ] Scheduled scraping jobs (daily/weekly automation)
- [ ] Advanced alert configuration UI
- [ ] Webhooks for external integrations
- [ ] Multi-language support (BM, English, Chinese)
- [ ] Real-time WebSocket updates for live monitoring
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Custom report generation
- [ ] Integration with trading systems

---

## License

Internal Use - Hackathon Project

---

**Last Updated:** January 14, 2025
**Version:** 1.0.0-mvp
