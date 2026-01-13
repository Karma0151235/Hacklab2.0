import { AppShell } from '@/components/layout/app-shell'

export default function CompaniesLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <AppShell>{children}</AppShell>
}
