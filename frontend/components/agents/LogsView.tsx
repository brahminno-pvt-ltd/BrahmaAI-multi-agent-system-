'use client'

import { useState, useMemo } from 'react'
import {
  ScrollText, Filter, Trash2, Download, ChevronRight,
  ChevronDown, Search, Activity, Brain, Wrench, Database, CheckCircle2
} from 'lucide-react'
import { clsx } from 'clsx'
import { useBrahmaStore, type AgentEvent } from '@/lib/store'

const EVENT_TYPES = [
  'all', 'planning', 'execution', 'step_result', 'reflection', 'memory_retrieval', 'error', 'complete'
]

const EVENT_COLORS: Record<string, string> = {
  planning:         'text-accent border-accent/20 bg-accent/10',
  execution:        'text-signal-amber border-signal-amber/20 bg-signal-amber/10',
  step_result:      'text-signal-green border-signal-green/20 bg-signal-green/10',
  step_error:       'text-signal-red border-signal-red/20 bg-signal-red/10',
  reflection:       'text-purple-400 border-purple-400/20 bg-purple-400/10',
  memory_retrieval: 'text-signal-blue border-signal-blue/20 bg-signal-blue/10',
  complete:         'text-signal-green border-signal-green/20 bg-signal-green/10',
  error:            'text-signal-red border-signal-red/20 bg-signal-red/10',
  synthesis:        'text-signal-green border-signal-green/20 bg-signal-green/10',
  step_start:       'text-text-secondary border-border bg-muted/10',
  warning:          'text-signal-amber border-signal-amber/20 bg-signal-amber/10',
}

function EventCard({ event, index }: { event: AgentEvent; index: number }) {
  const [expanded, setExpanded] = useState(false)
  const colorClass = EVENT_COLORS[event.event] || 'text-text-secondary border-border bg-muted/10'
  const time = new Date(event.timestamp * 1000).toLocaleTimeString([], {
    hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3
  })

  return (
    <div className={clsx(
      'border rounded-lg overflow-hidden transition-all animate-fade-in',
      expanded ? 'border-accent/20' : 'border-border hover:border-muted'
    )}>
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center gap-3 px-3 py-2.5 bg-panel hover:bg-muted/10 text-left transition-colors"
      >
        <span className="text-text-muted font-mono text-[10px] w-6 text-right shrink-0">
          {index + 1}
        </span>
        <span className={clsx(
          'px-1.5 py-0.5 rounded-md text-[10px] font-mono font-medium border shrink-0',
          colorClass
        )}>
          {event.event}
        </span>
        <span className="flex-1 text-xs text-text-secondary truncate text-left">
          {summarizeEvent(event)}
        </span>
        <span className="text-[10px] font-mono text-text-muted shrink-0">{time}</span>
        {expanded
          ? <ChevronDown size={12} className="text-text-muted shrink-0" />
          : <ChevronRight size={12} className="text-text-muted shrink-0" />
        }
      </button>

      {expanded && (
        <div className="px-4 py-3 bg-surface border-t border-border">
          <pre className="text-[11px] text-text-secondary font-mono overflow-x-auto leading-relaxed whitespace-pre-wrap break-words">
            {JSON.stringify(event.data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

function summarizeEvent(event: AgentEvent): string {
  const d = event.data
  switch (event.event) {
    case 'planning':
      if (d.status === 'complete') {
        const plan = d.plan as Record<string, unknown>
        return `Plan ready: ${(plan?.steps as unknown[])?.length || 0} steps`
      }
      return 'Generating plan…'
    case 'execution':
      return `Tool: ${d.tool || 'reasoning'} (attempt ${d.attempt})`
    case 'step_start':
      return `${(d.step as Record<string, unknown>)?.description || ''}`
    case 'step_result':
      return `Step ${d.step_id} → success`
    case 'step_error':
      return `Step ${d.step_id} → ${(d.error as string || '').slice(0, 80)}`
    case 'reflection':
      if (d.status === 'complete') {
        const r = d.reflection as Record<string, unknown>
        return `Quality: ${r?.quality_score}/10 — replan: ${r?.should_replan}`
      }
      return 'Evaluating quality…'
    case 'memory_retrieval':
      return d.status === 'done' ? `Retrieved ${d.retrieved} memories` : 'Searching memory…'
    case 'complete':
      return `Done in ${d.elapsed_seconds}s · ${d.iterations} iterations`
    case 'error':
      return `${d.phase}: ${(d.error as string || '').slice(0, 80)}`
    default:
      return JSON.stringify(d).slice(0, 80)
  }
}

export default function LogsView() {
  const { liveEvents, clearEvents, isAgentRunning } = useBrahmaStore()
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')

  const filtered = useMemo(() => {
    return liveEvents.filter(e => {
      const typeMatch = filter === 'all' || e.event === filter
      const searchMatch = !search || JSON.stringify(e).toLowerCase().includes(search.toLowerCase())
      return typeMatch && searchMatch
    })
  }, [liveEvents, filter, search])

  const downloadLogs = () => {
    const blob = new Blob([JSON.stringify(liveEvents, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `brahmaai-logs-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Event type counts
  const counts = useMemo(() => {
    const c: Record<string, number> = {}
    liveEvents.forEach(e => { c[e.event] = (c[e.event] || 0) + 1 })
    return c
  }, [liveEvents])

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border bg-surface shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <ScrollText size={18} className="text-accent" />
            <div>
              <h1 className="font-display font-bold text-lg text-text-primary">Agent Logs</h1>
              <p className="text-xs text-text-muted">
                {liveEvents.length} events · {isAgentRunning
                  ? <span className="text-signal-green">● Live</span>
                  : <span>Idle</span>}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={downloadLogs}
              disabled={liveEvents.length === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-muted/30 text-text-secondary text-xs hover:text-text-primary hover:bg-muted/50 transition-colors disabled:opacity-40"
            >
              <Download size={13} />
              Export
            </button>
            <button
              onClick={clearEvents}
              disabled={liveEvents.length === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-muted/30 text-text-secondary text-xs hover:text-signal-red hover:bg-signal-red/10 transition-colors disabled:opacity-40"
            >
              <Trash2 size={13} />
              Clear
            </button>
          </div>
        </div>

        {/* Stats chips */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          {Object.entries(counts).slice(0, 8).map(([type, count]) => (
            <span
              key={type}
              className={clsx(
                'px-2 py-0.5 rounded-full text-[10px] font-mono border cursor-pointer transition-colors',
                filter === type
                  ? EVENT_COLORS[type] || 'text-text-secondary border-border bg-muted/10'
                  : 'text-text-muted border-border hover:border-muted'
              )}
              onClick={() => setFilter(f => f === type ? 'all' : type)}
            >
              {type} {count}
            </span>
          ))}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search events…"
              className="w-full pl-8 pr-3 py-1.5 bg-panel border border-border rounded-lg text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/40"
            />
          </div>
          <div className="flex items-center gap-1">
            <Filter size={12} className="text-text-muted" />
            <select
              value={filter}
              onChange={e => setFilter(e.target.value)}
              className="bg-panel border border-border rounded-lg text-xs text-text-secondary px-2 py-1.5 focus:outline-none focus:border-accent/40"
            >
              {EVENT_TYPES.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Events list */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1.5">
        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center h-64 text-text-muted gap-3">
            <Activity size={32} className="opacity-20" />
            <div className="text-center">
              <p className="text-sm font-medium">No events yet</p>
              <p className="text-xs mt-1">Start a task in the Chat tab to see agent reasoning here</p>
            </div>
          </div>
        )}

        {filtered.map((event, i) => (
          <EventCard key={i} event={event} index={i} />
        ))}

        {isAgentRunning && (
          <div className="flex items-center gap-2 px-3 py-2 border border-accent/20 bg-accent/5 rounded-lg">
            <div className="flex gap-1">
              {[0, 1, 2].map(i => (
                <div key={i} className="thinking-dot w-1.5 h-1.5 rounded-full bg-accent/60" style={{ animationDelay: `${i * 0.2}s` }} />
              ))}
            </div>
            <span className="text-xs text-accent font-mono">Agent running — new events incoming…</span>
          </div>
        )}
      </div>
    </div>
  )
}
