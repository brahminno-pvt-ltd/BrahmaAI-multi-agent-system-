/**
 * BrahmaAI Global Store
 * Zustand-based state management for agent events, chat, memory
 */

import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export type AgentEvent = {
  event: string
  timestamp: number
  data: Record<string, unknown>
}

export type Message = {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  events?: AgentEvent[]
  timestamp: number
  isStreaming?: boolean
  taskId?: string
}

export type MemoryItem = {
  id: string
  text: string
  metadata: Record<string, unknown>
  created_at: number
  score?: number
}

type BrahmaStore = {
  // Session
  sessionId: string
  setSessionId: (id: string) => void

  // Auth
  token: string | null
  username: string | null
  setAuth: (token: string, username: string) => void
  clearAuth: () => void

  // Chat
  messages: Message[]
  addMessage: (msg: Message) => void
  updateMessage: (id: string, updates: Partial<Message>) => void
  clearMessages: () => void
  isAgentRunning: boolean
  setAgentRunning: (running: boolean) => void

  // Agent events (live log)
  liveEvents: AgentEvent[]
  addEvent: (event: AgentEvent) => void
  clearEvents: () => void
  selectedTaskEvents: AgentEvent[]
  setSelectedTaskEvents: (events: AgentEvent[]) => void

  // Memory
  memories: MemoryItem[]
  setMemories: (memories: MemoryItem[]) => void
  addMemory: (memory: MemoryItem) => void
  removeMemory: (id: string) => void

  // UI
  activeTab: 'chat' | 'dashboard' | 'logs' | 'memory'
  setActiveTab: (tab: 'chat' | 'dashboard' | 'logs' | 'memory') => void
  sidebarOpen: boolean
  toggleSidebar: () => void
}

const generateId = () => Math.random().toString(36).slice(2, 11)

export const useBrahmaStore = create<BrahmaStore>()(
  devtools(
    (set, get) => ({
      // Session
      sessionId: generateId(),
      setSessionId: (id) => set({ sessionId: id }),

      // Auth
      token: typeof window !== 'undefined' ? localStorage.getItem('brahma_token') : null,
      username: typeof window !== 'undefined' ? localStorage.getItem('brahma_username') : null,
      setAuth: (token, username) => {
        if (typeof window !== 'undefined') {
          localStorage.setItem('brahma_token', token)
          localStorage.setItem('brahma_username', username)
        }
        set({ token, username })
      },
      clearAuth: () => {
        if (typeof window !== 'undefined') {
          localStorage.removeItem('brahma_token')
          localStorage.removeItem('brahma_username')
        }
        set({ token: null, username: null })
      },

      // Chat
      messages: [],
      addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
      updateMessage: (id, updates) =>
        set((s) => ({
          messages: s.messages.map((m) => (m.id === id ? { ...m, ...updates } : m)),
        })),
      clearMessages: () => set({ messages: [] }),
      isAgentRunning: false,
      setAgentRunning: (running) => set({ isAgentRunning: running }),

      // Events
      liveEvents: [],
      addEvent: (event) =>
        set((s) => ({
          liveEvents: [...s.liveEvents.slice(-199), event], // Keep last 200
        })),
      clearEvents: () => set({ liveEvents: [] }),
      selectedTaskEvents: [],
      setSelectedTaskEvents: (events) => set({ selectedTaskEvents: events }),

      // Memory
      memories: [],
      setMemories: (memories) => set({ memories }),
      addMemory: (memory) => set((s) => ({ memories: [memory, ...s.memories] })),
      removeMemory: (id) =>
        set((s) => ({ memories: s.memories.filter((m) => m.id !== id) })),

      // UI
      activeTab: 'chat',
      setActiveTab: (tab) => set({ activeTab: tab }),
      sidebarOpen: true,
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
    }),
    { name: 'BrahmaStore' }
  )
)
