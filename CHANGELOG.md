# Changelog

All notable changes to BrahmaAI are documented here.
Format: [Semantic Versioning](https://semver.org/)

---

## [1.0.0] - 2025-01-01

### Added
- **Multi-agent orchestration loop**: Goal → Plan → Execute → Observe → Reflect → Repeat
- **Planner Agent**: LLM-powered goal decomposition into structured JSON plans
- **Executor Agent**: Tool-dispatching step runner with context injection and retry logic
- **Critic Agent**: Quality scoring (1–10) with automatic replan trigger
- **Memory Agent**: Unified interface over short-term and long-term memory
- **Short-term memory**: Per-session sliding window message history
- **Long-term memory**: FAISS vector store with OpenAI embeddings + keyword fallback
- **Tool Registry**: Plugin-style dynamic tool registration system
- **6 built-in tools**:
  - `web_search` — SerpAPI + DuckDuckGo fallback
  - `web_scraper` — BeautifulSoup HTML extraction
  - `file_reader` — PDF (pypdf), CSV, TXT, MD, JSON
  - `code_executor` — Sandboxed Python subprocess with import blocking
  - `email_tool` — Email simulation with persistent log
  - `calendar_tool` — Calendar scheduling mock with CRUD
- **FastAPI backend** with async architecture
- **SSE streaming** — real-time event stream from agent loop to frontend
- **Next.js 14 frontend** with App Router
- **Chat Interface** — streaming message bubbles with thinking indicators
- **Agent Log Viewer** — live event stream with filtering, search, and JSON inspection
- **Memory Viewer** — semantic search, add, delete with relevance scores
- **Mission Control Dashboard** — system stats, tool registry, demo task launcher
- **Settings page** — full environment variable reference with copy-to-clipboard
- **JWT authentication** — basic login with demo accounts
- **File upload API** — PDF/CSV/TXT ingestion with automatic text extraction
- **Error boundaries** — React error boundary + global Next.js error page
- **Loading states** — skeleton loaders for all async operations
- **Toast notifications** — success/error/warning feedback system
- **CLI runner** — `python cli.py "goal"` terminal interface with colored output
- **Seed script** — `python seed.py` populates sample memories
- **Docker Compose** — one-command full stack deployment
- **GitHub Actions CI** — pytest + tsc + docker build pipeline
- **Makefile** — 15 developer convenience commands
- **Plugin examples** — Stock price tool, Weather tool
- **40+ backend tests** — tools, agents, memory, API endpoints, orchestrator
- **Deployment guide** — Nginx + systemd + SSL + UFW for production VPS
- **Architecture docs** — deep dive into agent loop, memory, streaming, security

### Notes
- Demo mode works without any API keys (mock LLM responses)
- FAISS falls back to keyword search without OpenAI embedding key
- Web search falls back to DuckDuckGo without SerpAPI key
