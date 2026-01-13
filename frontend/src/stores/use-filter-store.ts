import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface FilterStore {
  companyCode?: string
  dateRange?: { start: Date; end: Date }
  documentType?: string
  severity?: 'high' | 'medium' | 'low'
  status?: 'active' | 'reviewed' | 'dismissed'
  alertType?: string
  sector?: string

  setCompanyCode: (code?: string) => void
  setDateRange: (range?: { start: Date; end: Date }) => void
  setDocumentType: (type?: string) => void
  setSeverity: (severity?: 'high' | 'medium' | 'low') => void
  setStatus: (status?: 'active' | 'reviewed' | 'dismissed') => void
  setAlertType: (type?: string) => void
  setSector: (sector?: string) => void
  resetFilters: () => void
}

export const useFilterStore = create<FilterStore>()(
  persist(
    (set) => ({
      companyCode: undefined,
      dateRange: undefined,
      documentType: undefined,
      severity: undefined,
      status: undefined,
      alertType: undefined,
      sector: undefined,

      setCompanyCode: (code) => set({ companyCode: code }),

      setDateRange: (range) => set({ dateRange: range }),

      setDocumentType: (type) => set({ documentType: type }),

      setSeverity: (severity) => set({ severity }),

      setStatus: (status) => set({ status }),

      setAlertType: (type) => set({ alertType: type }),

      setSector: (sector) => set({ sector }),

      resetFilters: () =>
        set({
          companyCode: undefined,
          dateRange: undefined,
          documentType: undefined,
          severity: undefined,
          status: undefined,
          alertType: undefined,
          sector: undefined,
        }),
    }),
    {
      name: 'filter-store',
    }
  )
)
