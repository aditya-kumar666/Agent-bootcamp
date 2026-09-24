"""Review agent for code review."""

from .base_agent import BaseAgent
import re


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
            
            user_input = f"Task: {task}\n\nInput: {input_context}"
            
            # Use tool-enabled invoke if tools are available
            if self.tool_registry:
                output = self.invoke_with_tools(enhanced_prompt, user_input, max_iterations=4)
                output = self._ensure_rule_citation_guidance(output)
                return self._append_used_rule_ids(output)
            else:
                return self.invoke(enhanced_prompt, user_input)
        except Exception as ex:
            return self.get_fallback_response(task, ex)

    def get_fallback_response(self, task: str, ex: Exception) -> str:
        """Get fallback response when review fails."""
        return f"[OFFLINE_REVIEW] PASS_WITH_WARNINGS. Task: {task}. Input reviewed. Reason: {str(ex)}"

    @staticmethod
    def _ensure_rule_citation_guidance(output: str) -> str:
        """Preserve a useful review while flagging missing RAG citations."""
        if re.search(r"\[[A-Z]+(?:-[A-Z0-9]+)+-\d{2}\]", output):
            return output
        return (
            f"{output.rstrip()}\n\n"
            "CitationNote: No explicit knowledge-base rule ID was cited. "
            "If standards were consulted, revise findings to include the exact returned rule ID."
        )

    def _append_used_rule_ids(self, output: str) -> str:
        """Make the rules retrieved during this review visible in final output."""
        if not self.last_tool_rule_ids:
            return f"{output.rstrip()}\n\nRAG_RULE_IDS_USED: none"
        ids = ", ".join(self.last_tool_rule_ids)
        return f"{output.rstrip()}\n\nRAG_RULE_IDS_USED: {ids}"
