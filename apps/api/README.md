# PDF Ingestion API

FastAPI-based REST API for uploading and processing PDF files through the ETL pipeline.

## Features

- ✅ **Multi-file upload**: Upload multiple PDFs in a single request
- ✅ **Background processing**: Async processing with job tracking
- ✅ **Real-time status**: Check processing progress via job ID
- ✅ **Full ETL pipeline**: Extract → Chunk → Embed → Load to MilvusDB
- ✅ **Error handling**: Comprehensive error reporting per file

## Quick Start

### 1. Start the API Server

```bash
# From the apps directory
uv run python run_api.py
```

The API will be available at: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

### 2. Upload PDFs

**Using the test client:**

```bash
uv run python test_upload_pdfs.py data/pdfs/*.pdf
```

**Using curl:**

```bash
curl -X POST "http://localhost:8000/api/v1/ingest/pdfs" \
  -F "files=@path/to/file1.pdf" \
  -F "files=@path/to/file2.pdf"
```

**Using Python requests:**

```python
import requests

files = [
    ('files', ('report1.pdf', open('report1.pdf', 'rb'), 'application/pdf')),
    ('files', ('report2.pdf', open('report2.pdf', 'rb'), 'application/pdf'))
]

response = requests.post('http://localhost:8000/api/v1/ingest/pdfs', files=files)
result = response.json()
print(f"Job ID: {result['job_id']}")
```

### 3. Check Status

```bash
curl "http://localhost:8000/api/v1/ingest/status/{job_id}"
```

## API Endpoints

### `POST /api/v1/ingest/pdfs`

Upload multiple PDF files for processing.

**Request:**
- Content-Type: `multipart/form-data`
- Body: Multiple files with key `files`

**Response:**
```json
{
  "job_id": "job_20260114_070000",
  "status": "pending",
  "message": "Processing started for 2 PDF files",
  "files_received": 2,
  "filenames": ["report1.pdf", "report2.pdf"]
}
```

### `GET /api/v1/ingest/status/{job_id}`

Get the status of a processing job.

**Response:**
```json
{
  "job_id": "job_20260114_070000",
  "status": "processing",
  "total_files": 2,
  "processed_files": 1,
  "text_chunks_loaded": 104,
  "table_chunks_loaded": 0,
  "errors": []
}
```

**Status values:**
- `pending`: Job queued but not started
- `processing`: Currently processing files
- `completed`: All files processed successfully
- `failed`: Fatal error occurred

### `GET /api/v1/ingest/jobs`

List all ingestion jobs.

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "job_20260114_070000",
      "status": "completed",
      "total_files": 2,
      "processed_files": 2,
      ...
    }
  ]
}
```

### `GET /health`

Health check endpoint.

### `GET /`

API information.

## Processing Flow

1. **Upload**: PDFs are uploaded and saved to temporary directory
2. **Job Creation**: Job ID is generated and returned immediately
3. **Background Processing**: For each PDF:
   - Extract text and tables using `PDFExtractor`
   - Chunk text into smaller pieces with `TextChunker`
   - Generate embeddings with `EmbeddingGenerator`
   - Load chunks into MilvusDB with `MilvusPDFManager`
4. **Status Updates**: Job status is updated in real-time
5. **Completion**: Final statistics are available via status endpoint

## Error Handling

- Individual file errors don't stop the entire job
- Errors are tracked per file in the `errors` array
- Job continues processing remaining files
- Failed files are logged but won't block successful ones

## Architecture

```
api/
├── main.py              # FastAPI app initialization
├── routes/
│   ├── __init__.py
│   └── pdf_ingestion.py # PDF upload and processing endpoints
run_api.py               # Server runner script
test_upload_pdfs.py      # Test client for uploads
```

## Configuration

The API uses the existing ETL components:
- **Text chunking**: 500 chars with 50 char overlap
- **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2`
- **Vector DB**: MilvusDB at `localhost:19639`

See `etl/` modules for configuration details.

## Production Considerations

For production deployment, consider:

1. **Replace in-memory job storage** with Redis or database
2. **Add authentication** and rate limiting
3. **Configure CORS** properly (currently allows all origins)
4. **Add file size limits** to prevent abuse
5. **Implement cleanup** for old job data
6. **Add monitoring** and metrics collection
7. **Use Celery/RQ** for more robust background task management

## Troubleshooting

**API won't start:**
- Check if port 8000 is available
- Ensure all dependencies are installed: `uv sync`
- Check MilvusDB is running

**Upload fails:**
- Verify file is valid PDF
- Check file size (no limit currently set)
- Ensure API server is running

**Processing stuck:**
- Check API logs for errors
- Verify MilvusDB connection
- Check embedding model is loaded

**No tables extracted:**
- See encoding fix in `pdf_extractor.py`
- Java must be installed for tabula-py
- Some PDFs may not have extractable tables
