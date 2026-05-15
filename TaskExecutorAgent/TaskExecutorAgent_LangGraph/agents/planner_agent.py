"""Planner agent for task planning."""

from .base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """Agent responsible for planning the task."""

    def plan(self, task: str) -> str:
        """Plan the given task.
        
        Args:
            task: The task description to plan.
            
        Returns:
            The plan for the task.
        """
        try:
            prompt = self.read_prompt("planner.txt")
            user_input = f"{prompt}\n\nTask: {task}"
            return self.invoke(prompt, user_input)
        except Exception as ex:
            return self.get_fallback_response(task, ex)

    def get_fallback_response(self, task: str, ex: Exception) -> str:
        """Get fallback response when planning fails."""
        return f"[OFFLINE_PLAN] 1) Analyze task 2) Propose changes 3) Validate output. Reason: {str(ex)}"
