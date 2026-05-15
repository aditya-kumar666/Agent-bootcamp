from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import TypedDict

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

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"

# Initialize agents
planner_agent = PlannerAgent(PROMPTS_DIR)
coding_agent = CodingAgent(PROMPTS_DIR)
review_agent = ReviewAgent(PROMPTS_DIR)
reflection_agent = ReflectionAgent(PROMPTS_DIR)
evaluation_agent = EvaluationAgent(PROMPTS_DIR)


class GraphState(TypedDict, total=False):
    task: str
    plan: str
    code: str
    review: str
    reflection: str
    evaluation: str
    memory: RunMemory


def planner_node(state: GraphState) -> GraphState:
    """Planner node: plan the task."""
    try:
        out = planner_agent.plan(state["task"])
        state["plan"] = out
        state["memory"].planner_outputs.append(out)
    except Exception as ex:
        print(f"Error in planner node: {ex}", file=sys.stderr)
        state["plan"] = planner_agent.get_fallback_response(state["task"], ex)
        state["memory"].planner_outputs.append(state["plan"])
    return state


def coding_node(state: GraphState) -> GraphState:
    """Coding node: generate code based on plan."""
    try:
        user_input = f"{state['task']}\n\nPlan:\n{state['plan']}\n\n{state['memory'].build_context_snapshot()}"
        out = coding_agent.execute(state["task"], user_input)
        state["code"] = out
        state["memory"].coding_outputs.append(out)
    except Exception as ex:
        print(f"Error in coding node: {ex}", file=sys.stderr)
        state["code"] = coding_agent.get_fallback_response(state["task"], "", ex)
        state["memory"].coding_outputs.append(state["code"])
    return state


def review_node(state: GraphState) -> GraphState:
    """Review node: review the generated code."""
    try:
        user_input = f"{state['task']}\n\nCode:\n{state['code']}\n\n{state['memory'].build_context_snapshot()}"
        out = review_agent.review(state["task"], user_input)
        state["review"] = out
        state["memory"].review_outputs.append(out)
    except Exception as ex:
        print(f"Error in review node: {ex}", file=sys.stderr)
        state["review"] = review_agent.get_fallback_response(state["task"], ex)
        state["memory"].review_outputs.append(state["review"])
    return state


def reflection_node(state: GraphState) -> GraphState:
    """Reflection node: reflect on review feedback and suggest improvements."""
    try:
        user_input = (
            f"Task:\n{state['task']}\n\n"
            f"Current Code:\n{state['code']}\n\n"
            f"Review Feedback:\n{state['review']}\n\n"
            f"{state['memory'].build_context_snapshot()}"
        )
        out = reflection_agent.reflect(state["task"], state["code"], state["review"])
        state["reflection"] = out
        state["memory"].reflection_outputs.append(out)
    except Exception as ex:
        print(f"Error in reflection node: {ex}", file=sys.stderr)
        state["reflection"] = reflection_agent.get_fallback_response(ex)
        state["memory"].reflection_outputs.append(state["reflection"])
    return state


def recode_after_reflection_node(state: GraphState) -> GraphState:
    """Recode node: regenerate code based on reflection."""
    try:
        user_input = f"{state['task']}\n\nReflection:\n{state['reflection']}\n\n{state['memory'].build_context_snapshot()}"
        out = coding_agent.execute(state["task"], user_input)
        state["code"] = out
        state["memory"].coding_outputs.append(out)
    except Exception as ex:
        print(f"Error in recode node: {ex}", file=sys.stderr)
        state["code"] = coding_agent.get_fallback_response(state["task"], "", ex)
        state["memory"].coding_outputs.append(state["code"])
    return state


def evaluate_node(state: GraphState) -> GraphState:
    """Evaluation node: evaluate the final output."""
    try:
        out = evaluation_agent.evaluate(state["task"], state.get("review", ""))
        state["evaluation"] = out
        state["memory"].evaluation_outputs.append(out)
    except Exception as ex:
        print(f"Error in evaluation node: {ex}", file=sys.stderr)
        state["evaluation"] = evaluation_agent.get_fallback_response(state["task"], ex)
        state["memory"].evaluation_outputs.append(state["evaluation"])
    return state


def review_gate(state: GraphState) -> str:
    enable_reflection = os.getenv("ENABLE_REFLECTION", "true").lower() == "true"
    if enable_reflection and "FAIL" in state.get("review", "").upper():
        return "reflection"
    return "evaluation"


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("planner", planner_node)
    graph.add_node("coding", coding_node)
    graph.add_node("review", review_node)
    graph.add_node("reflection", reflection_node)
    graph.add_node("recode", recode_after_reflection_node)
    graph.add_node("evaluation", evaluate_node)

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

    task = """Implement a practical C# feature in this repo:
- Create a file Models/TodoItem.cs with properties: Id (int), Title (string), IsDone (bool), CreatedAtUtc (DateTime).
- Create a service file Services/TodoService.cs with methods:
  1) Add(string title) -> TodoItem
  2) MarkDone(int id) -> bool
  3) GetAll() -> IReadOnlyList<TodoItem>
- Add validation: title must be non-empty and <= 100 chars.
- Add a minimal demo usage snippet for Program.cs.
Acceptance criteria:
- Compilable C# code
- Clear method signatures
- Handles missing id in MarkDone by returning false
- Includes brief unit-test suggestions."""

    app = build_graph()
    initial: GraphState = {"task": task, "memory": RunMemory()}
    final_state = app.invoke(initial)

    print("\n=== PLANNER OUTPUT ===")
    print(final_state.get("plan", ""))
    print("\n=== CODING OUTPUT ===")
    print(final_state.get("code", ""))
    print("\n=== REVIEW OUTPUT ===")
    print(final_state.get("review", ""))
    if final_state.get("reflection"):
        print("\n=== REFLECTION OUTPUT ===")
        print(final_state.get("reflection", ""))
    print("\n=== EVALUATION OUTPUT ===")
    print(final_state.get("evaluation", ""))


if __name__ == "__main__":
    main()
