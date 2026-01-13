#!/usr/bin/env python3
"""
PDF Processing Pipeline - Extract financial data from PDF reports
Separates text (for embeddings) and tables (for structured storage)
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from etl.processing.pdf_extractor import PDFExtractor
from etl.parsing.pdf_financial_extractor import PDFFinancialExtractor
from etl.db.postgres import PostgresStorage
from etl.chunking.chunker import TextChunker
from etl.logging_config import get_logger

logger = get_logger(__name__)


class PDFPipeline:
    """PDF to Financial Data Pipeline"""

    def __init__(self):
        self.pdf_dir = Path(__file__).parent / "storage" / "raw" / "pdfs"
        self.output_dir = Path(__file__).parent / "storage" / "processed" / "pdf_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.pdf_extractor = PDFExtractor()
        self.financial_extractor = PDFFinancialExtractor()
        self.text_chunker = TextChunker()

        # Database connection (use correct port for Docker)
        self.postgres = PostgresStorage(
            connection_string='postgresql://postgres:postgres@localhost:5489/market_intel'
        )

        self.processed_count = 0
        self.financial_records_saved = 0
        self.chunks_saved = 0

    def run(self) -> bool:
        """Run the PDF processing pipeline"""
        print("\n" + "="*80)
        print("PDF FINANCIAL DATA EXTRACTION PIPELINE")
        print("="*80 + "\n")

        if not self.pdf_dir.exists():
            print(f"[ERROR] PDF directory not found: {self.pdf_dir}")
            return False

        # Find all PDF files
        pdf_files = sorted(self.pdf_dir.glob("*.pdf"))
        print(f"[*] Found {len(pdf_files)} PDF files\n")

        if not pdf_files:
            print("[!] No PDF files found")
            return False

        # Check database connection
        print("[*] Checking database connection...")
        if not self.postgres.health_check():
            print("[ERROR] PostgreSQL health check failed")
            return False

        print("[*] Creating database tables...")
        self.postgres.create_tables()
        print("[+] Database ready\n")

        # Process each PDF
        for idx, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{idx}/{len(pdf_files)}] Processing: {pdf_file.name}")
            self._process_pdf(pdf_file)

        # Print summary
        print("\n" + "="*80)
        print("PIPELINE COMPLETE")
        print("="*80)
        print(f"PDF files processed:        {self.processed_count}")
        print(f"Financial records saved:    {self.financial_records_saved}")
        print(f"Text chunks saved:          {self.chunks_saved}")
        print("="*80 + "\n")

        return True

    def _process_pdf(self, pdf_path: Path) -> None:
        """Process a single PDF file"""
        try:
            # Extract content from PDF
            print(f"   [*] Extracting PDF content...")
            content = self.pdf_extractor.extract_from_file(pdf_path)

            if not content:
                print(f"   [!] Failed to extract PDF content")
                return

            print(f"   [+] Extracted: {len(content.text_content)} chars, {len(content.tables)} tables")

            # Extract financial metrics
            print(f"   [*] Parsing financial metrics...")
            financial_data = self.financial_extractor.extract_financial_data(
                content.tables,
                content.text_content,
                pdf_path.name
            )

            if not financial_data:
                print(f"   [!] Failed to extract financial data")
                return

            # Create filing record first (required for FK constraint)
            doc_id = f"pdf_{pdf_path.stem}_{datetime.now().timestamp()}"
            print(f"   [*] Creating filing record...")

            if self._create_filing_record(doc_id, pdf_path.name, financial_data):
                print(f"   [+] Created filing record")

                # Save financial results to PostgreSQL
                print(f"   [*] Saving financial results to PostgreSQL...")
                if self._save_financial_results(financial_data, doc_id):
                    print(f"   [+] Saved financial record")
                    self.financial_records_saved += 1
                else:
                    print(f"   [!] Failed to save financial record")
            else:
                print(f"   [!] Failed to create filing record")
                return

            # Chunk text for embeddings
            print(f"   [*] Chunking text for embeddings...")
            chunks = self.text_chunker.chunk_text(
                content.text_content,
                doc_id=doc_id
            )

            if chunks:
                print(f"   [+] Created {len(chunks)} text chunks")
                # Store chunks metadata (actual embeddings done separately)
                for chunk in chunks:
                    chunk['source'] = 'pdf'
                    chunk['source_file'] = pdf_path.name
                    chunk['document_type'] = 'FINANCIAL_RESULTS'
                    chunk['metadata_flags'] = {
                        'is_text': True,
                        'has_tables': len(content.tables) > 0,
                        'table_count': len(content.tables),
                    }
                self.chunks_saved += len(chunks)
            else:
                print(f"   [!] No chunks created from text")

            # Save processed output
            self._save_output(pdf_path.stem, content, financial_data, chunks)

            self.processed_count += 1

        except Exception as e:
            print(f"   [ERROR] {str(e)}")

    def _create_filing_record(self, doc_id: str, filename: str, financial_data: dict) -> bool:
        """Create a filing record in PostgreSQL (required for FK constraint)"""
        session = None
        try:
            import uuid
            from etl.db.models import Filing, Company

            if not financial_data:
                return False

            session = self.postgres.SessionLocal()

            # Get or create company
            company_code = str(financial_data.get('company_code') or 'PDF')[:10]
            company_name = str(financial_data.get('company_name') or filename)[:255]
            ticker = str(financial_data.get('ticker') or company_code)[:10]

            company = session.query(Company).filter_by(company_code=company_code).first()
            if not company:
                company = Company(
                    company_code=company_code,
                    company_name=company_name,
                    ticker=ticker,
                )
                session.add(company)
                session.flush()

            # Create filing record with unique filing_id
            filing_id = f"filing_{uuid.uuid4().hex[:12]}"
            filing = Filing(
                filing_id=filing_id,
                doc_id=doc_id,
                announcement_id=None,
                company_code=company_code,
                announcement_date=datetime.now().date(),
                document_type='FINANCIAL_RESULTS',
                title=filename[:500],
                raw_text='PDF financial report',
                source='pdf',
                source_url=None,
                confidence=0.8,
                scraper_version='pdf_extractor_v1',
            )
            session.add(filing)
            session.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to create filing record: {str(e)}")
            if session:
                try:
                    session.rollback()
                except:
                    pass
            return False
        finally:
            if session:
                try:
                    session.close()
                except:
                    pass

    def _save_financial_results(self, financial_data: dict, doc_id: str) -> bool:
        """Save financial results to PostgreSQL"""
        try:
            # Prepare data for storage (truncate long fields)
            result_data = {
                'doc_id': doc_id[:100],
                'company_code': str(financial_data.get('company_code', ''))[:10],
                'company_name': str(financial_data.get('company_name', ''))[:255],
                'ticker': str(financial_data.get('ticker', ''))[:10],
                'announcement_date': datetime.now().date(),
                'period_ended': financial_data.get('period_ended'),
                'quarter': str(financial_data.get('quarter', ''))[:20],
                'financial_year_end': str(financial_data.get('financial_year_end', ''))[:20],
                'is_audited': financial_data.get('is_audited', False),
                'currency': 'MYR',
            }

            # Add extracted metrics
            metrics = financial_data.get('metrics', {})
            for metric_key in ['revenue', 'profit_before_tax', 'profit_for_period',
                              'profit_attributable_to_holders', 'eps', 'dividend_per_share',
                              'net_assets_per_share']:
                result_data[metric_key] = metrics.get(metric_key)

            return self.postgres.save_financial_results(result_data, doc_id)

        except Exception as e:
            logger.error(f"Failed to save financial results: {str(e)}")
            return False

    def _save_output(self, filename_stem: str, content, financial_data: dict, chunks: list) -> None:
        """Save extracted data to JSON for verification"""
        try:
            output = {
                'filename': filename_stem,
                'extracted_at': datetime.now().isoformat(),
                'pages': content.pages,
                'tables_count': len(content.tables),
                'chunks_count': len(chunks),
                'financial_metrics': financial_data.get('metrics', {}),
                'company_info': {
                    'company_name': financial_data.get('company_name'),
                    'ticker': financial_data.get('ticker'),
                    'is_audited': financial_data.get('is_audited'),
                },
                'period_info': {
                    'period_ended': financial_data.get('period_ended'),
                    'quarter': financial_data.get('quarter'),
                    'financial_year_end': financial_data.get('financial_year_end'),
                },
            }

            output_file = self.output_dir / f"{filename_stem}_output.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, default=str)

        except Exception as e:
            logger.warning(f"Failed to save output JSON: {str(e)}")


if __name__ == "__main__":
    try:
        pipeline = PDFPipeline()
        success = pipeline.run()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
