using Microsoft.SemanticKernel;

namespace AiSdlcAgent.Agents;

public class CodingAgent
{
    private readonly Kernel _kernel;
    public CodingAgent(Kernel kernel) => _kernel = kernel;

    public async Task<string> ExecuteAsync(string task, string input)
    {
        try
        {
            var prompt = await File.ReadAllTextAsync("Prompts/coding.txt");
            var result = await _kernel.InvokePromptAsync($"{prompt}\n\nTask: {task}\n\nInput: {input}");
            return result.ToString();
        }
        catch (Exception ex)
        {
            return $"[OFFLINE_CODE] Generated fallback implementation plan for task '{task}'. Input summary: {input}. Reason: {ex.Message}";
        }
    }
}