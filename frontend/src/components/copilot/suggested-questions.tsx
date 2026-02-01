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
    <div className={cn('space-y-2', className)}>
      {/* Header */}
      <div className="flex items-center justify-center gap-2 mt-6">
        <Sparkles className="h-3.5 w-3.5 text-accent-primary" />
        <span className="font-mono text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">
          Suggested Questions
        </span>
      </div>

      {/* Question Chips */}
      <div className="flex flex-col items-center gap-3">
        {questions.map((question, index) => (
          <button
            key={index}
            onClick={() => onQuestionClick(question)}
            className="group rounded-full border border-border-secondary bg-gradient-to-br from-bg-tertiary to-bg-secondary px-4 py-2 text-center font-sans text-xs text-text-secondary transition-all hover:border-accent-primary/40 hover:text-text-primary hover:shadow-[0_0_15px_rgba(0,217,255,0.1)]"
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
