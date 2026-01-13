import { AppShell } from '@/components/layout/app-shell'
import { TestNotificationButton } from '@/components/notifications/test-notification-button'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      <AppShell>{children}</AppShell>
      <TestNotificationButton />
    </>
  )
}
