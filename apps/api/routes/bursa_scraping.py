"""
Bursa Malaysia Scraping API Routes
Handles scraping job control, status tracking, and results retrieval
"""

from pathlib import Path
from typing import List, Optional, Dict
import tempfile
import uuid
from datetime import datetime
import asyncio

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from scraping.bursa_web_scraper import BursaWebScraper
from scraping.scraper_runner import ScraperRunner
from etl.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


# Request/Response Models
class BursaScrapingRequest(BaseModel):
    """Request model for starting a Bursa scraping job"""
    year: int = Field(default=2024, ge=2020, le=2026, description="Financial year to scrape")
    max_announcements: int = Field(default=10, ge=5, le=100, description="Maximum announcements to scrape")
    company_filter: Optional[str] = Field(default=None, description="Comma-separated company names/codes (e.g., 'MAYBANK, CIMB, PCHEM')")
    resource_efficient: bool = Field(
        default=False,
        description="Use headless mode, block heavy resources, and disable video to reduce memory usage"
    )
    use_cloudscraper: bool = Field(
        default=True,
        description="Use cloudscraper + proxy rotation fallback when Cloudflare blocks the listing page"
    )
    manual_captcha_timeout_seconds: int = Field(
        default=120,
        ge=10,
        le=600,
        description="Max wait time for manual Cloudflare verification (seconds)"
    )


class BursaScrapingResponse(BaseModel):
    """Response model for scraping job initiation"""
    job_id: str
    status: str
    message: str
    year: int
    max_announcements: int
    company_filter: Optional[List[str]] = None
    resource_efficient: bool
    use_cloudscraper: bool
    manual_captcha_timeout_seconds: int


class BursaScrapingStatus(BaseModel):
    """Status model for scraping job"""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    phase: str  # loading, detecting, scraping, finalizing, complete
    message: Optional[str] = None
    total_announcements: int
    scraped_announcements: int
    errors: List[str] = Field(default_factory=list)
    ingestion_status: Optional[str] = None
    ingestion_stats: Optional[Dict[str, int]] = None
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    current_url: Optional[str] = None
    current_category: Optional[str] = None
    current_year: Optional[int] = None
    target_companies: Optional[List[str]] = None
    created_at: str
    completed_at: Optional[str] = None


class AnnouncementRecord(BaseModel):
    """Individual announcement record"""
    company_code: Optional[str]
    announcement_date: str
    category: str
    title: str
    tables_count: int
    detail_page_url: str


class BursaScrapingResults(BaseModel):
    """Results model for completed scraping job"""
    job_id: str
    status: str
    total_announcements: int
    announcements: List[AnnouncementRecord]
    video_available: bool
    ingestion_stats: Optional[Dict[str, int]] = None
    ingestion_status: Optional[str] = None


# In-memory job storage (replace with Redis/DB in production)
job_statuses = {}
job_results = {}


def parse_company_filter(company_filter: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated company filter string"""
    if not company_filter:
        return None
    
    # Split by comma and strip whitespace
    companies = [c.strip().upper() for c in company_filter.split(',') if c.strip()]
    return companies if companies else None


def run_scraping_task_sync(
    job_id: str,
    year: int,
    max_announcements: int,
    company_filter: Optional[List[str]],
    resource_efficient: bool,
    use_cloudscraper: bool,
    manual_captcha_timeout_seconds: int
):
    """
    Synchronous wrapper to run scraper in a separate thread with its own event loop
    This is required for Windows + Playwright + FastAPI compatibility
    """
    import sys
    import asyncio
    
    # Create new event loop for this thread
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(
            run_scraping_task_async(
                job_id,
                year,
                max_announcements,
                company_filter,
                resource_efficient,
                use_cloudscraper,
                manual_captcha_timeout_seconds
            )
        )
    finally:
        loop.close()


async def run_scraping_task_async(
    job_id: str,
    year: int,
    max_announcements: int,
    company_filter: Optional[List[str]],
    resource_efficient: bool,
    use_cloudscraper: bool,
    manual_captcha_timeout_seconds: int
):
    """
    Background task to run the Bursa scraper (async implementation)
    """
    try:
        logger.info(f"[Job {job_id}] Starting scraping: year={year}, max={max_announcements}, companies={company_filter}")
        
        # Update status to processing
        job_statuses[job_id]["status"] = "processing"
        job_statuses[job_id]["phase"] = "loading"
        job_statuses[job_id]["progress"] = 10
        
        def progress_callback(phase: str, percent: int, message: str, metadata: Dict[str, int]):
            job_statuses[job_id]["phase"] = phase
            job_statuses[job_id]["progress"] = percent
            job_statuses[job_id]["message"] = message
            if metadata:
                if "scraped_count" in metadata:
                    job_statuses[job_id]["scraped_announcements"] = metadata["scraped_count"]
                if "total_announcements" in metadata:
                    job_statuses[job_id]["total_announcements"] = metadata["total_announcements"]
                for key in [
                    "current_company",
                    "current_title",
                    "current_url",
                    "current_category",
                    "current_year",
                    "target_companies",
                ]:
                    if key in metadata:
                        job_statuses[job_id][key] = metadata[key]

        # Initialize scraper
        scraper = BursaWebScraper(progress_callback=progress_callback)
        
        # Run scraping
        result = await scraper.scrape(
            year=year,
            max_announcements=max_announcements,
            company_filter=company_filter,
            categories=None,
            scrape_all_categories=True,
            resource_efficient=resource_efficient,
            use_cloudscraper=use_cloudscraper,
            manual_captcha_timeout_seconds=manual_captcha_timeout_seconds
        )
        
        # Process results
        announcement_records = []
        for record in result.get('structured_records', []):
            announcement_records.append({
                'company_code': record.company_code,
                'announcement_date': record.announcement_date,
                'category': record.category,
                'title': record.title,
                'tables_count': record.tables_count,
                'detail_page_url': record.detail_page_url
            })
        
        # Store results
        job_results[job_id] = {
            'structured_records': result.get('structured_records', []),
            'document_objects': result.get('document_objects', []),
            'announcements': announcement_records,
            'video_base64': result.get('video_base64', ''),
            'total_announcements': result.get('total_announcements', 0)
        }
        
        # ============= NEW: Automatic Database Ingestion =============
        # Ingest scraped data into MilvusDB
        document_objects = result.get('document_objects', [])
        if document_objects:
            try:
                logger.info(f"[Job {job_id}] Starting database ingestion of {len(document_objects)} documents...")
                job_statuses[job_id]["phase"] = "ingesting"
                job_statuses[job_id]["progress"] = 85
                
                # Import ingestion module
                import sys
                from pathlib import Path
                
                # Add apps directory to path if not already there
                apps_dir = Path(__file__).parent.parent.parent
                if str(apps_dir) not in sys.path:
                    sys.path.insert(0, str(apps_dir))
                
                from bursa_ingestion import ingest_bursa_scraping_results
                
                # Ingest into MilvusDB
                def ingestion_progress_callback(stats: Dict[str, int]):
                    job_statuses[job_id]["ingestion_status"] = "processing"
                    job_statuses[job_id]["ingestion_stats"] = stats

                ingestion_result = ingest_bursa_scraping_results(
                    document_objects,
                    progress_callback=ingestion_progress_callback
                )
                
                # Store ingestion stats in job results
                job_results[job_id]['ingestion_stats'] = ingestion_result.get('stats', {})
                job_results[job_id]['ingestion_status'] = ingestion_result.get('status', 'unknown')
                job_statuses[job_id]["ingestion_stats"] = ingestion_result.get('stats', {})
                job_statuses[job_id]["ingestion_status"] = ingestion_result.get('status', 'unknown')
                
                if ingestion_result.get('status') == 'success':
                    logger.info(f"[Job {job_id}] Database ingestion complete: {ingestion_result.get('stats', {})}")
                else:
                    logger.warning(f"[Job {job_id}] Database ingestion failed: {ingestion_result.get('message', 'Unknown error')}")
                    
            except Exception as ingest_error:
                logger.error(f"[Job {job_id}] Database ingestion error: {str(ingest_error)}")
                job_statuses[job_id]["errors"].append(f"Ingestion error: {str(ingest_error)}")
                import traceback
                traceback.print_exc()
        else:
            logger.warning(f"[Job {job_id}] No document objects to ingest")
        # ==============================================================
        
        # Update status to completed
        job_statuses[job_id]["status"] = "completed"
        job_statuses[job_id]["phase"] = "complete"
        job_statuses[job_id]["progress"] = 100
        job_statuses[job_id]["scraped_announcements"] = len(announcement_records)
        job_statuses[job_id]["total_announcements"] = len(announcement_records)
        job_statuses[job_id]["completed_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"[Job {job_id}] Scraping complete: {len(announcement_records)} announcements")
        
    except Exception as e:
        logger.error(f"[Job {job_id}] Scraping failed: {str(e)}")
        job_statuses[job_id]["status"] = "failed"
        job_statuses[job_id]["phase"] = "error"
        job_statuses[job_id]["errors"].append(str(e))
        job_statuses[job_id]["message"] = str(e)
        import traceback
        traceback.print_exc()


@router.post("/scraping/bursa/start", response_model=BursaScrapingResponse)
async def start_bursa_scraping(
    request: BursaScrapingRequest
):
    """
    Start a Bursa Malaysia scraping job
    
    - **year**: Financial year to scrape (2020-2026)
    - **max_announcements**: Maximum announcements to scrape (5-100)
    - **company_filter**: Optional comma-separated company names/codes
    
    Returns job ID for tracking progress
    """
    import threading
    import os
    
    # ============= NEW: Pre-flight Milvus Health Check =============
    try:
        from etl.db.milvus import MilvusStorage
        milvus_host = os.getenv('MILVUS_HOST', 'localhost')
        milvus_port = int(os.getenv('MILVUS_PORT', '19639'))
        
        logger.info(f"Checking Milvus connection at {milvus_host}:{milvus_port}...")
        milvus_check = MilvusStorage(host=milvus_host, port=milvus_port)
        
        if not milvus_check.connected:
            raise HTTPException(
                status_code=503,
                detail=f"MilvusDB is not available at {milvus_host}:{milvus_port}. Please start Milvus before scraping."
            )
        
        if not milvus_check.health_check():
            raise HTTPException(
                status_code=503,
                detail=f"MilvusDB health check failed at {milvus_host}:{milvus_port}. Database may be unhealthy."
            )
        
        logger.info("✓ Milvus health check passed")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to verify Milvus connection: {str(e)}"
        )
    # ==============================================================
    
    # Generate job ID
    job_id = f"bursa_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # Parse company filter
    companies = parse_company_filter(request.company_filter)
    
    # Initialize job status
    job_statuses[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0,
        "phase": "initializing",
        "total_announcements": request.max_announcements,
        "scraped_announcements": 0,
        "errors": [],
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "year": request.year,
        "company_filter": companies,
        "resource_efficient": request.resource_efficient,
        "use_cloudscraper": request.use_cloudscraper,
        "manual_captcha_timeout_seconds": request.manual_captcha_timeout_seconds,
        "current_company": None,
        "current_title": None,
        "current_url": None,
        "current_category": None,
        "current_year": request.year,
        "target_companies": companies or [],
    }
    
    # Start scraping in a separate thread (required for Windows + Playwright)
    thread = threading.Thread(
        target=run_scraping_task_sync,
        args=(
            job_id,
            request.year,
            request.max_announcements,
            companies,
            request.resource_efficient,
            request.use_cloudscraper,
            request.manual_captcha_timeout_seconds
        ),
        daemon=True
    )
    thread.start()
    
    logger.info(f"[Job {job_id}] Created scraping job: year={request.year}, max={request.max_announcements}, companies={companies}")
    
    return BursaScrapingResponse(
        job_id=job_id,
        status="pending",
        message=f"Scraping job started for year {request.year}",
        year=request.year,
        max_announcements=request.max_announcements,
        company_filter=companies,
        resource_efficient=request.resource_efficient,
        use_cloudscraper=request.use_cloudscraper,
        manual_captcha_timeout_seconds=request.manual_captcha_timeout_seconds
    )


@router.get("/scraping/bursa/status/{job_id}", response_model=BursaScrapingStatus)
async def get_bursa_scraping_status(job_id: str):
    """
    Get the status of a Bursa scraping job
    
    - **job_id**: Job ID returned from start endpoint
    """
    if job_id not in job_statuses:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = job_statuses[job_id]
    
    return BursaScrapingStatus(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        phase=job["phase"],
        message=job.get("message"),
        total_announcements=job["total_announcements"],
        scraped_announcements=job["scraped_announcements"],
        errors=job["errors"],
        ingestion_status=job.get("ingestion_status"),
        ingestion_stats=job.get("ingestion_stats"),
        current_company=job.get("current_company"),
        current_title=job.get("current_title"),
        current_url=job.get("current_url"),
        current_category=job.get("current_category"),
        current_year=job.get("current_year"),
        target_companies=job.get("target_companies"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at")
    )


@router.get("/scraping/bursa/results/{job_id}", response_model=BursaScrapingResults)
async def get_bursa_scraping_results(job_id: str):
    """
    Get the results of a completed Bursa scraping job
    
    - **job_id**: Job ID returned from start endpoint
    """
    if job_id not in job_statuses:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = job_statuses[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job {job_id} is not completed yet (status: {job['status']})")
    
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail=f"Results for job {job_id} not found")
    
    results = job_results[job_id]
    
    return BursaScrapingResults(
        job_id=job_id,
        status="completed",
        total_announcements=results['total_announcements'],
        announcements=[AnnouncementRecord(**ann) for ann in results['announcements']],
        video_available=len(results.get('video_base64', '')) > 0,
        ingestion_stats=results.get('ingestion_stats'),
        ingestion_status=results.get('ingestion_status')
    )


@router.get("/scraping/bursa/video/{job_id}")
async def get_bursa_scraping_video(job_id: str):
    """
    Get the video recording of a scraping job
    
    - **job_id**: Job ID returned from start endpoint
    
    Returns video file as WebM (supports seeking)
    """
    from fastapi.responses import Response
    import base64
    
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail=f"Results for job {job_id} not found")
    
    results = job_results[job_id]
    video_base64 = results.get('video_base64', '')
    
    if not video_base64:
        raise HTTPException(status_code=404, detail=f"No video available for job {job_id}")
    
    # Decode base64 video
    video_bytes = base64.b64decode(video_base64)
    
    # Return as inline video (not attachment) to support seeking
    return Response(
        content=video_bytes,
        media_type="video/webm",
        headers={
            "Content-Disposition": f"inline; filename=bursa_scraping_{job_id}.webm",
            "Accept-Ranges": "bytes",
            "Content-Length": str(len(video_bytes))
        }
    )


@router.get("/scraping/bursa/jobs")
async def list_bursa_scraping_jobs():
    """
    List all Bursa scraping jobs
    """
    return {
        "jobs": list(job_statuses.values())
    }
