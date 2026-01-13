'use client'

import { Bell } from 'lucide-react'
import { showAlertNotification } from './alert-notification'
import { useAlertStore } from '@/stores/use-alert-store'
import { Alert } from '@/lib/types/api'

/**
 * Test button to manually trigger alert notifications
 * For demo/testing purposes only
 */
export function TestNotificationButton() {
  const addAlert = useAlertStore((state) => state.addAlert)

  const triggerTestAlert = (severity: 'high' | 'medium' | 'low') => {
    const testAlert: Alert = {
      alert_id: `TEST-${Date.now()}`,
      company_code: '1155',
      company_name: 'Malayan Banking Berhad',
      severity,
      alert_type: severity === 'high' 
        ? 'Critical Compliance Issue' 
        : severity === 'medium' 
        ? 'Corporate Governance Alert' 
        : 'Informational Notice',
      triggered_at: new Date().toISOString(),
      reason: severity === 'high'
        ? 'Significant irregularity detected in related party transactions. Immediate review required.'
        : severity === 'medium'
        ? 'Unusual pattern in director appointment disclosures detected.'
        : 'Quarterly filing submitted later than historical average.',
      evidence: [
        {
          source: 'Q4 2025 Financial Statements',
          link: '/filings/F001',
          page: 142,
          excerpt: 'Related party transactions amounted to RM1.8 billion...',
        },
      ],
      status: 'active',
    }

    // Add to store
    addAlert(testAlert)

    // Show notification
    showAlertNotification(testAlert)
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2">
      <div className="bg-[#0f1419] border border-[#21262d] rounded-lg p-4 shadow-2xl">
        <div className="flex items-center gap-2 mb-3">
          <Bell className="w-4 h-4 text-[#00d9ff]" />
          <span className="text-xs font-medium text-[#8b949e]">Test Notifications</span>
        </div>
        <div className="flex flex-col gap-2">
          <button
            onClick={() => triggerTestAlert('high')}
            className="px-3 py-1.5 bg-red-950/30 hover:bg-red-950/50 border border-red-500/30 hover:border-red-500/50 rounded text-xs font-medium text-red-400 transition-all"
          >
            High Severity
          </button>
          <button
            onClick={() => triggerTestAlert('medium')}
            className="px-3 py-1.5 bg-orange-950/30 hover:bg-orange-950/50 border border-orange-500/30 hover:border-orange-500/50 rounded text-xs font-medium text-orange-400 transition-all"
          >
            Medium Severity
          </button>
          <button
            onClick={() => triggerTestAlert('low')}
            className="px-3 py-1.5 bg-blue-950/30 hover:bg-blue-950/50 border border-blue-500/30 hover:border-blue-500/50 rounded text-xs font-medium text-blue-400 transition-all"
          >
            Low Severity
          </button>
        </div>
        <div className="mt-3 pt-3 border-t border-[#21262d]">
          <p className="text-xs text-[#6e7681] leading-relaxed">
            Auto-alerts every <span className="text-[#00d9ff] font-mono">45s</span>
          </p>
        </div>
      </div>
    </div>
  )
}
