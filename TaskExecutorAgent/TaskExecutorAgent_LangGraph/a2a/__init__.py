"""A2A external communication adapter for the LangGraph task executor.

This package intentionally sits outside the internal LangGraph orchestration.
The existing GraphState workflow remains the source of truth for agent-to-agent
handoff inside this application.
"""

from .registry import get_agent_card
from .server import run_a2a_server

__all__ = ["get_agent_card", "run_a2a_server"]
