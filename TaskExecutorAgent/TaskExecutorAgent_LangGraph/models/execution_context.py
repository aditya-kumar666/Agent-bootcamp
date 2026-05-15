from dataclasses import dataclass, field
from typing import List


@dataclass
class ExecutionContext:
    """Tracks the execution state and history throughout the agent pipeline.
    
    Attributes:
        steps: List of execution steps taken
        tool_logs: Logs from tool invocations
        changed_files: List of files modified during execution
        retry_count: Number of retries attempted
    """
    steps: List[str] = field(default_factory=list)
    tool_logs: List[str] = field(default_factory=list)
    changed_files: List[str] = field(default_factory=list)
    retry_count: int = 0

    def add_step(self, step: str) -> None:
        """Add a step to the execution history.
        
        Args:
            step: Description of the step taken
        """
        self.steps.append(step)

    def add_tool_log(self, log: str) -> None:
        """Add a tool execution log.
        
        Args:
            log: Tool execution output
        """
        self.tool_logs.append(log)

    def add_changed_file(self, file_path: str) -> None:
        """Record a file that was changed.
        
        Args:
            file_path: Path to the changed file
        """
        if file_path not in self.changed_files:
            self.changed_files.append(file_path)

    def increment_retry(self) -> None:
        """Increment the retry counter."""
        self.retry_count += 1

    def get_summary(self) -> str:
        """Get a summary of the execution context.
        
        Returns:
            Formatted summary string
        """
        return (
            f"Execution Summary:\n"
            f"- Steps: {len(self.steps)}\n"
            f"- Tool logs: {len(self.tool_logs)}\n"
            f"- Changed files: {len(self.changed_files)}\n"
            f"- Retries: {self.retry_count}"
        )
