"""Tool-integrated version of the task executor with tool calling support."""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import TypedDict
import re

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from agents import (
    PlannerAgent,
    CodingAgent,
    ReviewAgent,
    ReflectionAgent,
    EvaluationAgent,
)
from memory.run_memory import RunMemory
from plugins import FileToolsPlugin, TestToolsPlugin, ToolRegistry, ToolExecutor, AgenticLoop

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"


def _extract_file_blocks_from_output(coding_output: str) -> dict[str, str]:
    """Best-effort extraction of generated file blocks from agent markdown output."""
    files: dict[str, str] = {}

    def _store_file(path: str, content: str) -> None:
        path = path.strip()
        content = content.strip()
        if not path or not content:
            return
        # If the same file is discovered multiple times, keep the longer block.
        existing = files.get(path, "")
        if len(content) >= len(existing):
            files[path] = content

    # Pattern 1: "Code for `path/to/file.ext`" followed by any fenced code block
    p1 = re.compile(
        r"Code for\s+`([^`]+)`(?:[^\n`]*)\n?\s*```[a-zA-Z0-9_+-]*\s*(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    for m in p1.finditer(coding_output):
        rel = m.group(1).strip()
        content = m.group(2).strip()
        _store_file(rel, content)

    # Pattern 2: combined block with language comment headers:
    # // path/file.ext, # path/file.ext, -- path/file.ext
    # Only split on lines that look like file headers (contain path indicators)
    for combined in re.finditer(r"```[a-zA-Z0-9_+-]*\s*(.*?)```", coding_output, re.DOTALL | re.IGNORECASE):
        text = combined.group(1)
        # Split only on comments that have file path patterns (// File:, # File:, or paths with /)
        sections = re.split(r"\n\s*(?://|#|--)\s*(?:File:\s*)?([^\n]*?[/\\][^\n]*)\n", "\n" + text)
        
        # Reconstruct sections with their headers
        for i in range(1, len(sections), 2):
            if i + 1 < len(sections):
                header = sections[i].strip()
                body = sections[i + 1].strip()
                if header and body:
                    _store_file(header, body)

    return files


def _sanitize_relative_output_path(raw_path: str) -> str:
    """Normalize model-produced file labels into safe relative paths."""
    p = raw_path.strip().replace("\\", "/")
    if "(" in p or ")" in p:
        return ""
    p = re.sub(r"^[-*\d).\s]+", "", p)  # bullets / numbering
    p = re.sub(r"^(file|path)\s*:\s*", "", p, flags=re.IGNORECASE)
    p = p.strip("`\"' ")
    p = p.lstrip("/")
    p = re.sub(r"^generated_projects/todo_feature_project/", "", p, flags=re.IGNORECASE)
    p = re.sub(r"^generated_projects/todo_feature_project/", "", p, flags=re.IGNORECASE)
    # collapse accidental duplicate slashes
    p = re.sub(r"/{2,}", "/", p)
    if p.startswith("generated_projects/") or p.startswith("test_tools.") or p.startswith("file_tools."):
        return ""
    return p


def _is_complete_code_content(path: str, content: str) -> bool:
    """Heuristic check to avoid materializing truncated code files (language-agnostic).
    
    Checks if code content appears complete by verifying:
    - Content is not empty
    - Braces/brackets are balanced
    - Content ends with a closing brace (for files with code blocks)
    """
    text = content.strip()
    if not text:
        return False
    
    # Check for balanced braces and brackets (works across languages)
    if text.count("{") != text.count("}"):
        return False
    if text.count("[") != text.count("]"):
        return False
    if text.count("(") != text.count(")"):
        return False
    
    # If file contains code blocks, it should end with a closing brace
    if "{" in text and not text.rstrip().endswith(("}","};")):
        return False
    
    return True


def _create_csharp_project_file(output_dir_path: Path) -> bool:
    """Create a .csproj file for the C# project."""
    csproj_content = """<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
"""
    try:
        csproj_path = output_dir_path / "TodoApp.csproj"
        csproj_path.write_text(csproj_content, encoding="utf-8")
        print(f"[OK] Created project file: {csproj_path}", file=sys.stderr)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create .csproj file: {e}", file=sys.stderr)
        return False


def _build_and_execute_csharp(output_dir_path: Path) -> tuple[bool, str]:
    """Build and execute the generated C# project.
    
    Returns:
        Tuple of (success: bool, output: str)
    """
    import subprocess
    
    try:
        # Change to output directory
        print(f"\n[BUILD] Compiling C# project...", file=sys.stderr)
        
        # Run dotnet build
        build_result = subprocess.run(
            ["dotnet", "build", "-c", "Release"],
            cwd=str(output_dir_path),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if build_result.returncode != 0:
            error_msg = build_result.stderr or build_result.stdout
            print(f"[ERROR] Build failed: {error_msg}", file=sys.stderr)
            return False, error_msg
        
        print(f"[OK] Build successful", file=sys.stderr)
        
        # Find the executable
        exe_path = output_dir_path / "bin" / "Release" / "net9.0" / "TodoApp.exe"
        if not exe_path.exists():
            print(f"[ERROR] Executable not found at {exe_path}", file=sys.stderr)
            return False, "Executable not found after build"
        
        # Run the executable
        print(f"\n[RUN] Executing application...", file=sys.stderr)
        run_result = subprocess.run(
            [str(exe_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = run_result.stdout
        if run_result.returncode != 0:
            error_msg = run_result.stderr or "Unknown error"
            print(f"[ERROR] Execution failed: {error_msg}", file=sys.stderr)
            return False, f"Execution error: {error_msg}"
        
        print(f"[OK] Execution successful", file=sys.stderr)
        return True, output
        
    except subprocess.TimeoutExpired:
        return False, "Build or execution timed out"
    except FileNotFoundError as e:
        return False, f"dotnet not found. Make sure .NET SDK is installed: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


class GraphState(TypedDict, total=False):
    task: str
    plan: str
    code: str
    review: str
    reflection: str
    evaluation: str
    memory: RunMemory


def setup_tool_registry() -> ToolRegistry:
    """Set up tool registry with FileTools and TestTools.
    
    Returns:
        Configured ToolRegistry
    """
    registry = ToolRegistry()
    
    # Initialize tool plugins
    file_tools = FileToolsPlugin(BASE_DIR)
    test_tools = TestToolsPlugin(BASE_DIR)
    
    # Register FileTools
    registry.register(
        name="file_tools.read_file",
        func=file_tools.read_file,
        description="Read file content from the workspace",
        parameters={
            "path": {
                "type": "string",
                "description": "Path to file relative to workspace root"
            }
        }
    )
    
    registry.register(
        name="file_tools.write_file",
        func=file_tools.write_file,
        description="Write content to a file in the workspace",
        parameters={
            "path": {
                "type": "string",
                "description": "Path to file relative to workspace root"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        }
    )
    
    registry.register(
        name="file_tools.search_files",
        func=file_tools.search_files,
        description="Search for files matching a pattern",
        parameters={
            "pattern": {
                "type": "string",
                "description": "Search pattern (case-insensitive substring)"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return (default: 20)"
            }
        }
    )
    
    registry.register(
        name="file_tools.list_directory",
        func=file_tools.list_directory,
        description="List files and directories",
        parameters={
            "path": {
                "type": "string",
                "description": "Directory path relative to workspace (default: '.')"
            }
        }
    )
    
    registry.register(
        name="file_tools.delete_file",
        func=file_tools.delete_file,
        description="Delete a file from the workspace",
        parameters={
            "path": {
                "type": "string",
                "description": "Path to file to delete"
            }
        }
    )
    
    # Register TestTools
    registry.register(
        name="test_tools.run_tests",
        func=test_tools.run_tests,
        description="Run pytest tests",
        parameters={
            "test_filter": {
                "type": "string",
                "description": "Optional filter for specific tests"
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 30)"
            }
        }
    )
    
    registry.register(
        name="test_tools.run_unittest",
        func=test_tools.run_unittest,
        description="Run unittest tests",
        parameters={
            "module": {
                "type": "string",
                "description": "Optional specific test module"
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 30)"
            }
        }
    )
    
    registry.register(
        name="test_tools.check_syntax",
        func=test_tools.check_syntax,
        description="Check Python file syntax without running",
        parameters={
            "file_path": {
                "type": "string",
                "description": "Path to Python file to check"
            }
        }
    )
    
    registry.register(
        name="test_tools.run_linter",
        func=test_tools.run_linter,
        description="Run code linter (flake8)",
        parameters={
            "file_path": {
                "type": "string",
                "description": "Optional specific file to lint"
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 30)"
            }
        }
    )
    
    return registry


def create_agents_with_tools(tool_registry: ToolRegistry):
    """Create agent instances with tool registry.
    
    Args:
        tool_registry: ToolRegistry instance
        
    Returns:
        Tuple of all agent instances
    """
    planner = PlannerAgent(PROMPTS_DIR, tool_registry)
    coding = CodingAgent(PROMPTS_DIR, tool_registry)
    review = ReviewAgent(PROMPTS_DIR, tool_registry)
    reflection = ReflectionAgent(PROMPTS_DIR, tool_registry)
    evaluation = EvaluationAgent(PROMPTS_DIR, tool_registry)
    
    return planner, coding, review, reflection, evaluation


def planner_node(state: GraphState, planner: PlannerAgent) -> GraphState:
    """Planner node: plan the task."""
    try:
        out = planner.plan(state["task"])
        state["plan"] = out
        state["memory"].planner_outputs.append(out)
    except Exception as ex:
        print(f"Error in planner node: {ex}", file=sys.stderr)
        state["plan"] = planner.get_fallback_response(state["task"], ex)
        state["memory"].planner_outputs.append(state["plan"])
    return state


def coding_node(state: GraphState, coding: CodingAgent, tool_executor: ToolExecutor) -> GraphState:
    """Coding node: generate code based on plan."""
    try:
        user_input = f"{state['task']}\n\nPlan:\n{state['plan']}\n\n{state['memory'].build_context_snapshot()}"
        out = coding.execute(state["task"], user_input)
        state["code"] = out
        state["memory"].coding_outputs.append(out)
    except Exception as ex:
        print(f"Error in coding node: {ex}", file=sys.stderr)
        state["code"] = coding.get_fallback_response(state["task"], "", ex)
        state["memory"].coding_outputs.append(state["code"])
    return state


def review_node(state: GraphState, review: ReviewAgent) -> GraphState:
    """Review node: review the generated code."""
    try:
        user_input = f"{state['task']}\n\nCode:\n{state['code']}\n\n{state['memory'].build_context_snapshot()}"
        out = review.review(state["task"], user_input)
        state["review"] = out
        state["memory"].review_outputs.append(out)
    except Exception as ex:
        print(f"Error in review node: {ex}", file=sys.stderr)
        state["review"] = review.get_fallback_response(state["task"], ex)
        state["memory"].review_outputs.append(state["review"])
    return state


def reflection_node(state: GraphState, reflection: ReflectionAgent) -> GraphState:
    """Reflection node: reflect on review feedback and suggest improvements."""
    try:
        user_input = (
            f"Task:\n{state['task']}\n\n"
            f"Current Code:\n{state['code']}\n\n"
            f"Review Feedback:\n{state['review']}\n\n"
            f"{state['memory'].build_context_snapshot()}"
        )
        out = reflection.reflect(state["task"], state["code"], state["review"])
        state["reflection"] = out
        state["memory"].reflection_outputs.append(out)
    except Exception as ex:
        print(f"Error in reflection node: {ex}", file=sys.stderr)
        state["reflection"] = reflection.get_fallback_response(ex)
        state["memory"].reflection_outputs.append(state["reflection"])
    return state


def recode_after_reflection_node(state: GraphState, coding: CodingAgent) -> GraphState:
    """Recode node: regenerate code based on reflection."""
    try:
        user_input = f"{state['task']}\n\nReflection:\n{state['reflection']}\n\n{state['memory'].build_context_snapshot()}"
        out = coding.execute(state["task"], user_input)
        state["code"] = out
        state["memory"].coding_outputs.append(out)
    except Exception as ex:
        print(f"Error in recode node: {ex}", file=sys.stderr)
        state["code"] = coding.get_fallback_response(state["task"], "", ex)
        state["memory"].coding_outputs.append(state["code"])
    return state


def evaluate_node(state: GraphState, evaluation: EvaluationAgent) -> GraphState:
    """Evaluation node: evaluate the final output."""
    try:
        out = evaluation.evaluate(state["task"], state.get("review", ""))
        state["evaluation"] = out
        state["memory"].evaluation_outputs.append(out)
    except Exception as ex:
        print(f"Error in evaluation node: {ex}", file=sys.stderr)
        state["evaluation"] = evaluation.get_fallback_response(state["task"], ex)
        state["memory"].evaluation_outputs.append(state["evaluation"])
    return state


def review_gate(state: GraphState) -> str:
    """Conditional routing: FAIL goes to reflection, PASS goes to evaluation."""
    enable_reflection = os.getenv("ENABLE_REFLECTION", "true").lower() == "true"
    if enable_reflection and "FAIL" in state.get("review", "").upper():
        return "reflection"
    return "evaluation"


def build_graph(tool_registry: ToolRegistry):
    """Build the LangGraph with tool support.
    
    Args:
        tool_registry: ToolRegistry instance
        
    Returns:
        Compiled graph
    """
    planner, coding, review, reflection, evaluation = create_agents_with_tools(tool_registry)
    
    graph = StateGraph(GraphState)
    
    # Add nodes with closure over agents
    graph.add_node("planner", lambda state: planner_node(state, planner))
    graph.add_node("coding", lambda state: coding_node(state, coding, None))
    graph.add_node("review", lambda state: review_node(state, review))
    graph.add_node("reflection", lambda state: reflection_node(state, reflection))
    graph.add_node("recode", lambda state: recode_after_reflection_node(state, coding))
    graph.add_node("evaluation", lambda state: evaluate_node(state, evaluation))

    graph.set_entry_point("planner")
    graph.add_edge("planner", "coding")
    graph.add_edge("coding", "review")
    graph.add_conditional_edges("review", review_gate, {
        "reflection": "reflection",
        "evaluation": "evaluation",
    })
    graph.add_edge("reflection", "recode")
    graph.add_edge("recode", "review")
    graph.add_edge("evaluation", END)
    
    return graph.compile()


def validate_environment() -> bool:
    """Validate that required environment variables are set."""
    load_dotenv(BASE_DIR / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not api_key.strip():
        print("Error: OPENAI_API_KEY is not set.", file=sys.stderr)
        print("Please set OPENAI_API_KEY in .env file or environment variables.", file=sys.stderr)
        return False

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    print(f"Using model: {model}")
    return True


def main():
    """Main entry point for the task executor."""
    if not validate_environment():
        sys.exit(1)

    # Setup tools
    print("Setting up tool registry...")
    tool_registry = setup_tool_registry()
    print(f"[OK] Registered {len(tool_registry.list_tools())} tools")

    output_project_dir = "generated_projects/todo_feature_project"

    task = f"""Implement a practical C# feature in this repo.

IMPORTANT OUTPUT LOCATION RULE:
- Create all generated files ONLY under: {output_project_dir}
- Do not write outside that folder.
- Use file_tools.write_file for every created/updated file.

Requested implementation:
- Create a file Models/TodoItem.cs with properties: Id (int), Title (string), IsDone (bool), CreatedAtUtc (DateTime).
- Create a service file Services/TodoService.cs with methods:
  1) Add(string title) -> TodoItem
  2) MarkDone(int id) -> bool
  3) GetAll() -> IReadOnlyList<TodoItem>
- Add validation: title must be non-empty and <= 100 chars.
- Add a minimal demo usage snippet for Program.cs.

Path mapping requirement:
- Models/TodoItem.cs => {output_project_dir}/Models/TodoItem.cs
- Services/TodoService.cs => {output_project_dir}/Services/TodoService.cs
- Program.cs snippet => {output_project_dir}/Program.cs
- Use file_tools.write_file for every created/updated file.
- If code is shown in markdown output, include file paths clearly so they can be materialized.

Acceptance criteria:
- Compilable C# code
- Clear method signatures
- Handles missing id in MarkDone by returning false
- Includes brief unit-test suggestions."""

    print(f"Generated project directory: {output_project_dir}")
    output_dir_path = BASE_DIR / output_project_dir
    if output_dir_path.exists():
        import shutil
        shutil.rmtree(output_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Ensured output directory exists: {output_dir_path}")

    app = build_graph(tool_registry)
    initial: GraphState = {"task": task, "memory": RunMemory()}
    final_state = app.invoke(initial)

    # Safety net: if model claimed completion but didn't actually write files,
    # extract code blocks and materialize expected files under output folder.
    extracted = _extract_file_blocks_from_output(final_state.get("code", ""))
    if extracted:
        print(f"\nDEBUG: Found {len(extracted)} extracted files", file=sys.stderr)
        for orig_path, content in extracted.items():
            rel_path = _sanitize_relative_output_path(orig_path)
            print(f"DEBUG: Processing {orig_path} -> {rel_path}", file=sys.stderr)
            
            if not rel_path:
                print(f"DEBUG:   Skipping (empty path)", file=sys.stderr)
                continue
            
            is_complete = _is_complete_code_content(rel_path, content)
            print(f"DEBUG:   Is complete: {is_complete}", file=sys.stderr)
            
            if not is_complete:
                print(f"DEBUG:   Skipping (incomplete)", file=sys.stderr)
                continue
            
            # Force all generated output under configured project directory
            target = output_dir_path / rel_path
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content + "\n", encoding="utf-8")
                print(f"DEBUG:   Written to {target}", file=sys.stderr)
            except Exception as e:
                print(f"DEBUG:   ERROR writing to {target}: {e}", file=sys.stderr)

    # Create project file and execute if C# files were generated
    generated_files = [
        str(p.relative_to(BASE_DIR))
        for p in output_dir_path.rglob("*.cs")
        if p.is_file()
    ]
    
    execution_output = ""
    if generated_files:
        print(f"\nGenerating project file and preparing for execution...", file=sys.stderr)
        if _create_csharp_project_file(output_dir_path):
            success, exec_output = _build_and_execute_csharp(output_dir_path)
            execution_output = f"\n{'='*50}\n=== EXECUTION OUTPUT ===\n{'='*50}\n"
            if success:
                execution_output += f"[SUCCESS] Application executed successfully:\n\n{exec_output}"
            else:
                execution_output += f"[FAILED] Application execution failed:\n\n{exec_output}"

    print("\n" + "="*50)
    print("=== PLANNER OUTPUT ===")
    print("="*50)
    print(final_state.get("plan", ""))
    
    print("\n" + "="*50)
    print("=== CODING OUTPUT ===")
    print("="*50)
    print(final_state.get("code", ""))
    
    print("\n" + "="*50)
    print("=== REVIEW OUTPUT ===")
    print("="*50)
    print(final_state.get("review", ""))
    
    if final_state.get("reflection"):
        print("\n" + "="*50)
        print("=== REFLECTION OUTPUT ===")
        print("="*50)
        print(final_state.get("reflection", ""))
    
    print("\n" + "="*50)
    print("=== EVALUATION OUTPUT ===")
    print("="*50)
    print(final_state.get("evaluation", ""))

    # Post-run verification of generated files/folder
    existing = [
        str(p.relative_to(BASE_DIR))
        for p in output_dir_path.rglob("*")
        if p.is_file()
    ]

    print("\n" + "="*50)
    print("=== SUMMARY ===")
    print("="*50)
    
    # Show only generated source files
    source_files = [f for f in existing if f.endswith((".cs", ".csproj"))]
    print(f"Generated files: {len(source_files)}")
    for fp in sorted(source_files):
        if not any(x in fp for x in ["bin", "obj", ".deps", ".pdb", "runtimeconfig"]):
            print(f"  ✓ {fp}")
    
    # Show evaluation status
    eval_output = final_state.get("evaluation", "")
    if "Status: PASS" in eval_output:
        print("\nEvaluation: [PASS] ✓ Code meets all criteria")
    elif "Status: FAIL" in eval_output:
        print("\nEvaluation: [FAIL] ✗ Code needs improvements")
    else:
        # Extract first line or summary
        first_line = eval_output.split("\n")[0] if eval_output else ""
        print(f"\nEvaluation: {first_line}")

    if execution_output:
        print(execution_output)


if __name__ == "__main__":
    main()
