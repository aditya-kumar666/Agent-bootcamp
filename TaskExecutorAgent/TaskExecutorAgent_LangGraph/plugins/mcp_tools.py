"""MCP client adapter for registering MCP server tools in ToolRegistry.

Phase 1 scope:
- Load MCP stdio server definitions from mcp_servers.json.
- Connect to each configured server.
- Discover server tools.
- Register discovered tools as normal ToolRegistry callables.

Phase 3 enhancements:
- Support server enablement flags
- Environment variable substitution
- Server health checking
- Better error recovery

This keeps the existing ReAct tool loop unchanged:
LLM -> ToolExecutor -> ToolRegistry -> MCP callable -> MCP server.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .tool_registry import ToolRegistry


class MCPToolManager:
    """Loads MCP tools and registers them into the local ToolRegistry.
    
    Phase 3 Features:
    - Server enablement flags (enabled: true/false)
    - Environment variable substitution (${VAR} syntax)
    - Server health checks
    - Detailed logging
    """

    def __init__(self, config_path: Path):
        self.config_path = Path(config_path)
        self._server_configs: Dict[str, Dict[str, Any]] = {}
        self._registered_servers: list[str] = []

    def register_all(self, registry: ToolRegistry, verbose: bool = False) -> int:
        """Synchronously load configured MCP tools and register them.
        
        Args:
            registry: ToolRegistry to register tools into
            verbose: Enable detailed logging
        
        Returns:
            Number of MCP tools registered.
        """
        result = asyncio.run(self._register_all_async(registry, verbose))
        return result

    async def _register_all_async(self, registry: ToolRegistry, verbose: bool = False) -> int:
        if not self.config_path.exists():
            return 0

        try:
            config = json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception as e:
            if verbose:
                print(f"[ERROR] Failed to read MCP config: {e}", file=sys.stderr)
            return 0

        servers = config.get("servers", {})
        if not servers:
            return 0

        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as exc:
            if verbose:
                print(f"[WARN] MCP not available: {exc}", file=sys.stderr)
            return 0

        registered = 0

        for server_name, server_config in servers.items():
            # Phase 3: Check if server is enabled (default: true for backwards compatibility)
            enabled = server_config.get("enabled", True)
            if not enabled:
                if verbose:
                    print(f"[SKIP] Server '{server_name}' is disabled", file=sys.stderr)
                continue

            # Get command and args
            command = server_config.get("command")
            args = server_config.get("args", [])
            env = server_config.get("env", {})

            if not command:
                if verbose:
                    print(f"[SKIP] Server '{server_name}' has no command", file=sys.stderr)
                continue

            # Phase 3: Substitute environment variables
            try:
                args = [self._substitute_env_vars(arg) for arg in args]
                env = {k: self._substitute_env_vars(v) for k, v in env.items()}
            except Exception as e:
                if verbose:
                    print(f"[ERROR] Failed to substitute env vars for '{server_name}': {e}", file=sys.stderr)
                continue

            # Phase 3: Check server health before registration
            health_ok, health_msg = await self._check_server_health(command, args, env, verbose)
            if not health_ok:
                if verbose:
                    print(f"[WARN] Server '{server_name}' health check failed: {health_msg}", file=sys.stderr)
                continue

            try:
                self._server_configs[server_name] = {
                    "command": command,
                    "args": args,
                    "env": env,
                }
                
                params = StdioServerParameters(command=command, args=args, env=env if env else None)

                async with stdio_client(params) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        tools_response = await session.list_tools()

                tool_count = 0
                for tool in tools_response.tools:
                    tool_name = f"mcp.{server_name}.{tool.name}"
                    registry.register(
                        name=tool_name,
                        func=self._make_sync_callable(server_name, tool.name),
                        description=tool.description or f"MCP tool {tool.name} from server {server_name}",
                        parameters=self._json_schema_to_registry_parameters(
                            getattr(tool, "inputSchema", None)
                        ),
                    )
                    tool_count += 1
                    registered += 1

                self._registered_servers.append(server_name)
                if verbose:
                    print(f"[OK] Server '{server_name}' registered {tool_count} tools", file=sys.stderr)

            except Exception as e:
                if verbose:
                    print(f"[ERROR] Failed to register server '{server_name}': {e}", file=sys.stderr)
                continue

        return registered

    async def _check_server_health(self, command: str, args: list, env: dict, verbose: bool) -> Tuple[bool, str]:
        """Quick health check on server availability.
        
        Returns:
            Tuple of (is_healthy: bool, message: str)
        """
        # Check if command/executable exists (for local files)
        if command == "python" and args and len(args) > 0:
            script_path = args[0]
            if not Path(script_path).exists():
                return False, f"Script not found: {script_path}"

        # For npm packages, we can't easily check, so we allow them to fail gracefully
        if command in ["npx", "npm"]:
            return True, "NPM package (assuming installed)"

        # Try to find command in PATH
        import shutil
        if shutil.which(command) is None:
            if command not in ["npx", "npm"]:  # Don't fail for npm commands
                return False, f"Command not found in PATH: {command}"

        return True, "Health check passed"

    def _substitute_env_vars(self, value: str) -> str:
        """Substitute environment variables in format ${VAR_NAME} or ${VAR_NAME:default}.
        
        Args:
            value: String potentially containing env var references
            
        Returns:
            String with env vars substituted
        """
        def replace_var(match):
            var_spec = match.group(1)
            
            # Check for default value syntax: VAR_NAME:default_value
            if ":" in var_spec:
                var_name, default_value = var_spec.split(":", 1)
            else:
                var_name = var_spec
                default_value = ""
            
            # Handle special variables
            if var_name == "WORKSPACE_ROOT":
                return str(Path(__file__).parent.parent)
            
            return os.getenv(var_name, default_value)
        
        # Replace ${VAR} or ${VAR:default}
        return re.sub(r'\$\{([^}]+)\}', replace_var, value)

    def _make_sync_callable(self, server_name: str, tool_name: str):
        def _call(**kwargs):
            return asyncio.run(self._call_tool_async(server_name, tool_name, kwargs))

        return _call

    async def _call_tool_async(self, server_name: str, tool_name: str, args: Dict[str, Any]) -> str:
        server_config = self._server_configs.get(server_name)
        if not server_config:
            raise RuntimeError(f"MCP server config not found: {server_name}")

        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            return "ERROR: MCP not available"

        try:
            params = StdioServerParameters(
                command=server_config["command"],
                args=server_config.get("args", []),
                env=server_config.get("env") or None,
            )

            async with stdio_client(params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, args)
            
            content = getattr(result, "content", None) or []
            if not content:
                return ""

            parts = []
            for item in content:
                text = getattr(item, "text", None)
                if text is not None:
                    parts.append(text)
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        
        except Exception as e:
            return f"ERROR: Tool execution failed: {e}"

    @staticmethod
    def _json_schema_to_registry_parameters(schema: Any) -> Dict[str, Any]:
        if not isinstance(schema, dict):
            return {}
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            return properties
        return {}

    def get_registered_servers(self) -> list[str]:
        """Get list of successfully registered MCP servers."""
        return self._registered_servers.copy()
