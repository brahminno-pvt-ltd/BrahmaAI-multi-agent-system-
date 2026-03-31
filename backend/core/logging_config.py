"""
BrahmaAI Logging Configuration
Structured JSON logging for production, human-readable for development.
"""

import logging
import sys
import json
import time
from typing import Any
from backend.config.settings import settings


class JSONFormatter(logging.Formatter):
    """Emit logs as single-line JSON objects for log aggregation systems."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            log_data["exc"] = self.formatException(record.exc_info)
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
        if hasattr(record, "session_id"):
            log_data["session_id"] = record.session_id
        return json.dumps(log_data, ensure_ascii=False)


class ColorFormatter(logging.Formatter):
    """Human-readable colored logs for development."""

    COLORS = {
        "DEBUG":    "\033[36m",   # cyan
        "INFO":     "\033[32m",   # green
        "WARNING":  "\033[33m",   # yellow
        "ERROR":    "\033[31m",   # red
        "CRITICAL": "\033[35m",   # magenta
    }
    RESET = "\033[0m"
    DIM = "\033[2m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        ts = time.strftime("%H:%M:%S", time.localtime(record.created))
        level = f"{color}{record.levelname:<8}{self.RESET}"
        name = f"{self.DIM}{record.name:<30}{self.RESET}"
        msg = record.getMessage()
        line = f"{self.DIM}{ts}{self.RESET} {level} {name} {msg}"
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


def configure_logging() -> None:
    """
    Configure root logger based on environment.
    - Production (DEBUG=False): JSON output to stdout
    - Development (DEBUG=True): Colored human-readable output
    """
    root = logging.getLogger()
    root.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Remove any existing handlers
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    if settings.DEBUG:
        handler.setFormatter(ColorFormatter())
    else:
        handler.setFormatter(JSONFormatter())

    root.addHandler(handler)

    # Quiet noisy libraries
    for noisy in ["uvicorn.access", "httpx", "httpcore", "faiss"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("uvicorn").setLevel(
        logging.DEBUG if settings.DEBUG else logging.INFO
    )
