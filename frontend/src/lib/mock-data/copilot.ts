import { CopilotAnswer } from '../types/api'

// Mock copilot responses based on query types
export const mockCopilotAnswers: Record<string, CopilotAnswer> = {
  dividend: {
    answer_text:
      'Based on recent financial filings, MAYBANK (Malayan Banking Berhad) has maintained a consistent dividend policy. In Q3 2024, they declared a dividend of RM 0.62 per share, representing a payout ratio of approximately 45% of net profit. This aligns with their historical dividend distribution pattern and demonstrates strong commitment to shareholder returns despite economic headwinds.',
    citations: [
      {
        source: 'MAYBANK - Q3 2024 Financial Results',
        link: '/filings/FIL-2024-1155-Q3',
        page: 12,
        excerpt:
          'The Board of Directors has declared an interim dividend of RM 0.62 per share for the third quarter ended September 30, 2024.',
      },
      {
        source: 'MAYBANK - Dividend Policy Statement 2024',
        link: '/filings/FIL-2024-1155-DIV',
        page: 3,
        excerpt:
          'The Group maintains a dividend payout policy targeting 40-50% of net profit, subject to regulatory capital requirements and business growth opportunities.',
      },
      {
        source: 'MAYBANK - Annual Report 2023',
        link: '/filings/FIL-2023-1155-AR',
        page: 89,
        excerpt:
          'Total dividends declared for FY2023 amounted to RM 2.48 per share, representing a 5% increase year-on-year.',
      },
    ],
    tables: [
      {
        title: 'Dividend History (Last 8 Quarters)',
        columns: ['Period', 'Dividend per Share (RM)', 'Payout Ratio (%)', 'Ex-Date'],
        rows: [
          ['Q3 2024', '0.62', '45%', '2024-11-15'],
          ['Q2 2024', '0.60', '43%', '2024-08-15'],
          ['Q1 2024', '0.63', '46%', '2024-05-15'],
          ['Q4 2023', '0.63', '47%', '2024-02-15'],
          ['Q3 2023', '0.60', '44%', '2023-11-15'],
          ['Q2 2023', '0.58', '42%', '2023-08-15'],
          ['Q1 2023', '0.61', '45%', '2023-05-15'],
          ['Q4 2022', '0.60', '46%', '2023-02-15'],
        ],
      },
    ],
    alerts: [],
    confidence: 0.92,
    source_agents: ['rag', 'financial'],
  },

  risk: {
    answer_text:
      'Our alert system has identified 3 high-severity risks for GLICO (Great Eastern Life Insurance) in the past 30 days. The primary concern is a significant increase in insurance claim ratios (up 18% YoY) coupled with declining net margins. Additionally, unusual activity in related party transactions was flagged in the latest quarterly report, warranting further investigation by compliance teams.',
    citations: [
      {
        source: 'GLICO - Q3 2024 Quarterly Report',
        link: '/filings/FIL-2024-1023-Q3',
        page: 24,
        excerpt:
          'Total claims incurred increased to RM 1.8 billion in Q3 2024, up from RM 1.52 billion in Q3 2023, representing an 18.4% increase.',
      },
      {
        source: 'GLICO - Related Party Transactions Disclosure',
        link: '/filings/FIL-2024-1023-RPT',
        page: 7,
        excerpt:
          'Related party transactions for the quarter amounted to RM 450 million, primarily involving investment management fees paid to affiliated asset management companies.',
      },
      {
        source: 'Industry Benchmark Report - Insurance Sector Q3 2024',
        link: '/external/insurance-benchmark-2024-q3',
        page: 15,
        excerpt:
          'Average claims ratio for Malaysian life insurers stood at 65% in Q3 2024, indicating GLICO 72% ratio is above industry average.',
      },
    ],
    tables: [
      {
        title: 'Risk Metrics Comparison',
        columns: ['Metric', 'GLICO Q3 2024', 'Industry Avg', 'Status'],
        rows: [
          ['Claims Ratio', '72%', '65%', 'Above Threshold'],
          ['Net Margin', '8.2%', '12.5%', 'Below Target'],
          ['RPT Volume', 'RM 450M', 'RM 280M', 'High'],
          ['Solvency Ratio', '185%', '200%', 'Moderate'],
        ],
      },
    ],
    alerts: [
      {
        alert_id: 'ALERT-2024-1023-001',
        company_code: '1023',
        company_name: 'Great Eastern Life Insurance',
        severity: 'high',
        alert_type: 'Financial Deterioration',
        triggered_at: '2024-01-08T14:30:00Z',
        reason: 'Claims ratio significantly above industry benchmark with declining profitability',
        evidence: [],
        status: 'active',
      },
      {
        alert_id: 'ALERT-2024-1023-002',
        company_code: '1023',
        company_name: 'Great Eastern Life Insurance',
        severity: 'high',
        alert_type: 'Related Party Transaction',
        triggered_at: '2024-01-07T09:15:00Z',
        reason: 'Related party transaction volume 60% above historical average',
        evidence: [],
        status: 'active',
      },
    ],
    confidence: 0.88,
    source_agents: ['rag', 'sql', 'alerts'],
  },

  financial: {
    answer_text:
      'PETRONAS Gas Berhad (PETGAS) demonstrates strong financial health with consistent improvements across key metrics. Return on Equity (ROE) stands at 18.5% for Q3 2024, up from 16.2% in Q3 2023. The company maintains a healthy current ratio of 2.1x and minimal leverage with a debt-to-equity ratio of 0.35x. Operating cash flow generation remains robust at RM 2.8 billion for the 9-month period, supporting both dividend distributions and capital investments.',
    citations: [
      {
        source: 'PETGAS - Q3 2024 Financial Statements',
        link: '/filings/FIL-2024-6033-Q3',
        page: 8,
        excerpt:
          'Return on Equity improved to 18.5% in Q3 2024, driven by higher net profit margins and efficient asset utilization.',
      },
      {
        source: 'PETGAS - Balance Sheet Q3 2024',
        link: '/filings/FIL-2024-6033-Q3',
        page: 15,
        excerpt:
          'Current assets of RM 5.2 billion versus current liabilities of RM 2.5 billion, resulting in a current ratio of 2.08x.',
      },
      {
        source: 'PETGAS - Cash Flow Statement 9M 2024',
        link: '/filings/FIL-2024-6033-9M',
        page: 18,
        excerpt:
          'Net cash from operating activities for the nine months ended September 30, 2024, amounted to RM 2,847 million.',
      },
    ],
    tables: [
      {
        title: 'Key Financial Ratios - Trend Analysis',
        columns: ['Ratio', 'Q3 2024', 'Q2 2024', 'Q3 2023', 'YoY Change'],
        rows: [
          ['Return on Equity', '18.5%', '17.8%', '16.2%', '+2.3pp'],
          ['Return on Assets', '12.3%', '11.8%', '10.9%', '+1.4pp'],
          ['Net Margin', '22.1%', '21.5%', '20.3%', '+1.8pp'],
          ['Current Ratio', '2.1x', '2.0x', '1.9x', '+0.2x'],
          ['Debt/Equity', '0.35x', '0.38x', '0.42x', '-0.07x'],
        ],
      },
    ],
    alerts: [],
    confidence: 0.95,
    source_agents: ['sql', 'financial'],
  },

  default: {
    answer_text:
      'I can help you analyze financial data, company filings, and regulatory compliance. I have access to financial statements, SEC filings, alerts, and historical data for Malaysian public companies. Please ask specific questions about dividends, financial metrics, risk factors, company performance, or compliance issues.',
    citations: [],
    tables: [],
    alerts: [],
    confidence: 1.0,
    source_agents: ['rag'],
  },

  compliance: {
    answer_text:
      'Recent compliance analysis indicates that 12 out of 150 monitored companies have outstanding disclosure obligations. CIMB Holdings has delayed submission of their Q3 2024 quarterly report by 5 days past the regulatory deadline. Additionally, 3 companies (GLICO, MISC, AXIATA) have unusual patterns in related party transactions that exceed historical norms by more than 40%, triggering automatic compliance reviews.',
    citations: [
      {
        source: 'Bursa Malaysia Listing Requirements',
        link: '/external/bursa-listing-requirements-2024',
        page: 42,
        excerpt:
          'Public listed companies must submit quarterly reports within 2 months from the end of each quarter.',
      },
      {
        source: 'CIMB - Filing Status Dashboard',
        link: '/filings/status/CIMB',
        page: 1,
        excerpt:
          'Q3 2024 quarterly report due date: January 30, 2024. Actual submission: February 4, 2024.',
      },
    ],
    tables: [
      {
        title: 'Compliance Status Summary',
        columns: ['Company', 'Issue', 'Severity', 'Days Overdue', 'Status'],
        rows: [
          ['CIMB Holdings', 'Late filing', 'Medium', '5', 'Pending'],
          ['GLICO', 'RPT threshold breach', 'High', 'N/A', 'Under review'],
          ['MISC', 'RPT anomaly', 'Medium', 'N/A', 'Under review'],
          ['AXIATA', 'RPT pattern change', 'Medium', 'N/A', 'Under review'],
        ],
      },
    ],
    alerts: [
      {
        alert_id: 'ALERT-2024-CIMB-001',
        company_code: '1023',
        company_name: 'CIMB Holdings',
        severity: 'medium',
        alert_type: 'Filing Delay',
        triggered_at: '2024-01-31T00:01:00Z',
        reason: 'Quarterly report submission 5 days past regulatory deadline',
        evidence: [],
        status: 'active',
      },
    ],
    confidence: 0.91,
    source_agents: ['rag', 'sql', 'alerts'],
  },

  comparison: {
    answer_text:
      'Comparing MAYBANK vs CIMB (top 2 Malaysian banks by market cap): MAYBANK leads in ROE (15.2% vs 13.8%), asset quality (NPL ratio 1.4% vs 1.9%), and cost efficiency (CTI ratio 42% vs 48%). However, CIMB shows stronger loan growth (8.2% YoY vs 5.7%) and higher digital banking adoption rates. Both banks maintain healthy capital adequacy well above regulatory minimums.',
    citations: [
      {
        source: 'MAYBANK - Q3 2024 Financial Results',
        link: '/filings/FIL-2024-1155-Q3',
        page: 20,
        excerpt: 'Return on Equity: 15.2%. NPL ratio: 1.4%. Cost-to-Income: 42.1%.',
      },
      {
        source: 'CIMB - Q3 2024 Financial Results',
        link: '/filings/FIL-2024-1023-Q3',
        page: 18,
        excerpt: 'Return on Equity: 13.8%. NPL ratio: 1.9%. Cost-to-Income: 47.8%.',
      },
      {
        source: 'Banking Sector Comparative Analysis Q3 2024',
        link: '/external/banking-analysis-2024-q3',
        page: 25,
        excerpt:
          'CIMB reported gross loan growth of 8.2% YoY, outpacing MAYBANK 5.7% growth.',
      },
    ],
    tables: [
      {
        title: 'MAYBANK vs CIMB - Key Metrics Comparison',
        columns: ['Metric', 'MAYBANK', 'CIMB', 'Better'],
        rows: [
          ['ROE', '15.2%', '13.8%', 'MAYBANK'],
          ['NPL Ratio', '1.4%', '1.9%', 'MAYBANK'],
          ['Cost/Income', '42%', '48%', 'MAYBANK'],
          ['Loan Growth YoY', '5.7%', '8.2%', 'CIMB'],
          ['CAR', '18.5%', '17.2%', 'MAYBANK'],
          ['Digital Users', '12.5M', '14.8M', 'CIMB'],
        ],
      },
    ],
    alerts: [],
    confidence: 0.89,
    source_agents: ['sql', 'financial', 'rag'],
  },
}

// Helper function to get copilot response based on query
export function getCopilotResponse(query: string): CopilotAnswer {
  const lowerQuery = query.toLowerCase()

  if (lowerQuery.includes('dividend') || lowerQuery.includes('payout')) {
    return mockCopilotAnswers.dividend
  }

  if (lowerQuery.includes('risk') || lowerQuery.includes('alert')) {
    return mockCopilotAnswers.risk
  }

  if (
    lowerQuery.includes('financial') ||
    lowerQuery.includes('ratio') ||
    lowerQuery.includes('roe') ||
    lowerQuery.includes('performance')
  ) {
    return mockCopilotAnswers.financial
  }

  if (lowerQuery.includes('compliance') || lowerQuery.includes('regulatory')) {
    return mockCopilotAnswers.compliance
  }

  if (
    lowerQuery.includes('compare') ||
    lowerQuery.includes('comparison') ||
    lowerQuery.includes('vs')
  ) {
    return mockCopilotAnswers.comparison
  }

  return mockCopilotAnswers.default
}
