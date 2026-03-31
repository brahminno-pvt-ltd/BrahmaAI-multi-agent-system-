'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-react'
import { clsx } from 'clsx'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export type Toast = {
  id: string
  type: ToastType
  title: string
  message?: string
  duration?: number
}

const TOAST_ICONS = {
  success: CheckCircle2,
  error:   XCircle,
  warning: AlertTriangle,
  info:    Info,
}

const TOAST_STYLES = {
  success: 'border-signal-green/30 bg-signal-green/5 text-signal-green',
  error:   'border-signal-red/30 bg-signal-red/5 text-signal-red',
  warning: 'border-signal-amber/30 bg-signal-amber/5 text-signal-amber',
  info:    'border-accent/30 bg-accent/5 text-accent',
}

// ─── Single Toast Item ────────────────────────────────────────────────────────

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: string) => void }) {
  const [visible, setVisible] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout>>()
  const Icon = TOAST_ICONS[toast.type]
  const duration = toast.duration ?? 4000

  useEffect(() => {
    // Animate in
    requestAnimationFrame(() => setVisible(true))

    // Auto-dismiss
    timerRef.current = setTimeout(() => {
      setVisible(false)
      setTimeout(() => onDismiss(toast.id), 300)
    }, duration)

    return () => clearTimeout(timerRef.current)
  }, [toast.id, duration, onDismiss])

  return (
    <div className={clsx(
      'flex items-start gap-3 px-4 py-3 rounded-xl border backdrop-blur-sm',
      'shadow-xl shadow-black/30 max-w-sm w-full transition-all duration-300',
      TOAST_STYLES[toast.type],
      visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
    )}>
      <Icon size={15} className="shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary leading-tight">{toast.title}</p>
        {toast.message && (
          <p className="text-xs text-text-muted mt-0.5 leading-relaxed">{toast.message}</p>
        )}
      </div>
      <button
        onClick={() => {
          setVisible(false)
          setTimeout(() => onDismiss(toast.id), 300)
        }}
        className="shrink-0 text-text-muted hover:text-text-primary transition-colors mt-0.5"
      >
        <X size={13} />
      </button>
    </div>
  )
}

// ─── Toast Container ──────────────────────────────────────────────────────────

export function ToastContainer({ toasts, onDismiss }: {
  toasts: Toast[]
  onDismiss: (id: string) => void
}) {
  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
      {toasts.map(toast => (
        <div key={toast.id} className="pointer-events-auto">
          <ToastItem toast={toast} onDismiss={onDismiss} />
        </div>
      ))}
    </div>
  )
}

// ─── useToast hook ────────────────────────────────────────────────────────────

const genId = () => Math.random().toString(36).slice(2, 9)

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: string) => {
    setToasts(t => t.filter(toast => toast.id !== id))
  }, [])

  const push = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = genId()
    setToasts(t => [...t, { ...toast, id }])
    return id
  }, [])

  const success = useCallback((title: string, message?: string) =>
    push({ type: 'success', title, message }), [push])

  const error = useCallback((title: string, message?: string) =>
    push({ type: 'error', title, message, duration: 6000 }), [push])

  const warning = useCallback((title: string, message?: string) =>
    push({ type: 'warning', title, message }), [push])

  const info = useCallback((title: string, message?: string) =>
    push({ type: 'info', title, message }), [push])

  return { toasts, dismiss, push, success, error, warning, info }
}
