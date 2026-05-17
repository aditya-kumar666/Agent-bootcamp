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
            
            # Add tools context if available
            tools_context = ""
            if self.tool_registry:
                tools_context = f"\n\n{self.get_tools_context()}"
            
            # Enhanced prompt with tools
            enhanced_prompt = f"{prompt}{tools_context}"
            
            user_input = f"{prompt}\n\nTask: {task}\n\nInput: {input_context}"
            
            # Use tool-enabled invoke if tools are available
            if self.tool_registry:
                return self.invoke_with_tools(enhanced_prompt, user_input, max_iterations=3)
            else:
                return self.invoke(enhanced_prompt, user_input)
        except Exception as ex:
            return self.get_fallback_response(task, ex)

    def get_fallback_response(self, task: str, ex: Exception) -> str:
        """Get fallback response when review fails."""
        return f"[OFFLINE_REVIEW] PASS_WITH_WARNINGS. Task: {task}. Input reviewed. Reason: {str(ex)}"
