"use client"

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageCircle, Trash2, Bot, FileText, BarChart3, AlertTriangle, Sparkles } from 'lucide-react'
import { useCopilotStore } from '@/stores/use-copilot-store'
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
  const [showProgressBubble, setShowProgressBubble] = useState(false)
  const [agentSteps, setAgentSteps] = useState<AgentStep[]>(INITIAL_STEPS)
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const [isInputFocused, setIsInputFocused] = useState(false)
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
          setShowProgressBubble(false)
          setLoading(false)
          setActiveJobId(null)
        }
        if (status.status === 'error') {
          if (pollRef.current) {
            clearInterval(pollRef.current)
          }
          setShowProgressBubble(false)
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
        setShowProgressBubble(false)
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
    setShowProgressBubble(true)

    try {
      const job = await startCopilotJob(content)
      setActiveJobId(job.job_id)
      updateFromStatus(job)
      startPolling(job.job_id)
    } catch (error) {
      setShowProgressBubble(false)
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
      {/* Ambient background - FinIntel Logo */}
      {!isLoading && messages.length === 0 && (
        <div className="pointer-events-none absolute inset-0 -z-10 flex items-center justify-center">
          <div className="flex flex-col items-center gap-2 select-none">
            {/* FinIntel Logo Mark */}
            <div className="flex h-32 w-32 items-center justify-center rounded-3xl bg-gradient-to-br from-accent-primary/10 to-accent-secondary/5 border border-accent-primary/10">
              <span className="text-5xl font-bold bg-gradient-to-br from-accent-primary to-accent-secondary bg-clip-text text-transparent">
                FI
              </span>
            </div>
            <span className="text-xl font-semibold text-text-primary/10">FinIntel</span>
          </div>
        </div>
      )}

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        {messages.length === 0 ? (
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

            {/* Inline Progress Bubble */}
            {showProgressBubble && (
              <AgentProgressBubble steps={agentSteps} isComplete={false} />
            )}

            {/* Scroll anchor */}
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
