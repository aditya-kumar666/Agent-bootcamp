namespace AiSdlcAgent.Memory;

public class RunMemory
{
    public List<string> PlannerOutputs { get; } = new();
    public List<string> CodingOutputs { get; } = new();
    public List<string> ReviewOutputs { get; } = new();
    public List<string> ReflectionOutputs { get; } = new();
    public List<string> EvaluationOutputs { get; } = new();
}