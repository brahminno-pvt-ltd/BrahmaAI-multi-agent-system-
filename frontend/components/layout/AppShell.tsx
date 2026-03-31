'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  MessageSquare, LayoutDashboard, ScrollText, Database,
  Cpu, Settings, Shield, Activity, Sun, Moon,
  ChevronLeft, ChevronRight, LogOut, User, Zap, Menu, X,
} from 'lucide-react'
import { useAuth } from '@/lib/auth'
import { useTheme } from '@/lib/theme'

type NavItem = {
  href: string
  icon: React.ComponentType<{ size?: number }>
  label: string
  badge?: 'live' | null
  adminOnly?: boolean
}

const NAV_ITEMS: NavItem[] = [
  { href: '/chat',      icon: MessageSquare,   label: 'Chat' },
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/agents',    icon: Cpu,             label: 'Agents' },
  { href: '/logs',      icon: ScrollText,      label: 'Agent Logs', badge: 'live' },
  { href: '/memory',    icon: Database,        label: 'Memory' },
  { href: '/settings',  icon: Settings,        label: 'Settings' },
]

const ADMIN_NAV: NavItem[] = [
  { href: '/admin', icon: Shield, label: 'Admin Panel', adminOnly: true },
]

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const pathname  = usePathname()
  const { user, isAdmin, logout } = useAuth()
  const { theme, toggle } = useTheme()
  const isDark = theme === 'dark'

  const NavLink = ({ item }: { item: NavItem }) => {
    const isActive  = pathname.startsWith(item.href)
    const isAdminNv = item.adminOnly

    return (
      <Link
        href={item.href}
        onClick={() => setMobileOpen(false)}
        title={collapsed ? item.label : undefined}
        style={{
          display: 'flex', alignItems: 'center',
          gap: collapsed ? 0 : 9,
          padding: collapsed ? '8px' : '7px 10px',
          justifyContent: collapsed ? 'center' : 'flex-start',
          borderRadius: 9, margin: '1px 6px',
          textDecoration: 'none', fontSize: 13, fontWeight: 450,
          transition: 'all .15s',
          color: isActive
            ? (isAdminNv ? 'var(--adm)' : 'var(--ac)')
            : 'var(--t2)',
          background: isActive
            ? (isAdminNv ? 'var(--adm-bg)' : 'var(--ac-bg)')
            : 'transparent',
          border: isActive
            ? `1px solid ${isAdminNv ? 'var(--adm-br)' : 'var(--ac-br)'}`
            : '1px solid transparent',
          overflow: 'hidden', whiteSpace: 'nowrap',
        }}
        onMouseEnter={e => {
          if (!isActive) {
            e.currentTarget.style.background = 'var(--bgh)'
            e.currentTarget.style.color = 'var(--t1)'
          }
        }}
        onMouseLeave={e => {
          if (!isActive) {
            e.currentTarget.style.background = 'transparent'
            e.currentTarget.style.color = 'var(--t2)'
          }
        }}
      >
        <item.icon size={15} />
        {!collapsed && (
          <>
            <span style={{ flex: 1 }}>{item.label}</span>
            {item.badge === 'live' && (
              <span style={{
                fontSize: 9, fontFamily: 'var(--font-mono)', fontWeight: 600,
                background: 'var(--ok-bg)', color: 'var(--ok)',
                padding: '1px 5px', borderRadius: 99, letterSpacing: '.04em',
              }}>
                LIVE
              </span>
            )}
          </>
        )}
      </Link>
    )
  }

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div style={{
        padding: '13px 12px 10px',
        borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center',
        justifyContent: collapsed ? 'center' : 'space-between',
        flexShrink: 0,
      }}>
        {!collapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 8, flexShrink: 0,
              background: 'var(--ac-bg)', border: '1px solid var(--ac-br)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Cpu size={14} style={{ color: 'var(--ac)' }} />
            </div>
            <div>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 13, fontWeight: 700, color: 'var(--t1)', lineHeight: 1 }}>
                BrahmaAI
              </div>
              <div style={{ fontSize: 10, color: 'var(--t2)', marginTop: 1 }}>
                {isAdmin ? 'Admin Workspace' : 'Workspace'}
              </div>
            </div>
          </div>
        )}
        {collapsed && (
          <div style={{
            width: 28, height: 28, borderRadius: 8,
            background: 'var(--ac-bg)', border: '1px solid var(--ac-br)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Cpu size={14} style={{ color: 'var(--ac)' }} />
          </div>
        )}
        <button
          onClick={() => setCollapsed(c => !c)}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--t3)', padding: 2, display: 'flex',
            display: collapsed ? 'none' : 'flex',
          }}
          className="hidden lg:flex"
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>
      </div>

      {/* Main nav */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        <div style={{ padding: collapsed ? '4px 0' : '0 6px 4px 10px', fontSize: 10, fontWeight: 600, color: 'var(--t3)', letterSpacing: '.06em', textTransform: 'uppercase', marginTop: 4 }}>
          {!collapsed && 'Main'}
        </div>
        {NAV_ITEMS.map(item => <NavLink key={item.href} item={item} />)}

        {/* Admin section — only rendered for admin users */}
        {isAdmin && (
          <>
            <div style={{ height: 1, background: 'var(--border)', margin: '8px 12px' }} />
            <div style={{ padding: collapsed ? '4px 0' : '0 6px 4px 10px', fontSize: 10, fontWeight: 600, color: 'var(--adm)', letterSpacing: '.06em', textTransform: 'uppercase', opacity: .8 }}>
              {!collapsed && 'Admin'}
            </div>
            {ADMIN_NAV.map(item => <NavLink key={item.href} item={item} />)}
          </>
        )}
      </div>

      {/* Bottom bar */}
      <div style={{ borderTop: '1px solid var(--border)', padding: '8px 6px', flexShrink: 0 }}>
        {/* User info */}
        {!collapsed && user && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8,
            padding: '6px 8px', marginBottom: 4,
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
              background: isAdmin ? 'var(--adm-bg)' : 'var(--ac-bg)',
              border: `1px solid ${isAdmin ? 'var(--adm-br)' : 'var(--ac-br)'}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 11, fontWeight: 600,
              color: isAdmin ? 'var(--adm)' : 'var(--ac)',
            }}>
              {user.username.slice(0, 2).toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 500, color: 'var(--t1)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.username}
              </div>
              <span className={isAdmin ? 'badge badge-admin' : 'badge badge-user'} style={{ fontSize: 9, padding: '1px 5px' }}>
                {user.role}
              </span>
            </div>
          </div>
        )}

        {/* Actions */}
        <div style={{ display: 'flex', gap: 4, padding: '0 2px' }}>
          <button
            onClick={toggle}
            title="Toggle theme"
            style={{
              flex: 1, padding: '6px', borderRadius: 8, cursor: 'pointer',
              background: 'none', border: '1px solid var(--border)',
              color: 'var(--t2)', display: 'flex', alignItems: 'center',
              justifyContent: 'center', gap: collapsed ? 0 : 4, fontSize: 11,
              fontFamily: 'var(--font-body)',
            }}
          >
            {isDark ? <Sun size={13} /> : <Moon size={13} />}
            {!collapsed && <span>Theme</span>}
          </button>
          <button
            onClick={logout}
            title="Sign out"
            style={{
              flex: 1, padding: '6px', borderRadius: 8, cursor: 'pointer',
              background: 'none', border: '1px solid var(--border)',
              color: 'var(--t2)', display: 'flex', alignItems: 'center',
              justifyContent: 'center', gap: collapsed ? 0 : 4, fontSize: 11,
              fontFamily: 'var(--font-body)',
            }}
          >
            <LogOut size={13} />
            {!collapsed && <span>Sign out</span>}
          </button>
        </div>
      </div>
    </>
  )

  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden', background: 'var(--bg0)', color: 'var(--t1)' }}>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,.6)',
            zIndex: 20,
          }}
        />
      )}

      {/* Sidebar */}
      <aside style={{
        width: collapsed ? 52 : 210,
        flexShrink: 0,
        background: 'var(--bg1)',
        borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column',
        transition: 'width .2s ease',
        height: '100%', overflowX: 'hidden',
        position: 'relative', zIndex: 30,
      }}
        className={`${mobileOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:relative`}
      >
        <SidebarContent />
      </aside>

      {/* Main content area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, overflow: 'hidden' }}>
        {/* Mobile topbar */}
        <div
          className="lg:hidden"
          style={{
            height: 52, flexShrink: 0,
            borderBottom: '1px solid var(--border)',
            background: 'var(--bg1)',
            display: 'flex', alignItems: 'center',
            padding: '0 16px', gap: 10,
          }}
        >
          <button
            onClick={() => setMobileOpen(o => !o)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--t2)', display: 'flex' }}
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <div style={{ width: 22, height: 22, borderRadius: 6, background: 'var(--ac-bg)', border: '1px solid var(--ac-br)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Cpu size={11} style={{ color: 'var(--ac)' }} />
            </div>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, color: 'var(--t1)' }}>BrahmaAI</span>
          </div>
        </div>

        <main style={{ flex: 1, overflow: 'hidden' }}>
          {children}
        </main>
      </div>
    </div>
  )
}
