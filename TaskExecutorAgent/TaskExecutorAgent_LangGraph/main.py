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
from guardrails import build_context_snapshot_with_budget
from memory.run_memory import RunMemory
from plugins import FileToolsPlugin, TestToolsPlugin, ToolRegistry, ToolExecutor, AgenticLoop, BuilderFactory, MCPToolManager

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"


def is_verbose_logging_enabled() -> bool:
    """Enable noisy diagnostics only when VERBOSE_LOGS=true."""
    return os.getenv("VERBOSE_LOGS", "false").lower() == "true"


def verbose_log(message: str) -> None:
    """Print non-essential logs only in verbose mode."""
    if is_verbose_logging_enabled():
        print(message, file=sys.stderr, flush=True)


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


def _materialize_files(extracted: dict, output_dir_path: Path) -> int:
    """Materialize extracted code files to disk.
    
    Args:
        extracted: Dict of {path: content} to write
        output_dir_path: Target directory
        
    Returns:
        Number of files successfully written
    """
    written = 0
    if extracted:
        verbose_log(f"\nDEBUG: Found {len(extracted)} extracted files")
        for orig_path, content in extracted.items():
            rel_path = _sanitize_relative_output_path(orig_path)
            verbose_log(f"DEBUG: Processing {orig_path} -> {rel_path}")
            
            if not rel_path:
                verbose_log("DEBUG:   Skipping (empty path)")
                continue
            
            is_complete = _is_complete_code_content(rel_path, content)
            verbose_log(f"DEBUG:   Is complete: {is_complete}")
            
            if not is_complete:
                verbose_log("DEBUG:   Skipping (incomplete)")
                continue
            
            # Force all generated output under configured project directory
            target = output_dir_path / rel_path
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content + "\n", encoding="utf-8")
                verbose_log(f"DEBUG:   Written to {target}")
                written += 1
            except Exception as e:
                print(f"[ERROR] Failed to write generated file {target}: {e}", file=sys.stderr)
    return written


def _build_with_retry(builder, output_dir_path: Path, task: str, tool_registry: ToolRegistry,
                       lang_display: str, max_retries: int = 3) -> tuple[bool, str]:
    """Build and execute with automatic retry on error.
    
    When execution fails, feeds error back to coding agent for regeneration.
    
    Args:
        builder: ProjectBuilder instance
        output_dir_path: Output directory path
        task: Original task description
        tool_registry: Tool registry for agent execution
        lang_display: Language display name for feedback
        max_retries: Maximum number of retry attempts
        
    Returns:
        Tuple of (success: bool, output: str)
    """
    attempt = 0
    last_error = ""
    
    while attempt < max_retries:
        attempt += 1
        verbose_log(f"\n[RETRY {attempt}/{max_retries}] Building and executing {lang_display} project...")
        
        success, exec_output = builder.build_and_execute()
        
        if success:
            verbose_log(f"[OK] Execution succeeded on attempt {attempt}")
            return True, exec_output
        
        # Execution failed - capture error
        last_error = exec_output
        error_preview = (exec_output[:300] + "...") if len(exec_output) > 300 else exec_output
        print(f"[ERROR] Execution failed: {error_preview}", file=sys.stderr, flush=True)
        
        if attempt < max_retries:
            verbose_log(f"\n[REGENERATE] Attempting to fix code (attempt {attempt + 1}/{max_retries})...")
            
            # Create feedback-based coding task
            fix_task = f"""{task}

PREVIOUS EXECUTION ERROR (attempt {attempt}):
{last_error}

Please fix the above error and regenerate all files. Ensure:
1. The code handles all edge cases
2. All imports are correct  
3. No syntax errors exist
4. The application can execute successfully"""
            
            # Regenerate code with feedback
            try:
                coding_agent = CodingAgent(PROMPTS_DIR, tool_registry)
                regenerated_code = coding_agent.execute(fix_task, fix_task)
                
                # Extract and materialize new files
                extracted = _extract_file_blocks_from_output(regenerated_code)
                written = _materialize_files(extracted, output_dir_path)
                verbose_log(f"[OK] Regenerated and wrote {written} files")
                
                # Clean up build artifacts for next attempt
                import shutil
                for pattern in ["bin", "obj", "target", "dist", "__pycache__"]:
                    artifact_dir = output_dir_path / pattern
                    if artifact_dir.exists():
                        try:
                            shutil.rmtree(artifact_dir)
                            verbose_log(f"[OK] Cleaned {pattern} directory")
                        except:
                            pass
                
            except Exception as e:
                print(f"[ERROR] Regeneration failed: {e}", file=sys.stderr, flush=True)
                last_error = str(e)
        else:
            print(f"\n[FAILED] Max retries ({max_retries}) exceeded", file=sys.stderr, flush=True)
            break
    
    return False, last_error


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
    
    # Phase 3: Register MCP tools with verbose output
    mcp_config_path = BASE_DIR / "mcp_servers.json"
    try:
        mcp_manager = MCPToolManager(mcp_config_path)
        mcp_registered = mcp_manager.register_all(registry, verbose=is_verbose_logging_enabled())
        if mcp_registered:
            verbose_log(f"[OK] Registered {mcp_registered} MCP tools from {len(mcp_manager.get_registered_servers())} servers")
            if mcp_manager.get_registered_servers():
                verbose_log(f"     Servers: {', '.join(mcp_manager.get_registered_servers())}")
    except Exception as ex:
        print(f"[WARN] MCP tools not loaded: {ex}", file=sys.stderr)

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
        memory_context = build_context_snapshot_with_budget(state["memory"])
        user_input = f"{state['task']}\n\nPlan:\n{state['plan']}\n\n{memory_context}"
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
        memory_context = build_context_snapshot_with_budget(state["memory"])
        user_input = f"{state['task']}\n\nCode:\n{state['code']}\n\n{memory_context}"
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
        memory_context = build_context_snapshot_with_budget(state["memory"])
        user_input = (
            f"Task:\n{state['task']}\n\n"
            f"Current Code:\n{state['code']}\n\n"
            f"Review Feedback:\n{state['review']}\n\n"
            f"{memory_context}"
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
        memory_context = build_context_snapshot_with_budget(state["memory"])
        user_input = f"{state['task']}\n\nReflection:\n{state['reflection']}\n\n{memory_context}"
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
    verbose_log(f"Using model: {model}")
    return True


def print_memory_token_report(memory: RunMemory) -> None:
    """Print memory token usage at the end of a run."""
    print("\n" + "="*50)
    print("=== MEMORY TOKEN USAGE ===")
    print("="*50)
    print(f"Total memory tokens: {memory.get_total_memory_tokens()}")
    print("Token breakdown:")
    for buffer_name, token_count in memory.get_token_breakdown().items():
        print(f"- {buffer_name}: {token_count}")


def main(language: str = "csharp"):
    """Main entry point for the task executor.
    
    Args:
        language: Programming language for code generation (default: "csharp")
                 Supported: csharp, java, python, go
    """
    if not validate_environment():
        sys.exit(1)

    # Setup tools
    verbose_log("Setting up tool registry...")
    tool_registry = setup_tool_registry()
    verbose_log(f"[OK] Registered {len(tool_registry.list_tools())} tools")

    output_project_dir = "generated_projects/todo_feature_project"
    
    # Map language to code hints
    language_hints = {
        "csharp": "C#/.NET",
        "java": "Java",
        "python": "Python",
        "go": "Go",
    }
    lang_display = language_hints.get(language.lower(), language)

    task = f"""Implement a practical {lang_display} feature in this repo.

IMPORTANT OUTPUT LOCATION RULE:
- Create all generated files ONLY under: {output_project_dir}
- Do not write outside that folder.
- Use file_tools.write_file for every created/updated file.

Requested implementation:
- Create a file Models/TodoItem with properties: Id (int), Title (string), IsDone (bool), CreatedAt (timestamp).
- Create a service file Services/TodoService with methods:
  1) Add(title) -> TodoItem
  2) MarkDone(id) -> bool
  3) GetAll() -> List/Array of TodoItems
- Add validation: title must be non-empty and <= 100 chars.
- Add a minimal demo usage snippet in the main entry point file.

Path mapping requirement:
- Models/TodoItem -> {output_project_dir}/Models/TodoItem (appropriate extension for {lang_display})
- Services/TodoService -> {output_project_dir}/Services/TodoService (appropriate extension for {lang_display})
- Main entry point -> {output_project_dir}/Main (appropriate extension for {lang_display})
- Use file_tools.write_file for every created/updated file.
- If code is shown in markdown output, include file paths clearly so they can be materialized.

Acceptance criteria:
- Compilable/runnable {lang_display} code
- Clear method signatures
- Handles missing id in MarkDone by returning false
- Includes brief unit-test suggestions."""

    verbose_log(f"Generated project directory: {output_project_dir}")
    output_dir_path = BASE_DIR / output_project_dir
    if output_dir_path.exists():
        import shutil
        shutil.rmtree(output_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    verbose_log(f"[OK] Ensured output directory exists: {output_dir_path}")

    app = build_graph(tool_registry)
    initial: GraphState = {"task": task, "memory": RunMemory()}
    final_state = app.invoke(initial)

    # Safety net: extract and materialize generated files
    extracted = _extract_file_blocks_from_output(final_state.get("code", ""))
    _materialize_files(extracted, output_dir_path)

    # Setup builder for the target language
    verbose_log(f"\nSetting up {lang_display} builder...")
    try:
        builder = BuilderFactory.get_builder(language, output_dir_path)
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate environment
    if not builder.validate_environment():
        print(f"[ERROR] {lang_display} environment validation failed", file=sys.stderr)
        sys.exit(1)
    
    # Setup project structure
    if not builder.setup_project():
        print(f"[ERROR] Failed to setup {lang_display} project", file=sys.stderr)
        sys.exit(1)
    
    # Build and execute with automatic retry on error
    verbose_log(f"\nStarting {lang_display} build with error recovery...")
    success, exec_output = _build_with_retry(
        builder, output_dir_path, task, tool_registry, lang_display, max_retries=3
    )
    
    execution_output = f"\n{'='*50}\n=== EXECUTION OUTPUT ===\n{'='*50}\n"
    if success:
        execution_output += f"[SUCCESS] Application executed successfully after retries:\n\n{exec_output}"
    else:
        execution_output += f"[FAILED] Application execution failed after all retry attempts:\n\n{exec_output}"

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
    print_memory_token_report(final_state["memory"])

    # Post-run verification of generated files/folder
    existing = [
        str(p.relative_to(BASE_DIR))
        for p in output_dir_path.rglob("*")
        if p.is_file()
    ]

    print("\n" + "="*50)
    print("=== SUMMARY ===")
    print("="*50)
    
    # Show only generated source files (exclude build artifacts)
    source_files = [f for f in existing 
                   if not any(x in f for x in ["bin", "obj", ".deps", ".pdb", "runtimeconfig"])]
    print(f"Generated files: {len(source_files)}")
    for fp in sorted(source_files):
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
    import sys
    
    # Parse command-line arguments
    language = "csharp"  # default
    if len(sys.argv) > 1:
        language = sys.argv[1]
    
    # Show usage info
    if language in ["-h", "--help", "help"]:
        print("\nMulti-Language Task Executor")
        print("="*60)
        print("\nUsage:")
        print("  python main_with_tools.py [language]")
        print("\nSupported languages:")
        print("  csharp (default)  - Generate C#/.NET Todo app")
        print("  java              - Generate Java Todo app (requires Maven)")
        print("  python            - Generate Python Todo app")
        print("  go                - Generate Go Todo app (requires Go SDK)")
        print("\nExamples:")
        print("  python main_with_tools.py              # Default C#")
        print("  python main_with_tools.py java         # Java app")
        print("  python main_with_tools.py python       # Python app")
        print("  python main_with_tools.py go           # Go app")
        print()
        sys.exit(0)
    
    main(language=language)
