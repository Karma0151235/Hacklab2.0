import { notFound } from 'next/navigation'
import {
  AlertCircle,
  Building2,
  FileText,
  TrendingUp,
  Calendar,
  DollarSign,
} from 'lucide-react'
import Link from 'next/link'
import { MetricCard } from '@/components/data-display/metric-card'
import { TimelineCard } from '@/components/data-display/timeline-card'
import { AlertCard } from '@/components/data-display/alert-card'
import { mockCompanies } from '@/lib/mock-data/companies'
import { mockFilings } from '@/lib/mock-data/filings'
import { mockAlerts } from '@/lib/mock-data/alerts'
import { getFinancialRatios } from '@/lib/mock-data/financials'

interface CompanyPageProps {
  params: Promise<{
    code: string
  }>
}

export default async function CompanyPage({ params }: CompanyPageProps) {
  const { code } = await params

  // Find company
  const company = mockCompanies.find((c) => c.company_code === code)

  if (!company) {
    notFound()
  }

  // Get company-specific data
  const companyFilings = mockFilings
    .filter((f) => f.company_code === code)
    .sort(
      (a, b) =>
        new Date(b.announcement_date).getTime() -
        new Date(a.announcement_date).getTime()
    )
    .slice(0, 5)

  const companyAlerts = mockAlerts
    .filter((a) => a.company_code === code)
    .sort(
      (a, b) =>
        new Date(b.triggered_at).getTime() - new Date(a.triggered_at).getTime()
    )
    .slice(0, 3)

  const companyFinancials = getFinancialRatios(code)

  // Calculate health score color
  const getHealthScoreColor = (score?: number): 'success' | 'warning' | 'error' => {
    if (!score) return 'warning'
    if (score >= 75) return 'success'
    if (score >= 50) return 'warning'
    return 'error'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-bg-primary via-bg-secondary to-bg-primary p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Company Header */}
        <div className="rounded-lg border border-border-accent/20 bg-gradient-to-br from-bg-tertiary to-bg-secondary p-8">
          {/* Breadcrumbs */}
          <nav className="mb-6 flex items-center gap-2 font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
            <Link
              href="/companies"
              className="transition-colors hover:text-accent-primary"
            >
              Companies
            </Link>
            <span>/</span>
            <span className="text-accent-primary">{company.ticker}</span>
          </nav>

          {/* Company Info */}
          <div className="mb-6 flex items-start justify-between">
            <div>
              <div className="mb-2 flex items-center gap-3">
                <span className="font-mono text-2xl font-bold uppercase tracking-wider text-accent-primary">
                  {company.ticker}
                </span>
                <span className="rounded-md border border-border-secondary bg-bg-elevated px-2.5 py-1 font-mono text-xs font-semibold text-text-tertiary">
                  {company.company_code}
                </span>
              </div>
              <h1 className="mb-2 font-sans text-3xl font-bold text-text-primary">
                {company.company_name}
              </h1>
              <p className="font-sans text-lg text-text-secondary">
                {company.sector}
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Link
                href={`/copilot?company=${company.company_code}`}
                className="flex items-center gap-2 rounded-lg bg-accent-primary px-4 py-2.5 font-mono text-sm font-semibold text-bg-primary transition-all hover:bg-accent-secondary"
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
                    d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                  />
                </svg>
                <span>Ask Copilot</span>
              </Link>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {company.market_cap && (
              <div className="rounded-lg border border-border-secondary bg-bg-elevated p-4">
                <div className="mb-2 flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-text-tertiary" />
                  <p className="font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                    Market Cap
                  </p>
                </div>
                <p className="font-mono text-xl font-bold text-text-primary">
                  RM {(company.market_cap / 1000000000).toFixed(2)}B
                </p>
              </div>
            )}

            <div className="rounded-lg border border-border-secondary bg-bg-elevated p-4">
              <div className="mb-2 flex items-center gap-2">
                <FileText className="h-4 w-4 text-text-tertiary" />
                <p className="font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                  Total Filings
                </p>
              </div>
              <p className="font-mono text-xl font-bold text-text-primary">
                {company.filings_count}
              </p>
            </div>

            <div className="rounded-lg border border-border-secondary bg-bg-elevated p-4">
              <div className="mb-2 flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-text-tertiary" />
                <p className="font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                  Active Alerts
                </p>
              </div>
              <p
                className={`font-mono text-xl font-bold ${
                  company.alert_count > 0 ? 'text-error' : 'text-text-primary'
                }`}
              >
                {company.alert_count}
              </p>
            </div>

            <div className="rounded-lg border border-border-secondary bg-bg-elevated p-4">
              <div className="mb-2 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-text-tertiary" />
                <p className="font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                  Health Score
                </p>
              </div>
              <p
                className={`font-mono text-xl font-bold ${
                  company.financial_health_score
                    ? company.financial_health_score >= 75
                      ? 'text-success'
                      : company.financial_health_score >= 50
                        ? 'text-warning'
                        : 'text-error'
                    : 'text-text-tertiary'
                }`}
              >
                {company.financial_health_score ?? 'N/A'}
              </p>
            </div>
          </div>

          {company.latest_filing_date && (
            <div className="mt-4 flex items-center justify-between border-t border-border-secondary pt-4">
              <span className="font-sans text-sm font-medium text-text-tertiary">
                Latest Filing
              </span>
              <time className="font-mono text-sm font-semibold text-accent-primary">
                {new Date(company.latest_filing_date).toLocaleDateString(
                  'en-GB',
                  {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric',
                  }
                )}
              </time>
            </div>
          )}
        </div>

        {/* Content Sections */}
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          {/* Recent Filings */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-sans text-2xl font-bold text-text-primary">
                Recent Filings
              </h2>
              <Link
                href={`/filings?company=${company.company_code}`}
                className="font-mono text-sm font-semibold text-accent-primary transition-colors hover:text-accent-secondary"
              >
                View All →
              </Link>
            </div>

            {companyFilings.length === 0 ? (
              <div className="rounded-lg border border-border-primary bg-bg-secondary p-12 text-center">
                <FileText className="mx-auto mb-4 h-12 w-12 text-text-tertiary opacity-50" />
                <p className="font-sans text-sm text-text-tertiary">
                  No filings available
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {companyFilings.map((filing) => (
                  <TimelineCard
                    key={filing.filing_id}
                    filing={filing}
                    showCompanyName={false}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Recent Alerts */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="font-sans text-2xl font-bold text-text-primary">
                Active Alerts
              </h2>
              <Link
                href={`/alerts?company=${company.company_code}`}
                className="font-mono text-sm font-semibold text-accent-primary transition-colors hover:text-accent-secondary"
              >
                View All →
              </Link>
            </div>

            {companyAlerts.length === 0 ? (
              <div className="rounded-lg border border-border-primary bg-bg-secondary p-12 text-center">
                <AlertCircle className="mx-auto mb-4 h-12 w-12 text-text-tertiary opacity-50" />
                <p className="font-sans text-sm text-text-tertiary">
                  No active alerts
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {companyAlerts.map((alert) => (
                  <AlertCard key={alert.alert_id} alert={alert} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Financial Ratios Section */}
        {companyFinancials.length > 0 && (
          <div className="space-y-4">
            <h2 className="font-sans text-2xl font-bold text-text-primary">
              Financial Ratios
            </h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
              {companyFinancials.slice(0, 4).map((ratio, index) => (
                <MetricCard
                  key={index}
                  label={ratio.ratio_name}
                  value={ratio.ratio_value.toFixed(2)}
                  trend={
                    ratio.change_percent
                      ? {
                          value: Math.abs(ratio.change_percent),
                          direction: ratio.change_percent > 0 ? 'up' : 'down',
                        }
                      : undefined
                  }
                  variant={
                    ratio.trend === 'up'
                      ? 'success'
                      : ratio.trend === 'down'
                        ? 'error'
                        : 'default'
                  }
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
