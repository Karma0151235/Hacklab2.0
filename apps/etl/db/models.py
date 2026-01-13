"""
SQLAlchemy models for PostgreSQL
"""

from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, Integer, ForeignKey, JSON, Date, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Company(Base):
    """Company master data"""
    __tablename__ = "companies"

    company_code = Column(String(10), primary_key=True)
    company_name = Column(String(255), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, unique=True, index=True)
    sector = Column(String(100))
    listing_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    filings = relationship("Filing", back_populates="company")
    ratios = relationship("FinancialRatio", back_populates="company")

    def __repr__(self):
        return f"<Company {self.ticker} ({self.company_code})>"


class Filing(Base):
    """Document filing/announcement"""
    __tablename__ = "filings"

    filing_id = Column(String(50), primary_key=True, index=True)
    doc_id = Column(String(100), nullable=False, unique=True, index=True)
    announcement_id = Column(String(50))
    company_code = Column(String(10), ForeignKey("companies.company_code"), nullable=False, index=True)
    announcement_date = Column(Date, nullable=False, index=True)
    document_type = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    raw_text = Column(Text)
    source = Column(String(50), default="bursa", index=True)
    source_url = Column(String(500))
    confidence = Column(Float, default=0.0)
    scraper_version = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="filings")
    parsed_fields = relationship("ParsedField", back_populates="filing", cascade="all, delete-orphan")
    tables = relationship("ParsedTable", back_populates="filing", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_filing_company_date', 'company_code', 'announcement_date'),
        Index('idx_filing_type_date', 'document_type', 'announcement_date'),
    )

    def __repr__(self):
        return f"<Filing {self.doc_id}>"


class ParsedField(Base):
    """Extracted structured fields"""
    __tablename__ = "parsed_fields"

    field_id = Column(String(100), primary_key=True, index=True)
    filing_id = Column(String(50), ForeignKey("filings.filing_id"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    field_value = Column(Text)
    field_type = Column(String(50))  # string, float, date, etc
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    filing = relationship("Filing", back_populates="parsed_fields")

    def __repr__(self):
        return f"<ParsedField {self.field_name}={self.field_value}>"


class ParsedTable(Base):
    """Normalized tables from filings"""
    __tablename__ = "parsed_tables"

    table_id = Column(String(100), primary_key=True, index=True)
    filing_id = Column(String(50), ForeignKey("filings.filing_id"), nullable=False, index=True)
    table_title = Column(String(255))
    table_data = Column(JSON)  # Store table as JSON
    row_count = Column(Integer)
    col_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    filing = relationship("Filing", back_populates="tables")

    def __repr__(self):
        return f"<ParsedTable {self.table_title}>"


class FinancialRatio(Base):
    """Calculated financial ratios"""
    __tablename__ = "financial_ratios"

    ratio_id = Column(String(100), primary_key=True, index=True)
    company_code = Column(String(10), ForeignKey("companies.company_code"), nullable=False, index=True)
    filing_id = Column(String(50), ForeignKey("filings.filing_id"))
    statement_date = Column(Date, nullable=False, index=True)
    ratio_name = Column(String(100), nullable=False, index=True)
    ratio_value = Column(Float)
    ratio_unit = Column(String(50))  # %, times, etc
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="ratios")

    __table_args__ = (
        Index('idx_ratio_company_date', 'company_code', 'statement_date'),
    )

    def __repr__(self):
        return f"<FinancialRatio {self.ratio_name}={self.ratio_value}>"


class DocumentChunkVector(Base):
    """Generic chunks with vector embeddings for RAG (fallback)"""
    __tablename__ = "document_chunks"

    chunk_id = Column(String(100), primary_key=True, index=True)
    doc_id = Column(String(100), ForeignKey("filings.doc_id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_order = Column(Integer)
    chunk_metadata = Column(JSON)
    embedding_status = Column(String(20), default="pending")  # pending, generated, stored
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<DocumentChunk {self.chunk_id}>"


class ShareholdingChunk(Base):
    """Chunks from shareholding notices with type-specific fields"""
    __tablename__ = "shareholding_chunks"

    chunk_id = Column(String(100), primary_key=True, index=True)
    doc_id = Column(String(100), ForeignKey("filings.doc_id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_order = Column(Integer)

    # Type-specific fields
    shareholder_name = Column(String(255), index=True)
    company_code = Column(String(10), index=True)
    ticker = Column(String(10), index=True)
    current_percentage = Column(Float)
    previous_percentage = Column(Float)

    embedding_status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_shareholding_chunks_company', 'company_code'),
        Index('idx_shareholding_chunks_shareholder', 'shareholder_name'),
        Index('idx_shareholding_chunks_ticker', 'ticker'),
        Index('idx_shareholding_chunks_status', 'embedding_status'),
    )

    def __repr__(self):
        return f"<ShareholdingChunk {self.shareholder_name} - {self.current_percentage}%>"


class FinancialChunk(Base):
    """Chunks from financial reports with type-specific fields"""
    __tablename__ = "financial_chunks"

    chunk_id = Column(String(100), primary_key=True, index=True)
    doc_id = Column(String(100), ForeignKey("filings.doc_id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_order = Column(Integer)

    # Type-specific fields
    metric_type = Column(String(100), index=True)  # Revenue, EPS, Profit, ROE, etc
    period_covered = Column(String(50), index=True)  # Q1 2025, FY 2024, etc
    company_code = Column(String(10), index=True)
    ticker = Column(String(10), index=True)

    embedding_status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_financial_chunks_company', 'company_code'),
        Index('idx_financial_chunks_metric', 'metric_type'),
        Index('idx_financial_chunks_period', 'period_covered'),
        Index('idx_financial_chunks_status', 'embedding_status'),
    )

    def __repr__(self):
        return f"<FinancialChunk {self.company_code} - {self.metric_type}>"


class DividendChunk(Base):
    """Chunks from dividend announcements with type-specific fields"""
    __tablename__ = "dividend_chunks"

    chunk_id = Column(String(100), primary_key=True, index=True)
    doc_id = Column(String(100), ForeignKey("filings.doc_id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_order = Column(Integer)

    # Type-specific fields
    dividend_type = Column(String(50), index=True)  # interim, final, special
    dps_value = Column(Float)  # Dividend per share
    company_code = Column(String(10), index=True)
    ticker = Column(String(10), index=True)
    ex_date = Column(Date)
    payment_date = Column(Date)

    embedding_status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_dividend_chunks_company', 'company_code'),
        Index('idx_dividend_chunks_type', 'dividend_type'),
        Index('idx_dividend_chunks_date', 'ex_date'),
        Index('idx_dividend_chunks_status', 'embedding_status'),
    )

    def __repr__(self):
        return f"<DividendChunk {self.company_code} - {self.dps_value}>"


class CorporateActionChunk(Base):
    """Chunks from corporate actions with type-specific fields"""
    __tablename__ = "corporate_action_chunks"

    chunk_id = Column(String(100), primary_key=True, index=True)
    doc_id = Column(String(100), ForeignKey("filings.doc_id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_order = Column(Integer)

    # Type-specific fields
    action_type = Column(String(50), index=True)  # bonus, rights, split, consolidation
    ratio = Column(String(20))  # 1:2, 2:1, etc
    company_code = Column(String(10), index=True)
    ticker = Column(String(10), index=True)
    effective_date = Column(Date)

    embedding_status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_corporate_chunks_company', 'company_code'),
        Index('idx_corporate_chunks_action', 'action_type'),
        Index('idx_corporate_chunks_date', 'effective_date'),
        Index('idx_corporate_chunks_status', 'embedding_status'),
    )

    def __repr__(self):
        return f"<CorporateActionChunk {self.company_code} - {self.action_type}>"


class MeetingChunk(Base):
    """Chunks from meeting notices with type-specific fields"""
    __tablename__ = "meeting_chunks"

    chunk_id = Column(String(100), primary_key=True, index=True)
    doc_id = Column(String(100), ForeignKey("filings.doc_id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_order = Column(Integer)

    # Type-specific fields
    meeting_type = Column(String(50), index=True)  # AGM, EGM, Special Meeting, etc
    meeting_date = Column(Date, index=True)
    company_code = Column(String(10), index=True)
    ticker = Column(String(10), index=True)

    embedding_status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_meeting_chunks_company', 'company_code'),
        Index('idx_meeting_chunks_type', 'meeting_type'),
        Index('idx_meeting_chunks_date', 'meeting_date'),
        Index('idx_meeting_chunks_status', 'embedding_status'),
    )

    def __repr__(self):
        return f"<MeetingChunk {self.company_code} - {self.meeting_type}>"


class ShareholdingChange(Base):
    """Shareholding changes extracted from announcements"""
    __tablename__ = "shareholding_changes"

    change_id = Column(String(100), primary_key=True, index=True)
    filing_id = Column(String(50), ForeignKey("filings.filing_id"), nullable=False, index=True)
    company_code = Column(String(10), ForeignKey("companies.company_code"), nullable=False, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    shareholder_name = Column(String(255), nullable=False, index=True)
    previous_percentage = Column(Float)  # Percentage held before change
    current_percentage = Column(Float, nullable=False, index=True)
    shares_before = Column(String(50))  # Number of shares before (stored as string for large numbers)
    shares_acquired = Column(String(50))
    shares_after = Column(String(50))
    transaction_type = Column(String(50))  # Acquired, Disposed, etc
    nature_of_interest = Column(String(100))  # Direct, Indirect, etc
    change_date = Column(Date, nullable=False, index=True)
    announcement_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    filing = relationship("Filing", foreign_keys=[filing_id])
    company = relationship("Company", foreign_keys=[company_code])

    __table_args__ = (
        Index('idx_shareholding_company_date', 'company_code', 'change_date'),
        Index('idx_shareholding_shareholder', 'shareholder_name', 'company_code'),
        Index('idx_shareholding_percentage', 'company_code', 'current_percentage'),
    )

    def __repr__(self):
        return f"<ShareholdingChange {self.shareholder_name} {self.ticker} {self.current_percentage}%>"


class FinancialResult(Base):
    """Structured financial results from financial reports"""
    __tablename__ = "financial_results"

    result_id = Column(String(100), primary_key=True, index=True)
    doc_id = Column(String(100), ForeignKey("filings.doc_id"), nullable=False, index=True)
    company_code = Column(String(10), index=True)
    ticker = Column(String(10), index=True)
    announcement_date = Column(Date, index=True)
    period_ended = Column(Date, index=True)
    quarter = Column(String(20))  # e.g., "1 Qtr", "Q1 2025"
    financial_year_end = Column(String(20))  # e.g., "31 Dec 2025"

    # Key Financial Metrics (in MYR'000 unless specified)
    revenue = Column(Float)
    profit_before_tax = Column(Float)
    profit_for_period = Column(Float)
    profit_attributable_to_holders = Column(Float)

    # Per Share Metrics
    eps = Column(Float)  # Earnings per share
    dividend_per_share = Column(Float)
    net_assets_per_share = Column(Float)

    # Additional fields
    is_audited = Column(Boolean, default=False)
    currency = Column(String(10), default="MYR")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_financial_results_company', 'company_code'),
        Index('idx_financial_results_ticker', 'ticker'),
        Index('idx_financial_results_period', 'period_ended'),
        Index('idx_financial_results_date', 'announcement_date'),
    )

    def __repr__(self):
        return f"<FinancialResult {self.company_code} {self.quarter} - Revenue: {self.revenue}>"


# Create indexes
def create_indexes():
    """Create additional indexes for performance"""
    pass
