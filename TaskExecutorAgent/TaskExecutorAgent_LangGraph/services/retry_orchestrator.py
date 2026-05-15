"""Retry orchestration for agent workflow."""

import os
from typing import Callable, Any


class RetryOrchestrator:
    """Orchestrates retry logic for agent workflow."""

    def __init__(self, max_retries: int = 2):
        """Initialize retry orchestrator.
        
        Args:
            max_retries: Maximum number of retries allowed
        """
        self.max_retries = max_retries

    def should_retry(self, review_text: str, retry_count: int) -> bool:
        """Determine if retry should be attempted.
        
        Args:
            review_text: Review feedback text
            retry_count: Current retry count
            
        Returns:
            True if retry should be attempted, False otherwise
        """
        if retry_count >= self.max_retries:
            return False
        
        enable_reflection = os.getenv("ENABLE_REFLECTION", "true").lower() == "true"
        if not enable_reflection:
            return False
        
        # Retry if FAIL is detected in review
        return "FAIL" in review_text.upper()

    async def execute_with_retry(
        self,
        task_func: Callable,
        task_args: list[Any],
        review_func: Callable,
        review_args_builder: Callable,
        reflection_func: Callable,
        reflection_args_builder: Callable,
        max_attempts: int = 3
    ) -> tuple[str, str, int]:
        """Execute a task with retry logic.
        
        Args:
            task_func: Function to execute (e.g., coding agent)
            task_args: Arguments for task function
            review_func: Function to review output
            review_args_builder: Function to build review arguments from task output
            reflection_func: Function for reflection
            reflection_args_builder: Function to build reflection arguments
            max_attempts: Maximum attempts (task + retries)
            
        Returns:
            Tuple of (task_output, review_output, retry_count)
        """
        retry_count = 0
        task_output = None
        review_output = None
        
        for attempt in range(max_attempts):
            # Execute task
            task_output = await task_func(*task_args)
            
            # Review output
            review_args = review_args_builder(task_output)
            review_output = await review_func(*review_args)
            
            # Check if we need to retry
            if not self.should_retry(review_output, retry_count):
                break
            
            # Reflection and retry
            reflection_args = reflection_args_builder(task_output, review_output)
            reflection_output = await reflection_func(*reflection_args)
            
            # Update task args with reflection for next iteration
            task_args = [a if i != 1 else reflection_output for i, a in enumerate(task_args)]
            retry_count += 1
        
        return task_output, review_output, retry_count

    def get_config(self) -> dict:
        """Get current retry configuration.
        
        Returns:
            Configuration dictionary
        """
        return {
            "max_retries": self.max_retries,
            "enable_reflection": os.getenv("ENABLE_REFLECTION", "true"),
            "max_retries_env": int(os.getenv("MAX_RETRIES", "2")),
        }
