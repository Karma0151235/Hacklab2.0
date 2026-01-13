import { FinancialRatio } from '@/lib/types/api'
import { getFinancialRatios, getRatioTimeSeries } from '@/lib/mock-data/financials'

/**
 * Get financial ratios for a company
 */
export async function getCompanyFinancials(companyCode: string): Promise<FinancialRatio[]> {
  await new Promise((r) => setTimeout(r, 400))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/financials/${companyCode}`
  // )
  // if (!response.ok) throw new Error(`Failed to fetch financials for ${companyCode}`)
  // return response.json()

  return getFinancialRatios(companyCode)
}

/**
 * Get time series data for financial ratios
 */
export async function getFinancialTimeSeries(
  companyCode: string
): Promise<Array<{ period: string; roe: number; roa: number; margin: number }>> {
  await new Promise((r) => setTimeout(r, 400))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/financials/${companyCode}/timeseries`
  // )
  // if (!response.ok) throw new Error(`Failed to fetch time series for ${companyCode}`)
  // return response.json()

  return getRatioTimeSeries(companyCode)
}

/**
 * Get specific ratio for a company
 */
export async function getCompanyRatio(
  companyCode: string,
  ratioName: string
): Promise<FinancialRatio | undefined> {
  const ratios = await getCompanyFinancials(companyCode)
  return ratios.find((r) => r.ratio_name === ratioName)
}

/**
 * Compare financial ratios across companies
 */
export async function compareCompanyFinancials(
  companyCodes: string[]
): Promise<Record<string, FinancialRatio[]>> {
  await new Promise((r) => setTimeout(r, 600))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/financials/compare`,
  //   {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify({ companies: companyCodes }),
  //   }
  // )
  // if (!response.ok) throw new Error('Failed to compare financials')
  // return response.json()

  const result: Record<string, FinancialRatio[]> = {}

  for (const code of companyCodes) {
    result[code] = getFinancialRatios(code)
  }

  return result
}
