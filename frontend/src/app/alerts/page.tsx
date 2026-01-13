'use client'

import { AlertTriangle, Filter } from 'lucide-react'
import { useState, useMemo } from 'react'
import { AlertCard } from '@/components/data-display/alert-card'
import { mockAlerts } from '@/lib/mock-data/alerts'
import { mockCompanies } from '@/lib/mock-data/companies'
import { cn } from '@/lib/utils'
import type { Alert } from '@/lib/types/api'

type SeverityFilter = 'all' | 'high' | 'medium' | 'low'
type StatusFilter = 'all' | 'active' | 'reviewed' | 'dismissed'

export default function AlertsPage() {
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>('all')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [companyFilter, setCompanyFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Filter alerts
  const filteredAlerts = useMemo(() => {
    return mockAlerts.filter((alert) => {
      // Severity filter
      if (severityFilter !== 'all' && alert.severity !== severityFilter) {
        return false
      }

      // Status filter
      if (statusFilter !== 'all' && alert.status !== statusFilter) {
        return false
      }

      // Company filter
      if (companyFilter !== 'all' && alert.company_code !== companyFilter) {
        return false
      }

      // Search query
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        return (
          alert.alert_type.toLowerCase().includes(query) ||
          alert.company_name.toLowerCase().includes(query) ||
          alert.company_code.toLowerCase().includes(query) ||
          alert.reason.toLowerCase().includes(query)
        )
      }

      return true
    })
  }, [severityFilter, statusFilter, companyFilter, searchQuery])

  // Sort by date (newest first) and severity
  const sortedAlerts = useMemo(() => {
    return [...filteredAlerts].sort((a, b) => {
      // First sort by severity
      const severityOrder = { high: 3, medium: 2, low: 1 }
      const severityDiff = severityOrder[b.severity] - severityOrder[a.severity]
      if (severityDiff !== 0) return severityDiff

      // Then by date
      return (
        new Date(b.triggered_at).getTime() - new Date(a.triggered_at).getTime()
      )
    })
  }, [filteredAlerts])

  // Calculate summary statistics
  const stats = useMemo(() => {
    const high = filteredAlerts.filter((a) => a.severity === 'high').length
    const medium = filteredAlerts.filter((a) => a.severity === 'medium').length
    const low = filteredAlerts.filter((a) => a.severity === 'low').length
    const active = filteredAlerts.filter((a) => a.status === 'active').length

    return { high, medium, low, active, total: filteredAlerts.length }
  }, [filteredAlerts])

  return (
    <div className="min-h-screen bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-primary">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Page Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="mb-2 font-sans text-4xl font-bold text-text-primary">
              Alert Dashboard
            </h1>
            <p className="font-sans text-lg text-text-secondary">
              {stats.active} active alerts requiring attention
            </p>
          </div>
        </div>

        {/* Summary Bar */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <div className="rounded-lg border border-error/30 bg-gradient-to-br from-error/5 to-bg-secondary p-4">
            <div className="mb-1 font-mono text-xs font-semibold uppercase tracking-wider text-error">
              High Severity
            </div>
            <div className="font-mono text-3xl font-bold text-error">
              {stats.high}
            </div>
          </div>

          <div className="rounded-lg border border-warning/30 bg-gradient-to-br from-warning/5 to-bg-secondary p-4">
            <div className="mb-1 font-mono text-xs font-semibold uppercase tracking-wider text-warning">
              Medium Severity
            </div>
            <div className="font-mono text-3xl font-bold text-warning">
              {stats.medium}
            </div>
          </div>

          <div className="rounded-lg border border-info/30 bg-gradient-to-br from-info/5 to-bg-secondary p-4">
            <div className="mb-1 font-mono text-xs font-semibold uppercase tracking-wider text-info">
              Low Severity
            </div>
            <div className="font-mono text-3xl font-bold text-info">
              {stats.low}
            </div>
          </div>

          <div className="rounded-lg border border-accent-primary/30 bg-gradient-to-br from-accent-primary/5 to-bg-secondary p-4">
            <div className="mb-1 font-mono text-xs font-semibold uppercase tracking-wider text-accent-primary">
              Total Alerts
            </div>
            <div className="font-mono text-3xl font-bold text-text-primary">
              {stats.total}
            </div>
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
                placeholder="Search by type, company, or reason..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-md border border-border-secondary bg-bg-elevated px-4 py-2.5 font-sans text-sm text-text-primary placeholder:text-text-tertiary focus:border-accent-primary/40 focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
              />
            </div>

            {/* Severity Filter */}
            <div>
              <label className="mb-2 block font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                Severity
              </label>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value as SeverityFilter)}
                className="w-full rounded-md border border-border-secondary bg-bg-elevated px-4 py-2.5 font-sans text-sm text-text-primary focus:border-accent-primary/40 focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
              >
                <option value="all">All Severities</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="mb-2 block font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
                className="w-full rounded-md border border-border-secondary bg-bg-elevated px-4 py-2.5 font-sans text-sm text-text-primary focus:border-accent-primary/40 focus:outline-none focus:ring-2 focus:ring-accent-primary/20"
              >
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="reviewed">Reviewed</option>
                <option value="dismissed">Dismissed</option>
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
                  setSeverityFilter('all')
                  setStatusFilter('all')
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
        {sortedAlerts.length === 0 ? (
          <div className="rounded-lg border border-border-primary bg-bg-secondary p-12 text-center">
            <AlertTriangle className="mx-auto mb-4 h-16 w-16 text-text-tertiary opacity-50" />
            <h3 className="mb-2 font-sans text-xl font-semibold text-text-primary">
              No alerts found
            </h3>
            <p className="font-sans text-sm text-text-tertiary">
              Try adjusting your filters or search criteria
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {sortedAlerts.map((alert) => (
              <AlertCard key={alert.alert_id} alert={alert} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
