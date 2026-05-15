namespace AiSdlcAgent.Models;

public class ExecutionContext
{
    public List<string> Steps { get; } = new();
    public List<string> ToolLogs { get; } = new();
    public List<string> ChangedFiles { get; } = new();
    public int RetryCount { get; set; }
}