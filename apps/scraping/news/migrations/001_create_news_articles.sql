-- Supabase Migration: News Articles Table
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS news_articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id TEXT UNIQUE NOT NULL,
  source TEXT NOT NULL,  -- 'theedge' or 'bernama'
  title TEXT NOT NULL,
  content TEXT,
  summary TEXT,
  url TEXT,
  published_date TIMESTAMP WITH TIME ZONE,
  category TEXT,
  companies_mentioned TEXT[],  -- Array for company filtering
  keywords TEXT[],
  sentiment_score FLOAT,       -- -1.0 to 1.0 (null until analyzed)
  sentiment_label TEXT,        -- 'positive', 'neutral', 'negative'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast company filtering (GIN index for array containment)
CREATE INDEX IF NOT EXISTS idx_news_companies ON news_articles USING GIN(companies_mentioned);

-- Index for source and date filtering
CREATE INDEX IF NOT EXISTS idx_news_source_date ON news_articles(source, published_date DESC);

-- Index for sentiment queries
CREATE INDEX IF NOT EXISTS idx_news_sentiment ON news_articles(sentiment_label, sentiment_score);

-- Enable Row Level Security
ALTER TABLE news_articles ENABLE ROW LEVEL SECURITY;

-- Policy: Public read access (anyone can SELECT)
CREATE POLICY "Public read access" ON news_articles
  FOR SELECT
  USING (true);

-- Policy: Service role can insert (for batch scraping)
CREATE POLICY "Service role can insert" ON news_articles
  FOR INSERT
  WITH CHECK (auth.role() = 'service_role');

-- Policy: Service role can update (for sentiment analysis)
CREATE POLICY "Service role can update" ON news_articles
  FOR UPDATE
  USING (auth.role() = 'service_role');

-- Policy: Service role can delete (for cleanup)
CREATE POLICY "Service role can delete" ON news_articles
  FOR DELETE
  USING (auth.role() = 'service_role');

-- Example queries for agent:
-- Get news by company: SELECT * FROM news_articles WHERE 'MAYBANK' = ANY(companies_mentioned) ORDER BY published_date DESC LIMIT 10;
-- Get recent negative news: SELECT * FROM news_articles WHERE sentiment_label = 'negative' ORDER BY published_date DESC LIMIT 5;
