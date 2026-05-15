"""Base agent class for common functionality."""

import os
from abc import ABC, abstractmethod
from pathlib import Path

from langchain_openai import ChatOpenAI


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, prompts_dir: Path | None = None):
        self.prompts_dir = prompts_dir or Path(__file__).resolve().parent.parent / "prompts"
        self._llm_instance = None

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy load LLM instance."""
        if self._llm_instance is None:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self._llm_instance = ChatOpenAI(model=model, temperature=0)
        return self._llm_instance

    def read_prompt(self, filename: str) -> str:
        """Read a prompt file."""
        prompt_path = self.prompts_dir / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    def invoke(self, system_prompt: str, user_input: str) -> str:
        """Invoke the LLM with system and user prompts."""
        messages = [
            ("system", system_prompt),
            ("user", user_input),
        ]
        return self.llm.invoke(messages).content

    @abstractmethod
    def get_fallback_response(self, *args, **kwargs) -> str:
        """Get fallback response when LLM call fails. Must be implemented by subclasses."""
        pass
