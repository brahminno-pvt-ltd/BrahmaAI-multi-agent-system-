# BrahmaAI Architecture Deep Dive

## Overview

BrahmaAI implements an **OpenClaw-style autonomous agent loop** — a multi-step,
self-reflective execution pattern where the system plans, acts, observes, critiques,
and adapts until the goal is satisfactorily achieved.

---

## The Agent Loop

```
┌──────────────────────────────────────────────────────────────────────┐
│                         AGENT LOOP ITERATION                          │
│                                                                        │
│  USER GOAL ──► [1. Memory Retrieval] ──► [2. Planning]               │
│                                                   │                   │
│                              JSON Plan (steps[])  │                   │
│                                                   ▼                   │
│                              [3. Execute Step N] ──► TOOL CALL        │
│                                    │                      │           │
│                                    │ ◄─── result ─────────┘           │
│                                    │                                   │
│                              [4. Observe] ──► inject into context     │
│                                    │                                   │
│                              [5. Reflect] ──► quality_score           │
│                                    │                                   │
│                         score < 7? │ yes ──► [Re-plan] ──► loop       │
│                                    │ no                                │
│                                    ▼                                   │
│                              [6. Synthesize] ──► FINAL ANSWER         │
│                                                                        │
│                              [7. Store to Memory]                     │
└──────────────────────────────────────────────────────────────────────┘
```

### Why This Pattern?

Single-shot LLM calls fail on complex tasks because:
1. **Context limits** — can't hold an entire research session in one prompt
2. **No error recovery** — a wrong tool call silently fails
3. **No grounding** — pure LLM hallucination without real tool results
4. **No adaptation** — can't change approach mid-task

The agent loop solves all four: it breaks the task into tool-grounded steps,
retries on failure, and evaluates its own output quality.

---

## Component Responsibilities

### Orchestrator (`core/orchestrator.py`)

The central nervous system. It:
- Maintains `AgentState` across the full loop
- Coordinates all four agents in sequence
- Streams every event as SSE to the frontend
- Stores outcomes to long-term memory on completion
- Enforces `MAX_ITERATIONS` to prevent infinite loops

```python
async for event in orchestrator.run_task(goal, session_id):
    # Every event is yielded as it happens — real-time streaming
    print(event["event"], event["data"])
```

### Planner Agent (`agents/planner.py`)

Converts a natural language goal into a machine-executable JSON plan.

**Input:** Goal string + memory context + tool registry
**Output:**
```json
{
  "goal": "Research AI trends",
  "reasoning": "I'll search for recent news, scrape top articles, then synthesize",
  "steps": [
    {
      "id": "step_1",
      "description": "Search for recent AI developments",
      "tool": "web_search",
      "tool_args": {"query": "AI trends 2025", "num_results": 5},
      "depends_on": [],
      "expected_output": "List of relevant URLs and snippets"
    }
  ]
}
```

**Key design:** The planner reads the live tool registry, so adding a new tool
automatically makes it available for planning without changing any agent code.

### Executor Agent (`agents/executor.py`)

Runs each plan step by dispatching to the tool layer.

**Context injection:** Previous step results are automatically injected into
subsequent tool args. The `{prev_output}` placeholder in `tool_args` is replaced
with the previous step's output.

**LLM fallback:** Steps with `tool: null` are handled by the LLM directly —
useful for synthesis, reasoning, and formatting tasks.

**Retry logic:** Managed by the Orchestrator. Each step gets `MAX_RETRIES`
attempts before being marked as failed and execution continues.

### Critic Agent (`agents/critic.py`)

After all steps are executed, the Critic evaluates the aggregate result.

**Scoring rubric (enforced via prompt):**
| Score | Meaning |
|---|---|
| 9-10 | Excellent — comprehensive, accurate, complete |
| 7-8 | Good — adequate, minor gaps |
| 5-6 | Mediocre — important info missing |
| 1-4 | Poor — wrong approach or critical failures |

**Replan trigger:** Score < 7 sets `should_replan: true`, causing the Orchestrator
to run a second planning pass with a refined goal derived from the Critic's feedback.
Maximum one replan per task to prevent loops.

### Memory Agent (`agents/memory_agent.py`)

Provides a clean interface over both memory systems:

```python
# Store after task completion
await memory_agent.remember("Summary of what was accomplished", metadata)

# Retrieve before planning
context = await memory_agent.recall("user's goal", top_k=5)
```

---

## Memory Architecture

### Short-Term Memory

- **Implementation:** In-process Python dict keyed by `session_id`
- **Content:** Full message history per session
- **Limit:** `SHORT_TERM_MAX_MESSAGES` (default: 50), sliding window
- **Scope:** Single process lifetime (reset on restart)
- **Use case:** Conversation continuity within a session

### Long-Term Memory (FAISS)

- **Implementation:** Facebook FAISS `IndexFlatL2` (exact L2 search)
- **Embeddings:** OpenAI `text-embedding-3-small` (1536 dimensions)
- **Persistence:** Saved to disk as `.index` + `.meta.json` files
- **Fallback:** Keyword-based Jaccard similarity when no embedding API
- **Retrieval:** Cosine similarity via L2 distance conversion

**Storage flow:**
```
Text → OpenAI Embedding API → 1536-dim vector → FAISS.add()
                                               → metadata list append
                                               → faiss.write_index()
```

**Retrieval flow:**
```
Query → Embedding → FAISS.search(k=5) → indices + distances
      → metadata[indices] + similarity scores → return
```

---

## Tool Architecture

### BaseTool Interface

```python
class BaseTool:
    name: str           # Unique identifier used by agents
    description: str    # What the tool does (shown to Planner LLM)
    args: dict[str, str] # Argument name → description

    async def execute(self, **kwargs) -> dict[str, Any]:
        # Must return {"status": "success"|"error", "output": str, ...}
        raise NotImplementedError
```

### Tool Registry (Plugin System)

```python
registry = get_tool_registry()  # Singleton

# Register a new tool at runtime
registry.register(MyCustomTool())

# The Planner reads this on every invocation
tool_list = registry.list_tools()
# → {"web_search": {"name": ..., "description": ..., "args": ...}, ...}
```

**Key insight:** The Planner LLM receives the live registry on each call. This
means you never need to update prompt templates when adding tools — just register
the tool class and restart.

### Tool Return Contract

All tools must return:
```python
{
    "status": "success" | "error" | "blocked" | "timeout",
    "output": str,          # Human-readable result (injected into agent context)
    # ... tool-specific extra fields
}
```

---

## Streaming & Observability

### SSE Event Stream

The Orchestrator yields structured events throughout the loop:

```
data: {"event": "memory_retrieval", "timestamp": 1720000.0, "data": {"status": "retrieving"}}
data: {"event": "planning", "timestamp": 1720001.2, "data": {"status": "complete", "plan": {...}}}
data: {"event": "step_start", "timestamp": 1720001.5, "data": {"step": {...}}}
data: {"event": "execution", "timestamp": 1720001.6, "data": {"tool": "web_search", "attempt": 1}}
data: {"event": "step_result", "timestamp": 1720003.1, "data": {"step_id": "step_1", "result": {...}}}
data: {"event": "reflection", "timestamp": 1720004.0, "data": {"status": "complete", "reflection": {...}}}
data: {"event": "complete", "timestamp": 1720005.2, "data": {"final_answer": {...}, "elapsed_seconds": 4.2}}
data: [DONE]
```

### Frontend Consumption

```typescript
const res = await fetch('/api/chat/message', { method: 'POST', body: JSON.stringify({...}) })
const reader = res.body.getReader()

while (true) {
    const { done, value } = await reader.read()
    if (done) break
    const lines = decode(value).split('\n')
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const event = JSON.parse(line.slice(6))
            dispatch(event)  // Update Zustand store → UI re-renders
        }
    }
}
```

---

## LLM Client Abstraction

The `LLMClient` class provides a unified interface across providers:

```python
client = get_llm_client()  # Singleton

response = await client.complete(
    system="You are the Planner agent...",
    user="Goal: Research AI trends",
    json_mode=True,   # Forces JSON output (OpenAI response_format)
    temperature=0.1,  # Low temp for structured tasks
)

plan = client.parse_json(response)  # Handles markdown fences
```

**Provider switching:** Change `LLM_PROVIDER` in `.env` — no code changes needed.

**Demo mode:** When no API keys are configured, `_mock_response()` returns
realistic mock JSON that exercises the full agent loop without any API costs.
Ideal for UI development and testing.

---

## Security Model

| Layer | Mechanism |
|---|---|
| API auth | JWT tokens (HS256), 24h expiry |
| Code sandbox | Subprocess isolation + import blocking + timeout |
| File uploads | Extension allowlist + size limit + path traversal prevention |
| Rate limiting | In-memory sliding window (replace with Redis for multi-process) |
| CORS | Explicit origin allowlist in `ALLOWED_ORIGINS` |
| Request size | 10MB limit via `RequestSizeMiddleware` |
| Input validation | Pydantic models on all API endpoints |

---

## Extending BrahmaAI

### Add a Tool (5 minutes)
See `backend/tools/plugins/stock_tool.py` for a complete example.

### Add an Agent (15 minutes)
1. Create `backend/agents/my_agent.py` extending the base pattern
2. Add a method to `Orchestrator` that calls it
3. Emit appropriate SSE events

### Add a Memory Backend (30 minutes)
Implement the same `store()` / `retrieve()` interface as `LongTermMemory`.
Drop-in replacements: Pinecone, Weaviate, ChromaDB, Qdrant.

### Change the LLM (2 minutes)
Set `LLM_PROVIDER=anthropic` in `.env`. Or add a new provider to `llm_client.py`
following the `_openai_complete` / `_anthropic_complete` pattern.
