'use client'

import { FileText, Filter, Calendar } from 'lucide-react'
import { useState, useMemo } from 'react'
import { TimelineCard } from '@/components/data-display/timeline-card'
import { mockFilings } from '@/lib/mock-data/filings'
import { mockCompanies } from '@/lib/mock-data/companies'
import { cn } from '@/lib/utils'
import { Filing } from '@/lib/types/api'

type SentimentFilter = 'all' | 'positive' | 'neutral' | 'negative'
type DocumentTypeFilter = 'all' | string

export default function FilingsPage() {
  const [sentimentFilter, setSentimentFilter] = useState<SentimentFilter>('all')
  const [documentTypeFilter, setDocumentTypeFilter] =
    useState<DocumentTypeFilter>('all')
  const [companyFilter, setCompanyFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Get unique document types
  const documentTypes = useMemo(() => {
    const types = new Set(mockFilings.map((f) => f.document_type))
    return Array.from(types).sort()
  }, [])

  // Filter filings
  const filteredFilings = useMemo(() => {
    return mockFilings.filter((filing) => {
      // Sentiment filter
      if (sentimentFilter !== 'all' && filing.sentiment !== sentimentFilter) {
        return false
      }

      // Document type filter
      if (
        documentTypeFilter !== 'all' &&
        filing.document_type !== documentTypeFilter
      ) {
        return false
      }

      // Company filter
      if (companyFilter !== 'all' && filing.company_code !== companyFilter) {
        return false
      }

      // Search query
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        return (
          filing.title.toLowerCase().includes(query) ||
          filing.company_name.toLowerCase().includes(query) ||
          filing.company_code.toLowerCase().includes(query) ||
          filing.summary?.toLowerCase().includes(query) ||
          filing.keywords.some((k) => k.toLowerCase().includes(query))
        )
      }

      return true
    })
  }, [sentimentFilter, documentTypeFilter, companyFilter, searchQuery])

  // Sort by date (newest first)
  const sortedFilings = useMemo(() => {
    return [...filteredFilings].sort(
      (a, b) =>
        new Date(b.announcement_date).getTime() -
        new Date(a.announcement_date).getTime()
    )
  }, [filteredFilings])

  return (
    <div className="min-h-screen bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-primary p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Page Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="mb-2 font-sans text-4xl font-bold text-text-primary">
              Filings Timeline
            </h1>
            <p className="font-sans text-lg text-text-secondary">
              {sortedFilings.length} filings found
            </p>
          </div>
        </div>

        {/* Filters Section */}
        <div className="rounded-lg border border-border-accent/20 bg-gradient-to-br from-bg-tertiary to-bg-secondary p-6">
          <div className="mb-4 flex items-center gap-2">
            <Filter className="h-5 w-5 text-accent-primary" />
            <h2 className="font-sans text-lg font-bold text-text-primary">
              Filters
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* Search */}
            <div className="lg:col-span-2">
              <label className="mb-2 block font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                Search
              </label>
              <input
                type="text"
                placeholder="Search by title, company, or keyword..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-md border border-border-secondary bg-bg-elevated px-4 py-2.5 font-sans text-sm text-text-primary placeholder:text-text-tertiary focus:border-accent-primary/40 focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
              />
            </div>

            {/* Sentiment Filter */}
            <div>
              <label className="mb-2 block font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                Sentiment
              </label>
              <select
                value={sentimentFilter}
                onChange={(e) =>
                  setSentimentFilter(e.target.value as SentimentFilter)
                }
                className="w-full rounded-md border border-border-secondary bg-bg-elevated px-4 py-2.5 font-sans text-sm text-text-primary focus:border-accent-primary/40 focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
              >
                <option value="all">All Sentiments</option>
                <option value="positive">Positive</option>
                <option value="neutral">Neutral</option>
                <option value="negative">Negative</option>
              </select>
            </div>

            {/* Document Type Filter */}
            <div>
              <label className="mb-2 block font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                Document Type
              </label>
              <select
                value={documentTypeFilter}
                onChange={(e) => setDocumentTypeFilter(e.target.value)}
                className="w-full rounded-md border border-border-secondary bg-bg-elevated px-4 py-2.5 font-sans text-sm text-text-primary focus:border-accent-primary/40 focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
              >
                <option value="all">All Types</option>
                {documentTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </div>

            {/* Company Filter */}
            <div className="lg:col-span-2">
              <label className="mb-2 block font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                Company
              </label>
              <select
                value={companyFilter}
                onChange={(e) => setCompanyFilter(e.target.value)}
                className="w-full rounded-md border border-border-secondary bg-bg-elevated px-4 py-2.5 font-sans text-sm text-text-primary focus:border-accent-primary/40 focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
              >
                <option value="all">All Companies</option>
                {mockCompanies
                  .sort((a, b) => a.company_name.localeCompare(b.company_name))
                  .map((company) => (
                    <option key={company.company_code} value={company.company_code}>
                      {company.company_name} ({company.ticker})
                    </option>
                  ))}
              </select>
            </div>

            {/* Reset Button */}
            <div className="flex items-end lg:col-span-2">
              <button
                onClick={() => {
                  setSentimentFilter('all')
                  setDocumentTypeFilter('all')
                  setCompanyFilter('all')
                  setSearchQuery('')
                }}
                className="w-full rounded-md border border-border-secondary bg-bg-elevated px-4 py-2.5 font-mono text-sm font-semibold text-text-secondary transition-all hover:border-error/40 hover:text-error"
              >
                Reset Filters
              </button>
            </div>
          </div>
        </div>

        {/* Results */}
        {sortedFilings.length === 0 ? (
          <div className="rounded-lg border border-border-primary bg-bg-secondary p-12 text-center">
            <FileText className="mx-auto mb-4 h-16 w-16 text-text-tertiary opacity-50" />
            <h3 className="mb-2 font-sans text-xl font-semibold text-text-primary">
              No filings found
            </h3>
            <p className="font-sans text-sm text-text-tertiary">
              Try adjusting your filters or search criteria
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {sortedFilings.map((filing) => (
              <TimelineCard key={filing.filing_id} filing={filing} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
