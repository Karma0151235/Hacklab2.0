"use client"

import { format } from 'date-fns'
import { Copy, User, Bot, Check } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'
import { CopilotAnswer } from '@/lib/types/api'
import { CitationBlock } from './citation-block'
import { AgentWorkflow } from './agent-workflow'
import { ResultTabs } from './result-tabs'

interface MessageBubbleProps {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  copilotAnswer?: CopilotAnswer
  className?: string
}

export function MessageBubble({
  role,
  content,
  timestamp,
  copilotAnswer,
  className,
}: MessageBubbleProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const isUser = role === 'user'

  return (
    <div
      className={cn(
        'flex gap-4',
        isUser ? 'flex-row-reverse' : 'flex-row',
        className
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg',
          isUser
            ? 'bg-accent-primary/10 text-accent-primary'
            : 'bg-bg-elevated text-text-primary'
        )}
      >
        {isUser ? (
          <User className="h-5 w-5" />
        ) : (
          <Bot className="h-5 w-5" />
        )}
      </div>

      {/* Message Content */}
      <div className={cn('flex-1 min-w-0', isUser ? 'items-end' : 'items-start')}>
        {/* Agent Workflow Visualization (Assistant only) */}
        {!isUser && copilotAnswer && (
          <AgentWorkflow usedAgents={copilotAnswer.source_agents} />
        )}

        {/* Message Bubble */}
        <div
          className={cn(
            'group relative rounded-lg p-4',
            isUser
              ? 'ml-auto max-w-2xl border border-accent-primary/40 bg-gradient-to-br from-accent-primary/10 to-accent-secondary/10'
              : 'max-w-4xl border border-border-secondary bg-gradient-to-br from-bg-tertiary to-bg-secondary'
          )}
        >
          {/* Copy Button */}
          <button
            onClick={handleCopy}
            className={cn(
              'absolute right-2 top-2 z-10 rounded-md border border-border-secondary bg-bg-elevated p-1.5 opacity-0 transition-all hover:border-accent-primary/40 group-hover:opacity-100',
              copied && 'opacity-100'
            )}
            title="Copy message"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-success" />
            ) : (
              <Copy className="h-3.5 w-3.5 text-text-tertiary" />
            )}
          </button>

          {/* User Message (Simple Text) */}
          {isUser && (
            <div className="font-sans text-sm leading-relaxed text-text-primary">
              {content}
            </div>
          )}

          {/* Assistant Message (Rich Result Tabs) */}
          {!isUser && (
            <>
              {copilotAnswer ? (
                <ResultTabs answer={copilotAnswer} fullContent={content} />
              ) : (
                // Fallback for assistant messages without structured answer (e.g. errors)
                <div className="font-sans text-sm leading-relaxed text-text-primary whitespace-pre-wrap">
                  {content}
                </div>
              )}
              
              {/* Confidence Score Footer */}
              {!isUser && copilotAnswer && (
                <div className="mt-3 flex items-center gap-2 border-t border-border-secondary pt-3">
                  <span className="font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
                    Confidence
                  </span>
                  <div className="flex items-center gap-2 rounded-md bg-bg-elevated px-2 py-1">
                    <div className="h-1.5 w-16 overflow-hidden rounded-full bg-bg-primary">
                      <div
                        className={cn(
                          'h-full rounded-full transition-all duration-500',
                          copilotAnswer.confidence >= 0.8
                            ? 'bg-success'
                            : copilotAnswer.confidence >= 0.6
                              ? 'bg-warning'
                              : 'bg-error'
                        )}
                        style={{ width: `${copilotAnswer.confidence * 100}%` }}
                      />
                    </div>
                    <span
                      className={cn(
                        'font-mono text-xs font-bold',
                        copilotAnswer.confidence >= 0.8
                          ? 'text-success'
                          : copilotAnswer.confidence >= 0.6
                            ? 'text-warning'
                            : 'text-error'
                      )}
                    >
                      {Math.round(copilotAnswer.confidence * 100)}%
                    </span>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Citations */}
        {!isUser && copilotAnswer?.citations && copilotAnswer.citations.length > 0 && (
          <div className="mt-3">
            <CitationBlock citations={copilotAnswer.citations} />
          </div>
        )}

        {/* Timestamp */}
        <div
          className={cn(
            'mt-2 font-mono text-xs text-text-tertiary',
            isUser ? 'text-right' : 'text-left'
          )}
        >
          {format(new Date(timestamp), 'HH:mm')}
        </div>
      </div>
    </div>
  )
}
