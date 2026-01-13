import { Alert } from '@/lib/types/api'
import { mockAlerts } from '@/lib/mock-data/alerts'

/**
 * Get all alerts with optional filters
 */
export async function getAlerts(params?: {
  companyCode?: string
  severity?: 'high' | 'medium' | 'low'
  status?: 'active' | 'reviewed' | 'dismissed'
  alertType?: string
  limit?: number
}): Promise<Alert[]> {
  await new Promise((r) => setTimeout(r, 500))

  // TODO: Replace with actual API call
  // const queryParams = new URLSearchParams()
  // if (params?.companyCode) queryParams.append('company_code', params.companyCode)
  // if (params?.severity) queryParams.append('severity', params.severity)
  // if (params?.status) queryParams.append('status', params.status)
  // if (params?.alertType) queryParams.append('alert_type', params.alertType)
  // if (params?.limit) queryParams.append('limit', params.limit.toString())
  //
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/alerts?${queryParams}`
  // )
  // if (!response.ok) throw new Error('Failed to fetch alerts')
  // return response.json()

  let alerts = [...mockAlerts]

  // Apply filters
  if (params?.companyCode) {
    alerts = alerts.filter((a) => a.company_code === params.companyCode)
  }

  if (params?.severity) {
    alerts = alerts.filter((a) => a.severity === params.severity)
  }

  if (params?.status) {
    alerts = alerts.filter((a) => a.status === params.status)
  }

  if (params?.alertType) {
    alerts = alerts.filter((a) => a.alert_type === params.alertType)
  }

  // Sort by triggered date (most recent first)
  alerts.sort((a, b) => new Date(b.triggered_at).getTime() - new Date(a.triggered_at).getTime())

  // Apply limit
  if (params?.limit) {
    alerts = alerts.slice(0, params.limit)
  }

  return alerts
}

/**
 * Get a single alert by ID
 */
export async function getAlert(alertId: string): Promise<Alert> {
  await new Promise((r) => setTimeout(r, 300))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/alerts/${alertId}`
  // )
  // if (!response.ok) throw new Error(`Alert ${alertId} not found`)
  // return response.json()

  const alert = mockAlerts.find((a) => a.alert_id === alertId)
  if (!alert) {
    throw new Error(`Alert with ID ${alertId} not found`)
  }

  return alert
}

/**
 * Get alert counts by severity
 */
export async function getAlertCounts(): Promise<{
  high: number
  medium: number
  low: number
  total: number
}> {
  await new Promise((r) => setTimeout(r, 200))

  const activeAlerts = mockAlerts.filter((a) => a.status === 'active')

  return {
    high: activeAlerts.filter((a) => a.severity === 'high').length,
    medium: activeAlerts.filter((a) => a.severity === 'medium').length,
    low: activeAlerts.filter((a) => a.severity === 'low').length,
    total: activeAlerts.length,
  }
}

/**
 * Get recent active alerts
 */
export async function getRecentAlerts(limit: number = 10): Promise<Alert[]> {
  return getAlerts({ status: 'active', limit })
}

/**
 * Mark an alert as reviewed
 */
export async function markAlertAsReviewed(alertId: string): Promise<Alert> {
  await new Promise((r) => setTimeout(r, 300))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/alerts/${alertId}/review`,
  //   { method: 'PUT' }
  // )
  // if (!response.ok) throw new Error('Failed to mark alert as reviewed')
  // return response.json()

  const alert = mockAlerts.find((a) => a.alert_id === alertId)
  if (!alert) {
    throw new Error(`Alert with ID ${alertId} not found`)
  }

  // Update status in mock data (not persistent)
  alert.status = 'reviewed'
  return alert
}

/**
 * Dismiss an alert
 */
export async function dismissAlert(alertId: string): Promise<Alert> {
  await new Promise((r) => setTimeout(r, 300))

  // TODO: Replace with actual API call
  // const response = await fetch(
  //   `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/alerts/${alertId}/dismiss`,
  //   { method: 'PUT' }
  // )
  // if (!response.ok) throw new Error('Failed to dismiss alert')
  // return response.json()

  const alert = mockAlerts.find((a) => a.alert_id === alertId)
  if (!alert) {
    throw new Error(`Alert with ID ${alertId} not found`)
  }

  // Update status in mock data (not persistent)
  alert.status = 'dismissed'
  return alert
}

/**
 * Get all unique alert types
 */
export async function getAlertTypes(): Promise<string[]> {
  await new Promise((r) => setTimeout(r, 200))

  const types = [...new Set(mockAlerts.map((a) => a.alert_type))]
  return types.sort()
}

/**
 * Get alerts for a specific company
 */
export async function getCompanyAlerts(
  companyCode: string,
  limit?: number
): Promise<Alert[]> {
  return getAlerts({ companyCode, limit })
}
