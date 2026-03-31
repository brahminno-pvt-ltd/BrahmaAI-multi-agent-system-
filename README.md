# 🧠 BrahmaAI — Autonomous Multi-Agent AI Assistant

> A production-grade autonomous AI personal assistant built with multi-agent orchestration.  
> Plans. Executes. Reflects. Repeats.

![BrahmaAI Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-7c6dfa?style=flat-square)
![Python](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python%203.12-009688?style=flat-square)
![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014%20%2B%20TypeScript-000000?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🎯 What Is BrahmaAI?

BrahmaAI is **not a chatbot**. It's an autonomous multi-agent system that:

1. **Plans** your goal into structured, tool-grounded steps
2. **Executes** each step using real tools (web search, code runner, file reader, etc.)
3. **Observes** results and injects them as context for subsequent steps
4. **Reflects** on the quality of execution via a Critic agent
5. **Re-plans** if quality is insufficient
6. **Synthesizes** a final, comprehensive answer

Every reasoning step is logged, streamed in real-time, and inspectable in the UI.

---

## 📸 Features

| Feature | Description |
|---|---|
| 🤖 Multi-Agent Loop | Planner → Executor → Critic → Memory agent pipeline |
| 🛠 6 Real Tools | Web search, scraper, file reader, code sandbox, email, calendar |
| 🧠 Vector Memory | FAISS long-term memory + session short-term memory |
| 📡 Real-Time Streaming | SSE event stream shows agent reasoning live |
| 📊 Agent Log Viewer | Full observability of every plan, action, and tool call |
| 🔐 Auth | JWT-based authentication |
| 🐳 Docker | One-command full stack deployment |
| 🔌 Plugin System | Register custom tools via the ToolRegistry |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────┐
│                    USER GOAL                         │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │   ORCHESTRATOR   │  ◄── Central loop controller
              │  (core/orchestr) │
              └────────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
   │ PLANNER │   │ EXECUTOR  │  │ CRITIC  │
   │  Agent  │   │  Agent    │  │  Agent  │
   └────┬────┘   └─────┬─────┘  └────┬────┘
        │              │              │
        │    ┌─────────▼─────────┐    │
        │    │   TOOL LAYER      │    │
        │    │ • web_search      │    │
        │    │ • web_scraper     │    │
        │    │ • file_reader     │    │
        │    │ • code_executor   │    │
        │    │ • email_tool      │    │
        │    │ • calendar_tool   │    │
        │    └───────────────────┘    │
        │                             │
   ┌────▼─────────────────────────────▼────┐
   │           MEMORY SYSTEM                │
   │  Short-term (session)  Long-term FAISS │
   └────────────────────────────────────────┘
```

### Agent Loop

```
Goal → [Memory Retrieval] → Plan → Execute(step_1) → Execute(step_2)
     → ... → Execute(step_n) → Reflect → [Re-plan?] → Synthesize → Answer
```

---

## 📂 Project Structure

```
brahmaai/
├── backend/
│   ├── agents/
│   │   ├── planner.py          # Goal → JSON plan
│   │   ├── executor.py         # Plan step execution + synthesis
│   │   ├── critic.py           # Quality reflection + replan trigger
│   │   └── memory_agent.py     # Memory store/retrieve wrapper
│   ├── core/
│   │   ├── orchestrator.py     # Central agent loop (streaming)
│   │   ├── state.py            # Pydantic state models
│   │   └── llm_client.py       # OpenAI/Anthropic abstraction
│   ├── memory/
│   │   ├── short_term.py       # In-memory session store
│   │   └── long_term.py        # FAISS vector store
│   ├── tools/
│   │   ├── registry.py         # Plugin-style tool registry
│   │   ├── web_search.py       # SerpAPI + DuckDuckGo fallback
│   │   ├── web_scraper.py      # URL content extraction
│   │   ├── file_reader.py      # PDF, CSV, TXT reader
│   │   ├── code_executor.py    # Sandboxed Python execution
│   │   ├── email_tool.py       # Email simulation
│   │   └── calendar_tool.py    # Calendar scheduling mock
│   ├── api/
│   │   └── routes/
│   │       ├── chat.py         # SSE streaming chat endpoint
│   │       ├── tasks.py        # Task planning endpoint
│   │       ├── memory.py       # Memory CRUD
│   │       ├── tools.py        # Tool listing + direct execution
│   │       └── auth.py         # JWT auth
│   ├── config/
│   │   └── settings.py         # Pydantic settings
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Redirect to /chat
│   │   ├── chat/page.tsx       # Chat page
│   │   ├── dashboard/page.tsx  # Dashboard page
│   │   ├── logs/page.tsx       # Agent logs page
│   │   └── memory/page.tsx     # Memory viewer page
│   ├── components/
│   │   ├── layout/
│   │   │   └── AppShell.tsx    # Sidebar + nav shell
│   │   └── agents/
│   │       ├── ChatInterface.tsx     # Main chat UI
│   │       ├── AgentEventStream.tsx  # Live event log
│   │       ├── DashboardView.tsx     # System dashboard
│   │       ├── LogsView.tsx          # Full log inspector
│   │       └── MemoryView.tsx        # Memory manager
│   ├── lib/
│   │   ├── store.ts            # Zustand global store
│   │   └── api.ts              # Typed API client
│   ├── package.json
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- At least one LLM API key: [OpenAI](https://platform.openai.com) or [Anthropic](https://console.anthropic.com)

### 1. Clone and configure

```bash
git clone https://github.com/yourname/brahmaai.git
cd brahmaai

# Copy and fill in your API keys
cp .env.example .env
nano .env  # or vim, code, etc.
```

**Required in `.env`:**
```env
LLM_PROVIDER=openai          # or anthropic
OPENAI_API_KEY=sk-...        # if using OpenAI
ANTHROPIC_API_KEY=sk-ant-... # if using Anthropic
```

### 2. Run the backend

```bash
cd backend

# Create virtualenv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn backend.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/api/docs

### 3. Run the frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy env
cp .env.local.example .env.local

# Start dev server
npm run dev
```

Open: http://localhost:3000

---

## 🐳 Docker (Full Stack)

```bash
# From project root
cp .env.example .env
# Fill in your API keys in .env

docker-compose up --build
```

- Frontend: http://localhost:3000  
- Backend API: http://localhost:8000  
- API Docs: http://localhost:8000/api/docs

---

## 🔑 Authentication

Default demo credentials:

| Username | Password |
|----------|----------|
| `admin`  | `brahmaai123` |
| `demo`   | `demo` |

> Change these in `backend/api/routes/auth.py` for production. Replace with a database-backed user system.

---

## 🧪 Demo Tasks

Try these in the Chat interface:

```
1. "Search for the latest AI trends in 2025 and create a structured report"

2. "Generate a complete Python FastAPI application for a todo app with CRUD 
    endpoints and explain each part"

3. "Plan a detailed 5-day trip to Tokyo with a $2000 budget including hotels, 
    food, and must-see activities"

4. "Create a weekly productivity schedule with time blocks for deep work, 
    meetings, and exercise"
```

Watch the **Agent Logs** panel on the right side of the chat to see every planning step, tool call, and reflection in real time.

---

## 🔌 Adding Custom Tools

BrahmaAI has a plugin-style tool registry. Add a new tool in 3 steps:

**1. Create the tool class:**

```python
# backend/tools/my_tool.py
from backend.tools.registry import BaseTool
from typing import Any

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"
    args = {
        "input": "str: The input to process",
    }

    async def execute(self, input: str, **kwargs: Any) -> dict[str, Any]:
        result = do_something(input)
        return {
            "status": "success",
            "output": result,
        }
```

**2. Register it:**

```python
# In backend/tools/registry.py, add to _register_default_tools():
from backend.tools.my_tool import MyTool
registry.register_class(MyTool)
```

**3. The Planner agent will automatically know about it** — it reads all registered tools and their descriptions when generating plans.

---

## ⚙️ Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `openai` | `openai` or `anthropic` |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model name |
| `ANTHROPIC_MODEL` | `claude-3-5-sonnet-20241022` | Anthropic model |
| `MAX_ITERATIONS` | `10` | Max agent loop iterations |
| `MAX_RETRIES` | `3` | Retries per failed step |
| `SERPAPI_KEY` | `` | SerpAPI key (optional) |
| `FAISS_INDEX_PATH` | `./data/faiss_index` | Vector store path |
| `SHORT_TERM_MAX_MESSAGES` | `50` | Session history limit |

---

## 🧠 Memory System

### Short-Term Memory
- Per-session conversation history
- In-memory sliding window (50 messages)
- Automatically injected into agent context

### Long-Term Memory (FAISS)
- Semantic vector store using OpenAI `text-embedding-3-small`
- Stores task summaries and key insights after every completed task
- Retrieved via cosine similarity search before each planning phase
- Falls back to keyword matching when no embedding API is available

---

## 📊 Observability

Every agent event is structured and streamed:

```json
{
  "event": "planning",
  "timestamp": 1720000000.123,
  "data": {
    "status": "complete",
    "plan": {
      "goal": "Search AI trends",
      "steps": [...],
      "reasoning": "..."
    }
  }
}
```

Event types: `memory_retrieval`, `planning`, `step_start`, `execution`, `step_result`, `step_error`, `reflection`, `replanning`, `synthesis`, `complete`, `error`, `warning`

View all events in real-time in the **Agent Logs** tab, or inline below any chat message.

---

## 🗺 Roadmap

- [ ] Persistent task history with SQLite/PostgreSQL
- [ ] Multi-user support with proper DB-backed auth  
- [ ] Parallel step execution (async DAG)
- [ ] Tool marketplace / community plugins
- [ ] Voice interface
- [ ] Mobile app (React Native)
- [ ] Self-hosted LLM support (Ollama)
- [ ] Agent-to-agent communication

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-tool`
3. Commit your changes: `git commit -m 'feat: add my tool'`
4. Push and open a PR

---

## 📄 License

MIT © BrahmaAI Contributors

---

<p align="center">
  Built with ❤️ as a demonstration of production-grade autonomous AI systems.<br/>
  <strong>BrahmaAI</strong> — Where goals become actions.
</p>
