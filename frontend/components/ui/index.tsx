/**
 * BrahmaAI Shared UI Components
 */

import { clsx } from 'clsx'
import { Loader2 } from 'lucide-react'

// ─── Badge ────────────────────────────────────────────────────────────────────

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'accent' | 'blue'

const BADGE_VARIANTS: Record<BadgeVariant, string> = {
  default: 'bg-muted/30 text-text-muted border-border',
  success: 'bg-signal-green/10 text-signal-green border-signal-green/20',
  warning: 'bg-signal-amber/10 text-signal-amber border-signal-amber/20',
  error:   'bg-signal-red/10 text-signal-red border-signal-red/20',
  accent:  'bg-accent/10 text-accent border-accent/20',
  blue:    'bg-signal-blue/10 text-signal-blue border-signal-blue/20',
}

export function Badge({
  children,
  variant = 'default',
  className,
}: {
  children: React.ReactNode
  variant?: BadgeVariant
  className?: string
}) {
  return (
    <span className={clsx(
      'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-medium border',
      BADGE_VARIANTS[variant],
      className
    )}>
      {children}
    </span>
  )
}

// ─── Card ─────────────────────────────────────────────────────────────────────

export function Card({
  children,
  className,
  hover = false,
  glow = false,
}: {
  children: React.ReactNode
  className?: string
  hover?: boolean
  glow?: boolean
}) {
  return (
    <div className={clsx(
      'bg-panel border border-border rounded-xl',
      hover && 'hover:border-muted transition-colors',
      glow && 'glow-accent',
      className
    )}>
      {children}
    </div>
  )
}

export function CardHeader({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={clsx('px-4 py-3 border-b border-border', className)}>
      {children}
    </div>
  )
}

export function CardBody({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={clsx('px-4 py-3', className)}>
      {children}
    </div>
  )
}

// ─── Spinner ──────────────────────────────────────────────────────────────────

export function Spinner({ size = 16, className }: { size?: number; className?: string }) {
  return <Loader2 size={size} className={clsx('animate-spin text-text-muted', className)} />
}

// ─── StatusDot ───────────────────────────────────────────────────────────────

type StatusColor = 'green' | 'amber' | 'red' | 'blue' | 'gray'

const STATUS_COLORS: Record<StatusColor, string> = {
  green: 'bg-signal-green',
  amber: 'bg-signal-amber',
  red:   'bg-signal-red',
  blue:  'bg-signal-blue',
  gray:  'bg-text-muted',
}

export function StatusDot({
  color = 'gray',
  pulse = false,
  className,
}: {
  color?: StatusColor
  pulse?: boolean
  className?: string
}) {
  return (
    <span className={clsx(
      'inline-block w-1.5 h-1.5 rounded-full shrink-0',
      STATUS_COLORS[color],
      pulse && 'animate-pulse',
      className
    )} />
  )
}

// ─── EmptyState ───────────────────────────────────────────────────────────────

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: React.ComponentType<{ size?: number; className?: string }>
  title: string
  description?: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center gap-3">
      <Icon size={32} className="text-text-muted opacity-25" />
      <div>
        <p className="text-sm font-medium text-text-secondary">{title}</p>
        {description && (
          <p className="text-xs text-text-muted mt-1 max-w-xs">{description}</p>
        )}
      </div>
      {action}
    </div>
  )
}

// ─── Tooltip ─────────────────────────────────────────────────────────────────

export function Tooltip({
  children,
  content,
  side = 'top',
}: {
  children: React.ReactNode
  content: string
  side?: 'top' | 'bottom' | 'left' | 'right'
}) {
  const positions: Record<string, string> = {
    top:    'bottom-full left-1/2 -translate-x-1/2 mb-1.5',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-1.5',
    left:   'right-full top-1/2 -translate-y-1/2 mr-1.5',
    right:  'left-full top-1/2 -translate-y-1/2 ml-1.5',
  }

  return (
    <div className="relative group inline-flex">
      {children}
      <div className={clsx(
        'absolute z-50 px-2 py-1 text-[10px] text-text-primary bg-panel border border-border rounded-md',
        'whitespace-nowrap pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity',
        positions[side]
      )}>
        {content}
      </div>
    </div>
  )
}

// ─── KeyboardShortcut ────────────────────────────────────────────────────────

export function KbdShortcut({ keys }: { keys: string[] }) {
  return (
    <span className="flex items-center gap-0.5">
      {keys.map((k, i) => (
        <kbd key={i} className="px-1.5 py-0.5 text-[10px] font-mono bg-muted/30 border border-border rounded text-text-muted">
          {k}
        </kbd>
      ))}
    </span>
  )
}

// ─── CodeBlock ───────────────────────────────────────────────────────────────

export function CodeBlock({
  code,
  language = 'python',
  className,
}: {
  code: string
  language?: string
  className?: string
}) {
  return (
    <div className={clsx('relative rounded-lg overflow-hidden border border-border', className)}>
      <div className="flex items-center justify-between px-3 py-1.5 bg-muted/20 border-b border-border">
        <span className="text-[10px] font-mono text-text-muted uppercase">{language}</span>
      </div>
      <pre className="p-4 overflow-x-auto text-xs font-mono text-text-secondary leading-relaxed bg-surface">
        <code>{code}</code>
      </pre>
    </div>
  )
}

// ─── SectionHeader ────────────────────────────────────────────────────────────

export function SectionHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h2 className="font-display font-semibold text-sm text-text-secondary uppercase tracking-widest">
          {title}
        </h2>
        {subtitle && (
          <p className="text-xs text-text-muted mt-0.5">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  )
}
