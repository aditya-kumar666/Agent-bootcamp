"""Tool execution and parsing for agent tool calling."""

import re
import json
from typing import Optional, Dict, Any, Tuple
from .tool_registry import ToolRegistry


class ToolExecutor:
    """Executes tool calls from LLM responses."""

    def __init__(self, registry: ToolRegistry):
        """Initialize the tool executor.
        
        Args:
            registry: ToolRegistry instance with registered tools
        """
        self.registry = registry

    def parse_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse a tool call from LLM response text.
        
        Supports multiple formats:
        1. JSON: {"tool": "name", "args": {...}}
        2. Markdown: ```tool\n{"tool": "name", ...}\n```
        3. ReAct format: Action: tool_name(arg1=val1, arg2=val2)
        
        Args:
            text: LLM response text
            
        Returns:
            Dictionary with "tool" and "args", or None if no valid tool call found
        """
        # Try JSON format first
        json_match = re.search(r'\{[\s\n]*"tool"[\s\n]*:[\s\n]*"([^"]+)"', text)
        if json_match:
            try:
                # Extract JSON block
                json_start = text.find('{')
                json_end = text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = text[json_start:json_end]
                    parsed = json.loads(json_str)
                    return {
                        "tool": parsed.get("tool"),
                        "args": parsed.get("args", {})
                    }
            except json.JSONDecodeError:
                pass

        # Try Markdown code block format
        md_match = re.search(r'```(?:tool|json)?\n(.*?)\n```', text, re.DOTALL)
        if md_match:
            try:
                parsed = json.loads(md_match.group(1))
                return {
                    "tool": parsed.get("tool"),
                    "args": parsed.get("args", {})
                }
            except json.JSONDecodeError:
                pass

        # Try ReAct format: Action: tool_name(arg1=val1, arg2=val2)
        react_match = re.search(r'Action:\s*(\w+[\.\w]*)\((.*?)\)', text)
        if react_match:
            tool_name = react_match.group(1)
            args_str = react_match.group(2)
            args = self._parse_react_args(args_str)
            return {"tool": tool_name, "args": args}

        # Try plain python-style tool call in fenced blocks or prose:
        # file_tools.search_files(pattern='*.cs', limit=10)
        py_call_match = re.search(r'(\w+[\.\w]*)\(([^\)]*)\)', text)
        if py_call_match:
            tool_name = py_call_match.group(1)
            tool_def = self.registry.get_tool(tool_name)
            if tool_def:
                args_str = py_call_match.group(2)
                args = self._parse_react_args(args_str)
                return {"tool": tool_name, "args": args}

        return None

    def _parse_react_args(self, args_str: str) -> Dict[str, Any]:
        """Parse ReAct-style arguments.
        
        Args:
            args_str: String like "path=/tmp/file.py, limit=10"
            
        Returns:
            Dictionary of parsed arguments
        """
        args = {}
        for arg_pair in args_str.split(','):
            if '=' in arg_pair:
                key, val = arg_pair.split('=', 1)
                key = key.strip()
                val = val.strip()
                # Try to convert to appropriate type
                if val.lower() in ('true', 'false'):
                    args[key] = val.lower() == 'true'
                elif val.isdigit():
                    args[key] = int(val)
                else:
                    args[key] = val.strip('"\'')
        return args

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool call.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool
            
        Returns:
            String result from tool execution
        """
        tool_def = self.registry.get_tool(tool_name)
        if not tool_def:
            return f"ERROR: Tool '{tool_name}' not found. Available tools: {', '.join([t.name for t in self.registry.list_tools()])}"

        try:
            result = tool_def.func(**kwargs)
            return str(result)
        except TypeError as ex:
            return f"ERROR: Invalid arguments for '{tool_name}': {str(ex)}"
        except Exception as ex:
            return f"ERROR executing '{tool_name}': {str(ex)}"

    def execute_from_text(self, text: str) -> Tuple[bool, str]:
        """Parse and execute a tool call from LLM response text.
        
        Args:
            text: LLM response containing tool call
            
        Returns:
            Tuple of (success, result_string)
        """
        tool_call = self.parse_tool_call(text)
        if not tool_call:
            return False, "No valid tool call found in response"

        tool_name = tool_call.get("tool")
        args = tool_call.get("args", {})

        if not tool_name:
            return False, "Tool call missing 'tool' field"

        result = self.execute_tool(tool_name, **args)
        success = not result.startswith("ERROR")
        return success, result
