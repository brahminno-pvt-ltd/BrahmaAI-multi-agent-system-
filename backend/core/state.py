"""
BrahmaAI Agent State Models
Shared state objects that flow through the agent loop.
"""

from enum import Enum
from typing import Any
import time
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class PlanStep(BaseModel):
    """A single step in an agent plan."""
    id: str
    description: str
    tool: str | None = None
    tool_args: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    expected_output: str = ""


class Plan(BaseModel):
    """Structured plan output from the Planner agent."""
    goal: str
    steps: list[dict[str, Any]]
    reasoning: str
    estimated_steps: int


class AgentState(BaseModel):
    """Full state object maintained across the agent loop."""
    task_id: str
    session_id: str
    goal: str
    status: TaskStatus = TaskStatus.PENDING
    plan: dict[str, Any] | None = None
    current_step: str | None = None
    step_results: dict[str, Any] = Field(default_factory=dict)
    reflection: dict[str, Any] | None = None
    final_answer: dict[str, Any] | None = None
    memory_context: list[dict[str, Any]] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

    def update(self):
        self.updated_at = time.time()


class ToolCall(BaseModel):
    """Represents a tool invocation."""
    tool_name: str
    args: dict[str, Any]
    result: Any | None = None
    error: str | None = None
    duration_ms: float = 0.0
    called_at: float = Field(default_factory=time.time)


class AgentLogEntry(BaseModel):
    """A single observability log entry."""
    task_id: str
    session_id: str
    event: str
    data: dict[str, Any]
    timestamp: float = Field(default_factory=time.time)
