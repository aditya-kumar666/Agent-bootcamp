"""Local MCP server exposing this project's existing agent tools.

This is Phase 2 MCP support: the same FileTools/TestTools/Builder tools can be
served over MCP and then consumed back through the Phase 1 MCP client adapter.
"""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp.server.fastmcp import FastMCP
from plugins.file_tools import FileToolsPlugin
from plugins.test_tools import TestToolsPlugin
from plugins.project_builder import BuilderFactory


mcp = FastMCP("local-agent-tools")
file_tools = FileToolsPlugin(PROJECT_ROOT)
test_tools = TestToolsPlugin(PROJECT_ROOT)


@mcp.tool()
def read_file(path: str) -> str:
    """Read a file from the LangGraph workspace."""
    return file_tools.read_file(path)


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write a file within the LangGraph workspace."""
    return file_tools.write_file(path, content)


@mcp.tool()
def search_files(pattern: str, limit: int = 20) -> str:
    """Search files in the LangGraph workspace."""
    return file_tools.search_files(pattern, limit)


@mcp.tool()
def list_directory(path: str = ".") -> str:
    """List a directory in the LangGraph workspace."""
    return file_tools.list_directory(path)


@mcp.tool()
def delete_file(path: str) -> str:
    """Delete a file within the LangGraph workspace."""
    return file_tools.delete_file(path)


@mcp.tool()
def run_tests(test_filter: str = "", timeout: int = 30) -> str:
    """Run pytest tests in the LangGraph workspace."""
    return test_tools.run_tests(test_filter or None, timeout)


@mcp.tool()
def run_unittest(module: str = "", timeout: int = 30) -> str:
    """Run unittest tests in the LangGraph workspace."""
    return test_tools.run_unittest(module or None, timeout)


@mcp.tool()
def check_syntax(file_path: str) -> str:
    """Check Python syntax for a file in the LangGraph workspace."""
    return test_tools.check_syntax(file_path)


@mcp.tool()
def run_linter(file_path: str = "", timeout: int = 30) -> str:
    """Run flake8 against a file or the whole LangGraph workspace."""
    return test_tools.run_linter(file_path or None, timeout)


@mcp.tool()
def validate_environment(language: str) -> str:
    """Validate that the required tools/SDK for a language are installed.

    Supported languages: csharp, java, python, go.
    """
    try:
        builder = BuilderFactory.get_builder(language, PROJECT_ROOT)
        valid = builder.validate_environment()
        return "VALID" if valid else f"INVALID: {language} SDK/runtime not found"
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def setup_project(language: str, output_dir: str) -> str:
    """Set up project structure for a language in the given directory.

    Creates necessary files like csproj, pom.xml, go.mod, __init__.py, etc.
    """
    try:
        builder = BuilderFactory.get_builder(language, PROJECT_ROOT / output_dir)
        success = builder.setup_project()
        return "SUCCESS" if success else f"FAILED: Could not setup {language} project"
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def build_project(language: str, output_dir: str) -> str:
    """Build a project (compile code, no execution).

    For compiled languages (C#, Java, Go) this runs the compiler.
    For interpreted languages (Python) this is a no-op.
    """
    try:
        builder = BuilderFactory.get_builder(language, PROJECT_ROOT / output_dir)
        success, output = builder.build()
        status = "SUCCESS" if success else "FAILED"
        return f"{status}\n{output}"
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def execute_project(language: str, output_dir: str) -> str:
    """Execute a built project and return its output.

    The project must be built first using build_project() for compiled languages.
    """
    try:
        builder = BuilderFactory.get_builder(language, PROJECT_ROOT / output_dir)
        success, output = builder.execute()
        status = "SUCCESS" if success else "FAILED"
        return f"{status}\n{output}"
    except Exception as e:
        return f"ERROR: {e}"


@mcp.tool()
def build_and_execute_project(language: str, output_dir: str) -> str:
    """Build and execute a generated project for a supported language.

    Supported languages: csharp, java, python, go.
    Combines validate_environment(), setup_project(), build(), and execute().
    """
    try:
        builder = BuilderFactory.get_builder(language, PROJECT_ROOT / output_dir)
        if not builder.validate_environment():
            return f"ENVIRONMENT_INVALID_FOR_{language}"
        if not builder.setup_project():
            return f"PROJECT_SETUP_FAILED_FOR_{language}"
        success, output = builder.build_and_execute()
        status = "SUCCESS" if success else "FAILED"
        return f"{status}\n{output}"
    except Exception as e:
        return f"ERROR: {e}"


if __name__ == "__main__":
    mcp.run()