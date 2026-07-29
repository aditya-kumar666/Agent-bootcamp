"""A2A discovery metadata for the task executor agent."""

from __future__ import annotations

from .schemas import AgentCard, AgentSkill


def get_agent_card() -> AgentCard:
    """Return this agent's externally visible capabilities."""

    return AgentCard(
        name="task-executor-langgraph",
        description=(
            "External A2A adapter for a LangGraph AI SDLC workflow. "
            "Internally uses GraphState orchestration: planner, coding, review, "
            "reflection/recode, and evaluation."
        ),
        version="0.1.0",
        protocol="a2a-http-json",
        endpoints={
            "agent_card": "GET /.well-known/agent.json",
            "execute_task": "POST /a2a/tasks",
            "health": "GET /health",
        },
        skills=[
            AgentSkill(
                name="execute_sdlc_task",
                description="Plan, implement, review, and evaluate a software development task.",
                input_schema={
                    "type": "object",
                    "required": ["task"],
                    "properties": {
                        "task": {"type": "string", "minLength": 1},
                        "request_id": {"type": "string"},
                        "sender": {"type": "string"},
                        "metadata": {"type": "object"},
                    },
                },
            )
        ],
    )
