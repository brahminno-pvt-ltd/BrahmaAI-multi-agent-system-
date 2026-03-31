"""
BrahmaAI Executor Agent
Executes individual plan steps by dispatching to the appropriate tool.
Handles context injection, retries, and result formatting.
"""

import logging
from typing import Any

from backend.core.llm_client import get_llm_client
from backend.tools.registry import get_tool_registry

logger = logging.getLogger(__name__)

EXECUTOR_SYSTEM_PROMPT = """You are the Executor Agent for BrahmaAI.

Your role is to execute a specific task step using the provided tool result.

Given:
- The original goal
- The current step description  
- The tool result (raw data from a tool call)
- Context from previous steps

Your job is to:
1. Interpret the tool result in the context of the step
2. Extract key information
3. Format it clearly for the next step

Be concise and structured. Focus on facts, not opinions.
"""

SYNTHESIS_SYSTEM_PROMPT = """You are the Synthesis Agent for BrahmaAI.

You have completed a multi-step task. Now synthesize all results into a clear, comprehensive final answer.

Structure your response as:
1. **Summary**: One paragraph summarizing what was accomplished
2. **Key Findings**: Bullet points of the most important information
3. **Details**: More detailed breakdown if needed
4. **Next Steps**: What the user might want to do next

Be helpful, accurate, and concise. Format for readability.
"""


class ExecutorAgent:
    """
    Executor Agent: Runs individual plan steps against the tool layer.
    Injects context from previous steps and handles tool dispatch.
    """

    def __init__(self):
        self.llm = get_llm_client()
        self.tool_registry = get_tool_registry()

    async def execute_step(
        self,
        step: dict[str, Any],
        context: list[dict[str, Any]],
        memory_context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Execute a single plan step.

        Args:
            step: The step dict from the planner
            context: Results from previously executed steps
            memory_context: Long-term memory context

        Returns:
            Structured result dict
        """
        step_id = step.get("id", "unknown")
        description = step.get("description", "")
        tool_name = step.get("tool")
        tool_args = step.get("tool_args", {})

        logger.info(f"[ExecutorAgent] Executing step: {step_id} | tool: {tool_name}")

        # Inject context from previous steps into tool args
        tool_args = self._inject_context(tool_args, context)

        raw_tool_result: dict[str, Any] = {}

        if tool_name and self.tool_registry.has_tool(tool_name):
            # Execute the tool
            tool = self.tool_registry.get_tool(tool_name)
            raw_tool_result = await tool.execute(**tool_args)
            logger.info(f"[ExecutorAgent] Tool {tool_name} executed, status: {raw_tool_result.get('status')}")
        else:
            # No tool — use LLM reasoning directly
            context_str = self._format_context(context)
            memory_str = self._format_memory(memory_context or [])

            llm_response = await self.llm.complete(
                system=EXECUTOR_SYSTEM_PROMPT,
                user=f"""Goal context: {context[0]['step']['description'] if context else 'N/A'}
                
Current step: {description}

Previous results:
{context_str}

Memory context:
{memory_str}

Execute this step and provide a structured result.""",
            )
            raw_tool_result = {
                "status": "success",
                "output": llm_response,
                "tool": "llm_reasoning",
            }

        return {
            "step_id": step_id,
            "description": description,
            "tool": tool_name,
            "tool_result": raw_tool_result,
            "status": raw_tool_result.get("status", "success"),
        }

    async def synthesize(
        self,
        goal: str,
        results: list[dict[str, Any]],
        reflection: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Synthesize all step results into a final answer.

        Args:
            goal: The original user goal
            results: All step results from execution
            reflection: Critic's assessment

        Returns:
            Final answer with summary, findings, and details
        """
        results_text = self._format_results_for_synthesis(results)
        reflection_text = reflection.get("completeness", "")

        response = await self.llm.complete(
            system=SYNTHESIS_SYSTEM_PROMPT,
            user=f"""Original Goal: {goal}

Execution Results:
{results_text}

Critic Assessment: {reflection_text}

Please synthesize a comprehensive final answer.""",
        )

        return {
            "summary": response,
            "goal": goal,
            "steps_executed": len(results),
            "quality_score": reflection.get("quality_score", 7),
        }

    def _inject_context(
        self,
        tool_args: dict[str, Any],
        context: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Replace context placeholder tokens in tool args."""
        if not context:
            return tool_args

        # Get last result's output for injection
        last_result = context[-1].get("result", {})
        last_output = last_result.get("tool_result", {}).get("output", "")

        updated = {}
        for key, value in tool_args.items():
            if isinstance(value, str) and "{prev_output}" in value:
                updated[key] = value.replace("{prev_output}", str(last_output)[:500])
            else:
                updated[key] = value
        return updated

    def _format_context(self, context: list[dict[str, Any]]) -> str:
        """Format previous results for prompt injection."""
        if not context:
            return "No previous results."
        lines = []
        for item in context[-3:]:  # last 3 steps
            step_desc = item.get("step", {}).get("description", "")
            result = item.get("result", {})
            output = result.get("tool_result", {}).get("output", str(result))
            lines.append(f"Step: {step_desc}\nResult: {str(output)[:400]}\n")
        return "\n".join(lines)

    def _format_memory(self, memory_context: list[dict[str, Any]]) -> str:
        if not memory_context:
            return "No memory context."
        return "\n".join(
            f"- {item.get('text', '')[:200]}" for item in memory_context[:3]
        )

    def _format_results_for_synthesis(self, results: list[dict[str, Any]]) -> str:
        lines = []
        for item in results:
            step = item.get("step", {})
            result = item.get("result", {})
            tool_result = result.get("tool_result", {})
            output = tool_result.get("output", tool_result.get("data", str(tool_result)))
            lines.append(
                f"### {step.get('description', 'Step')}\n"
                f"Tool: {step.get('tool', 'reasoning')}\n"
                f"Output: {str(output)[:600]}\n"
            )
        return "\n".join(lines)
