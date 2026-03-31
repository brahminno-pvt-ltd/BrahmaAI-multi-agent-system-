'use client'

import { Component, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Bug } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, info: { componentStack: string }) => void
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: string
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: '' }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: '' }
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    this.setState({ errorInfo: info.componentStack })
    this.props.onError?.(error, info)
    console.error('[BrahmaAI ErrorBoundary]', error, info)
  }

  reset = () => {
    this.setState({ hasError: false, error: null, errorInfo: '' })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="flex flex-col items-center justify-center min-h-[300px] p-8 text-center">
          <div className="w-12 h-12 rounded-2xl bg-signal-red/10 border border-signal-red/20 flex items-center justify-center mb-4">
            <AlertTriangle size={20} className="text-signal-red" />
          </div>

          <h2 className="font-display font-bold text-lg text-text-primary mb-2">
            Something went wrong
          </h2>
          <p className="text-sm text-text-secondary mb-1 max-w-sm">
            {this.state.error?.message || 'An unexpected error occurred in this component.'}
          </p>

          <div className="flex items-center gap-3 mt-4">
            <button
              onClick={this.reset}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent/15 text-accent border border-accent/20 text-sm hover:bg-accent/25 transition-colors"
            >
              <RefreshCw size={13} />
              Try Again
            </button>
            <button
              onClick={() => window.location.reload()}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-muted/30 text-text-secondary text-sm hover:bg-muted/50 transition-colors"
            >
              Reload Page
            </button>
          </div>

          {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
            <details className="mt-6 text-left w-full max-w-2xl">
              <summary className="flex items-center gap-2 text-xs text-text-muted cursor-pointer hover:text-text-secondary">
                <Bug size={11} />
                Stack trace (dev only)
              </summary>
              <pre className="mt-2 p-3 bg-surface border border-border rounded-lg text-[10px] font-mono text-text-muted overflow-x-auto leading-relaxed">
                {this.state.error?.stack}
                {this.state.errorInfo}
              </pre>
            </details>
          )}
        </div>
      )
    }

    return this.props.children
  }
}

// ─── Inline error card (for non-boundary errors) ──────────────────────────────

export function ErrorCard({
  title = 'Something went wrong',
  message,
  onRetry,
}: {
  title?: string
  message?: string
  onRetry?: () => void
}) {
  return (
    <div className="flex items-start gap-3 p-4 bg-signal-red/5 border border-signal-red/20 rounded-xl">
      <AlertTriangle size={15} className="text-signal-red shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-signal-red">{title}</p>
        {message && (
          <p className="text-xs text-text-muted mt-0.5 leading-relaxed">{message}</p>
        )}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="shrink-0 p-1.5 rounded-lg text-signal-red/60 hover:text-signal-red hover:bg-signal-red/10 transition-colors"
        >
          <RefreshCw size={13} />
        </button>
      )}
    </div>
  )
}
