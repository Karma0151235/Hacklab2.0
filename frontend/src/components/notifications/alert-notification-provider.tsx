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
  criticalAlerts = [],
  simulateAlerts = false, // Disabled by default - alerts now come from copilot response
  simulationIntervalMs = 45000,
}: {
  children: React.ReactNode
  criticalAlerts?: any[]
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
      {/* Use real alerts from copilot response, with fallback to simulator if needed */}
      <AlertSimulator enabled={criticalAlerts.length > 0 || simulateAlerts} alerts={criticalAlerts} />
    </>
  )
}
