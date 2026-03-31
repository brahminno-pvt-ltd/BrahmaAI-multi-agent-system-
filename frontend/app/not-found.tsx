import Link from 'next/link'
import { Cpu, ArrowLeft } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-void flex flex-col items-center justify-center p-6 text-center">
      <div className="mb-6">
        <div className="w-12 h-12 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center mx-auto mb-4">
          <Cpu size={20} className="text-accent" />
        </div>
        <p className="font-mono text-6xl font-bold text-text-muted/20 mb-2">404</p>
        <h1 className="font-display font-bold text-2xl text-text-primary mb-2">
          Page not found
        </h1>
        <p className="text-sm text-text-secondary max-w-xs">
          The page you're looking for doesn't exist or has been moved.
        </p>
      </div>

      <Link
        href="/chat"
        className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-accent text-white text-sm font-medium hover:bg-accent/90 transition-colors"
      >
        <ArrowLeft size={14} />
        Back to Chat
      </Link>
    </div>
  )
}
