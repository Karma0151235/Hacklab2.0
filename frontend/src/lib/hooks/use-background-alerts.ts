'use client'

import { useEffect, useRef } from 'react'
import { useAlertStore } from '@/stores/use-alert-store'
import { showAlertNotification } from '@/components/notifications/alert-notification'
import { Alert } from '@/lib/types/api'

/**
 * Hook to poll for critical alerts from background monitoring
 * Runs on app startup and continuously checks for new alerts
 */
export function useBackgroundAlerts(
  enabled: boolean = true,
  pollIntervalSeconds: number = 18,
) {
  const addAlert = useAlertStore((state) => state.addAlert)
  const pollRef = useRef<NodeJS.Timeout | null>(null)
  const seenAlertIdsRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    if (!enabled) return

    const pollForAlerts = async () => {
      try {
        const response = await fetch('/api/v1/alerts/critical?since_minutes=120&limit=50')

        if (!response.ok) {
          console.warn('Failed to fetch critical alerts:', response.statusText)
          return
        }

        const data = await response.json()
        const alerts = data.alerts || []

        if (alerts.length === 0) {
          console.debug('No critical alerts found')
          return
        }

        // Process only new alerts (not seen before)
        const newAlerts = alerts.filter((alert: Alert) => {
          if (seenAlertIdsRef.current.has(alert.alert_id)) {
            return false // Already processed
          }
          seenAlertIdsRef.current.add(alert.alert_id)
          return true
        })

        if (newAlerts.length === 0) {
          console.debug('All alerts already seen')
          return
        }

        // Show notification and add to store for each new alert
        newAlerts.forEach((alert: Alert) => {
          // Trigger toast notification
          showAlertNotification(alert)

          // Add to alert store
          addAlert(alert)

          // Acknowledge alert to backend (mark as notified)
          fetch(`/api/v1/alerts/acknowledge/${alert.alert_id}`, {
            method: 'POST',
          }).catch((err) =>
            console.warn(`Failed to acknowledge alert ${alert.alert_id}:`, err),
          )

          console.log(
            '🚨 Background Alert:',
            alert.alert_type,
            'for',
            alert.company_name,
          )
        })
      } catch (error) {
        console.error('Error polling for background alerts:', error)
      }
    }

    // Initial poll
    pollForAlerts()

    // Set up polling interval
    pollRef.current = setInterval(pollForAlerts, pollIntervalSeconds * 1000)

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
      }
    }
  }, [enabled, pollIntervalSeconds, addAlert])
}
