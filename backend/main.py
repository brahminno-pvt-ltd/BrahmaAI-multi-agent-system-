"""
BrahmaAI FastAPI Application
Main entry point with all API routes and middleware.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json

from backend.config.settings import settings
from backend.api.routes import chat, tasks, memory, tools, auth, files, agents
from backend.tools.registry import get_tool_registry
from backend.core.logging_config import configure_logging
from backend.core.middleware import RequestIDMiddleware, RateLimitMiddleware, RequestSizeMiddleware

configure_logging()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info(f"🧠 {settings.APP_NAME} v{settings.APP_VERSION} starting...")

    # Pre-warm tool registry
    registry = get_tool_registry()
    tools_list = list(registry.list_tools().keys())
    logger.info(f"✅ Tools registered: {tools_list}")

    yield

    logger.info(f"👋 {settings.APP_NAME} shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade autonomous AI personal assistant",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Additional middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_window=120, window_seconds=60)
app.add_middleware(RequestSizeMiddleware, max_size_bytes=10 * 1024 * 1024)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def timing_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    response.headers["X-Response-Time"] = f"{duration}ms"
    return response


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(memory.router, prefix="/api/memory", tags=["Memory"])
app.include_router(tools.router, prefix="/api/tools", tags=["Tools"])
app.include_router(files.router, prefix="/api/files", tags=["Files"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "provider": settings.LLM_PROVIDER,
    }


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/api/docs",
        "health": "/api/health",
    }
