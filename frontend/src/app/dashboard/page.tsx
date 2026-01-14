import { Suspense } from 'react'
import {
  AlertTriangle,
  Building2,
  FileText,
} from 'lucide-react'
import Link from 'next/link'
import { MetricCard } from '@/components/data-display/metric-card'
import { TimelineCard } from '@/components/data-display/timeline-card'
import { AlertCard } from '@/components/data-display/alert-card'
import { getCompanies } from '@/lib/api/companies'
import { getFilings } from '@/lib/api/filings'
import { getAlerts } from '@/lib/api/alerts'

async function DashboardContent() {
  // Fetch data from API
  const [companies, filings, alerts] = await Promise.all([
    getCompanies(),
    getFilings(),
    getAlerts(),
  ])

  // Calculate metrics from real data
  const totalCompanies = companies.length
  const totalFilings = filings.length
  const activeAlerts = alerts.filter((a) => a.status === 'active').length

  // Get recent data (latest 5 filings)
  const recentFilings = filings
    .sort(
      (a, b) =>
        new Date(b.announcement_date).getTime() -
        new Date(a.announcement_date).getTime()
    )
    .slice(0, 5)

  const recentAlerts = alerts
    .filter((a) => a.status === 'active')
    .sort(
      (a, b) =>
        new Date(b.triggered_at).getTime() - new Date(a.triggered_at).getTime()
    )
    .slice(0, 3)

  return (
    <div className="space-y-6">
      {/* Page Header */}
        <div className="mb-6">
          <h1 className="mb-1 font-sans text-2xl font-bold text-text-primary">
            Dashboard Overview
          </h1>
          <p className="font-sans text-sm text-text-secondary">
            Financial Intelligence & Compliance Monitoring
          </p>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          <MetricCard
            label="Total Companies"
            value={totalCompanies}
            icon={Building2}
            variant="default"
          />
          <MetricCard
            label="Total Filings"
            value={totalFilings}
            icon={FileText}
            variant="default"
          />
          <MetricCard
            label="Active Alerts"
            value={activeAlerts}
            icon={AlertTriangle}
            variant={activeAlerts > 10 ? 'error' : 'success'}
          />
        </div>

                {/* Quick Actions */}
        <div className="rounded-lg border border-border-accent/20 bg-gradient-to-br from-bg-tertiary to-bg-secondary p-4">
          <h2 className="mb-3 font-sans text-lg font-bold text-text-primary">
            Quick Actions
          </h2>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <Link
              href="/copilot"
              className="group flex items-center gap-3 rounded-lg border border-border-secondary bg-bg-elevated p-3 transition-all hover:border-accent-primary/40 hover:shadow-[0_0_20px_rgba(0,217,255,0.1)]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-primary/10">
                <svg
                  className="h-5 w-5 text-accent-primary"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                  />
                </svg>
              </div>
              <div>
                <h3 className="font-sans text-sm font-semibold text-text-primary group-hover:text-accent-primary">
                  Ask Copilot
                </h3>
                <p className="font-sans text-xs text-text-tertiary">
                  Get AI-powered insights
                </p>
              </div>
            </Link>

            <Link
              href="/companies"
              className="group flex items-center gap-3 rounded-lg border border-border-secondary bg-bg-elevated p-3 transition-all hover:border-accent-primary/40 hover:shadow-[0_0_20px_rgba(0,217,255,0.1)]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-primary/10">
                <Building2 className="h-5 w-5 text-accent-primary" />
              </div>
              <div>
                <h3 className="font-sans text-sm font-semibold text-text-primary group-hover:text-accent-primary">
                  Browse Companies
                </h3>
                <p className="font-sans text-xs text-text-tertiary">
                  View all monitored entities
                </p>
              </div>
            </Link>

            <Link
              href="/ingest/upload"
              className="group flex items-center gap-3 rounded-lg border border-border-secondary bg-bg-elevated p-3 transition-all hover:border-accent-primary/40 hover:shadow-[0_0_20px_rgba(0,217,255,0.1)]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-primary/10">
                <svg
                  className="h-5 w-5 text-accent-primary"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
              </div>
              <div>
                <h3 className="font-sans text-sm font-semibold text-text-primary group-hover:text-accent-primary">
                  Upload Files
                </h3>
                <p className="font-sans text-xs text-text-tertiary">
                  Ingest new documents
                </p>
              </div>
            </Link>
          </div>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {/* Recent Filings */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-sans text-lg font-bold text-text-primary">
                Recent Filings
              </h2>
              <Link
                href="/filings"
                className="font-mono text-sm font-semibold text-accent-primary transition-colors hover:text-accent-secondary"
              >
                View All →
              </Link>
            </div>

            <div className="space-y-3">
              {recentFilings.map((filing) => (
                <TimelineCard key={filing.filing_id} filing={filing} />
              ))}
            </div>
          </div>

          {/* Recent Alerts */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="font-sans text-lg font-bold text-text-primary">
                Active Alerts
              </h2>
              <Link
                href="/alerts"
                className="font-mono text-sm font-semibold text-accent-primary transition-colors hover:text-accent-secondary"
              >
                View All →
              </Link>
            </div>

            <div className="space-y-3">
              {recentAlerts.length === 0 ? (
                <div className="rounded-lg border border-border-primary bg-bg-secondary p-8 text-center">
                  <AlertTriangle className="mx-auto mb-3 h-10 w-10 text-text-tertiary opacity-50" />
                  <p className="font-sans text-sm text-text-tertiary">
                    No active alerts at this time
                  </p>
                </div>
              ) : (
                recentAlerts.map((alert) => (
                  <AlertCard key={alert.alert_id} alert={alert} />
                ))
              )}
            </div>
          </div>
        </div>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-bg-primary">
          <div className="text-center">
            <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-accent-primary/20 border-t-accent-primary" />
            <p className="font-mono text-sm text-text-tertiary">
              Loading dashboard...
            </p>
          </div>
        </div>
      }
    >
      <DashboardContent />
    </Suspense>
  )
}
