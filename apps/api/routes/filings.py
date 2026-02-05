"""
Filings API Routes
Provides aggregated filing/announcement data from Milvus vector database
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
import re
import os

from etl.logging_config import get_logger
from agents.config import AgentConfig

logger = get_logger(__name__)

router = APIRouter()
_filings_collection = None


def _get_filings_collection():
    global _filings_collection
    if _filings_collection is not None:
        return _filings_collection

    try:
        from pymilvus import Collection, connections
    except ModuleNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"Milvus client not available: {str(e)}")

    env_host = os.getenv("MILVUS_HOST")
    env_port = os.getenv("MILVUS_PORT")
    milvus_host = env_host if env_host else AgentConfig.MILVUS_HOST
    milvus_port = int(env_port) if env_port else AgentConfig.MILVUS_PORT

    try:
        connections.connect("default", host=milvus_host, port=milvus_port)
    except Exception as e:
        _filings_collection = None
        raise HTTPException(status_code=503, detail=f"Milvus connection failed: {str(e)}")

    try:
        collection = Collection("pdf_text_chunks")
        collection.load()
        _filings_collection = collection
        return _filings_collection
    except Exception as e:
        _filings_collection = None
        raise HTTPException(status_code=503, detail=f"Milvus collection load failed: {str(e)}")


# Response Models
class Filing(BaseModel):
    """Filing/Announcement object for timeline display"""
    filing_id: str
    company_code: str
    company_name: str
    announcement_date: str
    document_type: str
    title: str
    summary: Optional[str] = None
    pdf_urls: List[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    tables_count: int = 0
    keywords: List[str] = Field(default_factory=list)


class FilingsResponse(BaseModel):
    """Response containing list of filings with pagination metadata"""
    filings: List[Filing]
    total: int
    limit: int
    offset: int


def extract_date_from_doc_id(doc_id: str) -> str:
    """Extract announcement date from doc_id format: bursa_*_YYYYMMDD_*"""
    try:
        # Pattern: bursa_announcement_details?ann_id=1234567_YYYYMMDD_...
        match = re.search(r'_(\d{8})_', str(doc_id))
        if match:
            date_str = match.group(1)
            year = date_str[0:4]
            month = date_str[4:6]
            day = date_str[6:8]
            return f"{year}-{month}-{day}T00:00:00Z"
        
        # Fallback: use current date
        return datetime.utcnow().isoformat() + "Z"
    except Exception as e:
        logger.warning(f"Failed to extract date from doc_id {doc_id}: {e}")
        return datetime.utcnow().isoformat() + "Z"


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text (capitalized words)"""
    try:
        # Find capitalized words (simple heuristic)
        words = re.findall(r'\b[A-Z][a-z]+\b', text)
        # Deduplicate and limit
        unique_words = list(dict.fromkeys(words))  # Preserve order
        return unique_words[:max_keywords]
    except Exception:
        return []


@router.get("/filings", response_model=FilingsResponse)
async def get_filings(
    company_code: Optional[str] = Query(None, description="Filter by company code"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of filings to return"),
    offset: int = Query(0, ge=0, description="Number of filings to skip")
):
    """
    Get filings/announcements from vector database

    Aggregates text chunks by doc_id to create Filing objects for timeline display.
    Falls back to mock data if Milvus is unavailable.
    """
    # Mock data fallback
    mock_filings = [
        Filing(
            filing_id="bursa_announcement_1_20250205",
            company_code="AMBANK",
            company_name="Ambank Group Limited",
            announcement_date="2025-02-05T10:30:00Z",
            document_type="announcement",
            title="Quarterly Financial Results - Q4 2024",
            summary="Ambank reports strong Q4 2024 results with 12% YoY growth in net income...",
            pdf_urls=["https://example.com/ambank-q4-2024.pdf"],
            sentiment="positive",
            tables_count=3,
            keywords=["Financial", "Results", "Growth", "Revenue"]
        ),
        Filing(
            filing_id="bursa_announcement_2_20250204",
            company_code="MAYBANK",
            company_name="Maybank Corporation",
            announcement_date="2025-02-04T09:15:00Z",
            document_type="announcement",
            title="Board Announcement - Dividend Declaration",
            summary="Maybank declares interim dividend of 8 sen per share for financial year 2024...",
            pdf_urls=["https://example.com/maybank-dividend.pdf"],
            sentiment="positive",
            tables_count=1,
            keywords=["Dividend", "Distribution", "Shareholders"]
        ),
        Filing(
            filing_id="bursa_announcement_3_20250203",
            company_code="CIMB",
            company_name="CIMB Group Holdings",
            announcement_date="2025-02-03T14:45:00Z",
            document_type="announcement",
            title="Corporate Action - Stock Split Announcement",
            summary="CIMB announces 2-for-1 stock split effective from February 15, 2025...",
            pdf_urls=["https://example.com/cimb-stock-split.pdf"],
            sentiment="neutral",
            tables_count=2,
            keywords=["Stock", "Split", "Corporate", "Action"]
        ),
        Filing(
            filing_id="bursa_announcement_4_20250201",
            company_code="PUBLIC",
            company_name="Public Bank Berhad",
            announcement_date="2025-02-01T11:20:00Z",
            document_type="announcement",
            title="Material Information - Strategic Partnership",
            summary="Public Bank enters into strategic partnership with Southeast Asian fintech firm...",
            pdf_urls=["https://example.com/public-partnership.pdf"],
            sentiment="positive",
            tables_count=1,
            keywords=["Partnership", "Technology", "Strategic", "Agreement"]
        ),
        Filing(
            filing_id="bursa_announcement_5_20250130",
            company_code="AMBANK",
            company_name="Ambank Group Limited",
            announcement_date="2025-01-30T16:10:00Z",
            document_type="announcement",
            title="Regulatory Announcement - Capital Adequacy",
            summary="Ambank maintains strong capital position with CAR above regulatory requirements...",
            pdf_urls=["https://example.com/ambank-capital.pdf"],
            sentiment="neutral",
            tables_count=2,
            keywords=["Capital", "Regulatory", "Compliance", "Adequacy"]
        ),
    ]

    try:
        collection = _get_filings_collection()

        # Normalize values if called directly (Query objects are not primitives)
        if not isinstance(company_code, str):
            company_code = None
        if not isinstance(document_type, str):
            document_type = None
        if not isinstance(limit, int):
            limit = 100
        if not isinstance(offset, int):
            offset = 0

        # Build filter expression
        filter_expr = ""
        if company_code:
            filter_expr = f'company_code == "{company_code}"'
        if document_type:
            if filter_expr:
                filter_expr += f' && document_type == "{document_type}"'
            else:
                filter_expr = f'document_type == "{document_type}"'

        # Query entities
        output_fields = ["chunk_id", "doc_id", "content", "company_code", "document_type", "chunk_order"]

        try:
            if filter_expr:
                results = collection.query(
                    expr=filter_expr,
                    output_fields=output_fields,
                    limit=limit * 10  # Get more to account for grouping
                )
            else:
                # No filter - get recent chunks
                results = collection.query(
                    expr="chunk_id != ''",  # Get all
                    output_fields=output_fields,
                    limit=limit * 10
                )
        except Exception as e:
            global _filings_collection
            _filings_collection = None
            logger.warning(f"Milvus query failed: {str(e)}, using mock data")
            total = len(mock_filings)
            filings_paginated = mock_filings[offset:offset + limit]
            return FilingsResponse(
                filings=filings_paginated,
                total=total,
                limit=limit,
                offset=offset
            )

        # Group by doc_id
        filings_map: Dict[str, Dict[str, Any]] = {}

        for entity in results:
            doc_id = entity.get("doc_id", "")
            if not doc_id:
                continue

            if doc_id not in filings_map:
                # Create new filing
                content = entity.get("content", "")
                company = entity.get("company_code", "UNKNOWN")

                filings_map[doc_id] = {
                    "filing_id": doc_id,
                    "company_code": company,
                    "company_name": company,  # Same as code in current schema
                    "announcement_date": extract_date_from_doc_id(doc_id),
                    "document_type": entity.get("document_type", "announcement"),
                    "title": content[:200] if len(content) > 200 else content,  # Full title, no ellipsis
                    "summary": content[:300] + "..." if len(content) > 300 else content,
                    "pdf_urls": [],
                    "sentiment": "neutral",
                    "tables_count": 0,
                    "keywords": extract_keywords(content),
                    "_chunks": [entity],
                    "_all_content": content,
                }
            else:
                # Add chunk to existing filing
                filing = filings_map[doc_id]
                filing["_chunks"].append(entity)
                filing["_all_content"] += " " + entity.get("content", "")

        # Aggregate metadata
        for filing in filings_map.values():
            # Count unique chunks as table count approximation
            filing["tables_count"] = len(filing["_chunks"])

            # Extract keywords from all content
            filing["keywords"] = extract_keywords(filing["_all_content"])

            # Clean up internal fields
            del filing["_chunks"]
            del filing["_all_content"]

        # Convert to list and sort by date (newest first)
        filings_list = list(filings_map.values())
        filings_list.sort(
            key=lambda x: x["announcement_date"],
            reverse=True
        )

        # Apply pagination
        total = len(filings_list)
        filings_paginated = filings_list[offset:offset + limit]

        # Convert to Pydantic models
        filing_models = [Filing(**f) for f in filings_paginated]

        logger.info(f"Retrieved {len(filing_models)} filings (total: {total}, limit: {limit}, offset: {offset})")

        return FilingsResponse(
            filings=filing_models,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.warning(f"Milvus unavailable ({str(e)}), using mock filings data")
        total = len(mock_filings)
        filings_paginated = mock_filings[offset:offset + limit]
        return FilingsResponse(
            filings=filings_paginated,
            total=total,
            limit=limit,
            offset=offset
        )
