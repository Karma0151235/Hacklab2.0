# PDF ETL Pipeline - Frontend Integration

## Overview

The PDF upload feature in the frontend is now fully integrated with the backend ETL pipeline. Users can upload PDFs through the web interface, and they will be automatically processed through the complete Extract-Transform-Load pipeline.

## Setup

### 1. Configure Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
# Backend API URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### 2. Start the Backend API

From the `apps/` directory:

```bash
cd ../apps
uv run python run_api.py
```

The API will start on `http://localhost:8000`

### 3. Start the Frontend

From the `frontend/` directory:

```bash
pnpm run dev
```

The frontend will start on `http://localhost:3000`

## Usage

### Navigate to Upload Page

Go to: `http://localhost:3000/ingest/upload`

### Upload PDFs

1. **Drag & Drop** PDFs into the upload zone, or **click to browse**
2. Selected files will appear in the list
3. Click **"Start ETL Pipeline"** button to begin processing
4. Watch real-time progress as files are:
   - Uploaded to the backend
   - Extracted (text + tables)
   - Chunked into smaller pieces
   - Embedded using sentence-transformers
   - Loaded into MilvusDB

### Monitor Progress

The UI displays:
- **Job Status**: pending → processing → completed/failed
- **Progress Bar**: Visual progress of file processing
- **Text Chunks**: Number of text chunks loaded to MilvusDB
- **Table Chunks**: Number of table chunks loaded
- **Errors**: Any errors encountered during processing

## Architecture

### Frontend Components

```
frontend/src/
├── components/upload/
│   ├── file-upload.tsx          # Base file upload component
│   └── pdf-upload-etl.tsx       # PDF ETL integration wrapper
├── lib/api/
│   └── ingestion.ts             # API client functions
└── app/ingest/upload/
    └── page.tsx                 # Upload page
```

### API Endpoints Used

- `POST /api/v1/ingest/pdfs` - Upload PDFs
- `GET /api/v1/ingest/status/{job_id}` - Get job status

### Data Flow

```
User Upload
    ↓
Frontend (PDFUploadWithETL)
    ↓
API Client (uploadPDFsForETL)
    ↓
Backend API (FastAPI)
    ↓
ETL Pipeline (pdf_etl_pipeline.py)
    ↓
MilvusDB (Vector Storage)
```

## Features

### ✅ Real-time Status Tracking
- Polls backend every 2 seconds for job updates
- Updates UI with current progress

### ✅ Error Handling
- Displays per-file errors
- Shows network/upload failures
- Graceful degradation

### ✅ File Validation
- Only accepts `.pdf` files
- Maximum 20 files per upload
- 50MB max file size
- Client-side validation before upload

### ✅ Visual Feedback
- File status icons (pending/processing/completed/failed)
- Animated progress bars
- Live statistics (text/table chunks)
- Color-coded status badges

## Troubleshooting

### `Upload failed with status 500`

- **Check**: Backend API is running on `http://localhost:8000`
- **Check**: MilvusDB is running and accessible
- **Check**: All ETL dependencies are installed

### `Failed to get job status`

- **Check**: Job ID is valid
- **Check**: Backend API is accessible
- **Solution**: The frontend polls for 2 minutes max, then times out

### `CORS errors`

- **Check**: Backend CORS is configured to allow frontend origin
- **Fix**: Update `api/main.py` CORS settings if needed

### `Table chunks show 0`

- **This is expected**: The encoding fix may still have issues with some PDFs
- **Tables are optional**: Text chunks are the primary data source
- **Check backend logs**: Look for table extraction warnings

## Development

### Run Tests

Backend:
```bash
cd apps
uv run python test_upload_pdfs.py data/pdfs/*.pdf
```

Frontend (manual testing):
1. Open `http://localhost:3000/ingest/upload`
2. Upload a sample PDF
3. Verify job status updates
4. Check MilvusDB for inserted chunks

### Debug Mode

Enable in browser DevTools:
```javascript
localStorage.setItem('debug', 'true')
```

Check network tab for API calls and responses.

## Next Steps

### Production Enhancements

1. **Authentication**: Add JWT/OAuth to API endpoints
2. **Rate Limiting**: Prevent abuse of upload endpoint
3. **File Storage**: Store uploaded PDFs (currently temp files are deleted)
4. **Job Persistence**: Use Redis/PostgreSQL instead of in-memory storage
5. **Webhooks**: Notify frontend when jobs complete (instead of polling)
6. **Batch Processing**: Queue system for large uploads (Celery/RQ)

### UI Enhancements

1. **Drag & drop everywhere**: Allow dropping files anywhere on upload page
2. **Resume uploads**: Handle interrupted uploads
3. **Download results**: Export extracted data as JSON/CSV
4. **History view**: Show past upload jobs
5. **Admin dashboard**: View all jobs, retry failed ones

## Related Files

- Backend API: `apps/api/main.py`
- ETL Pipeline: `apps/pdf_etl_pipeline.py`
- PDF Extractor: `apps/etl/processing/pdf_extractor.py`
- Frontend Component: `frontend/src/components/upload/pdf-upload-etl.tsx`
- API Client: `frontend/src/lib/api/ingestion.ts`
