'use client'

import { useBackgroundAlerts } from '@/lib/hooks/use-background-alerts'

/**
 * Background Alerts Provider
 * Initializes background alert monitoring on app startup
 * Polls for critical alerts every 18 seconds
 */
export function BackgroundAlertsProvider({ children }: { children: React.ReactNode }) {
  // DISABLED: Background alert monitoring
  useBackgroundAlerts(false, 18)

  return <>{children}</>
}
