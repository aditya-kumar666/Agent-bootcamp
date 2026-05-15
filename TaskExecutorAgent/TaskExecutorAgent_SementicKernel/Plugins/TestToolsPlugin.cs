using System.ComponentModel;
using System.Diagnostics;
using Microsoft.SemanticKernel;

namespace AiSdlcAgent.Plugins;

public class TestToolsPlugin
{
    [KernelFunction, Description("Run dotnet tests")]
    public string RunTests()
    {
        var psi = new ProcessStartInfo
        {
            FileName = "dotnet",
            Arguments = "test --nologo",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true
        };

        using var process = Process.Start(psi)!;
        var output = process.StandardOutput.ReadToEnd();
        var error = process.StandardError.ReadToEnd();
        process.WaitForExit();
        return output + "\n" + error;
    }
}