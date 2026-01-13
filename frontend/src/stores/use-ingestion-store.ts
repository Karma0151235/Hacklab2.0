import { create } from 'zustand'
import { IngestionJob } from '@/lib/types/api'

interface IngestionStore {
  jobs: IngestionJob[]
  activeJobId?: string
  addJob: (job: IngestionJob) => void
  updateJob: (jobId: string, updates: Partial<IngestionJob>) => void
  updateJobProgress: (jobId: string, progress: number, processedDocuments?: number) => void
  setActiveJob: (jobId?: string) => void
  getJobById: (jobId: string) => IngestionJob | undefined
  getRunningJobs: () => IngestionJob[]
  getRecentJobs: (limit?: number) => IngestionJob[]
}

export const useIngestionStore = create<IngestionStore>((set, get) => ({
  jobs: [],
  activeJobId: undefined,

  addJob: (job) =>
    set((state) => ({
      jobs: [job, ...state.jobs],
      activeJobId: job.job_id,
    })),

  updateJob: (jobId, updates) =>
    set((state) => ({
      jobs: state.jobs.map((job) =>
        job.job_id === jobId ? { ...job, ...updates } : job
      ),
    })),

  updateJobProgress: (jobId, progress, processedDocuments) =>
    set((state) => ({
      jobs: state.jobs.map((job) =>
        job.job_id === jobId
          ? {
              ...job,
              progress,
              ...(processedDocuments !== undefined && { processed_documents: processedDocuments }),
            }
          : job
      ),
    })),

  setActiveJob: (jobId) =>
    set({ activeJobId: jobId }),

  getJobById: (jobId) => {
    return get().jobs.find((job) => job.job_id === jobId)
  },

  getRunningJobs: () => {
    return get().jobs.filter((job) => job.status === 'running' || job.status === 'queued')
  },

  getRecentJobs: (limit = 5) => {
    return get()
      .jobs.sort(
        (a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
      )
      .slice(0, limit)
  },
}))
