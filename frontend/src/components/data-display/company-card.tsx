import { AlertCircle, FileText, TrendingUp } from 'lucide-react'
import Link from 'next/link'
import { Company } from '@/lib/types/api'
import { cn } from '@/lib/utils'

interface CompanyCardProps {
  company: Company
  className?: string
  onAlertClick?: (companyCode: string) => void
}

export function CompanyCard({ company, className, onAlertClick }: CompanyCardProps) {
  // Calculate health score color
  const getHealthScoreColor = (score?: number) => {
    if (!score) return 'text-text-tertiary'
    if (score >= 75) return 'text-success'
    if (score >= 50) return 'text-warning'
    return 'text-error'
  }

  const healthScoreColor = getHealthScoreColor(company.financial_health_score)

  return (
    <Link
      href={`/companies/${company.company_code}`}
      className={cn(
        'group relative block overflow-hidden rounded-lg border border-border-primary',
        'bg-gradient-to-br from-bg-tertiary to-bg-secondary',
        'transition-all duration-300 hover:border-accent-primary/40 hover:shadow-[0_0_20px_rgba(0,217,255,0.1)]',
        className
      )}
    >
      {/* Top accent line */}
      <div className="h-1 w-full bg-gradient-to-r from-accent-primary/0 via-accent-primary/50 to-accent-primary/0 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

      <div className="p-4">
        {/* Header */}
        <div className="mb-3">
          {/* Ticker */}
          <div className="mb-1.5 flex items-start justify-between gap-3">
            <span className="font-mono text-sm font-bold uppercase tracking-wider text-accent-primary">
              {company.ticker}
            </span>
            <span className="font-mono text-xs text-text-tertiary">
              {company.company_code}
            </span>
          </div>

          {/* Company Name */}
          <h3 className="mb-1 font-sans text-base font-bold leading-tight text-text-primary transition-colors group-hover:text-accent-primary">
            {company.company_name}
          </h3>

          {/* Sector - Temporarily hidden */}
          {/* <p className="font-sans text-xs font-medium text-text-secondary">
            {company.sector}
          </p> */}
        </div>

        {/* Market Cap - Temporarily hidden */}
        {/* {company.market_cap && (
          <div className="mb-3 rounded-md border border-border-secondary bg-bg-elevated p-2">
            <p className="mb-0.5 font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
              Market Cap
            </p>
            <p className="font-mono text-base font-bold text-text-primary">
              RM {(company.market_cap / 1000000000).toFixed(2)}B
            </p>
          </div>
        )} */}

        {/* Metrics Grid */}
        <div className="mb-3 grid grid-cols-2 gap-2">
          {/* Filings */}
          <div className="rounded-md border border-border-secondary bg-bg-elevated p-2">
            <div className="mb-0.5 flex items-center gap-1">
              <FileText className="h-3 w-3 text-text-tertiary" />
              <p className="font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                Filings
              </p>
            </div>
            <p className="font-mono text-base font-bold text-text-primary">
              {company.filings_count}
            </p>
          </div>

          {/* Alerts */}
          <button
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              if (company.alert_count > 0 && onAlertClick) {
                onAlertClick(company.company_code)
              }
            }}
            disabled={company.alert_count === 0 || !onAlertClick}
            className={cn(
              'rounded-md border border-border-secondary bg-bg-elevated p-2 transition-all text-left',
              company.alert_count > 0 && onAlertClick && 'cursor-pointer hover:border-error/40 hover:bg-error/5'
            )}
          >
            <div className="mb-0.5 flex items-center gap-1">
              <AlertCircle className="h-3 w-3 text-text-tertiary" />
              <p className="font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                Alerts
              </p>
            </div>
            <p
              className={cn(
                'font-mono text-base font-bold',
                company.alert_count > 0 ? 'text-error' : 'text-text-primary'
              )}
            >
              {company.alert_count}
            </p>
          </button>

          {/* Health Score - Temporarily hidden */}
          {/* <div className="rounded-md border border-border-secondary bg-bg-elevated p-2">
            <div className="mb-0.5 flex items-center gap-1">
              <TrendingUp className="h-3 w-3 text-text-tertiary" />
              <p className="font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                Health
              </p>
            </div>
            <p className={cn('font-mono text-base font-bold', healthScoreColor)}>
              {company.financial_health_score ?? 'N/A'}
            </p>
          </div> */}
        </div>

        {/* Latest Filing Date */}
        {company.latest_filing_date && (
          <div className="flex items-center justify-between border-t border-border-secondary pt-2">
            <span className="font-sans text-xs font-medium text-text-tertiary">
              Latest Filing
            </span>
            <time className="font-mono text-xs font-semibold text-accent-primary">
              {new Date(company.latest_filing_date).toLocaleDateString('en-GB', {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
              })}
            </time>
          </div>
        )}
      </div>
    </Link>
  )
}
