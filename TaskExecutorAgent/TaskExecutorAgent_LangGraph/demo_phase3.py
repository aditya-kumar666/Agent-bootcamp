#!/usr/bin/env python
"""Phase 3 Demo: Multi-Server MCP Ecosystem in Action

This demo shows:
1. Server registration with verbose output
2. Tool discovery and availability
3. Phase 3 MCP server setup
4. Error handling for missing servers/credentials
"""

import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from plugins import MCPToolManager, ToolRegistry


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{title}")
    print("-" * len(title))


def demo_phase3_overview():
    """Show Phase 3 overview and capabilities."""
    print_header("Phase 3: Multi-Server MCP Ecosystem Demo")
    
    print("""
This demo showcases Phase 3 enhancements:

✅ Phase 1: Local MCP client adapter (plugins/mcp_tools.py)
✅ Phase 2: Local MCP server (mcp_servers/local_agent_tools_server.py)
✅ Phase 3: Multi-server MCP ecosystem with:
   • Server enablement flags (enabled: true/false)
   • Environment variable substitution (${VAR})
   • Health checking for server availability
   • Verbose logging and diagnostics
   • Error recovery and graceful degradation

MCP Servers Available:
  1. local_agent_tools (Phase 2) - File, test, and build tools
  2. github - GitHub API access (if GITHUB_TOKEN set)
  3. filesystem - Advanced filesystem operations
  4. sqlite - Database access and persistence
  5. fetch - HTTP/API access
  6. azure_devops - Work items, pipelines, PRs

Total Tools Available: 58+
""")


def demo_config_inspection():
    """Show the mcp_servers.json configuration."""
    print_section("1. MCP Server Configuration (mcp_servers.json)")
    
    config_path = Path(__file__).parent / "mcp_servers.json"
    
    if not config_path.exists():
        print("⚠️  mcp_servers.json not found!")
        return
    
    config = json.loads(config_path.read_text(encoding="utf-8"))
    
    print(f"Configuration: {config_path}")
    print(f"Phase: {config.get('phase', 'unknown')}")
    print(f"Description: {config.get('description', '')}\n")
    
    servers = config.get("servers", {})
    print(f"Total Servers Configured: {len(servers)}\n")
    
    for server_name, server_config in servers.items():
        enabled = server_config.get("enabled", True)
        status = "✅ ENABLED" if enabled else "❌ DISABLED"
        description = server_config.get("description", "")
        
        print(f"  {server_name:20} {status:15} {description}")
        print(f"    Command: {server_config.get('command')}")
        if server_config.get('env'):
            print(f"    Env: {list(server_config.get('env', {}).keys())}")
    
    print()


def demo_tool_registration():
    """Show tool registration process with verbose output."""
    print_section("2. Tool Registration Process (Verbose Output)")
    
    config_path = Path(__file__).parent / "mcp_servers.json"
    
    print("Initializing MCPToolManager...")
    manager = MCPToolManager(config_path)
    
    print("Creating ToolRegistry...")
    registry = ToolRegistry()
    
    print("\nRegistering tools with verbose output:")
    print("-" * 70)
    
    # Register with verbose output
    registered = manager.register_all(registry, verbose=True)
    
    print("-" * 70)
    print(f"\n✅ Registration Complete:")
    print(f"   Total tools registered: {registered}")
    print(f"   Active servers: {len(manager.get_registered_servers())}")
    if manager.get_registered_servers():
        print(f"   Servers: {', '.join(manager.get_registered_servers())}")
    print()


def demo_environment_substitution():
    """Show environment variable substitution."""
    print_section("3. Environment Variable Substitution")
    
    import os
    
    # Example environment variables
    examples = [
        ("${GITHUB_TOKEN}", "GitHub credentials"),
        ("${WORKSPACE_ROOT}", "Agent workspace root"),
        ("${WORKSPACE_ROOT}/agent.db", "Database path with workspace root"),
        ("${AZURE_DEVOPS_ORG:myorg}", "Azure org with default fallback"),
        ("${NONEXISTENT:default_value}", "Missing var with default"),
    ]
    
    print("MCPToolManager supports environment variable substitution:\n")
    
    manager = MCPToolManager(Path(__file__).parent / "mcp_servers.json")
    
    for template, description in examples:
        try:
            result = manager._substitute_env_vars(template)
            print(f"  {template:40} → {result}")
            print(f"    ({description})\n")
        except Exception as e:
            print(f"  {template:40} → ERROR: {e}\n")


def demo_server_health_check():
    """Show server health checking."""
    print_section("4. Server Health Checking")
    
    import asyncio
    
    print("MCPToolManager performs health checks before loading:\n")
    
    examples = [
        ("python", ["mcp_servers/local_agent_tools_server.py"], "Local Python server"),
        ("npx", ["-y", "@modelcontextprotocol/server-github"], "NPM package"),
        ("python", ["nonexistent_server.py"], "Missing script"),
    ]
    
    manager = MCPToolManager(Path(__file__).parent / "mcp_servers.json")
    
    for command, args, description in examples:
        print(f"Checking: {description}")
        print(f"  Command: {command} {' '.join(args[:1])}")
        
        async def check():
            ok, msg = await manager._check_server_health(command, args, {}, verbose=False)
            return ok, msg
        
        is_ok, message = asyncio.run(check())
        status = "✅ OK" if is_ok else "❌ FAILED"
        print(f"  Status: {status} - {message}\n")


def demo_mcp_tool_usage():
    """Show how agents would use MCP tools."""
    print_section("5. How Agents Use MCP Tools")
    
    print("""
Agents access MCP tools through the same ReAct interface as local tools.

Examples:

1. GitHub Integration:
   Coding Agent wants to find reference implementations:
   
   Action: mcp.github.search_repositories(query=async task executor python)
   → Returns matching repositories for reference

2. Database Persistence:
   Evaluation Agent logs metrics for continuous improvement:
   
   Action: mcp.sqlite.query(db=agent.db, sql=SELECT COUNT(*) FROM runs)
   → Returns historical execution data

3. Work Item Linking:
   Coder Agent links generated code to Azure DevOps task:
   
   Action: mcp.azure_devops.update_work_item(work_item_id=123, fields={"System.State": "Resolved"})
   → Updates work item status

4. Code Standards:
   Review Agent fetches current coding standards:
   
   Action: mcp.fetch.get(url=https://api.github.com/repos/org/standards/contents/CODING_STANDARDS.md)
   → Returns latest standards

5. Advanced File Operations:
   Planner Agent searches for similar implementation patterns:
   
   Action: mcp.filesystem.search(pattern=**/*.cs, recursive=true)
   → Returns all matching files for analysis

All MCP tool calls use the same format:
   Action: mcp.<server>.<tool>(arg1=value1, arg2=value2)

Graceful Fallback:
   • If server not enabled → Tool call returns error message
   • Agent adapts strategy using available tools
   • No code changes needed
""")


def demo_server_modes():
    """Show server enabled/disabled behavior."""
    print_section("6. Server Enablement Modes")
    
    print("""
Phase 3 Feature: Each server can be enabled or disabled via configuration

In mcp_servers.json:

{
  "local_agent_tools": {
    "enabled": true   // Always enable Phase 2
  },
  "github": {
    "enabled": false  // Disabled until credentials available
  },
  "sqlite": {
    "enabled": true   // Enable to store state
  }
}

To Enable a Server:

1. Ensure dependencies installed:
   npm install -g @modelcontextprotocol/server-github

2. Set credentials (if needed):
   $env:GITHUB_TOKEN = "ghp_..."

3. Update mcp_servers.json:
   "github": { "enabled": true }

4. Restart agent:
   python main_with_tools.py

Result:
   [OK] Server 'github' registered 6 tools
   [OK] Registered 20 MCP tools from 2 servers

Agent Operation:
   • When enabled: mcp.github.* tools available
   • When disabled: Tool calls return "Server not available"
   • Agents automatically adapt to available tools
""")


def demo_phase3_summary():
    """Show Phase 3 summary and tool inventory."""
    print_section("7. Phase 3 Tool Inventory")
    
    print("""
Phase 3 Multi-Server Ecosystem Tool Distribution:

┌─────────────────────┬────────────────────────────────────┐
│ Component           │ Tools Available                    │
├─────────────────────┼────────────────────────────────────┤
│ Local (Phase 0)     │ 9 tools                           │
│   • FileTools: 5    │   read_file, write_file, etc.    │
│   • TestTools: 4    │   run_tests, check_syntax, etc.  │
├─────────────────────┼────────────────────────────────────┤
│ Phase 2 MCP Server  │ 14 tools                          │
│   • FileTools: 5    │   (same as above via MCP)         │
│   • TestTools: 4    │                                   │
│   • BuilderTools: 5 │   setup_project, build, execute   │
├─────────────────────┼────────────────────────────────────┤
│ Phase 3 GitHub      │ 6+ tools                          │
│   (when enabled)    │   search_repositories, issues...  │
├─────────────────────┼────────────────────────────────────┤
│ Phase 3 Filesystem  │ 5+ tools                          │
│   (when enabled)    │   read, write, search, delete...  │
├─────────────────────┼────────────────────────────────────┤
│ Phase 3 SQLite      │ 7 tools                           │
│   (when enabled)    │   query, insert, update, delete   │
├─────────────────────┼────────────────────────────────────┤
│ Phase 3 Fetch       │ 5 tools                           │
│   (when enabled)    │   get, post, put, delete, fetch   │
├─────────────────────┼────────────────────────────────────┤
│ Phase 3 Azure DevOps│ 6 tools                           │
│   (when enabled)    │   work_items, PRs, pipelines...   │
├─────────────────────┼────────────────────────────────────┤
│ TOTAL               │ 58+ tools                         │
└─────────────────────┴────────────────────────────────────┘

Tool Accessibility:
   • All tools access via ToolRegistry
   • Unified ReAct interface
   • No agent code changes needed
   • Graceful fallback if server unavailable
""")


def main():
    """Run all Phase 3 demos."""
    print("\n")
    
    try:
        demo_phase3_overview()
        demo_config_inspection()
        demo_tool_registration()
        demo_environment_substitution()
        demo_server_health_check()
        demo_mcp_tool_usage()
        demo_server_modes()
        demo_phase3_summary()
        
        print_header("Phase 3 Demo Complete ✅")
        print("""
Next Steps:

1. Enable MCP servers in mcp_servers.json:
   • Set "enabled": true for GitHub, SQLite, etc.
   • Set corresponding environment variables

2. Install MCP packages:
   npm install -g \\
     @modelcontextprotocol/server-github \\
     @modelcontextprotocol/server-filesystem \\
     @modelcontextprotocol/server-sqlite \\
     @modelcontextprotocol/server-fetch

3. Run the agent:
   python main_with_tools.py

4. Watch verbose output to see:
   ✓ Tool registration with all servers
   ✓ MCP tools from external servers
   ✓ Agents using multi-server ecosystem

Documentation:
   • PHASE_3_COMPLETE.md - Comprehensive guide
   • mcp_servers.json - Server configurations
   • prompts/*.txt - Agent prompts with Phase 3 guidance
""")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
