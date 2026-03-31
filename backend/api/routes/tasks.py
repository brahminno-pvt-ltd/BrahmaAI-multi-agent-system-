"""
BrahmaAI Tasks API Routes
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.agents.planner import PlannerAgent
from backend.agents.executor import ExecutorAgent

logger = logging.getLogger(__name__)
router = APIRouter()

_planner = PlannerAgent()
_executor = ExecutorAgent()

class PlanRequest(BaseModel):
    goal: str
    memory_context: list[dict] = []


@router.post("/plan")
async def create_plan(request: PlanRequest):
    """Generate a plan for a goal without executing it."""
    try:
        plan = await _planner.plan(
            goal=request.goal,
            memory_context=request.memory_context,
        )
        return {"status": "success", "plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo")
async def demo_tasks():
    """Return the list of demo tasks the system can handle."""
    return {
        "demo_tasks": [
            {
                "id": "pdf_summary",
                "title": "Summarize a PDF",
                "prompt": "Read the file at /tmp/sample.pdf and extract key insights",
                "tools": ["file_reader"],
            },
            {
                "id": "ai_trends",
                "title": "AI Trends Report",
                "prompt": "Search for the latest AI trends in 2025 and create a structured report",
                "tools": ["web_search", "web_scraper"],
            },
            {
                "id": "python_api",
                "title": "Generate Python API",
                "prompt": "Generate a complete Python FastAPI for a todo app with CRUD endpoints",
                "tools": ["code_executor"],
            },
            {
                "id": "trip_plan",
                "title": "Trip Planner",
                "prompt": "Plan a 5-day trip to Tokyo, Japan with a $2000 budget",
                "tools": ["web_search", "calendar_tool"],
            },
        ]
    }
