'use client'

import { useState } from 'react'
import { Sidebar } from './sidebar'
import { Header } from './header'

interface AppShellProps {
  children: React.ReactNode
  breadcrumbs?: { label: string; href?: string }[]
  alertCount?: number
}

export function AppShell({ children, breadcrumbs, alertCount = 5 }: AppShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--color-bg-primary)]">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <Header breadcrumbs={breadcrumbs} alertCount={alertCount} />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto dashboard-bg">
          {children}
        </main>
      </div>
    </div>
  )
}
