'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Building2,
  FileText,
  AlertTriangle,
  Bot,
  Database,
  Upload,
  Settings,
  Activity,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface SidebarProps {
  collapsed?: boolean
  onToggle?: () => void
}

const navigation = [
  {
    title: 'Dashboard',
    items: [
      { name: 'Overview', href: '/dashboard', icon: LayoutDashboard },
      { name: 'Companies', href: '/companies', icon: Building2 },
      { name: 'Filings', href: '/filings', icon: FileText },
      { name: 'Alerts', href: '/alerts', icon: AlertTriangle },
      { name: 'Copilot', href: '/copilot', icon: Bot },
      { name: 'SQL Query', href: '/sql', icon: Database },
    ],
  },
  {
    title: 'Ingestion',
    items: [
      { name: 'Status', href: '/ingest', icon: Activity },
      { name: 'Bursa Scraper', href: '/ingest/bursa', icon: Upload },
      { name: 'Upload Files', href: '/ingest/upload', icon: Upload },
    ],
  },
  {
    title: 'System',
    items: [
      { name: 'Settings', href: '/settings', icon: Settings },
    ],
  },
]

export function Sidebar({ collapsed = false, onToggle }: SidebarProps) {
  const pathname = usePathname()

  return (
    <aside
      className={cn(
        'h-screen bg-gradient-to-b from-[var(--color-bg-secondary)] to-[var(--color-bg-primary)] border-r border-[var(--color-border-primary)] transition-all duration-300 flex flex-col',
        collapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="h-14 flex items-center justify-between px-4 border-b border-[var(--color-border-primary)]">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-gradient-to-br from-[var(--color-accent-primary)] to-[var(--color-accent-secondary)] rounded-lg flex items-center justify-center font-mono font-bold text-xs text-[var(--color-bg-primary)]">
              FI
            </div>
            <div>
              <div className="text-xs font-bold gradient-text">FinIntel</div>
              <div className="text-xs text-subtle">AmBank</div>
            </div>
          </div>
        )}
        <button
          onClick={onToggle}
          className="p-1 hover:bg-[var(--color-bg-elevated)] rounded transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="w-3.5 h-3.5 text-[var(--color-text-secondary)]" />
          ) : (
            <ChevronLeft className="w-3.5 h-3.5 text-[var(--color-text-secondary)]" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 overflow-y-auto">
        {navigation.map((section) => (
          <div key={section.title} className="mb-6">
            {!collapsed && (
              <div className="px-3 mb-2 text-xs font-semibold text-subtle uppercase tracking-wider">
                {section.title}
              </div>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const isActive = pathname === item.href
                const Icon = item.icon

                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      'flex items-center gap-2.5 px-3 py-2.5 rounded-lg transition-all group relative min-h-11',
                      isActive
                        ? 'bg-[var(--color-bg-elevated)] text-[var(--color-accent-primary)] border-l-2 border-[var(--color-accent-primary)]'
                        : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-elevated)] hover:text-[var(--color-text-primary)]'
                    )}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    {!collapsed && (
                      <span className="font-medium text-sm">{item.name}</span>
                    )}
                    {collapsed && (
                      <div className="absolute left-full ml-2 px-2 py-1 bg-[var(--color-bg-elevated)] rounded shadow-lg text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                        {item.name}
                      </div>
                    )}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* System Health Indicator */}
      <div className={cn(
        'px-2 py-3 border-t border-[var(--color-border-primary)]',
        collapsed && 'px-1.5'
      )}>
        <div className={cn(
          'flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[var(--color-bg-elevated)]',
          collapsed && 'justify-center px-1.5'
        )}>
          <div className="w-1.5 h-1.5 bg-[var(--color-success)] rounded-full animate-pulse" />
          {!collapsed && (
            <div>
              <div className="text-xs font-medium text-[var(--color-text-primary)]">All Systems Operational</div>
              <div className="text-xs text-subtle">Last checked: 2m ago</div>
            </div>
          )}
        </div>
      </div>
    </aside>
  )
}
