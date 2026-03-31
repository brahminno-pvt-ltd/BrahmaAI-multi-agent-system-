"""
BrahmaAI Orchestrator Integration Test
Tests the full agent loop end-to-end with mocked LLM.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_planner_response():
    return json.dumps({
        "goal": "Test the orchestrator",
        "reasoning": "Run a simple test",
        "estimated_steps": 1,
        "steps": [
            {
                "id": "step_1",
                "description": "Execute a test",
                "tool": "code_executor",
                "tool_args": {"code": "print('orchestrator test')"},
                "depends_on": [],
                "expected_output": "test output",
            }
        ],
    })


@pytest.fixture
def mock_critic_response():
    return json.dumps({
        "quality_score": 9,
        "completeness": "Excellent",
        "issues": [],
        "improvements": [],
        "should_replan": False,
        "reason": "Task completed perfectly",
    })


class TestOrchestrator:
    @pytest.mark.asyncio
    async def test_full_loop_emits_all_phase_events(
        self, mock_planner_response, mock_critic_response
    ):
        from backend.core.orchestrator import Orchestrator

        with patch("backend.agents.planner.get_llm_client") as mock_planner_llm, \
             patch("backend.agents.critic.get_llm_client") as mock_critic_llm, \
             patch("backend.agents.executor.get_llm_client") as mock_executor_llm:

            # Setup planner mock
            planner_client = MagicMock()
            planner_client.complete = AsyncMock(return_value=mock_planner_response)
            planner_client.parse_json = MagicMock(side_effect=lambda t: json.loads(t))
            mock_planner_llm.return_value = planner_client

            # Setup critic mock
            critic_client = MagicMock()
            critic_client.complete = AsyncMock(return_value=mock_critic_response)
            critic_client.parse_json = MagicMock(side_effect=lambda t: json.loads(t))
            mock_critic_llm.return_value = critic_client

            # Setup executor mock
            executor_client = MagicMock()
            executor_client.complete = AsyncMock(return_value="Final synthesized answer")
            executor_client.parse_json = MagicMock(side_effect=lambda t: json.loads(t))
            mock_executor_llm.return_value = executor_client

            orchestrator = Orchestrator()
            events = []

            async for event in orchestrator.run_task(
                goal="Test the orchestrator",
                session_id="test-session",
            ):
                events.append(event)

        # Check all phases emitted
        event_types = {e["event"] for e in events}
        assert "memory_retrieval" in event_types
        assert "planning" in event_types
        assert "reflection" in event_types
        assert "complete" in event_types

    @pytest.mark.asyncio
    async def test_orchestrator_stores_in_short_term_memory(
        self, mock_planner_response, mock_critic_response
    ):
        from backend.core.orchestrator import Orchestrator
        from backend.memory.short_term import ShortTermMemory

        with patch("backend.agents.planner.get_llm_client") as mock_planner_llm, \
             patch("backend.agents.critic.get_llm_client") as mock_critic_llm, \
             patch("backend.agents.executor.get_llm_client") as mock_executor_llm:

            for mock in [mock_planner_llm, mock_critic_llm, mock_executor_llm]:
                client = MagicMock()
                client.complete = AsyncMock(side_effect=[
                    mock_planner_response, mock_critic_response, "Final answer"
                ])
                client.parse_json = MagicMock(side_effect=lambda t: json.loads(t))
                mock.return_value = client

            session_id = "memory-test-session"
            orchestrator = Orchestrator()
            orchestrator.short_term.add_message(session_id, "user", "Test goal")

            async for _ in orchestrator.run_task(
                goal="Test goal",
                session_id=session_id,
            ):
                pass

            history = orchestrator.short_term.get_context(session_id)
            assert len(history) >= 1

    @pytest.mark.asyncio
    async def test_event_structure_is_valid(self, mock_planner_response, mock_critic_response):
        from backend.core.orchestrator import Orchestrator

        with patch("backend.agents.planner.get_llm_client") as mock_planner_llm, \
             patch("backend.agents.critic.get_llm_client") as mock_critic_llm, \
             patch("backend.agents.executor.get_llm_client") as mock_executor_llm:

            for mock in [mock_planner_llm, mock_critic_llm, mock_executor_llm]:
                client = MagicMock()
                client.complete = AsyncMock(side_effect=[
                    mock_planner_response, mock_critic_response, "Final answer"
                ])
                client.parse_json = MagicMock(side_effect=lambda t: json.loads(t))
                mock.return_value = client

            orchestrator = Orchestrator()
            async for event in orchestrator.run_task(goal="test", session_id="ev-test"):
                assert "event" in event, f"Missing 'event' key: {event}"
                assert "timestamp" in event, f"Missing 'timestamp' key: {event}"
                assert "data" in event, f"Missing 'data' key: {event}"
                assert isinstance(event["timestamp"], float), "timestamp must be float"
                assert isinstance(event["data"], dict), "data must be dict"
