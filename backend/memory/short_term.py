"""
BrahmaAI Short-Term Memory
In-memory session context with sliding window management.
"""

import time
from collections import defaultdict
from typing import Any

from backend.config.settings import settings


class ShortTermMemory:
    """
    In-memory session store with automatic pruning.
    Stores conversation history per session_id.
    """

    def __init__(self):
        self._store: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._max_messages = settings.SHORT_TERM_MAX_MESSAGES

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to session history."""
        entry = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }
        self._store[session_id].append(entry)

        # Prune if over limit
        if len(self._store[session_id]) > self._max_messages:
            # Keep first (system) + last N messages
            self._store[session_id] = self._store[session_id][-self._max_messages:]

    def get_context(self, session_id: str) -> list[dict[str, Any]]:
        """Retrieve session history."""
        return self._store.get(session_id, [])

    def clear_session(self, session_id: str) -> None:
        """Clear a session's history."""
        if session_id in self._store:
            del self._store[session_id]

    def list_sessions(self) -> list[str]:
        """List active session IDs."""
        return list(self._store.keys())

    def session_summary(self, session_id: str) -> dict[str, Any]:
        """Get a summary of a session."""
        messages = self._store.get(session_id, [])
        return {
            "session_id": session_id,
            "message_count": len(messages),
            "first_message_at": messages[0]["timestamp"] if messages else None,
            "last_message_at": messages[-1]["timestamp"] if messages else None,
        }
