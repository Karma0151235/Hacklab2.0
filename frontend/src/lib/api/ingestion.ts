import { IngestionJob } from '@/lib/types/api'
import {
  mockIngestionJobs,
  getRecentJobs,
  getJobStats,
  getCurrentPhase,
  mockScrapingLogs,
} from '@/lib/mock-data/ingestion'

/**
 * Get all ingestion jobs
 */
export async function getIngestionJobs(params?: {
  type?: 'bursa' | 'news' | 'manual'
  status?: 'queued' | 'running' | 'completed' | 'failed'
  limit?: number
}): Promise<IngestionJob[]> {
  await new Promise((r) => setTimeout(r, 400))

  // TODO: Replace with actual API call
  // const queryParams = new URLSearchParams()
  // if (params?.type) queryParams.append('type', params.type)
  // if (params?.status) queryParams.append('status', params.status)
  // if (params?.limit) queryParams.append('limit', params.limit.toString())
  //
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/ingestion/jobs?${queryParams}`
  // )
  // if (!response.ok) throw new Error('Failed to fetch ingestion jobs')
  // return response.json()

  let jobs = [...mockIngestionJobs]

  // Apply filters
  if (params?.type) {
    jobs = jobs.filter((j) => j.type === params.type)
  }

  if (params?.status) {
    jobs = jobs.filter((j) => j.status === params.status)
  }

  // Sort by start date (most recent first)
  jobs.sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())

  // Apply limit
  if (params?.limit) {
    jobs = jobs.slice(0, params.limit)
  }

  return jobs
}

/**
 * Get a single ingestion job by ID
 */
export async function getIngestionJob(jobId: string): Promise<IngestionJob> {
  await new Promise((r) => setTimeout(r, 300))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/ingestion/jobs/${jobId}`
  // )
  // if (!response.ok) throw new Error(`Job ${jobId} not found`)
  // return response.json()

  const job = mockIngestionJobs.find((j) => j.job_id === jobId)
  if (!job) {
    throw new Error(`Ingestion job with ID ${jobId} not found`)
  }

  return job
}

/**
 * Get recent ingestion jobs
 */
export async function getRecentIngestionJobs(limit: number = 5): Promise<IngestionJob[]> {
  await new Promise((r) => setTimeout(r, 300))
  return getRecentJobs(limit)
}

/**
 * Get ingestion job statistics
 */
export async function getIngestionStats() {
  await new Promise((r) => setTimeout(r, 200))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/ingestion/stats`
  // )
  // if (!response.ok) throw new Error('Failed to fetch ingestion stats')
  // return response.json()

  return getJobStats()
}

/**
 * Start a new Bursa scraping job
 */
export async function startBursaScrapingJob(params: {
  year?: number
  companyFilter?: string[]
  maxAnnouncements?: number
}): Promise<IngestionJob> {
  await new Promise((r) => setTimeout(r, 500))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/ingestion/bursa/start`,
  //   {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify(params),
  //   }
  // )
  // if (!response.ok) throw new Error('Failed to start scraping job')
  // return response.json()

  // Mock: Create a new job
  const newJob: IngestionJob = {
    job_id: `JOB-${new Date().getFullYear()}-${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`,
    type: 'bursa',
    status: 'running',
    progress: 0,
    total_documents: params.maxAnnouncements || 100,
    processed_documents: 0,
    started_at: new Date().toISOString(),
  }

  return newJob
}

/**
 * Upload files for manual ingestion
 */
export async function uploadFiles(files: File[]): Promise<IngestionJob> {
  await new Promise((r) => setTimeout(r, 800))

  // TODO: Replace with actual API call
  // const formData = new FormData()
  // files.forEach((file, index) => {
  //   formData.append(`file_${index}`, file)
  // })
  //
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/ingestion/upload`,
  //   {
  //     method: 'POST',
  //     body: formData,
  //   }
  // )
  // if (!response.ok) throw new Error('Failed to upload files')
  // return response.json()

  // Mock: Create a new manual ingestion job
  const newJob: IngestionJob = {
    job_id: `JOB-${new Date().getFullYear()}-${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`,
    type: 'manual',
    status: 'queued',
    progress: 0,
    total_documents: files.length,
    processed_documents: 0,
    started_at: new Date().toISOString(),
  }

  return newJob
}

/**
 * Get scraping logs for a job
 */
export async function getScrapingLogs(jobId: string) {
  await new Promise((r) => setTimeout(r, 300))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/ingestion/jobs/${jobId}/logs`
  // )
  // if (!response.ok) throw new Error('Failed to fetch logs')
  // return response.json()

  // Return mock logs
  return mockScrapingLogs
}

/**
 * Get current phase description for a job
 */
export function getJobPhase(progress: number): string {
  return getCurrentPhase(progress)
}

/**
 * Cancel a running ingestion job
 */
export async function cancelIngestionJob(jobId: string): Promise<IngestionJob> {
  await new Promise((r) => setTimeout(r, 300))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/ingestion/jobs/${jobId}/cancel`,
  //   { method: 'POST' }
  // )
  // if (!response.ok) throw new Error('Failed to cancel job')
  // return response.json()

  const job = mockIngestionJobs.find((j) => j.job_id === jobId)
  if (!job) {
    throw new Error(`Ingestion job with ID ${jobId} not found`)
  }

  // Update status in mock data (not persistent)
  job.status = 'failed'
  job.completed_at = new Date().toISOString()

  return job
}

// ============================================================================
// PDF ETL Pipeline API
// ============================================================================

export interface PDFUploadResponse {
  job_id: string
  status: string
  message: string
  files_received: number
  filenames: string[]
}

export interface PDFProcessingStatus {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_files: number
  processed_files: number
  text_chunks_loaded: number
  table_chunks_loaded: number
  errors: string[]
}

/**
 * Upload PDFs to ETL pipeline
 * Connects to the backend API at http://localhost:8000/api/v1/ingest/pdfs
 */
export async function uploadPDFsForETL(files: File[]): Promise<PDFUploadResponse> {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })

  const response = await fetch(`${API_BASE_URL}/api/v1/ingest/pdfs`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(error.detail || `Upload failed with status ${response.status}`)
  }

  return response.json()
}

/**
 * Get ETL job status
 * Polls the backend API for job processing status
 */
export async function getETLJobStatus(jobId: string): Promise<PDFProcessingStatus> {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

  const response = await fetch(`${API_BASE_URL}/api/v1/ingest/status/${jobId}`)

  if (!response.ok) {
    throw new Error(`Failed to get job status: ${response.statusText}`)
  }

  return response.json()
}

// ==================== Bursa Scraping API ====================

export interface BursaScrapingRequest {
  year: number
  max_announcements: number
  company_filter?: string
  resource_efficient?: boolean
  use_cloudscraper?: boolean
  manual_captcha_timeout_seconds?: number
}

export interface BursaScrapingResponse {
  job_id: string
  status: string
  message: string
  year: number
  max_announcements: number
  company_filter?: string[]
  resource_efficient: boolean
  use_cloudscraper: boolean
  manual_captcha_timeout_seconds: number
}

export interface BursaScrapingStatus {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  phase: string
  message?: string
  total_announcements: number
  scraped_announcements: number
  errors: string[]
  ingestion_status?: string
  ingestion_stats?: Record<string, number>
  current_company?: string
  current_title?: string
  current_url?: string
  current_category?: string
  current_year?: number
  target_companies?: string[]
  created_at: string
  completed_at?: string
}

export interface BursaAnnouncementRecord {
  company_code?: string
  announcement_date: string
  category: string
  title: string
  tables_count: number
  detail_page_url: string
}

export interface BursaScrapingResults {
  job_id: string
  status: string
  total_announcements: number
  announcements: BursaAnnouncementRecord[]
  video_available: boolean
  ingestion_stats?: Record<string, number>
  ingestion_status?: string
}

/**
 * Start a Bursa Malaysia scraping job
 */
export async function startBursaScraping(request: BursaScrapingRequest): Promise<BursaScrapingResponse> {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

  // Clean up payload - remove undefined values
  const cleanPayload = {
    year: request.year,
    max_announcements: request.max_announcements,
    company_filter: request.company_filter || null,
    resource_efficient: request.resource_efficient ?? false,
    use_cloudscraper: request.use_cloudscraper ?? true,
    manual_captcha_timeout_seconds: request.manual_captcha_timeout_seconds ?? 120
  }

  console.log('Sending cleaned payload:', cleanPayload)

  const response = await fetch(`${API_BASE_URL}/api/v1/scraping/bursa/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(cleanPayload),
  })

  if (!response.ok) {
    let errorDetail = `Failed to start scraping: ${response.statusText}`
    try {
      const errorJson = await response.json()
      console.log('API Error Response:', errorJson)

      // Handle Pydantic validation errors
      if (errorJson.detail) {
        if (Array.isArray(errorJson.detail)) {
          errorDetail = errorJson.detail.map((err: any) =>
            `${err.loc?.join('.')}: ${err.msg}`
          ).join('; ')
        } else if (typeof errorJson.detail === 'string') {
          errorDetail = errorJson.detail
        }
      }
    } catch (e) {
      console.log('Could not parse error response')
    }

    throw new Error(errorDetail)
  }

  return response.json()
}

/**
 * Get Bursa scraping job status
 */
export async function getBursaScrapingStatus(jobId: string): Promise<BursaScrapingStatus> {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

  const response = await fetch(`${API_BASE_URL}/api/v1/scraping/bursa/status/${jobId}`)

  if (!response.ok) {
    throw new Error(`Failed to get job status: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Get Bursa scraping job results
 */
export async function getBursaScrapingResults(jobId: string): Promise<BursaScrapingResults> {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

  const response = await fetch(`${API_BASE_URL}/api/v1/scraping/bursa/results/${jobId}`)

  if (!response.ok) {
    throw new Error(`Failed to get results: ${response.statusText}`)
  }

  return response.json()
}

/**
 * Get video URL for a scraping job
 */
export function getBursaScrapingVideoUrl(jobId: string): string {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  return `${API_BASE_URL}/api/v1/scraping/bursa/video/${jobId}`
}
