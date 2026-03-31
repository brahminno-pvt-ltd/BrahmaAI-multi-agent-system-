#!/usr/bin/env python3
"""
BrahmaAI Seed Script
Populates long-term memory with sample data and verifies the system is working.

Usage:
    python seed.py              # seed memories only
    python seed.py --full       # seed + run a demo task
    python seed.py --clear      # clear all memory first
"""

import asyncio
import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


SAMPLE_MEMORIES = [
    {
        "text": "User prefers concise, structured answers with bullet points for complex topics.",
        "metadata": {"source": "preference", "category": "communication_style"},
    },
    {
        "text": "User is a senior software engineer working primarily with Python and TypeScript.",
        "metadata": {"source": "profile", "category": "professional"},
    },
    {
        "text": "User is interested in AI/ML topics, autonomous agents, and LLM applications.",
        "metadata": {"source": "profile", "category": "interests"},
    },
    {
        "text": "Previous task: Researched RAG architectures. Key finding: FAISS outperforms ChromaDB for large-scale retrieval.",
        "metadata": {"source": "task_history", "task": "rag_research", "category": "technical"},
    },
    {
        "text": "Previous task: Generated a FastAPI CRUD application for a blog. User was satisfied with the result.",
        "metadata": {"source": "task_history", "task": "fastapi_blog", "category": "code"},
    },
    {
        "text": "User prefers dark themes in UI and minimal design aesthetics.",
        "metadata": {"source": "preference", "category": "ui"},
    },
    {
        "text": "Budget constraint context: User typically works with startup-level budgets (~$500-2000/month for AI APIs).",
        "metadata": {"source": "profile", "category": "budget"},
    },
    {
        "text": "User's timezone: UTC+5:30 (India Standard Time). Prefers meetings in the morning.",
        "metadata": {"source": "profile", "category": "schedule"},
    },
    {
        "text": "Technical stack preferences: FastAPI backend, Next.js frontend, PostgreSQL, Redis, Docker.",
        "metadata": {"source": "preference", "category": "tech_stack"},
    },
    {
        "text": "User has asked about multi-agent systems before. Was interested in OpenAI Assistants API and LangGraph.",
        "metadata": {"source": "task_history", "category": "ai_research"},
    },
]


async def seed_memories(clear: bool = False) -> None:
    from backend.memory.long_term import LongTermMemory

    mem = LongTermMemory()

    if clear:
        mem._fallback_store.clear()
        if hasattr(mem, '_embeddings'):
            mem._embeddings.clear()
        print("🗑  Cleared existing memories")

    print(f"\n📝 Seeding {len(SAMPLE_MEMORIES)} memories into long-term store...\n")

    for i, item in enumerate(SAMPLE_MEMORIES, 1):
        memory_id = await mem.store(
            text=item["text"],
            metadata=item["metadata"],
        )
        category = item["metadata"].get("category", "general")
        print(f"  [{i:2d}/{len(SAMPLE_MEMORIES)}] ✓ [{category}] {item['text'][:60]}...")
        await asyncio.sleep(0.05)  # Small delay to avoid rate limiting if using embeddings

    stored = await mem.list_recent(limit=100)
    print(f"\n✅ Memory store now has {len(stored)} entries")


async def verify_tools() -> None:
    from backend.tools.registry import get_tool_registry

    registry = get_tool_registry()
    tools = registry.list_tools()

    print(f"\n🔧 Verifying {len(tools)} registered tools...\n")

    for name, schema in tools.items():
        # Quick execute test
        tool = registry.get_tool(name)
        try:
            if name == "code_executor":
                result = await tool.execute(code="print('brahmaai ok')", timeout=5)
            elif name == "email_tool":
                result = await tool.execute(to="test@test.com", subject="Test", body="Seed test")
            elif name == "calendar_tool":
                result = await tool.execute(action="list")
            elif name == "web_search":
                result = tool._mock_search("test", 1)
            elif name == "web_scraper":
                result = {"status": "skip", "output": "skipped in seed"}
            elif name == "file_reader":
                result = {"status": "skip", "output": "skipped in seed"}
            else:
                result = {"status": "skip"}

            status = result.get("status", "unknown")
            icon = "✅" if status in ("success", "skip") else "⚠️"
            print(f"  {icon} {name:<20} → {status}")
        except Exception as e:
            print(f"  ❌ {name:<20} → ERROR: {e}")


async def run_demo_task() -> None:
    from backend.core.orchestrator import Orchestrator

    print("\n🚀 Running demo task: 'What is 2+2? Use the code executor to verify.'\n")

    orch = Orchestrator()
    last_event = None

    async for event in orch.run_task(
        goal="Use the code executor to calculate 2+2 and return the result",
        session_id="seed-demo",
    ):
        etype = event.get("event", "")
        data  = event.get("data", {})

        if etype == "planning" and data.get("status") == "complete":
            plan  = data.get("plan", {})
            steps = plan.get("steps", [])
            print(f"  📋 Plan: {len(steps)} step(s)")
            for s in steps:
                print(f"       • {s.get('id')}: {s.get('description')} [tool: {s.get('tool', 'none')}]")

        elif etype == "step_result":
            print(f"  ✅ Step {data.get('step_id')} completed")

        elif etype == "reflection" and data.get("status") == "complete":
            ref = data.get("reflection", {})
            print(f"  🔍 Critic score: {ref.get('quality_score')}/10")

        elif etype == "complete":
            elapsed = data.get("elapsed_seconds", 0)
            final   = data.get("final_answer", {})
            print(f"\n  ✨ Done in {elapsed}s")
            summary = (final.get("summary", "") or "")[:200]
            print(f"  Answer: {summary}")

        elif etype == "error":
            print(f"  ❌ Error: {data.get('error')}")

        last_event = event

    return last_event


async def main(args: argparse.Namespace) -> None:
    print("\n" + "═" * 50)
    print("  🧠 BrahmaAI Seed Script")
    print("═" * 50)

    t0 = time.time()

    await seed_memories(clear=args.clear)
    await verify_tools()

    if args.full:
        await run_demo_task()

    elapsed = round(time.time() - t0, 2)
    print(f"\n{'═' * 50}")
    print(f"  ✅ Seed complete in {elapsed}s")
    print(f"  Run: uvicorn backend.main:app --reload")
    print(f"  Docs: http://localhost:8000/api/docs")
    print("═" * 50 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BrahmaAI seed script")
    parser.add_argument("--full",  action="store_true", help="Also run a demo task")
    parser.add_argument("--clear", action="store_true", help="Clear memory before seeding")
    args = parser.parse_args()

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
