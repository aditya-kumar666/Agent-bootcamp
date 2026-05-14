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

var task = @"Implement a practical C# feature in this repo:
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
- Includes brief unit-test suggestions.";

var plan = await planner.PlanAsync(task);
memory.PlannerOutputs.Add(plan);
Console.WriteLine("\n=== PLANNER OUTPUT ===");
Console.WriteLine(plan);

var codeOut = await coding.ExecuteAsync(task, $"{plan}\n\n{memory.BuildContextSnapshot()}");
memory.CodingOutputs.Add(codeOut);
Console.WriteLine("\n=== CODING OUTPUT ===");
Console.WriteLine(codeOut);

var reviewOut = await review.ReviewAsync(task, $"{codeOut}\n\n{memory.BuildContextSnapshot()}");
memory.ReviewOutputs.Add(reviewOut);
Console.WriteLine("\n=== REVIEW OUTPUT ===");
Console.WriteLine(reviewOut);

if (reviewOut.Contains("FAIL", StringComparison.OrdinalIgnoreCase))
{
    var reflectionOut = await reflection.ReflectAsync(task, codeOut, $"{reviewOut}\n\n{memory.BuildContextSnapshot()}");
    memory.ReflectionOutputs.Add(reflectionOut);
    Console.WriteLine("\n=== REFLECTION OUTPUT ===");
    Console.WriteLine(reflectionOut);

    codeOut = await coding.ExecuteAsync(task, $"{reflectionOut}\n\n{memory.BuildContextSnapshot()}");
    memory.CodingOutputs.Add(codeOut);
    Console.WriteLine("\n=== CODING OUTPUT (AFTER REFLECTION) ===");
    Console.WriteLine(codeOut);

    reviewOut = await review.ReviewAsync(task, $"{codeOut}\n\n{memory.BuildContextSnapshot()}");
    memory.ReviewOutputs.Add(reviewOut);
    Console.WriteLine("\n=== REVIEW OUTPUT (AFTER REFLECTION) ===");
    Console.WriteLine(reviewOut);
}

var evalOut = await evaluation.EvaluateAsync(task, $"{reviewOut}\n\n{memory.BuildContextSnapshot()}");
memory.EvaluationOutputs.Add(evalOut);

Console.WriteLine("\n=== EVALUATION OUTPUT ===");
Console.WriteLine(evalOut);

Console.WriteLine("\n=== FINAL RESPONSE ===");
Console.WriteLine(evalOut);