"""
BrahmaAI Core Orchestrator
Central agent loop: Goal → Plan → Execute → Observe → Reflect → Repeat
"""

import asyncio
import logging
import time
import uuid
from typing import Any, AsyncGenerator

from backend.agents.planner import PlannerAgent
from backend.agents.executor import ExecutorAgent
from backend.agents.critic import CriticAgent
from backend.agents.memory_agent import MemoryAgent
from backend.core.state import AgentState, StepStatus, TaskStatus
from backend.memory.short_term import ShortTermMemory
from backend.memory.long_term import LongTermMemory
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Central orchestrator that manages the full agent loop.
    Coordinates Planner → Executor → Critic agents across iterations.
    """

    def __init__(self):
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.critic = CriticAgent()
        self.memory_agent = MemoryAgent()
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()

    async def run_task(
        self,
        goal: str,
        session_id: str | None = None,
        stream: bool = False,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Execute a full agent loop for a given goal.
        Yields structured log events for real-time streaming.
        """
        task_id = str(uuid.uuid4())
        session_id = session_id or str(uuid.uuid4())
        start_time = time.time()

        state = AgentState(
            task_id=task_id,
            session_id=session_id,
            goal=goal,
            status=TaskStatus.RUNNING,
        )

        logger.info(f"[{task_id}] Starting task: {goal[:80]}...")

        # --- Retrieve long-term memory context ---
        yield self._event("memory_retrieval", {"status": "retrieving", "goal": goal})
        memory_context = await self.long_term.retrieve(goal, top_k=5)
        session_context = self.short_term.get_context(session_id)
        state.memory_context = memory_context
        yield self._event("memory_retrieval", {
            "status": "done",
            "retrieved": len(memory_context),
            "session_messages": len(session_context),
        })

        # --- Planning phase ---
        yield self._event("planning", {"status": "start"})
        try:
            plan = await self.planner.plan(
                goal=goal,
                memory_context=memory_context,
                session_context=session_context,
            )
            state.plan = plan
            yield self._event("planning", {"status": "complete", "plan": plan})
        except Exception as e:
            yield self._event("error", {"phase": "planning", "error": str(e)})
            state.status = TaskStatus.FAILED
            return

        # --- Execution loop ---
        max_iterations = settings.MAX_ITERATIONS
        iteration = 0
        all_results: list[dict] = []

        for step in plan["steps"]:
            if iteration >= max_iterations:
                yield self._event("warning", {"msg": "Max iterations reached", "iteration": iteration})
                break

            step_id = step["id"]
            state.current_step = step_id
            yield self._event("step_start", {"step": step})

            # Execute step with retries
            step_result = None
            for attempt in range(settings.MAX_RETRIES):
                try:
                    yield self._event("execution", {
                        "step_id": step_id,
                        "attempt": attempt + 1,
                        "tool": step.get("tool"),
                    })
                    step_result = await self.executor.execute_step(
                        step=step,
                        context=all_results,
                        memory_context=memory_context,
                    )
                    state.step_results[step_id] = step_result
                    yield self._event("step_result", {
                        "step_id": step_id,
                        "result": step_result,
                        "status": "success",
                    })
                    break
                except Exception as e:
                    logger.warning(f"[{task_id}] Step {step_id} attempt {attempt+1} failed: {e}")
                    yield self._event("step_error", {
                        "step_id": step_id,
                        "attempt": attempt + 1,
                        "error": str(e),
                    })
                    if attempt == settings.MAX_RETRIES - 1:
                        step_result = {"error": str(e), "status": "failed"}
                        state.step_results[step_id] = step_result

            if step_result:
                all_results.append({"step": step, "result": step_result})

            iteration += 1

        # --- Reflection phase ---
        yield self._event("reflection", {"status": "start"})
        try:
            reflection = await self.critic.reflect(
                goal=goal,
                plan=plan,
                results=all_results,
            )
            state.reflection = reflection
            yield self._event("reflection", {"status": "complete", "reflection": reflection})

            # If critic recommends re-planning, do one more pass
            if reflection.get("should_replan") and iteration < max_iterations:
                yield self._event("replanning", {"reason": reflection.get("reason")})
                new_goal = reflection.get("revised_goal", goal)
                replan = await self.planner.plan(
                    goal=new_goal,
                    memory_context=memory_context,
                    session_context=session_context + all_results,
                )
                yield self._event("replanning_complete", {"new_plan": replan})

        except Exception as e:
            yield self._event("error", {"phase": "reflection", "error": str(e)})

        # --- Final synthesis ---
        yield self._event("synthesis", {"status": "start"})
        try:
            final_answer = await self.executor.synthesize(
                goal=goal,
                results=all_results,
                reflection=state.reflection or {},
            )
            state.final_answer = final_answer
            state.status = TaskStatus.COMPLETE

            # Store in memory
            await self.long_term.store(
                text=f"Goal: {goal}\nAnswer: {final_answer.get('summary', '')}",
                metadata={"task_id": task_id, "goal": goal},
            )
            self.short_term.add_message(
                session_id=session_id,
                role="assistant",
                content=final_answer.get("summary", ""),
            )

            elapsed = round(time.time() - start_time, 2)
            yield self._event("complete", {
                "task_id": task_id,
                "final_answer": final_answer,
                "elapsed_seconds": elapsed,
                "iterations": iteration,
            })
        except Exception as e:
            yield self._event("error", {"phase": "synthesis", "error": str(e)})
            state.status = TaskStatus.FAILED

    def _event(self, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """Construct a structured log event."""
        return {
            "event": event_type,
            "timestamp": time.time(),
            "data": data,
        }
