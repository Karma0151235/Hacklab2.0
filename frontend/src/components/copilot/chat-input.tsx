'use client'

import { Send, Paperclip, Loader2 } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSend: (message: string) => void
  isLoading?: boolean
  placeholder?: string
  className?: string
}

export function ChatInput({
  onSend,
  isLoading = false,
  placeholder = 'Ask me anything about your filings, alerts, or companies...',
  className,
}: ChatInputProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [message])

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault()

    if (!message.trim() || isLoading) return

    onSend(message.trim())
    setMessage('')

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const characterCount = message.length
  const maxCharacters = 2000

  return (
    <div
      className={cn(
        'rounded-lg border border-border-accent/20 bg-gradient-to-br from-bg-tertiary to-bg-secondary p-4',
        className
      )}
    >
      <form onSubmit={handleSubmit} className="space-y-3">
        {/* Textarea */}
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            rows={1}
            className="max-h-40 min-h-[44px] w-full resize-none rounded-lg border border-border-secondary bg-bg-elevated px-4 py-3 pr-12 font-sans text-sm text-text-primary placeholder:text-text-tertiary focus:border-accent-primary/40 focus:outline-none focus:ring-2 focus:ring-accent-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
            style={{ overflowY: message.length > 100 ? 'auto' : 'hidden' }}
          />

          {/* Attachment Button (placeholder for future) */}
          <button
            type="button"
            className="absolute bottom-3 right-3 rounded-md p-1.5 text-text-tertiary transition-colors hover:bg-bg-tertiary hover:text-text-primary"
            title="Attach file (coming soon)"
            disabled
          >
            <Paperclip className="h-4 w-4" />
          </button>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between">
          {/* Character Count */}
          <div className="font-mono text-xs text-text-tertiary">
            <span
              className={cn(
                characterCount > maxCharacters && 'text-error'
              )}
            >
              {characterCount}
            </span>{' '}
            / {maxCharacters}
          </div>

          {/* Send Button */}
          <button
            type="submit"
            disabled={!message.trim() || isLoading || characterCount > maxCharacters}
            className={cn(
              'flex items-center gap-2 rounded-lg px-4 py-2 font-mono text-sm font-semibold transition-all',
              'disabled:cursor-not-allowed disabled:opacity-50',
              isLoading
                ? 'bg-bg-elevated text-text-tertiary'
                : 'bg-accent-primary text-bg-primary hover:bg-accent-secondary'
            )}
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Thinking...</span>
              </>
            ) : (
              <>
                <span>Send</span>
                <Send className="h-4 w-4" />
              </>
            )}
          </button>
        </div>

       
      </form>
    </div>
  )
}
