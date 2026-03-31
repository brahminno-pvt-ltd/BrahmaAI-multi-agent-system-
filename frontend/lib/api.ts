/**
 * BrahmaAI API Client
 * Typed wrapper around the FastAPI backend.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, err.detail || 'Request failed')
  }
  return res.json()
}

// ─── Auth ────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (username: string, password: string) =>
    request<{ access_token: string; username: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  me: (token: string) =>
    request<{ username: string; authenticated: boolean }>('/api/auth/me', {}, token),
}

// ─── Chat ─────────────────────────────────────────────────────────────────────

export type StreamEvent = {
  event: string
  timestamp: number
  data: Record<string, unknown>
}

export const chatApi = {
  streamMessage: async (
    message: string,
    sessionId: string,
    onEvent: (event: StreamEvent) => void,
    token?: string | null
  ): Promise<void> => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    if (token) headers['Authorization'] = `Bearer ${token}`

    const res = await fetch(`${BASE_URL}/api/chat/message`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ message, session_id: sessionId, stream: true }),
    })

    if (!res.ok) throw new ApiError(res.status, 'Chat request failed')

    const reader = res.body?.getReader()
    if (!reader) throw new Error('No response body')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const raw = line.slice(6).trim()
          if (raw === '[DONE]') return
          try {
            const event = JSON.parse(raw) as StreamEvent
            onEvent(event)
          } catch {
            // ignore parse errors
          }
        }
      }
    }
  },

  getHistory: (sessionId: string, token?: string | null) =>
    request<{ messages: unknown[]; count: number }>(
      `/api/chat/history/${sessionId}`,
      {},
      token
    ),

  clearHistory: (sessionId: string, token?: string | null) =>
    request<{ status: string }>(`/api/chat/history/${sessionId}`, { method: 'DELETE' }, token),
}

// ─── Memory ───────────────────────────────────────────────────────────────────

export const memoryApi = {
  list: (limit = 20, token?: string | null) =>
    request<{ memories: unknown[]; count: number }>(
      `/api/memory/list?limit=${limit}`,
      {},
      token
    ),

  retrieve: (query: string, topK = 5, token?: string | null) =>
    request<{ results: unknown[] }>('/api/memory/retrieve', {
      method: 'POST',
      body: JSON.stringify({ query, top_k: topK }),
    }, token),

  store: (text: string, metadata = {}, token?: string | null) =>
    request<{ memory_id: string }>('/api/memory/store', {
      method: 'POST',
      body: JSON.stringify({ text, metadata }),
    }, token),

  delete: (id: string, token?: string | null) =>
    request<{ status: string }>(`/api/memory/${id}`, { method: 'DELETE' }, token),
}

// ─── Tools ────────────────────────────────────────────────────────────────────

export const toolsApi = {
  list: (token?: string | null) =>
    request<{ tools: Record<string, unknown> }>('/api/tools/list', {}, token),

  execute: (toolName: string, args: Record<string, unknown>, token?: string | null) =>
    request<{ tool: string; result: unknown }>('/api/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ tool_name: toolName, args }),
    }, token),
}

// ─── Tasks ────────────────────────────────────────────────────────────────────

export const tasksApi = {
  plan: (goal: string, token?: string | null) =>
    request<{ plan: unknown }>('/api/tasks/plan', {
      method: 'POST',
      body: JSON.stringify({ goal }),
    }, token),

  demos: (token?: string | null) =>
    request<{ demo_tasks: unknown[] }>('/api/tasks/demo', {}, token),
}

// ─── Health ───────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () =>
    request<{ status: string; app: string; version: string; provider: string }>('/api/health'),
}
