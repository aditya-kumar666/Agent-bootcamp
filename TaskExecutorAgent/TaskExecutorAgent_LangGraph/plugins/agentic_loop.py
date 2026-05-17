"""Agentic loop implementing ReAct pattern (Reasoning + Acting)."""

from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI


class AgenticLoop:
    """Implements ReAct-style agentic loop for tool calling."""

    def __init__(self, llm: ChatOpenAI, max_iterations: int = 5):
        """Initialize the agentic loop.
        
        Args:
            llm: Language model instance
            max_iterations: Maximum iterations before stopping
        """
        self.llm = llm
        self.max_iterations = max_iterations
        self.history: List[Dict[str, str]] = []

    def run(
        self,
        task: str,
        system_prompt: str,
        tool_executor: 'ToolExecutor',
        tools_description: str
    ) -> str:
        """Run the agentic loop.
        
        Args:
            task: Task description for the agent
            system_prompt: System prompt defining agent behavior
            tool_executor: ToolExecutor instance for tool calls
            tools_description: Description of available tools
            
        Returns:
            Final response from the agent
        """
        self.history = []
        
        # Build initial prompt with tools
        system_with_tools = f"{system_prompt}\n\n{tools_description}"

        for iteration in range(self.max_iterations):
            # Get LLM response
            messages = [
                ("system", system_with_tools),
                ("user", task),
            ]
            
            # Add history
            for entry in self.history:
                messages.append((entry["role"], entry["content"]))

            response = self.llm.invoke(messages)
            response_text = response.content

            # Store response in history
            self.history.append({
                "role": "assistant",
                "content": response_text
            })

            # Check for final answer (no tool call)
            if "Final Answer:" in response_text or "FINAL_ANSWER:" in response_text:
                # Extract final answer
                final_answer = self._extract_final_answer(response_text)
                return final_answer

            # Try to parse and execute tool call
            tool_call = tool_executor.parse_tool_call(response_text)
            
            if not tool_call:
                # No tool call, return response as is
                return response_text

            # Execute tool
            tool_name = tool_call.get("tool")
            args = tool_call.get("args", {})
            
            result = tool_executor.execute_tool(tool_name, **args)
            
            # Add observation to history
            self.history.append({
                "role": "user",
                "content": f"Tool Result:\n{result}"
            })

        # Max iterations reached
        return f"Agent exceeded maximum iterations ({self.max_iterations}). Last response: {self.history[-1]['content']}"

    def _extract_final_answer(self, text: str) -> str:
        """Extract final answer from LLM response.
        
        Args:
            text: LLM response text
            
        Returns:
            Final answer text
        """
        # Look for "Final Answer:" marker
        if "Final Answer:" in text:
            parts = text.split("Final Answer:")
            return parts[-1].strip()
        
        if "FINAL_ANSWER:" in text:
            parts = text.split("FINAL_ANSWER:")
            return parts[-1].strip()
        
        return text

    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history.
        
        Returns:
            List of message history entries
        """
        return self.history
