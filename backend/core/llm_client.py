"""
BrahmaAI LLM Client
Abstraction over OpenAI / Anthropic / Ollama with unified interface.
"""

import json
import logging
from typing import Any

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Unified LLM client. Supports OpenAI and Anthropic.
    Swap providers via LLM_PROVIDER env var.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.provider == "openai":
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            except ImportError:
                logger.warning("OpenAI not installed. pip install openai")
        elif self.provider == "anthropic":
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            except ImportError:
                logger.warning("Anthropic not installed. pip install anthropic")

    async def complete(
        self,
        system: str,
        user: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> str:
        """
        Send a completion request and return the response text.
        Falls back to mock responses when no API key is configured.
        """
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        tokens = max_tokens or settings.LLM_MAX_TOKENS

        # Fallback: mock mode when no API keys
        if not settings.OPENAI_API_KEY and not settings.ANTHROPIC_API_KEY:
            return await self._mock_response(system, user, json_mode)

        if self.provider == "openai":
            return await self._openai_complete(system, user, temp, tokens, json_mode)
        elif self.provider == "anthropic":
            return await self._anthropic_complete(system, user, temp, tokens)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    async def _openai_complete(
        self,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self._client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def _anthropic_complete(
        self,
        system: str,
        user: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        response = await self._client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            temperature=temperature,
        )
        return response.content[0].text

    async def _mock_response(self, system: str, user: str, json_mode: bool) -> str:
        """
        Mock LLM responses for demo/testing when no API keys are set.
        Returns realistic structured responses.
        """
        import asyncio
        await asyncio.sleep(0.3)  # Simulate API latency

        user_lower = user.lower()

        if json_mode and "plan" in system.lower():
            # Planner mock
            return json.dumps({
                "goal": user[:100],
                "reasoning": "Breaking this goal into executable steps using available tools.",
                "estimated_steps": 3,
                "steps": [
                    {
                        "id": "step_1",
                        "description": "Research and gather relevant information",
                        "tool": "web_search",
                        "tool_args": {"query": user[:80]},
                        "depends_on": [],
                        "expected_output": "Search results with relevant information"
                    },
                    {
                        "id": "step_2",
                        "description": "Analyze and process the gathered information",
                        "tool": "code_executor",
                        "tool_args": {"code": "# Process and analyze results\nresults = []\nprint('Analysis complete')"},
                        "depends_on": ["step_1"],
                        "expected_output": "Processed analysis"
                    },
                    {
                        "id": "step_3",
                        "description": "Synthesize findings into a final report",
                        "tool": None,
                        "tool_args": {},
                        "depends_on": ["step_2"],
                        "expected_output": "Final structured report"
                    }
                ]
            })
        elif json_mode and "critic" in system.lower():
            return json.dumps({
                "quality_score": 8,
                "completeness": "The task was addressed with reasonable depth.",
                "issues": [],
                "improvements": ["Could include more specific data points"],
                "should_replan": False,
                "reason": "Results are satisfactory for the given goal."
            })
        else:
            # Generic synthesis mock
            return f"""Based on the analysis of your request, here is a comprehensive response:

**Task Completed Successfully**

The multi-agent system has processed your goal and gathered relevant information. 
Key findings have been synthesized into this response.

**Summary**: The task "{user[:60]}..." has been executed through a structured planning and execution pipeline. 
The system searched for relevant information, processed it, and compiled these insights.

**Next Steps**: You can ask follow-up questions or request deeper analysis on any specific aspect.

*Note: This is a demo response. Connect an OpenAI or Anthropic API key in .env for full AI-powered responses.*"""

    def parse_json(self, text: str) -> dict[str, Any]:
        """Safely parse JSON from LLM output, handling markdown fences."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}\nText: {text[:200]}")
            raise


# Singleton
_llm_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
