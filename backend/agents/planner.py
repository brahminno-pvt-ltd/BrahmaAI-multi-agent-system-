"""
BrahmaAI Planner Agent
Decomposes a high-level goal into a structured, executable step-by-step plan.
"""

import logging
from typing import Any

from backend.core.llm_client import get_llm_client
from backend.tools.registry import get_tool_registry

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are the Planner Agent for BrahmaAI, an autonomous AI assistant.

Your role is to decompose a user's goal into a precise, executable plan.

You have access to these tools:
{tool_descriptions}

RULES:
1. Break the goal into 2-6 concrete, actionable steps
2. Each step must specify which tool to use (if any)
3. Steps can depend on previous steps
4. Be specific — avoid vague steps like "analyze information"
5. Output ONLY valid JSON matching the schema below

OUTPUT SCHEMA:
{{
  "goal": "original goal string",
  "reasoning": "why you chose this approach",
  "estimated_steps": <number>,
  "steps": [
    {{
      "id": "step_1",
      "description": "Clear description of what to do",
      "tool": "tool_name or null",
      "tool_args": {{"arg": "value"}},
      "depends_on": [],
      "expected_output": "what this step produces"
    }}
  ]
}}

CONTEXT FROM MEMORY:
{memory_context}
"""


class PlannerAgent:
    """
    Planner Agent: Converts a goal into a structured, tool-grounded plan.
    Uses LLM reasoning to break complex tasks into discrete executable steps.
    """

    def __init__(self):
        self.llm = get_llm_client()
        self.tool_registry = get_tool_registry()

    async def plan(
        self,
        goal: str,
        memory_context: list[dict[str, Any]] | None = None,
        session_context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Generate a structured execution plan for the given goal.

        Args:
            goal: The high-level task to accomplish
            memory_context: Relevant past interactions from long-term memory
            session_context: Current session history

        Returns:
            Structured plan dict with steps and tool assignments
        """
        tool_descriptions = self._format_tool_descriptions()
        memory_str = self._format_memory(memory_context or [])

        system = PLANNER_SYSTEM_PROMPT.format(
            tool_descriptions=tool_descriptions,
            memory_context=memory_str,
        )

        session_str = ""
        if session_context:
            recent = session_context[-4:]  # last 4 messages
            session_str = "\nRecent conversation:\n" + "\n".join(
                f"{m.get('role', 'user')}: {str(m.get('content', ''))[:200]}"
                for m in recent
            )

        user_prompt = f"Goal: {goal}{session_str}\n\nGenerate the execution plan as JSON."

        logger.info(f"[PlannerAgent] Planning goal: {goal[:80]}...")

        response = await self.llm.complete(
            system=system,
            user=user_prompt,
            json_mode=True,
            temperature=0.1,
        )

        plan = self.llm.parse_json(response)
        self._validate_plan(plan)

        logger.info(f"[PlannerAgent] Plan generated with {len(plan.get('steps', []))} steps")
        return plan

    def _format_tool_descriptions(self) -> str:
        """Format available tools for the planner prompt."""
        tools = self.tool_registry.list_tools()
        lines = []
        for name, meta in tools.items():
            lines.append(f"- {name}: {meta.get('description', 'No description')}")
            if meta.get("args"):
                args_str = ", ".join(f"{k}: {v}" for k, v in meta["args"].items())
                lines.append(f"  Args: {args_str}")
        return "\n".join(lines)

    def _format_memory(self, memory_context: list[dict[str, Any]]) -> str:
        """Format memory context for injection into prompt."""
        if not memory_context:
            return "No relevant past context found."
        lines = []
        for item in memory_context[:3]:
            text = item.get("text", "")[:300]
            score = item.get("score", 0)
            lines.append(f"[relevance={score:.2f}] {text}")
        return "\n".join(lines)

    def _validate_plan(self, plan: dict[str, Any]) -> None:
        """Basic validation of plan structure."""
        required = ["goal", "steps"]
        for field in required:
            if field not in plan:
                raise ValueError(f"Plan missing required field: {field}")
        if not isinstance(plan["steps"], list) or len(plan["steps"]) == 0:
            raise ValueError("Plan must have at least one step")
        for step in plan["steps"]:
            if "id" not in step or "description" not in step:
                raise ValueError(f"Step missing id or description: {step}")
