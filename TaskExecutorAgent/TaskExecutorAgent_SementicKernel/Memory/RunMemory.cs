namespace AiSdlcAgent.Memory;

public class RunMemory
{
    public List<string> PlannerOutputs { get; } = new();
    public List<string> CodingOutputs { get; } = new();
    public List<string> ReviewOutputs { get; } = new();
    public List<string> ReflectionOutputs { get; } = new();
    public List<string> EvaluationOutputs { get; } = new();

    public string BuildContextSnapshot()
    {
        static string LastOrEmpty(List<string> items) => items.Count == 0 ? "" : items[^1];

        var planner = LastOrEmpty(PlannerOutputs);
        var coding = LastOrEmpty(CodingOutputs);
        var review = LastOrEmpty(ReviewOutputs);
        var reflection = LastOrEmpty(ReflectionOutputs);

        return $@"MEMORY_CONTEXT:
- LatestPlan: {planner}
- LatestCodingOutput: {coding}
- LatestReviewOutput: {review}
- LatestReflectionOutput: {reflection}
";
    }
}