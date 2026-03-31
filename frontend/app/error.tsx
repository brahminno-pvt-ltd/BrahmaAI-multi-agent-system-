'use client'

import { useEffect } from 'react'
import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import Link from 'next/link'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('[BrahmaAI] Global error:', error)
  }, [error])

  return (
    <html>
      <body className="bg-void text-text-primary min-h-screen flex items-center justify-center p-6">
        <div className="max-w-md w-full text-center space-y-6 animate-fade-in">
          <div className="w-14 h-14 rounded-2xl bg-signal-red/10 border border-signal-red/20 flex items-center justify-center mx-auto">
            <AlertTriangle size={24} className="text-signal-red" />
          </div>

          <div>
            <h1 className="font-display font-bold text-2xl text-text-primary mb-2">
              Application Error
            </h1>
            <p className="text-sm text-text-secondary">
              BrahmaAI encountered an unexpected error. This is likely a transient issue.
            </p>
            {error.message && (
              <p className="mt-3 px-4 py-2 bg-surface border border-border rounded-lg text-xs text-text-muted font-mono text-left">
                {error.message}
              </p>
            )}
            {error.digest && (
              <p className="text-[10px] text-text-muted mt-2 font-mono">
                Error ID: {error.digest}
              </p>
            )}
          </div>

          <div className="flex items-center justify-center gap-3">
            <button
              onClick={reset}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-accent text-white text-sm font-medium hover:bg-accent/90 transition-colors shadow-lg shadow-accent/20"
            >
              <RefreshCw size={14} />
              Try Again
            </button>
            <Link
              href="/chat"
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-panel border border-border text-text-secondary text-sm hover:border-muted hover:text-text-primary transition-colors"
            >
              <Home size={14} />
              Go Home
            </Link>
          </div>
        </div>
      </body>
    </html>
  )
}
