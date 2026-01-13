'use client'

import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SuggestedQuestionsProps {
  questions: string[]
  onQuestionClick: (question: string) => void
  className?: string
}

export function SuggestedQuestions({
  questions,
  onQuestionClick,
  className,
}: SuggestedQuestionsProps) {
  if (questions.length === 0) return null

  return (
    <div className={cn('space-y-3', className)}>
      {/* Header */}
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-accent-primary" />
        <span className="font-mono text-xs font-semibold uppercase tracking-wider text-text-tertiary">
          Suggested Questions
        </span>
      </div>

      {/* Question Chips */}
      <div className="flex flex-wrap gap-2">
        {questions.map((question, index) => (
          <button
            key={index}
            onClick={() => onQuestionClick(question)}
            className="group rounded-lg border border-border-secondary bg-gradient-to-br from-bg-tertiary to-bg-secondary px-4 py-2.5 text-left font-sans text-sm text-text-primary transition-all hover:border-accent-primary/40 hover:shadow-[0_0_15px_rgba(0,217,255,0.1)]"
          >
            <span className="transition-colors group-hover:text-accent-primary">
              {question}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
