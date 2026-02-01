"use client"

import { useEffect, useRef, useState } from 'react'
import { MessageCircle, Trash2, Bot, FileText, BarChart3, AlertTriangle } from 'lucide-react'
import { useCopilotStore } from '@/stores/use-copilot-store'
import { MessageBubble } from './message-bubble'
import { ChatInput } from './chat-input'
import { SuggestedQuestions } from './suggested-questions'
import { getCopilotResult, getCopilotStatus, startCopilotJob } from '@/lib/api/copilot'
import { AgentProgressModal, AgentStep } from './agent-progress-modal'
import { CopilotJobStatus } from '@/lib/types/api'

const SUGGESTED_QUESTIONS = [
  'What are the financials of Foodie Media Berhad?',
  'Show me the detailed analysis of Foodie Media Berhad',
  'Does Foodie Media Berhad have any recent alerts?',
]

const INITIAL_STEPS: AgentStep[] = [
  {
    id: 'supervisor',
    name: 'Supervisor Agent',
    description: 'Orchestrating workflow...',
    status: 'waiting',
    logs: [],
    icon: Bot
  },
  {
    id: 'rag',
    name: 'RAG Agent',
    description: 'Retrieving documents...',
    status: 'waiting',
    logs: [],
    icon: FileText
  },
  {
    id: 'financial',
    name: 'Financial Agent',
    description: 'Analyzing metrics...',
    status: 'waiting',
    logs: [],
    icon: BarChart3
  },
  {
    id: 'alert',
    name: 'Alert Agent',
    description: 'Checking risks...',
    status: 'waiting',
    logs: [],
    icon: AlertTriangle
  }
]

export function ChatWindow() {
  const { messages, isLoading, addMessage, clearMessages, setLoading } = useCopilotStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [showProgressModal, setShowProgressModal] = useState(false)
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>(INITIAL_STEPS)
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  // Auto-scroll logic
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const updateFromStatus = (status: CopilotJobStatus) => {
    setAgentSteps(prev => prev.map(step => {
      const agentStatus = status.agents?.[step.id]
      if (!agentStatus) {
        return step
      }
      return {
        ...step,
        status: agentStatus.status as AgentStep['status'],
        logs: agentStatus.logs || [],
        description: agentStatus.latest_message || step.description,
      }
    }))
  }

  const startPolling = (jobId: string) => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
    }
    pollRef.current = setInterval(async () => {
      try {
        const status = await getCopilotStatus(jobId)
        updateFromStatus(status)
        if (status.status === 'completed') {
          if (pollRef.current) {
            clearInterval(pollRef.current)
          }
          const answer = await getCopilotResult(jobId)
          const assistantMessage = {
            id: (Date.now() + 1).toString(),
            role: 'assistant' as const,
            content: answer.answer_text,
            copilotAnswer: answer,
            timestamp: new Date().toISOString(),
          }
          addMessage(assistantMessage)
          setShowProgressModal(false)
          setLoading(false)
          setActiveJobId(null)
        }
        if (status.status === 'error') {
          if (pollRef.current) {
            clearInterval(pollRef.current)
          }
          setShowProgressModal(false)
          setLoading(false)
          setActiveJobId(null)
          const errorMessage = {
            id: (Date.now() + 1).toString(),
            role: 'assistant' as const,
            content: status.error || 'Copilot job failed. Please try again.',
            timestamp: new Date().toISOString(),
          }
          addMessage(errorMessage)
        }
      } catch (error) {
        if (pollRef.current) {
          clearInterval(pollRef.current)
        }
        setShowProgressModal(false)
        setLoading(false)
        setActiveJobId(null)
        const errorMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant' as const,
          content: 'I ran into an error retrieving live progress. Please try again.',
          timestamp: new Date().toISOString(),
        }
        addMessage(errorMessage)
      }
    }, 1000)
  }

  const handleSendMessage = async (content: string) => {
    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content,
      timestamp: new Date().toISOString(),
    }
    addMessage(userMessage)

    setLoading(true)
    setAgentSteps(INITIAL_STEPS.map(s => ({ ...s, status: 'waiting', logs: [] })))
    setShowProgressModal(true)

    try {
      const job = await startCopilotJob(content)
      setActiveJobId(job.job_id)
      updateFromStatus(job)
      startPolling(job.job_id)
    } catch (error) {
      setShowProgressModal(false)
      setLoading(false)
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: 'I apologize, but I encountered an error starting the copilot job. Please try again.',
        timestamp: new Date().toISOString(),
      }
      addMessage(errorMessage)
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

  useEffect(() => {
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
      }
    }
  }, [])

  return (
    <div className="relative flex h-full flex-col overflow-hidden">
      {/* Ambient background label */}
      {!isLoading && messages.length === 0 && (
        <div className="pointer-events-none absolute inset-0 -z-10 flex items-center justify-center">
          <div className="select-none text-[120px] font-semibold tracking-tight text-text-primary/5 sm:text-[160px]">
            AI Copilot
          </div>
        </div>
      )}

      <AgentProgressModal 
        isOpen={showProgressModal} 
        onClose={() => setShowProgressModal(false)}
        steps={agentSteps}
      />

      {/* Messages Container */}
      <div

        className="flex-1 overflow-y-auto px-6 py-8"
      >
        {messages.length === 0 ? (
          /* Empty State */
          <div className="group relative flex h-full flex-col items-center justify-center space-y-6">
            <div className="pointer-events-none absolute inset-x-0 top-0 flex justify-center opacity-0 transition-opacity duration-300 group-hover:opacity-100">
              <div className="mt-2 flex items-center gap-3 rounded-full border border-border-secondary bg-bg-elevated/70 px-4 py-2 shadow-lg">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-primary/15">
                  <MessageCircle className="h-4 w-4 text-accent-primary" />
                </div>
                <div className="text-sm font-semibold text-text-primary">AI Copilot</div>
                <div className="text-xs text-text-tertiary">
                  Hover to reveal starter prompts
                </div>
              </div>
            </div>

            <div className="relative w-full max-w-4xl">
              <div className="rounded-3xl border border-border-secondary bg-bg-secondary/40 p-10 shadow-[0_30px_120px_-60px_rgba(10,120,255,0.45)]">
                <div className="flex items-center gap-4">
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-primary/15">
                    <MessageCircle className="h-7 w-7 text-accent-primary" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-semibold text-text-primary">
                      Ask for intelligence
                    </h2>
                    <p className="text-sm text-text-tertiary">
                      Fast financial context, alerts, and filings in one response.
                    </p>
                  </div>
                </div>
              </div>

              {/* Suggested Questions */}
              {!isLoading && (
                <div className="mt-6 w-full opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                  <SuggestedQuestions
                    questions={SUGGESTED_QUESTIONS}
                    onQuestionClick={handleQuestionClick}
                  />
                </div>
              )}
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
        </div>
      </div>
    </div>
  )
}
