"use client"

import { useState } from 'react'
import { cn } from '@/lib/utils'
import { FileText, Database, AlertCircle, FileSearch } from 'lucide-react'
import { CopilotAnswer, Citation } from '@/lib/types/api'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface ResultTabsProps {
  answer: CopilotAnswer
  fullContent: string
  citations?: Citation[]
}

export function ResultTabs({ answer, fullContent, citations = [] }: ResultTabsProps) {
  const [activeTab, setActiveTab] = useState<'summary' | 'data' | 'alerts'>('summary')

  // Cleaning logic: Try to extract the clean answer from the raw output if it contains separators
  let cleanAnswer = fullContent
  
  if (fullContent.includes('================ ANSWER ================')) {
    const parts = fullContent.split('================ ANSWER ================')
    if (parts.length > 1) {
      let answerPart = parts[1]
      if (answerPart.includes('================ AGENTS USED ================')) {
        answerPart = answerPart.split('================ AGENTS USED ================' as any)[0]
      }
      cleanAnswer = answerPart.trim()
    }
  } else if (fullContent.includes('**Chain-of-Thought Reasoning**')) {
    const match = fullContent.match(/---[\s\n]*### \*\*/)
    if (match && match.index) {
       cleanAnswer = fullContent.substring(match.index + 3).trim()
    }
  }

  // Merge citations from props and answer
  const allCitations = citations.length > 0 ? citations : (answer.citations || [])

  const tabs = [
    { id: 'summary', label: 'Summary', icon: FileText },
    { id: 'data', label: 'Data', icon: Database },
    { id: 'alerts', label: 'Alerts', icon: AlertCircle },
  ] as const

  // Check if citation link is internal/unreachable
  const isInternalSource = (link: string) => {
    return !link || link === '#' || link.startsWith('file://') || link.includes('localhost') || !link.startsWith('http')
  }

  return (
    <div className="overflow-hidden rounded-xl border border-border-secondary/60 bg-bg-secondary/80 backdrop-blur-sm">
      {/* Tab Header */}
      <div className="flex border-b border-border-secondary/60 bg-bg-tertiary/30">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex flex-1 items-center justify-center gap-2 border-b-2 py-3 text-sm font-medium transition-all',
              activeTab === tab.id
                ? 'border-accent-primary text-accent-primary bg-accent-primary/5'
                : 'border-transparent text-text-secondary hover:text-text-primary hover:bg-bg-elevated/30'
            )}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="p-5">
        {activeTab === 'summary' && (
          <div className="space-y-4">
            {/* Styled Markdown with proper table support */}
            <div className="prose prose-sm prose-invert max-w-none 
              prose-headings:text-text-primary prose-headings:font-semibold prose-headings:mb-3
              prose-p:text-text-primary prose-p:leading-relaxed prose-p:mb-4
              prose-strong:text-accent-primary prose-strong:font-semibold
              prose-em:text-text-secondary
              prose-table:w-full prose-table:border-collapse prose-table:mt-4 prose-table:mb-4
              prose-th:bg-bg-tertiary prose-th:text-text-primary prose-th:font-semibold prose-th:text-left prose-th:px-4 prose-th:py-2.5 prose-th:border prose-th:border-border-secondary
              prose-td:text-text-primary prose-td:px-4 prose-td:py-2.5 prose-td:border prose-td:border-border-secondary prose-td:bg-bg-secondary/50
              prose-code:text-accent-primary prose-code:bg-bg-tertiary prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm
              prose-ul:text-text-primary prose-ol:text-text-primary prose-li:mb-1.5
            ">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{cleanAnswer}</ReactMarkdown>
            </div>
          </div>
        )}

        {activeTab === 'data' && (
          <div className="space-y-5">
            {/* Citations Section */}
            {allCitations.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <FileSearch className="h-4 w-4 text-accent-primary" />
                  <h4 className="font-semibold text-sm text-text-primary">
                    Sources Referenced
                  </h4>
                  <span className="text-xs text-text-tertiary">({allCitations.length})</span>
                </div>
                <div className="space-y-2">
                  {allCitations.map((citation, index) => (
                    <div
                      key={index}
                      className="rounded-lg border border-border-secondary/60 bg-bg-tertiary/50 p-3 hover:bg-bg-tertiary/80 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        {/* Number badge */}
                        <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-md bg-accent-primary/15 font-mono text-xs font-bold text-accent-primary">
                          {index + 1}
                        </span>
                        
                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-medium text-sm text-text-primary">
                              {citation.source}
                            </span>
                            {citation.page && (
                              <span className="rounded-full bg-bg-secondary px-2 py-0.5 font-mono text-[10px] text-text-tertiary border border-border-secondary/50">
                                Page {citation.page}
                              </span>
                            )}
                            {isInternalSource(citation.link) && (
                              <span className="rounded-full bg-accent-primary/10 px-2 py-0.5 text-[10px] text-accent-primary font-medium">
                                Internal Document
                              </span>
                            )}
                          </div>
                          {citation.excerpt && citation.excerpt.trim() && citation.excerpt.length > 15 && (
                            <p className="text-xs text-text-secondary mt-2 leading-relaxed border-l-2 border-accent-primary/30 pl-3 italic">
                              "{citation.excerpt}"
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tables Section */}
            {answer.tables && answer.tables.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-accent-primary" />
                  <h4 className="font-semibold text-sm text-text-primary">
                    Extracted Data
                  </h4>
                </div>
                <pre className="overflow-auto rounded-lg bg-bg-tertiary/70 p-4 text-xs text-text-primary font-mono border border-border-secondary/50">
                  {JSON.stringify(answer.tables, null, 2)}
                </pre>
              </div>
            )}

            {/* Empty State */}
            {allCitations.length === 0 && (!answer.tables || answer.tables.length === 0) && (
              <div className="flex flex-col items-center justify-center py-10 text-center">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-bg-tertiary/50 mb-3">
                  <Database className="h-6 w-6 text-text-tertiary" />
                </div>
                <p className="text-sm text-text-tertiary">No structured data or sources available</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'alerts' && (
          <div className="min-h-[120px]">
             {answer.alerts && answer.alerts.length > 0 ? (
                <div className="space-y-3">
                  {answer.alerts.map((alert, index) => (
                    <div key={index} className={cn(
                      "rounded-lg border p-4",
                      alert.severity === 'high' ? 'border-error/50 bg-error/10' :
                      alert.severity === 'medium' ? 'border-warning/50 bg-warning/10' :
                      'border-border-secondary bg-bg-tertiary/50'
                    )}>
                      <div className="flex items-center gap-3 mb-2">
                        <AlertCircle className={cn(
                          "h-4 w-4",
                          alert.severity === 'high' ? 'text-error' :
                          alert.severity === 'medium' ? 'text-warning' :
                          'text-text-tertiary'
                        )} />
                        <span className={cn(
                          "text-xs font-bold uppercase tracking-wide",
                          alert.severity === 'high' ? 'text-error' :
                          alert.severity === 'medium' ? 'text-warning' :
                          'text-text-tertiary'
                        )}>
                          {alert.severity} Priority
                        </span>
                        <span className="text-sm text-text-primary font-medium">{alert.alert_type}</span>
                      </div>
                      <p className="text-sm text-text-secondary leading-relaxed">{alert.reason}</p>
                    </div>
                  ))}
                </div>
             ) : (
                <div className="flex flex-col items-center justify-center py-10 text-center">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-bg-tertiary/50 mb-3">
                    <AlertCircle className="h-6 w-6 text-text-tertiary" />
                  </div>
                  <p className="text-sm text-text-tertiary">No alerts triggered for this query</p>
                </div>
             )}
          </div>
        )}
      </div>
    </div>
  )
}


