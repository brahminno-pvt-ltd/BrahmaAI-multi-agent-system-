"""
BrahmaAI Specialised Agents API
Direct endpoints for Researcher, Coder, and Task Planner agents.
These bypass the full orchestrator loop for faster, specialised responses.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.agents.researcher import ResearcherAgent
from backend.agents.coder import CoderAgent
from backend.agents.task_planner import TaskPlannerAgent

logger = logging.getLogger(__name__)
router = APIRouter()

_researcher   = ResearcherAgent()
_coder        = CoderAgent()
_task_planner = TaskPlannerAgent()


# ─── Researcher ───────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    query: str
    depth: int = Field(default=3, ge=1, le=6)
    scrape_top_n: int = Field(default=2, ge=0, le=5)


@router.post("/researcher/research")
async def run_research(request: ResearchRequest):
    """Conduct deep multi-source research on a query."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        result = await _researcher.research(
            query=request.query,
            depth=request.depth,
            scrape_top_n=request.scrape_top_n,
        )
        return result
    except Exception as e:
        logger.error(f"Research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Coder ────────────────────────────────────────────────────────────────────

class CodeGenRequest(BaseModel):
    description: str
    language: str = "python"
    test: bool = True
    max_iterations: int = Field(default=3, ge=1, le=5)


class CodeReviewRequest(BaseModel):
    code: str
    language: str = "python"


class DebugRequest(BaseModel):
    code: str
    error: str
    language: str = "python"


@router.post("/coder/generate")
async def generate_code(request: CodeGenRequest):
    """Generate code for a description, with optional test-and-fix loop."""
    if not request.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    try:
        return await _coder.generate(
            description=request.description,
            language=request.language,
            test=request.test,
            max_iterations=request.max_iterations,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coder/review")
async def review_code(request: CodeReviewRequest):
    """Review code and return structured feedback."""
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")
    try:
        return await _coder.review(code=request.code, language=request.language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/coder/debug")
async def debug_code(request: DebugRequest):
    """Debug code given an error and return a fix."""
    try:
        return await _coder.debug(
            code=request.code,
            error=request.error,
            language=request.language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Task Planner ─────────────────────────────────────────────────────────────

class TripRequest(BaseModel):
    destination: str
    duration_days: int = Field(default=5, ge=1, le=30)
    budget: float = Field(default=2000.0, ge=0)
    interests: list[str] = []
    departure_city: str = ""


class ProjectRequest(BaseModel):
    project_name: str
    description: str
    deadline: str = ""
    team_size: int = Field(default=1, ge=1)
    budget: float | None = None


class ScheduleRequest(BaseModel):
    goals: list[str]
    available_hours_per_day: float = Field(default=8.0, ge=1.0, le=24.0)
    schedule_type: str = "weekly"
    constraints: list[str] = []


class GenericPlanRequest(BaseModel):
    goal: str
    context: str = ""


@router.post("/planner/trip")
async def plan_trip(request: TripRequest):
    """Generate a detailed trip itinerary."""
    try:
        return await _task_planner.plan_trip(
            destination=request.destination,
            duration_days=request.duration_days,
            budget=request.budget,
            interests=request.interests,
            departure_city=request.departure_city,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/planner/project")
async def plan_project(request: ProjectRequest):
    """Generate a structured project plan with WBS and risk register."""
    try:
        return await _task_planner.plan_project(
            project_name=request.project_name,
            description=request.description,
            deadline=request.deadline,
            team_size=request.team_size,
            budget=request.budget,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/planner/schedule")
async def plan_schedule(request: ScheduleRequest):
    """Generate an optimised productivity schedule."""
    if not request.goals:
        raise HTTPException(status_code=400, detail="At least one goal is required")
    try:
        return await _task_planner.plan_schedule(
            goals=request.goals,
            available_hours_per_day=request.available_hours_per_day,
            schedule_type=request.schedule_type,
            constraints=request.constraints,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/planner/generic")
async def plan_generic(request: GenericPlanRequest):
    """Generic structured planning for any goal."""
    try:
        return await _task_planner.plan_generic(
            goal=request.goal,
            context=request.context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
