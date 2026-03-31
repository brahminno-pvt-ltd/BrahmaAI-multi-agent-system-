'use client'

import { useState } from 'react'
import { Cpu, Eye, EyeOff, Loader2, AlertCircle, Sun, Moon } from 'lucide-react'
import { useAuth } from '@/lib/auth'
import { useTheme } from '@/lib/theme'

const FEATURES = [
  { color: 'var(--ac)',   title: 'Agent Loop',     desc: 'Planner → Executor → Critic → Memory' },
  { color: 'var(--ok)',   title: '6 Real Tools',   desc: 'Web, Scraper, Code, Files, Email, Calendar' },
  { color: 'var(--warn)', title: 'Vector Memory',  desc: 'FAISS long-term + session short-term' },
  { color: 'var(--adm)',  title: 'Live Streaming', desc: 'Every reasoning step observable in real-time' },
]

const DEMO_ACCOUNTS = [
  { username: 'admin', password: 'brahmaai123', label: 'Admin',  note: 'Full access + admin panel' },
  { username: 'demo',  password: 'demo',        label: 'Demo',   note: 'Standard user access' },
]

export default function LoginPage() {
  const { login } = useAuth()
  const { theme, toggle } = useTheme()
  const [username, setUsername]   = useState('')
  const [password, setPassword]   = useState('')
  const [showPw,   setShowPw]     = useState(false)
  const [error,    setError]      = useState<string | null>(null)
  const [loading,  setLoading]    = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!username.trim() || !password.trim()) return
    setLoading(true); setError(null)
    try {
      await login(username.trim(), password)
    } catch (err: unknown) {
      setError((err as Error)?.message || 'Invalid username or password')
      setLoading(false)
    }
  }

  const fillDemo = (u: string, p: string) => { setUsername(u); setPassword(p); setError(null) }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', background: 'var(--bg0)', color: 'var(--t1)' }}>

      {/* ── Left panel: form ─────────────────────────────────────────────── */}
      <div style={{
        width: 360, flexShrink: 0,
        background: 'var(--bg1)', borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column', justifyContent: 'center',
        padding: '40px 32px', position: 'relative',
      }}>

        {/* Theme toggle */}
        <button
          onClick={toggle}
          title="Toggle theme"
          style={{
            position: 'absolute', top: 18, right: 18,
            width: 34, height: 34, borderRadius: 9, cursor: 'pointer',
            background: 'var(--bg2)', border: '1px solid var(--border)',
            color: 'var(--t2)', display: 'flex', alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        </button>

        {/* Logo */}
        <div style={{ marginBottom: 32 }}>
          <div style={{
            width: 44, height: 44, borderRadius: 13, marginBottom: 14,
            background: 'var(--ac-bg)', border: '1px solid var(--ac-br)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Cpu size={20} style={{ color: 'var(--ac)' }} />
          </div>
          <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--t1)', margin: 0 }}>
            BrahmaAI
          </h1>
          <p style={{ fontSize: 12, color: 'var(--t2)', marginTop: 3 }}>
            Autonomous Multi-Agent System
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--t2)' }}>Username</label>
            <input
              className="brahma-input"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="admin or demo"
              autoComplete="username"
              autoFocus
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
            <label style={{ fontSize: 11, fontWeight: 500, color: 'var(--t2)' }}>Password</label>
            <div style={{ position: 'relative' }}>
              <input
                className="brahma-input"
                type={showPw ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                style={{ paddingRight: 38 }}
              />
              <button
                type="button"
                onClick={() => setShowPw(s => !s)}
                style={{
                  position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer',
                  color: 'var(--t3)', display: 'flex', padding: 2,
                }}
              >
                {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </div>

          {error && (
            <div
              className="animate-fade-in"
              style={{
                display: 'flex', alignItems: 'center', gap: 7,
                padding: '8px 11px', borderRadius: 9, fontSize: 12,
                background: 'var(--err-bg)', border: '1px solid var(--err)', color: 'var(--err)',
              }}
            >
              <AlertCircle size={13} style={{ flexShrink: 0 }} />
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !username.trim() || !password.trim()}
            style={{
              width: '100%', padding: '10px', borderRadius: 10, border: 'none',
              background: 'var(--ac)', color: '#fff', fontSize: 14, fontWeight: 500,
              cursor: loading || !username.trim() || !password.trim() ? 'not-allowed' : 'pointer',
              opacity: loading || !username.trim() || !password.trim() ? 0.55 : 1,
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 7,
              fontFamily: 'var(--font-body)',
              marginTop: 4,
            }}
          >
            {loading ? (
              <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />Signing in…</>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Divider */}
        <div style={{ position: 'relative', margin: '20px 0 14px' }}>
          <div style={{ height: 1, background: 'var(--border)' }} />
          <span style={{
            position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
            background: 'var(--bg1)', padding: '0 8px', fontSize: 10,
            color: 'var(--t3)', letterSpacing: '.06em', textTransform: 'uppercase',
          }}>
            Demo accounts
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {DEMO_ACCOUNTS.map(({ username: u, password: p, label, note }) => (
            <button
              key={u}
              type="button"
              onClick={() => fillDemo(u, p)}
              style={{
                padding: '10px 8px', borderRadius: 10,
                background: 'var(--bg2)', border: '1px solid var(--border)',
                cursor: 'pointer', display: 'flex', flexDirection: 'column',
                alignItems: 'center', gap: 3, fontFamily: 'var(--font-body)',
                transition: 'border-color .15s',
              }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = 'var(--ac-br)')}
              onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
            >
              <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--t1)' }}>{label}</span>
              <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--t2)' }}>{u}</span>
              <span style={{ fontSize: 10, color: 'var(--t3)', textAlign: 'center', lineHeight: 1.3 }}>{note}</span>
            </button>
          ))}
        </div>

        <p style={{ textAlign: 'center', fontSize: 10, color: 'var(--t3)', marginTop: 28 }}>
          BrahmaAI v1.0.0 · MIT License
        </p>
      </div>

      {/* ── Right panel: showcase ─────────────────────────────────────────── */}
      <div
        className="bg-grid"
        style={{
          flex: 1, display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          padding: '0 48px', gap: 28,
        }}
      >
        <div style={{ textAlign: 'center', maxWidth: 420 }}>
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--t3)', letterSpacing: '.08em', textTransform: 'uppercase', marginBottom: 10 }}>
            Goal → Plan → Execute → Reflect
          </p>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, color: 'var(--t1)', lineHeight: 1.2, marginBottom: 12 }}>
            Not a chatbot.<br />An autonomous agent.
          </h2>
          <p style={{ fontSize: 14, color: 'var(--t2)', lineHeight: 1.7 }}>
            BrahmaAI breaks your goal into structured steps, runs real tools,
            scores its own output quality, and refines until the task is done right.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, width: '100%', maxWidth: 440 }}>
          {FEATURES.map(({ color, title, desc }) => (
            <div
              key={title}
              style={{
                background: 'var(--bg1)', border: '1px solid var(--border)',
                borderLeft: `3px solid ${color}`,
                borderRadius: '0 10px 10px 0',
                padding: '12px 14px',
              }}
            >
              <p style={{ fontSize: 13, fontWeight: 500, color: 'var(--t1)', marginBottom: 3 }}>{title}</p>
              <p style={{ fontSize: 11, color: 'var(--t2)', lineHeight: 1.5 }}>{desc}</p>
            </div>
          ))}
        </div>

        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '8px 18px', borderRadius: 99,
          background: 'var(--bg1)', border: '1px solid var(--border)',
          fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--t2)',
        }}>
          {['Plan', 'Execute', 'Observe', 'Reflect'].map((s, i) => (
            <span key={s} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ color: 'var(--ac)' }}>{s}</span>
              {i < 3 && <span style={{ color: 'var(--t3)' }}>→</span>}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
