"""
FastAPI main application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import pdf_ingestion, bursa_scraping, vectordb

app = FastAPI(
    title="Financial Intelligence ETL API",
    description="API for PDF ingestion and financial data processing",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pdf_ingestion.router, prefix="/api/v1", tags=["PDF Ingestion"])
app.include_router(bursa_scraping.router, prefix="/api/v1", tags=["Bursa Scraping"])
app.include_router(vectordb.router, prefix="/api/v1", tags=["Vector Database"])

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
    return {"status": "healthy"}
