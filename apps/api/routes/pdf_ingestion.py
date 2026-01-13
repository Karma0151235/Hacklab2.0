"""
PDF Ingestion API Routes
Handles multi-file PDF uploads and triggers ETL pipeline
"""

from pathlib import Path
from typing import List
import tempfile
import shutil
from datetime import datetime

from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks
from pydantic import BaseModel

from etl.processing.pdf_extractor import PDFExtractor
from etl.chunking.chunker import TextChunker
from etl.embeddings.generator import EmbeddingGenerator
from etl.db.milvus_pdf_manager import MilvusPDFManager
from etl.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter()


class PDFUploadResponse(BaseModel):
    """Response model for PDF upload"""
    job_id: str
    status: str
    message: str
    files_received: int
    filenames: List[str]


class PDFProcessingStatus(BaseModel):
    """Status model for PDF processing"""
    job_id: str
    status: str  # pending, processing, completed, failed
    total_files: int
    processed_files: int
    text_chunks_loaded: int
    table_chunks_loaded: int
    errors: List[str] = []


class IngestionStats(BaseModel):
    """Statistics for ingestion job"""
    filename: str
    text_chars: int
    tables_count: int
    text_chunks: int
    table_chunks: int
    pages: int
    company_name: str


# In-memory job storage (replace with Redis/DB in production)
job_statuses = {}


def extract_company_name(filename: str) -> str:
    """Extract company name from filename"""
    # Remove file extension
    name = Path(filename).stem
    # Remove common suffixes
    for suffix in [' - Quarterly results', '_Financial Report_Q12026', 'Financial Report', 'Quarterly results']:
        name = name.replace(suffix, '')
    return name.strip()


async def process_pdfs_task(job_id: str, pdf_paths: List[Path]):
    """
    Background task to process PDFs through the ETL pipeline
    """
    import uuid
    
    try:
        logger.info(f"[Job {job_id}] Starting PDF processing for {len(pdf_paths)} files")
        
        # Update status to processing
        job_statuses[job_id]["status"] = "processing"
        
        # Initialize ETL components
        extractor = PDFExtractor()
        chunker = TextChunker(chunk_size=500, overlap=50)
        embedding_gen = EmbeddingGenerator()
        db_manager = MilvusPDFManager()
        
        stats = []
        total_text_chunks = 0
        total_table_chunks = 0
        
        for idx, pdf_path in enumerate(pdf_paths, 1):
            try:
                logger.info(f"[Job {job_id}] Processing {idx}/{len(pdf_paths)}: {pdf_path.name}")
                
                # Step 1: Extract PDF content
                pdf_content = extractor.extract_from_file(pdf_path)
                if not pdf_content:
                    error_msg = f"Failed to extract content from {pdf_path.name}"
                    logger.error(f"[Job {job_id}] {error_msg}")
                    job_statuses[job_id]["errors"].append(error_msg)
                    continue
                
                # Extract company name
                company_name = extract_company_name(pdf_path.name)
                
                # Generate document ID
                doc_id = f"pdf_{pdf_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
                
                # Step 2: Chunk text and generate embeddings
                text_chunks = chunker.chunk_text(
                    text=pdf_content.text_content,
                    filename=pdf_path.name,
                    company_name=company_name,
                    doc_id=doc_id
                )
                
                # Prepare text chunks data for MilvusDB
                text_chunks_data = []
                if text_chunks:
                    # Generate embeddings
                    chunk_contents = [chunk.content for chunk in text_chunks]
                    embeddings = embedding_gen.generate_batch(chunk_contents)
                    
                    # Prepare chunks data
                    for chunk, embedding in zip(text_chunks, embeddings):
                        chunk_dict = {
                            "chunk_id": chunk.chunk_id,
                            "filename": pdf_path.name,
                            "company_name": company_name,
                            "content": chunk.content,
                            "embedding": embedding,
                            "page_number": chunk.page_number,
                            "source": "pdf",
                            "doc_id": doc_id,
                            "metadata": chunk.metadata,
                        }
                        text_chunks_data.append(chunk_dict)
                
                # Step 3: Prepare table chunks (if any tables were extracted)
                table_chunks_data = []
                if pdf_content.tables:
                    # Convert tables to text and generate embeddings
                    table_texts = []
                    table_indices = []
                    
                    for table_idx, table in enumerate(pdf_content.tables):
                        if not table:
                            continue
                        
                        # Convert table to readable text
                        table_text = "\n".join([" | ".join(str(cell).strip() for cell in row if cell) for row in table])
                        table_texts.append(table_text)
                        table_indices.append(table_idx)
                    
                    if table_texts:
                        # Generate embeddings for tables
                        table_embeddings = embedding_gen.generate_batch(table_texts)
                        
                        # Prepare table chunks
                        for table_idx, table_text, embedding in zip(table_indices, table_texts, table_embeddings):
                            table = pdf_content.tables[table_idx]
                            
                            table_dict = {
                                "table_id": f"table_{doc_id}_{table_idx}_{uuid.uuid4().hex[:8]}",
                                "filename": pdf_path.name,
                                "company_name": company_name,
                                "table_data": table,
                                "table_index": table_idx,
                                "source": "pdf",
                                "doc_id": doc_id,
                                "embedding": embedding,
                                "metadata": {
                                    "source": "pdf",
                                    "chunk_type": "table",
                                    "filename": pdf_path.name,
                                    "company_name": company_name,
                                    "table_index": table_idx,
                                },
                            }
                            table_chunks_data.append(table_dict)
                
                # Step 4: Load to MilvusDB
                if text_chunks_data:
                    db_manager.insert_text_chunks(text_chunks_data)
                    total_text_chunks += len(text_chunks_data)
                
                if table_chunks_data:
                    db_manager.insert_table_chunks(table_chunks_data)
                    total_table_chunks += len(table_chunks_data)
                
                # Track stats
                stats.append({
                    "filename": pdf_path.name,
                    "text_chars": len(pdf_content.text_content),
                    "tables_count": len(pdf_content.tables),
                    "text_chunks": len(text_chunks_data),
                    "table_chunks": len(table_chunks_data),
                    "pages": pdf_content.pages,
                    "company_name": company_name
                })
                
                # Update progress
                job_statuses[job_id]["processed_files"] = idx
                
                logger.info(f"[Job {job_id}] ✓ Completed {pdf_path.name}")
                
            except Exception as e:
                error_msg = f"Error processing {pdf_path.name}: {str(e)}"
                logger.error(f"[Job {job_id}] {error_msg}")
                job_statuses[job_id]["errors"].append(error_msg)
                import traceback
                traceback.print_exc()
            
            finally:
                # Clean up temp file
                try:
                    pdf_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {pdf_path}: {str(e)}")
        
        # Update final status
        job_statuses[job_id]["status"] = "completed"
        job_statuses[job_id]["text_chunks_loaded"] = total_text_chunks
        job_statuses[job_id]["table_chunks_loaded"] = total_table_chunks
        job_statuses[job_id]["stats"] = stats
        
        logger.info(f"[Job {job_id}] Processing complete: {total_text_chunks} text chunks, {total_table_chunks} table chunks")
        
    except Exception as e:
        logger.error(f"[Job {job_id}] Fatal error: {str(e)}")
        job_statuses[job_id]["status"] = "failed"
        job_statuses[job_id]["errors"].append(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()



@router.post("/ingest/pdfs", response_model=PDFUploadResponse)
async def upload_pdfs(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    Upload multiple PDF files for ETL processing
    
    - **files**: List of PDF files to process
    
    Returns job ID for tracking progress
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate file types
    pdf_files = []
    for file in files:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type: {file.filename}. Only PDF files are allowed."
            )
        pdf_files.append(file)
    
    # Generate job ID
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Save uploaded files to temp directory
    temp_dir = Path(tempfile.gettempdir()) / "pdf_ingestion" / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    saved_paths = []
    filenames = []
    
    try:
        for file in pdf_files:
            # Save file
            file_path = temp_dir / file.filename
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            saved_paths.append(file_path)
            filenames.append(file.filename)
            logger.info(f"[Job {job_id}] Saved uploaded file: {file.filename}")
    
    except Exception as e:
        # Clean up on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to save files: {str(e)}")
    
    # Initialize job status
    job_statuses[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "total_files": len(saved_paths),
        "processed_files": 0,
        "text_chunks_loaded": 0,
        "table_chunks_loaded": 0,
        "errors": [],
        "filenames": filenames,
        "created_at": datetime.now().isoformat()
    }
    
    # Start background processing
    background_tasks.add_task(process_pdfs_task, job_id, saved_paths)
    
    logger.info(f"[Job {job_id}] Created job for {len(saved_paths)} PDF files")
    
    return PDFUploadResponse(
        job_id=job_id,
        status="pending",
        message=f"Processing started for {len(saved_paths)} PDF files",
        files_received=len(saved_paths),
        filenames=filenames
    )


@router.get("/ingest/status/{job_id}", response_model=PDFProcessingStatus)
async def get_job_status(job_id: str):
    """
    Get the status of a PDF processing job
    
    - **job_id**: Job ID returned from upload endpoint
    """
    if job_id not in job_statuses:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    job = job_statuses[job_id]
    
    return PDFProcessingStatus(
        job_id=job["job_id"],
        status=job["status"],
        total_files=job["total_files"],
        processed_files=job["processed_files"],
        text_chunks_loaded=job["text_chunks_loaded"],
        table_chunks_loaded=job["table_chunks_loaded"],
        errors=job["errors"]
    )


@router.get("/ingest/jobs")
async def list_jobs():
    """
    List all ingestion jobs
    """
    return {
        "jobs": list(job_statuses.values())
    }
