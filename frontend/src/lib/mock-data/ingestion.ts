import { IngestionJob } from '../types/api'

// Mock ingestion jobs with various statuses
export const mockIngestionJobs: IngestionJob[] = [
  {
    job_id: 'JOB-2024-001',
    type: 'bursa',
    status: 'completed',
    progress: 100,
    total_documents: 450,
    processed_documents: 450,
    started_at: '2024-01-13T10:30:00Z',
    completed_at: '2024-01-13T14:45:00Z',
    video_url: '/videos/scraping-job-2024-001.webm',
  },
  {
    job_id: 'JOB-2024-002',
    type: 'bursa',
    status: 'running',
    progress: 65,
    total_documents: 380,
    processed_documents: 247,
    started_at: '2024-01-14T02:15:00Z',
    completed_at: undefined,
    video_url: undefined,
  },
  {
    job_id: 'JOB-2024-003',
    type: 'manual',
    status: 'completed',
    progress: 100,
    total_documents: 12,
    processed_documents: 12,
    started_at: '2024-01-12T16:20:00Z',
    completed_at: '2024-01-12T16:35:00Z',
    video_url: undefined,
  },
  {
    job_id: 'JOB-2024-004',
    type: 'news',
    status: 'completed',
    progress: 100,
    total_documents: 1250,
    processed_documents: 1250,
    started_at: '2024-01-11T08:00:00Z',
    completed_at: '2024-01-11T09:30:00Z',
    video_url: undefined,
  },
  {
    job_id: 'JOB-2024-005',
    type: 'bursa',
    status: 'failed',
    progress: 42,
    total_documents: 500,
    processed_documents: 210,
    started_at: '2024-01-10T14:00:00Z',
    completed_at: '2024-01-10T15:12:00Z',
    video_url: undefined,
  },
  {
    job_id: 'JOB-2024-006',
    type: 'manual',
    status: 'queued',
    progress: 0,
    total_documents: 8,
    processed_documents: 0,
    started_at: '2024-01-14T03:00:00Z',
    completed_at: undefined,
    video_url: undefined,
  },
  {
    job_id: 'JOB-2023-099',
    type: 'bursa',
    status: 'completed',
    progress: 100,
    total_documents: 2340,
    processed_documents: 2340,
    started_at: '2023-12-28T06:00:00Z',
    completed_at: '2023-12-29T18:30:00Z',
    video_url: '/videos/scraping-job-2023-099.webm',
  },
  {
    job_id: 'JOB-2023-098',
    type: 'news',
    status: 'completed',
    progress: 100,
    total_documents: 850,
    processed_documents: 850,
    started_at: '2023-12-25T10:00:00Z',
    completed_at: '2023-12-25T12:45:00Z',
    video_url: undefined,
  },
]

// Mock scraping progress logs
export const mockScrapingLogs: Array<{
  timestamp: string
  phase: string
  message: string
  level: 'info' | 'success' | 'warning' | 'error'
}> = [
  {
    timestamp: '2024-01-14T02:45:30Z',
    phase: 'crawling',
    message: 'Processing announcement page 247/380',
    level: 'info',
  },
  {
    timestamp: '2024-01-14T02:45:15Z',
    phase: 'extraction',
    message: 'Extracted 3 tables from filing FIL-2024-1155-Q3',
    level: 'success',
  },
  {
    timestamp: '2024-01-14T02:45:00Z',
    phase: 'download',
    message: 'Downloaded PDF: maybank-q3-2024.pdf (2.4 MB)',
    level: 'success',
  },
  {
    timestamp: '2024-01-14T02:44:45Z',
    phase: 'crawling',
    message: 'Processing announcement page 246/380',
    level: 'info',
  },
  {
    timestamp: '2024-01-14T02:44:30Z',
    phase: 'extraction',
    message: 'Extracted 5 tables from filing FIL-2024-6033-Q3',
    level: 'success',
  },
  {
    timestamp: '2024-01-14T02:44:20Z',
    phase: 'download',
    message: 'Downloaded PDF: petgas-q3-2024.pdf (1.8 MB)',
    level: 'success',
  },
  {
    timestamp: '2024-01-14T02:44:05Z',
    phase: 'validation',
    message: 'Skipping duplicate filing: FIL-2023-1023-Q4',
    level: 'warning',
  },
  {
    timestamp: '2024-01-14T02:43:50Z',
    phase: 'crawling',
    message: 'Processing announcement page 245/380',
    level: 'info',
  },
  {
    timestamp: '2024-01-14T02:43:35Z',
    phase: 'extraction',
    message: 'No tables found in filing FIL-2024-5183-ANN',
    level: 'warning',
  },
  {
    timestamp: '2024-01-14T02:43:20Z',
    phase: 'download',
    message: 'Downloaded PDF: glico-announcement.pdf (512 KB)',
    level: 'success',
  },
]

// Mock scraping phases
export const scrapingPhases = [
  { id: 1, name: 'Initializing', progress: 0 },
  { id: 2, name: 'Crawling announcement listings', progress: 15 },
  { id: 3, name: 'Extracting table data', progress: 40 },
  { id: 4, name: 'Downloading PDFs', progress: 70 },
  { id: 5, name: 'Finalizing video recording', progress: 95 },
  { id: 6, name: 'Completed', progress: 100 },
]

// Helper function to get current phase based on progress
export function getCurrentPhase(progress: number): string {
  if (progress === 0) return 'Initializing'
  if (progress < 15) return 'Starting scraper'
  if (progress < 40) return 'Crawling announcement listings'
  if (progress < 70) return 'Extracting table data'
  if (progress < 95) return 'Downloading PDFs'
  if (progress < 100) return 'Finalizing video recording'
  return 'Completed'
}

// Helper function to get jobs by status
export function getJobsByStatus(status: IngestionJob['status']): IngestionJob[] {
  return mockIngestionJobs.filter((job) => job.status === status)
}

// Helper function to get jobs by type
export function getJobsByType(type: IngestionJob['type']): IngestionJob[] {
  return mockIngestionJobs.filter((job) => job.type === type)
}

// Helper function to get recent jobs
export function getRecentJobs(limit: number = 5): IngestionJob[] {
  return mockIngestionJobs
    .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())
    .slice(0, limit)
}

// Helper function to get job stats
export function getJobStats() {
  const total = mockIngestionJobs.length
  const completed = mockIngestionJobs.filter((j) => j.status === 'completed').length
  const running = mockIngestionJobs.filter((j) => j.status === 'running').length
  const failed = mockIngestionJobs.filter((j) => j.status === 'failed').length
  const queued = mockIngestionJobs.filter((j) => j.status === 'queued').length

  const totalDocuments = mockIngestionJobs
    .filter((j) => j.status === 'completed')
    .reduce((sum, job) => sum + job.total_documents, 0)

  return {
    total,
    completed,
    running,
    failed,
    queued,
    totalDocuments,
    successRate: total > 0 ? Math.round((completed / total) * 100) : 0,
  }
}
