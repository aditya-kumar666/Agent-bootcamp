"""Base agent class for common functionality."""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(
        self,
        prompts_dir: Path | None = None,
        tool_registry: Optional['ToolRegistry'] = None
    ):
        """Initialize the base agent.
        
        Args:
            prompts_dir: Directory containing prompt files
            tool_registry: ToolRegistry instance for tool calling
        """
        self.prompts_dir = prompts_dir or Path(__file__).resolve().parent.parent / "prompts"
        self.tool_registry = tool_registry
        self._llm_instance = None

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy load LLM instance."""
        if self._llm_instance is None:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self._llm_instance = ChatOpenAI(model=model, temperature=0)
        return self._llm_instance

    def read_prompt(self, filename: str) -> str:
        """Read a prompt file.
        
        Args:
            filename: Name of prompt file
            
        Returns:
            Prompt content
        """
        prompt_path = self.prompts_dir / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        return prompt_path.read_text(encoding="utf-8")

    def get_tools_context(self) -> str:
        """Get tools description for prompts.
        
        Returns:
            Markdown-formatted tools description
        """
        if not self.tool_registry:
            return ""
        return self.tool_registry.get_tools_markdown()

    def invoke(self, system_prompt: str, user_input: str) -> str:
        """Invoke the LLM with system and user prompts.
        
        Args:
            system_prompt: System prompt
            user_input: User input/task
            
        Returns:
            LLM response
        """
        messages = [
            ("system", system_prompt),
            ("user", user_input),
        ]
        return self.llm.invoke(messages).content

    def invoke_with_tools(self, system_prompt: str, user_input: str, max_iterations: int = 5) -> str:
        """Invoke LLM with tool calling support (ReAct pattern).
        
        Implements: Thought → Action → Observation loop
        
        Args:
            system_prompt: System prompt
            user_input: User input/task
            max_iterations: Maximum think→act→observe cycles (default: 5)
            
        Returns:
            Final LLM response after tool calls
        """
        # If no tools available, fall back to regular invoke
        if not self.tool_registry:
            return self.invoke(system_prompt, user_input)
        
        # Import here to avoid circular imports
        from plugins import ToolExecutor
        
        executor = ToolExecutor(self.tool_registry)
        messages = [
            HumanMessage(content=system_prompt),
            HumanMessage(content=user_input),
        ]
        
        iteration = 0
        while iteration < max_iterations:
            iteration += 1
            
            try:
                # Call LLM
                response = self.llm.invoke(messages).content
                
                # Try to parse tool call from response
                tool_call = executor.parse_tool_call(response)
                
                if not tool_call:
                    # No tool call found, this is the final answer
                    return response
                
                # Execute the tool
                tool_name = tool_call["tool"]
                tool_args = tool_call.get("args", {})
                
                try:
                    tool_result = executor.execute_tool(tool_name, **tool_args)
                except Exception as tool_ex:
                    tool_result = f"ERROR executing {tool_name}: {str(tool_ex)}"
                
                # Add exchange to conversation
                messages.append(AIMessage(content=response))
                messages.append(HumanMessage(content=f"Tool Result:\n{tool_result}"))
                
            except Exception as ex:
                # If parsing/execution fails, return what we have
                print(f"[Agent] Tool execution error (iteration {iteration}): {ex}")
                return response if 'response' in locals() else f"Error: {str(ex)}"
        
        # Max iterations reached, return last response
        return response if 'response' in locals() else "Max iterations reached without final answer"

    @abstractmethod
    def get_fallback_response(self, *args, **kwargs) -> str:
        """Get fallback response when LLM call fails. Must be implemented by subclasses."""
        pass
