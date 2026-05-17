"""Tool registry for agent tool calling."""

from typing import Dict, Callable, Any, List
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    """Definition of a tool available to agents."""
    name: str
    description: str
    func: Callable
    parameters: Dict[str, Any]  # Expected parameters and types


class ToolRegistry:
    """Registry of tools available to agents."""

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str,
        parameters: Dict[str, Any]
    ) -> None:
        """Register a tool.
        
        Args:
            name: Unique tool name (e.g., "file_tools.read_file")
            func: Callable function
            description: Human-readable description
            parameters: Expected parameters as dict
                       Example: {"path": {"type": "string", "description": "File path"}}
        """
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            func=func,
            parameters=parameters
        )

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            ToolDefinition or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        """List all registered tools.
        
        Returns:
            List of all tool definitions
        """
        return list(self._tools.values())

    def get_tools_markdown(self) -> str:
        """Get tools formatted as markdown for prompts.
        
        Returns:
            Markdown formatted tool listing
        """
        lines = ["## Available Tools:\n"]
        for tool in self.list_tools():
            lines.append(f"### {tool.name}")
            lines.append(f"Description: {tool.description}")
            if tool.parameters:
                lines.append("Parameters:")
                for param_name, param_info in tool.parameters.items():
                    param_type = param_info.get("type", "unknown")
                    param_desc = param_info.get("description", "")
                    lines.append(f"  - {param_name} ({param_type}): {param_desc}")
            lines.append("")
        return "\n".join(lines)

    def get_tools_json_schema(self) -> List[Dict]:
        """Get tools as JSON schema for function calling.
        
        Returns:
            List of JSON schema tool definitions
        """
        schemas = []
        for tool in self.list_tools():
            schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": list(tool.parameters.keys())
                    }
                }
            }
            schemas.append(schema)
        return schemas

    def clear(self) -> None:
        """Clear all registered tools."""
        self._tools.clear()
