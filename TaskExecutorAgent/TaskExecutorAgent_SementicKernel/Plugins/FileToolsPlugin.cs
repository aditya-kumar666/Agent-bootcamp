using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace AiSdlcAgent.Plugins;

public class FileToolsPlugin
{
    [KernelFunction, Description("Read file content")]
    public string ReadFile(string path)
    {
        return File.Exists(path) ? File.ReadAllText(path) : "FILE_NOT_FOUND";
    }

    [KernelFunction, Description("Write file content")]
    public string WriteFile(string path, string content)
    {
        var fullPath = Path.GetFullPath(path);
        var root = Path.GetFullPath(Directory.GetCurrentDirectory());
        if (!fullPath.StartsWith(root, StringComparison.OrdinalIgnoreCase))
            return "DENIED_OUTSIDE_WORKSPACE";

        File.WriteAllText(fullPath, content);
        return "WRITE_OK";
    }

    [KernelFunction, Description("Search files by pattern")]
    public string Search(string pattern)
    {
        var files = Directory.GetFiles(Directory.GetCurrentDirectory(), "*", SearchOption.AllDirectories)
            .Where(f => f.Contains(pattern, StringComparison.OrdinalIgnoreCase))
            .Take(20);
        return string.Join("\n", files);
    }
}