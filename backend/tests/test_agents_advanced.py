"""
BrahmaAI Specialised Agent Tests
Tests for Researcher, Coder, and Task Planner agents.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─── Researcher Agent Tests ───────────────────────────────────────────────────

class TestResearcherAgent:

    @pytest.mark.asyncio
    async def test_research_returns_report(self):
        from backend.agents.researcher import ResearcherAgent
        agent = ResearcherAgent()

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(side_effect=[
            '["AI trends 2025", "latest machine learning", "LLM developments"]',  # query expansion
            "## Research Report\n\nKey findings about AI trends...",               # synthesis
        ])
        mock_llm.parse_json = MagicMock(side_effect=lambda t: json.loads(t))
        agent.llm = mock_llm

        # Mock tools
        mock_registry = MagicMock()
        mock_registry.has_tool.return_value = False  # Skip actual tool calls
        agent.registry = mock_registry

        result = await agent.research(query="AI trends 2025", depth=2)
        assert result["status"] == "success"
        assert "report" in result
        assert result["query"] == "AI trends 2025"

    @pytest.mark.asyncio
    async def test_query_expansion_fallback(self):
        from backend.agents.researcher import ResearcherAgent
        agent = ResearcherAgent()

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value="not valid json {{{")
        mock_llm.parse_json = MagicMock(side_effect=json.JSONDecodeError("", "", 0))
        agent.llm = mock_llm

        queries = await agent._expand_query("test query", 3)
        # Should fall back to original query
        assert queries == ["test query"]

    @pytest.mark.asyncio
    async def test_format_sources_with_empty_data(self):
        from backend.agents.researcher import ResearcherAgent
        agent = ResearcherAgent()
        result = agent._format_sources([], [])
        assert "No sources" in result

    @pytest.mark.asyncio
    async def test_format_sources_includes_titles(self):
        from backend.agents.researcher import ResearcherAgent
        agent = ResearcherAgent()
        search_results = [
            {"title": "OpenAI Blog", "url": "https://openai.com", "snippet": "Latest AI news"},
        ]
        result = agent._format_sources(search_results, [])
        assert "OpenAI Blog" in result
        assert "https://openai.com" in result


# ─── Coder Agent Tests ────────────────────────────────────────────────────────

class TestCoderAgent:

    @pytest.mark.asyncio
    async def test_generate_code_returns_code(self):
        from backend.agents.coder import CoderAgent
        agent = CoderAgent()

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(side_effect=[
            "```python\ndef add(a, b):\n    return a + b\n```",  # code gen
            "This function adds two numbers.",                   # explanation
        ])
        agent.llm = mock_llm

        # Skip code execution
        mock_registry = MagicMock()
        mock_registry.has_tool.return_value = False
        agent.registry = mock_registry

        result = await agent.generate(description="write an add function", language="python", test=False)
        assert result["status"] == "success"
        assert "code" in result
        assert "def add" in result["code"]

    @pytest.mark.asyncio
    async def test_generate_with_test_and_fix(self):
        from backend.agents.coder import CoderAgent
        agent = CoderAgent()

        # First code has error, second is fixed
        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(side_effect=[
            "```python\nprint(undefined_var)\n```",        # initial broken code
            "```python\nprint('hello world')\n```",        # fixed code
            "This prints hello world.",                    # explanation
        ])
        agent.llm = mock_llm

        mock_tool = AsyncMock()
        mock_tool.execute = AsyncMock(side_effect=[
            {"status": "error", "error": "NameError: name 'undefined_var' is not defined"},
            {"status": "success", "output": "hello world"},
        ])
        mock_registry = MagicMock()
        mock_registry.has_tool.return_value = True
        mock_registry.get_tool.return_value = mock_tool
        agent.registry = mock_registry

        result = await agent.generate(
            description="print hello world",
            language="python",
            test=True,
            max_iterations=2,
        )
        assert result["status"] == "success"
        assert result["test_result"]["status"] == "success"

    @pytest.mark.asyncio
    async def test_review_returns_feedback(self):
        from backend.agents.coder import CoderAgent
        agent = CoderAgent()

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value="## Code Review\n\nScore: 8/10\nLooks good!")
        agent.llm = mock_llm

        result = await agent.review(code="x = 1 + 2\nprint(x)", language="python")
        assert result["status"] == "success"
        assert "review" in result
        assert "8/10" in result["review"]

    @pytest.mark.asyncio
    async def test_debug_returns_fix(self):
        from backend.agents.coder import CoderAgent
        agent = CoderAgent()

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value=(
            "**Root Cause:** NameError\n"
            "**Fix:**\n```python\nx = 'hello'\nprint(x)\n```\n"
            "**What Changed:** Added variable definition"
        ))
        agent.llm = mock_llm

        result = await agent.debug(
            code="print(x)",
            error="NameError: name 'x' is not defined",
            language="python",
        )
        assert result["status"] == "success"
        assert "fixed" in result
        assert "explanation" in result

    def test_extract_code_block_from_markdown(self):
        from backend.agents.coder import CoderAgent
        agent = CoderAgent()
        text = "Here is the code:\n```python\ndef hello():\n    print('hi')\n```\nEnd."
        code = agent._extract_code_block(text)
        assert code == "def hello():\n    print('hi')"

    def test_extract_code_block_returns_none_if_missing(self):
        from backend.agents.coder import CoderAgent
        agent = CoderAgent()
        code = agent._extract_code_block("No code block here, just text.")
        assert code is None


# ─── Task Planner Agent Tests ─────────────────────────────────────────────────

class TestTaskPlannerAgent:

    @pytest.mark.asyncio
    async def test_plan_trip_returns_itinerary(self):
        from backend.agents.task_planner import TaskPlannerAgent
        agent = TaskPlannerAgent()

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value=(
            "## 5-Day Tokyo Itinerary\n\n"
            "### Day 1: Asakusa & Ueno\n"
            "- Morning: Senso-ji Temple\n"
            "- Afternoon: Ueno Park\n\n"
            "## Budget: $2000 total"
        ))
        agent.llm = mock_llm

        result = await agent.plan_trip(
            destination="Tokyo",
            duration_days=5,
            budget=2000,
            interests=["culture", "food"],
        )
        assert result["status"] == "success"
        assert result["type"] == "trip"
        assert result["destination"] == "Tokyo"
        assert "Tokyo" in result["plan"]

    @pytest.mark.asyncio
    async def test_plan_project_returns_wbs(self):
        from backend.agents.task_planner import TaskPlannerAgent
        agent = TaskPlannerAgent()

        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value=(
            "## Project Plan: BrahmaAI\n\n"
            "### Phase 1: Foundation (2 weeks)\n"
            "- Backend setup\n- Database schema\n\n"
            "### Risk Register\n| Risk | Likelihood |\n|---|---|\n"
        ))
        agent.llm = mock_llm

        result = await agent.plan_project(
            project_name="BrahmaAI",
            description="Build an AI assistant",
            team_size=3,
        )
        assert result["status"] == "success"
        assert result["type"] == "project"
        assert result["name"] == "BrahmaAI"

    @pytest.mark.asyncio
    async def test_plan_schedule_requires_goals(self):
        from backend.agents.task_planner import TaskPlannerAgent
        agent = TaskPlannerAgent()
        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value="## Weekly Schedule\n\n- 9am: Deep work")
        agent.llm = mock_llm

        result = await agent.plan_schedule(
            goals=["Ship MVP", "Exercise daily"],
            available_hours_per_day=8,
        )
        assert result["status"] == "success"
        assert result["type"] == "schedule"
        assert len(result["goals"]) == 2

    @pytest.mark.asyncio
    async def test_generic_plan(self):
        from backend.agents.task_planner import TaskPlannerAgent
        agent = TaskPlannerAgent()
        mock_llm = MagicMock()
        mock_llm.complete = AsyncMock(return_value="## Plan\n\n1. Step one\n2. Step two")
        agent.llm = mock_llm

        result = await agent.plan_generic(goal="Learn Rust in 30 days")
        assert result["status"] == "success"
        assert result["type"] == "generic"


# ─── Specialised Agent API Tests ─────────────────────────────────────────────

class TestAgentEndpoints:

    @pytest.mark.asyncio
    async def test_coder_generate_endpoint(self):
        from backend.main import app
        from httpx import AsyncClient, ASGITransport

        with patch("backend.agents.coder.get_llm_client") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.complete = AsyncMock(side_effect=[
                "```python\nprint('hello')\n```",
                "Prints hello.",
            ])
            mock_get_llm.return_value = mock_llm

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/agents/coder/generate", json={
                    "description": "print hello world",
                    "language": "python",
                    "test": False,
                })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "code" in data

    @pytest.mark.asyncio
    async def test_planner_trip_endpoint(self):
        from backend.main import app
        from httpx import AsyncClient, ASGITransport

        with patch("backend.agents.task_planner.get_llm_client") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.complete = AsyncMock(return_value="## Tokyo Trip\n\nDay 1: ...")
            mock_get_llm.return_value = mock_llm

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/agents/planner/trip", json={
                    "destination": "Tokyo",
                    "duration_days": 3,
                    "budget": 1500,
                })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["destination"] == "Tokyo"

    @pytest.mark.asyncio
    async def test_planner_schedule_endpoint(self):
        from backend.main import app
        from httpx import AsyncClient, ASGITransport

        with patch("backend.agents.task_planner.get_llm_client") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.complete = AsyncMock(return_value="## Weekly Schedule...")
            mock_get_llm.return_value = mock_llm

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/agents/planner/schedule", json={
                    "goals": ["Exercise", "Code"],
                    "available_hours_per_day": 6,
                })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    @pytest.mark.asyncio
    async def test_coder_empty_description_returns_400(self):
        from backend.main import app
        from httpx import AsyncClient, ASGITransport

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/agents/coder/generate", json={
                "description": "   ",
                "language": "python",
            })

        assert response.status_code == 400
