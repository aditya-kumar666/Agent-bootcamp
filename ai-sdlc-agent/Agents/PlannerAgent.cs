using Microsoft.SemanticKernel;

namespace AiSdlcAgent.Agents;

public class PlannerAgent
{
    private readonly Kernel _kernel;
    public PlannerAgent(Kernel kernel) => _kernel = kernel;

    public async Task<string> PlanAsync(string task)
    {
        try
        {
            var prompt = await File.ReadAllTextAsync("Prompts/planner.txt");
            var result = await _kernel.InvokePromptAsync($"{prompt}\n\nTask: {task}");
            return result.ToString();
        }
        catch (Exception ex)
        {
            return $"[OFFLINE_PLAN] 1) Analyze task 2) Propose changes 3) Validate output. Reason: {ex.Message}";
        }
    }
}