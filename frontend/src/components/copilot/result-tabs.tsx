"use client"

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { FileText, Database, AlertCircle } from 'lucide-react'
import { CopilotAnswer } from '@/lib/types/api'
import ReactMarkdown from 'react-markdown'

interface ResultTabsProps {
  answer: CopilotAnswer
  fullContent: string
}

export function ResultTabs({ answer, fullContent }: ResultTabsProps) {
  const [activeTab, setActiveTab] = useState<'summary' | 'data' | 'alerts'>('summary')

  // Cleaning logic: Try to extract the clean answer from the raw output if it contains separators
  // The backend log showed "================ ANSWER ================"
  // If not found, use fullContent
  let cleanAnswer = fullContent
  
  if (fullContent.includes('================ ANSWER ================')) {
    const parts = fullContent.split('================ ANSWER ================')
    if (parts.length > 1) {
      // Take the part after the separator
      // And also cut off at "================ AGENTS USED ================" if present
      let answerPart = parts[1]
      if (answerPart.includes('================ AGENTS USED ================')) {
        answerPart = answerPart.split('================ AGENTS USED ================' as any)[0]
      }
      cleanAnswer = answerPart.trim()
    }
  } else if (fullContent.includes('**Chain-of-Thought Reasoning**')) {
    // If no explicit separator but starts with CoT, try to find the start of the actual response
    // Heuristic: Last "---" or first H1/H2 header after the first few lines?
    // For now, let's keep it simple: if detailed CoT is detected but no separator, show all but warn.
    // Or we could regex for '### **Summary' or similar.
    const match = fullContent.match(/---[\s\n]*### \*\*/)
    if (match && match.index) {
       cleanAnswer = fullContent.substring(match.index + 3).trim()
    }
  }

  const tabs = [
    { id: 'summary', label: 'Summary', icon: FileText },
    { id: 'data', label: 'Data', icon: Database },
    { id: 'alerts', label: 'Alerts', icon: AlertCircle },
  ] as const

  return (
    <div className="mt-4 overflow-hidden rounded-lg border border-border-secondary bg-bg-secondary">
      {/* Tab Header */}
      <div className="flex border-b border-border-secondary bg-bg-tertiary/50">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex flex-1 items-center justify-center gap-2 border-b-2 py-3 text-sm font-medium transition-colors hover:bg-bg-elevated/50',
              activeTab === tab.id
                ? 'border-accent-primary text-accent-primary bg-accent-primary/5'
                : 'border-transparent text-text-secondary hover:text-text-primary'
            )}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="p-4">
        {activeTab === 'summary' && (
          <div className="space-y-4">
            <div className="prose prose-sm prose-invert max-w-none text-text-secondary">
              <ReactMarkdown>{cleanAnswer}</ReactMarkdown>
            </div>
          </div>
        )}

        {activeTab === 'data' && (
          <div className="flex min-h-[150px] flex-col items-center justify-center text-center">
            {answer.tables && answer.tables.length > 0 ? (
              <div className="w-full space-y-4">
                {/* Placeholder for table rendering - MVP assumes pre-formatted or raw data */}
                <p className="text-sm text-text-secondary">Data extract found:</p>
                <pre className="overflow-auto rounded bg-bg-tertiary p-2 text-xs">
                  {JSON.stringify(answer.tables, null, 2)}
                </pre>
              </div>
            ) : (
                <div className="space-y-2">
                    <Database className="mx-auto h-8 w-8 text-text-tertiary opacity-50" />
                    <p className="text-sm text-text-secondary">No structured tabular data extracted.</p>
                </div>
            )}
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="flex min-h-[150px] flex-col items-center justify-center text-center">
             {answer.alerts && answer.alerts.length > 0 ? (
                <div className="w-full">
                     {/* Placeholder for alerts list */}
                     <p>Alerts found</p>
                </div>
             ) : (
                <div className="space-y-2">
                    <AlertCircle className="mx-auto h-8 w-8 text-text-tertiary opacity-50" />
                    <p className="text-sm text-text-secondary">No alerts triggered for this query.</p>
                </div>
             )}
          </div>
        )}
      </div>
    </div>
  )
}
