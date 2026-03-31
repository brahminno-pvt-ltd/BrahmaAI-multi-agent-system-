'use client'

import { useState, useEffect } from 'react'
import {
  Shield, Key, Users, Wrench, Activity, Save, Plus,
  Trash2, RefreshCw, Check, AlertTriangle, ChevronDown,
  Eye, EyeOff,
} from 'lucide-react'
import { useAuth } from '@/lib/auth'
import { useRouter } from 'next/navigation'

/* ─── Types ──────────────────────────────────────────────────────────────── */

type Tab = 'system' | 'users' | 'tools' | 'audit'

type ConfigState = {
  provider: string; model: string; temperature: string; maxTokens: string
  openaiKey: string; anthropicKey: string; serpKey: string
  maxIter: string; maxRetry: string; timeout: string
  jwtExpiry: string; origins: string; rateLimit: string
  debug: boolean
}

type ManagedUser = {
  id: number; username: string; role: 'admin' | 'user'
  email: string; lastSeen: string; status: 'active' | 'inactive'
}

type ToolConfig = {
  id: string; name: string; desc: string; enabled: boolean; plugin?: boolean
}

const DEFAULT_CONFIG: ConfigState = {
  provider: 'openai', model: 'gpt-4o', temperature: '0.2', maxTokens: '4096',
  openaiKey: '', anthropicKey: '', serpKey: '',
  maxIter: '10', maxRetry: '3', timeout: '60',
  jwtExpiry: '1440', origins: 'http://localhost:3000', rateLimit: '60',
  debug: false,
}

const INITIAL_USERS: ManagedUser[] = [
  { id: 1, username: 'admin', role: 'admin', email: 'admin@brahmaai.dev', lastSeen: 'just now', status: 'active' },
  { id: 2, username: 'demo',  role: 'user',  email: 'demo@brahmaai.dev',  lastSeen: '1h ago',   status: 'active' },
  { id: 3, username: 'alice', role: 'user',  email: 'alice@company.com',  lastSeen: '2d ago',   status: 'active' },
  { id: 4, username: 'bob',   role: 'user',  email: 'bob@company.com',    lastSeen: '5d ago',   status: 'inactive' },
]

const INITIAL_TOOLS: ToolConfig[] = [
  { id: 'web_search',    name: 'Web Search',    desc: 'SerpAPI with DuckDuckGo fallback', enabled: true },
  { id: 'web_scraper',   name: 'Web Scraper',   desc: 'HTML text extraction via BeautifulSoup', enabled: true },
  { id: 'file_reader',   name: 'File Reader',   desc: 'PDF, CSV, TXT, MD, JSON support', enabled: true },
  { id: 'code_executor', name: 'Code Executor', desc: 'Sandboxed Python subprocess runner', enabled: true },
  { id: 'email_tool',    name: 'Email Tool',    desc: 'Email simulation layer (mock)', enabled: true },
  { id: 'calendar_tool', name: 'Calendar Tool', desc: 'Calendar scheduling mock API', enabled: true },
  { id: 'stock_price',   name: 'Stock Price',   desc: 'yfinance plugin (pip install yfinance)', enabled: false, plugin: true },
  { id: 'weather',       name: 'Weather',       desc: 'Open-Meteo API — no key required', enabled: false, plugin: true },
]

const AUDIT_EVENTS = [
  { actor: 'admin', action: 'Saved system configuration', time: '2 min ago', type: 'config' },
  { actor: 'admin', action: 'Disabled stock_price tool', time: '15 min ago', type: 'tool' },
  { actor: 'demo',  action: 'Login success', time: '1 hour ago', type: 'auth' },
  { actor: 'admin', action: 'Deleted user bob@company.com', time: '2 hours ago', type: 'user' },
  { actor: 'admin', action: 'Login success from 127.0.0.1', time: '2 hours ago', type: 'auth' },
  { actor: 'alice', action: 'Login success', time: '2 days ago', type: 'auth' },
  { actor: 'admin', action: 'Changed LLM provider to Anthropic', time: '3 days ago', type: 'config' },
]

const AUDIT_COLORS: Record<string, string> = {
  config: 'var(--ac)',
  tool:   'var(--warn)',
  auth:   'var(--ok)',
  user:   'var(--err)',
}

/* ─── Sub-components ─────────────────────────────────────────────────────── */

function SectionHead({ children }: { children: string }) {
  return (
    <p style={{
      fontSize: 10, fontWeight: 600, color: 'var(--t3)',
      letterSpacing: '.07em', textTransform: 'uppercase',
      marginBottom: 10, marginTop: 4,
    }}>
      {children}
    </p>
  )
}

function FormRow({
  label, hint, children,
}: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 5, marginBottom: 12 }}>
      <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--t2)' }}>
        {label}
        {hint && <span style={{ color: 'var(--t3)', fontWeight: 400, marginLeft: 6 }}>{hint}</span>}
      </label>
      {children}
    </div>
  )
}

function Toggle({
  checked, onChange,
}: { checked: boolean; onChange: () => void }) {
  return (
    <label className="toggle-track">
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span className="toggle-thumb" />
    </label>
  )
}

function SaveBanner({ visible }: { visible: boolean }) {
  if (!visible) return null
  return (
    <div
      className="animate-fade-in"
      style={{
        position: 'absolute', top: 14, right: 16,
        display: 'flex', alignItems: 'center', gap: 6,
        padding: '6px 14px', borderRadius: 9, fontSize: 12,
        background: 'var(--ok-bg)', border: '1px solid var(--ok)', color: 'var(--ok)',
        zIndex: 10,
      }}
    >
      <Check size={12} /> Configuration saved
    </div>
  )
}

/* ─── System config tab ──────────────────────────────────────────────────── */

function SystemTab({
  config, setConfig, onSave,
}: { config: ConfigState; setConfig: React.Dispatch<React.SetStateAction<ConfigState>>; onSave: () => void }) {
  const [showOAI, setShowOAI] = useState(false)
  const [showANT, setShowANT] = useState(false)
  const set = (k: keyof ConfigState, v: string | boolean) =>
    setConfig(c => ({ ...c, [k]: v }))

  return (
    <div style={{ maxWidth: 600 }}>
      <SectionHead>LLM Provider</SectionHead>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <FormRow label="Provider">
          <select className="brahma-select" value={config.provider} onChange={e => set('provider', e.target.value)}>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
          </select>
        </FormRow>
        <FormRow label="Model">
          <select className="brahma-select" value={config.model} onChange={e => set('model', e.target.value)}>
            {config.provider === 'openai' ? (
              <>
                <option value="gpt-4o">gpt-4o</option>
                <option value="gpt-4o-mini">gpt-4o-mini</option>
                <option value="gpt-4-turbo">gpt-4-turbo</option>
              </>
            ) : (
              <>
                <option value="claude-3-5-sonnet-20241022">claude-3-5-sonnet</option>
                <option value="claude-3-haiku-20240307">claude-3-haiku</option>
                <option value="claude-opus-4-6">claude-opus-4</option>
              </>
            )}
          </select>
        </FormRow>
      </div>

      <FormRow label="OpenAI API Key">
        <div style={{ position: 'relative' }}>
          <input
            className="brahma-input"
            type={showOAI ? 'text' : 'password'}
            value={config.openaiKey}
            onChange={e => set('openaiKey', e.target.value)}
            placeholder="sk-…"
            style={{ paddingRight: 38 }}
          />
          <button
            type="button"
            onClick={() => setShowOAI(s => !s)}
            style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--t3)', display: 'flex' }}
          >
            {showOAI ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        </div>
      </FormRow>

      <FormRow label="Anthropic API Key">
        <div style={{ position: 'relative' }}>
          <input
            className="brahma-input"
            type={showANT ? 'text' : 'password'}
            value={config.anthropicKey}
            onChange={e => set('anthropicKey', e.target.value)}
            placeholder="sk-ant-…"
            style={{ paddingRight: 38 }}
          />
          <button
            type="button"
            onClick={() => setShowANT(s => !s)}
            style={{ position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--t3)', display: 'flex' }}
          >
            {showANT ? <EyeOff size={14} /> : <Eye size={14} />}
          </button>
        </div>
      </FormRow>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <FormRow label="Temperature" hint="0 – 1">
          <input className="brahma-input" type="number" step=".1" min="0" max="1" value={config.temperature} onChange={e => set('temperature', e.target.value)} />
        </FormRow>
        <FormRow label="Max Tokens">
          <input className="brahma-input" type="number" value={config.maxTokens} onChange={e => set('maxTokens', e.target.value)} />
        </FormRow>
      </div>

      <div style={{ height: 1, background: 'var(--border)', margin: '8px 0 16px' }} />
      <SectionHead>Agent Loop</SectionHead>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
        <FormRow label="Max Iterations">
          <input className="brahma-input" type="number" value={config.maxIter} onChange={e => set('maxIter', e.target.value)} />
        </FormRow>
        <FormRow label="Max Retries">
          <input className="brahma-input" type="number" value={config.maxRetry} onChange={e => set('maxRetry', e.target.value)} />
        </FormRow>
        <FormRow label="Step Timeout (s)">
          <input className="brahma-input" type="number" value={config.timeout} onChange={e => set('timeout', e.target.value)} />
        </FormRow>
      </div>

      <div style={{ height: 1, background: 'var(--border)', margin: '8px 0 16px' }} />
      <SectionHead>Security</SectionHead>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <FormRow label="JWT Expiry (min)">
          <input className="brahma-input" type="number" value={config.jwtExpiry} onChange={e => set('jwtExpiry', e.target.value)} />
        </FormRow>
        <FormRow label="Rate Limit (req/window)">
          <input className="brahma-input" type="number" value={config.rateLimit} onChange={e => set('rateLimit', e.target.value)} />
        </FormRow>
      </div>

      <FormRow label="SerpAPI Key" hint="optional">
        <input className="brahma-input" value={config.serpKey} onChange={e => set('serpKey', e.target.value)} placeholder="Leave empty to use DuckDuckGo" />
      </FormRow>

      <FormRow label="Allowed Origins (CORS)">
        <input className="brahma-input" value={config.origins} onChange={e => set('origins', e.target.value)} />
      </FormRow>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 13px', background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 9, marginBottom: 16 }}>
        <div>
          <p style={{ fontSize: 13, color: 'var(--t1)' }}>Debug Mode</p>
          <p style={{ fontSize: 11, color: 'var(--t2)' }}>Verbose colored logs in the terminal</p>
        </div>
        <Toggle checked={config.debug} onChange={() => set('debug', !config.debug)} />
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <button
          onClick={onSave}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '9px 20px', borderRadius: 10, border: 'none',
            background: 'var(--ac)', color: '#fff', fontSize: 13, fontWeight: 500,
            cursor: 'pointer', fontFamily: 'var(--font-body)',
          }}
        >
          <Save size={14} /> Save Configuration
        </button>
      </div>
    </div>
  )
}

/* ─── Users tab ──────────────────────────────────────────────────────────── */

function UsersTab({
  users, setUsers,
}: { users: ManagedUser[]; setUsers: React.Dispatch<React.SetStateAction<ManagedUser[]>> }) {
  const [delConfirm, setDelConfirm] = useState<number | null>(null)
  const { user: currentUser } = useAuth()

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
        <p style={{ fontSize: 13, color: 'var(--t2)' }}>{users.length} accounts registered</p>
        <button
          style={{
            display: 'flex', alignItems: 'center', gap: 5,
            padding: '6px 14px', borderRadius: 8, border: '1px solid var(--ac-br)',
            background: 'var(--ac-bg)', color: 'var(--ac)', cursor: 'pointer',
            fontSize: 12, fontFamily: 'var(--font-body)',
          }}
        >
          <Plus size={12} /> Add User
        </button>
      </div>

      {users.map(u => (
        <div
          key={u.id}
          style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '10px 12px', background: 'var(--bg2)',
            border: '1px solid var(--border)', borderRadius: 10, marginBottom: 7,
          }}
        >
          {/* Avatar */}
          <div style={{
            width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
            background: u.role === 'admin' ? 'var(--adm-bg)' : 'var(--ac-bg)',
            border: `1px solid ${u.role === 'admin' ? 'var(--adm-br)' : 'var(--ac-br)'}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 11, fontWeight: 600,
            color: u.role === 'admin' ? 'var(--adm)' : 'var(--ac)',
          }}>
            {u.username.slice(0, 2).toUpperCase()}
          </div>

          {/* Info */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 13, fontWeight: 450, color: 'var(--t1)' }}>{u.username}</div>
            <div style={{ fontSize: 11, color: 'var(--t2)' }}>{u.email}</div>
          </div>

          {/* Meta */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
            <span className={u.role === 'admin' ? 'badge badge-admin' : 'badge badge-user'}>
              {u.role}
            </span>
            <span style={{
              fontSize: 10, padding: '2px 8px', borderRadius: 99,
              background: u.status === 'active' ? 'var(--ok-bg)' : 'var(--warn-bg)',
              color: u.status === 'active' ? 'var(--ok)' : 'var(--warn)',
            }}>
              {u.status}
            </span>
            <span style={{ fontSize: 11, color: 'var(--t3)', minWidth: 52, textAlign: 'right' }}>
              {u.lastSeen}
            </span>

            {/* Delete — can't delete yourself or other admins */}
            {u.role !== 'admin' && u.username !== currentUser?.username && (
              delConfirm === u.id ? (
                <div style={{ display: 'flex', gap: 4 }}>
                  <button
                    onClick={() => { setUsers(us => us.filter(x => x.id !== u.id)); setDelConfirm(null) }}
                    style={{ padding: '3px 10px', borderRadius: 6, fontSize: 11, background: 'var(--err-bg)', border: '1px solid var(--err)', color: 'var(--err)', cursor: 'pointer', fontFamily: 'var(--font-body)' }}
                  >
                    Delete
                  </button>
                  <button
                    onClick={() => setDelConfirm(null)}
                    style={{ padding: '3px 8px', borderRadius: 6, fontSize: 11, background: 'var(--bg1)', border: '1px solid var(--border)', color: 'var(--t2)', cursor: 'pointer', fontFamily: 'var(--font-body)' }}
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setDelConfirm(u.id)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--t3)', padding: 4, display: 'flex' }}
                  onMouseEnter={e => (e.currentTarget.style.color = 'var(--err)')}
                  onMouseLeave={e => (e.currentTarget.style.color = 'var(--t3)')}
                >
                  <Trash2 size={13} />
                </button>
              )
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

/* ─── Tools tab ──────────────────────────────────────────────────────────── */

function ToolsTab({
  tools, setTools, onSave,
}: { tools: ToolConfig[]; setTools: React.Dispatch<React.SetStateAction<ToolConfig[]>>; onSave: () => void }) {
  const toggleTool = (id: string) =>
    setTools(ts => ts.map(t => t.id === id ? { ...t, enabled: !t.enabled } : t))

  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--t2)', marginBottom: 14 }}>
        Enable or disable tools. Changes take effect on the next agent task.
      </p>

      <SectionHead>Built-in Tools</SectionHead>
      {tools.filter(t => !t.plugin).map(t => (
        <div
          key={t.id}
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '10px 13px', background: 'var(--bg2)', border: '1px solid var(--border)',
            borderRadius: 9, marginBottom: 6,
          }}
        >
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: 13, fontWeight: 450, color: 'var(--t1)', fontFamily: 'var(--font-mono)' }}>{t.name}</p>
            <p style={{ fontSize: 11, color: 'var(--t2)', marginTop: 1 }}>{t.desc}</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 11, color: t.enabled ? 'var(--ok)' : 'var(--t3)' }}>
              {t.enabled ? 'enabled' : 'disabled'}
            </span>
            <Toggle checked={t.enabled} onChange={() => toggleTool(t.id)} />
          </div>
        </div>
      ))}

      <div style={{ height: 1, background: 'var(--border)', margin: '14px 0' }} />
      <SectionHead>Plugin Tools</SectionHead>
      {tools.filter(t => t.plugin).map(t => (
        <div
          key={t.id}
          style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '10px 13px', background: 'var(--bg2)', border: '1px solid var(--border)',
            borderRadius: 9, marginBottom: 6,
          }}
        >
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: 13, fontWeight: 450, color: 'var(--t1)', fontFamily: 'var(--font-mono)' }}>{t.name}</p>
            <p style={{ fontSize: 11, color: 'var(--t2)', marginTop: 1 }}>{t.desc}</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 11, color: t.enabled ? 'var(--ok)' : 'var(--t3)' }}>
              {t.enabled ? 'enabled' : 'disabled'}
            </span>
            <Toggle checked={t.enabled} onChange={() => toggleTool(t.id)} />
          </div>
        </div>
      ))}

      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 14 }}>
        <button
          onClick={onSave}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '9px 20px', borderRadius: 10, border: 'none',
            background: 'var(--ac)', color: '#fff', fontSize: 13, fontWeight: 500,
            cursor: 'pointer', fontFamily: 'var(--font-body)',
          }}
        >
          <Save size={14} /> Save Tool Config
        </button>
      </div>
    </div>
  )
}

/* ─── Audit tab ──────────────────────────────────────────────────────────── */

function AuditTab() {
  return (
    <div>
      <p style={{ fontSize: 12, color: 'var(--t2)', marginBottom: 14 }}>
        Immutable log of all admin actions. Read-only.
      </p>
      {AUDIT_EVENTS.map((ev, i) => (
        <div
          key={i}
          style={{
            display: 'flex', alignItems: 'flex-start', gap: 10,
            padding: '9px 0', borderBottom: '1px solid var(--border)',
          }}
        >
          <div style={{
            width: 7, height: 7, borderRadius: '50%', flexShrink: 0, marginTop: 5,
            background: AUDIT_COLORS[ev.type] ?? 'var(--t3)',
          }} />
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: 12, color: 'var(--adm)', fontWeight: 500 }}>[{ev.actor}]</span>
            <span style={{ fontSize: 12, color: 'var(--t2)', marginLeft: 5 }}>{ev.action}</span>
          </div>
          <span style={{ fontSize: 11, color: 'var(--t3)', flexShrink: 0 }}>{ev.time}</span>
        </div>
      ))}
    </div>
  )
}

/* ─── Main Admin Page ────────────────────────────────────────────────────── */

export default function AdminPage() {
  const { isAdmin, isLoading } = useAuth()
  const router = useRouter()
  const [tab, setTab]       = useState<Tab>('system')
  const [config, setConfig] = useState<ConfigState>(DEFAULT_CONFIG)
  const [users,  setUsers]  = useState<ManagedUser[]>(INITIAL_USERS)
  const [tools,  setTools]  = useState<ToolConfig[]>(INITIAL_TOOLS)
  const [saved,  setSaved]  = useState(false)

  useEffect(() => {
    if (!isLoading && !isAdmin) router.replace('/chat')
  }, [isAdmin, isLoading, router])

  if (isLoading || !isAdmin) return null

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 2500)
  }

  const TABS: { id: Tab; icon: React.ComponentType<{ size?: number }>; label: string }[] = [
    { id: 'system', icon: Key,      label: 'System' },
    { id: 'users',  icon: Users,    label: 'Users' },
    { id: 'tools',  icon: Wrench,   label: 'Tools' },
    { id: 'audit',  icon: Activity, label: 'Audit Log' },
  ]

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      <SaveBanner visible={saved} />

      {/* Header */}
      <div style={{
        padding: '14px 22px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--adm-bg)',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Shield size={18} style={{ color: 'var(--adm)' }} />
          <div>
            <p style={{ fontWeight: 500, color: 'var(--adm)', fontSize: 15, margin: 0 }}>Admin Panel</p>
            <p style={{ fontSize: 11, color: 'var(--t2)', margin: 0, marginTop: 1 }}>
              Restricted access — visible to administrators only
            </p>
          </div>
        </div>
      </div>

      {/* Tab bar */}
      <div style={{
        padding: '10px 18px',
        borderBottom: '1px solid var(--border)',
        flexShrink: 0,
        display: 'flex', gap: 4,
      }}>
        {TABS.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 14px', borderRadius: 9, cursor: 'pointer',
              fontSize: 13, fontFamily: 'var(--font-body)',
              background: tab === id ? 'var(--bg2)' : 'transparent',
              border: tab === id ? '1px solid var(--border-s)' : '1px solid transparent',
              color: tab === id ? 'var(--t1)' : 'var(--t2)',
              fontWeight: tab === id ? 500 : 400,
              transition: 'all .15s',
            }}
          >
            <Icon size={13} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '18px 22px' }}>
        {tab === 'system' && <SystemTab config={config} setConfig={setConfig} onSave={handleSave} />}
        {tab === 'users'  && <UsersTab  users={users} setUsers={setUsers} />}
        {tab === 'tools'  && <ToolsTab  tools={tools} setTools={setTools} onSave={handleSave} />}
        {tab === 'audit'  && <AuditTab />}
      </div>
    </div>
  )
}
