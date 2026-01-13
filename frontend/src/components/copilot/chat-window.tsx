'use client'

import { useEffect, useRef } from 'react'
import { MessageCircle, Trash2 } from 'lucide-react'
import { useCopilotStore } from '@/stores/use-copilot-store'
import { MessageBubble } from './message-bubble'
import { ChatInput } from './chat-input'
import { SuggestedQuestions } from './suggested-questions'
import { sendCopilotMessage } from '@/lib/api/copilot'

const SUGGESTED_QUESTIONS = [
  'What are the latest filings from MAYBANK?',
  'Show me all high-severity alerts',
  'What are the financial ratios for Top Glove?',
  'Summarize recent announcements in the Technology sector',
  'Which companies have deteriorating financial health?',
]

export function ChatWindow() {
  const { messages, isLoading, addMessage, clearMessages, setLoading } =
    useCopilotStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content,
      timestamp: new Date().toISOString(),
    }
    addMessage(userMessage)

    // Simulate loading
    setLoading(true)

    try {
      // Call copilot API
      const answer = await sendCopilotMessage(content)

      // Add assistant message
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: answer.answer_text,
        copilotAnswer: answer,
        timestamp: new Date().toISOString(),
      }
      addMessage(assistantMessage)
    } catch (error) {
      // Add error message
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content:
          'I apologize, but I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
      }
      addMessage(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleQuestionClick = (question: string) => {
    handleSendMessage(question)
  }

  const handleClearChat = () => {
    if (confirm('Are you sure you want to clear the chat history?')) {
      clearMessages()
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Messages Container */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-6 py-8"
      >
        {messages.length === 0 ? (
          /* Empty State */
          <div className="flex h-full flex-col items-center justify-center space-y-6">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-accent-primary/10">
              <MessageCircle className="h-10 w-10 text-accent-primary" />
            </div>
            <div className="text-center">
              <h2 className="mb-2 font-sans text-2xl font-bold text-text-primary">
                Welcome to Copilot
              </h2>
              <p className="font-sans text-base text-text-secondary">
                Ask me anything about your companies, filings, or alerts
              </p>
            </div>

            {/* Suggested Questions */}
            <div className="w-full max-w-3xl">
              <SuggestedQuestions
                questions={SUGGESTED_QUESTIONS}
                onQuestionClick={handleQuestionClick}
              />
            </div>
          </div>
        ) : (
          /* Messages */
          <div className="mx-auto max-w-4xl space-y-6">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                role={message.role}
                content={message.content}
                timestamp={message.timestamp}
                copilotAnswer={message.copilotAnswer}
              />
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex gap-4">
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-bg-elevated">
                  <MessageCircle className="h-5 w-5 text-text-primary" />
                </div>
                <div className="flex-1">
                  <div className="max-w-4xl rounded-lg border border-border-secondary bg-gradient-to-br from-bg-tertiary to-bg-secondary p-4">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 animate-pulse rounded-full bg-accent-primary" />
                      <div className="h-2 w-2 animate-pulse rounded-full bg-accent-primary delay-150" />
                      <div className="h-2 w-2 animate-pulse rounded-full bg-accent-primary delay-300" />
                      <span className="ml-2 font-sans text-sm text-text-tertiary">
                        Thinking...
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Scroll anchor */}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-border-secondary bg-bg-secondary px-6 py-4">
        <div className="mx-auto max-w-4xl space-y-4">
          {/* Suggested Questions (when chat has started) */}
          {messages.length > 0 && !isLoading && (
            <SuggestedQuestions
              questions={SUGGESTED_QUESTIONS.filter(
                (q) => !messages.some((m) => m.content === q)
              ).slice(0, 3)}
              onQuestionClick={handleQuestionClick}
            />
          )}

          {/* Chat Input */}
          <ChatInput onSend={handleSendMessage} isLoading={isLoading} />

          {/* Clear Chat Button */}
          {messages.length > 0 && (
            <div className="flex justify-center">
              <button
                onClick={handleClearChat}
                className="flex items-center gap-2 rounded-md border border-border-secondary bg-bg-elevated px-3 py-2 font-mono text-xs font-semibold text-text-secondary transition-all hover:border-error/40 hover:text-error"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>Clear Chat</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
