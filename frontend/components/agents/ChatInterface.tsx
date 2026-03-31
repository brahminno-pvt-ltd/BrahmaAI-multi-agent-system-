'use client'

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { usePendingPrompt, useKeyboardShortcut } from '@/lib/hooks'
import { Send, StopCircle, Sparkles, ChevronDown, Zap, Search, Code, FileText, Calendar, Mail } from 'lucide-react'
import { clsx } from 'clsx'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useBrahmaStore, type Message, type AgentEvent } from '@/lib/store'
import { chatApi, type StreamEvent } from '@/lib/api'
import AgentEventStream from './AgentEventStream'

const DEMO_PROMPTS = [
  { icon: Search,   label: 'AI Trends Report',    prompt: 'Search for the latest AI trends in 2025 and create a structured report with key insights' },
  { icon: Code,     label: 'Generate Python API', prompt: 'Generate a complete Python FastAPI application for a todo app with full CRUD endpoints and explain the code' },
  { icon: FileText, label: 'Plan a Trip',         prompt: 'Plan a detailed 5-day trip to Tokyo, Japan with a $2000 budget including hotels, food, and activities' },
  { icon: Calendar, label: 'Schedule Tasks',      prompt: 'Help me create a weekly productivity schedule with time blocks for deep work, meetings, and exercise' },
]

const generateId = () => Math.random().toString(36).slice(2, 11)

export default function ChatInterface() {
  const [input, setInput] = useState('')
  const [abortController, setAbortController] = useState<AbortController | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const {
    messages, addMessage, updateMessage, clearMessages,
    isAgentRunning, setAgentRunning,
    addEvent, clearEvents, liveEvents,
    sessionId, token,
  } = useBrahmaStore()

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => { scrollToBottom() }, [messages, scrollToBottom])

  // Handle prompts launched from Dashboard demo cards
  const pendingPrompt = usePendingPrompt()
  useEffect(() => {
    if (pendingPrompt && !isAgentRunning) {
      setTimeout(() => handleSubmit(pendingPrompt), 100)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingPrompt])

  // Focus input on Cmd+K / Ctrl+K
  useKeyboardShortcut(['Meta', 'k'], (e) => { e.preventDefault(); inputRef.current?.focus() })

  const handleSubmit = async (text?: string) => {
    const messageText = (text || input).trim()
    if (!messageText || isAgentRunning) return

    setInput('')
    clearEvents()
    setAgentRunning(true)

    const userMsg: Message = {
      id: generateId(),
      role: 'user',
      content: messageText,
      timestamp: Date.now(),
    }
    addMessage(userMsg)

    const assistantId = generateId()
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
      isStreaming: true,
      events: [],
    }
    addMessage(assistantMsg)

    const collectedEvents: AgentEvent[] = []

    const ac = new AbortController()
    setAbortController(ac)

    try {
      await chatApi.streamMessage(
        messageText,
        sessionId,
        (event: StreamEvent) => {
          const agentEvent: AgentEvent = {
            event: event.event,
            timestamp: event.timestamp,
            data: event.data as Record<string, unknown>,
          }
          collectedEvents.push(agentEvent)
          addEvent(agentEvent)

          // Update assistant message with latest events
          updateMessage(assistantId, { events: [...collectedEvents] })

          // When complete, set the final answer
          if (event.event === 'complete') {
            const finalAnswer = event.data.final_answer as Record<string, unknown>
            const summary = (finalAnswer?.summary as string) || 'Task completed.'
            updateMessage(assistantId, {
              content: summary,
              isStreaming: false,
              events: [...collectedEvents],
            })
          }

          if (event.event === 'error') {
            updateMessage(assistantId, {
              content: `Error: ${(event.data as Record<string, string>).error || 'Unknown error'}`,
              isStreaming: false,
            })
          }
        },
        token
      )
    } catch (err: unknown) {
      if ((err as Error)?.name !== 'AbortError') {
        updateMessage(assistantId, {
          content: `Connection error: ${(err as Error)?.message || 'Failed to connect to backend'}`,
          isStreaming: false,
        })
      }
    } finally {
      setAgentRunning(false)
      setAbortController(null)
      updateMessage(assistantId, { isStreaming: false })
    }
  }

  const handleStop = () => {
    abortController?.abort()
    setAgentRunning(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  // Auto-resize textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 180) + 'px'
  }

  return (
    <div className="flex h-full">
      {/* Chat column */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
          {messages.length === 0 && (
            <WelcomeScreen onPrompt={(p) => handleSubmit(p)} />
          )}

          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              isLatest={msg.id === messages[messages.length - 1]?.id}
            />
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="px-4 pb-4 pt-2 border-t border-border bg-surface/50 backdrop-blur-sm shrink-0">
          <div className={clsx(
            'flex items-end gap-3 bg-panel border rounded-xl px-3 py-2.5 transition-all',
            isAgentRunning ? 'border-accent/40 glow-accent' : 'border-border hover:border-muted'
          )}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask BrahmaAI anything… (Shift+Enter for newline)"
              rows={1}
              disabled={isAgentRunning}
              className="flex-1 bg-transparent text-sm text-text-primary placeholder:text-text-muted resize-none focus:outline-none leading-relaxed min-h-[24px] max-h-[180px] font-sans"
            />
            <div className="flex items-center gap-2 shrink-0 pb-0.5">
              {isAgentRunning ? (
                <button
                  onClick={handleStop}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-signal-red/15 text-signal-red text-xs font-medium hover:bg-signal-red/25 transition-colors"
                >
                  <StopCircle size={13} />
                  Stop
                </button>
              ) : (
                <button
                  onClick={() => handleSubmit()}
                  disabled={!input.trim()}
                  className={clsx(
                    'p-2 rounded-lg transition-all duration-150',
                    input.trim()
                      ? 'bg-accent text-white hover:bg-accent/90 shadow-lg shadow-accent/20'
                      : 'bg-muted/30 text-text-muted cursor-not-allowed'
                  )}
                >
                  <Send size={14} />
                </button>
              )}
            </div>
          </div>

          <p className="text-center text-[11px] text-text-muted mt-2">
            Multi-agent AI · Plans · Executes · Reflects
          </p>
        </div>
      </div>

      {/* Live events sidebar (only when running or has events) */}
      {(isAgentRunning || liveEvents.length > 0) && (
        <div className="w-80 border-l border-border bg-surface overflow-hidden flex-shrink-0 hidden xl:flex flex-col">
          <AgentEventStream events={liveEvents} isRunning={isAgentRunning} />
        </div>
      )}
    </div>
  )
}

// ─── Welcome Screen ───────────────────────────────────────────────────────────

function WelcomeScreen({ onPrompt }: { onPrompt: (p: string) => void }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-8 animate-fade-in">
      <div className="text-center">
        <div className="w-14 h-14 rounded-2xl bg-accent/15 border border-accent/20 flex items-center justify-center mx-auto mb-5">
          <Sparkles size={24} className="text-accent" />
        </div>
        <h1 className="font-display font-bold text-2xl text-text-primary mb-2">
          BrahmaAI
        </h1>
        <p className="text-sm text-text-secondary max-w-sm">
          Autonomous multi-agent assistant. I plan, use tools, reflect, and refine — not just chat.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg">
        {DEMO_PROMPTS.map(({ icon: Icon, label, prompt }) => (
          <button
            key={label}
            onClick={() => onPrompt(prompt)}
            className="flex items-start gap-3 p-3.5 rounded-xl bg-panel border border-border hover:border-accent/30 hover:bg-accent/5 text-left transition-all group"
          >
            <div className="w-7 h-7 rounded-lg bg-muted/50 flex items-center justify-center shrink-0 group-hover:bg-accent/10 transition-colors">
              <Icon size={13} className="text-text-secondary group-hover:text-accent transition-colors" />
            </div>
            <div>
              <p className="text-xs font-medium text-text-primary">{label}</p>
              <p className="text-[11px] text-text-muted mt-0.5 leading-relaxed line-clamp-2">{prompt}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}

// ─── Message Bubble ───────────────────────────────────────────────────────────

function MessageBubble({ message, isLatest }: { message: Message; isLatest: boolean }) {
  const [showEvents, setShowEvents] = useState(false)
  const isUser = message.role === 'user'

  return (
    <div className={clsx('flex gap-3 animate-fade-in', isUser && 'justify-end')}>
      {!isUser && (
        <div className="w-7 h-7 rounded-lg bg-accent/15 border border-accent/20 flex items-center justify-center shrink-0 mt-0.5">
          <Zap size={12} className="text-accent" />
        </div>
      )}

      <div className={clsx('max-w-[80%] space-y-2', isUser && 'items-end flex flex-col')}>
        <div className={clsx(
          'rounded-2xl px-4 py-3 text-sm leading-relaxed',
          isUser
            ? 'bg-accent text-white rounded-tr-sm'
            : 'bg-panel border border-border rounded-tl-sm'
        )}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : message.isStreaming && !message.content ? (
            <ThinkingIndicator events={message.events || []} />
          ) : (
            <div className="prose-brahma">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content || '…'}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Events toggle for assistant messages */}
        {!isUser && (message.events?.length || 0) > 0 && (
          <button
            onClick={() => setShowEvents(s => !s)}
            className="flex items-center gap-1.5 text-[11px] text-text-muted hover:text-text-secondary transition-colors"
          >
            <span className="font-mono">{message.events!.length} events</span>
            <ChevronDown size={11} className={clsx('transition-transform', showEvents && 'rotate-180')} />
          </button>
        )}

        {showEvents && message.events && (
          <div className="w-full max-w-[600px] rounded-xl border border-border bg-surface overflow-hidden">
            <AgentEventStream events={message.events} isRunning={false} compact />
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Thinking Indicator ───────────────────────────────────────────────────────

function ThinkingIndicator({ events }: { events: AgentEvent[] }) {
  const lastEvent = events[events.length - 1]
  const phase = lastEvent?.event || 'thinking'

  const labels: Record<string, string> = {
    memory_retrieval: 'Retrieving memory…',
    planning: 'Planning steps…',
    execution: 'Executing…',
    step_start: 'Running step…',
    reflection: 'Reflecting…',
    synthesis: 'Synthesizing…',
    thinking: 'Thinking…',
  }

  return (
    <div className="flex items-center gap-2.5">
      <div className="flex gap-1">
        {[0, 1, 2].map(i => (
          <div
            key={i}
            className="thinking-dot w-1.5 h-1.5 rounded-full bg-accent/60"
            style={{ animationDelay: `${i * 0.2}s` }}
          />
        ))}
      </div>
      <span className="text-xs text-text-secondary font-mono">
        {labels[phase] || 'Processing…'}
      </span>
    </div>
  )
}
