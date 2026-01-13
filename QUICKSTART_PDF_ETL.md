# Quick Start: PDF ETL Pipeline

## 🚀 Getting Started

### Step 1: Create Environment File

Create `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Step 2: Start Backend API

Terminal 1:
```bash
cd apps
uv run python run_api.py
```

✅ API running at: `http://localhost:8000`  
📖 API docs at: `http://localhost:8000/docs`

### Step 3: Start Frontend

Terminal 2:
```bash
cd frontend
pnpm run dev
```

✅ Frontend running at: `http://localhost:3000`

### Step 4: Upload PDFs

1. Open: `http://localhost:3000/ingest/upload`
2. Drag & drop PDFs or click "Browse Files"
3. Click "Start ETL Pipeline"
4. Watch real-time progress!

## 📊 What Gets Processed

Each PDF goes through:
1. **Extract**: Text extraction with pdfplumber, tables with tabula-py
2. **Transform**: Text chunking (500 chars), vector embeddings (384-dim)
3. **Load**: Insert into MilvusDB collections

## 🎯 Features

- ✅ Multi-file upload (up to 20 PDFs, 50MB each)
- ✅ Real-time progress tracking
- ✅ Background processing with job IDs
- ✅ Error handling per file
- ✅ Vector embedding generation
- ✅ MilvusDB integration

## 📝 Example API Usage

### Using curl:
```bash
curl -X POST "http://localhost:8000/api/v1/ingest/pdfs" \
  -F "files=@report1.pdf" \
  -F "files=@report2.pdf"
```

### Using Python:
```python
from frontend.src.lib.api.ingestion import uploadPDFsForETL

files = [open('report1.pdf', 'rb'), open('report2.pdf', 'rb')]
response = await uploadPDFsForETL(files)
print(f"Job ID: {response['job_id']}")
```

## 🔍 Verify Data

Check MilvusDB has data:
```python
from etl.db.milvus_pdf_manager import MilvusPDFManager

db = MilvusPDFManager()
print(f"Text chunks: {db.text_collection.num_entities}")
print(f"Table chunks: {db.table_collection.num_entities}")
```

## 💡 Tips

- **Check logs**: Backend shows detailed ETL progress
- **Monitor MilvusDB**: Use Attu UI at `http://localhost:8000` (if installed)
- **Table extraction**: May fail with encoding issues (normal, working on fix)
- **Job tracking**: Job IDs are returned immediately, processing is async

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend won't start | Check MilvusDB is running |
| Upload fails | Verify backend API is accessible |
| No progress updates | Check browser console for CORS errors |
| Table chunks = 0 | Expected, tables extraction has encoding issues |

## 📚 More Info

See `frontend/PDF_ETL_INTEGRATION.md` for detailed documentation.
