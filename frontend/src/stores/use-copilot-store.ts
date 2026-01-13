import { create } from 'zustand'
import { CopilotAnswer } from '@/lib/types/api'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  copilotAnswer?: CopilotAnswer
  timestamp: string
}

interface CopilotStore {
  messages: Message[]
  isLoading: boolean
  context: {
    companyCode?: string
    startDate?: string
    endDate?: string
  }
  addMessage: (message: Message) => void
  setLoading: (loading: boolean) => void
  setContext: (context: { companyCode?: string; startDate?: string; endDate?: string }) => void
  clearMessages: () => void
  clearContext: () => void
}

export const useCopilotStore = create<CopilotStore>((set) => ({
  messages: [],
  isLoading: false,
  context: {},

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
}))
