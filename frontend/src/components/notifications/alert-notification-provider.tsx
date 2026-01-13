'use client'

import { useAlertNotifications } from './alert-notification'
import { useAlertStore } from '@/stores/use-alert-store'
import { AlertSimulator } from './alert-simulator'

/**
 * Alert notification provider that:
 * 1. Listens for new alert events
 * 2. Integrates with alert store
 * 3. Optionally simulates real-time alerts
 */
export function AlertNotificationProvider({
  children,
  simulateAlerts = true,
  simulationIntervalMs = 45000, // 45 seconds between alerts
}: {
  children: React.ReactNode
  simulateAlerts?: boolean
  simulationIntervalMs?: number
}) {
  const dismissAlert = useAlertStore((state) => state.dismissAlert)
  const markAsRead = useAlertStore((state) => state.markAsRead)

  // Set up notification listener
  useAlertNotifications({
    enabled: true,
    onDismiss: (alertId) => {
      dismissAlert(alertId)
    },
    onView: (alertId) => {
      markAsRead(alertId)
    },
  })

  return (
    <>
      {children}
      {simulateAlerts && (
        <AlertSimulator enabled={simulateAlerts} intervalMs={simulationIntervalMs} />
      )}
    </>
  )
}
