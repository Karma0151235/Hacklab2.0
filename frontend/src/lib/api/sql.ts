/**
 * SQL Query Result
 */
export interface SQLQueryResult {
  sql: string
  columns: string[]
  rows: any[][]
  executionTime: number
  rowCount: number
}

/**
 * Execute a natural language query and get SQL + results
 */
export async function executeNaturalLanguageQuery(
  query: string
): Promise<SQLQueryResult> {
  // Simulate AI processing + SQL execution time
  await new Promise((r) => setTimeout(r, 1200))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/sql/query`,
  //   {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify({ query }),
  //   }
  // )
  // if (!response.ok) throw new Error('Failed to execute query')
  // return response.json()

  // Mock response based on query keywords
  const lowerQuery = query.toLowerCase()

  if (lowerQuery.includes('dividend') || lowerQuery.includes('highest')) {
    return {
      sql: `SELECT company_name, ticker, dividend_yield, payout_ratio
FROM companies
JOIN financials ON companies.company_code = financials.company_code
WHERE period = 'Q3 2024'
ORDER BY dividend_yield DESC
LIMIT 10;`,
      columns: ['Company Name', 'Ticker', 'Dividend Yield (%)', 'Payout Ratio (%)'],
      rows: [
        ['Malayan Banking Berhad', 'MAYBANK', 5.8, 45],
        ['CIMB Group Holdings', 'CIMB', 5.2, 43],
        ['Public Bank Berhad', 'PBBANK', 4.9, 50],
        ['Hong Leong Bank', 'HLBANK', 4.7, 42],
        ['RHB Bank Berhad', 'RHBBANK', 4.5, 40],
        ['AmBank Group', 'AMBANK', 4.2, 38],
        ['Tenaga Nasional', 'TENAGA', 3.8, 55],
        ['Petronas Gas', 'PETGAS', 3.5, 40],
        ['Axiata Group', 'AXIATA', 3.2, 60],
        ['Maxis Berhad', 'MAXIS', 3.0, 58],
      ],
      executionTime: 245,
      rowCount: 10,
    }
  }

  if (lowerQuery.includes('alert') || lowerQuery.includes('high severity')) {
    return {
      sql: `SELECT company_name, alert_type, severity, reason, triggered_at
FROM alerts
WHERE severity = 'high' AND status = 'active'
ORDER BY triggered_at DESC;`,
      columns: ['Company', 'Alert Type', 'Severity', 'Reason', 'Triggered At'],
      rows: [
        [
          'Great Eastern Life Insurance',
          'Financial Deterioration',
          'high',
          'Claims ratio above industry benchmark',
          '2024-01-08 14:30:00',
        ],
        [
          'Great Eastern Life Insurance',
          'Related Party Transaction',
          'high',
          'RPT volume 60% above historical average',
          '2024-01-07 09:15:00',
        ],
        [
          'MISC Berhad',
          'Profit Warning',
          'high',
          'Net margin declined 18% YoY',
          '2024-01-06 11:20:00',
        ],
      ],
      executionTime: 189,
      rowCount: 3,
    }
  }

  if (lowerQuery.includes('roe') || lowerQuery.includes('financial')) {
    return {
      sql: `SELECT company_name, sector, roe, roa, net_margin
FROM companies
JOIN financials ON companies.company_code = financials.company_code
WHERE sector = 'Financial Services' AND period = 'Q3 2024'
ORDER BY roe DESC;`,
      columns: ['Company', 'Sector', 'ROE (%)', 'ROA (%)', 'Net Margin (%)'],
      rows: [
        ['Malayan Banking Berhad', 'Financial Services', 15.2, 1.18, 2.35],
        ['CIMB Group Holdings', 'Financial Services', 13.8, 1.05, 2.28],
        ['Public Bank Berhad', 'Financial Services', 13.5, 1.12, 2.40],
        ['Hong Leong Bank', 'Financial Services', 12.8, 0.98, 2.15],
        ['RHB Bank Berhad', 'Financial Services', 11.9, 0.92, 2.08],
      ],
      executionTime: 312,
      rowCount: 5,
    }
  }

  if (lowerQuery.includes('filing') || lowerQuery.includes('recent')) {
    return {
      sql: `SELECT company_name, document_type, announcement_date, title
FROM filings
WHERE announcement_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY announcement_date DESC
LIMIT 20;`,
      columns: ['Company', 'Document Type', 'Date', 'Title'],
      rows: [
        ['Malayan Banking Berhad', 'Quarterly Report', '2024-01-10', 'Q3 2024 Financial Results'],
        ['CIMB Group Holdings', 'Announcement', '2024-01-09', 'Board Changes Notification'],
        ['Petronas Gas', 'Quarterly Report', '2024-01-09', 'Q3 2024 Results'],
        [
          'Great Eastern Life',
          'Disclosure',
          '2024-01-08',
          'Related Party Transactions Q3',
        ],
        ['MISC Berhad', 'Quarterly Report', '2024-01-07', 'Q3 2024 Financial Results'],
        ['Axiata Group', 'Announcement', '2024-01-06', 'Dividend Declaration'],
        ['Tenaga Nasional', 'Annual Report', '2024-01-05', 'FY2023 Annual Report'],
      ],
      executionTime: 278,
      rowCount: 7,
    }
  }

  // Default response
  return {
    sql: `SELECT company_name, sector, market_cap, filings_count, alert_count
FROM companies
ORDER BY market_cap DESC
LIMIT 20;`,
    columns: ['Company', 'Sector', 'Market Cap (RM)', 'Filings', 'Alerts'],
    rows: [
      ['Malayan Banking Berhad', 'Financial Services', 95000000000, 124, 3],
      ['CIMB Group Holdings', 'Financial Services', 55000000000, 98, 2],
      ['Public Bank Berhad', 'Financial Services', 82000000000, 112, 1],
      ['Tenaga Nasional', 'Utilities', 70000000000, 85, 2],
      ['Petronas Gas', 'Energy', 42000000000, 76, 1],
      ['Axiata Group', 'Telecommunications', 38000000000, 92, 3],
      ['Maxis Berhad', 'Telecommunications', 32000000000, 68, 1],
      ['MISC Berhad', 'Logistics', 28000000000, 54, 4],
    ],
    executionTime: 195,
    rowCount: 8,
  }
}

/**
 * Get query history (last N queries)
 */
export async function getQueryHistory(limit: number = 10): Promise<
  Array<{
    id: string
    query: string
    timestamp: string
    executionTime: number
  }>
> {
  await new Promise((r) => setTimeout(r, 200))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/sql/history?limit=${limit}`
  // )
  // if (!response.ok) throw new Error('Failed to fetch query history')
  // return response.json()

  // Mock query history
  return [
    {
      id: 'Q-001',
      query: 'Show me companies with highest dividend yields',
      timestamp: '2024-01-14T02:30:00Z',
      executionTime: 245,
    },
    {
      id: 'Q-002',
      query: 'What are the high severity alerts?',
      timestamp: '2024-01-14T01:15:00Z',
      executionTime: 189,
    },
    {
      id: 'Q-003',
      query: 'Compare ROE across financial sector',
      timestamp: '2024-01-13T23:45:00Z',
      executionTime: 312,
    },
    {
      id: 'Q-004',
      query: 'Show recent filings from last week',
      timestamp: '2024-01-13T22:20:00Z',
      executionTime: 278,
    },
    {
      id: 'Q-005',
      query: 'List all companies by market cap',
      timestamp: '2024-01-13T20:10:00Z',
      executionTime: 195,
    },
  ].slice(0, limit)
}

/**
 * Export query results to CSV
 */
export async function exportQueryResultsToCSV(result: SQLQueryResult): Promise<Blob> {
  await new Promise((r) => setTimeout(r, 200))

  // Generate CSV content
  const csvRows = []

  // Add header row
  csvRows.push(result.columns.join(','))

  // Add data rows
  result.rows.forEach((row) => {
    csvRows.push(row.map((cell) => `"${cell}"`).join(','))
  })

  const csvContent = csvRows.join('\n')
  return new Blob([csvContent], { type: 'text/csv' })
}
