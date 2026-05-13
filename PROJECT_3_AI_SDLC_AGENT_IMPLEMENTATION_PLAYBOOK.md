# PHASE 2C — Build AI SDLC Agent (Implementation Playbook)

Estimated Time: **4–5 days**

Goal: Build a real AI SDLC orchestration system similar to Cursor / Claude Code / Devin / Copilot Workspace.

You will build pipeline:

**Task → Planner Agent → Coding Agent → Review Agent → Reflection Agent → Evaluation Layer → Final Result**

---

## What this project teaches

- AI agents
- Orchestration
- Tool calling
- Reflection loops
- Memory
- Structured outputs
- Autonomous workflows
- AI SDLC systems

---

## Final Architecture

```text
User Task
   ↓
Planner Agent
   ↓
Tool Selection
   ↓
Coding Agent
   ↓
Review Agent
   ↓
Reflection Agent
   ↓
Evaluation Layer
   ↓
Final Response
```

---

## Step 1 — Create Project

Open terminal in `D:\Agent` and run:

```bash
mkdir ai-sdlc-agent
cd ai-sdlc-agent
dotnet new console
```

---

## Step 2 — Install Packages

Run:

```bash
dotnet add package Microsoft.SemanticKernel
dotnet add package Microsoft.SemanticKernel.Connectors.OpenAI
dotnet add package Microsoft.Extensions.Hosting
dotnet add package Microsoft.Extensions.DependencyInjection
dotnet add package Microsoft.Extensions.Configuration
dotnet add package Microsoft.Extensions.Configuration.Json
dotnet add package Serilog
dotnet add package Serilog.Sinks.Console
```

---

## Step 3 — Create Folder Structure

Create these folders:

```text
ai-sdlc-agent/
  Agents/
  Prompts/
  Plugins/
  Models/
  Services/
  Memory/
  Evaluation/
  Program.cs
  appsettings.json
```

---

## Step 4 — Add Configuration

Create `appsettings.json`:

```json
{
  "OpenAI": {
    "Model": "gpt-4o-mini",
    "ApiKey": "YOUR_API_KEY_HERE"
  },
  "Agent": {
    "MaxRetries": 2,
    "EnableReflection": true,
    "EnableMemory": true
  }
}
```

> Better: keep secrets in environment variable and inject at runtime.

---

## Step 5 — Create Core Models

### `Models/UserTask.cs`

```csharp
namespace AiSdlcAgent.Models;

public record UserTask(string Title, string Description, string AcceptanceCriteria);
```

### `Models/AgentResult.cs`

```csharp
namespace AiSdlcAgent.Models;

public record AgentResult(bool Success, string Output, string? Error = null);
```

### `Models/ExecutionContext.cs`

```csharp
namespace AiSdlcAgent.Models;

public class ExecutionContext
{
    public List<string> Steps { get; } = new();
    public List<string> ToolLogs { get; } = new();
    public List<string> ChangedFiles { get; } = new();
    public int RetryCount { get; set; }
}
```

---

## Step 6 — Create Prompt Files

Create these prompt files under `Prompts/`:

1. `planner.txt`
2. `coding.txt`
3. `review.txt`
4. `reflection.txt`
5. `evaluation.txt`

### `Prompts/planner.txt`

```text
You are a Planner Agent. Break the task into numbered implementation steps.
Output strict JSON array with fields: stepNumber, goal, expectedOutput.
```

### `Prompts/coding.txt`

```text
You are a Coding Agent. Implement the requested step with minimal, safe edits.
Return: changed files + patch summary + rationale.
```

### `Prompts/review.txt`

```text
You are a Review Agent. Review for correctness, edge cases, style, and architecture.
Return actionable issues only.
```

### `Prompts/reflection.txt`

```text
Previous attempt failed. Diagnose root cause and suggest corrected next action.
```

### `Prompts/evaluation.txt`

```text
Evaluate output against acceptance criteria. Return pass/fail and reasons.
```

---

## Step 7 — Build Tool Plugins

### `Plugins/FileToolsPlugin.cs`

```csharp
using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace AiSdlcAgent.Plugins;

public class FileToolsPlugin
{
    [KernelFunction, Description("Read file content")]
    public string ReadFile(string path)
    {
        return File.Exists(path) ? File.ReadAllText(path) : "FILE_NOT_FOUND";
    }

    [KernelFunction, Description("Write file content")]
    public string WriteFile(string path, string content)
    {
        var fullPath = Path.GetFullPath(path);
        var root = Path.GetFullPath(Directory.GetCurrentDirectory());
        if (!fullPath.StartsWith(root, StringComparison.OrdinalIgnoreCase))
            return "DENIED_OUTSIDE_WORKSPACE";

        File.WriteAllText(fullPath, content);
        return "WRITE_OK";
    }

    [KernelFunction, Description("Search files by pattern")]
    public string Search(string pattern)
    {
        var files = Directory.GetFiles(Directory.GetCurrentDirectory(), "*", SearchOption.AllDirectories)
            .Where(f => f.Contains(pattern, StringComparison.OrdinalIgnoreCase))
            .Take(20);
        return string.Join("\n", files);
    }
}
```

### `Plugins/TestToolsPlugin.cs`

```csharp
using System.ComponentModel;
using System.Diagnostics;
using Microsoft.SemanticKernel;

namespace AiSdlcAgent.Plugins;

public class TestToolsPlugin
{
    [KernelFunction, Description("Run dotnet tests")]
    public string RunTests()
    {
        var psi = new ProcessStartInfo
        {
            FileName = "dotnet",
            Arguments = "test --nologo",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        using var process = Process.Start(psi)!;
        var output = process.StandardOutput.ReadToEnd();
        var error = process.StandardError.ReadToEnd();
        process.WaitForExit();
        return output + "\n" + error;
    }
}
```

---

## Step 8 — Create Agent Classes

Create these files in `Agents/`:

1. `PlannerAgent.cs`
2. `CodingAgent.cs`
3. `ReviewAgent.cs`
4. `ReflectionAgent.cs`
5. `EvaluationAgent.cs`

Each agent should:
- load its prompt file
- call Semantic Kernel
- return structured text/JSON response

### Example skeleton (`Agents/PlannerAgent.cs`)

```csharp
using Microsoft.SemanticKernel;

namespace AiSdlcAgent.Agents;

public class PlannerAgent
{
    private readonly Kernel _kernel;
    public PlannerAgent(Kernel kernel) => _kernel = kernel;

    public async Task<string> PlanAsync(string task)
    {
        var prompt = await File.ReadAllTextAsync("Prompts/planner.txt");
        var result = await _kernel.InvokePromptAsync($"{prompt}\n\nTask: {task}");
        return result.ToString();
    }
}
```

Follow same pattern for Coding/Review/Reflection/Evaluation agents.

---

## Step 9 — Add Memory Store

Create `Memory/RunMemory.cs`:

```csharp
namespace AiSdlcAgent.Memory;

public class RunMemory
{
    public List<string> PlannerOutputs { get; } = new();
    public List<string> CodingOutputs { get; } = new();
    public List<string> ReviewOutputs { get; } = new();
    public List<string> ReflectionOutputs { get; } = new();
    public List<string> EvaluationOutputs { get; } = new();
}
```

Use it to persist intermediate state across retries.

---

## Step 10 — Add Reflection + Retry Handler

Create `Services/RetryOrchestrator.cs`:

- if review or tests fail:
  - call ReflectionAgent
  - apply correction
  - rerun CodingAgent + ReviewAgent
- stop when success OR `MaxRetries` reached

Pseudo-flow:

```text
for each planned step:
  run coding
  run review
  if fail:
    reflect
    retry coding/review
```

---

## Step 11 — Build Main Orchestration Flow

In `Program.cs`, wire:

1. Host + configuration
2. Semantic Kernel with OpenAI connector
3. Import plugins (FileTools, TestTools)
4. Create all agents
5. Run full pipeline in order

### Program.cs flow (required)

```text
Read user task
  -> PlannerAgent
  -> CodingAgent (tool calls)
  -> ReviewAgent
  -> ReflectionAgent (if needed)
  -> EvaluationAgent
  -> Final formatted response
```

---

## Step 12 — Program.cs Reference Wiring

Use this as template:

```csharp
using AiSdlcAgent.Agents;
using AiSdlcAgent.Memory;
using AiSdlcAgent.Plugins;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;

var config = new ConfigurationBuilder()
    .AddJsonFile("appsettings.json", optional: false)
    .AddEnvironmentVariables()
    .Build();

var model = config["OpenAI:Model"]!;
var apiKey = Environment.GetEnvironmentVariable("OPENAI_API_KEY") ?? config["OpenAI:ApiKey"]!;

var builder = Kernel.CreateBuilder();
builder.AddOpenAIChatCompletion(model, apiKey);
var kernel = builder.Build();

kernel.ImportPluginFromObject(new FileToolsPlugin(), "FileTools");
kernel.ImportPluginFromObject(new TestToolsPlugin(), "TestTools");

var planner = new PlannerAgent(kernel);
var coding = new CodingAgent(kernel);
var review = new ReviewAgent(kernel);
var reflection = new ReflectionAgent(kernel);
var evaluation = new EvaluationAgent(kernel);
var memory = new RunMemory();

var task = "Add validation in registration flow and ensure tests pass.";

var plan = await planner.PlanAsync(task);
memory.PlannerOutputs.Add(plan);

var codeOut = await coding.ExecuteAsync(task, plan);
memory.CodingOutputs.Add(codeOut);

var reviewOut = await review.ReviewAsync(task, codeOut);
memory.ReviewOutputs.Add(reviewOut);

if (reviewOut.Contains("FAIL", StringComparison.OrdinalIgnoreCase))
{
    var reflectionOut = await reflection.ReflectAsync(task, codeOut, reviewOut);
    memory.ReflectionOutputs.Add(reflectionOut);
    codeOut = await coding.ExecuteAsync(task, reflectionOut);
    reviewOut = await review.ReviewAsync(task, codeOut);
}

var evalOut = await evaluation.EvaluateAsync(task, reviewOut);
memory.EvaluationOutputs.Add(evalOut);

Console.WriteLine("=== FINAL RESPONSE ===");
Console.WriteLine(evalOut);
```

---

## Step 13 — Add Evaluation Layer Rules

EvaluationAgent must explicitly check:
- acceptance criteria met/not met
- tests passed/failed
- unresolved review findings
- risk level (low/medium/high)

Output format:

```text
Status: PASS|FAIL
AcceptanceCriteria: ...
Tests: ...
OpenIssues: ...
Risk: ...
FinalSummary: ...
```

---

## Step 14 — Add Autonomous Workflow Behavior

To make it “agentic”, enforce:

1. Agents decide next action from previous output.
2. Tools are called only when required by step context.
3. Reflection modifies strategy, not just repeats prompt.
4. Memory influences future decisions.

---

## Step 15 — Add Production Concepts

Implement these improvements:

- structured JSON outputs from every agent
- token/time logging per step
- bounded retries and timeout per call
- safety guardrails for file operations
- deterministic mode for tests

---

## Step 16 — Run and Validate

Run:

```bash
dotnet build
dotnet run
```

Validate:
- planner returns ordered steps
- coding uses tools
- review flags issues
- reflection retries once/twice
- evaluation prints final PASS/FAIL summary

---

## Step 17 — Definition of Done

Project is complete when:

- [ ] Full pipeline runs end-to-end
- [ ] Reflection retry path works
- [ ] File tool safety checks enforced
- [ ] Evaluation layer produces structured verdict
- [ ] Final response includes implementation + quality status

---

## Step 18 — Next Extension (Optional)

After baseline works, add:

- Git plugin (diff/commit generation)
- Test failure parser
- Multi-file planning graph
- SQLite memory for historical runs
- Web API wrapper around orchestrator

---

If you want, I can now generate the **actual source files** for this structure inside `D:\Agent\ai-sdlc-agent` so you can run it immediately.
