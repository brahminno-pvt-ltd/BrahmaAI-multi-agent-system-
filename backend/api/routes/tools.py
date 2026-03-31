"""
BrahmaAI Tools API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.tools.registry import get_tool_registry

router = APIRouter()


class ToolExecuteRequest(BaseModel):
    tool_name: str
    args: dict = {}


@router.get("/list")
async def list_tools():
    """List all available tools."""
    registry = get_tool_registry()
    return {"tools": registry.list_tools()}


@router.post("/execute")
async def execute_tool(request: ToolExecuteRequest):
    """Directly execute a tool by name."""
    registry = get_tool_registry()
    if not registry.has_tool(request.tool_name):
        raise HTTPException(status_code=404, detail=f"Tool not found: {request.tool_name}")
    tool = registry.get_tool(request.tool_name)
    result = await tool.execute(**request.args)
    return {"tool": request.tool_name, "result": result}
