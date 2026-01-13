# Market Intelligence MVP - Bursa Malaysia Announcements

Qualitative Market Intelligence Surveillance system for Bursa Malaysia announcements with intelligent agents, RAG-powered search, and real-time alerts.

## Overview

This MVP ingests Bursa Malaysia announcements through automated web scraping, extracts structured data, performs NLP analysis, and provides an evidence-grounded AI copilot interface for market intelligence queries.

## Features

### Data Acquisition

- ✅ Bursa Malaysia announcement scraping with Playwright
- ✅ Full video recording of scraping process (WebM)
- ✅ Bounding box visualization of detected elements
- ✅ Real-time progress tracking (Redis)
- ✅ PDF download & processing

### Data Processing

- ✅ HTML table extraction & normalization
- ✅ OCR for scanned documents (PaddleOCR)
- ✅ NLP sentiment analysis & entity extraction
- ✅ Financial statement parsing & ratio calculation
- ✅ Automated chunking for RAG

### Intelligence Layer

- ✅ Supervisor agent (orchestrates reasoning)
- ✅ RAG agent (semantic search + grounding)
- ✅ SQL agent (NL → SQL translation)
- ✅ Financial agent (ratio analysis)
- ✅ Alert agent (risk evaluation)
- ✅ Vector embeddings & semantic search (Pinecone/Weaviate)

### User Interface

- ✅ Dashboard (company 360, filing timeline, financials, alerts)
- ✅ AI Copilot (evidence-grounded answers with citations)

## Quick Start

### Backend Setup

```bash
cd apps
uv sync
cp ../env.example .env  # Edit with your credentials

# Run ingestion
uv run python -m ingestion.ingest_runner

# Run API server
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

## Project Structure

```
HackLab2.0_Ambank/
│
├── apps/                          # Backend (Python/FastAPI)
│   ├── scraping/                 # Data acquisition (Playwright, Bursa scraper)
│   ├── etl/                       # Transformation pipelines (OCR, PDF, NLP, financials)
│   ├── storage/                   # Persistence (PostgreSQL, Vector DB, raw archives)
│   ├── schemas/                   # Pydantic data contracts (SSOT)
│   ├── agents/                    # LLM-powered reasoning (Supervisor, RAG, SQL, etc)
│   ├── workflows/                 # LangGraph orchestration
│   ├── api/                       # FastAPI REST API
│   ├── tests/                     # Unit & integration tests
│   ├── pyproject.toml             # Backend dependencies (uv)
│   └── README.md                  # Backend-specific documentation
│
├── frontend/                      # Frontend (Next.js/TypeScript/Tailwind)
│   ├── app/                       # Next.js App Router
│   ├── components/                # React components
│   ├── public/                    # Static assets
│   └── package.json
│
├── ingestion/                     # Shared ingestion logic (referenced in PLAN.md)
├── etl/                          # Shared ETL logic (referenced in PLAN.md)
├── storage/                       # Storage layer (PostgreSQL, Vector DB)
│   ├── raw/                       # Raw HTML/PDF archives
│   ├── processed/                 # Processed documents
│   └── embeddings/                # Vector embeddings
│
├── docs/                          # Documentation
│   ├── PLAN.md                    # System architecture & design
│   ├── ENDPOINTS.md               # API reference
│   ├── BursaWebScraper.md         # Scraping methodology & implementation guide
│   ├── STRUCTURE_VALIDATION.md    # ingestion/ structure validation
│   └── WebScraper.md              # Playwright-based scraping (SupplyOS)
│
├── infra/                         # Infrastructure
│   ├── docker-compose.yml         # Services: PostgreSQL, Redis, Vector DB
│   └── ...
│
├── pyproject.toml                 # Backend project config (should be in apps/)
├── requirements.txt               # Backend dependencies (should be in apps/)
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules (at root + apps/)
└── README.md                      # This file
```

## Environment Setup

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/market_intel_mvp

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI (LLM)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Bursa Scraping
BURSA_BASE_URL=https://bursa-bm.listedcompany.com/newsroom.html
BURSA_SCRAPE_YEAR=2025
PLAYWRIGHT_HEADLESS=True
VIDEO_RECORDING_ENABLED=True

# Vector DB (Pinecone)
PINECONE_API_KEY=xxx
PINECONE_ENVIRONMENT=us-east1-aws

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the System

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- uv (Python package manager)

### Start Docker Services

```bash
cd infra
docker-compose up -d
```

### Backend (Terminal 1)

```bash
cd apps
uv sync
uv run uvicorn api.main:app --reload --port 8000
```

### Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev  # Open http://localhost:3000
```

### Run Scraping Job

```bash
cd apps
uv run python -m ingestion.ingest_runner --year 2025 --max-announcements 10
```

## Architecture

### Data Flow

```
Bursa Announcements
        ↓
ingestion/ (Playwright, video recording)
        ↓
RawDocument (raw HTML, text, tables)
        ↓
etl/ (parsing, normalization, chunking)
        ↓
storage/ (PostgreSQL + Vector DB)
        ↓
agents/ (Supervisor orchestrates reasoning)
        ├─ RAG Agent (semantic search)
        ├─ SQL Agent (NL → SQL)
        ├─ Financial Agent (ratios)
        └─ Alert Agent (risk evaluation)
        ↓
api/ (FastAPI REST endpoints)
        ↓
frontend/ (Next.js Dashboard + Copilot)
```

### Key Principles

1. **ETL is Deterministic** - No AI in pipelines, pure transformation
2. **Agents Reason** - LLM decisions only in intelligence layer
3. **Schema-First** - All data contracts defined in Pydantic
4. **Evidence-Grounded** - Copilot answers must cite sources
5. **Modular** - Each layer has clear responsibilities

## API Endpoints

See `ENDPOINTS.md` for complete API reference.

**Quick Examples:**

```bash
# Start ingestion
curl -X POST http://localhost:8000/api/v1/ingestion/bursa \
  -H "Content-Type: application/json" \
  -d '{"year": 2025, "max_announcements": 10}'

# Query Copilot
curl -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest dividend announcements?"}'

# Get alerts
curl http://localhost:8000/api/v1/alerts
```

## Documentation

- **PLAN.md** - System design, architecture principles, project structure
- **BursaWebScraper.md** - Complete scraping implementation guide with code examples
- **STRUCTURE_VALIDATION.md** - ingestion/ directory structure validation & optimization
- **ENDPOINTS.md** - API reference (coming soon)

## Testing

```bash
cd apps
uv run pytest tests/ -v --cov=. --cov-report=html
```

## Development

### Code Quality

```bash
cd apps

# Format code
uv run black .

# Sort imports
uv run isort .

# Lint
uv run flake8

# Type checking
uv run mypy .
```

### Pre-commit Hooks

```bash
cd apps
uv run pre-commit install
uv run pre-commit run --all-files
```

## Troubleshooting

### Playwright Issues

```bash
# Install browsers
uv run playwright install chromium
```

### PostgreSQL Connection

```bash
# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT version();"
```

### Redis Connection

```bash
# Test Redis
redis-cli ping  # Should return PONG
```

## Future Enhancements

- [ ] Additional news sources (The Edge, NST, Star)
- [ ] Manual PDF upload & processing
- [ ] Scheduled scraping (daily/weekly)
- [ ] Advanced alert rules & webhooks
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Real-time WebSocket updates

## Contributing

1. Read PLAN.md for architecture principles
2. Follow code quality standards (black, isort, mypy, flake8)
3. Write tests for new features
4. Update documentation

## License

Internal Use - Hackathon Project

## Support

For issues or questions, refer to:

- BursaWebScraper.md (scraping implementation)
- PLAN.md (system architecture)
- ENDPOINTS.md (API documentation)
