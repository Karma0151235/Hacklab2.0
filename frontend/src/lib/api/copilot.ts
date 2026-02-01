import { CopilotAnswer, CopilotJobStatus } from '@/lib/types/api'

/**
 * Send a message to the copilot and get a response
 */
function getBaseUrl() {
  let baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'
  baseUrl = baseUrl.replace(/\/+$/, '')
  if (!baseUrl.endsWith('/api/v1')) {
    baseUrl = `${baseUrl}/api/v1`
  }
  return baseUrl
}

export async function startCopilotJob(query: string): Promise<CopilotJobStatus> {
  const baseUrl = getBaseUrl()
  const response = await fetch(`${baseUrl}/copilot/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      session_id: 'default-session',
      stream: false,
    }),
  })

  if (!response.ok) {
    throw new Error(`Copilot start failed: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

export async function getCopilotStatus(jobId: string): Promise<CopilotJobStatus> {
  const baseUrl = getBaseUrl()
  const response = await fetch(`${baseUrl}/copilot/status/${jobId}`)
  if (!response.ok) {
    throw new Error(`Copilot status failed: ${response.status} ${response.statusText}`)
  }
  return response.json()
}

export async function getCopilotResult(jobId: string): Promise<CopilotAnswer> {
  const baseUrl = getBaseUrl()
  const response = await fetch(`${baseUrl}/copilot/results/${jobId}`)
  if (!response.ok) {
    throw new Error(`Copilot result failed: ${response.status} ${response.statusText}`)
  }

  const data = await response.json()
  return {
    answer_text: data.answer,
    confidence: data.confidence_score,
    source_agents: data.agents_used,
    citations: (data.citations || []).map((c: any) => ({
      source: c.filename || c.company_name || 'Unknown',
      excerpt: c.text,
      page: c.page_number,
      link: c.source_id ? `/filings/${c.source_id}` : '#',
    })),
    tables: [],
    alerts: [],
  }
}

export async function sendCopilotMessage(
  query: string,
  context?: {
    companyCode?: string
    startDate?: string
    endDate?: string
  }
): Promise<CopilotAnswer> {
  const baseUrl = getBaseUrl()

  try {
    const response = await fetch(`${baseUrl}/copilot/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        query, 
        session_id: 'default-session',
        stream: false
      }),
    })

    if (!response.ok) {
      throw new Error(`Copilot API request failed: ${response.status} ${response.statusText}`)
    }

    const data = await response.json()
    return {
      answer_text: data.answer,
      confidence: data.confidence_score,
      source_agents: data.agents_used,
      citations: (data.citations || []).map((c: any) => ({
        source: c.filename || c.company_name || 'Unknown',
        excerpt: c.text,
        page: c.page_number,
        link: c.source_id ? `/filings/${c.source_id}` : '#',
      })),
      tables: [],
      alerts: [],
    }
  } catch (error) {
    console.error('Copilot API error:', error)
    throw error // Re-throw to let UI handle the error state instead of using mock data
  }
}


