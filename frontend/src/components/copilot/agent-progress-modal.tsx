import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bot, FileText, BarChart3, AlertTriangle, CheckCircle2, Loader2, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AgentProgressModalProps {
  isOpen: boolean
  onClose: () => void
  steps: AgentStep[]
}

export interface AgentStep {
  id: string
  name: string
  description: string
  status: 'waiting' | 'running' | 'completed' | 'skipped' | 'error'
  logs: string[]
  icon: any
}

export function AgentProgressModal({ isOpen, onClose, steps }: AgentProgressModalProps) {
  const [selectedAgent, setSelectedAgent] = useState<string>('supervisor')

  // Auto-select running agent
  useEffect(() => {
    const runningStep = steps.find(s => s.status === 'running')
    if (runningStep) {
      setSelectedAgent(runningStep.id)
    }
  }, [steps])

  const currentStep = steps.find(s => s.id === selectedAgent) || steps[0]
  const activeAgent = steps.find(s => s.status === 'running')?.id
  const progressPercent = getProgressPercent(currentStep.status)

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-bg-primary/80 backdrop-blur-sm"
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="relative h-[600px] w-full max-w-4xl overflow-hidden rounded-xl border border-border-secondary bg-bg-secondary shadow-2xl"
        >
          {/* Header */}
              <div className="flex items-center justify-between border-b border-border-secondary px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent-primary/10">
                <Loader2 className="h-5 w-5 animate-spin text-accent-primary" />
              </div>
              <div>
                    <h2 className="font-sans text-lg font-bold text-text-primary">
                      Agent Orchestration
                    </h2>
                    <p className="font-sans text-xs text-text-tertiary">
                      Live backend progress and logs
                    </p>
              </div>
            </div>
            {/* 
               We usually disable closing while loading, but for UX freedom let's allow minimizing 
               or just show it's working. For now, strict modal.
            */}
          </div>

          <div className="flex h-[calc(100%-80px)]">
            {/* Left Panel: Workflow Tree */}
            <div className="w-1/3 border-r border-border-secondary bg-bg-tertiary/30 p-6">
              <div className="flex flex-col items-center gap-8">
                {/* Root: Supervisor */}
                <AgentNode 
                  step={steps.find(s => s.id === 'supervisor')!} 
                  isSelected={selectedAgent === 'supervisor'}
                  onClick={() => setSelectedAgent('supervisor')}
                  isRoot
                  isActive={activeAgent === 'supervisor'}
                />
                
                {/* Connections */}
                <div className="relative h-8 w-full">
                  <svg className="absolute inset-0 h-full w-full overflow-visible">
                    {activeAgent === 'rag' ? (
                      <motion.path
                        d="M50% 0 L50% 100%"
                        stroke="currentColor"
                        className="stroke-blue-400 drop-shadow-[0_0_10px_rgba(59,130,246,0.95)]"
                        strokeWidth="2.5"
                        strokeDasharray="6 6"
                        animate={{ strokeDashoffset: [12, 0] }}
                        transition={{ repeat: Infinity, duration: 1.1, ease: "linear" }}
                      />
                    ) : (
                      <path
                        d="M50% 0 L50% 100%"
                        stroke="currentColor"
                        className="stroke-border-secondary"
                        strokeWidth="2"
                        strokeDasharray="4 4"
                      />
                    )}
                    {activeAgent === 'financial' ? (
                      <motion.path
                        d="M15% 100% C15% 50, 50% 50, 50% 0"
                        stroke="currentColor"
                        className="stroke-emerald-400 drop-shadow-[0_0_10px_rgba(52,211,153,0.95)]"
                        strokeWidth="2.5"
                        strokeDasharray="6 6"
                        animate={{ strokeDashoffset: [12, 0] }}
                        transition={{ repeat: Infinity, duration: 1.1, ease: "linear" }}
                      />
                    ) : (
                      <path
                        d="M15% 100% C15% 50, 50% 50, 50% 0"
                        stroke="currentColor"
                        className="stroke-border-secondary"
                        strokeWidth="2"
                        strokeDasharray="4 4"
                      />
                    )}
                    {activeAgent === 'alert' ? (
                      <motion.path
                        d="M85% 100% C85% 50, 50% 50, 50% 0"
                        stroke="currentColor"
                        className="stroke-amber-400 drop-shadow-[0_0_10px_rgba(251,191,36,0.95)]"
                        strokeWidth="2.5"
                        strokeDasharray="6 6"
                        animate={{ strokeDashoffset: [12, 0] }}
                        transition={{ repeat: Infinity, duration: 1.1, ease: "linear" }}
                      />
                    ) : (
                      <path
                        d="M85% 100% C85% 50, 50% 50, 50% 0"
                        stroke="currentColor"
                        className="stroke-border-secondary"
                        strokeWidth="2"
                        strokeDasharray="4 4"
                      />
                    )}
                  </svg>
                </div>

                {/* Leaves: Sub-agents */}
                <div className="grid w-full grid-cols-3 gap-2">
                  <AgentNode 
                    step={steps.find(s => s.id === 'rag')!} 
                    isSelected={selectedAgent === 'rag'}
                    onClick={() => setSelectedAgent('rag')}
                    isActive={activeAgent === 'rag'}
                  />
                  <AgentNode 
                    step={steps.find(s => s.id === 'financial')!} 
                    isSelected={selectedAgent === 'financial'}
                    onClick={() => setSelectedAgent('financial')}
                    isActive={activeAgent === 'financial'}
                  />
                  <AgentNode 
                    step={steps.find(s => s.id === 'alert')!} 
                    isSelected={selectedAgent === 'alert'}
                    onClick={() => setSelectedAgent('alert')}
                    isActive={activeAgent === 'alert'}
                  />
                </div>
              </div>
            </div>

            {/* Right Panel: Agent Details & Logs */}
            <div className="flex-1 bg-bg-secondary p-6">
              <div className="mb-6 flex items-center gap-4">
                <div className={cn(
                  "flex h-12 w-12 items-center justify-center rounded-xl",
                   selectedAgent === 'supervisor' ? "bg-accent-primary/10 text-accent-primary" : 
                   selectedAgent === 'rag' ? "bg-blue-500/10 text-blue-500" :
                   selectedAgent === 'financial' ? "bg-green-500/10 text-green-500" :
                   "bg-amber-500/10 text-amber-500"
                )}>
                  <currentStep.icon className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="font-sans text-xl font-bold text-text-primary">
                    {currentStep.name}
                  </h3>
                  <p className="text-sm text-text-tertiary">
                    {currentStep.description}
                  </p>
                </div>
                <div className="ml-auto">
                    <StatusBadge status={currentStep.status} />
                </div>
              </div>

              {/* Progress bar */}
              <div className="mb-6">
                <div className="flex items-center justify-between text-xs text-text-tertiary">
                  <span>Progress</span>
                  <span>{progressPercent}%</span>
                </div>
                <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-bg-primary">
                  <div
                    className={cn(
                      "h-full rounded-full transition-all duration-700",
                      currentStep.status === 'running' && "bg-accent-primary",
                      currentStep.status === 'completed' && "bg-success",
                      currentStep.status === 'skipped' && "bg-warning",
                      currentStep.status === 'error' && "bg-error",
                      currentStep.status === 'waiting' && "bg-border-secondary"
                    )}
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>

              {/* Live Terminal/Logs */}
              <div className="h-[350px] overflow-hidden rounded-lg border border-border-secondary bg-bg-tertiary font-mono text-xs">
                <div className="flex items-center border-b border-border-secondary bg-bg-elevated px-4 py-2 text-text-tertiary">
                  <span className="mr-2 h-2 w-2 rounded-full bg-error"></span>
                  <span className="mr-2 h-2 w-2 rounded-full bg-warning"></span>
                  <span className="h-2 w-2 rounded-full bg-success"></span>
                  <span className="ml-4">terminal_output.log</span>
                </div>
                <div className="h-full overflow-y-auto p-4 text-text-secondary">
                  {currentStep.logs.length > 0 ? (
                    currentStep.logs.map((log, i) => (
                      <div key={i} className="mb-1.5 border-l-2 border-border-secondary pl-2 opacity-80 hover:opacity-100">
                        <span className="mr-2 text-text-tertiary">
                          {log.split(' - ')[0]}
                        </span>
                        <span>{log.split(' - ')[1] || log}</span>
                      </div>
                    ))
                  ) : (
                     <div className="flex h-full items-center justify-center text-text-tertiary italic">
                        Waiting for agent initialization...
                     </div>
                  )}
                  {currentStep.status === 'running' && (
                    <div className="animate-pulse text-accent-primary">_</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

function AgentNode({ step, isSelected, onClick, isRoot, isActive }: { step: AgentStep, isSelected: boolean, onClick: () => void, isRoot?: boolean, isActive?: boolean }) {
  if (!step) return null
  return (
    <button
      onClick={onClick}
      className={cn(
        "relative flex flex-col items-center rounded-xl border p-3 transition-all duration-300",
        isSelected 
          ? "border-accent-primary bg-accent-primary/5 shadow-[0_0_20px_-5px_rgba(var(--accent-primary),0.3)] scale-105" 
          : "border-border-secondary bg-bg-elevated hover:border-text-tertiary",
        step.status === 'completed' && !isSelected && "border-success/30 bg-success/5",
        step.status === 'skipped' && !isSelected && "border-warning/30 bg-warning/5",
        step.status === 'error' && !isSelected && "border-error/30 bg-error/5",
        step.status === 'running' && !isSelected && "shadow-[0_0_30px_-6px_rgba(56,189,248,0.8)] border-sky-400/40",
        isActive && step.id === 'supervisor' && "shadow-[0_0_40px_-4px_rgba(168,85,247,0.9)] border-fuchsia-400/50",
        isRoot ? "w-48" : "w-full"
      )}
    >
      <div className={cn(
        "mb-2 rounded-full p-2 transition-colors",
        step.status === 'running' && "animate-pulse bg-accent-primary/20",
        step.status === 'completed' && "text-success",
        step.status === 'skipped' && "text-warning",
        step.status === 'error' && "text-error",
        step.status === 'waiting' && "text-text-tertiary grayscale"
      )}>
        <step.icon className="h-5 w-5" />
      </div>
      <span className="text-xs font-semibold text-text-primary">{step.name}</span>
      <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-bg-primary">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-700",
            step.status === 'running' && "bg-accent-primary",
            step.status === 'completed' && "bg-success",
            step.status === 'skipped' && "bg-warning",
            step.status === 'error' && "bg-error",
            step.status === 'waiting' && "bg-border-secondary"
          )}
          style={{ width: `${getProgressPercent(step.status)}%` }}
        />
      </div>
      
      {/* Status Dot */}
      <div className="absolute -right-1 -top-1">
        {step.status === 'completed' && <CheckCircle2 className="h-4 w-4 text-success fill-bg-secondary" />}
        {step.status === 'running' && (
           <span className="relative flex h-3 w-3">
             <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent-primary opacity-75"></span>
             <span className="relative inline-flex h-3 w-3 rounded-full bg-accent-primary"></span>
           </span>
        )}
        {step.status === 'error' && <CheckCircle2 className="h-4 w-4 text-error fill-bg-secondary" />}
        {step.status === 'skipped' && <CheckCircle2 className="h-4 w-4 text-warning fill-bg-secondary" />}
      </div>
    </button>
  )
}

function StatusBadge({ status }: { status: string }) {
    if (status === 'completed') return <span className="rounded-full bg-success/10 px-2.5 py-1 text-xs font-medium text-success">Completed</span>
    if (status === 'running') return <span className="rounded-full bg-accent-primary/10 px-2.5 py-1 text-xs font-medium text-accent-primary animate-pulse">Running</span>
    if (status === 'skipped') return <span className="rounded-full bg-warning/10 px-2.5 py-1 text-xs font-medium text-warning">Skipped</span>
    if (status === 'error') return <span className="rounded-full bg-error/10 px-2.5 py-1 text-xs font-medium text-error">Error</span>
    return <span className="rounded-full bg-bg-elevated px-2.5 py-1 text-xs font-medium text-text-tertiary">Waiting</span>
}

function getProgressPercent(status: AgentStep['status']) {
  if (status === 'completed') return 100
  if (status === 'error') return 100
  if (status === 'skipped') return 0
  if (status === 'running') return 60
  return 0
}
