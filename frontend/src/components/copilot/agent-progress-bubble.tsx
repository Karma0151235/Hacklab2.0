"use client"

import { motion, AnimatePresence } from 'framer-motion'
import { Bot, FileText, BarChart3, AlertTriangle, Loader2, CheckCircle2, ChevronUp, ChevronDown, Sparkles } from 'lucide-react'
import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import { AgentStep } from './agent-progress-modal'

interface AgentProgressBubbleProps {
  steps: AgentStep[]
  isComplete?: boolean
}

export function AgentProgressBubble({ steps, isComplete }: AgentProgressBubbleProps) {
  // Auto-collapse when complete
  const [isExpanded, setIsExpanded] = useState(!isComplete)
  
  const activeStep = steps.find(s => s.status === 'running')
  const completedCount = steps.filter(s => s.status === 'completed').length
  const totalCount = steps.length
  const progressPercent = Math.round((completedCount / totalCount) * 100)

  // Auto-collapse workflow diagram when completed
  useEffect(() => {
    if (isComplete) {
      setIsExpanded(false)
    }
  }, [isComplete])

  // Get the current status message
  const getCurrentMessage = () => {
    if (isComplete) return 'Analysis complete'
    if (activeStep) return activeStep.description
    return 'Initializing agents...'
  }

  // Get summary of completed agents
  const getCompletedSummary = () => {
    const completed = steps.filter(s => s.status === 'completed')
    return completed.map(s => s.name).join(', ')
  }

  return (
    <div className="flex gap-4">
      {/* Bot Avatar */}
      <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-bg-elevated text-text-primary">
        <Bot className="h-5 w-5" />
      </div>

      {/* Progress Content */}
      <div className="flex-1 min-w-0">
        {/* Main Bubble */}
        <div className="rounded-lg border border-border-secondary bg-gradient-to-br from-bg-tertiary to-bg-secondary overflow-hidden">
          {/* Header */}
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="w-full flex items-center justify-between p-4 hover:bg-bg-elevated/30 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-primary/15">
                <Sparkles className="h-4 w-4 text-accent-primary" />
              </div>
              <div className="text-left">
                <div className="text-sm font-semibold text-text-primary">
                  Multi-Agent Workflow
                </div>
                <div className="text-xs text-text-tertiary">
                  {isComplete ? 'Completed' : `Processing with ${totalCount} agents`}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {!isComplete && (
                <div className="flex items-center gap-2 bg-bg-elevated rounded-full px-3 py-1">
                  <Loader2 className="h-3 w-3 animate-spin text-accent-primary" />
                  <span className="text-xs font-medium text-text-secondary">{progressPercent}%</span>
                </div>
              )}
              {isComplete && (
                <div className="flex items-center gap-2 bg-success/10 rounded-full px-3 py-1">
                  <CheckCircle2 className="h-3 w-3 text-success" />
                  <span className="text-xs font-medium text-success">Done</span>
                </div>
              )}
              {isExpanded ? (
                <ChevronUp className="h-4 w-4 text-text-tertiary" />
              ) : (
                <ChevronDown className="h-4 w-4 text-text-tertiary" />
              )}
            </div>
          </button>

          {/* Expandable Content */}
          <AnimatePresence>
            {isExpanded && !isComplete && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="border-t border-border-secondary overflow-hidden"
              >
                {/* Workflow Diagram */}
                <div className="p-4 bg-bg-primary/30">
                  <div className="relative">
                    {/* Supervisor Node */}
                    <div className="flex justify-center mb-6">
                      <WorkflowNode
                        step={steps.find(s => s.id === 'supervisor')!}
                        isActive={activeStep?.id === 'supervisor'}
                      />
                    </div>

                    {/* Connection Lines with Animation */}
                    <svg className="absolute inset-0 w-full h-full pointer-events-none overflow-visible" style={{ top: 60 }}>
                      <defs>
                        <linearGradient id="flowGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor="rgb(var(--accent-primary))" stopOpacity="0" />
                          <stop offset="50%" stopColor="rgb(var(--accent-primary))" stopOpacity="1" />
                          <stop offset="100%" stopColor="rgb(var(--accent-primary))" stopOpacity="0" />
                        </linearGradient>
                      </defs>
                      
                      {/* RAG Line */}
                      <FlowingLine 
                        path="M 50% 0 L 16.67% 50"
                        isActive={activeStep?.id === 'rag' || activeStep?.id === 'supervisor'}
                      />
                      
                      {/* Financial Line */}
                      <FlowingLine 
                        path="M 50% 0 L 50% 50"
                        isActive={activeStep?.id === 'financial' || activeStep?.id === 'supervisor'}
                      />
                      
                      {/* Alert Line */}
                      <FlowingLine 
                        path="M 50% 0 L 83.33% 50"
                        isActive={activeStep?.id === 'alert' || activeStep?.id === 'supervisor'}
                      />
                    </svg>

                    {/* Agent Nodes */}
                    <div className="grid grid-cols-3 gap-3 mt-8">
                      <WorkflowNode
                        step={steps.find(s => s.id === 'rag')!}
                        isActive={activeStep?.id === 'rag'}
                        compact
                      />
                      <WorkflowNode
                        step={steps.find(s => s.id === 'financial')!}
                        isActive={activeStep?.id === 'financial'}
                        compact
                      />
                      <WorkflowNode
                        step={steps.find(s => s.id === 'alert')!}
                        isActive={activeStep?.id === 'alert'}
                        compact
                      />
                    </div>
                  </div>
                </div>

                {/* Current Status */}
                <div className="p-4 border-t border-border-secondary bg-bg-secondary/50">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">
                      <Loader2 className="h-5 w-5 animate-spin text-accent-primary" />
                    </div>
                    <div>
                      <div className="text-sm font-medium text-text-primary">
                        {getCurrentMessage()}
                      </div>
                      {activeStep && activeStep.logs.length > 0 && (
                        <div className="mt-1 text-xs text-text-tertiary">
                          {activeStep.logs[activeStep.logs.length - 1]}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Completed Summary (shows when collapsed after completion) */}
          {isComplete && !isExpanded && (
            <div className="px-4 pb-4">
              <div className="text-xs text-text-tertiary">
                Processed by: {getCompletedSummary()}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Flowing animated line component
function FlowingLine({ path, isActive }: { path: string; isActive: boolean }) {
  return (
    <g>
      {/* Base line */}
      <path
        d={path}
        stroke="currentColor"
        className="stroke-border-secondary"
        strokeWidth="1.5"
        fill="none"
      />
      
      {/* Animated flowing effect when active */}
      {isActive && (
        <motion.path
          d={path}
          stroke="url(#flowGradient)"
          strokeWidth="2"
          fill="none"
          strokeDasharray="20 80"
          initial={{ strokeDashoffset: 100 }}
          animate={{ strokeDashoffset: 0 }}
          transition={{
            repeat: Infinity,
            duration: 1.5,
            ease: "linear"
          }}
        />
      )}
    </g>
  )
}

function WorkflowNode({ step, isActive, compact }: { step: AgentStep; isActive?: boolean; compact?: boolean }) {
  const getStatusColor = () => {
    if (step.status === 'completed') return 'border-success/40 bg-success/5'
    if (step.status === 'running') return 'border-accent-primary/60 bg-accent-primary/5'
    if (step.status === 'error') return 'border-error/40 bg-error/5'
    return 'border-border-secondary bg-bg-elevated/50'
  }

  const getIconColor = () => {
    if (step.id === 'supervisor') return 'bg-fuchsia-500/15 text-fuchsia-400'
    if (step.id === 'rag') return 'bg-blue-500/15 text-blue-400'
    if (step.id === 'financial') return 'bg-emerald-500/15 text-emerald-400'
    return 'bg-amber-500/15 text-amber-400'
  }

  const getLabel = () => {
    if (step.id === 'supervisor') return 'Orchestrator'
    if (step.id === 'rag') return 'Context Retrieval'
    if (step.id === 'financial') return 'Financial Analysis'
    return 'Risk Assessment'
  }

  const getGlowAnimation = () => {
    if (step.id === 'supervisor') {
      return {
        boxShadow: [
          '0 0 15px rgba(217,70,239,0.3), 0 0 30px rgba(217,70,239,0.15)',
          '0 0 25px rgba(217,70,239,0.6), 0 0 50px rgba(217,70,239,0.3)',
          '0 0 15px rgba(217,70,239,0.3), 0 0 30px rgba(217,70,239,0.15)',
        ]
      }
    }
    if (step.id === 'rag') {
      return {
        boxShadow: [
          '0 0 15px rgba(59,130,246,0.3), 0 0 30px rgba(59,130,246,0.15)',
          '0 0 25px rgba(59,130,246,0.6), 0 0 50px rgba(59,130,246,0.3)',
          '0 0 15px rgba(59,130,246,0.3), 0 0 30px rgba(59,130,246,0.15)',
        ]
      }
    }
    if (step.id === 'financial') {
      return {
        boxShadow: [
          '0 0 15px rgba(16,185,129,0.3), 0 0 30px rgba(16,185,129,0.15)',
          '0 0 25px rgba(16,185,129,0.6), 0 0 50px rgba(16,185,129,0.3)',
          '0 0 15px rgba(16,185,129,0.3), 0 0 30px rgba(16,185,129,0.15)',
        ]
      }
    }
    return {
      boxShadow: [
        '0 0 15px rgba(245,158,11,0.3), 0 0 30px rgba(245,158,11,0.15)',
        '0 0 25px rgba(245,158,11,0.6), 0 0 50px rgba(245,158,11,0.3)',
        '0 0 15px rgba(245,158,11,0.3), 0 0 30px rgba(245,158,11,0.15)',
      ]
    }
  }

  return (
    <motion.div
      className={cn(
        "relative rounded-xl border px-3 py-3 transition-all",
        getStatusColor(),
        compact && "px-2 py-2"
      )}
      animate={isActive ? getGlowAnimation() : {}}
      transition={isActive ? {
        duration: 1.5,
        repeat: Infinity,
        ease: "easeInOut"
      } : {}}
    >
      <div className={cn("flex items-center gap-2", compact && "flex-col text-center")}>
        <div className={cn(
          "flex items-center justify-center rounded-lg",
          getIconColor(),
          compact ? "h-8 w-8" : "h-9 w-9"
        )}>
          <step.icon className={cn(compact ? "h-4 w-4" : "h-5 w-5")} />
        </div>
        <div>
          <div className={cn(
            "font-semibold text-text-primary",
            compact ? "text-xs" : "text-sm"
          )}>
            {step.name}
          </div>
          <div className={cn(
            "text-text-tertiary",
            compact ? "text-[10px]" : "text-xs"
          )}>
            {getLabel()}
          </div>
        </div>
      </div>

      {/* Progress indicator for active step */}
      {isActive && !compact && (
        <div className="mt-2 pt-2 border-t border-border-secondary/50">
          <div className="flex items-center justify-between text-xs">
            <span className="text-text-tertiary truncate max-w-[140px]">{step.description}</span>
            <Loader2 className="h-3 w-3 animate-spin text-accent-primary ml-2 flex-shrink-0" />
          </div>
        </div>
      )}

      {/* Status icons */}
      {step.status === 'completed' && (
        <div className="absolute -top-1 -right-1">
          <CheckCircle2 className="h-4 w-4 text-success bg-bg-primary rounded-full" />
        </div>
      )}
    </motion.div>
  )
}
