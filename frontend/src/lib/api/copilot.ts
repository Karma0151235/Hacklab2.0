import { CopilotAnswer } from '@/lib/types/api'

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
  // Use environment variable or default to localhost
  let baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1'
  
  // Normalize: remove trailing slash
  baseUrl = baseUrl.replace(/\/+$/, '')
  
  // Ensure we have the /api/v1 suffix if it's not present (and not just raw host)
  // This handles cases where user sets base url to just 'http://localhost:8000'
  if (!baseUrl.endsWith('/api/v1')) {
     baseUrl = `${baseUrl}/api/v1`
  }

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
    
    // Map backend response (SupervisorOutput) to frontend type (CopilotAnswer)
    return {
      answer_text: data.answer,
      confidence: data.confidence_score,
      source_agents: data.agents_used,
      citations: (data.citations || []).map((c: any) => ({
        source: c.filename || c.company_name || 'Unknown',
        excerpt: c.text,
        page: c.page_number,
        link: c.source_id ? `/filings/${c.source_id}` : '#'
      })),
      tables: [], 
      alerts: []
    }
  } catch (error) {
    console.error('Copilot API error:', error)
    throw error // Re-throw to let UI handle the error state instead of using mock data
  }
}


