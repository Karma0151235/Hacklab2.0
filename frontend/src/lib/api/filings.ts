import { Filing } from '@/lib/types/api'
import { mockFilings } from '@/lib/mock-data/filings'

/**
 * Get all filings with optional filters
 */
export async function getFilings(params?: {
  companyCode?: string
  documentType?: string
  startDate?: string
  endDate?: string
  limit?: number
}): Promise<Filing[]> {
  await new Promise((r) => setTimeout(r, 500))

  // TODO: Replace with actual API call
  // const queryParams = new URLSearchParams()
  // if (params?.companyCode) queryParams.append('company_code', params.companyCode)
  // if (params?.documentType) queryParams.append('document_type', params.documentType)
  // if (params?.startDate) queryParams.append('start_date', params.startDate)
  // if (params?.endDate) queryParams.append('end_date', params.endDate)
  // if (params?.limit) queryParams.append('limit', params.limit.toString())
  //
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/filings?${queryParams}`
  // )
  // if (!response.ok) throw new Error('Failed to fetch filings')
  // return response.json()

  let filings = [...mockFilings]

  // Apply filters
  if (params?.companyCode) {
    filings = filings.filter((f) => f.company_code === params.companyCode)
  }

  if (params?.documentType) {
    filings = filings.filter((f) => f.document_type === params.documentType)
  }

  if (params?.startDate) {
    filings = filings.filter((f) => f.announcement_date >= params.startDate!)
  }

  if (params?.endDate) {
    filings = filings.filter((f) => f.announcement_date <= params.endDate!)
  }

  // Sort by date (most recent first)
  filings.sort(
    (a, b) => new Date(b.announcement_date).getTime() - new Date(a.announcement_date).getTime()
  )

  // Apply limit
  if (params?.limit) {
    filings = filings.slice(0, params.limit)
  }

  return filings
}

/**
 * Get a single filing by ID
 */
export async function getFiling(filingId: string): Promise<Filing> {
  await new Promise((r) => setTimeout(r, 300))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/filings/${filingId}`
  // )
  // if (!response.ok) throw new Error(`Filing ${filingId} not found`)
  // return response.json()

  const filing = mockFilings.find((f) => f.filing_id === filingId)
  if (!filing) {
    throw new Error(`Filing with ID ${filingId} not found`)
  }

  return filing
}

/**
 * Get recent filings (last N filings)
 */
export async function getRecentFilings(limit: number = 10): Promise<Filing[]> {
  return getFilings({ limit })
}

/**
 * Get all unique document types
 */
export async function getDocumentTypes(): Promise<string[]> {
  await new Promise((r) => setTimeout(r, 200))

  const types = [...new Set(mockFilings.map((f) => f.document_type))]
  return types.sort()
}

/**
 * Get filings for a specific company
 */
export async function getCompanyFilings(
  companyCode: string,
  limit?: number
): Promise<Filing[]> {
  return getFilings({ companyCode, limit })
}

/**
 * Search filings by title or keywords
 */
export async function searchFilings(query: string): Promise<Filing[]> {
  await new Promise((r) => setTimeout(r, 400))

  const lowerQuery = query.toLowerCase()

  return mockFilings.filter(
    (f) =>
      f.title.toLowerCase().includes(lowerQuery) ||
      f.summary?.toLowerCase().includes(lowerQuery) ||
      f.keywords.some((k) => k.toLowerCase().includes(lowerQuery))
  )
}
