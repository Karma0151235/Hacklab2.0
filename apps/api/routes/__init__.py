"""
API routes package
"""

from . import (
    pdf_ingestion,
    bursa_scraping,
    vectordb,
    copilot,
    filings,
    companies,
    news,
    alerts,
)

__all__ = [
    "pdf_ingestion",
    "bursa_scraping",
    "vectordb",
    "copilot",
    "filings",
    "companies",
    "news",
    "alerts",
]
