"""
BrahmaAI Backend Tests
Covers: agents, tools, memory, API endpoints, orchestrator
"""

import asyncio
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_client():
    """Return a mock LLM client that yields predictable JSON."""
    client = MagicMock()
    client.complete = AsyncMock(return_value=json.dumps({
        "goal": "test goal",
        "reasoning": "test reasoning",
        "estimated_steps": 2,
        "steps": [
            {
                "id": "step_1",
                "description": "Search for information",
                "tool": "web_search",
                "tool_args": {"query": "test query"},
                "depends_on": [],
                "expected_output": "search results",
            },
            {
                "id": "step_2",
                "description": "Synthesize results",
                "tool": None,
                "tool_args": {},
                "depends_on": ["step_1"],
                "expected_output": "summary",
            },
        ],
    }))
    client.parse_json = MagicMock(side_effect=lambda t: json.loads(t))
    return client


@pytest.fixture
def mock_tool_registry():
    """Return a registry with a mock web_search tool."""
    from backend.tools.registry import ToolRegistry, BaseTool

    class MockWebSearchTool(BaseTool):
        name = "web_search"
        description = "Mock search"
        args = {"query": "str"}

        async def execute(self, query: str, **kwargs):
            return {
                "status": "success",
                "query": query,
                "output": f"Mock results for: {query}",
                "results": [{"title": "Result 1", "url": "https://example.com", "snippet": "Test"}],
            }

    registry = ToolRegistry()
    registry.register_class(MockWebSearchTool)
    return registry


# ─── Tool Tests ───────────────────────────────────────────────────────────────

class TestWebSearchTool:
    @pytest.mark.asyncio
    async def test_mock_search_returns_results(self):
        from backend.tools.web_search import WebSearchTool
        tool = WebSearchTool()
        result = tool._mock_search("artificial intelligence", 3)
        assert result["status"] == "success"
        assert result["query"] == "artificial intelligence"
        assert len(result["results"]) == 3
        assert "output" in result

    @pytest.mark.asyncio
    async def test_execute_falls_back_to_mock(self):
        from backend.tools.web_search import WebSearchTool
        tool = WebSearchTool()
        # No API keys set — should return mock results
        with patch("backend.tools.web_search.settings") as mock_settings:
            mock_settings.SERPAPI_KEY = ""
            result = await tool.execute(query="test query", num_results=3)
        assert result["status"] == "success"
        assert "query" in result


class TestCodeExecutorTool:
    @pytest.mark.asyncio
    async def test_safe_code_executes(self):
        from backend.tools.code_executor import CodeExecutorTool
        tool = CodeExecutorTool()
        result = await tool.execute(code="print(2 + 2)", timeout=10)
        assert result["status"] == "success"
        assert "4" in result["output"]

    @pytest.mark.asyncio
    async def test_blocked_code_returns_blocked_status(self):
        from backend.tools.code_executor import CodeExecutorTool
        tool = CodeExecutorTool()
        result = await tool.execute(code="import os; os.system('ls')", timeout=10)
        assert result["status"] == "blocked"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_syntax_error_returns_error_status(self):
        from backend.tools.code_executor import CodeExecutorTool
        tool = CodeExecutorTool()
        result = await tool.execute(code="def broken(:\n  pass", timeout=10)
        assert result["status"] in ("error", "blocked")

    def test_safety_check_passes_for_safe_code(self):
        from backend.tools.code_executor import CodeExecutorTool
        tool = CodeExecutorTool()
        check = tool._check_safety("x = 1 + 2\nprint(x)")
        assert check["safe"] is True

    def test_safety_check_blocks_import_os(self):
        from backend.tools.code_executor import CodeExecutorTool
        tool = CodeExecutorTool()
        check = tool._check_safety("import os\nos.listdir('.')")
        assert check["safe"] is False


class TestFileReaderTool:
    @pytest.mark.asyncio
    async def test_file_not_found_returns_error(self):
        from backend.tools.file_reader import FileReaderTool
        tool = FileReaderTool()
        result = await tool.execute(file_path="/nonexistent/file.txt")
        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_reads_txt_file(self, tmp_path):
        from backend.tools.file_reader import FileReaderTool
        f = tmp_path / "test.txt"
        f.write_text("Hello, BrahmaAI!")
        tool = FileReaderTool()
        result = await tool.execute(file_path=str(f))
        assert result["status"] == "success"
        assert "Hello, BrahmaAI!" in result["output"]

    @pytest.mark.asyncio
    async def test_reads_csv_file(self, tmp_path):
        from backend.tools.file_reader import FileReaderTool
        f = tmp_path / "data.csv"
        f.write_text("name,age\nAlice,30\nBob,25")
        tool = FileReaderTool()
        result = await tool.execute(file_path=str(f))
        assert result["status"] == "success"
        assert "Alice" in result["output"]

    @pytest.mark.asyncio
    async def test_unsupported_extension_returns_error(self, tmp_path):
        from backend.tools.file_reader import FileReaderTool
        f = tmp_path / "file.docx"
        f.write_bytes(b"fake docx content")
        tool = FileReaderTool()
        result = await tool.execute(file_path=str(f))
        assert result["status"] == "error"


class TestEmailTool:
    @pytest.mark.asyncio
    async def test_send_email_returns_success(self):
        from backend.tools.email_tool import EmailTool
        tool = EmailTool()
        result = await tool.execute(
            to="test@example.com",
            subject="Test Subject",
            body="Test body content",
        )
        assert result["status"] == "success"
        assert "email_id" in result
        assert "test@example.com" in result["output"]

    @pytest.mark.asyncio
    async def test_sent_emails_are_stored(self):
        from backend.tools.email_tool import EmailTool
        EmailTool._sent_emails.clear()
        tool = EmailTool()
        await tool.execute(to="a@b.com", subject="S", body="B")
        await tool.execute(to="c@d.com", subject="S2", body="B2")
        sent = EmailTool.get_sent_emails()
        assert len(sent) >= 2


class TestCalendarTool:
    @pytest.mark.asyncio
    async def test_create_event(self):
        from backend.tools.calendar_tool import CalendarTool
        CalendarTool._events.clear()
        tool = CalendarTool()
        result = await tool.execute(
            action="create",
            title="Team Meeting",
            date="2025-08-01",
            time="10:00",
            duration_minutes=60,
        )
        assert result["status"] == "success"
        assert "event_id" in result

    @pytest.mark.asyncio
    async def test_list_events(self):
        from backend.tools.calendar_tool import CalendarTool
        CalendarTool._events.clear()
        tool = CalendarTool()
        await tool.execute(action="create", title="Event A", date="2025-08-01")
        result = await tool.execute(action="list")
        assert result["status"] == "success"
        assert len(result["events"]) >= 1

    @pytest.mark.asyncio
    async def test_delete_event(self):
        from backend.tools.calendar_tool import CalendarTool
        CalendarTool._events.clear()
        tool = CalendarTool()
        create = await tool.execute(action="create", title="Delete Me", date="2025-08-01")
        event_id = create["event_id"]
        delete = await tool.execute(action="delete", event_id=event_id)
        assert delete["status"] == "success"

    @pytest.mark.asyncio
    async def test_unknown_action_returns_error(self):
        from backend.tools.calendar_tool import CalendarTool
        tool = CalendarTool()
        result = await tool.execute(action="fly_to_moon")
        assert result["status"] == "error"


# ─── Tool Registry Tests ──────────────────────────────────────────────────────

class TestToolRegistry:
    def test_register_and_retrieve_tool(self):
        from backend.tools.registry import ToolRegistry, BaseTool

        class DummyTool(BaseTool):
            name = "dummy"
            description = "A dummy tool"
            args = {}
            async def execute(self, **kwargs): return {"status": "success"}

        registry = ToolRegistry()
        registry.register_class(DummyTool)
        assert registry.has_tool("dummy")
        tool = registry.get_tool("dummy")
        assert tool.name == "dummy"

    def test_list_tools_returns_all(self):
        from backend.tools.registry import ToolRegistry, BaseTool

        class ToolA(BaseTool):
            name = "tool_a"; description = "A"; args = {}
            async def execute(self, **kwargs): return {}

        class ToolB(BaseTool):
            name = "tool_b"; description = "B"; args = {}
            async def execute(self, **kwargs): return {}

        registry = ToolRegistry()
        registry.register_class(ToolA)
        registry.register_class(ToolB)
        tools = registry.list_tools()
        assert "tool_a" in tools
        assert "tool_b" in tools

    def test_get_nonexistent_tool_raises(self):
        from backend.tools.registry import ToolRegistry
        registry = ToolRegistry()
        with pytest.raises(KeyError):
            registry.get_tool("nonexistent_tool")


# ─── Memory Tests ─────────────────────────────────────────────────────────────

class TestShortTermMemory:
    def test_add_and_retrieve_message(self):
        from backend.memory.short_term import ShortTermMemory
        mem = ShortTermMemory()
        mem.add_message("sess1", "user", "Hello there")
        mem.add_message("sess1", "assistant", "Hi!")
        ctx = mem.get_context("sess1")
        assert len(ctx) == 2
        assert ctx[0]["content"] == "Hello there"
        assert ctx[1]["role"] == "assistant"

    def test_different_sessions_isolated(self):
        from backend.memory.short_term import ShortTermMemory
        mem = ShortTermMemory()
        mem.add_message("sess_a", "user", "Message A")
        mem.add_message("sess_b", "user", "Message B")
        assert len(mem.get_context("sess_a")) == 1
        assert len(mem.get_context("sess_b")) == 1
        assert mem.get_context("sess_a")[0]["content"] == "Message A"

    def test_clear_session(self):
        from backend.memory.short_term import ShortTermMemory
        mem = ShortTermMemory()
        mem.add_message("sess_clear", "user", "test")
        mem.clear_session("sess_clear")
        assert mem.get_context("sess_clear") == []

    def test_pruning_at_max_messages(self):
        from backend.memory.short_term import ShortTermMemory
        mem = ShortTermMemory()
        mem._max_messages = 5
        for i in range(10):
            mem.add_message("sess_prune", "user", f"Message {i}")
        ctx = mem.get_context("sess_prune")
        assert len(ctx) <= 5

    def test_session_summary(self):
        from backend.memory.short_term import ShortTermMemory
        mem = ShortTermMemory()
        mem.add_message("sess_sum", "user", "test")
        summary = mem.session_summary("sess_sum")
        assert summary["session_id"] == "sess_sum"
        assert summary["message_count"] == 1


class TestLongTermMemory:
    @pytest.mark.asyncio
    async def test_store_and_retrieve_with_keyword_fallback(self):
        from backend.memory.long_term import LongTermMemory
        mem = LongTermMemory()
        # Ensure we use fallback mode
        mem._use_faiss = False

        await mem.store("The quick brown fox jumps", {"source": "test"})
        await mem.store("Python is a programming language", {"source": "test"})

        results = await mem.retrieve("fox jumping quickly")
        assert len(results) > 0
        assert any("fox" in r["text"] for r in results)

    @pytest.mark.asyncio
    async def test_list_recent_returns_latest(self):
        from backend.memory.long_term import LongTermMemory
        mem = LongTermMemory()
        mem._use_faiss = False
        mem._fallback_store.clear()

        await mem.store("First memory")
        await mem.store("Second memory")
        await mem.store("Third memory")

        recent = await mem.list_recent(limit=2)
        assert len(recent) == 2

    @pytest.mark.asyncio
    async def test_delete_removes_memory(self):
        from backend.memory.long_term import LongTermMemory
        mem = LongTermMemory()
        mem._use_faiss = False

        mem_id = await mem.store("Delete me")
        assert any(m["id"] == mem_id for m in mem._fallback_store)

        deleted = await mem.delete(mem_id)
        assert deleted is True
        assert not any(m["id"] == mem_id for m in mem._fallback_store)

    @pytest.mark.asyncio
    async def test_retrieve_empty_store_returns_empty(self):
        from backend.memory.long_term import LongTermMemory
        mem = LongTermMemory()
        mem._use_faiss = False
        mem._fallback_store.clear()
        results = await mem.retrieve("anything")
        assert results == []


# ─── Agent Tests ─────────────────────────────────────────────────────────────

class TestPlannerAgent:
    @pytest.mark.asyncio
    async def test_plan_returns_valid_structure(self, mock_llm_client, mock_tool_registry):
        from backend.agents.planner import PlannerAgent
        agent = PlannerAgent()
        agent.llm = mock_llm_client
        agent.tool_registry = mock_tool_registry

        plan = await agent.plan(goal="Search for AI news")
        assert "goal" in plan
        assert "steps" in plan
        assert isinstance(plan["steps"], list)
        assert len(plan["steps"]) >= 1

    @pytest.mark.asyncio
    async def test_plan_with_memory_context(self, mock_llm_client, mock_tool_registry):
        from backend.agents.planner import PlannerAgent
        agent = PlannerAgent()
        agent.llm = mock_llm_client
        agent.tool_registry = mock_tool_registry

        memory = [{"text": "User likes concise answers", "score": 0.9}]
        plan = await agent.plan(goal="Summarize AI trends", memory_context=memory)
        assert plan is not None
        assert "steps" in plan

    def test_validate_plan_raises_on_missing_steps(self):
        from backend.agents.planner import PlannerAgent
        agent = PlannerAgent()
        with pytest.raises(ValueError, match="steps"):
            agent._validate_plan({"goal": "test"})  # missing steps

    def test_validate_plan_raises_on_empty_steps(self):
        from backend.agents.planner import PlannerAgent
        agent = PlannerAgent()
        with pytest.raises(ValueError):
            agent._validate_plan({"goal": "test", "steps": []})


class TestExecutorAgent:
    @pytest.mark.asyncio
    async def test_execute_step_with_tool(self, mock_tool_registry, mock_llm_client):
        from backend.agents.executor import ExecutorAgent
        agent = ExecutorAgent()
        agent.llm = mock_llm_client
        agent.tool_registry = mock_tool_registry

        step = {
            "id": "step_1",
            "description": "Search for AI news",
            "tool": "web_search",
            "tool_args": {"query": "AI news 2025"},
        }
        result = await agent.execute_step(step=step, context=[])
        assert result["status"] == "success"
        assert result["step_id"] == "step_1"
        assert "tool_result" in result

    @pytest.mark.asyncio
    async def test_execute_step_without_tool_uses_llm(self, mock_tool_registry, mock_llm_client):
        from backend.agents.executor import ExecutorAgent
        agent = ExecutorAgent()
        agent.llm = mock_llm_client
        agent.tool_registry = mock_tool_registry

        mock_llm_client.complete = AsyncMock(return_value="LLM reasoning output")

        step = {
            "id": "step_2",
            "description": "Analyze the results",
            "tool": None,
            "tool_args": {},
        }
        result = await agent.execute_step(step=step, context=[])
        assert result["step_id"] == "step_2"
        assert "tool_result" in result

    @pytest.mark.asyncio
    async def test_synthesize_returns_summary(self, mock_llm_client, mock_tool_registry):
        from backend.agents.executor import ExecutorAgent
        agent = ExecutorAgent()
        agent.llm = mock_llm_client
        mock_llm_client.complete = AsyncMock(return_value="Final summary text")

        result = await agent.synthesize(
            goal="Find AI trends",
            results=[{"step": {"description": "search"}, "result": {"tool_result": {"output": "results"}}}],
            reflection={"completeness": "Good", "quality_score": 8},
        )
        assert "summary" in result
        assert result["goal"] == "Find AI trends"


class TestCriticAgent:
    @pytest.mark.asyncio
    async def test_reflect_returns_valid_structure(self, mock_llm_client):
        from backend.agents.critic import CriticAgent
        agent = CriticAgent()

        mock_llm_client.complete = AsyncMock(return_value=json.dumps({
            "quality_score": 8,
            "completeness": "Good results",
            "issues": [],
            "improvements": ["Add more sources"],
            "should_replan": False,
            "reason": "Results are satisfactory",
        }))
        mock_llm_client.parse_json = MagicMock(side_effect=lambda t: json.loads(t))
        agent.llm = mock_llm_client

        plan = {"steps": [{"id": "s1", "description": "search", "tool": "web_search"}]}
        results = [{"step": plan["steps"][0], "result": {"status": "success", "tool_result": {"output": "data"}}}]

        reflection = await agent.reflect(goal="Find AI news", plan=plan, results=results)
        assert "quality_score" in reflection
        assert "should_replan" in reflection
        assert isinstance(reflection["quality_score"], int)

    @pytest.mark.asyncio
    async def test_reflect_recommends_replan_on_low_score(self, mock_llm_client):
        from backend.agents.critic import CriticAgent
        agent = CriticAgent()

        mock_llm_client.complete = AsyncMock(return_value=json.dumps({
            "quality_score": 3,
            "completeness": "Insufficient",
            "issues": ["Missing data"],
            "improvements": ["Search more"],
            "should_replan": True,
            "reason": "Quality too low",
            "revised_goal": "Better goal",
        }))
        mock_llm_client.parse_json = MagicMock(side_effect=lambda t: json.loads(t))
        agent.llm = mock_llm_client

        reflection = await agent.reflect(
            goal="test",
            plan={"steps": []},
            results=[],
        )
        assert reflection["should_replan"] is True
        assert reflection["quality_score"] < 7


# ─── API Tests ────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_returns_ok(self):
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(self):
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/auth/login", json={
                "username": "demo",
                "password": "demo",
            })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["username"] == "demo"

    @pytest.mark.asyncio
    async def test_login_with_invalid_credentials(self):
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/auth/login", json={
                "username": "admin",
                "password": "wrongpassword",
            })
        assert response.status_code == 401


class TestToolsEndpoints:
    @pytest.mark.asyncio
    async def test_list_tools_returns_all(self):
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/tools/list")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) >= 6  # All 6 default tools

    @pytest.mark.asyncio
    async def test_execute_code_tool_directly(self):
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/tools/execute", json={
                "tool_name": "code_executor",
                "args": {"code": "print('hello from brahmaai')"},
            })
        assert response.status_code == 200
        data = response.json()
        assert data["result"]["status"] == "success"
        assert "hello from brahmaai" in data["result"]["output"]

    @pytest.mark.asyncio
    async def test_execute_unknown_tool_returns_404(self):
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/tools/execute", json={
                "tool_name": "nonexistent_tool",
                "args": {},
            })
        assert response.status_code == 404


class TestMemoryEndpoints:
    @pytest.mark.asyncio
    async def test_store_and_list_memory(self):
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Store
            store_resp = await client.post("/api/memory/store", json={
                "text": "BrahmaAI is an autonomous multi-agent system",
                "metadata": {"source": "test"},
            })
            assert store_resp.status_code == 200

            # List
            list_resp = await client.get("/api/memory/list?limit=10")
            assert list_resp.status_code == 200
            data = list_resp.json()
            assert "memories" in data

    @pytest.mark.asyncio
    async def test_retrieve_memory(self):
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Store something first
            await client.post("/api/memory/store", json={
                "text": "Python is great for AI development",
            })
            # Retrieve
            resp = await client.post("/api/memory/retrieve", json={
                "query": "Python programming AI",
                "top_k": 3,
            })
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data


class TestTasksEndpoints:
    @pytest.mark.asyncio
    async def test_demo_tasks_endpoint(self):
        from backend.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/tasks/demo")
        assert response.status_code == 200
        data = response.json()
        assert "demo_tasks" in data
        assert len(data["demo_tasks"]) == 4

    @pytest.mark.asyncio
    async def test_plan_endpoint(self):
        from backend.main import app
        with patch("backend.agents.planner.get_llm_client") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.complete = AsyncMock(return_value=json.dumps({
                "goal": "Test goal",
                "reasoning": "testing",
                "estimated_steps": 1,
                "steps": [{"id": "s1", "description": "Do it", "tool": None, "tool_args": {}, "depends_on": [], "expected_output": "done"}],
            }))
            mock_llm.parse_json = MagicMock(side_effect=lambda t: json.loads(t))
            mock_get_llm.return_value = mock_llm

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/tasks/plan", json={"goal": "Test goal"})

        assert response.status_code == 200
        data = response.json()
        assert "plan" in data


# ─── LLM Client Tests ─────────────────────────────────────────────────────────

class TestLLMClient:
    @pytest.mark.asyncio
    async def test_mock_mode_returns_response(self):
        from backend.core.llm_client import LLMClient
        with patch("backend.core.llm_client.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = ""
            mock_settings.ANTHROPIC_API_KEY = ""
            mock_settings.LLM_PROVIDER = "openai"
            mock_settings.LLM_TEMPERATURE = 0.2
            mock_settings.LLM_MAX_TOKENS = 4096

            client = LLMClient()
            response = await client.complete(system="You are helpful", user="Hello")
            assert isinstance(response, str)
            assert len(response) > 0

    @pytest.mark.asyncio
    async def test_mock_planner_returns_json(self):
        from backend.core.llm_client import LLMClient
        with patch("backend.core.llm_client.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = ""
            mock_settings.ANTHROPIC_API_KEY = ""
            mock_settings.LLM_PROVIDER = "openai"
            mock_settings.LLM_TEMPERATURE = 0.2
            mock_settings.LLM_MAX_TOKENS = 4096

            client = LLMClient()
            response = await client.complete(
                system="You are the planner agent",
                user="Plan this: Search for AI news",
                json_mode=True,
            )
            parsed = json.loads(response)
            assert "steps" in parsed

    def test_parse_json_strips_markdown_fences(self):
        from backend.core.llm_client import LLMClient
        client = LLMClient()
        text = '```json\n{"key": "value"}\n```'
        result = client.parse_json(text)
        assert result == {"key": "value"}

    def test_parse_json_raises_on_invalid(self):
        from backend.core.llm_client import LLMClient
        client = LLMClient()
        with pytest.raises(json.JSONDecodeError):
            client.parse_json("not valid json {{{")


# ─── State Model Tests ────────────────────────────────────────────────────────

class TestStateModels:
    def test_agent_state_creation(self):
        from backend.core.state import AgentState, TaskStatus
        state = AgentState(
            task_id="t1",
            session_id="s1",
            goal="Test goal",
        )
        assert state.status == TaskStatus.PENDING
        assert state.step_results == {}
        assert state.memory_context == []

    def test_task_status_enum_values(self):
        from backend.core.state import TaskStatus
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETE == "complete"
        assert TaskStatus.FAILED == "failed"

    def test_agent_log_entry_creation(self):
        from backend.core.state import AgentLogEntry
        entry = AgentLogEntry(
            task_id="t1",
            session_id="s1",
            event="planning",
            data={"status": "start"},
        )
        assert entry.event == "planning"
        assert entry.timestamp > 0
