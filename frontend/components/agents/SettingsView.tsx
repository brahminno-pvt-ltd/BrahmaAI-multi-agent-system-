'use client'

import { useState } from 'react'
import { Settings, Key, Cpu, Database, Wrench, Copy, Check, ExternalLink, Shield } from 'lucide-react'
import { clsx } from 'clsx'
import { useCopyToClipboard } from '@/lib/hooks'

const ENV_VARS = [
  {
    group: 'LLM Provider',
    icon: Cpu,
    color: 'text-accent',
    vars: [
      { key: 'LLM_PROVIDER',       default: 'openai',                  desc: 'LLM provider: openai or anthropic', required: true },
      { key: 'OPENAI_API_KEY',      default: 'sk-...',                  desc: 'OpenAI API key (if using OpenAI)', required: false },
      { key: 'OPENAI_MODEL',        default: 'gpt-4o',                  desc: 'OpenAI model name', required: false },
      { key: 'ANTHROPIC_API_KEY',   default: 'sk-ant-...',              desc: 'Anthropic API key (if using Anthropic)', required: false },
      { key: 'ANTHROPIC_MODEL',     default: 'claude-3-5-sonnet-20241022', desc: 'Anthropic model name', required: false },
      { key: 'LLM_TEMPERATURE',     default: '0.2',                     desc: 'Generation temperature (0.0-1.0)', required: false },
      { key: 'LLM_MAX_TOKENS',      default: '4096',                    desc: 'Max output tokens per request', required: false },
    ]
  },
  {
    group: 'Agent Loop',
    icon: Settings,
    color: 'text-signal-amber',
    vars: [
      { key: 'MAX_ITERATIONS',      default: '10',   desc: 'Maximum agent loop iterations', required: false },
      { key: 'MAX_RETRIES',         default: '3',    desc: 'Retries per failed step', required: false },
      { key: 'STEP_TIMEOUT_SECONDS', default: '60',  desc: 'Per-step execution timeout', required: false },
    ]
  },
  {
    group: 'Memory',
    icon: Database,
    color: 'text-signal-blue',
    vars: [
      { key: 'FAISS_INDEX_PATH',          default: './data/faiss_index',       desc: 'Path for FAISS vector index files', required: false },
      { key: 'EMBEDDING_MODEL',           default: 'text-embedding-3-small',   desc: 'OpenAI embedding model name', required: false },
      { key: 'SHORT_TERM_MAX_MESSAGES',   default: '50',                       desc: 'Max session history messages', required: false },
      { key: 'LONG_TERM_TOP_K',           default: '5',                        desc: 'Memories retrieved per query', required: false },
    ]
  },
  {
    group: 'Tools',
    icon: Wrench,
    color: 'text-signal-green',
    vars: [
      { key: 'SERPAPI_KEY',            default: '',   desc: 'SerpAPI key for web search (optional — uses DuckDuckGo if empty)', required: false },
      { key: 'SANDBOX_TIMEOUT_SECONDS', default: '10', desc: 'Code execution timeout in seconds', required: false },
    ]
  },
  {
    group: 'Security',
    icon: Shield,
    color: 'text-purple-400',
    vars: [
      { key: 'SECRET_KEY',       default: 'change-in-production',     desc: 'App secret key', required: true },
      { key: 'JWT_SECRET',       default: 'change-in-production',     desc: 'JWT signing secret', required: true },
      { key: 'JWT_EXPIRE_MINUTES', default: '1440',                   desc: 'JWT token expiry (minutes)', required: false },
      { key: 'ALLOWED_ORIGINS',  default: '["http://localhost:3000"]', desc: 'CORS allowed origins (JSON array)', required: false },
    ]
  },
]

function EnvRow({ varKey, defaultVal, desc, required }: { varKey: string; defaultVal: string; desc: string; required: boolean }) {
  const { copied, copy } = useCopyToClipboard()

  return (
    <div className="group flex items-start gap-3 py-2.5 border-b border-border/50 last:border-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <code className="text-xs text-accent font-mono">{varKey}</code>
          {required && (
            <span className="px-1.5 py-px text-[9px] font-mono bg-signal-red/10 text-signal-red border border-signal-red/20 rounded-full">
              required
            </span>
          )}
        </div>
        <p className="text-[11px] text-text-muted leading-relaxed">{desc}</p>
        {defaultVal && (
          <p className="text-[10px] text-text-muted/60 font-mono mt-0.5">default: {defaultVal}</p>
        )}
      </div>
      <button
        onClick={() => copy(`${varKey}=${defaultVal}`)}
        className="shrink-0 p-1.5 rounded-md text-text-muted hover:text-text-primary hover:bg-muted/30 opacity-0 group-hover:opacity-100 transition-all"
      >
        {copied ? <Check size={11} className="text-signal-green" /> : <Copy size={11} />}
      </button>
    </div>
  )
}

export default function SettingsView() {
  const [activeGroup, setActiveGroup] = useState<string | null>(null)

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">

        {/* Header */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Settings size={18} className="text-accent" />
            <h1 className="font-display font-bold text-2xl text-text-primary">Configuration</h1>
          </div>
          <p className="text-sm text-text-secondary">
            BrahmaAI is configured entirely via environment variables.
            Create a <code className="text-accent font-mono text-xs">.env</code> file in the backend root.
          </p>
        </div>

        {/* Quick start */}
        <div className="bg-panel border border-accent/20 rounded-xl p-4">
          <p className="text-xs font-semibold text-accent mb-2 font-mono uppercase tracking-widest">Quick Start</p>
          <pre className="text-xs text-text-secondary font-mono leading-relaxed overflow-x-auto">{`cp .env.example .env

# Minimum required config:
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Start backend:
uvicorn backend.main:app --reload`}
          </pre>
        </div>

        {/* Demo mode notice */}
        <div className="bg-signal-amber/5 border border-signal-amber/20 rounded-xl p-4">
          <p className="text-xs font-semibold text-signal-amber mb-1">Demo Mode</p>
          <p className="text-xs text-text-muted">
            BrahmaAI runs without any API keys. In demo mode, the LLM client returns realistic mock responses
            so you can explore the full UI, agent loop, and observability features without cost.
            Connect a real API key to activate full AI-powered reasoning.
          </p>
        </div>

        {/* Env var groups */}
        {ENV_VARS.map(({ group, icon: Icon, color, vars }) => (
          <div key={group} className="bg-panel border border-border rounded-xl overflow-hidden">
            <button
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-muted/10 transition-colors text-left"
              onClick={() => setActiveGroup(g => g === group ? null : group)}
            >
              <Icon size={15} className={color} />
              <span className="font-semibold text-sm text-text-primary flex-1">{group}</span>
              <span className="text-[10px] text-text-muted font-mono">{vars.length} vars</span>
              <span className={clsx(
                'text-text-muted transition-transform duration-200',
                activeGroup === group && 'rotate-90'
              )}>›</span>
            </button>

            {(activeGroup === group || activeGroup === null) && (
              <div className="px-4 pb-2 border-t border-border">
                {vars.map(v => (
                  <EnvRow
                    key={v.key}
                    varKey={v.key}
                    defaultVal={v.default}
                    desc={v.desc}
                    required={v.required}
                  />
                ))}
              </div>
            )}
          </div>
        ))}

        {/* External links */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {[
            { label: 'OpenAI Platform', href: 'https://platform.openai.com', desc: 'Get API keys' },
            { label: 'Anthropic Console', href: 'https://console.anthropic.com', desc: 'Get API keys' },
            { label: 'SerpAPI', href: 'https://serpapi.com', desc: 'Web search API' },
          ].map(({ label, href, desc }) => (
            <a
              key={href}
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 p-3 bg-panel border border-border rounded-xl hover:border-muted transition-colors group"
            >
              <div className="flex-1">
                <p className="text-xs font-medium text-text-primary">{label}</p>
                <p className="text-[10px] text-text-muted">{desc}</p>
              </div>
              <ExternalLink size={11} className="text-text-muted group-hover:text-accent transition-colors" />
            </a>
          ))}
        </div>

        <p className="text-center text-[11px] text-text-muted pb-4">
          BrahmaAI v1.0.0 · MIT License · Built for production
        </p>
      </div>
    </div>
  )
}
