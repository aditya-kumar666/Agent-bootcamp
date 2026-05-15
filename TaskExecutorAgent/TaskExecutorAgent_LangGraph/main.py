from __future__ import annotations
import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from memory.run_memory import RunMemory

BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"

class GraphState(TypedDict, total=False):
    task: str
    plan: str
    code: str
    review: str
    reflection: str
    evaluation: str
    memory: RunMemory


def _read_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _llm() -> ChatOpenAI:
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return ChatOpenAI(model=model, temperature=0)


def _invoke(agent_name: str, system_prompt: str, user_input: str) -> str:
    llm = _llm()
    msg = [
        ("system", system_prompt),
        ("user", user_input),
    ]
    return llm.invoke(msg).content


def planner_node(state: GraphState) -> GraphState:
    out = _invoke("planner", _read_prompt("planner.txt"), state["task"])
    state["plan"] = out
    state["memory"].planner_outputs.append(out)
    return state


def coding_node(state: GraphState) -> GraphState:
    user_input = f"{state['task']}\n\nPlan:\n{state['plan']}\n\n{state['memory'].build_context_snapshot()}"
    out = _invoke("coding", _read_prompt("coding.txt"), user_input)
    state["code"] = out
    state["memory"].coding_outputs.append(out)
    return state


def review_node(state: GraphState) -> GraphState:
    user_input = f"{state['task']}\n\nCode:\n{state['code']}\n\n{state['memory'].build_context_snapshot()}"
    out = _invoke("review", _read_prompt("review.txt"), user_input)
    state["review"] = out
    state["memory"].review_outputs.append(out)
    return state


def reflection_node(state: GraphState) -> GraphState:
    user_input = (
        f"Task:\n{state['task']}\n\n"
        f"Current Code:\n{state['code']}\n\n"
        f"Review Feedback:\n{state['review']}\n\n"
        f"{state['memory'].build_context_snapshot()}"
    )
    out = _invoke("reflection", _read_prompt("reflection.txt"), user_input)
    state["reflection"] = out
    state["memory"].reflection_outputs.append(out)
    return state


def recode_after_reflection_node(state: GraphState) -> GraphState:
    user_input = f"{state['task']}\n\nReflection:\n{state['reflection']}\n\n{state['memory'].build_context_snapshot()}"
    out = _invoke("coding", _read_prompt("coding.txt"), user_input)
    state["code"] = out
    state["memory"].coding_outputs.append(out)
    return state


def evaluate_node(state: GraphState) -> GraphState:
    user_input = f"{state['task']}\n\nReview:\n{state['review']}\n\n{state['memory'].build_context_snapshot()}"
    out = _invoke("evaluation", _read_prompt("evaluation.txt"), user_input)
    state["evaluation"] = out
    state["memory"].evaluation_outputs.append(out)
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


def main():
    load_dotenv(BASE_DIR / ".env")

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
