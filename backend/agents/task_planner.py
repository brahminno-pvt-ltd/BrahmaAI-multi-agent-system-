"""
BrahmaAI Task Planner Agent
Specialised agent for structured planning tasks — projects, trips, schedules.
Returns rich structured plans with timelines, budgets, and action items.
"""

import logging
from typing import Any

from backend.core.llm_client import get_llm_client

logger = logging.getLogger(__name__)

TRIP_PLANNER_SYSTEM = """You are an expert travel planner with deep knowledge of destinations worldwide.

Create a detailed, practical trip itinerary. Structure your response as follows:

## Trip Overview
- Destination, duration, total budget, best time to visit

## Day-by-Day Itinerary
For each day:
- Morning / Afternoon / Evening activities
- Specific venues/attractions with brief descriptions
- Estimated time at each location

## Budget Breakdown
| Category | Estimated Cost |
|---|---|
| Flights | $X |
| Accommodation | $X/night × N nights |
| Food | $X/day |
| Activities | $X total |
| Transport | $X |
| **Total** | **$X** |

## Practical Tips
- Visa requirements, best transport options, local customs, safety

## Booking Checklist
- [ ] Flights
- [ ] Hotels
- [ ] Key attractions (advance booking needed)

Be specific: name actual hotels, restaurants, and attractions. Give realistic prices.
"""

PROJECT_PLANNER_SYSTEM = """You are a senior project manager. Create a structured project plan.

Structure your response as:

## Project Overview
- Goal, scope, total timeline, team size needed

## Phases & Milestones
| Phase | Duration | Key Deliverables | Dependencies |
|---|---|---|---|

## Task Breakdown (WBS)
For each phase, list specific tasks with:
- Task name
- Estimated hours
- Responsible role
- Priority (High/Medium/Low)

## Risk Register
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|

## Resource Requirements
- Team roles needed
- Tools and technologies
- Budget estimate

## Success Criteria
Clear, measurable definition of done.
"""

SCHEDULE_SYSTEM = """You are a productivity coach and schedule optimizer.

Create a detailed, realistic schedule that:
1. Respects human energy patterns (deep work in morning, admin in afternoon)
2. Includes buffer time and breaks
3. Groups similar tasks together
4. Accounts for realistic task durations
5. Builds in review and planning time

Format as a structured weekly/daily schedule with time blocks.
Include:
- Time blocks with specific activities
- Energy level requirements (High/Medium/Low focus)
- Rationale for the schedule design
- Tips for sticking to the schedule
"""


class TaskPlannerAgent:
    """
    Task Planner Agent: Generates rich structured plans for trips, projects, and schedules.
    
    Unlike the generic Executor, this agent uses domain-specific prompts optimised
    for planning tasks and returns richly formatted markdown output.
    """

    def __init__(self):
        self.llm = get_llm_client()

    async def plan_trip(
        self,
        destination: str,
        duration_days: int,
        budget: float,
        interests: list[str] | None = None,
        departure_city: str = "",
    ) -> dict[str, Any]:
        """Generate a detailed trip itinerary."""
        logger.info(f"[TaskPlannerAgent] Planning trip to {destination} ({duration_days} days, ${budget})")

        interests_str = f"Interests: {', '.join(interests)}" if interests else ""
        departure_str = f"Departing from: {departure_city}" if departure_city else ""

        response = await self.llm.complete(
            system=TRIP_PLANNER_SYSTEM,
            user=(
                f"Destination: {destination}\n"
                f"Duration: {duration_days} days\n"
                f"Budget: ${budget:,.0f} USD total\n"
                f"{departure_str}\n{interests_str}\n\n"
                "Create a comprehensive trip plan."
            ),
            temperature=0.4,
        )

        return {
            "status":      "success",
            "type":        "trip",
            "destination": destination,
            "duration":    duration_days,
            "budget":      budget,
            "plan":        response,
            "output":      response,
        }

    async def plan_project(
        self,
        project_name: str,
        description: str,
        deadline: str = "",
        team_size: int = 1,
        budget: float | None = None,
    ) -> dict[str, Any]:
        """Generate a structured project plan with WBS and risk register."""
        logger.info(f"[TaskPlannerAgent] Planning project: {project_name[:60]}")

        response = await self.llm.complete(
            system=PROJECT_PLANNER_SYSTEM,
            user=(
                f"Project: {project_name}\n"
                f"Description: {description}\n"
                f"Deadline: {deadline or 'Flexible'}\n"
                f"Team Size: {team_size}\n"
                f"Budget: {'$' + str(budget) if budget else 'Not specified'}\n\n"
                "Create a comprehensive project plan."
            ),
            temperature=0.3,
        )

        return {
            "status":  "success",
            "type":    "project",
            "name":    project_name,
            "plan":    response,
            "output":  response,
        }

    async def plan_schedule(
        self,
        goals: list[str],
        available_hours_per_day: float = 8.0,
        schedule_type: str = "weekly",
        constraints: list[str] | None = None,
    ) -> dict[str, Any]:
        """Generate an optimised productivity schedule."""
        logger.info(f"[TaskPlannerAgent] Planning {schedule_type} schedule with {len(goals)} goals")

        goals_str  = "\n".join(f"- {g}" for g in goals)
        const_str  = "\n".join(f"- {c}" for c in (constraints or []))

        response = await self.llm.complete(
            system=SCHEDULE_SYSTEM,
            user=(
                f"Schedule type: {schedule_type}\n"
                f"Available hours/day: {available_hours_per_day}\n"
                f"Goals:\n{goals_str}\n"
                + (f"\nConstraints:\n{const_str}" if const_str else "") +
                "\n\nCreate a detailed, realistic schedule."
            ),
            temperature=0.3,
        )

        return {
            "status":   "success",
            "type":     "schedule",
            "goals":    goals,
            "schedule": response,
            "output":   response,
        }

    async def plan_generic(
        self,
        goal: str,
        context: str = "",
    ) -> dict[str, Any]:
        """Generic planning for any structured task."""
        logger.info(f"[TaskPlannerAgent] Generic plan: {goal[:60]}")

        response = await self.llm.complete(
            system=(
                "You are an expert planner. Create a clear, actionable, structured plan. "
                "Use markdown headers, numbered steps, tables where useful. "
                "Be specific and practical."
            ),
            user=f"Goal: {goal}\n{('Context: ' + context) if context else ''}\n\nCreate a detailed plan.",
            temperature=0.3,
        )

        return {
            "status": "success",
            "type":   "generic",
            "goal":   goal,
            "plan":   response,
            "output": response,
        }
