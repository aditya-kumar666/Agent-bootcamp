using Microsoft.SemanticKernel;

namespace AiSdlcAgent.Agents;

public class ReflectionAgent
{
    private readonly Kernel _kernel;
    public ReflectionAgent(Kernel kernel) => _kernel = kernel;

    public async Task<string> ReflectAsync(string task, string codeOutput, string reviewOutput)
    {
        try
        {
            var prompt = await File.ReadAllTextAsync("Prompts/reflection.txt");
            var result = await _kernel.InvokePromptAsync($"{prompt}\n\nTask: {task}\n\nCodeOutput: {codeOutput}\n\nReviewOutput: {reviewOutput}");
            return result.ToString();
        }
        catch (Exception ex)
        {
            return $"[OFFLINE_REFLECTION] Retry with smaller scoped change and rerun review. Reason: {ex.Message}";
        }
    }
}