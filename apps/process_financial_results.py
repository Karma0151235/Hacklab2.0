#!/usr/bin/env python3
"""
Direct processor for financial_result JSON files
Reads pre-processed ETL output format and extracts financial data to PostgreSQL
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from etl.parsing.financial_parser import FinancialResultsParser
from etl.db.postgres import PostgresStorage
from etl.logging_config import get_logger

logger = get_logger(__name__)

def process_financial_results_directory():
    """Process all financial_result JSON files and store in PostgreSQL"""

    base_path = Path(__file__).parent / "storage" / "raw" / "bursa" / "financial_result"

    if not base_path.exists():
        print(f"[ERROR] Directory not found: {base_path}")
        return False

    print("\n" + "="*80)
    print("FINANCIAL RESULTS PROCESSOR")
    print("="*80 + "\n")

    # Initialize services
    print("[*] Initializing services...")
    parser = FinancialResultsParser()
    # Use correct port for Docker - PostgreSQL is exposed on 5489
    postgres = PostgresStorage(connection_string='postgresql://postgres:postgres@localhost:5489/market_intel')

    if not postgres.health_check():
        print("[ERROR] PostgreSQL health check failed")
        return False

    print("[+] PostgreSQL connected")
    print("[*] Creating database tables...")
    postgres.create_tables()
    print("[+] Database tables ready\n")

    # Find all JSON files (date/file.json)
    json_files = sorted(base_path.glob("*/*.json"))
    print(f"[*] Found {len(json_files)} JSON files to process\n")

    if not json_files:
        print("[!] No JSON files found")
        return False

    processed = 0
    saved = 0
    errors = 0

    for idx, json_file in enumerate(json_files, 1):
        try:
            print(f"[{idx}/{len(json_files)}] Processing: {json_file.name}")

            # Read JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            document_object = data.get("document_object", {})
            structured_record = data.get("structured_record", {})

            if not document_object:
                print(f"   [!] No document_object found - skipping")
                errors += 1
                continue

            # Extract financial data
            print(f"   [*] Parsing financial metrics...")
            financial_data = parser.parse_financial_results(document_object)

            if not financial_data:
                print(f"   [!] Failed to extract financial data")
                errors += 1
                continue

            # Add doc_id for storage
            doc_id = document_object.get("doc_id")
            if not doc_id:
                doc_id = f"doc_{structured_record.get('announcement_id', 'unknown')}"

            financial_data['doc_id'] = doc_id

            # Ensure company code and ticker are set
            if not financial_data.get('company_code'):
                company_code = document_object.get("company_code", "").upper()
                # Truncate to 10 chars for DB column
                financial_data['company_code'] = (company_code[:10] if company_code else "")

            if not financial_data.get('ticker'):
                company_name = document_object.get("company_code", "")
                # Extract ticker from company name (first 4 letters of first word usually)
                if company_name:
                    words = company_name.upper().split()
                    financial_data['ticker'] = (words[0][:4] if words else "")[:10]

            print(f"   [*] Extracted: Revenue={financial_data.get('revenue')}, "
                  f"EPS={financial_data.get('eps')}, Dividend={financial_data.get('dividend_per_share')}")

            # Save to PostgreSQL
            if postgres.save_financial_results(financial_data, doc_id):
                print(f"   [+] Saved to financial_results table")
                saved += 1
            else:
                print(f"   [!] Failed to save to database")
                errors += 1

            processed += 1

        except Exception as e:
            print(f"   [ERROR] {str(e)}")
            errors += 1
            continue

    # Print summary
    print("\n" + "="*80)
    print("PROCESSING COMPLETE")
    print("="*80)
    print(f"Total processed: {processed}")
    print(f"Successfully saved: {saved}")
    print(f"Errors: {errors}")
    print("="*80 + "\n")

    # Verify by querying database
    if saved > 0:
        print("[*] Verifying data in financial_results table...\n")
        try:
            from sqlalchemy import text
            session = postgres.SessionLocal()
            result = session.execute(
                text("SELECT COUNT(*), company_code, COUNT(DISTINCT doc_id) FROM market_intel.financial_results GROUP BY company_code")
            )
            for row in result:
                print(f"   Company: {row[1]}, Records: {row[0]}, Documents: {row[2]}")
            session.close()
        except Exception as e:
            print(f"   [!] Verification query failed: {str(e)}")

    return True

if __name__ == "__main__":
    try:
        success = process_financial_results_directory()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
