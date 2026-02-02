"use client"

import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Trash2, Bot, FileText, BarChart3, AlertTriangle, Sparkles, Send } from 'lucide-react'
import { useCopilotStore, INITIAL_STEPS, AgentStepState } from '@/stores/use-copilot-store'
import { MessageBubble } from './message-bubble'
import { getCopilotResult, getCopilotStatus, startCopilotJob } from '@/lib/api/copilot'
import { AgentProgressBubble } from './agent-progress-bubble'
import { AgentStep } from './agent-progress-modal'
import { CopilotJobStatus } from '@/lib/types/api'

const SUGGESTED_QUESTIONS = [
  'What are the financials of Foodie Media Berhad?',
  'Show me detailed analysis of Foodie Media Berhad',
  'Any recent alerts for Foodie Media Berhad?',
]

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
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const [inputValue, setInputValue] = useState('')
  const pollRef = useRef<NodeJS.Timeout | null>(null)
  const hasResumedRef = useRef(false)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (activeJobId && showProgressBubble && !hasResumedRef.current) {
      hasResumedRef.current = true
      setLoading(true)
      startPolling(activeJobId)
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [activeJobId, showProgressBubble])

  const updateFromStatus = (status: CopilotJobStatus) => {
    const updated = agentSteps.map(step => {
      const agentStatus = status.agents?.[step.id]
      if (!agentStatus) return step
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
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const status = await getCopilotStatus(jobId)
        updateFromStatus(status)
        if (status.status === 'completed') {
          if (pollRef.current) clearInterval(pollRef.current)
          const answer = await getCopilotResult(jobId)
          addMessage({
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: answer.answer_text,
            copilotAnswer: answer,
            timestamp: new Date().toISOString(),
          })
          resetJobState()
        }
        if (status.status === 'error') {
          if (pollRef.current) clearInterval(pollRef.current)
          resetJobState()
          addMessage({
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: status.error || 'Copilot job failed. Please try again.',
            timestamp: new Date().toISOString(),
          })
        }
      } catch {
        if (pollRef.current) clearInterval(pollRef.current)
        resetJobState()
        addMessage({
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Error retrieving progress. Please try again.',
          timestamp: new Date().toISOString(),
        })
      }
    }, 1000)
  }

  const handleSend = async () => {
    const content = inputValue.trim()
    if (!content || isLoading) return
    
    setInputValue('')
    addMessage({
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    })

    setLoading(true)
    setAgentSteps(INITIAL_STEPS.map(s => ({ ...s, status: 'waiting', logs: [] })))
    setShowProgressBubble(true)

    try {
      const job = await startCopilotJob(content)
      setActiveJob(job.job_id)
      updateFromStatus(job)
      startPolling(job.job_id)
    } catch {
      resetJobState()
      addMessage({
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Failed to start. Please try again.',
        timestamp: new Date().toISOString(),
      })
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleClear = () => {
    clearMessages()
    resetJobState()
    if (pollRef.current) clearInterval(pollRef.current)
  }

  const stepsWithIcons = mapStepsWithIcons(agentSteps)
  const isComplete = agentSteps.every(s => s.status === 'completed' || s.status === 'skipped')
  const hasMessages = messages.length > 0 || showProgressBubble

  return (
    <div className="flex h-full flex-col">
      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto">
        {!hasMessages ? (
          // Empty State - Centered
          <div className="flex h-full items-center justify-center p-4">
            <div className="max-w-md text-center">
              <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500/20 to-blue-500/20">
                <Sparkles className="h-6 w-6 text-cyan-400" />
              </div>
              <h1 className="mb-2 text-xl font-semibold text-white">FinIntel Copilot</h1>
              <p className="mb-8 text-sm text-gray-400">
                Ask about companies, filings, or financial insights
              </p>
              <div className="space-y-2">
                {SUGGESTED_QUESTIONS.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => { setInputValue(q); inputRef.current?.focus() }}
                    className="block w-full rounded-lg border border-gray-700 bg-gray-800/50 px-4 py-2.5 text-left text-sm text-gray-300 transition-colors hover:border-cyan-500/50 hover:bg-gray-800"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // Messages
          <div className="mx-auto max-w-3xl space-y-4 p-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} {...msg} />
            ))}
            {showProgressBubble && (
              <AgentProgressBubble steps={stepsWithIcons} isComplete={isComplete} />
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-800 bg-gray-900/50 p-3">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-end gap-2 rounded-xl border border-gray-700 bg-gray-800/80 p-2">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about financials, filings, alerts..."
              rows={1}
              className="flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-white placeholder-gray-500 outline-none"
              style={{ minHeight: '36px', maxHeight: '120px' }}
            />
            <div className="flex items-center gap-1">
              {messages.length > 0 && (
                <button
                  onClick={handleClear}
                  className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-700 hover:text-gray-300"
                  title="Clear chat"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || isLoading}
                className="rounded-lg bg-cyan-600 p-2 text-white transition-colors hover:bg-cyan-500 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
          <p className="mt-2 text-center text-[10px] text-gray-600">
            FinIntel may produce inaccurate information
          </p>
        </div>
      </div>
    </div>
  )
}
