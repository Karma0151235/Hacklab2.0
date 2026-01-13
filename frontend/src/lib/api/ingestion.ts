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
