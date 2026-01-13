'use client'

import { useEffect } from 'react'
import { useAlertStore } from '@/stores/use-alert-store'
import { triggerAlertNotification } from './alert-notification'
import { mockAlerts } from '@/lib/mock-data/alerts'

interface AlertSimulatorProps {
  enabled?: boolean
  intervalMs?: number
}

/**
 * Component that simulates real-time alert generation
 * For demo purposes - replace with actual WebSocket/SSE in production
 */
export function AlertSimulator({ enabled = true, intervalMs = 30000 }: AlertSimulatorProps) {
  const addAlert = useAlertStore((state) => state.addAlert)

  useEffect(() => {
    if (!enabled) return

    // Initialize with some mock alerts
    const activeAlerts = mockAlerts.filter((a) => a.status === 'active')
    activeAlerts.forEach((alert) => {
      addAlert(alert)
    })

    // Simulate new alerts arriving periodically
    const interval = setInterval(() => {
      // Pick a random active alert from mock data
      const randomAlert = activeAlerts[Math.floor(Math.random() * activeAlerts.length)]

      if (randomAlert) {
        // Create a new alert with current timestamp
        const newAlert = {
          ...randomAlert,
          alert_id: `A${Date.now()}`,
          triggered_at: new Date().toISOString(),
        }

        // Add to store
        addAlert(newAlert)

        // Show notification
        triggerAlertNotification(newAlert)

        console.log('🔔 New alert generated:', newAlert.alert_type, '-', newAlert.company_name)
      }
    }, intervalMs)

    return () => {
      clearInterval(interval)
    }
  }, [enabled, intervalMs, addAlert])

  return null
}
