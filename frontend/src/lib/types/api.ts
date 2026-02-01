// API Response Types for Financial Intelligence Dashboard

export interface Company {
  company_code: string
  company_name: string
  ticker: string
  sector: string
  market_cap?: number
  filings_count: number
  latest_filing_date?: string
  alert_count: number
  financial_health_score?: number
}

export interface Filing {
  filing_id: string
  company_code: string
  company_name: string
  announcement_date: string
  document_type: string
  title: string
  summary?: string
  pdf_urls: string[]
  sentiment?: 'positive' | 'neutral' | 'negative'
  tables_count: number
  keywords: string[]
}

export interface Alert {
  alert_id: string
  company_code: string
  company_name: string
  severity: 'high' | 'medium' | 'low'
  alert_type: string
  triggered_at: string
  reason: string
  evidence: Citation[]
  status: 'active' | 'reviewed' | 'dismissed'
}

export interface Citation {
  source: string
  link: string
  page?: number
  excerpt: string
}

export interface CopilotAnswer {
  answer_text: string
  citations: Citation[]
  tables?: any[]
  alerts?: Alert[]
  confidence: number
  source_agents: string[] // ["rag", "sql", "financial"]
}

export interface CopilotAgentStatus {
  status: 'waiting' | 'running' | 'completed' | 'skipped' | 'error'
  logs: string[]
  latest_message: string
  started_at?: string
  completed_at?: string
  duration_ms?: number
}

export interface CopilotJobStatus {
  job_id: string
  query: string
  status: 'running' | 'completed' | 'error'
  started_at: string
  updated_at: string
  completed_at?: string
  error?: string
  steps: string[]
  agents: Record<string, CopilotAgentStatus>
}

export interface FinancialRatio {
  ratio_name: string
  ratio_value: number
  period: string
  change_percent?: number
  trend: 'up' | 'down' | 'stable'
}

export interface IngestionJob {
  job_id: string
  type: 'bursa' | 'news' | 'manual'
  status: 'queued' | 'running' | 'completed' | 'failed'
  progress: number
  total_documents: number
  processed_documents: number
  started_at: string
  completed_at?: string
  video_url?: string
}

// Additional UI Types

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  copilotAnswer?: CopilotAnswer
  timestamp: string
}

export interface FilterState {
  companyCode?: string
  dateRange?: { start: Date; end: Date }
  documentType?: string
  severity?: 'high' | 'medium' | 'low'
}

export interface MetricCardData {
  label: string
  value: string | number
  trend?: {
    direction: 'up' | 'down' | 'stable'
    percentage: number
  }
  variant?: 'default' | 'success' | 'warning' | 'error'
  icon?: string
}

export interface ChartDataPoint {
  period: string
  value: number
  label?: string
}

export interface TimelineEvent {
  id: string
  date: string
  title: string
  description?: string
  type: 'filing' | 'alert' | 'other'
  companyCode?: string
  companyName?: string
}

// Vector Database Types

export interface VectorCollection {
  collectionName: string
  dbName?: string
  schema?: CollectionSchema
  loaded?: boolean
}

export interface CollectionSchema {
  fields: FieldSchema[]
  description?: string
}

export interface FieldSchema {
  fieldName: string
  dataType: string
  isPrimary?: boolean
  elementTypeParams?: Record<string, any>
}

export interface CollectionStats {
  collectionName: string
  rowCount: number
  dataSize?: number
}

export interface VectorSearchResult {
  chunk_id: string
  doc_id: string
  content: string
  distance: number
  company_code?: string
  document_type?: string
}

export interface VectorEntity {
  chunk_id: string
  doc_id: string
  content: string
  chunk_order?: number
  company_code?: string
  document_type?: string
  // Fields from pdf_text_chunks collection
  filename?: string
  company_name?: string
  page_number?: number
  source?: string
  metadata_json?: string
}
