# TaskExecutorAgent_LangGraph

A **multi-agent AI SDLC orchestration system** that automates software development tasks using LangGraph and LangChain. The system mirrors the C# SemanticKernel implementation and simulates autonomous AI workflows similar to Cursor, Claude Code, Devin, and Copilot Workspace.

## 🎯 What It Does

This system takes a **user-defined software development task** and orchestrates a team of AI agents to:

1. **Plan** the implementation strategy
2. **Code** the solution with context awareness
3. **Review** the code for quality and correctness
4. **Reflect** (if needed) on failures and suggest improvements
5. **Evaluate** the final output against acceptance criteria

The workflow is autonomous and includes retry logic—if review reveals issues, the system reflects on the problem and re-codes until it passes review or reaches max retries.

## 🏗️ Architecture

```
                           ┌─────────────────┐
                           │   User Task     │
                           └────────┬────────┘
                                    │
                           ┌────────▼────────┐
                           │  Planner Agent  │
                           │ (Plan Strategy) │
                           └────────┬────────┘
                                    │
                           ┌────────▼────────┐
                           │  Coding Agent   │
                           │(Generate Code)  │
                           └────────┬────────┘
                                    │
                           ┌────────▼────────┐
                           │  Review Agent   │
                           │(Assess Quality) │
                           └────────┬────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
              Pass Review               Fail Review
                    │                               │
                    ▼                               ▼
          ┌──────────────────┐        ┌─────────────────────┐
          │ Evaluation Agent │        │ Reflection Agent    │
          │ (Final Verdict)  │        │ (Diagnose Issues)   │
          └────────┬─────────┘        └──────────┬──────────┘
                   │                             │
                   │                    ┌────────▼────────┐
                   │                    │  Recode Agent   │
                   │                    │ (Fix & Retry)   │
                   │                    └────────┬────────┘
                   │                             │
                   │                    ┌────────▼────────┐
                   │                    │ Review Again    │
                   │                    └────────┬────────┘
                   │                             │
                   │         ┌───────────────────┘
                   │         │
                   └────────►FINAL OUTPUT
```

---

## 📂 Project Structure & Module Responsibilities

### **`agents/`** - AI Agent Implementations
Responsible for executing specific tasks in the SDLC pipeline using LLMs.

- **`base_agent.py`** - Abstract base class providing:
  - LLM invocation (ChatOpenAI wrapper)
  - Prompt file reading with error handling
  - Lazy LLM initialization for efficiency
  - Fallback response interface

- **`planner_agent.py`** - **Planning Phase**
  - Breaks down user task into numbered implementation steps
  - Provides strategic guidance for coding tasks
  - Output: Structured plan with step goals and expected outputs

- **`coding_agent.py`** - **Code Generation Phase**
  - Generates implementation code based on task and plan
  - Receives reflection feedback if previous attempt failed
  - Integrates with FileTools for file operations
  - Output: Complete code implementation

- **`review_agent.py`** - **Quality Review Phase**
  - Reviews code for correctness, edge cases, style
  - Checks against best practices and architecture
  - Identifies blocking issues vs. warnings
  - Output: Review verdict with specific findings

- **`reflection_agent.py`** - **Failure Analysis Phase**
  - Analyzes why review failed
  - Diagnoses root causes of issues
  - Suggests corrected approach
  - Output: Improvement strategy and next steps

- **`evaluation_agent.py`** - **Final Evaluation Phase**
  - Validates code against acceptance criteria
  - Checks test results
  - Generates final pass/fail verdict
  - Output: Structured evaluation with risk assessment

---

### **`models/`** - Data Structures
Defines typed data models for task specifications and execution results.

- **`user_task.py`** - Task Input Model
  - `title`: Brief task name
  - `description`: Detailed task requirements
  - `acceptance_criteria`: Success conditions
  - Includes Pydantic validation

- **`agent_result.py`** - Execution Result Model
  - `success`: Boolean execution status
  - `output`: Result content
  - `error`: Optional error message
  - Structured return value for all agents

- **`execution_context.py`** - Execution State Tracker
  - `steps`: List of execution steps taken
  - `tool_logs`: Output from tool invocations
  - `changed_files`: Files modified during execution
  - `retry_count`: Number of retry attempts
  - Methods: `add_step()`, `add_tool_log()`, `add_changed_file()`, `increment_retry()`, `get_summary()`
  - Provides complete execution audit trail

---

### **`plugins/`** - Tool Integrations
Plugins that agents can invoke to interact with external systems.

- **`file_tools.py`** - File System Operations
  - `read_file(path)`: Read file content with workspace boundary checks
  - `write_file(path, content)`: Write files safely within workspace
  - `search_files(pattern)`: Find files by pattern matching
  - `list_directory(path)`: List directory contents
  - `delete_file(path)`: Delete files with safety validation
  - Security: Prevents directory traversal attacks, validates all paths

- **`test_tools.py`** - Test Execution & Validation
  - `run_tests(filter, timeout)`: Execute pytest with optional filtering
  - `run_unittest(module, timeout)`: Run unittest tests
  - `check_syntax(file)`: Validate Python syntax without execution
  - `run_linter(file, timeout)`: Run flake8 code quality checks
  - Includes timeout protection for long-running tests

---

### **`evaluation/`** - Task Evaluation Rules
Provides evaluation logic and structured results.

- **`evaluation_rules.py`** - Evaluation Engine
  - `EvaluationRules` class with static methods:
    - `extract_status_from_review()`: Parse PASS/FAIL from review text
    - `extract_issues_from_review()`: Extract identified issues
    - `assess_risk()`: Calculate risk level (low/medium/high)
  - `EvaluationResult` model: Structured evaluation output
  - `TaskStatus` enum: PASS, FAIL, PARTIAL states

---

### **`services/`** - Orchestration Services
High-level services that coordinate workflow behavior.

- **`retry_orchestrator.py`** - Retry Logic Manager
  - `should_retry()`: Determine if retry needed based on review feedback
  - `execute_with_retry()`: Orchestrate full retry workflow
  - `get_config()`: Return current configuration
  - Respects `MAX_RETRIES` and `ENABLE_REFLECTION` settings
  - Coordinates planner → coding → review loop

---

### **`memory/`** - Execution Context & History
Tracks outputs from each agent for context building.

- **`run_memory.py`** - Execution Memory
  - `planner_outputs`: Store all planning outputs
  - `coding_outputs`: Store all code generation outputs
  - `review_outputs`: Store all review findings
  - `reflection_outputs`: Store all reflection analyses
  - `evaluation_outputs`: Store final evaluations
  - `build_context_snapshot()`: Create rich context for LLM decision-making
  - Used by agents to inform subsequent decisions

---

### **`prompts/`** - LLM System Prompts
Text files defining agent behavior and instructions.

- **`planner.txt`** - Planner system prompt
  - Instructs agent to break down tasks into steps
  - Specifies output format

- **`coding.txt`** - Coding system prompt
  - Instructs agent to implement code changes
  - Defines implementation strategy

- **`review.txt`** - Review system prompt
  - Instructs agent to review code quality
  - Specifies what to check

- **`reflection.txt`** - Reflection system prompt
  - Instructs agent to analyze failures
  - Defines improvement suggestions

- **`evaluation.txt`** - Evaluation system prompt
  - Instructs agent to validate against criteria
  - Defines evaluation structure

---

### **`main.py`** - LangGraph Orchestration
The main entry point that orchestrates the entire workflow.

**Responsibilities:**
- Initialize LangGraph StateGraph with execution nodes
- Load environment variables and validate API keys
- Create task state with UserTask and RunMemory
- Define graph edges (workflow connections)
- Implement conditional routing (pass vs. fail paths)
- Execute the compiled graph
- Format and display results

**Graph Structure:**
```
planner → coding → review → [conditional decision]
                                ├─ FAIL → reflection → recode → review (loop)
                                └─ PASS → evaluation → END
```

---

## 🚀 Step-by-Step Execution Guide

### **Step 1: Installation & Setup**

```bash
# Navigate to project directory
cd TaskExecutorAgent_LangGraph

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **Step 2: Configure Environment**

```bash
# Copy example configuration
copy .env.example .env
# Or on macOS/Linux:
cp .env.example .env

# Edit .env file and add your OpenAI API key
# Open .env in your editor and fill in:
OPENAI_API_KEY=sk-...your_key_here...
```

**Required Variables:**
- `OPENAI_API_KEY`: Your OpenAI API key (required)

**Optional Variables:**
- `OPENAI_MODEL`: LLM model to use (default: `gpt-4o-mini`)
- `ENABLE_REFLECTION`: Enable retry on failure (default: `true`)
- `ENABLE_MEMORY`: Enable memory context (default: `true`)
- `MAX_RETRIES`: Maximum retry attempts (default: `2`)

### **Step 3: Verify Installation**

```bash
# Test all imports work correctly
python -c "from agents import *; from models import *; print('✓ All imports successful')"

# Test graph builds
python -c "from main import build_graph; app = build_graph(); print('✓ Graph ready')"
```

### **Step 4: Run the System**

```bash
# Execute the agent workflow
python main.py
```

**Output Example:**
```
Using model: gpt-4o-mini

=== PLANNER OUTPUT ===
1. Analyze task requirements
2. Design implementation strategy
3. Create implementation plan
...

=== CODING OUTPUT ===
# Generated code implementation
class TodoItem:
    ...

=== REVIEW OUTPUT ===
PASS: Code meets quality standards
- Correct syntax
- Proper error handling
- Good documentation
...

=== EVALUATION OUTPUT ===
Status: PASS
AcceptanceCriteria: Met
Tests: Passed
OpenIssues: None
Risk: low
FinalSummary: Task completed successfully
```

---

## 📋 Workflow Examples

### **Example 1: Simple Code Generation**

```
Task: "Create a Python function to validate email addresses"
  ↓
Planner → Plan: 1) Design validator, 2) Implement regex, 3) Add tests
  ↓
Coding → Generated: email_validator() function
  ↓
Review → Result: PASS - Code is correct and well-documented
  ↓
Evaluation → Status: PASS, Risk: low
```

### **Example 2: Code With Retry**

```
Task: "Implement async database connection pooling"
  ↓
Planner → Detailed plan
  ↓
Coding → Initial implementation
  ↓
Review → Result: FAIL - Missing error handling
  ↓
Reflection → "Add try-catch around connection attempts"
  ↓
Recode → Improved implementation with error handling
  ↓
Review → Result: PASS
  ↓
Evaluation → Status: PASS, Risk: medium (1 retry)
```

---

## ⚙️ Configuration & Customization

### **Custom Tasks**

Edit `main.py` to define a custom task:

```python
task = """Create a REST API endpoint that:
- Accepts POST requests with user data
- Validates input using Pydantic
- Returns JSON response
Acceptance criteria:
- Must handle invalid input gracefully
- Must include proper error messages
- Code must be type-annotated
"""
```

### **Tool Plugins Usage**

Agents can invoke tools like:

```python
# In an agent's context:
file_tools = FileToolsPlugin()
content = file_tools.read_file("models/user.py")
file_tools.write_file("models/user.py", updated_content)
```

### **Retry Configuration**

Control retry behavior via environment:

```env
ENABLE_REFLECTION=false      # Disable retry
MAX_RETRIES=5                 # Increase max retries
```

---

## 🔍 Monitoring & Debugging

### **View Execution Memory**

The `RunMemory` class tracks all outputs:

```python
memory = RunMemory()
print(memory.build_context_snapshot())
# Output: Shows count of outputs from each agent
```

### **Check Execution Context**

Track what happened during execution:

```python
ctx = ExecutionContext()
ctx.add_step("Planning started")
ctx.add_tool_log("File read: models/user.py")
ctx.add_changed_file("models/user.py")
print(ctx.get_summary())
```

### **Enable Debug Logging**

All nodes log errors to stderr for troubleshooting:

```bash
python main.py 2>&1 | tee debug.log
```

---

## 📊 Module Dependency Graph

```
main.py
  ├─ agents/ (all 6 agents)
  │  └─ base_agent.py (LLM + prompt loading)
  ├─ models/ (data structures)
  │  ├─ user_task.py
  │  ├─ agent_result.py
  │  └─ execution_context.py
  ├─ memory/
  │  └─ run_memory.py
  ├─ plugins/ (tool invocation)
  │  ├─ file_tools.py
  │  └─ test_tools.py
  ├─ evaluation/
  │  └─ evaluation_rules.py
  ├─ services/
  │  └─ retry_orchestrator.py
  └─ prompts/ (system instructions)
     ├─ planner.txt
     ├─ coding.txt
     ├─ review.txt
     ├─ reflection.txt
     └─ evaluation.txt
```

---

## ⚠️ Error Handling & Fallbacks

All agents include **offline fallback responses**:

- If LLM API is unavailable → Returns safe fallback output
- If file operation fails → Returns error status
- If test execution fails → Returns test output with error
- Workflow continues with degraded functionality

Example:
```
[OFFLINE_PLAN] 1) Analyze task 2) Propose changes 3) Validate output. Reason: Connection timeout
```

---

## 🔐 Security Features

- **Path Validation**: FileTools prevents directory traversal
- **Workspace Boundary**: All file operations confined to workspace root
- **Timeout Protection**: All tools have configurable timeouts
- **API Key Protection**: Never logs sensitive information
- **Syntax Validation**: Code checked before execution

---

## 📚 Additional Resources

### **Comparison with C# Version**

| Aspect | C# (SemanticKernel) | Python (LangGraph) |
|--------|---------------------|-------------------|
| Framework | Semantic Kernel | LangChain + LangGraph |
| Data Models | C# Records | Pydantic + Dataclasses |
| Workflow | Sequential | LangGraph StateGraph |
| Tools | KernelFunction | Python Methods |
| Orchestration | Manual loops | Graph-based |
| Memory | List-based | List-based |

### **Dependencies**

See `requirements.txt`:
- `langgraph>=0.2.34` - Workflow orchestration
- `langchain-openai>=0.2.0` - OpenAI integration
- `python-dotenv>=1.0.1` - Environment configuration
- `pydantic>=2.8.2` - Data validation

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` in virtual environment |
| `OPENAI_API_KEY not set` | Add key to `.env` file |
| `Connection timeout` | Check internet connection and API key validity |
| `Graph build error` | Verify all prompt files exist in `prompts/` folder |
| `Tool execution failed` | Check file paths are within workspace root |

---

## 📝 License & Attribution

This is a Python implementation of the AI SDLC Agent pattern, inspired by tools like Cursor, Claude Code, Devin, and Copilot Workspace.

---

## 🔧 Tool Calling and Execution Flow

This project supports **agentic tool calling** using the ReAct pattern (**Think → Act → Observe**).

### Tool Components
- **`plugins/tool_registry.py`**: Registers tools and exposes tool metadata/descriptions.
- **`plugins/tool_executor.py`**: Parses tool-call text and executes the mapped callable.
- **`plugins/agentic_loop.py`**: Iterative reasoning loop for tool usage.
- **`plugins/file_tools.py`** / **`plugins/test_tools.py`**: Concrete tool implementations.

### High-Level Flow
1. Agent receives task + context.
2. Agent prompt includes available tools (name, purpose, params).
3. LLM responds with either:
   - final answer, or
   - tool action like: `Action: file_tools.read_file(path=models/user.py)`
4. Tool executor parses action and resolves it via registry.
5. Tool function is executed and result is captured.
6. Result is appended back into conversation context.
7. LLM continues next iteration until no more tool actions.

### Runtime Call Path (Typical)
- `CodingAgent.execute(...)` / `ReviewAgent.review(...)`
  → `BaseAgent.invoke_with_tools(...)`
  → parse action
  → `ToolExecutor.execute_tool(...)`
  → mapped plugin method (e.g., `FileToolsPlugin.read_file(...)`)
  → observation returned to LLM
  → final response.

### Supported Action Formats
- ReAct style: `Action: tool_name(arg=value)`
- JSON style: `{"tool": "tool_name", "args": {...}}`
- Markdown fenced tool payloads.

### Example
```text
Thought: I should inspect existing model structure.
Action: file_tools.read_file(path=models/user.py)
Observation: <file contents>
Thought: I can now generate a compatible update.
```

This keeps agents grounded in real workspace state and improves output quality.
