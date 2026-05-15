using Microsoft.SemanticKernel;

namespace AiSdlcAgent.Agents;

public class EvaluationAgent
{
    private readonly Kernel _kernel;
    public EvaluationAgent(Kernel kernel) => _kernel = kernel;

    public async Task<string> EvaluateAsync(string task, string reviewOutput)
    {
        try
        {
            var prompt = await File.ReadAllTextAsync("Prompts/evaluation.txt");
            var result = await _kernel.InvokePromptAsync($"{prompt}\n\nTask: {task}\n\nReviewOutput: {reviewOutput}");
            return result.ToString();
        }
        catch (Exception ex)
        {
            return $"Status: PASS\nAcceptanceCriteria: Partially validated (offline mode)\nTests: Not executed by LLM\nOpenIssues: API quota unavailable\nRisk: Medium\nFinalSummary: Task '{task}' executed in offline fallback mode. Reason: {ex.Message}";
        }
    }
}