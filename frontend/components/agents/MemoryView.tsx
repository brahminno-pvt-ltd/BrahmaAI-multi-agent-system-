'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Database, Search, Trash2, Plus, RefreshCw,
  Clock, Tag, X, Loader2, BookOpen
} from 'lucide-react'
import { clsx } from 'clsx'
import { memoryApi } from '@/lib/api'
import { useBrahmaStore, type MemoryItem } from '@/lib/store'
import { formatDistanceToNow } from 'date-fns'

export default function MemoryView() {
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<MemoryItem[] | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newText, setNewText] = useState('')
  const [newMeta, setNewMeta] = useState('')
  const [adding, setAdding] = useState(false)
  const [deleting, setDeleting] = useState<string | null>(null)

  const { memories, setMemories, addMemory, removeMemory, token } = useBrahmaStore()

  const loadMemories = useCallback(async () => {
    setLoading(true)
    try {
      const res = await memoryApi.list(50, token)
      setMemories(res.memories as MemoryItem[])
    } catch (e) {
      console.error('Failed to load memories', e)
    } finally {
      setLoading(false)
    }
  }, [token, setMemories])

  useEffect(() => { loadMemories() }, [loadMemories])

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null)
      return
    }
    setLoading(true)
    try {
      const res = await memoryApi.retrieve(searchQuery, 10, token)
      setSearchResults(res.results as MemoryItem[])
    } catch (e) {
      console.error('Search failed', e)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    setDeleting(id)
    try {
      await memoryApi.delete(id, token)
      removeMemory(id)
      if (searchResults) {
        setSearchResults(r => r?.filter(m => m.id !== id) || null)
      }
    } catch (e) {
      console.error('Delete failed', e)
    } finally {
      setDeleting(null)
    }
  }

  const handleAdd = async () => {
    if (!newText.trim()) return
    setAdding(true)
    try {
      let metadata: Record<string, string> = {}
      try { metadata = JSON.parse(newMeta || '{}') } catch {}
      const res = await memoryApi.store(newText, metadata, token)
      const newMemory: MemoryItem = {
        id: (res as Record<string, string>).memory_id,
        text: newText,
        metadata,
        created_at: Date.now() / 1000,
      }
      addMemory(newMemory)
      setNewText('')
      setNewMeta('')
      setShowAddForm(false)
    } catch (e) {
      console.error('Store failed', e)
    } finally {
      setAdding(false)
    }
  }

  const displayedMemories = searchResults ?? memories

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border bg-surface shrink-0">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Database size={18} className="text-signal-blue" />
            <div>
              <h1 className="font-display font-bold text-lg text-text-primary">Memory Store</h1>
              <p className="text-xs text-text-muted">
                {memories.length} long-term memories · FAISS vector store
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadMemories}
              className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-muted/30 transition-colors"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
            <button
              onClick={() => setShowAddForm(s => !s)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent/15 text-accent border border-accent/20 text-xs font-medium hover:bg-accent/25 transition-colors"
            >
              <Plus size={13} />
              Add Memory
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="Semantic search memories…"
              className="w-full pl-8 pr-3 py-1.5 bg-panel border border-border rounded-lg text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/40 transition-colors"
            />
          </div>
          <button
            onClick={handleSearch}
            className="px-3 py-1.5 bg-panel border border-border rounded-lg text-xs text-text-secondary hover:border-accent/40 hover:text-accent transition-colors"
          >
            Search
          </button>
          {searchResults && (
            <button
              onClick={() => { setSearchResults(null); setSearchQuery('') }}
              className="p-1.5 text-text-muted hover:text-text-primary transition-colors"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Add form */}
        {showAddForm && (
          <div className="mt-3 p-3 bg-panel border border-accent/20 rounded-xl space-y-2 animate-fade-in">
            <textarea
              value={newText}
              onChange={e => setNewText(e.target.value)}
              placeholder="Memory content…"
              rows={3}
              className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/40 resize-none"
            />
            <input
              type="text"
              value={newMeta}
              onChange={e => setNewMeta(e.target.value)}
              placeholder='Metadata JSON (optional) e.g. {"source": "user"}'
              className="w-full px-3 py-1.5 bg-surface border border-border rounded-lg text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent/40"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowAddForm(false)}
                className="px-3 py-1.5 text-xs text-text-muted hover:text-text-primary transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAdd}
                disabled={adding || !newText.trim()}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-accent text-white text-xs rounded-lg font-medium hover:bg-accent/90 disabled:opacity-50 transition-colors"
              >
                {adding ? <Loader2 size={12} className="animate-spin" /> : <Plus size={12} />}
                Store
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Memory list */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {loading && memories.length === 0 && (
          <div className="flex items-center justify-center h-40">
            <Loader2 size={20} className="animate-spin text-text-muted" />
          </div>
        )}

        {!loading && displayedMemories.length === 0 && (
          <div className="flex flex-col items-center justify-center h-64 text-text-muted gap-3">
            <BookOpen size={32} className="opacity-20" />
            <div className="text-center">
              <p className="text-sm font-medium">
                {searchResults !== null ? 'No matching memories' : 'No memories yet'}
              </p>
              <p className="text-xs mt-1">
                {searchResults !== null
                  ? 'Try a different search query'
                  : 'Start chatting — BrahmaAI will store insights automatically'}
              </p>
            </div>
          </div>
        )}

        {searchResults !== null && (
          <div className="flex items-center gap-2 mb-3">
            <Search size={12} className="text-signal-blue" />
            <span className="text-xs text-text-muted">
              {searchResults.length} results for <span className="text-text-primary">"{searchQuery}"</span>
            </span>
          </div>
        )}

        <div className="space-y-2">
          {displayedMemories.map((memory) => (
            <MemoryCard
              key={memory.id}
              memory={memory}
              onDelete={handleDelete}
              deleting={deleting === memory.id}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function MemoryCard({
  memory, onDelete, deleting
}: {
  memory: MemoryItem
  onDelete: (id: string) => void
  deleting: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const metaKeys = Object.keys(memory.metadata || {})
  const timeAgo = memory.created_at
    ? formatDistanceToNow(new Date(memory.created_at * 1000), { addSuffix: true })
    : 'unknown'

  return (
    <div className={clsx(
      'group bg-panel border rounded-xl p-3.5 hover:border-muted transition-all',
      memory.score !== undefined ? 'border-signal-blue/20' : 'border-border'
    )}>
      <div className="flex items-start gap-3">
        <div className="w-6 h-6 rounded-md bg-signal-blue/10 flex items-center justify-center shrink-0 mt-0.5">
          <Database size={11} className="text-signal-blue" />
        </div>
        <div className="flex-1 min-w-0">
          <p className={clsx(
            'text-xs text-text-secondary leading-relaxed',
            !expanded && 'line-clamp-3'
          )}>
            {memory.text}
          </p>
          {memory.text.length > 200 && (
            <button
              onClick={() => setExpanded(e => !e)}
              className="text-[10px] text-accent hover:underline mt-1"
            >
              {expanded ? 'Show less' : 'Show more'}
            </button>
          )}

          <div className="flex items-center gap-3 mt-2 flex-wrap">
            <span className="flex items-center gap-1 text-[10px] text-text-muted">
              <Clock size={9} />
              {timeAgo}
            </span>
            {memory.score !== undefined && (
              <span className="flex items-center gap-1 text-[10px] text-signal-blue font-mono">
                relevance: {(memory.score * 100).toFixed(0)}%
              </span>
            )}
            {metaKeys.length > 0 && (
              <div className="flex items-center gap-1 flex-wrap">
                <Tag size={9} className="text-text-muted" />
                {metaKeys.map(k => (
                  <span key={k} className="px-1.5 py-0.5 bg-muted/30 rounded text-[10px] text-text-muted font-mono">
                    {k}: {String(memory.metadata[k]).slice(0, 20)}
                  </span>
                ))}
              </div>
            )}
            <span className="text-[9px] text-text-muted/50 font-mono ml-auto">
              {memory.id?.slice(0, 8)}
            </span>
          </div>
        </div>
        <button
          onClick={() => onDelete(memory.id)}
          disabled={deleting}
          className="shrink-0 p-1.5 rounded-lg text-text-muted hover:text-signal-red hover:bg-signal-red/10 opacity-0 group-hover:opacity-100 transition-all disabled:opacity-50"
        >
          {deleting ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
        </button>
      </div>
    </div>
  )
}
