"""
Demonstration of tool calling in action (ReAct pattern).
Shows how agents can autonomously decide and execute tools.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Verify API key
if not os.getenv("OPENAI_API_KEY"):
    print("❌ Error: OPENAI_API_KEY not set")
    print("Please set OPENAI_API_KEY in .env file")
    sys.exit(1)

from agents import CodingAgent, ReviewAgent
from main_with_tools import setup_tool_registry


def demo_tool_calling_coding_agent():
    """Demonstrate CodingAgent using tools."""
    print("=" * 70)
    print("DEMO 1: CodingAgent with Tool Calling")
    print("=" * 70)
    
    # Setup
    registry = setup_tool_registry()
    agent = CodingAgent(BASE_DIR / "prompts", tool_registry=registry)
    
    task = "Create a simple Python module for managing users"
    context = """
    Requirements:
    - Create models/user.py with User class
    - Should have id, name, email fields
    - Create services/user_service.py with UserService class
    - Should have create(), get(), list() methods
    """
    
    print(f"\n📋 Task: {task}")
    print(f"\n📝 Context:\n{context}")
    print("\n🤖 Agent starting... (may call tools like read_file, write_file, check_syntax)")
    print("-" * 70)
    
    try:
        result = agent.execute(task, context)
        print("\n✅ Result:")
        print(result[:1000])  # First 1000 chars
        if len(result) > 1000:
            print("... (truncated)")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def demo_tool_calling_review_agent():
    """Demonstrate ReviewAgent using tools."""
    print("\n\n" + "=" * 70)
    print("DEMO 2: ReviewAgent with Tool Calling")
    print("=" * 70)
    
    # Setup
    registry = setup_tool_registry()
    agent = ReviewAgent(BASE_DIR / "prompts", tool_registry=registry)
    
    task = "Review Python code quality"
    code = """
def calculate_average(numbers):
    sum = 0
    for i in range(len(numbers)):
        sum = sum + numbers[i]
    return sum / len(numbers)
    """
    
    context = f"Code to review:\n```python\n{code}\n```"
    
    print(f"\n📋 Task: {task}")
    print(f"\n📝 Code to review:\n{code}")
    print("\n🤖 Agent starting... (may call tools like check_syntax, run_linter)")
    print("-" * 70)
    
    try:
        result = agent.review(task, context)
        print("\n✅ Review Result:")
        print(result[:1000])  # First 1000 chars
        if len(result) > 1000:
            print("... (truncated)")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def show_tool_execution_flow():
    """Show how tool calling works."""
    print("\n\n" + "=" * 70)
    print("TOOL CALLING FLOW (ReAct Pattern)")
    print("=" * 70)
    
    print("""
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Agent Receives Task                                      │
├─────────────────────────────────────────────────────────────────┤
│ Task: "Create and validate a Python file"                        │
└─────────────────────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: invoke_with_tools() Called                               │
├─────────────────────────────────────────────────────────────────┤
│ - Prompt includes tool descriptions                              │
│ - Max iterations: 3-5                                            │
└─────────────────────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: LLM Thinks & Acts                                        │
├─────────────────────────────────────────────────────────────────┤
│ LLM Response:                                                    │
│ "I'll start by reading the existing code structure..."          │
│ "Action: file_tools.read_file(path=models/user.py)"            │
└─────────────────────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: Parse Tool Call                                          │
├─────────────────────────────────────────────────────────────────┤
│ Extracted:                                                       │
│   - Tool: file_tools.read_file                                   │
│   - Args: {path: "models/user.py"}                               │
└─────────────────────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: Execute Tool                                             │
├─────────────────────────────────────────────────────────────────┤
│ Result: [file contents from models/user.py]                     │
│         or error if file not found                              │
└─────────────────────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: Observe & Continue                                       │
├─────────────────────────────────────────────────────────────────┤
│ Send tool result back to LLM                                    │
│ Add to conversation history                                      │
│ Loop back to LLM (STEP 3)                                       │
└─────────────────────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: Final Answer                                             │
├─────────────────────────────────────────────────────────────────┤
│ When LLM stops calling tools, return final response             │
│ OR max iterations reached                                        │
└─────────────────────────────────────────────────────────────────┘
""")


def show_tool_registry():
    """Display registered tools."""
    print("\n" + "=" * 70)
    print("REGISTERED TOOLS")
    print("=" * 70)
    
    registry = setup_tool_registry()
    tools = registry.list_tools()
    
    print(f"\n📚 Total Tools Registered: {len(tools)}\n")
    
    for i, tool_def in enumerate(tools, 1):
        print(f"{i}. {tool_def.name}")
        print(f"   Description: {tool_def.description}")
        print(f"   Parameters: {list(tool_def.parameters.keys())}")
        print()


if __name__ == "__main__":
    print("\n" + "🚀 " * 20)
    print("TOOL CALLING DEMONSTRATION")
    print("🚀 " * 20)
    
    # Show tool registry
    show_tool_registry()
    
    # Show flow diagram
    show_tool_execution_flow()
    
    # Run demos (requires OpenAI API key)
    print("\n⚠️  Running live demos requires OPENAI_API_KEY")
    print("Attempting to run live demos...\n")
    
    try:
        demo_tool_calling_coding_agent()
        demo_tool_calling_review_agent()
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("\nNote: If you see OpenAI API errors, ensure:")
        print("  1. OPENAI_API_KEY is set in .env file")
        print("  2. Your API key is valid and has credits")
        print("  3. Your internet connection is working")
