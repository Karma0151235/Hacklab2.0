import { Company } from '@/lib/types/api'
import { mockCompanies } from '@/lib/mock-data/companies'

/**
 * Get all companies
 */
export async function getCompanies(): Promise<Company[]> {
  // Simulate network delay
  await new Promise((r) => setTimeout(r, 500))

  // TODO: Replace with actual API call when backend is ready
  // const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/companies`)
  // if (!response.ok) throw new Error('Failed to fetch companies')
  // return response.json()

  return mockCompanies
}

/**
 * Get a single company by code
 */
export async function getCompany(code: string): Promise<Company> {
  await new Promise((r) => setTimeout(r, 300))

  // TODO: Replace with actual API call
  // const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/companies/${code}`)
  // if (!response.ok) throw new Error(`Company ${code} not found`)
  // return response.json()

  const company = mockCompanies.find((c) => c.company_code === code)
  if (!company) {
    throw new Error(`Company with code ${code} not found`)
  }

  return company
}

/**
 * Search companies by name or ticker
 */
export async function searchCompanies(query: string): Promise<Company[]> {
  await new Promise((r) => setTimeout(r, 300))

  const lowerQuery = query.toLowerCase()

  return mockCompanies.filter(
    (c) =>
      c.company_name.toLowerCase().includes(lowerQuery) ||
      c.ticker.toLowerCase().includes(lowerQuery) ||
      c.company_code.includes(lowerQuery)
  )
}

/**
 * Get companies by sector
 */
export async function getCompaniesBySector(sector: string): Promise<Company[]> {
  await new Promise((r) => setTimeout(r, 300))

  return mockCompanies.filter((c) => c.sector === sector)
}

/**
 * Get all unique sectors
 */
export async function getSectors(): Promise<string[]> {
  await new Promise((r) => setTimeout(r, 200))

  const sectors = [...new Set(mockCompanies.map((c) => c.sector))]
  return sectors.sort()
}
