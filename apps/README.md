# Market Intelligence MVP - Backend

Qualitative Market Intelligence Surveillance system for Bursa Malaysia announcements.

## Features

- ✅ Bursa Malaysia announcement scraping with Playwright
- ✅ Full video recording of scraping process
- ✅ Bounding box visualization
- ✅ Real-time progress tracking (Redis)
- ✅ PDF & OCR processing
- ✅ LLM-powered agents (RAG, SQL, Financial)
- ✅ Vector embeddings & semantic search
- ✅ Alert generation & evaluation

## Quick Start

```bash
uv sync
uv run python -m ingestion.ingest_runner
```

## Project Structure

```
apps/
├── ingestion/          # Data acquisition layer
├── etl/               # Transformation pipelines
├── storage/           # Persistence (PostgreSQL, Vector DB)
├── schemas/           # Pydantic data contracts
├── agents/            # LLM-powered reasoning
├── workflows/         # LangGraph orchestration
├── api/               # FastAPI REST API
└── tests/             # Unit & integration tests
```

## Environment Setup

Copy `.env.example` to `.env` and update:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/market_intel_mvp
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
```

## Running the Backend

```bash
# Development
uv run uvicorn api.main:app --reload

# Production
uv run gunicorn api.main:app
```
