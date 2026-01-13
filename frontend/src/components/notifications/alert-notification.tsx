'use client'

import { useEffect } from 'react'
import { toast } from 'sonner'
import { AlertTriangle, AlertCircle, Info, X, Eye } from 'lucide-react'
import { Alert } from '@/lib/types/api'
import { useRouter } from 'next/navigation'

interface AlertNotificationProps {
  alert: Alert
  onDismiss?: (alertId: string) => void
  onView?: (alertId: string) => void
}

/**
 * Individual alert notification component
 * Used with Sonner to display toast notifications
 */
export function AlertNotification({ alert, onDismiss, onView }: AlertNotificationProps) {
  const router = useRouter()

  const handleView = () => {
    if (onView) {
      onView(alert.alert_id)
    }
    router.push(`/alerts/${alert.alert_id}`)
    toast.dismiss()
  }

  const handleDismiss = () => {
    if (onDismiss) {
      onDismiss(alert.alert_id)
    }
    toast.dismiss()
  }

  // Get severity styles
  const getSeverityStyles = () => {
    switch (alert.severity) {
      case 'high':
        return {
          icon: AlertTriangle,
          iconColor: 'text-red-400',
          borderColor: 'border-l-red-500',
          bgGradient: 'from-red-950/30 to-transparent',
        }
      case 'medium':
        return {
          icon: AlertCircle,
          iconColor: 'text-orange-400',
          borderColor: 'border-l-orange-500',
          bgGradient: 'from-orange-950/30 to-transparent',
        }
      case 'low':
        return {
          icon: Info,
          iconColor: 'text-blue-400',
          borderColor: 'border-l-blue-500',
          bgGradient: 'from-blue-950/30 to-transparent',
        }
    }
  }

  const styles = getSeverityStyles()
  const Icon = styles.icon

  return (
    <div
      className={`
        relative w-full max-w-md
        bg-gradient-to-r ${styles.bgGradient}
        bg-[#0f1419] border border-[#21262d] ${styles.borderColor} border-l-4
        rounded-lg p-4 shadow-2xl
        flex items-start gap-3
      `}
    >
      {/* Severity Icon */}
      <div className={`flex-shrink-0 mt-0.5 ${styles.iconColor}`}>
        <Icon className="w-5 h-5" />
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2 mb-1">
          <div className="flex-1">
            <p className="text-sm font-semibold text-[#e6edf3] leading-tight">
              {alert.alert_type}
            </p>
            <p className="text-xs text-[#8b949e] mt-0.5">
              {alert.company_name}
            </p>
          </div>
        </div>

        <p className="text-sm text-[#8b949e] leading-snug mt-2 line-clamp-2">
          {alert.reason}
        </p>

        {/* Action buttons */}
        <div className="flex items-center gap-2 mt-3">
          <button
            onClick={handleView}
            className="
              flex items-center gap-1.5 px-3 py-1.5
              bg-[#00d9ff]/10 hover:bg-[#00d9ff]/20
              border border-[#00d9ff]/30 hover:border-[#00d9ff]/50
              rounded text-xs font-medium text-[#00d9ff]
              transition-all duration-200
            "
          >
            <Eye className="w-3.5 h-3.5" />
            View Details
          </button>
          <button
            onClick={handleDismiss}
            className="
              flex items-center gap-1.5 px-3 py-1.5
              bg-[#21262d] hover:bg-[#2d333b]
              border border-[#21262d] hover:border-[#2d333b]
              rounded text-xs font-medium text-[#8b949e] hover:text-[#e6edf3]
              transition-all duration-200
            "
          >
            <X className="w-3.5 h-3.5" />
            Dismiss
          </button>
        </div>
      </div>

      {/* Glow effect */}
      <div
        className={`
          absolute inset-0 rounded-lg pointer-events-none
          bg-gradient-to-br ${styles.bgGradient}
          opacity-0 group-hover:opacity-100 transition-opacity
        `}
      />
    </div>
  )
}

/**
 * Utility function to show alert notification
 */
export function showAlertNotification(
  alert: Alert,
  onDismiss?: (alertId: string) => void,
  onView?: (alertId: string) => void
) {
  // Determine duration based on severity
  const duration = alert.severity === 'high' ? 10000 : alert.severity === 'medium' ? 7000 : 5000

  toast.custom(
    (t) => <AlertNotification alert={alert} onDismiss={onDismiss} onView={onView} />,
    {
      duration,
      position: 'top-right',
      // Keep on screen for high severity alerts
      dismissible: true,
      id: alert.alert_id,
    }
  )
}

/**
 * Hook to enable real-time alert notifications
 */
export function useAlertNotifications({
  enabled = true,
  onDismiss,
  onView,
}: {
  enabled?: boolean
  onDismiss?: (alertId: string) => void
  onView?: (alertId: string) => void
} = {}) {
  useEffect(() => {
    if (!enabled) return

    // Listen for custom alert events
    const handleNewAlert = (event: CustomEvent<Alert>) => {
      showAlertNotification(event.detail, onDismiss, onView)
    }

    window.addEventListener('new-alert' as any, handleNewAlert)

    return () => {
      window.removeEventListener('new-alert' as any, handleNewAlert)
    }
  }, [enabled, onDismiss, onView])
}

/**
 * Utility to trigger a new alert notification
 */
export function triggerAlertNotification(alert: Alert) {
  const event = new CustomEvent('new-alert', { detail: alert })
  window.dispatchEvent(event)
}
