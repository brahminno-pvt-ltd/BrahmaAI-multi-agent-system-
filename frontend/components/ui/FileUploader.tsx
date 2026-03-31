'use client'

import { useState, useRef, useCallback } from 'react'
import { Upload, FileText, File, Loader2, CheckCircle2, X, AlertCircle } from 'lucide-react'
import { clsx } from 'clsx'
import { useBrahmaStore } from '@/lib/store'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const ALLOWED_TYPES: Record<string, { icon: typeof File; label: string }> = {
  '.pdf': { icon: FileText, label: 'PDF' },
  '.csv': { icon: FileText, label: 'CSV' },
  '.txt': { icon: FileText, label: 'Text' },
  '.md':  { icon: FileText, label: 'Markdown' },
  '.json': { icon: FileText, label: 'JSON' },
}

type UploadState = 'idle' | 'uploading' | 'success' | 'error'

interface UploadResult {
  filename: string
  file_path: string
  agent_prompt: string
  extraction: { output: string; char_count: number }
}

interface FileUploaderProps {
  onUploadComplete?: (result: UploadResult) => void
  onSendPrompt?: (prompt: string) => void
  compact?: boolean
}

export default function FileUploader({ onUploadComplete, onSendPrompt, compact = false }: FileUploaderProps) {
  const [state, setState] = useState<UploadState>('idle')
  const [dragOver, setDragOver] = useState(false)
  const [result, setResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { token } = useBrahmaStore()

  const uploadFile = useCallback(async (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_TYPES[ext]) {
      setError(`Unsupported file type: ${ext}. Allowed: ${Object.keys(ALLOWED_TYPES).join(', ')}`)
      setState('error')
      return
    }

    setState('uploading')
    setProgress(0)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      // Fake progress
      const progressInterval = setInterval(() => {
        setProgress(p => Math.min(p + 15, 85))
      }, 200)

      const res = await fetch(`${BASE_URL}/api/files/upload`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      })

      clearInterval(progressInterval)
      setProgress(100)

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
        throw new Error(err.detail || 'Upload failed')
      }

      const data = await res.json()
      setResult(data)
      setState('success')
      onUploadComplete?.(data)
    } catch (err: unknown) {
      setState('error')
      setError((err as Error)?.message || 'Upload failed')
    }
  }, [token, onUploadComplete])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) uploadFile(file)
  }, [uploadFile])

  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) uploadFile(file)
  }

  const reset = () => {
    setState('idle')
    setResult(null)
    setError(null)
    setProgress(0)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  if (compact && state === 'idle') {
    return (
      <button
        onClick={() => fileInputRef.current?.click()}
        className="p-1.5 rounded-lg text-text-muted hover:text-accent hover:bg-accent/10 transition-colors"
        title="Upload file (PDF, CSV, TXT)"
      >
        <Upload size={14} />
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.csv,.txt,.md,.json"
          className="hidden"
          onChange={handleInput}
        />
      </button>
    )
  }

  return (
    <div className="w-full space-y-3">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.csv,.txt,.md,.json"
        className="hidden"
        onChange={handleInput}
      />

      {/* Drop zone */}
      {state === 'idle' && (
        <div
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={clsx(
            'flex flex-col items-center justify-center gap-3 p-6 rounded-xl border-2 border-dashed',
            'cursor-pointer transition-all',
            dragOver
              ? 'border-accent/60 bg-accent/5'
              : 'border-border hover:border-accent/30 hover:bg-muted/10'
          )}
        >
          <div className="w-10 h-10 rounded-xl bg-muted/30 flex items-center justify-center">
            <Upload size={18} className={dragOver ? 'text-accent' : 'text-text-muted'} />
          </div>
          <div className="text-center">
            <p className="text-sm text-text-secondary font-medium">
              {dragOver ? 'Drop to upload' : 'Upload a file'}
            </p>
            <p className="text-xs text-text-muted mt-0.5">
              PDF, CSV, TXT, MD, JSON · Max 20MB
            </p>
          </div>
        </div>
      )}

      {/* Uploading */}
      {state === 'uploading' && (
        <div className="p-4 bg-panel border border-border rounded-xl space-y-3">
          <div className="flex items-center gap-3">
            <Loader2 size={16} className="animate-spin text-accent shrink-0" />
            <p className="text-sm text-text-secondary">Uploading and extracting…</p>
          </div>
          <div className="w-full h-1 bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-accent rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Success */}
      {state === 'success' && result && (
        <div className="bg-panel border border-signal-green/20 rounded-xl overflow-hidden">
          <div className="flex items-start gap-3 p-3.5">
            <CheckCircle2 size={15} className="text-signal-green shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-text-primary truncate">{result.filename}</p>
              <p className="text-[11px] text-text-muted mt-0.5">
                {result.extraction.char_count.toLocaleString()} characters extracted
              </p>
            </div>
            <button onClick={reset} className="text-text-muted hover:text-text-primary transition-colors">
              <X size={13} />
            </button>
          </div>
          {onSendPrompt && (
            <div className="px-3.5 pb-3">
              <button
                onClick={() => onSendPrompt(result.agent_prompt)}
                className="w-full px-3 py-2 bg-accent/10 border border-accent/20 text-accent text-xs rounded-lg hover:bg-accent/15 transition-colors font-medium"
              >
                Ask BrahmaAI to analyze this file →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {state === 'error' && (
        <div className="flex items-start gap-3 p-3.5 bg-signal-red/5 border border-signal-red/20 rounded-xl">
          <AlertCircle size={14} className="text-signal-red shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-xs font-medium text-signal-red">Upload failed</p>
            <p className="text-[11px] text-text-muted mt-0.5">{error}</p>
          </div>
          <button onClick={reset} className="text-text-muted hover:text-text-primary transition-colors">
            <X size={13} />
          </button>
        </div>
      )}
    </div>
  )
}
