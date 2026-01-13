# Fix Summary: API PDF Processing Error

## Error
```
TextChunker.chunk_text() got an unexpected keyword argument 'source_filename'
```

## Root Cause
The API route `pdf_ingestion.py` was calling the chunking methods with incorrect parameter names:
- Used `source_filename` instead of `filename`
- Called non-existent `chunker.chunk_tables()` method
- Missing required parameters like `company_name` and `doc_id`

## Solution
Updated `apps/api/routes/pdf_ingestion.py` to:

### 1. Fixed `chunk_text()` call
**Before:**
```python
text_chunks = chunker.chunk_text(
    text=pdf_content.text_content,
    source_filename=pdf_path.name  # ❌ Wrong parameter name
)
```

**After:**
```python
text_chunks = chunker.chunk_text(
    text=pdf_content.text_content,
    filename=pdf_path.name,         # ✅ Correct
    company_name=company_name,      # ✅ Added
    doc_id=doc_id                   # ✅ Added
)
```

### 2. Fixed table processing
**Before:**
```python
table_chunks = chunker.chunk_tables(  # ❌ Method doesn't exist
    tables=pdf_content.tables,
    source_filename=pdf_path.name
)
```

**After:**
```python
# Convert tables to text and generate embeddings manually
table_texts = []
for table_idx, table in enumerate(pdf_content.tables):
    table_text = "\n".join([" | ".join(str(cell).strip() for cell in row if cell) for row in table])
    table_texts.append(table_text)

# Generate embeddings
table_embeddings = embedding_gen.generate_batch(table_texts)

# Prepare table chunks dict for MilvusDB
table_chunks_data = [...]  # Proper structure
```

### 3. Fixed data structure
Now properly creates dict objects that match MilvusDB schema instead of raw chunk objects.

## Test Results
After the fix, the pipeline should successfully:
- ✅ Extract text from PDFs
- ✅ Chunk text into 500-char pieces
- ✅ Generate 384-dim embeddings
- ✅ Extract and process tables (if encoding allows)
- ✅ Insert into MilvusDB collections

## Files Modified
- `apps/api/routes/pdf_ingestion.py` - Fixed chunking method calls

## How to Test
```bash
# Start the API
cd apps
uv run python run_api.py

# Upload PDFs via frontend
# Navigate to: http://localhost:3000/ingest/upload
```

Expected output:
```
[Job job_XXXXX] ✓ Completed filename.pdf
[Job job_XXXXX] Processing complete: N text chunks, M table chunks
```
