import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { CopilotAnswer, SentimentOutput } from "@/lib/types/api";
import {
  Bot,
  FileText,
  BarChart3,
  AlertTriangle,
  TrendingUp,
  LucideIcon,
} from "lucide-react";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  copilotAnswer?: CopilotAnswer;
  timestamp: string;
}

export interface AgentStepState {
  id: string;
  name: string;
  description: string;
  status: "waiting" | "running" | "completed" | "error" | "skipped";
  logs: string[];
}

export interface ChatSession {
  id: string;
  title: string;
  autoTitleGenerated: boolean;
  messages: Message[];
  context: {
    companyCode?: string;
    startDate?: string;
    endDate?: string;
  };
  activeJobId: string | null;
  agentSteps: AgentStepState[];
  showProgressBubble: boolean;
  fetchLatestNews: boolean;
  sentimentResults: SentimentOutput | null;
  isLoading: boolean;
  createdAt: string;
  updatedAt: string;
}

interface CopilotStore {
  // Multi-chat support
  chats: Record<string, ChatSession>;
  currentChatId: string;

  // Chat management
  createNewChat: (title?: string) => string;
  deleteChat: (chatId: string) => void;
  switchChat: (chatId: string) => void;
  renameChat: (chatId: string, newTitle: string) => void;
  setAutoTitleGenerated: (chatId: string, generated: boolean) => void;

  // Message operations
  addMessage: (message: Message) => void;
  setLoading: (loading: boolean) => void;
  setContext: (context: {
    companyCode?: string;
    startDate?: string;
    endDate?: string;
  }) => void;
  clearMessages: () => void;
  clearContext: () => void;

  // Job management actions
  setActiveJob: (jobId: string | null) => void;
  setAgentSteps: (steps: AgentStepState[]) => void;
  updateAgentStep: (stepId: string, update: Partial<AgentStepState>) => void;
  setShowProgressBubble: (show: boolean) => void;
  resetJobState: () => void;

  // Sentiment actions
  setFetchLatestNews: (fetch: boolean) => void;
  setSentimentResults: (results: SentimentOutput | null) => void;
}

const INITIAL_STEPS: AgentStepState[] = [
  {
    id: "supervisor",
    name: "Supervisor Agent",
    description: "Orchestrating workflow...",
    status: "waiting",
    logs: [],
  },
  {
    id: "rag",
    name: "RAG Agent",
    description: "Searching documents...",
    status: "waiting",
    logs: [],
  },
  {
    id: "financial",
    name: "Financial Agent",
    description: "Analyzing metrics...",
    status: "waiting",
    logs: [],
  },
  {
    id: "alert",
    name: "Alert Agent",
    description: "Checking risks...",
    status: "waiting",
    logs: [],
  },
  {
    id: "sentiment",
    name: "Sentiment Agent",
    description: "Analyzing market sentiment...",
    status: "waiting",
    logs: [],
  },
];

const generateChatId = () =>
  `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

const createNewChatSession = (title?: string): ChatSession => {
  const now = new Date().toISOString();
  const defaultTitle = title || "New Chat";
  return {
    id: generateChatId(),
    title: defaultTitle,
    autoTitleGenerated: false,
    messages: [],
    context: {},
    activeJobId: null,
    agentSteps: INITIAL_STEPS.map((s) => ({ ...s })),
    showProgressBubble: false,
    fetchLatestNews: false,
    sentimentResults: null,
    isLoading: false,
    createdAt: now,
    updatedAt: now,
  };
};

export const useCopilotStore = create<CopilotStore>()(
  persist(
    (set, get) => {
      const initialChat = createNewChatSession();

      return {
        chats: { [initialChat.id]: initialChat },
        currentChatId: initialChat.id,

        // Chat management
        createNewChat: (title?: string) => {
          const newChat = createNewChatSession(title);
          set((state) => ({
            chats: { ...state.chats, [newChat.id]: newChat },
            currentChatId: newChat.id,
          }));
          return newChat.id;
        },

        deleteChat: (chatId: string) => {
          set((state) => {
            const newChats = { ...state.chats };
            delete newChats[chatId];

            // If deleting current chat, switch to another one
            let newCurrentId = state.currentChatId;
            if (newCurrentId === chatId) {
              const remainingIds = Object.keys(newChats);
              if (remainingIds.length === 0) {
                // Create a new chat if all are deleted
                const newChat = createNewChatSession();
                newChats[newChat.id] = newChat;
                newCurrentId = newChat.id;
              } else {
                newCurrentId = remainingIds[0];
              }
            }

            return {
              chats: newChats,
              currentChatId: newCurrentId,
            };
          });
        },

        switchChat: (chatId: string) => {
          set({ currentChatId: chatId });
        },

        renameChat: (chatId: string, newTitle: string) => {
          set((state) => ({
            chats: {
              ...state.chats,
              [chatId]: {
                ...state.chats[chatId],
                title: newTitle,
                autoTitleGenerated: true,
                updatedAt: new Date().toISOString(),
              },
            },
          }));
        },

        setAutoTitleGenerated: (chatId: string, generated: boolean) => {
          set((state) => {
            const chat = state.chats[chatId];
            if (!chat) return state;
            return {
              chats: {
                ...state.chats,
                [chatId]: {
                  ...chat,
                  autoTitleGenerated: generated,
                  updatedAt: new Date().toISOString(),
                },
              },
            };
          });
        },

        // Message operations on current chat
        addMessage: (message) =>
          set((state) => {
            const currentChat = state.chats[state.currentChatId];
            if (!currentChat) return state;
            return {
              chats: {
                ...state.chats,
                [state.currentChatId]: {
                  ...currentChat,
                  messages: [...currentChat.messages, message],
                  updatedAt: new Date().toISOString(),
                },
              },
            };
          }),

        setLoading: (loading) =>
          set((state) => {
            const currentChat = state.chats[state.currentChatId];
            if (!currentChat) return state;
            return {
              chats: {
                ...state.chats,
                [state.currentChatId]: {
                  ...currentChat,
                  isLoading: loading,
                },
              },
            };
          }),

        setContext: (context) =>
          set((state) => {
            const currentChat = state.chats[state.currentChatId];
            if (!currentChat) return state;
            return {
              chats: {
                ...state.chats,
                [state.currentChatId]: {
                  ...currentChat,
                  context,
                },
              },
            };
          }),

        clearMessages: () =>
          set((state) => {
            const currentChat = state.chats[state.currentChatId];
            if (!currentChat) return state;
            return {
              chats: {
                ...state.chats,
                [state.currentChatId]: {
                  ...currentChat,
                  messages: [],
                  updatedAt: new Date().toISOString(),
                },
              },
            };
          }),

        clearContext: () =>
          set((state) => {
            const currentChat = state.chats[state.currentChatId];
            if (!currentChat) return state;
            return {
              chats: {
                ...state.chats,
                [state.currentChatId]: {
                  ...currentChat,
                  context: {},
                },
              },
            };
          }),

        setActiveJob: (jobId) =>
          set((state) => {
            const currentChat = state.chats[state.currentChatId];
            if (!currentChat) return state;
            return {
              chats: {
                ...state.chats,
                [state.currentChatId]: {
                  ...currentChat,
                  activeJobId: jobId,
                },
              },
            };
          }),

        setAgentSteps: (steps) =>
          set((state) => {
            const currentChat = state.chats[state.currentChatId];
            if (!currentChat) return state;
            return {
              chats: {
                ...state.chats,
                [state.currentChatId]: {
                  ...currentChat,
                  agentSteps: steps,
                },
              },
            };
          }),

        updateAgentStep: (stepId, update) =>
          set((state) => {
            const currentChat = state.chats[state.currentChatId];
            if (!currentChat) return state;
            return {
              chats: {
                ...state.chats,
                [state.currentChatId]: {
                  ...currentChat,
                  agentSteps: currentChat.agentSteps.map((step) =>
                    step.id === stepId ? { ...step, ...update } : step,
                  ),
                },
              },
            };
          }),

        setShowProgressBubble: (show) =>
          set((state) => {
            const currentChat = state.chats[state.currentChatId];
            if (!currentChat) return state;
            return {
              chats: {
                ...state.chats,
                [state.currentChatId]: {
                  ...currentChat,
                  showProgressBubble: show,
                },
              },
            };
          }),

        resetJobState: () =>
          set((state) => {
            const currentChat = state.chats[state.currentChatId];
            if (!currentChat) return state;
            return {
              chats: {
                ...state.chats,
                [state.currentChatId]: {
                  ...currentChat,
                  activeJobId: null,
                  agentSteps: INITIAL_STEPS.map((s) => ({ ...s })),
                  showProgressBubble: false,
                  isLoading: false,
                },
              },
            };
          }),

        setFetchLatestNews: (fetch) =>
          set((state) => {
            const currentChat = state.chats[state.currentChatId];
            if (!currentChat) return state;
            return {
              chats: {
                ...state.chats,
                [state.currentChatId]: {
                  ...currentChat,
                  fetchLatestNews: fetch,
                },
              },
            };
          }),

        setSentimentResults: (results) =>
          set((state) => {
            const currentChat = state.chats[state.currentChatId];
            if (!currentChat) return state;
            return {
              chats: {
                ...state.chats,
                [state.currentChatId]: {
                  ...currentChat,
                  sentimentResults: results,
                },
              },
            };
          }),
      };
    },
    {
      name: "finintel-copilot-storage",
      storage: createJSONStorage(() => localStorage),
      // Persist all chats and current chat ID
      partialize: (state) => ({
        chats: state.chats,
        currentChatId: state.currentChatId,
      }),
    },
  ),
);

// Export initial steps for use in components
export { INITIAL_STEPS };
