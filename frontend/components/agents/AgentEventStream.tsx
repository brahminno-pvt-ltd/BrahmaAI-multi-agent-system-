'use client'

import { useEffect, useRef } from 'react'
import { clsx } from 'clsx'
import {
  Brain, Wrench, CheckCircle2, XCircle, RefreshCw,
  Zap, Database, BarChart3, AlertTriangle, Layers
} from 'lucide-react'
import type { AgentEvent } from '@/lib/store'

const EVENT_CONFIG: Record<string, {
  icon: React.ComponentType<{ size?: number; className?: string }>
  color: string
  label: string
  bg: string
}> = {
  memory_retrieval: { icon: Database,    color: 'text-signal-blue',  bg: 'bg-signal-blue/10',  label: 'Memory' },
  planning:         { icon: Brain,       color: 'text-accent',       bg: 'bg-accent/10',       label: 'Planning' },
  step_start:       { icon: Layers,      color: 'text-text-secondary', bg: 'bg-muted/20',      label: 'Step' },
  execution:        { icon: Wrench,      color: 'text-signal-amber', bg: 'bg-signal-amber/10', label: 'Execute' },
  step_result:      { icon: CheckCircle2, color: 'text-signal-green', bg: 'bg-signal-green/10', label: 'Result' },
  step_error:       { icon: XCircle,    color: 'text-signal-red',   bg: 'bg-signal-red/10',   label: 'Error' },
  reflection:       { icon: RefreshCw,  color: 'text-purple-400',   bg: 'bg-purple-400/10',   label: 'Reflect' },
  replanning:       { icon: Brain,      color: 'text-signal-amber', bg: 'bg-signal-amber/10', label: 'Replan' },
  synthesis:        { icon: BarChart3,  color: 'text-signal-green', bg: 'bg-signal-green/10', label: 'Synth' },
  complete:         { icon: CheckCircle2, color: 'text-signal-green', bg: 'bg-signal-green/10', label: 'Done' },
  error:            { icon: AlertTriangle, color: 'text-signal-red', bg: 'bg-signal-red/10',  label: 'Error' },
  warning:          { icon: AlertTriangle, color: 'text-signal-amber', bg: 'bg-signal-amber/10', label: 'Warn' },
  default:          { icon: Zap,        color: 'text-text-secondary', bg: 'bg-muted/20',      label: 'Event' },
}

function getConfig(eventType: string) {
  return EVENT_CONFIG[eventType] || EVENT_CONFIG.default
}

function formatEventData(event: AgentEvent): string {
  const { data } = event
  switch (event.event) {
    case 'memory_retrieval':
      if (data.status === 'done') return `Retrieved ${data.retrieved} memories`
      return 'Searching long-term memory…'
    case 'planning':
      if (data.status === 'complete') {
        const plan = data.plan as Record<string, unknown>
        return `Plan: ${(plan?.steps as unknown[])?.length || 0} steps — ${(plan?.reasoning as string || '').slice(0, 80)}`
      }
      return 'Generating execution plan…'
    case 'execution':
      return `Tool: ${data.tool || 'reasoning'} (attempt ${data.attempt})`
    case 'step_start':
      const step = data.step as Record<string, unknown>
      return `${step?.description as string || ''}`
    case 'step_result':
      return `Step ${data.step_id} completed`
    case 'step_error':
      return `Step ${data.step_id} failed: ${(data.error as string || '').slice(0, 80)}`
    case 'reflection':
      if (data.status === 'complete') {
        const ref = data.reflection as Record<string, unknown>
        return `Score: ${ref?.quality_score}/10 — ${(ref?.completeness as string || '').slice(0, 80)}`
      }
      return 'Evaluating execution quality…'
    case 'synthesis':
      return 'Synthesizing final answer…'
    case 'complete':
      return `Completed in ${data.elapsed_seconds}s · ${data.iterations} iterations`
    case 'error':
      return `${data.phase}: ${(data.error as string || '').slice(0, 100)}`
    default:
      return JSON.stringify(data).slice(0, 120)
  }
}

interface Props {
  events: AgentEvent[]
  isRunning: boolean
  compact?: boolean
}

export default function AgentEventStream({ events, isRunning, compact = false }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isRunning) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [events.length, isRunning])

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      {!compact && (
        <div className="flex items-center justify-between px-3 py-2.5 border-b border-border shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-text-primary font-display">Agent Log</span>
            <span className="font-mono text-[10px] text-text-muted">{events.length} events</span>
          </div>
          {isRunning && (
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-signal-green animate-pulse" />
              <span className="text-[10px] text-signal-green font-mono">LIVE</span>
            </div>
          )}
        </div>
      )}

      {/* Event list */}
      <div className={clsx(
        'flex-1 overflow-y-auto',
        compact ? 'max-h-64 px-2 py-1.5' : 'px-2 py-2'
      )}>
        {events.length === 0 && (
          <div className="flex flex-col items-center justify-center h-32 text-text-muted">
            <Zap size={20} className="mb-2 opacity-30" />
            <p className="text-xs">No events yet</p>
          </div>
        )}

        <div className="space-y-0.5">
          {events.map((event, i) => {
            const config = getConfig(event.event)
            const Icon = config.icon
            const text = formatEventData(event)
            const isLast = i === events.length - 1

            return (
              <div
                key={i}
                className={clsx(
                  'flex items-start gap-2 px-2 py-1.5 rounded-lg transition-all',
                  isLast && isRunning ? 'bg-accent/5 border border-accent/10' : 'hover:bg-muted/20',
                  'animate-fade-in'
                )}
              >
                {/* Line connector */}
                <div className="flex flex-col items-center gap-0.5 shrink-0 mt-0.5">
                  <div className={clsx('p-1 rounded-md', config.bg)}>
                    <Icon size={10} className={config.color} />
                  </div>
                  {i < events.length - 1 && (
                    <div className="w-px h-2 bg-border" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className={clsx('text-[10px] font-mono font-medium uppercase tracking-wide', config.color)}>
                      {config.label}
                    </span>
                    <span className="text-[9px] text-text-muted font-mono ml-auto shrink-0">
                      {new Date(event.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                    </span>
                  </div>
                  <p className="text-[11px] text-text-secondary leading-relaxed line-clamp-2 break-words">
                    {text}
                  </p>
                </div>
              </div>
            )
          })}
        </div>

        {isRunning && (
          <div className="flex items-center gap-2 px-2 py-2 mt-1">
            <div className="flex gap-1">
              {[0, 1, 2].map(i => (
                <div key={i} className="thinking-dot w-1 h-1 rounded-full bg-accent/50" style={{ animationDelay: `${i * 0.2}s` }} />
              ))}
            </div>
            <span className="text-[10px] text-text-muted font-mono">processing…</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
