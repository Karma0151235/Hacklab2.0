'use client'

import { Search, Building2, Loader2 } from 'lucide-react'
import { useState, useMemo, useEffect } from 'react'
import Link from 'next/link'
import { CompanyCard } from '@/components/data-display/company-card'
import { DataTable } from '@/components/data-display/data-table'
import { getCompanies } from '@/lib/api/companies'
import { Company } from '@/lib/types/api'
import { cn } from '@/lib/utils'

type ViewMode = 'grid' | 'table'

export default function CompaniesPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [companies, setCompanies] = useState<Company[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch companies from API
  useEffect(() => {
    async function fetchCompanies() {
      setIsLoading(true)
      setError(null)
      try {
        const data = await getCompanies()
        setCompanies(data)
      } catch (err) {
        console.error('Failed to fetch companies:', err)
        setError('Failed to load companies')
      } finally {
        setIsLoading(false)
      }
    }
    fetchCompanies()
  }, [])

  // Filter companies based on search
  const filteredCompanies = useMemo(() => {
    if (!searchQuery) return companies

    const query = searchQuery.toLowerCase()
    return companies.filter(
      (company) =>
        company.company_name.toLowerCase().includes(query) ||
        company.ticker.toLowerCase().includes(query) ||
        company.company_code.toLowerCase().includes(query) ||
        company.sector.toLowerCase().includes(query)
    )
  }, [searchQuery, companies])

  // Table columns configuration
  const columns = [
    {
      key: 'ticker',
      label: 'Ticker',
      sortable: true,
      render: (company: Company) => (
        <Link
          href={`/companies/${company.company_code}`}
          className="font-mono font-bold text-accent-primary hover:text-accent-secondary"
        >
          {company.ticker}
        </Link>
      ),
    },
    {
      key: 'company_name',
      label: 'Company Name',
      sortable: true,
      render: (company: Company) => (
        <div>
          <p className="font-sans font-semibold text-text-primary">
            {company.company_name}
          </p>
          <p className="font-mono text-xs text-text-tertiary">
            {company.company_code}
          </p>
        </div>
      ),
    },
    // Temporarily hidden
    // {
    //   key: 'sector',
    //   label: 'Sector',
    //   sortable: true,
    //   render: (company: Company) => (
    //     <span className="font-sans text-text-secondary">{company.sector}</span>
    //   ),
    // },
    // {
    //   key: 'market_cap',
    //   label: 'Market Cap',
    //   sortable: true,
    //   render: (company: Company) =>
    //     company.market_cap ? (
    //       <span className="font-mono text-text-primary">
    //         RM {(company.market_cap / 1000000000).toFixed(2)}B
    //       </span>
    //     ) : (
    //       <span className="text-text-tertiary">N/A</span>
    //     ),
    // },
    {
      key: 'filings_count',
      label: 'Filings',
      sortable: true,
      render: (company: Company) => (
        <span className="font-mono font-semibold text-text-primary">
          {company.filings_count}
        </span>
      ),
      className: 'text-center',
    },
    {
      key: 'alert_count',
      label: 'Alerts',
      sortable: true,
      render: (company: Company) => (
        <span
          className={cn(
            'font-mono font-semibold',
            company.alert_count > 0 ? 'text-error' : 'text-text-tertiary'
          )}
        >
          {company.alert_count}
        </span>
      ),
      className: 'text-center',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Loading State */}
      {isLoading && (
        <div className="flex min-h-[400px] items-center justify-center">
          <div className="text-center">
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-accent-primary" />
            <p className="mt-4 font-sans text-lg text-text-secondary">
              Loading companies...
            </p>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && !isLoading && (
        <div className="rounded-lg border border-error/40 bg-bg-secondary p-8 text-center">
          <Building2 className="mx-auto mb-4 h-16 w-16 text-error opacity-50" />
          <h3 className="mb-2 font-sans text-xl font-semibold text-text-primary">
            Error Loading Companies
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
            <h1 className="mb-1 font-sans text-2xl font-bold text-text-primary">
              Companies
            </h1>
            <p className="font-sans text-sm text-text-secondary">
              {filteredCompanies.length} monitored entities
            </p>
          </div>

          {/* View Mode Toggle */}
          <div className="flex gap-2 rounded-lg border border-border-secondary bg-bg-secondary p-1">
            <button
              onClick={() => setViewMode('grid')}
              className={cn(
                'flex items-center gap-2 rounded-md px-3 py-2 font-mono text-xs font-semibold transition-all',
                viewMode === 'grid'
                  ? 'bg-accent-primary text-bg-primary'
                  : 'text-text-secondary hover:text-text-primary'
              )}
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                />
              </svg>
              Grid
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={cn(
                'flex items-center gap-2 rounded-md px-3 py-2 font-mono text-xs font-semibold transition-all',
                viewMode === 'table'
                  ? 'bg-accent-primary text-bg-primary'
                  : 'text-text-secondary hover:text-text-primary'
              )}
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
              Table
            </button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-tertiary" />
          <input
            type="text"
            placeholder="Search by name, ticker, code, or sector..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-border-secondary bg-bg-secondary py-3 pl-10 pr-4 font-sans text-sm text-text-primary placeholder:text-text-tertiary focus:border-accent-primary/40 focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
          />
        </div>

        {/* Companies Display */}
        {filteredCompanies.length === 0 ? (
          <div className="rounded-lg border border-border-primary bg-bg-secondary p-8 text-center">
            <Building2 className="mx-auto mb-3 h-12 w-12 text-text-tertiary opacity-50" />
            <h3 className="mb-1 font-sans text-base font-semibold text-text-primary">
              No companies found
            </h3>
            <p className="font-sans text-sm text-text-tertiary">
              Try adjusting your search criteria
            </p>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredCompanies.map((company) => (
              <CompanyCard key={company.company_code} company={company} />
            ))}
          </div>
        ) : (
          <DataTable
            data={filteredCompanies}
            columns={columns}
            keyExtractor={(company) => company.company_code}
            itemsPerPage={15}
          />
        )}
        </>
      )}
    </div>
  )
}
