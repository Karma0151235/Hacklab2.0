"""
Companies API Routes
Provides aggregated company data from Milvus vector database
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pymilvus import Collection, connections
import os
from collections import defaultdict

from etl.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Response Models
class Company(BaseModel):
    """Company object for companies list"""
    company_code: str
    company_name: str
    ticker: str
    sector: str = "General"
    market_cap: Optional[int] = None
    filings_count: int
    latest_filing_date: Optional[str] = None
    alert_count: int = 0


class CompaniesResponse(BaseModel):
    """Response containing list of companies"""
    companies: List[Company]
    total: int


@router.get("/companies", response_model=CompaniesResponse)
async def get_companies():
    """
    Get all companies from vector database
    
    Aggregates unique companies from pdf_text_chunks collection
    and counts their filings.
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
        
        # Query all entities
        output_fields = ["doc_id", "company_code", "chunk_id"]
        
        results = collection.query(
            expr="chunk_id != ''",  # Get all
            output_fields=output_fields,
            limit=16384  # Max limit to get all companies
        )
        
        # Aggregate by company_code
        companies_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "doc_ids": set(),
            "company_code": "",
            "company_name": "",
        })
        
        for entity in results:
            company_code = entity.get("company_code", "UNKNOWN")
            doc_id = entity.get("doc_id", "")
            
            if company_code and doc_id:
                companies_map[company_code]["company_code"] = company_code
                companies_map[company_code]["company_name"] = company_code  # Same as code
                companies_map[company_code]["doc_ids"].add(doc_id)
        
        # Convert to Company objects
        companies_list = []
        for company_code, data in companies_map.items():
            company = Company(
                company_code=company_code,
                company_name=data["company_name"],
                ticker=company_code,  # Use company_code as ticker
                sector="General",  # Default sector
                market_cap=None,  # Not available in current schema
                filings_count=len(data["doc_ids"]),
                latest_filing_date=None,  # Could extract from doc_id if needed
                alert_count=0  # Alerts not implemented yet
            )
            companies_list.append(company)
        
        # Sort by company_code
        companies_list.sort(key=lambda x: x.company_code)
        
        logger.info(f"Retrieved {len(companies_list)} companies")
        
        return CompaniesResponse(
            companies=companies_list,
            total=len(companies_list)
        )
        
    except Exception as e:
        logger.error(f"Error fetching companies: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch companies: {str(e)}"
        )
