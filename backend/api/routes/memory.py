"""
BrahmaAI Memory API Routes
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.agents.memory_agent import MemoryAgent

logger = logging.getLogger(__name__)
router = APIRouter()
_memory_agent = MemoryAgent()


class StoreRequest(BaseModel):
    text: str
    metadata: dict = {}


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/store")
async def store_memory(request: StoreRequest):
    """Store a piece of information in long-term memory."""
    memory_id = await _memory_agent.remember(
        text=request.text,
        metadata=request.metadata,
    )
    return {"status": "stored", "memory_id": memory_id}


@router.post("/retrieve")
async def retrieve_memory(request: RetrieveRequest):
    """Retrieve semantically similar memories."""
    results = await _memory_agent.recall(
        query=request.query,
        top_k=request.top_k,
    )
    return {"results": results, "count": len(results)}


@router.get("/list")
async def list_memories(limit: int = 20):
    """List recent long-term memories."""
    memories = await _memory_agent.list_memories(limit=limit)
    return {"memories": memories, "count": len(memories)}


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a specific memory."""
    success = await _memory_agent.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted", "memory_id": memory_id}
