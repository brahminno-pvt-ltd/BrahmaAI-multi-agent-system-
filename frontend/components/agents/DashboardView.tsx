'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Search, Code, FileText, Calendar, Mail, Cpu, Database,
  Globe, Zap, CheckCircle2, Clock, Activity, ArrowRight,
  BarChart3, Layers, Brain, Wrench
} from 'lucide-react'
import { clsx } from 'clsx'
import { toolsApi, tasksApi, healthApi } from '@/lib/api'
import { useBrahmaStore } from '@/lib/store'

type Tool = { description: string; args: Record<string, string> }
type DemoTask = { id: string; title: string; prompt: string; tools: string[] }

const TOOL_ICONS: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
  web_search: Globe,
  web_scraper: Search,
  file_reader: FileText,
  code_executor: Code,
  email_tool: Mail,
  calendar_tool: Calendar,
}

const AGENT_CARDS = [
  { name: 'Planner Agent',  icon: Brain,    desc: 'Breaks goals into structured JSON plans',  color: 'text-accent',       bg: 'bg-accent/10' },
  { name: 'Executor Agent', icon: Wrench,   desc: 'Runs steps via tools with retry logic',    color: 'text-signal-amber', bg: 'bg-signal-amber/10' },
  { name: 'Critic Agent',   icon: BarChart3, desc: 'Reflects on results & triggers replanning', color: 'text-purple-400', bg: 'bg-purple-400/10' },
  { name: 'Memory Agent',   icon: Database, desc: 'Stores & retrieves semantic memories',      color: 'text-signal-blue',  bg: 'bg-signal-blue/10' },
]

export default function DashboardView() {
  const [tools, setTools] = useState<Record<string, Tool>>({})
  const [demoTasks, setDemoTasks] = useState<DemoTask[]>([])
  const [health, setHealth] = useState<Record<string, string> | null>(null)
  const [launching, setLaunching] = useState<string | null>(null)
  const { token, liveEvents, messages, memories, setActiveTab } = useBrahmaStore()
  const router = useRouter()

  useEffect(() => {
    toolsApi.list(token).then(r => setTools(r.tools as Record<string, Tool>)).catch(() => {})
    tasksApi.demos(token).then(r => setDemoTasks(r.demo_tasks as DemoTask[])).catch(() => {})
    healthApi.check().then(r => setHealth(r as unknown as Record<string, string>)).catch(() => {})
  }, [token])

  const launchDemo = (task: DemoTask) => {
    setLaunching(task.id)
    // Store the prompt so ChatInterface picks it up
    sessionStorage.setItem('brahma_pending_prompt', task.prompt)
    router.push('/chat')
  }

  const stats = [
    { label: 'Messages',   value: messages.length,   icon: Zap,        color: 'text-accent' },
    { label: 'Events',     value: liveEvents.length,  icon: Activity,   color: 'text-signal-green' },
    { label: 'Memories',   value: memories.length,    icon: Database,   color: 'text-signal-blue' },
    { label: 'Tools',      value: Object.keys(tools).length, icon: Wrench, color: 'text-signal-amber' },
  ]

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">

        {/* Header */}
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className={clsx(
              'w-2 h-2 rounded-full',
              health?.status === 'ok' ? 'bg-signal-green animate-pulse' : 'bg-signal-red'
            )} />
            <span className="text-xs font-mono text-text-muted uppercase tracking-widest">
              {health?.status === 'ok' ? `Connected · ${health.provider}` : 'Offline'}
            </span>
          </div>
          <h1 className="font-display font-bold text-2xl text-text-primary">
            Mission Control
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Overview of agents, tools, and system state
          </p>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {stats.map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="bg-panel border border-border rounded-xl p-4 hover:border-muted transition-colors">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs text-text-muted">{label}</span>
                <Icon size={14} className={color} />
              </div>
              <p className="font-display font-bold text-2xl text-text-primary">{value}</p>
            </div>
          ))}
        </div>

        {/* Agent pipeline */}
        <section>
          <h2 className="font-display font-semibold text-sm text-text-secondary uppercase tracking-widest mb-4">
            Agent Pipeline
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {AGENT_CARDS.map(({ name, icon: Icon, desc, color, bg }, i) => (
              <div key={name} className="relative bg-panel border border-border rounded-xl p-4 hover:border-muted transition-all group">
                {/* Connector arrow */}
                {i < AGENT_CARDS.length - 1 && (
                  <div className="absolute -right-3 top-1/2 -translate-y-1/2 z-10 hidden lg:block">
                    <ArrowRight size={12} className="text-border" />
                  </div>
                )}
                <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center mb-3', bg)}>
                  <Icon size={15} className={color} />
                </div>
                <p className="text-xs font-semibold text-text-primary mb-1">{name}</p>
                <p className="text-[11px] text-text-muted leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
          <div className="mt-2 flex items-center gap-2 text-[11px] text-text-muted">
            <div className="h-px flex-1 bg-border" />
            <span className="font-mono">Goal → Plan → Execute → Observe → Reflect → Repeat</span>
            <div className="h-px flex-1 bg-border" />
          </div>
        </section>

        {/* Demo tasks */}
        <section>
          <h2 className="font-display font-semibold text-sm text-text-secondary uppercase tracking-widest mb-4">
            Demo Tasks
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {demoTasks.map((task) => (
              <div
                key={task.id}
                className="bg-panel border border-border rounded-xl p-4 hover:border-accent/30 hover:bg-accent/5 transition-all group"
              >
                <div className="flex items-start justify-between gap-3 mb-3">
                  <p className="text-sm font-semibold text-text-primary group-hover:text-accent transition-colors">
                    {task.title}
                  </p>
                  <button
                    onClick={() => launchDemo(task)}
                    disabled={launching === task.id}
                    className={clsx(
                      'shrink-0 flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium transition-all',
                      launching === task.id
                        ? 'bg-accent/10 text-accent cursor-wait'
                        : 'bg-muted/30 text-text-secondary hover:bg-accent hover:text-white'
                    )}
                  >
                    {launching === task.id ? 'Launching…' : 'Run'}
                    <ArrowRight size={11} />
                  </button>
                </div>
                <p className="text-[11px] text-text-muted leading-relaxed mb-3 line-clamp-2">
                  {task.prompt}
                </p>
                <div className="flex flex-wrap gap-1">
                  {task.tools.map((t) => {
                    const Icon = TOOL_ICONS[t] || Cpu
                    return (
                      <span key={t} className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-muted/30 text-[10px] text-text-muted font-mono">
                        <Icon size={9} />
                        {t}
                      </span>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Tools registry */}
        <section>
          <h2 className="font-display font-semibold text-sm text-text-secondary uppercase tracking-widest mb-4">
            Tool Registry
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Object.entries(tools).map(([name, meta]) => {
              const Icon = TOOL_ICONS[name] || Cpu
              return (
                <div key={name} className="bg-panel border border-border rounded-xl p-3.5 hover:border-muted transition-colors">
                  <div className="flex items-center gap-2.5 mb-2">
                    <div className="w-7 h-7 rounded-lg bg-muted/50 flex items-center justify-center">
                      <Icon size={13} className="text-text-secondary" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-text-primary font-mono">{name}</p>
                      <div className="flex items-center gap-1 mt-0.5">
                        <CheckCircle2 size={9} className="text-signal-green" />
                        <span className="text-[10px] text-signal-green">Active</span>
                      </div>
                    </div>
                  </div>
                  <p className="text-[11px] text-text-muted leading-relaxed line-clamp-2">
                    {meta.description}
                  </p>
                  {meta.args && Object.keys(meta.args).length > 0 && (
                    <div className="mt-2 pt-2 border-t border-border/50">
                      <p className="text-[10px] text-text-muted mb-1 font-mono">Args:</p>
                      <div className="flex flex-wrap gap-1">
                        {Object.keys(meta.args).map(arg => (
                          <span key={arg} className="px-1.5 py-0.5 bg-muted/30 rounded text-[10px] text-text-muted font-mono">
                            {arg}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
            {Object.keys(tools).length === 0 && (
              <div className="col-span-3 text-center py-8 text-text-muted text-sm">
                <Cpu size={24} className="mx-auto mb-2 opacity-30" />
                <p>Loading tools… (backend must be running)</p>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
