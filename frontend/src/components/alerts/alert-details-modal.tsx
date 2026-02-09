'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { X, AlertTriangle, AlertCircle, AlertOctagon, Clock, Badge } from 'lucide-react'
import { Alert } from '@/lib/types/api'
import { cn } from '@/lib/utils'

interface AlertDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  alert: Alert | null
  companyName?: string
}

export function AlertDetailsModal({
  isOpen,
  onClose,
  alert,
  companyName,
}: AlertDetailsModalProps) {
  if (!alert) return null

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertOctagon className="h-5 w-5" />
      case 'medium':
        return <AlertTriangle className="h-5 w-5" />
      default:
        return <AlertCircle className="h-5 w-5" />
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'text-error bg-error/10'
      case 'medium':
        return 'text-warning bg-warning/10'
      default:
        return 'text-info bg-info/10'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 z-50 flex items-center justify-center bg-bg-primary/80 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 20 }}
            onClick={(e) => e.stopPropagation()}
            className="relative w-full max-w-2xl overflow-hidden rounded-2xl border border-border-secondary bg-bg-secondary shadow-2xl"
          >
            {/* Header */}
            <div className={cn(
              'border-b border-border-secondary px-6 py-4 flex items-start justify-between',
              alert.severity === 'high' && 'bg-error/5',
              alert.severity === 'medium' && 'bg-warning/5',
            )}>
              <div className="flex items-start gap-4">
                <div className={cn(
                  'flex h-12 w-12 items-center justify-center rounded-xl',
                  getSeverityColor(alert.severity)
                )}>
                  {getSeverityIcon(alert.severity)}
                </div>
                <div>
                  <h2 className="font-sans text-xl font-bold text-text-primary">
                    {alert.alert_type}
                  </h2>
                  <p className="font-sans text-sm text-text-secondary">
                    {companyName || alert.company_name}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="rounded-lg p-2 hover:bg-bg-tertiary transition-colors"
              >
                <X className="h-5 w-5 text-text-tertiary" />
              </button>
            </div>

            {/* Content */}
            <div className="space-y-4 p-6 max-h-[calc(100vh-200px)] overflow-y-auto">
              {/* Severity Badge */}
              <div className="flex items-center gap-2">
                <Badge className={cn(
                  'px-3 py-1 rounded-full text-xs font-semibold uppercase',
                  alert.severity === 'high' && 'bg-error/20 text-error',
                  alert.severity === 'medium' && 'bg-warning/20 text-warning',
                  alert.severity === 'low' && 'bg-info/20 text-info',
                )}>
                  {alert.severity} Severity
                </Badge>
                <span className={cn(
                  'px-3 py-1 rounded-full text-xs font-medium',
                  alert.status === 'active' && 'bg-error/10 text-error',
                  alert.status === 'reviewed' && 'bg-warning/10 text-warning',
                  alert.status === 'dismissed' && 'bg-bg-tertiary text-text-tertiary',
                )}>
                  {alert.status}
                </span>
              </div>

              {/* Reason/Description */}
              <div>
                <h3 className="mb-2 font-sans text-sm font-semibold text-text-primary">
                  Alert Reason
                </h3>
                <p className="font-sans text-sm text-text-secondary leading-relaxed">
                  {alert.reason}
                </p>
              </div>

              {/* Triggered At */}
              <div className="flex items-center gap-2 text-sm">
                <Clock className="h-4 w-4 text-text-tertiary" />
                <span className="font-sans text-text-secondary">
                  Triggered: {formatDate(alert.triggered_at)}
                </span>
              </div>

              {/* Evidence */}
              {alert.evidence && alert.evidence.length > 0 && (
                <div>
                  <h3 className="mb-3 font-sans text-sm font-semibold text-text-primary">
                    Supporting Evidence
                  </h3>
                  <div className="space-y-2">
                    {alert.evidence.map((item, index) => (
                      <div
                        key={index}
                        className="rounded-lg border border-border-secondary bg-bg-tertiary/40 p-3"
                      >
                        <div className="mb-1 flex items-center justify-between">
                          <p className="font-sans text-xs font-semibold text-text-primary">
                            {item.source}
                          </p>
                          {item.page && (
                            <span className="font-mono text-xs text-text-tertiary">
                              pg. {item.page}
                            </span>
                          )}
                        </div>
                        <p className="font-sans text-xs text-text-secondary leading-relaxed">
                          {item.excerpt}
                        </p>
                        {item.link && (
                          <a
                            href={item.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="mt-2 inline-block text-xs font-medium text-accent-primary hover:text-accent-secondary"
                          >
                            View source →
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="border-t border-border-secondary bg-bg-tertiary px-6 py-4 flex items-center justify-end gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 rounded-lg font-sans text-sm font-medium text-text-secondary hover:bg-bg-secondary transition-colors"
              >
                Close
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
