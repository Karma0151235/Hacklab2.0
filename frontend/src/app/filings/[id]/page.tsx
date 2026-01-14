'use client'

import { useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import { ArrowLeft, Calendar, FileText, Loader2 } from 'lucide-react'
import Link from 'next/link'
import { Filing } from '@/lib/types/api'
import { getFilings } from '@/lib/api/vectordb'
import { format } from 'date-fns'

export default function FilingDetailPage() {
  const params = useParams()
  const filingId = decodeURIComponent(params.id as string)
  
  const [filing, setFiling] = useState<Filing | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchFiling() {
      setIsLoading(true)
      setError(null)
      
      try {
        // Fetch all filings and find the matching one
        const filings = await getFilings({ limit: 1000 })
        const matchingFiling = filings.find((f) => f.filing_id === filingId)
        
        if (matchingFiling) {
          setFiling(matchingFiling as Filing)
        } else {
          setError('Filing not found')
        }
      } catch (err) {
        console.error('Failed to fetch filing:', err)
        setError('Failed to load filing details')
      } finally {
        setIsLoading(false)
      }
    }
    
    fetchFiling()
  }, [filingId])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-primary p-8">
        <div className="mx-auto max-w-4xl">
          <div className="flex min-h-[400px] items-center justify-center">
            <div className="text-center">
              <Loader2 className="mx-auto h-12 w-12 animate-spin text-accent-primary" />
              <p className="mt-4 font-sans text-lg text-text-secondary">
                Loading filing details...
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !filing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-primary p-8">
        <div className="mx-auto max-w-4xl">
          <Link
            href="/filings"
            className="mb-6 inline-flex items-center gap-2 font-mono text-sm font-semibold text-accent-primary transition-colors hover:text-accent-secondary"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Filings
          </Link>
          
          <div className="rounded-lg border border-error/40 bg-bg-secondary p-8 text-center">
            <FileText className="mx-auto mb-4 h-16 w-16 text-error opacity-50" />
            <h3 className="mb-2 font-sans text-xl font-semibold text-text-primary">
              {error || 'Filing Not Found'}
            </h3>
            <p className="font-sans text-sm text-text-tertiary">
              The filing you're looking for doesn't exist or has been removed.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-primary p-8">
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Back Button */}
        <Link
          href="/filings"
          className="inline-flex items-center gap-2 font-mono text-sm font-semibold text-accent-primary transition-colors hover:text-accent-secondary"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Filings
        </Link>

        {/* Filing Header */}
        <div className="rounded-lg border border-border-primary bg-gradient-to-br from-bg-tertiary to-bg-secondary p-8">
          {/* Date & Company */}
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <time className="mb-2 block font-mono text-xs font-bold uppercase tracking-wider text-accent-primary">
                {format(new Date(filing.announcement_date), 'dd MMM yyyy, HH:mm')}
              </time>
              <h2 className="font-sans text-2xl font-bold text-text-primary">
                {filing.company_name}
              </h2>
              <p className="mt-1 font-mono text-sm text-text-tertiary">
                {filing.company_code}
              </p>
            </div>
            
            {/* Document Type Badge */}
            <span className="rounded-md border border-border-secondary bg-bg-elevated px-3 py-1.5 font-mono text-xs font-bold uppercase tracking-wide text-text-secondary">
              {filing.document_type}
            </span>
          </div>

          {/* Title */}
          <h1 className="mb-4 font-sans text-3xl font-bold leading-tight text-text-primary">
            {filing.title}
          </h1>

          {/* Metadata */}
          <div className="flex flex-wrap items-center gap-3 border-t border-border-secondary pt-4">
            {/* Tables Count */}
            {filing.tables_count > 0 && (
              <div className="flex items-center gap-2 rounded-md border border-border-secondary bg-bg-elevated px-3 py-1.5">
                <FileText className="h-4 w-4 text-text-tertiary" />
                <span className="font-mono text-sm font-semibold text-text-secondary">
                  {filing.tables_count} {filing.tables_count === 1 ? 'table' : 'tables'}
                </span>
              </div>
            )}

            {/* Sentiment */}
            {filing.sentiment && (
              <span className="rounded-md border border-info/30 bg-info/15 px-3 py-1.5 font-mono text-xs font-bold uppercase tracking-wide text-info">
                {filing.sentiment}
              </span>
            )}
          </div>
        </div>

        {/* Summary */}
        {filing.summary && (
          <div className="rounded-lg border border-border-primary bg-gradient-to-br from-bg-tertiary to-bg-secondary p-6">
            <h3 className="mb-3 font-sans text-lg font-bold text-text-primary">
              Summary
            </h3>
            <p className="font-sans text-base leading-relaxed text-text-secondary">
              {filing.summary}
            </p>
          </div>
        )}

        {/* Keywords */}
        {filing.keywords.length > 0 && (
          <div className="rounded-lg border border-border-primary bg-gradient-to-br from-bg-tertiary to-bg-secondary p-6">
            <h3 className="mb-3 font-sans text-lg font-bold text-text-primary">
              Keywords
            </h3>
            <div className="flex flex-wrap gap-2">
              {filing.keywords.map((keyword) => (
                <span
                  key={keyword}
                  className="rounded-md border border-accent-primary/20 bg-accent-primary/5 px-3 py-1.5 font-mono text-sm font-medium text-accent-primary"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Placeholder for Future Content */}
        <div className="rounded-lg border border-border-primary bg-gradient-to-br from-bg-tertiary to-bg-secondary p-6">
          <h3 className="mb-3 font-sans text-lg font-bold text-text-primary">
            Full Document Content
          </h3>
          <p className="font-sans text-sm text-text-tertiary">
            Full document viewer and table extraction will be available in a future update.
          </p>
        </div>
      </div>
    </div>
  )
}
