import { Alert } from '../types/api'

export const mockAlerts: Alert[] = [
  {
    alert_id: 'A001',
    company_code: '1155',
    company_name: 'Malayan Banking Berhad',
    severity: 'high',
    alert_type: 'Related Party Transaction',
    triggered_at: '2026-01-13T09:15:00Z',
    reason: 'Significant increase in related party transactions detected. Total value increased by 340% compared to previous quarter.',
    evidence: [
      {
        source: 'Q4 2025 Financial Statements - Note 28',
        link: '/filings/F001',
        page: 142,
        excerpt: 'Related party transactions amounted to RM1.8 billion for the quarter, compared to RM520 million in Q3 2025...',
      },
      {
        source: 'Directors Report - Section 4.2',
        link: '/filings/F001',
        page: 28,
        excerpt: 'The Board approved several transactions with associates including...',
      },
    ],
    status: 'active',
  },
  {
    alert_id: 'A002',
    company_code: '1082',
    company_name: 'Hong Leong Bank Berhad',
    severity: 'high',
    alert_type: 'Credit Risk Deterioration',
    triggered_at: '2026-01-12T14:22:00Z',
    reason: 'NPL ratio increased above industry average threshold. Potential provisioning impact of RM450 million identified.',
    evidence: [
      {
        source: 'NPL Update Disclosure',
        link: '/filings/F004',
        page: 3,
        excerpt: 'Gross impaired loans ratio increased to 1.8% from 1.5%, primarily due to exposure in property development sector...',
      },
      {
        source: 'Risk Management Report',
        link: '/filings/F004',
        page: 7,
        excerpt: 'Additional provisions of RM280 million have been made for the quarter...',
      },
    ],
    status: 'active',
  },
  {
    alert_id: 'A003',
    company_code: '1023',
    company_name: 'CIMB Group Holdings Berhad',
    severity: 'medium',
    alert_type: 'Corporate Governance',
    triggered_at: '2026-01-11T11:45:00Z',
    reason: 'Multiple board members with overlapping directorships in related entities detected.',
    evidence: [
      {
        source: 'Board of Directors Profile',
        link: '/filings/F005',
        page: 15,
        excerpt: 'Directors John Lim and Sarah Wong also serve on boards of FinTech Solutions Sdn Bhd and Digital Pay Malaysia...',
      },
    ],
    status: 'reviewed',
  },
  {
    alert_id: 'A004',
    company_code: '6888',
    company_name: 'Axiata Group Berhad',
    severity: 'high',
    alert_type: 'Material Impairment',
    triggered_at: '2026-01-07T16:30:00Z',
    reason: 'Significant asset impairment disclosed. Amount represents 8.5% of total assets.',
    evidence: [
      {
        source: 'Myanmar Operations Update',
        link: '/filings/F007',
        page: 2,
        excerpt: 'Management has determined that an impairment of RM1.2 billion is required for Myanmar telecom license and related assets...',
      },
      {
        source: 'Financial Impact Assessment',
        link: '/filings/F007',
        page: 5,
        excerpt: 'This non-cash charge will impact FY2025 net profit significantly...',
      },
    ],
    status: 'active',
  },
  {
    alert_id: 'A005',
    company_name: '4863',
    company_code: 'Tenaga Nasional Berhad',
    severity: 'medium',
    alert_type: 'Operational Risk',
    triggered_at: '2026-01-13T10:00:00Z',
    reason: 'Significant cost pressure identified from commodity price volatility.',
    evidence: [
      {
        source: 'Coal Price Impact Assessment',
        link: '/filings/F009',
        page: 1,
        excerpt: 'Coal prices have increased 28% from budgeted levels, resulting in estimated additional cost of RM800 million...',
      },
    ],
    status: 'active',
  },
  {
    alert_id: 'A006',
    company_code: '1155',
    company_name: 'Malayan Banking Berhad',
    severity: 'low',
    alert_type: 'Disclosure Timing',
    triggered_at: '2026-01-10T08:30:00Z',
    reason: 'Financial results announced later than historical pattern (typically announced first week of January).',
    evidence: [
      {
        source: 'Q4 2025 Results',
        link: '/filings/F001',
        excerpt: 'Results announced on January 10, compared to January 5 in previous years...',
      },
    ],
    status: 'dismissed',
  },
  {
    alert_id: 'A007',
    company_code: '5347',
    company_name: 'Great Eastern Holdings Limited',
    severity: 'low',
    alert_type: 'Executive Changes',
    triggered_at: '2026-01-08T12:00:00Z',
    reason: 'Key management personnel change detected in C-suite position.',
    evidence: [
      {
        source: 'FY2025 Annual Report - Corporate Governance',
        link: '/filings/F003',
        page: 45,
        excerpt: 'Mr. David Ng retired as Chief Investment Officer, replaced by Ms. Jennifer Lee...',
      },
    ],
    status: 'reviewed',
  },
]

export function getAlertsByCompany(companyCode: string): Alert[] {
  return mockAlerts.filter(a => a.company_code === companyCode)
}

export function getAlertsBySeverity(severity: 'high' | 'medium' | 'low'): Alert[] {
  return mockAlerts.filter(a => a.severity === severity)
}

export function getActiveAlerts(): Alert[] {
  return mockAlerts.filter(a => a.status === 'active')
}
