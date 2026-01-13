'use client'

import { Search, Bell, User, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAlertStore } from '@/stores/use-alert-store'
import { useRouter } from 'next/navigation'

interface HeaderProps {
  breadcrumbs?: { label: string; href?: string }[]
}

export function Header({ breadcrumbs = [] }: HeaderProps) {
  const router = useRouter()
  const unreadCount = useAlertStore((state) => state.unreadCount)
  return (
    <header className="h-16 bg-[var(--color-bg-secondary)] border-b border-[var(--color-border-primary)] flex items-center justify-between px-6">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2">
        {breadcrumbs.length > 0 ? (
          breadcrumbs.map((crumb, index) => (
            <div key={index} className="flex items-center gap-2">
              {index > 0 && <span className="text-subtle">/</span>}
              <span
                className={cn(
                  'text-sm font-medium',
                  index === breadcrumbs.length - 1
                    ? 'text-[var(--color-text-primary)]'
                    : 'text-subtle hover:text-[var(--color-text-primary)] cursor-pointer'
                )}
              >
                {crumb.label}
              </span>
            </div>
          ))
        ) : (
          <div className="flex items-center gap-3">
            <div className="w-1 h-6 bg-[var(--color-accent-primary)] rounded-full" />
            <h1 className="text-lg font-bold text-[var(--color-text-primary)]">
              Financial Intelligence Dashboard
            </h1>
          </div>
        )}
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-4">
        {/* Global Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-subtle" />
          <input
            type="text"
            placeholder="Search companies, filings, alerts..."
            className="w-80 pl-10 pr-4 py-2 bg-[var(--color-bg-primary)] border border-[var(--color-border-primary)] rounded-lg text-sm text-[var(--color-text-primary)] placeholder:text-subtle focus:outline-none focus:border-[var(--color-accent-primary)] transition-colors"
          />
        </div>

        {/* Alert Badge */}
        <button 
          onClick={() => router.push('/alerts')}
          className="relative p-2 hover:bg-[var(--color-bg-elevated)] rounded-lg transition-colors group"
        >
          <Bell className="w-5 h-5 text-[var(--color-text-secondary)] group-hover:text-[var(--color-text-primary)]" />
          {unreadCount > 0 && (
            <span className="absolute top-1 right-1 w-5 h-5 bg-[var(--color-error)] text-white text-xs font-bold rounded-full flex items-center justify-center animate-pulse">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>

        {/* User Profile */}
        <div className="flex items-center gap-3 pl-4 border-l border-[var(--color-border-primary)]">
          <div className="text-right">
            <div className="text-sm font-medium text-[var(--color-text-primary)]">
              Compliance Officer
            </div>
            <div className="text-xs text-subtle">AmBank Malaysia</div>
          </div>
          <button className="flex items-center gap-2 p-2 hover:bg-[var(--color-bg-elevated)] rounded-lg transition-colors group">
            <div className="w-8 h-8 bg-gradient-to-br from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-[var(--color-bg-primary)]" />
            </div>
            <ChevronDown className="w-4 h-4 text-subtle group-hover:text-[var(--color-text-primary)]" />
          </button>
        </div>
      </div>
    </header>
  )
}
