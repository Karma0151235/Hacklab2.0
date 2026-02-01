"use client"

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageCircle, Trash2, Bot, FileText, BarChart3, AlertTriangle, Sparkles } from 'lucide-react'
import { useCopilotStore, INITIAL_STEPS, AgentStepState } from '@/stores/use-copilot-store'
import { MessageBubble } from './message-bubble'
import { ChatInput } from './chat-input'
import { SuggestedQuestions } from './suggested-questions'
import { getCopilotResult, getCopilotStatus, startCopilotJob } from '@/lib/api/copilot'
import { AgentProgressBubble } from './agent-progress-bubble'
import { AgentStep } from './agent-progress-modal'
import { CopilotJobStatus } from '@/lib/types/api'

const SUGGESTED_QUESTIONS = [
  'What are the financials of Foodie Media Berhad?',
  'Show me the detailed analysis of Foodie Media Berhad',
  'Does Foodie Media Berhad have any recent alerts?',
]

// Map store steps to component steps with icons
const mapStepsWithIcons = (steps: AgentStepState[]): AgentStep[] => {
  const iconMap: Record<string, typeof Bot> = {
    supervisor: Bot,
    rag: FileText,
    financial: BarChart3,
    alert: AlertTriangle,
  }
  return steps.map(step => ({
    ...step,
    icon: iconMap[step.id] || Bot
  }))
}

export function ChatWindow() {
  const { 
    messages, 
    isLoading, 
    addMessage, 
    clearMessages, 
    setLoading,
    activeJobId,
    agentSteps,
    showProgressBubble,
    setActiveJob,
    setAgentSteps,
    setShowProgressBubble,
    resetJobState
  } = useCopilotStore()
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isInputFocused, setIsInputFocused] = useState(false)
  const pollRef = useRef<NodeJS.Timeout | null>(null)
  const hasResumedRef = useRef(false)

  // Auto-scroll logic
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Resume polling if there's an active job when returning to page
  useEffect(() => {
    if (activeJobId && showProgressBubble && !hasResumedRef.current) {
      hasResumedRef.current = true
      setLoading(true)
      startPolling(activeJobId)
    }
    
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
      }
    }
  }, [activeJobId, showProgressBubble])

  const updateFromStatus = (status: CopilotJobStatus) => {
    const updated = agentSteps.map(step => {
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
    })
    setAgentSteps(updated)
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
          resetJobState()
        }
        if (status.status === 'error') {
          if (pollRef.current) {
            clearInterval(pollRef.current)
          }
          resetJobState()
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
        resetJobState()
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
    // Reset steps to initial state
    setAgentSteps(INITIAL_STEPS.map(s => ({ ...s, status: 'waiting', logs: [] })))
    setShowProgressBubble(true)

    try {
      const job = await startCopilotJob(content)
      setActiveJob(job.job_id)
      updateFromStatus(job)
      startPolling(job.job_id)
    } catch (error) {
      resetJobState()
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
    clearMessages()
    resetJobState()
    if (pollRef.current) {
      clearInterval(pollRef.current)
    }
  }

  // Convert store steps to component steps with icons
  const stepsWithIcons = mapStepsWithIcons(agentSteps)
  const isComplete = agentSteps.every(s => s.status === 'completed' || s.status === 'skipped')

  return (
    <div className="flex h-full flex-col bg-bg-primary">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-secondary bg-bg-secondary px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-primary/10">
            <MessageCircle className="h-5 w-5 text-accent-primary" />
          </div>
          <div>
            <h1 className="font-sans text-lg font-semibold text-text-primary">FinIntel Copilot</h1>
            <p className="font-mono text-xs text-text-tertiary">AI-powered financial assistant</p>
          </div>
        </div>
        <button
          onClick={handleClearChat}
          className="rounded-lg border border-border-secondary bg-bg-elevated px-3 py-2 font-mono text-xs text-text-secondary transition-colors hover:bg-bg-tertiary hover:text-text-primary"
        >
          <Trash2 className="mr-1.5 inline-block h-3.5 w-3.5" />
          Clear chat
        </button>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        {messages.length === 0 && !showProgressBubble ? (
          /* Empty State - Simplified */
          <div className="flex h-full flex-col items-center justify-center">
            <div className="flex flex-col items-center text-center max-w-lg">
              {/* Logo */}
              <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br from-accent-primary/15 to-accent-secondary/10 border border-accent-primary/20 mb-8">
                <Sparkles className="h-8 w-8 text-accent-primary" />
              </div>
              
              {/* Title */}
              <h1 className="text-2xl font-bold text-text-primary mb-2">
                FinIntel Copilot
              </h1>
              
              {/* Description */}
              <p className="text-sm text-text-tertiary mb-12">
                Your intelligent financial assistant. Ask about companies, filings, alerts, and market insights.
              </p>

              {/* Suggested Questions */}
              <div className="w-full">
                <SuggestedQuestions
                  questions={SUGGESTED_QUESTIONS}
                  onQuestionClick={handleQuestionClick}
                />
              </div>
            </div>
          </div>
        ) : (
          /* Chat Messages */
          <div className="mx-auto max-w-4xl space-y-6">
            {messages.map((message) => (
              <MessageBubble key={message.id} {...message} />
            ))}
            
            {/* Inline Progress Bubble */}
            {showProgressBubble && (
              <AgentProgressBubble 
                steps={stepsWithIcons}
                isComplete={isComplete}
              />
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-border-secondary bg-bg-secondary px-6 py-4">
        <div className="mx-auto max-w-4xl space-y-3">
          {/* Floating Suggested Questions - Show on focus */}
          <AnimatePresence>
            {isInputFocused && messages.length > 0 && !isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                transition={{ duration: 0.2, ease: 'easeOut' }}
              >
                <SuggestedQuestions
                  questions={SUGGESTED_QUESTIONS.filter(
                    (q) => !messages.some((m) => m.content === q)
                  ).slice(0, 3)}
                  onQuestionClick={handleQuestionClick}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Chat Input */}
          <ChatInput 
            onSend={handleSendMessage} 
            isLoading={isLoading} 
            onFocusChange={setIsInputFocused}
          />
        </div>
      </div>
    </div>
  )
}
