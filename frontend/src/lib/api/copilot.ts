import { CopilotAnswer } from '@/lib/types/api'
import { getCopilotResponse } from '@/lib/mock-data/copilot'

/**
 * Send a message to the copilot and get a response
 */
export async function sendCopilotMessage(
  query: string,
  context?: {
    companyCode?: string
    startDate?: string
    endDate?: string
  }
): Promise<CopilotAnswer> {
  // Simulate AI processing time
  await new Promise((r) => setTimeout(r, 1500))

  // TODO: Replace with actual API call
  // const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/copilot/query`, {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ query, context }),
  // })
  // if (!response.ok) throw new Error('Failed to get copilot response')
  // return response.json()

  // Get mock response based on query keywords
  return getCopilotResponse(query)
}

/**
 * Get suggested questions based on context
 */
export async function getSuggestedQuestions(context?: {
  companyCode?: string
  page?: string
}): Promise<string[]> {
  await new Promise((r) => setTimeout(r, 300))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/copilot/suggestions`,
  //   {
  //     method: 'POST',
  //     headers: { 'Content-Type': 'application/json' },
  //     body: JSON.stringify(context),
  //   }
  // )
  // if (!response.ok) throw new Error('Failed to get suggestions')
  // return response.json()

  // Return context-aware suggestions
  if (context?.companyCode) {
    return [
      `What are the latest financial highlights for ${context.companyCode}?`,
      `Show me all high-severity alerts for ${context.companyCode}`,
      `What is the dividend policy of ${context.companyCode}?`,
      `Compare ${context.companyCode} with industry peers`,
    ]
  }

  if (context?.page === 'alerts') {
    return [
      'What are the most critical alerts in the past 30 days?',
      'Show me companies with deteriorating financial health',
      'Which companies have unusual related party transactions?',
      'Are there any late filing violations?',
    ]
  }

  if (context?.page === 'filings') {
    return [
      'What are the key changes in recent quarterly reports?',
      'Show me companies with declining profit margins',
      'Which filings mention dividend announcements?',
      'Summarize recent M&A activity',
    ]
  }

  // Default suggestions
  return [
    'What companies have the highest dividend yields?',
    'Show me recent high-severity compliance alerts',
    'Which companies have the best ROE in the financial sector?',
    'Are there any unusual patterns in recent filings?',
    'Compare MAYBANK and CIMB financial performance',
  ]
}
