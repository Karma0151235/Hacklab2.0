import { FinancialRatio } from '../types/api'

// Mock financial ratios for different companies and periods
export const mockFinancialRatios: Record<string, FinancialRatio[]> = {
  '1155': [
    // MAYBANK
    {
      ratio_name: 'Return on Equity (ROE)',
      ratio_value: 15.2,
      period: 'Q3 2024',
      change_percent: 8.6,
      trend: 'up',
    },
    {
      ratio_name: 'Return on Assets (ROA)',
      ratio_value: 1.18,
      period: 'Q3 2024',
      change_percent: 6.3,
      trend: 'up',
    },
    {
      ratio_name: 'Net Interest Margin',
      ratio_value: 2.35,
      period: 'Q3 2024',
      change_percent: -2.1,
      trend: 'down',
    },
    {
      ratio_name: 'Cost-to-Income Ratio',
      ratio_value: 42.1,
      period: 'Q3 2024',
      change_percent: -5.4,
      trend: 'down',
    },
    {
      ratio_name: 'NPL Ratio',
      ratio_value: 1.4,
      period: 'Q3 2024',
      change_percent: -12.5,
      trend: 'down',
    },
    {
      ratio_name: 'Capital Adequacy Ratio (CAR)',
      ratio_value: 18.5,
      period: 'Q3 2024',
      change_percent: 3.4,
      trend: 'up',
    },
    {
      ratio_name: 'Loan-to-Deposit Ratio',
      ratio_value: 88.2,
      period: 'Q3 2024',
      change_percent: 1.2,
      trend: 'stable',
    },
  ],

  '1023': [
    // CIMB
    {
      ratio_name: 'Return on Equity (ROE)',
      ratio_value: 13.8,
      period: 'Q3 2024',
      change_percent: 5.3,
      trend: 'up',
    },
    {
      ratio_name: 'Return on Assets (ROA)',
      ratio_value: 1.05,
      period: 'Q3 2024',
      change_percent: 4.2,
      trend: 'up',
    },
    {
      ratio_name: 'Net Interest Margin',
      ratio_value: 2.28,
      period: 'Q3 2024',
      change_percent: -1.7,
      trend: 'down',
    },
    {
      ratio_name: 'Cost-to-Income Ratio',
      ratio_value: 47.8,
      period: 'Q3 2024',
      change_percent: -3.2,
      trend: 'down',
    },
    {
      ratio_name: 'NPL Ratio',
      ratio_value: 1.9,
      period: 'Q3 2024',
      change_percent: -8.1,
      trend: 'down',
    },
    {
      ratio_name: 'Capital Adequacy Ratio (CAR)',
      ratio_value: 17.2,
      period: 'Q3 2024',
      change_percent: 2.9,
      trend: 'up',
    },
    {
      ratio_name: 'Loan-to-Deposit Ratio',
      ratio_value: 92.5,
      period: 'Q3 2024',
      change_percent: 2.8,
      trend: 'up',
    },
  ],

  '5183': [
    // GLICO (Great Eastern Life Insurance)
    {
      ratio_name: 'Return on Equity (ROE)',
      ratio_value: 11.5,
      period: 'Q3 2024',
      change_percent: -8.0,
      trend: 'down',
    },
    {
      ratio_name: 'Return on Assets (ROA)',
      ratio_value: 2.3,
      period: 'Q3 2024',
      change_percent: -6.5,
      trend: 'down',
    },
    {
      ratio_name: 'Net Profit Margin',
      ratio_value: 8.2,
      period: 'Q3 2024',
      change_percent: -12.8,
      trend: 'down',
    },
    {
      ratio_name: 'Claims Ratio',
      ratio_value: 72.0,
      period: 'Q3 2024',
      change_percent: 18.4,
      trend: 'up',
    },
    {
      ratio_name: 'Solvency Ratio',
      ratio_value: 185.0,
      period: 'Q3 2024',
      change_percent: -5.1,
      trend: 'down',
    },
    {
      ratio_name: 'Expense Ratio',
      ratio_value: 19.8,
      period: 'Q3 2024',
      change_percent: 6.2,
      trend: 'up',
    },
  ],

  '6033': [
    // PETGAS
    {
      ratio_name: 'Return on Equity (ROE)',
      ratio_value: 18.5,
      period: 'Q3 2024',
      change_percent: 14.2,
      trend: 'up',
    },
    {
      ratio_name: 'Return on Assets (ROA)',
      ratio_value: 12.3,
      period: 'Q3 2024',
      change_percent: 12.8,
      trend: 'up',
    },
    {
      ratio_name: 'Net Profit Margin',
      ratio_value: 22.1,
      period: 'Q3 2024',
      change_percent: 8.9,
      trend: 'up',
    },
    {
      ratio_name: 'Current Ratio',
      ratio_value: 2.1,
      period: 'Q3 2024',
      change_percent: 5.0,
      trend: 'up',
    },
    {
      ratio_name: 'Debt-to-Equity Ratio',
      ratio_value: 0.35,
      period: 'Q3 2024',
      change_percent: -16.7,
      trend: 'down',
    },
    {
      ratio_name: 'Asset Turnover',
      ratio_value: 0.56,
      period: 'Q3 2024',
      change_percent: 3.7,
      trend: 'up',
    },
    {
      ratio_name: 'Operating Cash Flow Margin',
      ratio_value: 28.5,
      period: 'Q3 2024',
      change_percent: 6.4,
      trend: 'up',
    },
  ],

  '3816': [
    // MISC (Logistics)
    {
      ratio_name: 'Return on Equity (ROE)',
      ratio_value: 9.8,
      period: 'Q3 2024',
      change_percent: -15.5,
      trend: 'down',
    },
    {
      ratio_name: 'Return on Assets (ROA)',
      ratio_value: 5.2,
      period: 'Q3 2024',
      change_percent: -12.3,
      trend: 'down',
    },
    {
      ratio_name: 'Net Profit Margin',
      ratio_value: 6.7,
      period: 'Q3 2024',
      change_percent: -18.2,
      trend: 'down',
    },
    {
      ratio_name: 'Current Ratio',
      ratio_value: 1.3,
      period: 'Q3 2024',
      change_percent: -8.5,
      trend: 'down',
    },
    {
      ratio_name: 'Debt-to-Equity Ratio',
      ratio_value: 0.85,
      period: 'Q3 2024',
      change_percent: 12.1,
      trend: 'up',
    },
    {
      ratio_name: 'Asset Turnover',
      ratio_value: 0.78,
      period: 'Q3 2024',
      change_percent: 1.3,
      trend: 'stable',
    },
  ],
}

// Time series data for ratio trends (8 quarters)
export const mockRatioTimeSeries: Record<
  string,
  Array<{ period: string; roe: number; roa: number; margin: number }>
> = {
  '1155': [
    { period: 'Q4 2022', roe: 12.8, roa: 0.98, margin: 2.18 },
    { period: 'Q1 2023', roe: 13.5, roa: 1.02, margin: 2.22 },
    { period: 'Q2 2023', roe: 13.9, roa: 1.06, margin: 2.28 },
    { period: 'Q3 2023', roe: 14.0, roa: 1.09, margin: 2.40 },
    { period: 'Q4 2023', roe: 14.3, roa: 1.11, margin: 2.38 },
    { period: 'Q1 2024', roe: 14.8, roa: 1.14, margin: 2.36 },
    { period: 'Q2 2024', roe: 15.0, roa: 1.16, margin: 2.37 },
    { period: 'Q3 2024', roe: 15.2, roa: 1.18, margin: 2.35 },
  ],

  '1023': [
    { period: 'Q4 2022', roe: 11.2, roa: 0.88, margin: 2.15 },
    { period: 'Q1 2023', roe: 11.8, roa: 0.91, margin: 2.18 },
    { period: 'Q2 2023', roe: 12.3, roa: 0.95, margin: 2.22 },
    { period: 'Q3 2023', roe: 13.1, roa: 1.01, margin: 2.32 },
    { period: 'Q4 2023', roe: 13.2, roa: 1.02, margin: 2.30 },
    { period: 'Q1 2024', roe: 13.5, roa: 1.03, margin: 2.29 },
    { period: 'Q2 2024', roe: 13.6, roa: 1.04, margin: 2.28 },
    { period: 'Q3 2024', roe: 13.8, roa: 1.05, margin: 2.28 },
  ],

  '5183': [
    { period: 'Q4 2022', roe: 15.2, roa: 3.1, margin: 12.5 },
    { period: 'Q1 2023', roe: 14.8, roa: 2.9, margin: 11.8 },
    { period: 'Q2 2023', roe: 14.5, roa: 2.8, margin: 11.2 },
    { period: 'Q3 2023', roe: 12.5, roa: 2.5, margin: 9.5 },
    { period: 'Q4 2023', roe: 12.0, roa: 2.4, margin: 9.0 },
    { period: 'Q1 2024', roe: 11.8, roa: 2.3, margin: 8.5 },
    { period: 'Q2 2024', roe: 11.6, roa: 2.3, margin: 8.3 },
    { period: 'Q3 2024', roe: 11.5, roa: 2.3, margin: 8.2 },
  ],

  '6033': [
    { period: 'Q4 2022', roe: 14.2, roa: 9.5, margin: 18.5 },
    { period: 'Q1 2023', roe: 14.8, roa: 9.9, margin: 19.2 },
    { period: 'Q2 2023', roe: 15.5, roa: 10.3, margin: 19.8 },
    { period: 'Q3 2023', roe: 16.2, roa: 10.9, margin: 20.3 },
    { period: 'Q4 2023', roe: 16.8, roa: 11.2, margin: 20.8 },
    { period: 'Q1 2024', roe: 17.5, roa: 11.6, margin: 21.2 },
    { period: 'Q2 2024', roe: 17.8, roa: 11.8, margin: 21.5 },
    { period: 'Q3 2024', roe: 18.5, roa: 12.3, margin: 22.1 },
  ],

  '3816': [
    { period: 'Q4 2022', roe: 14.5, roa: 7.8, margin: 9.2 },
    { period: 'Q1 2023', roe: 13.8, roa: 7.3, margin: 8.8 },
    { period: 'Q2 2023', roe: 13.2, roa: 7.0, margin: 8.5 },
    { period: 'Q3 2023', roe: 11.6, roa: 6.0, margin: 8.2 },
    { period: 'Q4 2023', roe: 11.0, roa: 5.8, margin: 7.8 },
    { period: 'Q1 2024', roe: 10.5, roa: 5.5, margin: 7.2 },
    { period: 'Q2 2024', roe: 10.0, roa: 5.3, margin: 6.9 },
    { period: 'Q3 2024', roe: 9.8, roa: 5.2, margin: 6.7 },
  ],
}

// Helper function to get ratios for a company
export function getFinancialRatios(companyCode: string): FinancialRatio[] {
  return mockFinancialRatios[companyCode] || []
}

// Helper function to get time series data
export function getRatioTimeSeries(
  companyCode: string
): Array<{ period: string; roe: number; roa: number; margin: number }> {
  return mockRatioTimeSeries[companyCode] || []
}
