-- PostgreSQL Initialization Script
-- Creates schema and base tables for market intelligence platform

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schema
CREATE SCHEMA IF NOT EXISTS market_intel;

-- Switch to schema
SET search_path TO market_intel, public;

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    company_code VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    ticker VARCHAR(10) NOT NULL UNIQUE,
    sector VARCHAR(100),
    listing_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_companies_ticker ON companies(ticker);
CREATE INDEX idx_companies_name ON companies USING GIN (company_name gin_trgm_ops);

-- Filings table
CREATE TABLE IF NOT EXISTS filings (
    filing_id VARCHAR(50) PRIMARY KEY,
    doc_id VARCHAR(100) NOT NULL UNIQUE,
    announcement_id VARCHAR(50),
    company_code VARCHAR(10) NOT NULL REFERENCES companies(company_code),
    announcement_date DATE NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    raw_text TEXT,
    source VARCHAR(50) DEFAULT 'bursa',
    source_url VARCHAR(500),
    confidence FLOAT DEFAULT 0.0,
    scraper_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_filings_doc_id ON filings(doc_id);
CREATE INDEX idx_filings_company_date ON filings(company_code, announcement_date);
CREATE INDEX idx_filings_type_date ON filings(document_type, announcement_date);
CREATE INDEX idx_filings_source ON filings(source);

-- Shareholding-specific chunks
CREATE TABLE IF NOT EXISTS shareholding_chunks (
    chunk_id VARCHAR(100) PRIMARY KEY,
    doc_id VARCHAR(100) NOT NULL REFERENCES filings(doc_id),
    content TEXT NOT NULL,
    chunk_order INTEGER,
    shareholder_name VARCHAR(255),
    company_code VARCHAR(10),
    ticker VARCHAR(10),
    current_percentage FLOAT,
    previous_percentage FLOAT,
    embedding_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shareholding_chunks_doc ON shareholding_chunks(doc_id);
CREATE INDEX idx_shareholding_chunks_company ON shareholding_chunks(company_code);
CREATE INDEX idx_shareholding_chunks_shareholder ON shareholding_chunks(shareholder_name);
CREATE INDEX idx_shareholding_chunks_ticker ON shareholding_chunks(ticker);
CREATE INDEX idx_shareholding_chunks_status ON shareholding_chunks(embedding_status);

-- Financial-specific chunks
CREATE TABLE IF NOT EXISTS financial_chunks (
    chunk_id VARCHAR(100) PRIMARY KEY,
    doc_id VARCHAR(100) NOT NULL REFERENCES filings(doc_id),
    content TEXT NOT NULL,
    chunk_order INTEGER,
    metric_type VARCHAR(100),
    period_covered VARCHAR(50),
    company_code VARCHAR(10),
    ticker VARCHAR(10),
    embedding_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_financial_chunks_doc ON financial_chunks(doc_id);
CREATE INDEX idx_financial_chunks_company ON financial_chunks(company_code);
CREATE INDEX idx_financial_chunks_metric ON financial_chunks(metric_type);
CREATE INDEX idx_financial_chunks_period ON financial_chunks(period_covered);
CREATE INDEX idx_financial_chunks_status ON financial_chunks(embedding_status);

-- Dividend-specific chunks
CREATE TABLE IF NOT EXISTS dividend_chunks (
    chunk_id VARCHAR(100) PRIMARY KEY,
    doc_id VARCHAR(100) NOT NULL REFERENCES filings(doc_id),
    content TEXT NOT NULL,
    chunk_order INTEGER,
    dividend_type VARCHAR(50),
    dps_value FLOAT,
    company_code VARCHAR(10),
    ticker VARCHAR(10),
    ex_date DATE,
    payment_date DATE,
    embedding_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dividend_chunks_doc ON dividend_chunks(doc_id);
CREATE INDEX idx_dividend_chunks_company ON dividend_chunks(company_code);
CREATE INDEX idx_dividend_chunks_type ON dividend_chunks(dividend_type);
CREATE INDEX idx_dividend_chunks_date ON dividend_chunks(ex_date);
CREATE INDEX idx_dividend_chunks_status ON dividend_chunks(embedding_status);

-- Financial Results (Structured tabular data from financial reports)
CREATE TABLE IF NOT EXISTS financial_results (
    result_id VARCHAR(100) PRIMARY KEY,
    doc_id VARCHAR(100) NOT NULL REFERENCES filings(doc_id),
    company_code VARCHAR(10),
    ticker VARCHAR(10),
    announcement_date DATE,
    period_ended DATE,
    quarter VARCHAR(20),
    financial_year_end VARCHAR(20),

    -- Key Financial Metrics (in MYR'000 unless specified)
    revenue NUMERIC,
    profit_before_tax NUMERIC,
    profit_for_period NUMERIC,
    profit_attributable_to_holders NUMERIC,

    -- Per Share Metrics
    eps NUMERIC,
    dividend_per_share NUMERIC,
    net_assets_per_share NUMERIC,

    -- Additional fields
    is_audited BOOLEAN DEFAULT FALSE,
    currency VARCHAR(10) DEFAULT 'MYR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_financial_results_doc ON financial_results(doc_id);
CREATE INDEX idx_financial_results_company ON financial_results(company_code);
CREATE INDEX idx_financial_results_ticker ON financial_results(ticker);
CREATE INDEX idx_financial_results_period ON financial_results(period_ended);
CREATE INDEX idx_financial_results_date ON financial_results(announcement_date);

-- Grant permissions (adjust user as needed)
GRANT CONNECT ON DATABASE market_intel TO postgres;
GRANT USAGE ON SCHEMA market_intel TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA market_intel TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA market_intel TO postgres;

-- Insert sample company data
INSERT INTO companies (company_code, company_name, ticker, sector) VALUES
    ('0177', 'GLICO HOLDINGS BHD', 'GLICO', 'Insurance'),
    ('1155', 'MAYBANK GROUP BHD', 'MAYBANK', 'Financial Services'),
    ('1818', 'BURSA MALAYSIA BERHAD', 'BURSA', 'Financial Infrastructure'),
    ('3824', 'TENAGA NASIONAL BHD', 'TENAGA', 'Utilities'),
    ('4677', 'AEON CO (M) BERHAD', 'AEON', 'Retail')
ON CONFLICT DO NOTHING;

-- Display success message
SELECT 'PostgreSQL initialization complete!' as status;
