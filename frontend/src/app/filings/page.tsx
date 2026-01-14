'use client'

import { FileText, Filter, Calendar, Loader2, ArrowUpDown } from 'lucide-react'
import { useState, useMemo, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { TimelineCard } from '@/components/data-display/timeline-card'
import { getFilings } from '@/lib/api/vectordb'
import { cn } from '@/lib/utils'
import { Filing } from '@/lib/types/api'

type DocumentTypeFilter = 'all' | string
type SortOrder = 'newest' | 'oldest'

export default function FilingsPage() {
  const router = useRouter()
  const [documentTypeFilter, setDocumentTypeFilter] =
    useState<DocumentTypeFilter>('all')
  const [companyFilter, setCompanyFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortOrder, setSortOrder] = useState<SortOrder>('newest')
  const [filings, setFilings] = useState<Filing[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch filings from vector database
  useEffect(() => {
    async function fetchFilings() {
      setIsLoading(true)
      setError(null)
      try {
        const data = await getFilings({ limit: 500 })
        setFilings(data as Filing[])
      } catch (err) {
        console.error('Failed to fetch filings:', err)
        setError('Failed to load filings from database')
      } finally {
        setIsLoading(false)
      }
    }
    fetchFilings()
  }, [])

  // Get unique document types
  const documentTypes = useMemo(() => {
    const types = new Set(filings.map((f) => f.document_type))
    return Array.from(types).sort()
  }, [filings])

  // Get unique companies
  const companies = useMemo(() => {
    const companiesMap = new Map<string, { code: string; name: string }>()
    filings.forEach((f) => {
      if (!companiesMap.has(f.company_code)) {
        companiesMap.set(f.company_code, {
          code: f.company_code,
          name: f.company_name,
        })
      }
    })
    return Array.from(companiesMap.values()).sort((a, b) => 
      a.name.localeCompare(b.name)
    )
  }, [filings])

  // Filter filings
  const filteredFilings = useMemo(() => {
    return filings.filter((filing) => {
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
  }, [filings, documentTypeFilter, companyFilter, searchQuery])

  // Sort by date
  const sortedFilings = useMemo(() => {
    return [...filteredFilings].sort((a, b) => {
      const dateA = new Date(a.announcement_date).getTime()
      const dateB = new Date(b.announcement_date).getTime()
      return sortOrder === 'newest' ? dateB - dateA : dateA - dateB
    })
  }, [filteredFilings, sortOrder])

  // Handle filing click
  const handleFilingClick = (filing: Filing) => {
    // URL-encode filing_id to handle special characters (?, ., etc.)
    router.push(`/filings/${encodeURIComponent(filing.filing_id)}`)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-primary p-8">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Loading State */}
        {isLoading && (
          <div className="flex min-h-[400px] items-center justify-center">
            <div className="text-center">
              <Loader2 className="mx-auto h-12 w-12 animate-spin text-accent-primary" />
              <p className="mt-4 font-sans text-lg text-text-secondary">
                Loading filings from database...
              </p>
            </div>
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="rounded-lg border border-error/40 bg-bg-secondary p-8 text-center">
            <FileText className="mx-auto mb-4 h-16 w-16 text-error opacity-50" />
            <h3 className="mb-2 font-sans text-xl font-semibold text-text-primary">
              Error Loading Filings
            </h3>
            <p className="font-sans text-sm text-text-tertiary">{error}</p>
          </div>
        )}

        {/* Main Content */}
        {!isLoading && !error && (
          <>
            {/* Page Header */}
            <div className="flex items-start justify-between">
              <div>
                <h1 className="mb-2 font-sans text-4xl font-bold text-text-primary">
                  Filings Timeline
                </h1>
                <p className="font-sans text-lg text-text-secondary">
                  {sortedFilings.length} filing{sortedFilings.length !== 1 ? 's' : ''} found
                </p>
              </div>
              
              {/* Sort Toggle */}
              <button
                onClick={() => setSortOrder(sortOrder === 'newest' ? 'oldest' : 'newest')}
                className="flex items-center gap-2 rounded-lg border border-border-secondary bg-bg-tertiary px-4 py-2.5 font-mono text-sm font-semibold text-text-primary transition-all hover:border-accent-primary/40 hover:bg-bg-elevated"
              >
                <Calendar className="h-4 w-4" />
                {sortOrder === 'newest' ? 'Newest First' : 'Oldest First'}
                <ArrowUpDown className="h-4 w-4" />
              </button>
            </div>

            {/* Compact Filters Section */}
            <div className="rounded-lg border border-border-accent/20 bg-gradient-to-br from-bg-tertiary to-bg-secondary p-4">
              <div className="mb-3 flex items-center gap-2">
                <Filter className="h-4 w-4 text-accent-primary" />
                <h2 className="font-sans text-sm font-bold text-text-primary">
                  Filters
                </h2>
              </div>

              <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                {/* Search */}
                <div>
                  <input
                    type="text"
                    placeholder="Search filings..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full rounded-md border border-border-secondary bg-bg-elevated px-3 py-2 font-sans text-sm text-text-primary placeholder:text-text-tertiary focus:border-accent-primary/40 focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
                  />
                </div>

                {/* Company Filter */}
                <div>
                  <select
                    value={companyFilter}
                    onChange={(e) => setCompanyFilter(e.target.value)}
                    className="w-full rounded-md border border-border-secondary bg-bg-elevated px-3 py-2 font-sans text-sm text-text-primary focus:border-accent-primary/40 focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
                  >
                    <option value="all">All Companies</option>
                    {companies.map((company) => (
                      <option key={company.code} value={company.code}>
                        {company.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Document Type Filter */}
                <div>
                  <select
                    value={documentTypeFilter}
                    onChange={(e) => setDocumentTypeFilter(e.target.value)}
                    className="w-full rounded-md border border-border-secondary bg-bg-elevated px-3 py-2 font-sans text-sm text-text-primary focus:border-accent-primary/40 focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
                  >
                    <option value="all">All Types</option>
                    {documentTypes.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Reset Button */}
              {(searchQuery || companyFilter !== 'all' || documentTypeFilter !== 'all') && (
                <div className="mt-3">
                  <button
                    onClick={() => {
                      setDocumentTypeFilter('all')
                      setCompanyFilter('all')
                      setSearchQuery('')
                    }}
                    className="rounded-md border border-border-secondary bg-bg-elevated px-3 py-1.5 font-mono text-xs font-semibold text-text-secondary transition-all hover:border-error/40 hover:text-error"
                  >
                    Reset Filters
                  </button>
                </div>
              )}
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
              <div className="space-y-3">
                {sortedFilings.map((filing) => (
                  <div
                    key={filing.filing_id}
                    onClick={() => handleFilingClick(filing)}
                    className="cursor-pointer transition-transform hover:scale-[1.01]"
                  >
                    <TimelineCard filing={filing} showFullTitle />
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
