"""Coding agent for code generation."""

from typing import Optional
from .base_agent import BaseAgent


class CodingAgent(BaseAgent):
    """Agent responsible for code generation."""

    def execute(self, task: str, input_context: str) -> str:
        """Generate code based on task and context.
        
        Args:
            task: The task description.
            input_context: Additional context for code generation (plan, memory, etc.).
            
        Returns:
            The generated code.
        """
        try:
            prompt = self.read_prompt("coding.txt")
            
            # Add tools context if available
            tools_context = ""
            if self.tool_registry:
                tools_context = f"\n\n{self.get_tools_context()}"
            
            # Enhanced prompt with tools
            enhanced_prompt = f"{prompt}{tools_context}"
            
            user_input = f"{prompt}\n\nTask: {task}\n\nInput: {input_context}"
            
            # Use tool-enabled invoke if tools are available
            if self.tool_registry:
                out = self.invoke_with_tools(enhanced_prompt, user_input, max_iterations=3)
            else:
                out = self.invoke(enhanced_prompt, user_input)
            
            return out
        except Exception as ex:
            return self.get_fallback_response(task, input_context, ex)

    def get_fallback_response(self, task: str, input_context: str, ex: Exception) -> str:
        """Get fallback response when code generation fails."""
        return f"[OFFLINE_CODE] Generated fallback implementation plan for task '{task}'. Input summary: {input_context[:100]}... Reason: {str(ex)}"
