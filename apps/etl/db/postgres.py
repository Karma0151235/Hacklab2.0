"""
PostgreSQL storage for ETL pipeline
"""

import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from etl.db.models import (
    Base, Company, Filing, ParsedField, ParsedTable, FinancialRatio,
    DocumentChunkVector, ShareholdingChange, FinancialResult,
    ShareholdingChunk, FinancialChunk, DividendChunk, CorporateActionChunk, MeetingChunk
)
from etl.models import StructuredRecord, DocumentObject
from etl.logging_config import get_logger

logger = get_logger(__name__)


class PostgresStorage:
    """PostgreSQL storage operations"""

    def __init__(self, connection_string: str = None):
        """
        Initialize PostgreSQL connection

        Args:
            connection_string: PostgreSQL URL (default from env)
        """
        if connection_string is None:
            connection_string = os.getenv(
                'DATABASE_URL',
                'postgresql://postgres:postgres@localhost:5432/market_intel'
            )

        self.connection_string = connection_string
        logger.info(f"Connecting to PostgreSQL: {connection_string.split('@')[1] if '@' in connection_string else 'localhost'}")

        try:
            self.engine = create_engine(connection_string, echo=False)
            self.SessionLocal = sessionmaker(bind=self.engine)
            logger.info("✅ PostgreSQL connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {str(e)}")
            raise

    def create_tables(self):
        """Create all tables"""
        try:
            logger.info("Creating PostgreSQL tables...")
            Base.metadata.create_all(self.engine)
            logger.info("✅ All tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise

    def save_filing(self, structured_record: StructuredRecord, document_object: DocumentObject) -> bool:
        """
        Save filing and related data to PostgreSQL

        Args:
            structured_record: StructuredRecord from ETL
            document_object: DocumentObject from ETL

        Returns:
            Success status
        """
        session = self.SessionLocal()

        try:
            # 1. Ensure company exists
            logger.debug(f"  └─ Saving company: {structured_record.company_code}")
            company = session.query(Company).filter_by(company_code=structured_record.company_code).first()

            if not company:
                company = Company(
                    company_code=structured_record.company_code,
                    company_name=document_object.metadata.get("company_name", ""),
                    ticker=document_object.ticker,
                )
                session.add(company)
                logger.debug(f"     └─ Created company: {company.ticker}")

            # 2. Save filing
            logger.debug(f"  └─ Saving filing: {structured_record.doc_id}")
            filing = Filing(
                filing_id=structured_record.doc_id,
                doc_id=structured_record.doc_id,
                announcement_id=structured_record.announcement_id,
                company_code=structured_record.company_code,
                announcement_date=structured_record.announcement_date,
                document_type=structured_record.document_type,
                title=structured_record.title,
                raw_text=structured_record.source_text[:5000],  # Limit to 5000 chars
                source=structured_record.source,
                source_url=document_object.metadata.get("source_url", ""),
                confidence=document_object.metadata.get("confidence", 0.0),
                scraper_version=document_object.metadata.get("scraper_version", ""),
            )
            session.add(filing)
            logger.debug(f"     └─ Saved filing: {filing.filing_id}")

            # 3. Save parsed fields
            logger.debug(f"  └─ Saving parsed fields: {len(structured_record.parsed_fields)} fields")
            for idx, (field_name, field_value) in enumerate(structured_record.parsed_fields.items()):
                field = ParsedField(
                    field_id=f"{structured_record.doc_id}_{field_name}",
                    filing_id=structured_record.doc_id,
                    field_name=field_name,
                    field_value=str(field_value),
                    field_type=type(field_value).__name__,
                )
                session.add(field)
            logger.debug(f"     └─ Saved {len(structured_record.parsed_fields)} fields")

            # 4. Save tables
            logger.debug(f"  └─ Saving tables: {len(document_object.tables)} tables")
            for idx, table in enumerate(document_object.tables):
                parsed_table = ParsedTable(
                    table_id=f"{structured_record.doc_id}_table_{idx}",
                    filing_id=structured_record.doc_id,
                    table_title=table.get("title", f"Table {idx}"),
                    table_data=table,
                    row_count=len(table.get("rows", [])),
                    col_count=len(table.get("headers", [])),
                )
                session.add(parsed_table)
            logger.debug(f"     └─ Saved {len(document_object.tables)} tables")

            # Commit transaction
            session.commit()
            logger.info(f"✅ Saved filing to PostgreSQL: {structured_record.doc_id}")
            return True

        except IntegrityError as e:
            session.rollback()
            logger.warning(f"Filing already exists: {structured_record.doc_id}")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save filing: {str(e)}")
            return False
        finally:
            session.close()

    def save_chunks(self, document_chunks: List, doc_id: str, document_type: str = "GENERAL_ANNOUNCEMENT") -> int:
        """
        Save document chunks to category-specific table based on document_type

        Routes to:
        - shareholding_chunks for SHAREHOLDING_NOTICE
        - financial_chunks for FINANCIAL_RESULTS
        - dividend_chunks for DIVIDEND_ANNOUNCEMENT
        - corporate_action_chunks for CORPORATE_ACTION
        - meeting_chunks for MEETING_NOTICE
        - document_chunks (generic) for others

        Args:
            document_chunks: List of DocumentChunk objects
            doc_id: Parent document ID
            document_type: Type of document (for routing)

        Returns:
            Number of chunks saved
        """
        if document_type == "SHAREHOLDING_NOTICE":
            return self._save_shareholding_chunks(document_chunks, doc_id)
        elif document_type == "FINANCIAL_RESULTS":
            return self._save_financial_chunks(document_chunks, doc_id)
        elif document_type == "DIVIDEND_ANNOUNCEMENT":
            return self._save_dividend_chunks(document_chunks, doc_id)
        elif document_type == "CORPORATE_ACTION":
            return self._save_corporate_action_chunks(document_chunks, doc_id)
        elif document_type == "MEETING_NOTICE":
            return self._save_meeting_chunks(document_chunks, doc_id)
        else:
            # Generic fallback for unknown types
            return self._save_generic_chunks(document_chunks, doc_id)

    def _save_shareholding_chunks(self, document_chunks: List, doc_id: str) -> int:
        """Save chunks to shareholding_chunks table with type-specific fields"""
        session = self.SessionLocal()
        saved_count = 0

        try:
            logger.debug(f"  └─ Saving {len(document_chunks)} shareholding chunks")
            for chunk in document_chunks:
                shareholding_chunk = ShareholdingChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=doc_id,
                    content=chunk.content,
                    chunk_order=chunk.chunk_order,
                    shareholder_name=chunk.metadata.get("shareholder_name") if chunk.metadata else None,
                    company_code=chunk.metadata.get("company_code") if chunk.metadata else None,
                    ticker=chunk.metadata.get("ticker") if chunk.metadata else None,
                    current_percentage=chunk.metadata.get("current_percentage") if chunk.metadata else None,
                    previous_percentage=chunk.metadata.get("previous_percentage") if chunk.metadata else None,
                    embedding_status="pending",
                )
                session.add(shareholding_chunk)
                saved_count += 1

            session.commit()
            logger.debug(f"     └─ Saved {saved_count} shareholding chunks")
            return saved_count

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save shareholding chunks: {str(e)}")
            return 0
        finally:
            session.close()

    def _save_financial_chunks(self, document_chunks: List, doc_id: str) -> int:
        """Save chunks to financial_chunks table with type-specific fields"""
        session = self.SessionLocal()
        saved_count = 0

        try:
            logger.debug(f"  └─ Saving {len(document_chunks)} financial chunks")
            for chunk in document_chunks:
                financial_chunk = FinancialChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=doc_id,
                    content=chunk.content,
                    chunk_order=chunk.chunk_order,
                    metric_type=chunk.metadata.get("metric_type") if chunk.metadata else None,
                    period_covered=chunk.metadata.get("period_covered") if chunk.metadata else None,
                    company_code=chunk.metadata.get("company_code") if chunk.metadata else None,
                    ticker=chunk.metadata.get("ticker") if chunk.metadata else None,
                    embedding_status="pending",
                )
                session.add(financial_chunk)
                saved_count += 1

            session.commit()
            logger.debug(f"     └─ Saved {saved_count} financial chunks")
            return saved_count

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save financial chunks: {str(e)}")
            return 0
        finally:
            session.close()

    def _save_dividend_chunks(self, document_chunks: List, doc_id: str) -> int:
        """Save chunks to dividend_chunks table with type-specific fields"""
        session = self.SessionLocal()
        saved_count = 0

        try:
            logger.debug(f"  └─ Saving {len(document_chunks)} dividend chunks")
            for chunk in document_chunks:
                dividend_chunk = DividendChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=doc_id,
                    content=chunk.content,
                    chunk_order=chunk.chunk_order,
                    dividend_type=chunk.metadata.get("dividend_type") if chunk.metadata else None,
                    dps_value=chunk.metadata.get("dps_value") if chunk.metadata else None,
                    company_code=chunk.metadata.get("company_code") if chunk.metadata else None,
                    ticker=chunk.metadata.get("ticker") if chunk.metadata else None,
                    ex_date=chunk.metadata.get("ex_date") if chunk.metadata else None,
                    payment_date=chunk.metadata.get("payment_date") if chunk.metadata else None,
                    embedding_status="pending",
                )
                session.add(dividend_chunk)
                saved_count += 1

            session.commit()
            logger.debug(f"     └─ Saved {saved_count} dividend chunks")
            return saved_count

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save dividend chunks: {str(e)}")
            return 0
        finally:
            session.close()

    def _save_corporate_action_chunks(self, document_chunks: List, doc_id: str) -> int:
        """Save chunks to corporate_action_chunks table with type-specific fields"""
        session = self.SessionLocal()
        saved_count = 0

        try:
            logger.debug(f"  └─ Saving {len(document_chunks)} corporate action chunks")
            for chunk in document_chunks:
                corporate_chunk = CorporateActionChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=doc_id,
                    content=chunk.content,
                    chunk_order=chunk.chunk_order,
                    action_type=chunk.metadata.get("action_type") if chunk.metadata else None,
                    ratio=chunk.metadata.get("ratio") if chunk.metadata else None,
                    company_code=chunk.metadata.get("company_code") if chunk.metadata else None,
                    ticker=chunk.metadata.get("ticker") if chunk.metadata else None,
                    effective_date=chunk.metadata.get("effective_date") if chunk.metadata else None,
                    embedding_status="pending",
                )
                session.add(corporate_chunk)
                saved_count += 1

            session.commit()
            logger.debug(f"     └─ Saved {saved_count} corporate action chunks")
            return saved_count

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save corporate action chunks: {str(e)}")
            return 0
        finally:
            session.close()

    def _save_meeting_chunks(self, document_chunks: List, doc_id: str) -> int:
        """Save chunks to meeting_chunks table with type-specific fields"""
        session = self.SessionLocal()
        saved_count = 0

        try:
            logger.debug(f"  └─ Saving {len(document_chunks)} meeting chunks")
            for chunk in document_chunks:
                meeting_chunk = MeetingChunk(
                    chunk_id=chunk.chunk_id,
                    doc_id=doc_id,
                    content=chunk.content,
                    chunk_order=chunk.chunk_order,
                    meeting_type=chunk.metadata.get("meeting_type") if chunk.metadata else None,
                    meeting_date=chunk.metadata.get("meeting_date") if chunk.metadata else None,
                    company_code=chunk.metadata.get("company_code") if chunk.metadata else None,
                    ticker=chunk.metadata.get("ticker") if chunk.metadata else None,
                    embedding_status="pending",
                )
                session.add(meeting_chunk)
                saved_count += 1

            session.commit()
            logger.debug(f"     └─ Saved {saved_count} meeting chunks")
            return saved_count

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save meeting chunks: {str(e)}")
            return 0
        finally:
            session.close()

    def _save_generic_chunks(self, document_chunks: List, doc_id: str) -> int:
        """Save chunks to generic document_chunks table (fallback)"""
        session = self.SessionLocal()
        saved_count = 0

        try:
            logger.debug(f"  └─ Saving {len(document_chunks)} generic chunks")
            for chunk in document_chunks:
                chunk_vector = DocumentChunkVector(
                    chunk_id=chunk.chunk_id,
                    doc_id=doc_id,
                    content=chunk.content,
                    chunk_order=chunk.chunk_order,
                    metadata=chunk.metadata,
                    embedding_status="pending",
                )
                session.add(chunk_vector)
                saved_count += 1

            session.commit()
            logger.debug(f"     └─ Saved {saved_count} generic chunks")
            return saved_count

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save generic chunks: {str(e)}")
            return 0
        finally:
            session.close()

    def get_filing(self, doc_id: str) -> Optional[Filing]:
        """Get filing by doc_id"""
        session = self.SessionLocal()
        try:
            return session.query(Filing).filter_by(doc_id=doc_id).first()
        finally:
            session.close()

    def get_filings_by_company(self, company_code: str) -> List[Filing]:
        """Get all filings for a company"""
        session = self.SessionLocal()
        try:
            return session.query(Filing).filter_by(company_code=company_code).all()
        finally:
            session.close()

    def get_filings_by_date_range(self, start_date, end_date) -> List[Filing]:
        """Get filings within date range"""
        session = self.SessionLocal()
        try:
            return session.query(Filing).filter(
                Filing.announcement_date.between(start_date, end_date)
            ).all()
        finally:
            session.close()

    def count_filings(self) -> int:
        """Get total number of filings"""
        session = self.SessionLocal()
        try:
            return session.query(Filing).count()
        finally:
            session.close()

    def count_pending_chunks(self) -> int:
        """Get number of chunks pending embedding"""
        session = self.SessionLocal()
        try:
            return session.query(DocumentChunkVector).filter_by(embedding_status="pending").count()
        finally:
            session.close()

    def get_pending_chunks(self, batch_size: int = 100) -> List[DocumentChunkVector]:
        """Get batch of pending chunks for embedding"""
        session = self.SessionLocal()
        try:
            return session.query(DocumentChunkVector).filter_by(
                embedding_status="pending"
            ).limit(batch_size).all()
        finally:
            session.close()

    def update_chunk_embedding_status(self, chunk_id: str, status: str):
        """Update chunk embedding status"""
        session = self.SessionLocal()
        try:
            chunk = session.query(DocumentChunkVector).filter_by(chunk_id=chunk_id).first()
            if chunk:
                chunk.embedding_status = status
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update chunk status: {str(e)}")
        finally:
            session.close()

    def save_shareholding_change(self, structured_record: StructuredRecord, parsed_fields: dict) -> bool:
        """
        Save shareholding change for SHAREHOLDING_NOTICE documents

        Args:
            structured_record: StructuredRecord from ETL
            parsed_fields: Extracted shareholding fields

        Returns:
            Success status
        """
        session = self.SessionLocal()

        try:
            logger.debug(f"  └─ Saving shareholding change for: {parsed_fields.get('shareholder', 'Unknown')}")

            shareholding = ShareholdingChange(
                change_id=f"{structured_record.doc_id}_shareholding",
                filing_id=structured_record.doc_id,
                company_code=structured_record.company_code,
                ticker=parsed_fields.get("ticker", ""),
                shareholder_name=parsed_fields.get("shareholder", ""),
                previous_percentage=parsed_fields.get("previous_percentage"),
                current_percentage=float(parsed_fields.get("current_percentage", 0)),
                shares_before=str(parsed_fields.get("shares_before", "")),
                shares_acquired=str(parsed_fields.get("shares_acquired", "")),
                shares_after=str(parsed_fields.get("shares_after", "")),
                transaction_type=parsed_fields.get("transaction_type", ""),
                nature_of_interest=parsed_fields.get("nature_of_interest", ""),
                change_date=parsed_fields.get("change_date", structured_record.announcement_date),
                announcement_date=structured_record.announcement_date,
            )
            session.add(shareholding)
            session.commit()
            logger.debug(f"     └─ Saved shareholding: {shareholding.shareholder_name} ({shareholding.current_percentage}%)")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save shareholding change: {str(e)}")
            return False
        finally:
            session.close()

    def save_financial_results(self, result_data: dict, doc_id: str) -> bool:
        """Save structured financial results"""
        if not result_data:
            logger.debug("No financial results data to save")
            return False

        session = self.SessionLocal()

        try:
            import uuid
            result_id = f"fin_{uuid.uuid4().hex[:12]}"

            # Truncate string fields to match column widths
            company_code = result_data.get("company_code")
            ticker = result_data.get("ticker")

            financial_result = FinancialResult(
                result_id=result_id,
                doc_id=doc_id,
                company_code=str(company_code)[:10] if company_code else None,
                ticker=str(ticker)[:10] if ticker else None,
                announcement_date=result_data.get("announcement_date"),
                period_ended=result_data.get("period_ended"),
                quarter=result_data.get("quarter"),
                financial_year_end=result_data.get("financial_year_end"),
                revenue=result_data.get("revenue"),
                profit_before_tax=result_data.get("profit_before_tax"),
                profit_for_period=result_data.get("profit_for_period"),
                profit_attributable_to_holders=result_data.get("profit_attributable_to_holders"),
                eps=result_data.get("eps"),
                dividend_per_share=result_data.get("dividend_per_share"),
                net_assets_per_share=result_data.get("net_assets_per_share"),
                is_audited=result_data.get("is_audited", False),
                currency=result_data.get("currency", "MYR"),
            )

            session.add(financial_result)
            session.commit()
            logger.debug(f"     └─ Saved financial result: {result_data.get('company_code')} {result_data.get('quarter')}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save financial result: {str(e)}")
            return False
        finally:
            session.close()

    def health_check(self) -> bool:
        """Check PostgreSQL connection"""
        try:
            from sqlalchemy import text
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {str(e)}")
            return False
