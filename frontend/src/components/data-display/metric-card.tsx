import { LucideIcon, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'

interface MetricCardProps {
  label: string
  value: string | number
  icon?: LucideIcon
  trend?: {
    value: number
    direction: 'up' | 'down' | 'stable'
    label?: string
  }
  variant?: 'default' | 'success' | 'warning' | 'error'
  className?: string
}

const variantStyles = {
  default: {
    border: 'border-border-accent/20',
    iconBg: 'bg-accent-primary/10',
    iconColor: 'text-accent-primary',
    trendUp: 'text-success', // Use new semantic color vars
    trendDown: 'text-error',
    trendStable: 'text-text-tertiary',
  },
  success: {
    border: 'border-success/30',
    iconBg: 'bg-success/10',
    iconColor: 'text-success',
    trendUp: 'text-success',
    trendDown: 'text-success/60',
    trendStable: 'text-success/40',
  },
  warning: {
    border: 'border-warning/30',
    iconBg: 'bg-warning/10',
    iconColor: 'text-warning',
    trendUp: 'text-warning',
    trendDown: 'text-error',
    trendStable: 'text-warning/60',
  },
  error: {
    border: 'border-error/30',
    iconBg: 'bg-error/10',
    iconColor: 'text-error',
    trendUp: 'text-warning',
    trendDown: 'text-error',
    trendStable: 'text-error/60',
  },
}

export function MetricCard({
  label,
  value,
  icon: Icon,
  trend,
  variant = 'default',
  className,
}: MetricCardProps) {
  const styles = variantStyles[variant]

  const getTrendColor = (direction: 'up' | 'down' | 'stable') => {
    switch (direction) {
      case 'up': return styles.trendUp
      case 'down': return styles.trendDown
      case 'stable': return styles.trendStable
    }
  }

  return (
    <div
      className={cn(
        'group relative overflow-hidden rounded-[var(--radius)] border bg-gradient-to-br from-bg-tertiary to-bg-secondary', // No default padding
        'transition-all duration-300 hover:border-accent-primary/40 hover:shadow-[0_0_20px_rgba(0,217,255,0.1)]',
        styles.border,
        className
      )}
    >
      {/* Background glow effect on hover */}
      <div className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
        <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-accent-primary/5 blur-2xl" />
      </div>

      <div className="relative flex items-start justify-between p-6">
        <div className="flex-1">
          {/* Label - Muted for hierarchy */}
          <p className="mb-1 font-sans text-xs font-medium uppercase tracking-wider text-text-secondary">
            {label}
          </p>

          {/* Value - Prominent */}
          <p className="font-mono text-2xl font-bold text-text-primary tracking-tight">
            {value}
          </p>

          {/* Trend */}
          {trend && (
            <div className="mt-2 flex items-center gap-2">
              {trend.direction === 'stable' ? (
                <Minus className={cn('h-3 w-3', getTrendColor(trend.direction))} />
              ) : (
                <svg
                  className={cn(
                    'h-3 w-3 transition-transform',
                    trend.direction === 'up' ? 'rotate-0' : 'rotate-180',
                    getTrendColor(trend.direction)
                  )}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                  />
                </svg>
              )}
              <span
                className={cn(
                  'font-mono text-xs font-semibold',
                  getTrendColor(trend.direction)
                )}
              >
                {Math.abs(trend.value)}%
              </span>
              <span className="font-sans text-xs font-medium text-text-secondary">
                {trend.label || 'vs last period'}
              </span>
            </div>
          )}
        </div>

        {/* Icon */}
        {Icon && (
          <div
            className={cn(
              'flex h-11 w-11 items-center justify-center rounded-xl ring-1 ring-white/5',
              styles.iconBg
            )}
          >
            <Icon className={cn('h-5 w-5', styles.iconColor)} />
          </div>
        )}
      </div>
    </div>
  )
}
