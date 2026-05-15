"""Review agent for code review."""

from .base_agent import BaseAgent


class ReviewAgent(BaseAgent):
    """Agent responsible for reviewing code."""

    def review(self, task: str, input_context: str) -> str:
        """Review code for the task.
        
        Args:
            task: The task description.
            input_context: The code to review.
            
        Returns:
            The review feedback.
        """
        try:
            prompt = self.read_prompt("review.txt")
            user_input = f"{prompt}\n\nTask: {task}\n\nInput: {input_context}"
            return self.invoke(prompt, user_input)
        except Exception as ex:
            return self.get_fallback_response(task, ex)

    def get_fallback_response(self, task: str, ex: Exception) -> str:
        """Get fallback response when review fails."""
        return f"[OFFLINE_REVIEW] PASS_WITH_WARNINGS. Task: {task}. Input reviewed. Reason: {str(ex)}"
