import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  BursaScrapingStatus,
  BursaScrapingResults,
  BursaAnnouncementRecord,
} from '@/lib/api/ingestion'

interface BursaScrapeState {
  jobId?: string
  status?: BursaScrapingStatus
  results?: BursaScrapingResults
  announcements: BursaAnnouncementRecord[]
  videoAvailable: boolean
  lastUpdated?: string
  setJobId: (jobId?: string) => void
  setStatus: (status: BursaScrapingStatus) => void
  setResults: (results: BursaScrapingResults) => void
  clearJob: () => void
}

export const useBursaScrapeStore = create<BursaScrapeState>()(
  persist(
    (set) => ({
      jobId: undefined,
      status: undefined,
      results: undefined,
      announcements: [],
      videoAvailable: false,
      lastUpdated: undefined,
      setJobId: (jobId) => set({ jobId }),
      setStatus: (status) =>
        set({
          status,
          lastUpdated: new Date().toISOString(),
        }),
      setResults: (results) =>
        set({
          results,
          announcements: results.announcements,
          videoAvailable: results.video_available,
          lastUpdated: new Date().toISOString(),
        }),
      clearJob: () =>
        set({
          jobId: undefined,
          status: undefined,
          results: undefined,
          announcements: [],
          videoAvailable: false,
          lastUpdated: undefined,
        }),
    }),
    {
      name: 'bursa-scrape-state',
      version: 1,
      partialize: (state) => ({
        jobId: state.jobId,
        status: state.status,
        results: state.results,
        announcements: state.announcements,
        videoAvailable: state.videoAvailable,
        lastUpdated: state.lastUpdated,
      }),
    }
  )
)
