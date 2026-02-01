import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { CopilotAnswer } from '@/lib/types/api'
import { Bot, FileText, BarChart3, AlertTriangle, LucideIcon } from 'lucide-react'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  copilotAnswer?: CopilotAnswer
  timestamp: string
}

export interface AgentStepState {
  id: string
  name: string
  description: string
  status: 'waiting' | 'running' | 'completed' | 'error' | 'skipped'
  logs: string[]
}

interface CopilotStore {
  messages: Message[]
  isLoading: boolean
  context: {
    companyCode?: string
    startDate?: string
    endDate?: string
  }
  // Active job state for workflow persistence
  activeJobId: string | null
  agentSteps: AgentStepState[]
  showProgressBubble: boolean
  
  addMessage: (message: Message) => void
  setLoading: (loading: boolean) => void
  setContext: (context: { companyCode?: string; startDate?: string; endDate?: string }) => void
  clearMessages: () => void
  clearContext: () => void
  
  // Job management actions
  setActiveJob: (jobId: string | null) => void
  setAgentSteps: (steps: AgentStepState[]) => void
  updateAgentStep: (stepId: string, update: Partial<AgentStepState>) => void
  setShowProgressBubble: (show: boolean) => void
  resetJobState: () => void
}

const INITIAL_STEPS: AgentStepState[] = [
  {
    id: 'supervisor',
    name: 'Supervisor Agent',
    description: 'Orchestrating workflow...',
    status: 'waiting',
    logs: [],
  },
  {
    id: 'rag',
    name: 'RAG Agent',
    description: 'Searching documents...',
    status: 'waiting',
    logs: [],
  },
  {
    id: 'financial',
    name: 'Financial Agent',
    description: 'Analyzing metrics...',
    status: 'waiting',
    logs: [],
  },
  {
    id: 'alert',
    name: 'Alert Agent',
    description: 'Checking risks...',
    status: 'waiting',
    logs: [],
  }
]

export const useCopilotStore = create<CopilotStore>()(
  persist(
    (set) => ({
      messages: [],
      isLoading: false,
      context: {},
      activeJobId: null,
      agentSteps: INITIAL_STEPS,
      showProgressBubble: false,

      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),

      setLoading: (loading) =>
        set({ isLoading: loading }),

      setContext: (context) =>
        set({ context }),

      clearMessages: () =>
        set({ messages: [] }),

      clearContext: () =>
        set({ context: {} }),
        
      setActiveJob: (jobId) =>
        set({ activeJobId: jobId }),
        
      setAgentSteps: (steps) =>
        set({ agentSteps: steps }),
        
      updateAgentStep: (stepId, update) =>
        set((state) => ({
          agentSteps: state.agentSteps.map((step) =>
            step.id === stepId ? { ...step, ...update } : step
          ),
        })),
        
      setShowProgressBubble: (show) =>
        set({ showProgressBubble: show }),
        
      resetJobState: () =>
        set({
          activeJobId: null,
          agentSteps: INITIAL_STEPS,
          showProgressBubble: false,
          isLoading: false,
        }),
    }),
    {
      name: 'finintel-copilot-storage',
      storage: createJSONStorage(() => localStorage),
      // Persist messages, context, and active job state
      partialize: (state) => ({
        messages: state.messages,
        context: state.context,
        activeJobId: state.activeJobId,
        agentSteps: state.agentSteps,
        showProgressBubble: state.showProgressBubble,
      }),
    }
  )
)

// Export initial steps for use in components
export { INITIAL_STEPS }
