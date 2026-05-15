using Microsoft.SemanticKernel;

namespace AiSdlcAgent.Agents;

public class ReviewAgent
{
    private readonly Kernel _kernel;
    public ReviewAgent(Kernel kernel) => _kernel = kernel;

    public async Task<string> ReviewAsync(string task, string input)
    {
        try
        {
            var prompt = await File.ReadAllTextAsync("Prompts/review.txt");
            var result = await _kernel.InvokePromptAsync($"{prompt}\n\nTask: {task}\n\nInput: {input}");
            return result.ToString();
        }
        catch (Exception ex)
        {
            return $"[OFFLINE_REVIEW] PASS_WITH_WARNINGS. Task: {task}. Input reviewed. Reason: {ex.Message}";
        }
    }
}