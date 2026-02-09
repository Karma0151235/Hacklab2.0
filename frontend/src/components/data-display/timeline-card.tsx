import { format } from 'date-fns'
import { ExternalLink, FileText } from 'lucide-react'
import Link from 'next/link'
import { Filing } from '@/lib/types/api'
import { cn } from '@/lib/utils'

interface TimelineCardProps {
  filing: Filing
  showCompanyName?: boolean
  showFullTitle?: boolean
  className?: string
}

const sentimentStyles = {
  positive: {
    badge: 'bg-success/15 text-success border-success/30',
    dot: 'bg-success',
  },
  neutral: {
    badge: 'bg-info/15 text-info border-info/30',
    dot: 'bg-info',
  },
  negative: {
    badge: 'bg-error/15 text-error border-error/30',
    dot: 'bg-error',
  },
}

export function TimelineCard({
  filing,
  showCompanyName = true,
  showFullTitle = false,
  className,
}: TimelineCardProps) {
  const sentimentStyle = filing.sentiment
    ? sentimentStyles[filing.sentiment]
    : sentimentStyles.neutral

  return (
    <Link
      href={`/filings/${encodeURIComponent(filing.filing_id)}`}
      className={cn(
        'group relative block overflow-hidden rounded-[var(--radius)] border border-border-primary bg-gradient-to-br from-bg-tertiary to-bg-secondary',
        'transition-all duration-300 hover:border-accent-primary/40 hover:shadow-[0_0_20px_rgba(0,217,255,0.1)]',
        className
      )}
    >
      {/* Left accent bar */}
      <div className="absolute inset-y-0 left-0 w-1 bg-gradient-to-b from-accent-primary/50 to-accent-secondary/50 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

      <div className="p-8"> {/* Increased padding */}
        {/* Header */}
        <div className="mb-3 flex items-start justify-between gap-3">
          <div className="flex-1">
            {/* Date */}
            <time className="mb-1.5 block font-mono text-xs font-bold uppercase tracking-wider text-accent-primary">
              {format(new Date(filing.announcement_date), 'dd MMM yyyy, HH:mm')}
            </time>

            {/* Company Name */}
            {showCompanyName && (
              <p className="mb-0.5 font-sans text-sm font-semibold text-text-secondary group-hover:text-text-primary transition-colors">
                {filing.company_name}
                <span className="ml-2 font-mono text-xs text-text-secondary">
                  {filing.company_code}
                </span>
              </p>
            )}
          </div>

          {/* Document Type Badge */}
          <div className="flex items-center gap-2">
            <span className="rounded-md border border-border-secondary bg-bg-elevated px-2 py-0.5 font-mono text-xs font-bold uppercase tracking-wide text-text-secondary">
              {filing.document_type}
            </span>
          </div>
        </div>

        {/* Title - Full or Truncated */}
        <h3 className={cn(
          "mb-2 font-sans text-base font-bold leading-snug text-text-primary transition-colors group-hover:text-accent-primary",
          !showFullTitle && "line-clamp-2"
        )}>
          {filing.title}
        </h3>

        {/* Summary - Readable Gray */}
        {filing.summary && (
          <p className="mb-3 line-clamp-2 font-sans text-sm leading-relaxed text-text-secondary">
            {filing.summary}
          </p>
        )}

        {/* Footer */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Sentiment */}
          {filing.sentiment && (
            <div className="flex items-center gap-2">
              <div
                className={cn('h-2 w-2 rounded-full', sentimentStyle.dot)}
              />
              <span
                className={cn(
                  'rounded-md border px-2 py-0.5 font-mono text-xs font-bold uppercase tracking-wide',
                  sentimentStyle.badge
                )}
              >
                {filing.sentiment}
              </span>
            </div>
          )}

          {/* Tables Count */}
          {filing.tables_count > 0 && (
            <div className="flex items-center gap-1.5 rounded-md border border-border-secondary bg-bg-elevated px-2 py-0.5 transition-colors group-hover:border-border-accent/30">
              <FileText className="h-3 w-3 text-text-secondary" />
              <span className="font-mono text-xs font-semibold text-text-secondary">
                {filing.tables_count} {filing.tables_count === 1 ? 'table' : 'tables'}
              </span>
            </div>
          )}

          {/* Keywords */}
          {filing.keywords.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {filing.keywords.slice(0, 3).map((keyword) => (
                <span
                  key={keyword}
                  className="rounded-md bg-accent-primary/5 px-2 py-0.5 font-mono text-xs font-medium text-accent-primary/80 border border-transparent group-hover:border-accent-primary/20"
                >
                  {keyword}
                </span>
              ))}
              {filing.keywords.length > 3 && (
                <span className="rounded-md bg-bg-elevated px-2 py-0.5 font-mono text-xs text-text-tertiary">
                  +{filing.keywords.length - 3}
                </span>
              )}
            </div>
          )}

          {/* View Link */}
          <div className="ml-auto flex items-center gap-1.5 font-mono text-xs font-bold text-accent-primary opacity-0 transition-opacity group-hover:opacity-100">
            <span>View Details</span>
            <ExternalLink className="h-3 w-3" />
          </div>
        </div>
      </div>
    </Link>
  )
}
