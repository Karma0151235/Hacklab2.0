import { Company } from '../types/api'

export const mockCompanies: Company[] = [
  {
    company_code: '1155',
    company_name: 'Malayan Banking Berhad',
    ticker: 'MAYBANK',
    sector: 'Financial Services',
    market_cap: 95000000000,
    filings_count: 124,
    latest_filing_date: '2026-01-10',
    alert_count: 3,
    financial_health_score: 78,
  },
  {
    company_code: '5347',
    company_name: 'Great Eastern Holdings Limited',
    ticker: 'GLICO',
    sector: 'Insurance',
    market_cap: 28000000000,
    filings_count: 89,
    latest_filing_date: '2026-01-08',
    alert_count: 1,
    financial_health_score: 85,
  },
  {
    company_code: '1082',
    company_name: 'Hong Leong Bank Berhad',
    ticker: 'HLBANK',
    sector: 'Financial Services',
    market_cap: 42000000000,
    filings_count: 156,
    latest_filing_date: '2026-01-12',
    alert_count: 5,
    financial_health_score: 72,
  },
  {
    company_code: '1023',
    company_name: 'CIMB Group Holdings Berhad',
    ticker: 'CIMB',
    sector: 'Financial Services',
    market_cap: 58000000000,
    filings_count: 201,
    latest_filing_date: '2026-01-11',
    alert_count: 7,
    financial_health_score: 68,
  },
  {
    company_code: '5183',
    company_name: 'Public Bank Berhad',
    ticker: 'PBBANK',
    sector: 'Financial Services',
    market_cap: 88000000000,
    filings_count: 178,
    latest_filing_date: '2026-01-09',
    alert_count: 2,
    financial_health_score: 82,
  },
  {
    company_code: '6888',
    company_name: 'Axiata Group Berhad',
    ticker: 'AXIATA',
    sector: 'Telecommunications',
    market_cap: 35000000000,
    filings_count: 145,
    latest_filing_date: '2026-01-07',
    alert_count: 4,
    financial_health_score: 65,
  },
  {
    company_code: '5225',
    company_name: 'Petronas Chemicals Group Berhad',
    ticker: 'PCHEM',
    sector: 'Chemicals',
    market_cap: 52000000000,
    filings_count: 98,
    latest_filing_date: '2026-01-06',
    alert_count: 2,
    financial_health_score: 74,
  },
  {
    company_code: '4863',
    company_name: 'Tenaga Nasional Berhad',
    ticker: 'TNB',
    sector: 'Utilities',
    market_cap: 65000000000,
    filings_count: 187,
    latest_filing_date: '2026-01-13',
    alert_count: 6,
    financial_health_score: 70,
  },
  {
    company_code: '5349',
    company_name: 'Dialog Group Berhad',
    ticker: 'DIALOG',
    sector: 'Oil & Gas',
    market_cap: 18000000000,
    filings_count: 76,
    latest_filing_date: '2026-01-05',
    alert_count: 1,
    financial_health_score: 79,
  },
  {
    company_code: '7277',
    company_name: 'Genting Malaysia Berhad',
    ticker: 'GENM',
    sector: 'Gaming & Leisure',
    market_cap: 21000000000,
    filings_count: 112,
    latest_filing_date: '2026-01-04',
    alert_count: 3,
    financial_health_score: 66,
  },
]

export function getCompany(code: string): Company | undefined {
  return mockCompanies.find(c => c.company_code === code)
}

export function searchCompanies(query: string): Company[] {
  const lowerQuery = query.toLowerCase()
  return mockCompanies.filter(c =>
    c.company_name.toLowerCase().includes(lowerQuery) ||
    c.ticker.toLowerCase().includes(lowerQuery) ||
    c.company_code.includes(lowerQuery)
  )
}
