"""Lightweight A2A-style request/response schemas.

These models provide a stable external contract without changing the internal
LangGraph GraphState orchestration.
"""

from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class A2ATaskRequest(BaseModel):
    """External request for this agent workflow to perform a task."""

    task: str = Field(..., min_length=1, description="Task for the LangGraph workflow")
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    sender: str | None = Field(default=None, description="Calling agent identity")
    metadata: dict[str, Any] = Field(default_factory=dict)


class A2ATaskResponse(BaseModel):
    """External response returned after the internal graph completes."""

    request_id: str
    status: Literal["completed", "failed"]
    agent: str = "task-executor-langgraph"
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class AgentSkill(BaseModel):
    """Capability advertised by this agent."""

    name: str
    description: str
    input_schema: dict[str, Any]


class AgentCard(BaseModel):
    """Discovery metadata for external A2A clients."""

    name: str
    description: str
    version: str
    protocol: str
    endpoints: dict[str, str]
    skills: list[AgentSkill]
