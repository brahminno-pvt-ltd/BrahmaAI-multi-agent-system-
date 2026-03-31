'use client'

import { useState } from 'react'
import { Search, Code, Calendar, Loader2, Copy, Check, ChevronDown, ChevronUp } from 'lucide-react'
import { clsx } from 'clsx'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useCopyToClipboard } from '@/lib/hooks'
import { useBrahmaStore } from '@/lib/store'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type Tab = 'researcher' | 'coder' | 'planner'

// ─── Shared fetch helper ──────────────────────────────────────────────────────

async function callAgent(endpoint: string, body: Record<string, unknown>, token: string | null) {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

// ─── Result renderer ──────────────────────────────────────────────────────────

function ResultPanel({ output, label }: { output: string; label?: string }) {
  const { copied, copy } = useCopyToClipboard()
  const [expanded, setExpanded] = useState(true)

  return (
    <div className="bg-panel border border-signal-green/20 rounded-xl overflow-hidden animate-fade-in">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-signal-green/5">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-signal-green" />
          <span className="text-xs font-medium text-signal-green">{label || 'Result'}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => copy(output)}
            className="flex items-center gap-1 text-[10px] text-text-muted hover:text-text-primary transition-colors px-2 py-1 rounded hover:bg-muted/30"
          >
            {copied ? <Check size={11} className="text-signal-green" /> : <Copy size={11} />}
            {copied ? 'Copied' : 'Copy'}
          </button>
          <button
            onClick={() => setExpanded(e => !e)}
            className="text-text-muted hover:text-text-primary transition-colors"
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>
      {expanded && (
        <div className="px-4 py-4 prose-brahma overflow-x-auto max-h-[600px] overflow-y-auto">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{output}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}

// ─── Researcher Tab ───────────────────────────────────────────────────────────

function ResearcherTab() {
  const [query, setQuery] = useState('')
  const [depth, setDepth] = useState(3)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { token } = useBrahmaStore()

  const run = async () => {
    if (!query.trim() || loading) return
    setLoading(true); setError(null); setResult(null)
    try {
      const res = await callAgent('/api/agents/researcher/research', { query, depth }, token)
      setResult(res)
    } catch (e: unknown) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="bg-panel border border-border rounded-xl p-4 space-y-3">
        <label className="text-xs font-medium text-text-secondary">Research Query</label>
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="e.g. What are the latest breakthroughs in quantum computing in 2025?"
          rows={3}
          className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/40 resize-none"
        />
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-xs text-text-muted">Search depth:</label>
            {[2, 3, 4, 5].map(n => (
              <button key={n} onClick={() => setDepth(n)}
                className={clsx('w-7 h-7 rounded-lg text-xs font-mono transition-colors',
                  depth === n ? 'bg-accent text-white' : 'bg-muted/30 text-text-muted hover:bg-muted/50'
                )}>
                {n}
              </button>
            ))}
          </div>
          <button
            onClick={run}
            disabled={!query.trim() || loading}
            className="ml-auto flex items-center gap-2 px-4 py-2 bg-accent text-white text-sm rounded-lg font-medium hover:bg-accent/90 disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
            {loading ? 'Researching…' : 'Research'}
          </button>
        </div>
      </div>

      {error && <div className="px-4 py-3 bg-signal-red/5 border border-signal-red/20 rounded-xl text-sm text-signal-red">{error}</div>}

      {result && (
        <div className="space-y-3">
          <div className="grid grid-cols-3 gap-2 text-center">
            {[
              { label: 'Queries', value: (result.queries_used as string[])?.length || 0 },
              { label: 'Sources Found', value: result.sources_found as number || 0 },
              { label: 'Deep Scraped', value: result.sources_scraped as number || 0 },
            ].map(({ label, value }) => (
              <div key={label} className="bg-panel border border-border rounded-lg p-2.5">
                <p className="text-lg font-bold font-display text-text-primary">{value}</p>
                <p className="text-[10px] text-text-muted">{label}</p>
              </div>
            ))}
          </div>
          <ResultPanel
            output={(result.report as Record<string, unknown>)?.full_text as string || result.output as string || ''}
            label="Research Report"
          />
        </div>
      )}
    </div>
  )
}

// ─── Coder Tab ────────────────────────────────────────────────────────────────

function CoderTab() {
  const [mode, setMode] = useState<'generate' | 'review' | 'debug'>('generate')
  const [desc, setDesc] = useState(''); const [lang, setLang] = useState('python')
  const [code, setCode] = useState(''); const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const { token } = useBrahmaStore()

  const LANGS = ['python', 'typescript', 'javascript', 'go', 'rust', 'sql']

  const run = async () => {
    setLoading(true); setApiError(null); setResult(null)
    try {
      let endpoint = ''; let body: Record<string, unknown> = {}
      if (mode === 'generate') { endpoint = '/api/agents/coder/generate'; body = { description: desc, language: lang, test: true } }
      else if (mode === 'review') { endpoint = '/api/agents/coder/review'; body = { code, language: lang } }
      else { endpoint = '/api/agents/coder/debug'; body = { code, error, language: lang } }
      setResult(await callAgent(endpoint, body, token))
    } catch (e: unknown) { setApiError((e as Error).message) }
    finally { setLoading(false) }
  }

  const outputText = result
    ? mode === 'generate'
      ? result.output as string
      : mode === 'review'
        ? result.review as string
        : result.explanation as string
    : ''

  return (
    <div className="space-y-4">
      {/* Mode tabs */}
      <div className="flex gap-1 p-1 bg-surface border border-border rounded-xl w-fit">
        {(['generate', 'review', 'debug'] as const).map(m => (
          <button key={m} onClick={() => setMode(m)}
            className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors',
              mode === m ? 'bg-accent text-white' : 'text-text-muted hover:text-text-primary'
            )}>
            {m}
          </button>
        ))}
      </div>

      <div className="bg-panel border border-border rounded-xl p-4 space-y-3">
        {/* Language selector */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-text-muted">Language:</span>
          {LANGS.map(l => (
            <button key={l} onClick={() => setLang(l)}
              className={clsx('px-2.5 py-1 rounded-md text-[10px] font-mono transition-colors',
                lang === l ? 'bg-accent/15 text-accent border border-accent/20' : 'bg-muted/20 text-text-muted hover:bg-muted/40'
              )}>
              {l}
            </button>
          ))}
        </div>

        {mode === 'generate' && (
          <textarea value={desc} onChange={e => setDesc(e.target.value)}
            placeholder="Describe what the code should do…"
            rows={3}
            className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/40 resize-none"
          />
        )}

        {(mode === 'review' || mode === 'debug') && (
          <textarea value={code} onChange={e => setCode(e.target.value)}
            placeholder={`Paste your ${lang} code here…`}
            rows={8}
            className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/40 resize-none font-mono text-xs"
          />
        )}

        {mode === 'debug' && (
          <textarea value={error} onChange={e => setError(e.target.value)}
            placeholder="Paste the error message here…"
            rows={3}
            className="w-full px-3 py-2 bg-surface border border-signal-red/20 rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-signal-red/40 resize-none font-mono text-xs"
          />
        )}

        <div className="flex justify-end">
          <button onClick={run} disabled={loading || (mode === 'generate' ? !desc.trim() : !code.trim())}
            className="flex items-center gap-2 px-4 py-2 bg-accent text-white text-sm rounded-lg font-medium hover:bg-accent/90 disabled:opacity-50 transition-colors">
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Code size={14} />}
            {loading ? 'Running…' : mode === 'generate' ? 'Generate' : mode === 'review' ? 'Review' : 'Debug'}
          </button>
        </div>
      </div>

      {apiError && <div className="px-4 py-3 bg-signal-red/5 border border-signal-red/20 rounded-xl text-sm text-signal-red">{apiError}</div>}
      {result && outputText && <ResultPanel output={outputText} label={mode === 'generate' ? 'Generated Code' : mode === 'review' ? 'Code Review' : 'Debug Analysis'} />}
    </div>
  )
}

// ─── Planner Tab ──────────────────────────────────────────────────────────────

function PlannerTab() {
  const [mode, setMode] = useState<'trip' | 'project' | 'schedule' | 'generic'>('trip')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [apiError, setApiError] = useState<string | null>(null)
  const [fields, setFields] = useState<Record<string, string>>({})
  const { token } = useBrahmaStore()

  const set = (k: string, v: string) => setFields(f => ({ ...f, [k]: v }))

  const run = async () => {
    setLoading(true); setApiError(null); setResult(null)
    try {
      let endpoint = ''; let body: Record<string, unknown> = {}
      if (mode === 'trip') {
        endpoint = '/api/agents/planner/trip'
        body = { destination: fields.destination || 'Tokyo', duration_days: Number(fields.days || 5), budget: Number(fields.budget || 2000), interests: (fields.interests || '').split(',').map(s => s.trim()).filter(Boolean) }
      } else if (mode === 'project') {
        endpoint = '/api/agents/planner/project'
        body = { project_name: fields.name || 'My Project', description: fields.description || '', team_size: Number(fields.team || 1), deadline: fields.deadline || '' }
      } else if (mode === 'schedule') {
        endpoint = '/api/agents/planner/schedule'
        body = { goals: (fields.goals || '').split('\n').filter(Boolean), available_hours_per_day: Number(fields.hours || 8) }
      } else {
        endpoint = '/api/agents/planner/generic'
        body = { goal: fields.goal || '', context: fields.context || '' }
      }
      setResult(await callAgent(endpoint, body, token))
    } catch (e: unknown) { setApiError((e as Error).message) }
    finally { setLoading(false) }
  }

  const outputText = result ? (result.plan || result.schedule || result.output) as string : ''

  return (
    <div className="space-y-4">
      <div className="flex gap-1 p-1 bg-surface border border-border rounded-xl w-fit flex-wrap">
        {(['trip', 'project', 'schedule', 'generic'] as const).map(m => (
          <button key={m} onClick={() => setMode(m)}
            className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors',
              mode === m ? 'bg-accent text-white' : 'text-text-muted hover:text-text-primary'
            )}>
            {m}
          </button>
        ))}
      </div>

      <div className="bg-panel border border-border rounded-xl p-4 space-y-3">
        {mode === 'trip' && (
          <>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-xs text-text-muted">Destination</label><input value={fields.destination||''} onChange={e=>set('destination',e.target.value)} placeholder="Tokyo, Japan" className="mt-1 w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/40" /></div>
              <div><label className="text-xs text-text-muted">Duration (days)</label><input type="number" value={fields.days||'5'} onChange={e=>set('days',e.target.value)} className="mt-1 w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm focus:outline-none focus:border-accent/40" /></div>
              <div><label className="text-xs text-text-muted">Budget (USD)</label><input type="number" value={fields.budget||'2000'} onChange={e=>set('budget',e.target.value)} className="mt-1 w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm focus:outline-none focus:border-accent/40" /></div>
              <div><label className="text-xs text-text-muted">Interests (comma-separated)</label><input value={fields.interests||''} onChange={e=>set('interests',e.target.value)} placeholder="food, culture, nature" className="mt-1 w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm placeholder:text-text-muted focus:outline-none focus:border-accent/40" /></div>
            </div>
          </>
        )}
        {mode === 'project' && (
          <div className="space-y-3">
            <div><label className="text-xs text-text-muted">Project Name</label><input value={fields.name||''} onChange={e=>set('name',e.target.value)} placeholder="My SaaS Product" className="mt-1 w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm placeholder:text-text-muted focus:outline-none focus:border-accent/40" /></div>
            <div><label className="text-xs text-text-muted">Description</label><textarea value={fields.description||''} onChange={e=>set('description',e.target.value)} rows={3} placeholder="Describe what you're building…" className="mt-1 w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm placeholder:text-text-muted focus:outline-none focus:border-accent/40 resize-none" /></div>
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-xs text-text-muted">Team Size</label><input type="number" value={fields.team||'1'} onChange={e=>set('team',e.target.value)} className="mt-1 w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm focus:outline-none focus:border-accent/40" /></div>
              <div><label className="text-xs text-text-muted">Deadline</label><input value={fields.deadline||''} onChange={e=>set('deadline',e.target.value)} placeholder="e.g. Q3 2025" className="mt-1 w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm placeholder:text-text-muted focus:outline-none focus:border-accent/40" /></div>
            </div>
          </div>
        )}
        {mode === 'schedule' && (
          <div className="space-y-3">
            <div><label className="text-xs text-text-muted">Goals (one per line)</label><textarea value={fields.goals||''} onChange={e=>set('goals',e.target.value)} rows={4} placeholder={"Ship MVP\nExercise daily\nLearn Spanish"} className="mt-1 w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm placeholder:text-text-muted focus:outline-none focus:border-accent/40 resize-none" /></div>
            <div><label className="text-xs text-text-muted">Available hours/day</label><input type="number" value={fields.hours||'8'} onChange={e=>set('hours',e.target.value)} className="mt-1 w-32 px-3 py-2 bg-surface border border-border rounded-lg text-sm focus:outline-none focus:border-accent/40" /></div>
          </div>
        )}
        {mode === 'generic' && (
          <div className="space-y-3">
            <div><label className="text-xs text-text-muted">Goal</label><input value={fields.goal||''} onChange={e=>set('goal',e.target.value)} placeholder="e.g. Learn machine learning in 90 days" className="mt-1 w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm placeholder:text-text-muted focus:outline-none focus:border-accent/40" /></div>
            <div><label className="text-xs text-text-muted">Context (optional)</label><textarea value={fields.context||''} onChange={e=>set('context',e.target.value)} rows={2} placeholder="Any constraints or background…" className="mt-1 w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm placeholder:text-text-muted focus:outline-none focus:border-accent/40 resize-none" /></div>
          </div>
        )}

        <div className="flex justify-end">
          <button onClick={run} disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-accent text-white text-sm rounded-lg font-medium hover:bg-accent/90 disabled:opacity-50 transition-colors">
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Calendar size={14} />}
            {loading ? 'Planning…' : 'Create Plan'}
          </button>
        </div>
      </div>

      {apiError && <div className="px-4 py-3 bg-signal-red/5 border border-signal-red/20 rounded-xl text-sm text-signal-red">{apiError}</div>}
      {result && outputText && <ResultPanel output={outputText} label="Generated Plan" />}
    </div>
  )
}

// ─── Main View ────────────────────────────────────────────────────────────────

const TABS: { id: Tab; label: string; icon: typeof Search; desc: string }[] = [
  { id: 'researcher', label: 'Researcher',    icon: Search,   desc: 'Deep multi-source web research with synthesis' },
  { id: 'coder',      label: 'Coder',         icon: Code,     desc: 'Generate, review, and debug code with sandbox testing' },
  { id: 'planner',    label: 'Task Planner',  icon: Calendar, desc: 'Trips, projects, schedules with structured output' },
]

export default function AgentsView() {
  const [tab, setTab] = useState<Tab>('researcher')

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto px-6 py-8">
        <div className="mb-6">
          <h1 className="font-display font-bold text-2xl text-text-primary">Specialised Agents</h1>
          <p className="text-sm text-text-secondary mt-1">Purpose-built agents with domain-specific prompts and structured output</p>
        </div>

        <div className="grid grid-cols-3 gap-3 mb-6">
          {TABS.map(({ id, label, icon: Icon, desc }) => (
            <button key={id} onClick={() => setTab(id)}
              className={clsx('p-3.5 rounded-xl border text-left transition-all',
                tab === id ? 'border-accent/30 bg-accent/5' : 'border-border bg-panel hover:border-muted'
              )}>
              <Icon size={16} className={clsx('mb-2', tab === id ? 'text-accent' : 'text-text-muted')} />
              <p className={clsx('text-xs font-semibold', tab === id ? 'text-accent' : 'text-text-primary')}>{label}</p>
              <p className="text-[10px] text-text-muted mt-0.5 leading-relaxed">{desc}</p>
            </button>
          ))}
        </div>

        {tab === 'researcher' && <ResearcherTab />}
        {tab === 'coder'      && <CoderTab />}
        {tab === 'planner'    && <PlannerTab />}
      </div>
    </div>
  )
}
