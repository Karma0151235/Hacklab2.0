# HackLab 2.0 — Ambank Market Intelligence Platform

## Project at a Glance

Python multi-agent backend (FastAPI) + Next.js frontend for Malaysian stock market
intelligence. Ingests Bursa announcements and financial PDFs, indexes them into Milvus,
and surfaces insights through a copilot chat interface powered by a supervisor-orchestrated
agent system.

**Current active branch: `sentiment`** — integrating the Sentiment Agent into the
existing supervisor workflow.

---

## Repository Layout

```
/
├── apps/                       ← Python backend (all work happens here)
│   ├── agents/                 ← Multi-agent system (supervisor + sub-agents)
│   ├── api/                    ← FastAPI routes
│   ├── etl/                    ← PDF extraction, chunking, embeddings, DB ops
│   ├── scraping/               ← Playwright-based web scrapers
│   │   └── news/               ├── bernama_scraper.py / theedge_scraper.py
│   │                           ├── supabase_client.py   (news storage)
│   │                           ├── search_company.py    (CLI search)
│   │                           └── batch_job.py         (scheduled scrape)
│   ├── workflows/              ← LangGraph orchestration (intelligence_flow.py)
│   ├── storage/                ← Raw/processed file storage
│   ├── tests/                  ← 35+ test files
│   ├── pyproject.toml
│   └── .env                    ← secrets (see .env.example)
├── frontend/                   ← Next.js (ignored for current work)
├── docker-compose.yml          ← full stack: PG, Milvus, Minio, Etcd, Redis
└── CLAUDE.md                   ← this file
```

---

## Environment & Running

```bash
# From apps/
cd apps

# Install (uses uv)
uv sync

# Run API server
uv run python run_api.py

# Run a single news search (CLI)
uv run python -m scraping.news.search_company --company "MAYBANK" --max 10

# Run scheduled batch scrape
uv run python -m scraping.news.batch_job

# Run tests
uv run pytest tests/
```

Key env vars (`apps/.env`):

| Var | Purpose |
|-----|---------|
| `OPENROUTER_API_KEY` | LLM calls via OpenRouter (required) |
| `MILVUS_HOST` / `MILVUS_PORT` | Vector DB (default localhost:19639) |
| `SUPABASE_URL` / `SUPABASE_KEY` | News article storage |
| `USE_SENTIMENT_AGENT` | Master toggle for sentiment agent (new — Phase 1) |

---

## Agent Architecture

```
User query
    │
    ▼
┌─────────────────────────────────────────────────┐
│  IntelligenceFlow  (workflows/intelligence_flow) │  ← LangGraph StateGraph
│    └── SupervisorAgent.process()                 │
└──────────┬──────────────────────────────────────┘
           │  orchestrates (conditional per query)
     ┌─────┴──────┬────────────┬──────────────┐
     ▼            ▼            ▼              ▼
┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐
│ RAGAgent│ │Financial │ │AlertAgent│ │Sentiment   │  ← NEW (being wired)
│(always) │ │Agent     │ │          │ │Agent       │
└─────────┘ └──────────┘ └──────────┘ └────────────┘
                                            │
                                            │ needs news articles
                                     ┌──────▼──────┐
                                     │ news_fetcher │  ← NEW (Phase 2)
                                     │  Supabase    │
                                     │  ↓ miss      │
                                     │  scrapers    │
                                     └─────────────┘
```

### Agent responsibilities

| Agent | File | Role |
|-------|------|------|
| **Supervisor** | `agents/supervisor.py` | Reads the query, decides which agents to call via LLM planning, orchestrates execution, synthesises final answer with citations |
| **RAG** | `agents/rag_agent.py` | Semantic search over Milvus (PDF text + table chunks). Always called. |
| **Financial** | `agents/financial_agent.py` | Extracts and calculates financial ratios from RAG context. Called when query is about metrics/performance. |
| **Alert** | `agents/alert_agent.py` | Evaluates threshold breaches and risk signals. Called when query touches risks/warnings, or whenever Financial runs. |
| **Sentiment** | `agents/sentiment_agent.py` | LLM-based news sentiment analysis with keyword fallback. Called when query is about sentiment/media/perception. |

### Supervisor decision flow (inside `process()`)

1. `_plan_agent_execution` — single LLM call returns which agents to use + (soon) the company name
2. RAG retrieval — always runs
3. RAG quality gate — if low quality, early-exit path (but sentiment should still run; see Phase 3)
4. Financial Agent — conditional on plan
5. Alert Agent — conditional on plan or if Financial ran
6. **Sentiment Agent — conditional on `USE_SENTIMENT_AGENT` flag AND plan** (being added)
7. Synthesise response — aggregates all outputs into a single answer with citations

### Key schemas (`agents/schemas.py`)

All agent I/O is Pydantic. Central file. Do not define schemas inside agent files.

- `SupervisorInput` / `SupervisorOutput` — top-level query/response
- `RAGQuery` / `RAGOutput` — retrieval contract
- `FinancialAgentInput` / `FinancialAgentOutput` — metrics
- `AlertAgentInput` / `AlertAgentOutput` — alert signals
- `SentimentAgentInput` / `SentimentAgentOutput` — news sentiment (added on this branch)
- `SupervisorOutput.sentiment` — optional field for sentiment results (added on this branch)

### Config (`agents/config.py`)

Single source of truth for all agent settings. Class attributes, driven by env vars.
Models route through OpenRouter. Milvus connection details live here.

---

## News Data Pipeline

```
batch_job.py  (cron / scheduled)
  └── BernamaScraper + TheEdgeScraper   (Playwright, async)
        └── store_articles()            → Supabase  news_articles table
                                              │
search_company.py  (CLI, ad-hoc)              │  read path
  └── same scrapers + store                   ▼
                                     supabase_client.py
                                       get_articles_by_company()
                                       get_articles_without_sentiment()
                                       update_article_sentiment()
```

Supabase table `news_articles` has columns for `sentiment_score` and `sentiment_label`
that are populated post-analysis. `get_articles_without_sentiment()` is the queue.

---

## Current Branch Status (`sentiment`)

### What is already done

- `SentimentAgent` class: fully implemented (LLM analysis + keyword fallback)
- Schemas moved to `schemas.py` (no per-file definitions)
- `SupervisorOutput.sentiment` field exists
- Supervisor imports and instantiates `SentimentAgent`
- `_plan_agent_execution` prompt already mentions `use_sentiment`
- `pandas` added to deps

### What is NOT done (the gaps)

- No `USE_SENTIMENT_AGENT` boolean in config
- Supervisor never calls `self.sentiment_agent.analyze()`
- No news-fetching logic wired to the supervisor
- `_plan_agent_execution` does not extract `company_name`
- `_synthesize_response` does not include sentiment context
- Early-exit (low RAG quality) path ignores sentiment entirely
- `copilot.py` progress tracking missing `"sentiment"` agent ID
- `SentimentAgentInput.news_articles` typed as `List[Any]` (should be `List[NewsArticle]`)

---

## Integration Plan — 5 Phases

### Phase 1 — Config toggle
**File:** `apps/agents/config.py`

Add `USE_SENTIMENT_AGENT` class attribute, env-var driven, default `True`.
This is the master kill switch. The LLM planning decision (`use_sentiment` in the
returned JSON) is the second, per-query gate. Both must pass.

### Phase 2 — News Fetcher
**File:** `apps/agents/news_fetcher.py` (new)

Owns the "get news for company X" contract:

1. Query Supabase via `get_articles_by_company()` — sync, <1 s
2. If empty → scrape fallback:
   - Runs `BernamaScraper` + `TheEdgeScraper` inside a `ThreadPoolExecutor`
     with its own `asyncio.run()` (solves async-in-sync inside FastAPI)
   - Stores results to Supabase via `store_articles()`
   - 60 s timeout; on timeout returns `[]`
3. Parses raw Supabase dicts back into `NewsArticle` objects before returning

Why thread-pool? Scrapers are async (Playwright). Supervisor is sync. FastAPI already owns
the event loop. `asyncio.run()` inside a running loop crashes. A thread with its own loop
is the safe, standard pattern.

### Phase 3 — Supervisor wiring
**File:** `apps/agents/supervisor.py`

Four touch-points:

- **`_plan_agent_execution`** — add `"company_name"` to the expected JSON output.
  Piggy-backs on the existing LLM call; zero extra API cost. Update fallback default.
- **New sentiment step** — after Alert, before Synthesis. Gate: config flag AND plan.
  Fetches news via Phase 2 module, calls `sentiment_agent.analyze()`, emits progress.
- **Early-exit path** — run sentiment BEFORE the early return (sentiment is news-based,
  not RAG-dependent). Include it in the early-exit `SupervisorOutput`.
- **`_synthesize_response`** — accept `sentiment_output` param, inject a
  `=== Sentiment Analysis ===` block into the LLM context. Update
  `_calculate_confidence` to factor in sentiment confidence.

### Phase 4 — Schema cleanup
**File:** `apps/agents/schemas.py`

- Add `from scraping.news.schemas import NewsArticle` at top
- Replace `news_articles: List[Any]` → `List[NewsArticle]`
- Delete the 4-line comment block about circular deps (no circular dep exists)

### Phase 5 — Copilot route
**File:** `apps/api/routes/copilot.py`

- Add `"sentiment"` to `DEFAULT_AGENT_IDS`
- Add `"sentiment": "ready"` to health-check response

---

## Design Decisions

| Decision | Why |
|----------|-----|
| Two-gate toggle (config + LLM plan) | Config = ops kill switch. LLM plan = per-query relevance. A revenue query should not hit news scrapers. |
| Supabase first, scrape fallback | DB is <1 s. Scraping is 10-30 s + needs Playwright. Only pay scrape cost on cache miss. |
| Thread-pool for async scrapers | Supervisor is sync; scrapers are async; FastAPI owns the loop. Thread with own `asyncio.run()` is deadlock-free. |
| 60 s scraping timeout | Scraping can hang. Agent handles empty `news_articles` gracefully — falls back to keyword analysis on RAG context. |
| Company name extracted in planning call | Already making that LLM call. One extra JSON field = free. Separate extraction call would double latency. |
| Sentiment runs even when RAG is low | Orthogonal sources. RAG = PDFs. Sentiment = news. "What's the sentiment on X?" deserves an answer even if PDFs have nothing on X. |
| `news_fetcher.py` lives in `agents/` | It's agent-layer decision logic (try DB → fallback → timeout). The scrapers it calls stay in `scraping/`. Clean boundary. |

## Risk Points

| Risk | Mitigation |
|------|------------|
| Playwright not installed at runtime | Scraping throws; `news_fetcher` catches; returns `[]`; agent proceeds on RAG context |
| Supabase env vars missing | `get_supabase_client()` returns `None`; triggers scrape fallback |
| Scraping latency (10-30 s) | `USE_SENTIMENT_AGENT=false` disables entirely; timeout caps worst case at 60 s |
| `datetime.utcnow` deprecation (3.12+) | Minor warning only; follow-up task |
