"""Coding agent for code generation."""

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
            user_input = f"{prompt}\n\nTask: {task}\n\nInput: {input_context}"
            return self.invoke(prompt, user_input)
        except Exception as ex:
            return self.get_fallback_response(task, input_context, ex)

    def get_fallback_response(self, task: str, input_context: str, ex: Exception) -> str:
        """Get fallback response when code generation fails."""
        return f"[OFFLINE_CODE] Generated fallback implementation plan for task '{task}'. Input summary: {input_context[:100]}... Reason: {str(ex)}"
