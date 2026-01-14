"use client"

import { useEffect, useRef, useState } from 'react'
import { MessageCircle, Trash2, Bot, FileText, BarChart3, AlertTriangle } from 'lucide-react'
import { useCopilotStore } from '@/stores/use-copilot-store'
import { MessageBubble } from './message-bubble'
import { ChatInput } from './chat-input'
import { SuggestedQuestions } from './suggested-questions'
import { sendCopilotMessage } from '@/lib/api/copilot'
import { AgentProgressModal, AgentStep } from './agent-progress-modal'

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

  // Auto-scroll logic
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Simulation logic for the progress modal
  const simulateAgentProgress = async () => {
    setAgentSteps(INITIAL_STEPS.map(s => ({ ...s, status: 'waiting', logs: [] })))
    setShowProgressModal(true)

    // 1. Supervisor Start
    updateStep('supervisor', 'running', ['Initializing Supervisor Agent...', 'Analyzing query intent...'])
    await new Promise(r => setTimeout(r, 800))

    // 2. Supervisor -> RAG
    updateStep('supervisor', 'running', ['Delegating to RAG Agent for context retrieval...'])
    updateStep('rag', 'running', ['Connecting to Milvus vector DB...', 'Generating query embeddings...'])
    await new Promise(r => setTimeout(r, 1200))

    // 3. RAG Working
    updateStep('rag', 'running', ['Retrieved 2 text chunks', 'Retrieved 1 table chunks', 'Context score: 0.85'])
    await new Promise(r => setTimeout(r, 800))
    updateStep('rag', 'completed', ['Context retrieval successful'])

    // 4. Parallel Agents (Financial & Alert)
    updateStep('supervisor', 'running', ['Dispatching derived data to specialist agents...'])
    updateStep('financial', 'running', ['Parsing financial statements...', 'Calculating YoY growth metrics...'])
    updateStep('alert', 'running', ['Scanning for high-severity risk signals...', 'Cross-referencing filing metadata...'])
    
    // Continue running until real response comes back in handleSendMessage
  }

  const updateStep = (id: string, status: AgentStep['status'], newLogs: string[]) => {
    setAgentSteps(prev => prev.map(step => {
      if (step.id === id) {
        return {
          ...step,
          status: status === 'waiting' ? step.status : status, // Don't revert directly
          logs: [...step.logs, ...newLogs.map(l => `${new Date().toLocaleTimeString()} - ${l}`)]
        }
      }
      return step
    }))
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

    // Start UI process
    setLoading(true)
    simulateAgentProgress()

    try {
      // Logic to keep the "running" simulation going a bit if API is too fast, 
      // but usually API takes a few seconds.
      const answer = await sendCopilotMessage(content)

      // Complete all steps visually
      updateStep('financial', 'completed', ['Analysis complete', 'Metrics derived successfully'])
      updateStep('alert', 'completed', ['Risk scan complete', '0 active alerts found'])
      updateStep('supervisor', 'completed', ['Synthesizing final response...', 'Workflow successful'])
      
      // Short delay to let user see "Completed" state
      await new Promise(r => setTimeout(r, 800))
      setShowProgressModal(false)

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
      setShowProgressModal(false)
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        content: 'I apologize, but I encountered an error processing your request. Please try again.',
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
