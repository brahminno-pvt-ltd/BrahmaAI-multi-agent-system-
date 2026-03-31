/**
 * BrahmaAI Custom Hooks
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { useBrahmaStore } from '@/lib/store'
import { healthApi } from '@/lib/api'

// ─── useAutoScroll ────────────────────────────────────────────────────────────

/**
 * Auto-scrolls a container to the bottom when dependencies change,
 * but only if the user hasn't manually scrolled up.
 */
export function useAutoScroll(deps: unknown[]) {
  const ref = useRef<HTMLDivElement>(null)
  const [isAtBottom, setIsAtBottom] = useState(true)

  const handleScroll = useCallback(() => {
    const el = ref.current
    if (!el) return
    const threshold = 80
    setIsAtBottom(el.scrollHeight - el.scrollTop - el.clientHeight < threshold)
  }, [])

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.addEventListener('scroll', handleScroll, { passive: true })
    return () => el.removeEventListener('scroll', handleScroll)
  }, [handleScroll])

  useEffect(() => {
    if (isAtBottom && ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { ref, isAtBottom }
}

// ─── useHealthCheck ───────────────────────────────────────────────────────────

/**
 * Polls the backend health endpoint every 30 seconds.
 */
export function useHealthCheck(intervalMs = 30_000) {
  const [health, setHealth] = useState<{
    status: string
    provider: string
    version: string
  } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const check = useCallback(async () => {
    try {
      const result = await healthApi.check()
      setHealth(result)
      setError(null)
    } catch (e) {
      setError('Backend offline')
      setHealth(null)
    }
  }, [])

  useEffect(() => {
    check()
    const interval = setInterval(check, intervalMs)
    return () => clearInterval(interval)
  }, [check, intervalMs])

  return { health, error, refetch: check }
}

// ─── usePendingPrompt ─────────────────────────────────────────────────────────

/**
 * Reads and clears a "pending prompt" stored in sessionStorage.
 * Used by the Dashboard to launch demo tasks in the Chat view.
 */
export function usePendingPrompt(): string | null {
  const [prompt, setPrompt] = useState<string | null>(null)

  useEffect(() => {
    const pending = sessionStorage.getItem('brahma_pending_prompt')
    if (pending) {
      sessionStorage.removeItem('brahma_pending_prompt')
      setPrompt(pending)
    }
  }, [])

  return prompt
}

// ─── useKeyboardShortcut ──────────────────────────────────────────────────────

/**
 * Register a global keyboard shortcut.
 * e.g. useKeyboardShortcut(['Meta', 'k'], () => openSearch())
 */
export function useKeyboardShortcut(
  keys: string[],
  callback: (e: KeyboardEvent) => void,
  options: { enabled?: boolean } = {}
) {
  const { enabled = true } = options

  useEffect(() => {
    if (!enabled) return

    const handler = (e: KeyboardEvent) => {
      const pressed = keys.every(key => {
        switch (key) {
          case 'Meta': return e.metaKey
          case 'Ctrl': return e.ctrlKey
          case 'Alt': return e.altKey
          case 'Shift': return e.shiftKey
          default: return e.key === key || e.code === key
        }
      })
      if (pressed) callback(e)
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [keys, callback, enabled])
}

// ─── useLocalStorage ─────────────────────────────────────────────────────────

/**
 * Synced localStorage state.
 */
export function useLocalStorage<T>(
  key: string,
  defaultValue: T
): [T, (v: T) => void] {
  const [value, setValue] = useState<T>(() => {
    if (typeof window === 'undefined') return defaultValue
    try {
      const stored = window.localStorage.getItem(key)
      return stored ? JSON.parse(stored) : defaultValue
    } catch {
      return defaultValue
    }
  })

  const set = useCallback((v: T) => {
    setValue(v)
    try {
      window.localStorage.setItem(key, JSON.stringify(v))
    } catch {}
  }, [key])

  return [value, set]
}

// ─── useCopyToClipboard ───────────────────────────────────────────────────────

export function useCopyToClipboard(resetMs = 2000) {
  const [copied, setCopied] = useState(false)

  const copy = useCallback(async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), resetMs)
    } catch {}
  }, [resetMs])

  return { copied, copy }
}
