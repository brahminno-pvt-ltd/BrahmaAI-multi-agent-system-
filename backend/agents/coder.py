"""
BrahmaAI Coder Agent
Specialised agent for code generation, review, debugging, and explanation.
Generates, tests, and iteratively refines code using the sandbox executor.
"""

import logging
import re
from typing import Any

from backend.core.llm_client import get_llm_client
from backend.tools.registry import get_tool_registry

logger = logging.getLogger(__name__)

CODE_GEN_SYSTEM = """You are an expert software engineer. Generate clean, production-quality code.

Rules:
- Write complete, runnable code (not pseudocode)
- Include proper error handling
- Add clear docstrings and type hints (Python) or JSDoc (JS/TS)
- Follow language-specific best practices
- Include a brief usage example in comments
- For Python: prefer stdlib; only suggest third-party packages when necessary

If the user asks for a specific framework (FastAPI, React, etc.), use it correctly.
"""

CODE_REVIEW_SYSTEM = """You are a senior code reviewer. Analyse the given code and provide:

1. **Summary**: What the code does (1-2 sentences)
2. **Issues Found**: Security vulnerabilities, bugs, performance problems (with line references)
3. **Code Quality**: Style, naming, documentation, complexity
4. **Improvements**: Concrete suggestions with code snippets
5. **Overall Score**: X/10 with justification

Be direct, constructive, and specific.
"""

DEBUG_SYSTEM = """You are a debugging expert. You will receive code and an error message.

Your task:
1. Identify the exact cause of the error
2. Explain why it occurs in plain English
3. Provide a corrected version of the code
4. Add a comment in the fix explaining what changed and why

Format your response as:
**Root Cause:** [explanation]
**Fix:**
```[language]
[corrected code]
```
**What Changed:** [brief explanation]
"""


class CoderAgent:
    """
    Coder Agent: Handles code generation, review, debugging, and explanation.
    
    Integrates with the code_executor tool to test generated code and
    iterate until it runs successfully.
    """

    def __init__(self):
        self.llm = get_llm_client()
        self.registry = get_tool_registry()

    async def generate(
        self,
        description: str,
        language: str = "python",
        test: bool = True,
        max_iterations: int = 3,
    ) -> dict[str, Any]:
        """
        Generate code for a description, optionally testing and refining it.

        Args:
            description: What the code should do
            language: Target language (python, typescript, javascript, etc.)
            test: Whether to test Python code in the sandbox
            max_iterations: Max fix-and-retry iterations

        Returns:
            Generated code, test results, and explanation
        """
        logger.info(f"[CoderAgent] Generating {language} code: {description[:60]}")

        code = await self._generate_code(description, language)
        test_result = None
        iteration = 0

        # Only test Python code (sandbox only supports Python)
        if test and language.lower() == "python" and self.registry.has_tool("code_executor"):
            executor = self.registry.get_tool("code_executor")

            while iteration < max_iterations:
                test_result = await executor.execute(code=code, timeout=10)
                if test_result.get("status") == "success":
                    logger.info(f"[CoderAgent] Code passed on iteration {iteration + 1}")
                    break
                elif test_result.get("status") == "blocked":
                    # Safety block — don't retry
                    break
                else:
                    # Try to fix
                    error = test_result.get("error", test_result.get("output", ""))
                    logger.info(f"[CoderAgent] Fixing error (iter {iteration + 1}): {error[:60]}")
                    code = await self._fix_code(code, error, language)
                    iteration += 1

        explanation = await self._explain_code(code, language)

        return {
            "status":       "success",
            "language":     language,
            "code":         code,
            "explanation":  explanation,
            "test_result":  test_result,
            "iterations":   iteration,
            "output":       self._format_output(code, language, explanation, test_result),
        }

    async def review(self, code: str, language: str = "python") -> dict[str, Any]:
        """Review code and return structured feedback."""
        logger.info(f"[CoderAgent] Reviewing {language} code ({len(code)} chars)")

        response = await self.llm.complete(
            system=CODE_REVIEW_SYSTEM,
            user=f"Language: {language}\n\nCode to review:\n```{language}\n{code}\n```",
            temperature=0.1,
        )

        return {
            "status":   "success",
            "language": language,
            "review":   response,
            "output":   response,
        }

    async def debug(
        self,
        code: str,
        error: str,
        language: str = "python",
    ) -> dict[str, Any]:
        """Debug code given an error message and return a fix."""
        logger.info(f"[CoderAgent] Debugging {language}: {error[:60]}")

        response = await self.llm.complete(
            system=DEBUG_SYSTEM,
            user=(
                f"Language: {language}\n\n"
                f"Error:\n```\n{error}\n```\n\n"
                f"Code:\n```{language}\n{code}\n```"
            ),
            temperature=0.1,
        )

        # Extract fixed code from response
        fixed_code = self._extract_code_block(response) or code

        return {
            "status":      "success",
            "original":    code,
            "fixed":       fixed_code,
            "explanation": response,
            "output":      response,
        }

    async def _generate_code(self, description: str, language: str) -> str:
        """Generate initial code."""
        response = await self.llm.complete(
            system=CODE_GEN_SYSTEM,
            user=(
                f"Language: {language}\n"
                f"Task: {description}\n\n"
                f"Generate complete, working {language} code. "
                f"Return ONLY the code block, no extra explanation."
            ),
            temperature=0.2,
        )
        return self._extract_code_block(response) or response

    async def _fix_code(self, code: str, error: str, language: str) -> str:
        """Attempt to fix code given an error."""
        response = await self.llm.complete(
            system=DEBUG_SYSTEM,
            user=(
                f"Language: {language}\n"
                f"Error: {error[:500]}\n\n"
                f"Code:\n```{language}\n{code}\n```\n\n"
                "Fix the code. Return ONLY the corrected code block."
            ),
            temperature=0.1,
        )
        return self._extract_code_block(response) or code

    async def _explain_code(self, code: str, language: str) -> str:
        """Generate a brief explanation of what the code does."""
        response = await self.llm.complete(
            system="You are a technical writer. Explain code clearly and concisely.",
            user=(
                f"Explain this {language} code in 2-4 sentences. "
                f"Focus on what it does and how to use it.\n\n"
                f"```{language}\n{code[:1000]}\n```"
            ),
            temperature=0.3,
        )
        return response

    def _extract_code_block(self, text: str) -> str | None:
        """Extract code from markdown code fences."""
        # Match ```language ... ``` or ``` ... ```
        pattern = r"```(?:\w+)?\n([\s\S]*?)```"
        matches = re.findall(pattern, text)
        if matches:
            return matches[0].strip()
        return None

    def _format_output(
        self,
        code: str,
        language: str,
        explanation: str,
        test_result: dict[str, Any] | None,
    ) -> str:
        lines = [
            f"## Generated {language.title()} Code\n",
            f"```{language}",
            code,
            "```\n",
            f"**Explanation:** {explanation}",
        ]
        if test_result:
            status = test_result.get("status", "unknown")
            icon = "✅" if status == "success" else "❌"
            lines.append(f"\n**Test Result:** {icon} {status}")
            if status == "success" and test_result.get("output"):
                lines.append(f"```\n{test_result['output']}\n```")
        return "\n".join(lines)
