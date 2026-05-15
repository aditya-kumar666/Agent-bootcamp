namespace AiSdlcAgent.Models;

public record AgentResult(bool Success, string Output, string? Error = null);