"""
BrahmaAI Long-Term Memory
Vector store using FAISS for semantic retrieval of past interactions.
Falls back to simple in-memory store when FAISS is unavailable.
"""

import json
import logging
import os
import time
import uuid
from typing import Any

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class LongTermMemory:
    """
    Long-term vector memory using FAISS + OpenAI embeddings.
    Automatically falls back to cosine-similarity in-memory store
    when FAISS or embedding APIs are unavailable.
    """

    def __init__(self):
        self._use_faiss = False
        self._fallback_store: list[dict[str, Any]] = []
        self._embeddings: list[list[float]] = []
        self._faiss_index = None
        self._embedding_client = None
        self._try_init_faiss()

    def _try_init_faiss(self) -> None:
        """Attempt to initialize FAISS + embeddings."""
        try:
            import faiss  # noqa: F401
            from openai import AsyncOpenAI

            if settings.OPENAI_API_KEY:
                self._embedding_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                self._use_faiss = True
                self._init_faiss_index()
                logger.info("[LongTermMemory] FAISS initialized with OpenAI embeddings")
            else:
                logger.info("[LongTermMemory] No API key; using fallback memory store")
        except ImportError:
            logger.info("[LongTermMemory] FAISS not installed; using fallback memory store")

    def _init_faiss_index(self) -> None:
        """Initialize or load a FAISS flat index."""
        import faiss
        index_path = settings.FAISS_INDEX_PATH
        meta_path = index_path + ".meta.json"

        if os.path.exists(index_path + ".index"):
            self._faiss_index = faiss.read_index(index_path + ".index")
            if os.path.exists(meta_path):
                with open(meta_path) as f:
                    self._fallback_store = json.load(f)
            logger.info(f"[LongTermMemory] Loaded existing FAISS index ({self._faiss_index.ntotal} vectors)")
        else:
            # text-embedding-3-small dim = 1536
            self._faiss_index = faiss.IndexFlatL2(1536)
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            logger.info("[LongTermMemory] Created new FAISS index")

    async def store(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Store text and its embedding in long-term memory.

        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        entry = {
            "id": memory_id,
            "text": text,
            "metadata": metadata or {},
            "created_at": time.time(),
        }

        if self._use_faiss:
            embedding = await self._embed(text)
            import numpy as np
            vec = np.array([embedding], dtype=np.float32)
            self._faiss_index.add(vec)
            self._fallback_store.append(entry)
            self._embeddings.append(embedding)
            self._save_faiss()
        else:
            self._fallback_store.append(entry)

        return memory_id

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Retrieve semantically similar memories.

        Returns:
            List of memory entries with similarity scores
        """
        if not self._fallback_store:
            return []

        if self._use_faiss and self._faiss_index.ntotal > 0:
            return await self._faiss_retrieve(query, top_k)
        else:
            return self._keyword_retrieve(query, top_k)

    async def _faiss_retrieve(
        self,
        query: str,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Vector similarity search via FAISS."""
        import numpy as np
        query_embedding = await self._embed(query)
        vec = np.array([query_embedding], dtype=np.float32)
        k = min(top_k, self._faiss_index.ntotal)
        distances, indices = self._faiss_index.search(vec, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self._fallback_store):
                entry = self._fallback_store[idx].copy()
                entry["score"] = float(1 / (1 + dist))  # Convert L2 to similarity
                results.append(entry)
        return results

    def _keyword_retrieve(
        self,
        query: str,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Simple keyword-based fallback retrieval."""
        query_words = set(query.lower().split())
        scored = []
        for entry in self._fallback_store:
            text_words = set(entry["text"].lower().split())
            overlap = len(query_words & text_words)
            if overlap > 0:
                scored.append((overlap / len(query_words | text_words), entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, entry in scored[:top_k]:
            e = entry.copy()
            e["score"] = score
            results.append(e)
        return results

    async def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        """List most recently stored memories."""
        sorted_entries = sorted(
            self._fallback_store,
            key=lambda x: x.get("created_at", 0),
            reverse=True,
        )
        return sorted_entries[:limit]

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory entry (marks as deleted; FAISS index not rebuilt)."""
        for i, entry in enumerate(self._fallback_store):
            if entry["id"] == memory_id:
                self._fallback_store.pop(i)
                logger.info(f"[LongTermMemory] Deleted memory: {memory_id}")
                return True
        return False

    async def _embed(self, text: str) -> list[float]:
        """Get embedding vector from OpenAI."""
        response = await self._embedding_client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text[:8000],
        )
        return response.data[0].embedding

    def _save_faiss(self) -> None:
        """Persist FAISS index and metadata to disk."""
        try:
            import faiss
            index_path = settings.FAISS_INDEX_PATH
            faiss.write_index(self._faiss_index, index_path + ".index")
            with open(index_path + ".meta.json", "w") as f:
                json.dump(self._fallback_store, f)
        except Exception as e:
            logger.error(f"[LongTermMemory] Failed to save FAISS index: {e}")
