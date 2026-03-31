'use client'

import { clsx } from 'clsx'

// ─── Base Skeleton ────────────────────────────────────────────────────────────

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={clsx('shimmer rounded-lg', className)} />
  )
}

// ─── Card Skeleton ────────────────────────────────────────────────────────────

export function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="bg-panel border border-border rounded-xl p-4 space-y-3">
      <div className="flex items-center gap-3">
        <Skeleton className="w-8 h-8 rounded-lg" />
        <div className="flex-1 space-y-1.5">
          <Skeleton className="h-3 w-2/3" />
          <Skeleton className="h-2.5 w-1/3" />
        </div>
      </div>
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton
            key={i}
            className="h-2.5"
            style={{ width: `${85 - i * 10}%` } as React.CSSProperties}
          />
        ))}
      </div>
    </div>
  )
}

// ─── Message Skeleton ─────────────────────────────────────────────────────────

export function MessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={clsx('flex gap-3', isUser && 'justify-end')}>
      {!isUser && <Skeleton className="w-7 h-7 rounded-lg shrink-0 mt-0.5" />}
      <div className={clsx('space-y-2', isUser ? 'items-end flex flex-col w-48' : 'flex-1 max-w-sm')}>
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </div>
    </div>
  )
}

// ─── Event Skeleton ───────────────────────────────────────────────────────────

export function EventSkeleton() {
  return (
    <div className="flex items-start gap-2 px-2 py-1.5">
      <Skeleton className="w-6 h-6 rounded-md shrink-0" />
      <div className="flex-1 space-y-1.5">
        <div className="flex items-center gap-2">
          <Skeleton className="h-2.5 w-16" />
          <Skeleton className="h-2 w-12 ml-auto" />
        </div>
        <Skeleton className="h-2.5 w-full" />
        <Skeleton className="h-2.5 w-3/4" />
      </div>
    </div>
  )
}

// ─── Memory Item Skeleton ─────────────────────────────────────────────────────

export function MemorySkeleton() {
  return (
    <div className="bg-panel border border-border rounded-xl p-3.5">
      <div className="flex items-start gap-3">
        <Skeleton className="w-6 h-6 rounded-md shrink-0 mt-0.5" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-5/6" />
          <Skeleton className="h-3 w-4/6" />
          <div className="flex items-center gap-3 mt-1">
            <Skeleton className="h-2 w-20" />
            <Skeleton className="h-2 w-16" />
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Dashboard Stats Skeleton ─────────────────────────────────────────────────

export function StatsSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {[1, 2, 3, 4].map(i => (
        <div key={i} className="bg-panel border border-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <Skeleton className="h-2.5 w-16" />
            <Skeleton className="w-4 h-4 rounded" />
          </div>
          <Skeleton className="h-7 w-12" />
        </div>
      ))}
    </div>
  )
}

// ─── Full page loader ─────────────────────────────────────────────────────────

export function PageLoader({ message = 'Loading…' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[400px] gap-4">
      <div className="relative">
        <div className="w-10 h-10 rounded-xl bg-accent/15 border border-accent/20 flex items-center justify-center">
          <div className="w-4 h-4 border-2 border-accent/40 border-t-accent rounded-full animate-spin" />
        </div>
      </div>
      <p className="text-sm text-text-muted font-mono">{message}</p>
    </div>
  )
}
