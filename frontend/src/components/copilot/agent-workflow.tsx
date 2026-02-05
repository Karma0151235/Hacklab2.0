import { cn } from '@/lib/utils'
import { Bot, FileText, BarChart3, AlertTriangle, TrendingUp, CheckCircle2 } from 'lucide-react'
import { motion } from 'framer-motion'

interface AgentWorkflowProps {
  usedAgents: string[]
}

export function AgentWorkflow({ usedAgents }: AgentWorkflowProps) {
  const agents = [
    {
      id: 'rag',
      name: 'RAG Agent',
      icon: FileText,
      description: 'Knowledge Retrieval',
      color: 'text-blue-400',
      bgColor: 'bg-blue-400/10',
      borderColor: 'border-blue-400/20',
    },
    {
      id: 'financial',
      name: 'Financial Agent',
      icon: BarChart3,
      description: 'Metric Analysis',
      color: 'text-green-400',
      bgColor: 'bg-green-400/10',
      borderColor: 'border-green-400/20',
    },
    {
      id: 'alert',
      name: 'Alert Agent',
      icon: AlertTriangle,
      description: 'Risk Monitoring',
      color: 'text-amber-400',
      bgColor: 'bg-amber-400/10',
      borderColor: 'border-amber-400/20',
    },
    {
      id: 'sentiment',
      name: 'Sentiment Agent',
      icon: TrendingUp,
      description: 'Market Sentiment',
      color: 'text-purple-400',
      bgColor: 'bg-purple-400/10',
      borderColor: 'border-purple-400/20',
    },
  ]

  // Filter agents to only those that were used
  // Or show all but dim the unused ones? 
  // Let's show all for context, but highlight used ones.
  
  return (
    <div className="mb-6 rounded-lg border border-border-secondary bg-bg-tertiary/50 p-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-sans text-sm font-semibold text-text-primary">
          Agent Workflow Execution
        </h3>
        <span className="rounded-full bg-accent-primary/10 px-2 py-1 text-xs font-medium text-accent-primary">
          Completed
        </span>
      </div>

      <div className="relative flex flex-col items-center gap-8">
        {/* Supervisor Node */}
        <div className="relative z-10 flex flex-col items-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-accent-primary/30 bg-accent-primary/10 shadow-[0_0_15px_-3px_rgba(var(--accent-primary),0.3)]">
            <Bot className="h-6 w-6 text-accent-primary" />
          </div>
          <div className="mt-2 text-center">
            <p className="font-sans text-sm font-bold text-text-primary">Supervisor Agent</p>
            <p className="text-xs text-text-tertiary">Orchestrator</p>
          </div>
        </div>

        {/* Connection Lines (SVG) */}
        <div className="absolute top-12 h-8 w-full">
          <svg className="h-full w-full overflow-visible">
            {agents.map((agent, index) => {
              // Calculate positions for 4 agents
              // 0: 12.5%, 1: 37.5%, 2: 62.5%, 3: 87.5%
              const x2 = `${12.5 + (index * 25)}%`
              return (
                <path
                  key={agent.id}
                  d={`M50% 0 C50% 15, ${x2} 15, ${x2} 32`}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className={cn(
                    'transition-all duration-1000',
                    usedAgents.includes(agent.id)
                      ? 'text-accent-primary opacity-50'
                      : 'text-border-secondary opacity-20'
                  )}
                  strokeDasharray={usedAgents.includes(agent.id) ? "none" : "4 4"}
                />
              )
            })}
          </svg>
        </div>

        {/* Sub-Agents Row */}
        <div className="grid w-full grid-cols-4 gap-4">
          {agents.map((agent) => {
            const isUsed = usedAgents.includes(agent.id)
            return (
              <div
                key={agent.id}
                className={cn(
                  'flex flex-col items-center rounded-lg border p-3 transition-all',
                  isUsed
                    ? `${agent.bgColor} ${agent.borderColor} opacity-100`
                    : 'border-transparent bg-bg-elevated opacity-40 grayscale'
                )}
              >
                <div className="relative mb-2">
                  <agent.icon className={cn('h-5 w-5', isUsed ? agent.color : 'text-text-tertiary')} />
                  {isUsed && (
                    <div className="absolute -right-1 -top-1 rounded-full bg-bg-tertiary text-success">
                      <CheckCircle2 className="h-3 w-3 fill-current" />
                    </div>
                  )}
                </div>
                <p className="text-center font-sans text-xs font-semibold text-text-primary">
                  {agent.name}
                </p>
                <p className="text-center text-[10px] text-text-tertiary">
                  {agent.description}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
