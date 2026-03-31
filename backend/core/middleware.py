"""
BrahmaAI Middleware
Rate limiting, request ID injection, and request size validation.
"""

import time
import uuid
import logging
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Injects a unique X-Request-ID header into every request and response.
    Useful for distributed tracing and log correlation.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory sliding window rate limiter.
    Limits requests per IP address. For production, use Redis-backed rate limiting.

    Default: 60 requests per 60 seconds per IP.
    """

    def __init__(
        self,
        app,
        requests_per_window: int = 60,
        window_seconds: int = 60,
        skip_paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.skip_paths = skip_paths or ["/api/health", "/"]
        self._store: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for certain paths
        if any(request.url.path.startswith(p) for p in self.skip_paths):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        self._store[client_ip] = [
            ts for ts in self._store[client_ip] if ts > window_start
        ]

        if len(self._store[client_ip]) >= self.requests_per_window:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Max {self.requests_per_window} requests per {self.window_seconds}s",
                    "retry_after": self.window_seconds,
                },
                headers={"Retry-After": str(self.window_seconds)},
            )

        self._store[client_ip].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_window - len(self._store[client_ip])
        )
        return response


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """
    Rejects requests larger than a configured size limit.
    Default: 10MB
    """

    def __init__(self, app, max_size_bytes: int = 10 * 1024 * 1024):
        super().__init__(app)
        self.max_size_bytes = max_size_bytes

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_size_bytes:
            return JSONResponse(
                status_code=413,
                content={
                    "error": "Request too large",
                    "detail": f"Max request size: {self.max_size_bytes // 1024 // 1024}MB",
                },
            )
        return await call_next(request)
