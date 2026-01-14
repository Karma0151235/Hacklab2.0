"""
Filings API Routes
Provides aggregated filing/announcement data from Milvus vector database
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from pymilvus import Collection, connections
import re
import os

from etl.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


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
    """
    try:
        # Connect to Milvus
        milvus_host = os.getenv('MILVUS_HOST', 'localhost')
        milvus_port = int(os.getenv('MILVUS_PORT', '19639'))
        
        try:
            connections.connect("default", host=milvus_host, port=milvus_port)
        except Exception:
            pass  # May already be connected
        
        # Get collection
        collection = Collection("pdf_text_chunks")
        collection.load()
        
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
        logger.error(f"Error fetching filings: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch filings: {str(e)}"
        )
