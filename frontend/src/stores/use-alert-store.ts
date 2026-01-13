import { create } from 'zustand'
import { Alert } from '@/lib/types/api'

interface AlertStore {
  alerts: Alert[]
  unreadCount: number
  addAlert: (alert: Alert) => void
  addAlerts: (alerts: Alert[]) => void
  markAsRead: (alertId: string) => void
  dismissAlert: (alertId: string) => void
  clearAlerts: () => void
  getAlertsBySeverity: (severity: 'high' | 'medium' | 'low') => Alert[]
  getActiveAlerts: () => Alert[]
}

export const useAlertStore = create<AlertStore>((set, get) => ({
  alerts: [],
  unreadCount: 0,

  addAlert: (alert) =>
    set((state) => ({
      alerts: [alert, ...state.alerts],
      unreadCount: state.unreadCount + 1,
    })),

  addAlerts: (alerts) =>
    set((state) => ({
      alerts: [...alerts, ...state.alerts],
      unreadCount: state.unreadCount + alerts.length,
    })),

  markAsRead: (alertId) =>
    set((state) => ({
      alerts: state.alerts.map((alert) =>
        alert.alert_id === alertId ? { ...alert, status: 'reviewed' as const } : alert
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    })),

  dismissAlert: (alertId) =>
    set((state) => ({
      alerts: state.alerts.map((alert) =>
        alert.alert_id === alertId ? { ...alert, status: 'dismissed' as const } : alert
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    })),

  clearAlerts: () =>
    set({
      alerts: [],
      unreadCount: 0,
    }),

  getAlertsBySeverity: (severity) => {
    return get().alerts.filter((alert) => alert.severity === severity && alert.status === 'active')
  },

  getActiveAlerts: () => {
    return get().alerts.filter((alert) => alert.status === 'active')
  },
}))
