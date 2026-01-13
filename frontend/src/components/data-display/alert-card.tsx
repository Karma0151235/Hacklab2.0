import { format } from 'date-fns'
import { AlertTriangle, CheckCircle2, Eye, X } from 'lucide-react'
import Link from 'next/link'
import { Alert } from '@/lib/types/api'
import { cn } from '@/lib/utils'

interface AlertCardProps {
  alert: Alert
  onDismiss?: (alertId: string) => void
  onMarkAsRead?: (alertId: string) => void
  className?: string
}

const severityStyles = {
  high: {
    border: 'border-error/40',
    bg: 'bg-error/5',
    iconBg: 'bg-error/10',
    iconColor: 'text-error',
    badge: 'bg-error/20 text-error border-error/40',
    glow: 'hover:shadow-[0_0_20px_rgba(255,68,68,0.15)]',
  },
  medium: {
    border: 'border-warning/40',
    bg: 'bg-warning/5',
    iconBg: 'bg-warning/10',
    iconColor: 'text-warning',
    badge: 'bg-warning/20 text-warning border-warning/40',
    glow: 'hover:shadow-[0_0_20px_rgba(255,170,0,0.15)]',
  },
  low: {
    border: 'border-info/40',
    bg: 'bg-info/5',
    iconBg: 'bg-info/10',
    iconColor: 'text-info',
    badge: 'bg-info/20 text-info border-info/40',
    glow: 'hover:shadow-[0_0_20px_rgba(0,170,255,0.15)]',
  },
}

const statusIcons = {
  active: AlertTriangle,
  reviewed: CheckCircle2,
  dismissed: X,
}

export function AlertCard({
  alert,
  onDismiss,
  onMarkAsRead,
  className,
}: AlertCardProps) {
  const styles = severityStyles[alert.severity]
  const StatusIcon = statusIcons[alert.status]

  return (
    <div
      className={cn(
        'group relative overflow-hidden rounded-[var(--radius)] border bg-gradient-to-br from-bg-tertiary to-bg-secondary',
        'transition-all duration-300',
        styles.border,
        styles.glow,
        className
      )}
    >
      {/* Left severity indicator */}
      <div
        className={cn(
          'absolute inset-y-0 left-0 w-1.5',
          alert.severity === 'high' && 'bg-error',
          alert.severity === 'medium' && 'bg-warning',
          alert.severity === 'low' && 'bg-info'
        )}
      />

      <div className={cn('p-4 pl-5', styles.bg)}> {/* Compact padding, compensated for left bar */}
        {/* Header */}
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div className={cn('mt-0.5 rounded-lg p-2', styles.iconBg)}>
              <StatusIcon className={cn('h-4 w-4', styles.iconColor)} />
            </div>

            <div className="flex-1">
              {/* Alert Type & Company */}
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <h3 className="font-sans text-base font-bold text-text-primary">
                  {alert.alert_type}
                </h3>
                <span className="font-mono text-xs text-text-tertiary">
                  {alert.company_code}
                </span>
              </div>

              {/* Company Name */}
              <p className="font-sans text-sm font-medium text-text-secondary">
                {alert.company_name}
              </p>
            </div>
          </div>

          {/* Severity & Status Badges */}
          <div className="flex flex-col items-end gap-1.5">
            <span
              className={cn(
                'rounded-md border px-2.5 py-0.5 font-mono text-xs font-bold uppercase tracking-wide',
                styles.badge
              )}
            >
              {alert.severity}
            </span>
            <span className="rounded-md border border-border-secondary bg-bg-elevated px-2 py-0.5 font-mono text-xs font-semibold uppercase tracking-wide text-text-tertiary">
              {alert.status}
            </span>
          </div>
        </div>

        {/* Reason - Prominent enough for reading but secondary to title */}
        <p className="mb-3 font-sans text-sm leading-relaxed text-text-primary/90">
          {alert.reason}
        </p>

        {/* Evidence Count */}
        {alert.evidence.length > 0 && (
          <div className="mb-3 flex items-center gap-2">
            <div className="h-px flex-1 bg-border-secondary/50" />
            <span className="font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
              {alert.evidence.length}{' '}
              {alert.evidence.length === 1 ? 'citation' : 'citations'}
            </span>
            <div className="h-px flex-1 bg-border-secondary/50" />
          </div>
        )}

        {/* Footer */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Timestamp */}
          <time className="font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
            {format(new Date(alert.triggered_at), 'dd MMM yyyy, HH:mm')}
          </time>

          {/* Actions - Consistent Buttons */}
          <div className="flex items-center gap-2">
            {alert.status === 'active' && onMarkAsRead && (
              <button
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  onMarkAsRead(alert.alert_id)
                }}
                className="btn-secondary px-3 py-1.5 text-xs h-auto bg-bg-primary hover:bg-bg-elevated hover:text-success hover:border-success/30 flex items-center gap-2"
              >
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span>Mark Read</span>
              </button>
            )}

            {onDismiss && alert.status !== 'dismissed' && (
              <button
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  onDismiss(alert.alert_id)
                }}
                className="btn-secondary px-3 py-1.5 text-xs h-auto bg-bg-primary hover:bg-bg-elevated hover:text-error hover:border-error/30 flex items-center gap-2"
              >
                <X className="h-3.5 w-3.5" />
                <span>Dismiss</span>
              </button>
            )}

            <Link
              href={`/alerts/${alert.alert_id}`}
              className="btn-primary px-4 py-1.5 text-xs h-auto flex items-center gap-2 shadow-lg shadow-accent-primary/20"
            >
              <Eye className="h-3.5 w-3.5" />
              <span>View Details</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
