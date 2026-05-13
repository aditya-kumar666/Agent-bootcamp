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