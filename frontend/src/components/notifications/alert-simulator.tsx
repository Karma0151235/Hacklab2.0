'use client'

import { useEffect } from 'react'
import { useAlertStore } from '@/stores/use-alert-store'
import { showAlertNotification } from './alert-notification'
import { Alert } from '@/lib/types/api'

interface AlertSimulatorProps {
  alerts?: Alert[]
  enabled?: boolean
}

/**
 * Component that processes real alerts from copilot response
 * Displays critical (HIGH severity) alerts only
 * Replaces old mock-data based simulator
 */
export function AlertSimulator({ alerts = [], enabled = true }: AlertSimulatorProps) {
  const addAlert = useAlertStore((state) => state.addAlert)

  useEffect(() => {
    if (!enabled || !alerts || alerts.length === 0) return

    // Filter for HIGH severity alerts only (critical alerts)
    const criticalAlerts = alerts.filter((a) => a.severity === 'high')

    if (criticalAlerts.length === 0) {
      console.log('ℹ️ No critical alerts in response')
      return
    }

    // Add each critical alert to store
    criticalAlerts.forEach((alert) => {
      addAlert(alert)
      showAlertNotification(alert)
      console.log('🚨 Critical Alert:', alert.alert_type, 'for', alert.company_name, '-', alert.reason)
    })
  }, [alerts, enabled, addAlert])

  return null
}
