"""Reflection agent for code reflection and improvement."""

from .base_agent import BaseAgent


class ReflectionAgent(BaseAgent):
    """Agent responsible for reflecting on code quality and suggesting improvements."""

    def reflect(self, task: str, code_output: str, review_output: str) -> str:
        """Reflect on code and suggest improvements.
        
        Args:
            task: The task description.
            code_output: The generated code.
            review_output: The review feedback.
            
        Returns:
            The reflection and improvement suggestions.
        """
        try:
            prompt = self.read_prompt("reflection.txt")
            user_input = f"{prompt}\n\nTask: {task}\n\nCodeOutput: {code_output}\n\nReviewOutput: {review_output}"
            return self.invoke(prompt, user_input)
        except Exception as ex:
            return self.get_fallback_response(ex)

    def get_fallback_response(self, ex: Exception) -> str:
        """Get fallback response when reflection fails."""
        return f"[OFFLINE_REFLECTION] Retry with smaller scoped change and rerun review. Reason: {str(ex)}"
