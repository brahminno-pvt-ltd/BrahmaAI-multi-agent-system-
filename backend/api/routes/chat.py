"""
BrahmaAI Chat API Routes
Handles chat messages with streaming agent loop execution.
"""

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.core.orchestrator import Orchestrator
from backend.memory.short_term import ShortTermMemory

logger = logging.getLogger(__name__)
router = APIRouter()

_orchestrator = Orchestrator()
_short_term = ShortTermMemory()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    stream: bool = True


class ChatMessage(BaseModel):
    role: str
    content: str
    session_id: str | None = None


@router.post("/message")
async def chat_message(request: ChatRequest):
    """
    Send a message to the AI agent system.
    Returns a streaming SSE response with real-time agent events.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Store user message
    session_id = request.session_id or "default"
    _short_term.add_message(
        session_id=session_id,
        role="user",
        content=request.message,
    )

    if request.stream:
        return StreamingResponse(
            _stream_response(request.message, session_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # Non-streaming: collect all events and return final answer
        events = []
        final = None
        async for event in _orchestrator.run_task(
            goal=request.message,
            session_id=session_id,
        ):
            events.append(event)
            if event.get("event") == "complete":
                final = event["data"]

        return {
            "session_id": session_id,
            "events": events,
            "final": final,
        }


async def _stream_response(
    message: str,
    session_id: str,
) -> AsyncGenerator[str, None]:
    """Stream SSE events from the agent loop."""
    try:
        async for event in _orchestrator.run_task(
            goal=message,
            session_id=session_id,
        ):
            payload = json.dumps(event, default=str)
            yield f"data: {payload}\n\n"

        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_event = json.dumps({"event": "error", "data": {"error": str(e)}})
        yield f"data: {error_event}\n\n"
        yield "data: [DONE]\n\n"


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    """Get conversation history for a session."""
    messages = _short_term.get_context(session_id)
    return {
        "session_id": session_id,
        "messages": messages,
        "count": len(messages),
    }


@router.delete("/history/{session_id}")
async def clear_history(session_id: str):
    """Clear conversation history for a session."""
    _short_term.clear_session(session_id)
    return {"status": "cleared", "session_id": session_id}


@router.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    sessions = _short_term.list_sessions()
    return {"sessions": sessions, "count": len(sessions)}
