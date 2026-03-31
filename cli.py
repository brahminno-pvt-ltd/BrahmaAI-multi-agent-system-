#!/usr/bin/env python3
"""
BrahmaAI CLI
Run the agent loop directly from the terminal without the web UI.

Usage:
    python cli.py "Search for AI trends and summarize"
    python cli.py "Generate a Python FastAPI app" --session my-session
    python cli.py "Plan a trip to Tokyo" --verbose
"""

import argparse
import asyncio
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


COLORS = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "dim":     "\033[2m",
    "cyan":    "\033[36m",
    "green":   "\033[32m",
    "yellow":  "\033[33m",
    "red":     "\033[31m",
    "blue":    "\033[34m",
    "magenta": "\033[35m",
    "white":   "\033[97m",
}

EVENT_COLORS = {
    "planning":         "cyan",
    "execution":        "yellow",
    "step_start":       "dim",
    "step_result":      "green",
    "step_error":       "red",
    "reflection":       "magenta",
    "memory_retrieval": "blue",
    "synthesis":        "green",
    "complete":         "green",
    "error":            "red",
    "warning":          "yellow",
}


def colorize(text: str, color: str) -> str:
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


def fmt_event(event: dict, verbose: bool) -> str | None:
    etype = event.get("event", "")
    data = event.get("data", {})
    color = EVENT_COLORS.get(etype, "white")

    prefix = colorize(f"[{etype:>20}]", color)

    match etype:
        case "memory_retrieval":
            if data.get("status") == "done":
                return f"{prefix} Retrieved {data.get('retrieved', 0)} memories"
            return f"{prefix} Searching long-term memory…"

        case "planning":
            if data.get("status") == "complete":
                plan = data.get("plan", {})
                steps = plan.get("steps", [])
                msg = f"{prefix} Plan: {len(steps)} steps"
                if verbose:
                    for s in steps:
                        tool = f" [{s.get('tool', 'reasoning')}]" if s.get("tool") else ""
                        msg += f"\n{'':>24}  • {s.get('id')}: {s.get('description')}{tool}"
                return msg
            return f"{prefix} Generating execution plan…"

        case "step_start":
            step = data.get("step", {})
            tool = f" → {step.get('tool', 'reasoning')}" if step.get("tool") else ""
            return f"{prefix} {step.get('id', '?')}: {step.get('description', '')[:70]}{tool}"

        case "execution":
            return f"{prefix} Running tool: {data.get('tool', 'reasoning')} (attempt {data.get('attempt', 1)})"

        case "step_result":
            return f"{prefix} {data.get('step_id')} ✓ completed"

        case "step_error":
            return f"{prefix} {data.get('step_id')} ✗ {str(data.get('error', ''))[:80]}"

        case "reflection":
            if data.get("status") == "complete":
                ref = data.get("reflection", {})
                score = ref.get("quality_score", "?")
                replan = ref.get("should_replan", False)
                bar = "█" * int(score) + "░" * (10 - int(score)) if isinstance(score, int) else ""
                return f"{prefix} Score: {score}/10 {bar} | replan: {replan}"
            return f"{prefix} Evaluating quality…"

        case "synthesis":
            return f"{prefix} Synthesizing final answer…"

        case "complete":
            elapsed = data.get("elapsed_seconds", 0)
            iters = data.get("iterations", 0)
            return (
                f"\n{colorize('━' * 60, 'cyan')}\n"
                f"{colorize('✅ COMPLETE', 'green')} in {elapsed}s · {iters} iterations\n"
                f"{colorize('━' * 60, 'cyan')}"
            )

        case "error":
            return f"{prefix} {data.get('phase', '?')}: {str(data.get('error', ''))[:100]}"

        case "replanning":
            return f"{prefix} Re-planning: {data.get('reason', '')[:80]}"

        case _:
            if verbose:
                return f"{prefix} {json.dumps(data)[:120]}"
            return None


async def run_cli(goal: str, session_id: str, verbose: bool):
    from backend.core.orchestrator import Orchestrator

    print(f"\n{colorize('BrahmaAI', 'cyan')} {colorize('━', 'dim')} Autonomous Agent Loop")
    print(colorize(f"Goal: {goal}", "white"))
    print(colorize("─" * 60, "dim"))
    print()

    orchestrator = Orchestrator()
    final_answer = None

    async for event in orchestrator.run_task(goal=goal, session_id=session_id):
        line = fmt_event(event, verbose)
        if line:
            print(line)

        if event.get("event") == "complete":
            final_answer = event.get("data", {}).get("final_answer", {})

    if final_answer:
        print(f"\n{colorize('FINAL ANSWER', 'bold')}\n")
        summary = final_answer.get("summary", "No summary available.")
        print(summary)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="BrahmaAI CLI — Run the autonomous agent loop from the terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "Search for AI trends in 2025 and create a report"
  python cli.py "Generate a Python FastAPI todo app" --verbose
  python cli.py "Plan a 5-day Tokyo trip with $2000 budget" --session tokyo-trip
        """
    )
    parser.add_argument("goal", help="The goal or task for BrahmaAI to execute")
    parser.add_argument("--session", default="cli-session", help="Session ID (default: cli-session)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all event details")
    args = parser.parse_args()

    try:
        asyncio.run(run_cli(
            goal=args.goal,
            session_id=args.session,
            verbose=args.verbose,
        ))
    except KeyboardInterrupt:
        print(f"\n{colorize('Interrupted.', 'yellow')}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{colorize(f'Error: {e}', 'red')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
