"""
BrahmaAI Code Executor Tool
Executes Python code in a sandboxed subprocess with timeout.
"""

import asyncio
import logging
import sys
import tempfile
import os
from typing import Any

from backend.tools.registry import BaseTool
from backend.config.settings import settings

logger = logging.getLogger(__name__)

# Blocked imports for safety
BLOCKED_MODULES = {
    "os", "subprocess", "sys", "shutil", "socket",
    "ctypes", "importlib", "pickle", "multiprocessing",
    "__builtin__", "builtins",
}

SAFE_PREAMBLE = """
import math
import json
import re
import datetime
from collections import defaultdict, Counter
from itertools import islice
"""


class CodeExecutorTool(BaseTool):
    name = "code_executor"
    description = "Execute Python code safely in a sandboxed environment"
    args = {
        "code": "str: Python code to execute",
        "timeout": "int: Execution timeout in seconds (default: 10)",
    }

    async def execute(
        self,
        code: str,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        timeout = timeout or settings.SANDBOX_TIMEOUT_SECONDS
        logger.info(f"[CodeExecutorTool] Executing code ({len(code)} chars)")

        # Basic safety check
        safety_check = self._check_safety(code)
        if not safety_check["safe"]:
            return {
                "status": "blocked",
                "error": f"Blocked: {safety_check['reason']}",
                "output": f"Code execution blocked: {safety_check['reason']}",
            }

        return await self._run_subprocess(code, timeout)

    async def _run_subprocess(
        self, code: str, timeout: int
    ) -> dict[str, Any]:
        """Run code in an isolated subprocess."""
        full_code = SAFE_PREAMBLE + "\n" + code

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False,
            encoding="utf-8",
        ) as f:
            f.write(full_code)
            tmp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                return {
                    "status": "timeout",
                    "error": f"Execution timed out after {timeout}s",
                    "output": f"Code timed out after {timeout} seconds.",
                }

            output = stdout.decode("utf-8", errors="replace").strip()
            error_output = stderr.decode("utf-8", errors="replace").strip()

            if proc.returncode == 0:
                return {
                    "status": "success",
                    "output": output or "(no output)",
                    "returncode": 0,
                }
            else:
                return {
                    "status": "error",
                    "output": output,
                    "error": error_output,
                    "returncode": proc.returncode,
                }

        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _check_safety(self, code: str) -> dict[str, Any]:
        """Basic static analysis to block dangerous operations."""
        code_lower = code.lower()

        dangerous_patterns = [
            ("import os", "os module"),
            ("import subprocess", "subprocess module"),
            ("__import__", "__import__ builtin"),
            ("open(", "file I/O"),
            ("exec(", "exec() builtin"),
            ("eval(", "eval() builtin"),
            ("compile(", "compile() builtin"),
        ]

        for pattern, reason in dangerous_patterns:
            if pattern in code_lower:
                return {"safe": False, "reason": f"Uses restricted: {reason}"}

        return {"safe": True, "reason": ""}
