"""
Test client for PDF upload API
Usage: python test_upload_pdfs.py <pdf_file1> <pdf_file2> ...
"""

import sys
import requests
import time
from pathlib import Path

API_BASE_URL = "http://localhost:8000/api/v1"


def upload_pdfs(pdf_files: list[Path]):
    """Upload PDFs to the API"""
    print(f"\n📤 Uploading {len(pdf_files)} PDF files...")
    
    # Prepare files for upload
    files = []
    for pdf_path in pdf_files:
        if not pdf_path.exists():
            print(f"❌ File not found: {pdf_path}")
            continue
        files.append(('files', (pdf_path.name, open(pdf_path, 'rb'), 'application/pdf')))
    
    if not files:
        print("❌ No valid files to upload")
        return None
    
    # Upload files
    try:
        response = requests.post(f"{API_BASE_URL}/ingest/pdfs", files=files)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"   Job ID: {result['job_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Files: {result['files_received']}")
        print(f"   Filenames: {', '.join(result['filenames'])}")
        
        return result['job_id']
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Upload failed: {str(e)}")
        return None
    
    finally:
        # Close file handles
        for _, (_, file_obj, _) in files:
            file_obj.close()


def check_status(job_id: str, poll_interval: int = 2):
    """Check job status and poll until complete"""
    print(f"\n📊 Checking status for job: {job_id}")
    
    while True:
        try:
            response = requests.get(f"{API_BASE_URL}/ingest/status/{job_id}")
            response.raise_for_status()
            
            status = response.json()
            
            print(f"\r   Status: {status['status']} | "
                  f"Progress: {status['processed_files']}/{status['total_files']} files | "
                  f"Text chunks: {status['text_chunks_loaded']} | "
                  f"Table chunks: {status['table_chunks_loaded']}", end='')
            
            if status['errors']:
                print(f"\n   ⚠️  Errors: {len(status['errors'])}")
                for error in status['errors']:
                    print(f"      - {error}")
            
            if status['status'] in ['completed', 'failed']:
                print()  # New line
                break
            
            time.sleep(poll_interval)
        
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Status check failed: {str(e)}")
            break
    
    return status


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_upload_pdfs.py <pdf_file1> <pdf_file2> ...")
        print("\nExample:")
        print("  python test_upload_pdfs.py data/pdfs/*.pdf")
        sys.exit(1)
    
    # Get PDF files from arguments
    pdf_files = [Path(arg) for arg in sys.argv[1:]]
    
    print("=" * 80)
    print("PDF UPLOAD API TEST CLIENT")
    print("=" * 80)
    
    # Upload PDFs
    job_id = upload_pdfs(pdf_files)
    
    if not job_id:
        print("\n❌ Upload failed. Exiting.")
        sys.exit(1)
    
    # Poll for status
    final_status = check_status(job_id)
    
    # Print final results
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Job ID: {final_status['job_id']}")
    print(f"Status: {final_status['status']}")
    print(f"Files processed: {final_status['processed_files']}/{final_status['total_files']}")
    print(f"Text chunks loaded: {final_status['text_chunks_loaded']}")
    print(f"Table chunks loaded: {final_status['table_chunks_loaded']}")
    
    if final_status['errors']:
        print(f"\n⚠️  Errors ({len(final_status['errors'])}):")
        for error in final_status['errors']:
            print(f"  - {error}")
    
    print("=" * 80)
    
    # Exit code based on status
    sys.exit(0 if final_status['status'] == 'completed' else 1)


if __name__ == "__main__":
    main()
