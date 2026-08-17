"""Google A2A SDK-backed discovery metadata for the task executor agent."""

from __future__ import annotations

from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentProvider, AgentSkill


def get_agent_card(base_url: str = "http://127.0.0.1:8080") -> AgentCard:
    """Return this agent's externally visible capabilities using a2a-sdk models."""

    return AgentCard(
        name="task-executor-langgraph",
        description=(
            "External A2A adapter for a LangGraph AI SDLC workflow. "
            "Internally uses GraphState orchestration: planner, coding, review, "
            "reflection/recode, and evaluation."
        ),
        supported_interfaces=[
            AgentInterface(
                url=f"{base_url}/a2a/tasks",
                protocol_binding="HTTP+JSON",
                protocol_version="0.3.0",
            )
        ],
        provider=AgentProvider(
            organization="Agent Bootcamp",
            url="https://github.com/aditya-kumar666/Agent-bootcamp",
        ),
        version="0.1.0",
        documentation_url=f"{base_url}/.well-known/agent.json",
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=False,
        ),
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="execute_sdlc_task",
                name="execute_sdlc_task",
                description="Plan, implement, review, and evaluate a software development task.",
                tags=["software-development", "planning", "coding", "review", "evaluation"],
                examples=["Build a REST API endpoint and include tests."],
                input_modes=["text/plain", "application/json"],
                output_modes=["application/json"],
            )
        ],
    )
