"""
FastAPI main application
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import pdf_ingestion, bursa_scraping, vectordb, copilot, filings, companies, news
from agents.config import AgentConfig

app = FastAPI(
    title="Financial Intelligence ETL API",
    description="API for PDF ingestion and financial data processing",
    version="1.0.0"
)

def _get_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        return ["http://localhost:3000"]
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    # Deduplicate while preserving order
    origins = list(dict.fromkeys(origins))
    if "*" in origins and len(origins) > 1:
        origins = [origin for origin in origins if origin != "*"]
    return origins or ["http://localhost:3000"]


def _get_cors_allow_credentials(origins: list[str]) -> bool:
    if "*" in origins:
        return False
    return True


# Configure CORS
_cors_origins = _get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_get_cors_allow_credentials(_cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pdf_ingestion.router, prefix="/api/v1", tags=["PDF Ingestion"])
app.include_router(bursa_scraping.router, prefix="/api/v1", tags=["Bursa Scraping"])
app.include_router(vectordb.router, prefix="/api/v1", tags=["Vector Database"])
app.include_router(copilot.router, prefix="/api/v1", tags=["Copilot"])
app.include_router(filings.router, prefix="/api/v1", tags=["Filings"])
app.include_router(companies.router, prefix="/api/v1", tags=["Companies"])
app.include_router(news.router, prefix="/api/v1", tags=["News"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Financial Intelligence ETL API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
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

    openrouter_status = "configured" if os.getenv("OPENROUTER_API_KEY") else "missing_key"
    status = "healthy" if milvus_status == "connected" and openrouter_status == "configured" else "degraded"

    return {
        "status": status,
        "milvus": milvus_status,
        "openrouter": openrouter_status,
    }
