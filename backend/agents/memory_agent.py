"""
BrahmaAI Memory Agent
Manages intelligent storage and retrieval of past interactions.
"""

import logging
from typing import Any

from backend.memory.long_term import LongTermMemory
from backend.memory.short_term import ShortTermMemory

logger = logging.getLogger(__name__)


class MemoryAgent:
    """
    Memory Agent: Wraps long-term and short-term memory with intelligent
    retrieval and storage operations.
    """

    def __init__(self):
        self.long_term = LongTermMemory()
        self.short_term = ShortTermMemory()

    async def remember(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Store a piece of information in long-term memory."""
        try:
            await self.long_term.store(text=text, metadata=metadata or {})
            logger.info(f"[MemoryAgent] Stored: {text[:60]}...")
            return True
        except Exception as e:
            logger.error(f"[MemoryAgent] Failed to store: {e}")
            return False

    async def recall(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant memories based on semantic similarity."""
        try:
            results = await self.long_term.retrieve(query=query, top_k=top_k)
            logger.info(f"[MemoryAgent] Retrieved {len(results)} memories for: {query[:60]}")
            return results
        except Exception as e:
            logger.error(f"[MemoryAgent] Failed to retrieve: {e}")
            return []

    def get_session(self, session_id: str) -> list[dict[str, Any]]:
        """Get session history from short-term memory."""
        return self.short_term.get_context(session_id)

    def add_to_session(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Add a message to short-term session memory."""
        self.short_term.add_message(session_id=session_id, role=role, content=content)

    async def list_memories(
        self,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List recent long-term memories."""
        try:
            return await self.long_term.list_recent(limit=limit)
        except Exception as e:
            logger.error(f"[MemoryAgent] Failed to list memories: {e}")
            return []

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory by ID."""
        try:
            return await self.long_term.delete(memory_id)
        except Exception as e:
            logger.error(f"[MemoryAgent] Failed to delete memory: {e}")
            return False
