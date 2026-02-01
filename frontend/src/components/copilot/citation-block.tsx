'use client'

import { ChevronDown, ChevronUp, ExternalLink, FileText } from 'lucide-react'
import { useState } from 'react'
import { Citation } from '@/lib/types/api'
import { cn } from '@/lib/utils'

interface CitationBlockProps {
  citations: Citation[]
  className?: string
}

export function CitationBlock({ citations, className }: CitationBlockProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (citations.length === 0) return null

  return (
    <div
      className={cn(
        'rounded-lg border border-border-secondary bg-bg-elevated',
        className
      )}
    >
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex w-full items-center justify-between p-4 transition-colors hover:bg-bg-tertiary"
      >
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-accent-primary" />
          <span className="font-mono text-sm font-semibold text-text-primary">
            {citations.length} {citations.length === 1 ? 'Citation' : 'Citations'}
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4 text-text-tertiary" />
        ) : (
          <ChevronDown className="h-4 w-4 text-text-tertiary" />
        )}
      </button>

      {/* Citation List */}
      {isExpanded && (
        <div className="border-t border-border-secondary">
          {citations.map((citation, index) => (
            <div
              key={index}
              className="border-b border-border-secondary p-4 last:border-b-0 hover:bg-bg-tertiary"
            >
              {/* Citation Header */}
              <div className="mb-2 flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    {/* Citation Number */}
                    <span className="flex h-6 w-6 items-center justify-center rounded-md bg-accent-primary/10 font-mono text-xs font-bold text-accent-primary">
                      {index + 1}
                    </span>

                    {/* Source Name */}
                    <span className="font-sans text-sm font-semibold text-text-primary">
                      {citation.source}
                    </span>

                    {/* Page Number */}
                    {citation.page && (
                      <span className="rounded-md border border-border-secondary bg-bg-secondary px-2 py-0.5 font-mono text-xs text-text-tertiary">
                        Page {citation.page}
                      </span>
                    )}
                  </div>
                </div>

                {/* Link */}
                <a
                  href={citation.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 rounded-md border border-border-secondary bg-bg-secondary px-2.5 py-1 font-mono text-xs font-semibold text-accent-primary transition-all hover:border-accent-primary/40 hover:bg-accent-primary/5"
                >
                  <span>Open</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>

              {/* Excerpt / Referenced Text */}
              {citation.excerpt && citation.excerpt.trim() && (
                <div className="mt-2">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary mb-1 block">
                    Referenced Text
                  </span>
                  <div className="rounded-md border-l-2 border-accent-primary/40 bg-bg-secondary pl-3 pr-3 py-2">
                    <p className="font-sans text-sm leading-relaxed text-text-secondary italic">
                      "{citation.excerpt}"
                    </p>
                  </div>
                </div>
              )}
              {(!citation.excerpt || !citation.excerpt.trim()) && (
                <div className="mt-2 text-xs text-text-tertiary italic">
                  No specific text reference available
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
