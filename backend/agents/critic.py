"""
BrahmaAI Critic (Reflection) Agent
Evaluates the quality of execution results and decides if re-planning is needed.
"""

import logging
from typing import Any

from backend.core.llm_client import get_llm_client

logger = logging.getLogger(__name__)

CRITIC_SYSTEM_PROMPT = """You are the Critic Agent for BrahmaAI — a ruthlessly analytical quality evaluator.

Your role is to assess whether the executed plan has adequately addressed the user's goal.

Evaluate based on:
1. **Completeness**: Did the results cover all aspects of the goal?
2. **Accuracy**: Are the results likely to be accurate and reliable?
3. **Usefulness**: Would a user find this response genuinely helpful?
4. **Gaps**: What important information is missing?

Output ONLY valid JSON with this schema:
{
  "quality_score": <1-10>,
  "completeness": "assessment of how complete the results are",
  "issues": ["list of specific problems found"],
  "improvements": ["list of concrete improvements"],
  "should_replan": <true/false>,
  "reason": "why you recommend replanning or not",
  "revised_goal": "if should_replan=true, a refined goal string"
}

Be strict but fair. Score 7+ means no replanning needed.
"""


class CriticAgent:
    """
    Critic Agent: Reflects on execution results and recommends improvements.
    Triggers re-planning if quality is insufficient.
    """

    def __init__(self):
        self.llm = get_llm_client()

    async def reflect(
        self,
        goal: str,
        plan: dict[str, Any],
        results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Evaluate execution results and produce a quality assessment.

        Args:
            goal: Original user goal
            plan: The plan that was executed
            results: All step results

        Returns:
            Reflection dict with quality score and improvement suggestions
        """
        logger.info("[CriticAgent] Reflecting on execution results...")

        results_summary = self._summarize_results(results)
        plan_summary = self._summarize_plan(plan)

        user_prompt = f"""Goal: {goal}

Executed Plan:
{plan_summary}

Results:
{results_summary}

Assess whether this execution adequately addressed the goal."""

        response = await self.llm.complete(
            system=CRITIC_SYSTEM_PROMPT,
            user=user_prompt,
            json_mode=True,
            temperature=0.1,
        )

        reflection = self.llm.parse_json(response)
        logger.info(
            f"[CriticAgent] Quality score: {reflection.get('quality_score')}/10 | "
            f"Replan: {reflection.get('should_replan')}"
        )
        return reflection

    def _summarize_plan(self, plan: dict[str, Any]) -> str:
        steps = plan.get("steps", [])
        lines = [f"Plan has {len(steps)} steps:"]
        for step in steps:
            lines.append(f"  - [{step.get('id')}] {step.get('description')} (tool: {step.get('tool', 'none')})")
        return "\n".join(lines)

    def _summarize_results(self, results: list[dict[str, Any]]) -> str:
        lines = []
        for item in results:
            step = item.get("step", {})
            result = item.get("result", {})
            status = result.get("status", "unknown")
            tool_result = result.get("tool_result", {})
            output = tool_result.get("output", str(tool_result))
            error = tool_result.get("error")

            lines.append(
                f"Step: {step.get('description', 'N/A')}\n"
                f"  Status: {status}\n"
                f"  {'Error: ' + str(error) if error else 'Output: ' + str(output)[:300]}"
            )
        return "\n\n".join(lines) if lines else "No results available."
