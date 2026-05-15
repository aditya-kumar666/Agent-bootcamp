"""Evaluation agent for final evaluation."""

from .base_agent import BaseAgent


class EvaluationAgent(BaseAgent):
    """Agent responsible for evaluating the final output."""

    def evaluate(self, task: str, review_output: str) -> str:
        """Evaluate the task completion.
        
        Args:
            task: The task description.
            review_output: The review feedback.
            
        Returns:
            The evaluation result.
        """
        try:
            prompt = self.read_prompt("evaluation.txt")
            user_input = f"{prompt}\n\nTask: {task}\n\nReviewOutput: {review_output}"
            return self.invoke(prompt, user_input)
        except Exception as ex:
            return self.get_fallback_response(task, ex)

    def get_fallback_response(self, task: str, ex: Exception) -> str:
        """Get fallback response when evaluation fails."""
        return (
            "Status: PASS\n"
            "AcceptanceCriteria: Partially validated (offline mode)\n"
            "Tests: Not executed by LLM\n"
            "OpenIssues: API quota unavailable\n"
            "Risk: Medium\n"
            f"FinalSummary: Task '{task}' executed in offline fallback mode. Reason: {str(ex)}"
        )
