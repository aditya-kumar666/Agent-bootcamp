"""Evaluation module for assessing task completion."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class TaskStatus(str, Enum):
    """Task completion status."""
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"


class EvaluationResult(BaseModel):
    """Result of task evaluation.
    
    Attributes:
        status: Task completion status (PASS/FAIL/PARTIAL)
        acceptance_criteria_met: Whether acceptance criteria are met
        tests_passed: Whether tests passed
        open_issues: List of unresolved issues
        risk_level: Risk assessment (low/medium/high)
        summary: Final summary text
    """
    status: TaskStatus
    acceptance_criteria_met: bool
    tests_passed: bool
    open_issues: list[str]
    risk_level: str  # low, medium, high
    summary: str

    def to_formatted_string(self) -> str:
        """Format evaluation result as readable string.
        
        Returns:
            Formatted evaluation output
        """
        return (
            f"Status: {self.status}\n"
            f"AcceptanceCriteria: {'Met' if self.acceptance_criteria_met else 'Not Met'}\n"
            f"Tests: {'Passed' if self.tests_passed else 'Failed'}\n"
            f"OpenIssues: {', '.join(self.open_issues) if self.open_issues else 'None'}\n"
            f"Risk: {self.risk_level}\n"
            f"FinalSummary: {self.summary}"
        )


class EvaluationRules:
    """Rules engine for task evaluation."""

    @staticmethod
    def extract_status_from_review(review_text: str) -> bool:
        """Extract pass/fail status from review text.
        
        Args:
            review_text: Review output text
            
        Returns:
            True if PASS detected, False if FAIL detected
        """
        review_upper = review_text.upper()
        if "FAIL" in review_upper:
            return False
        return True

    @staticmethod
    def extract_issues_from_review(review_text: str) -> list[str]:
        """Extract issues from review text.
        
        Args:
            review_text: Review output text
            
        Returns:
            List of identified issues
        """
        issues = []
        lines = review_text.split("\n")
        for line in lines:
            if "issue" in line.lower() or "error" in line.lower() or "warning" in line.lower():
                line_stripped = line.strip()
                if line_stripped:
                    issues.append(line_stripped)
        return issues

    @staticmethod
    def assess_risk(review_passed: bool, issues_count: int, retry_count: int) -> str:
        """Assess risk level based on evaluation factors.
        
        Args:
            review_passed: Whether review passed
            issues_count: Number of issues found
            retry_count: Number of retries attempted
            
        Returns:
            Risk level: low, medium, or high
        """
        if not review_passed or retry_count > 2:
            return "high"
        elif issues_count > 3 or retry_count > 0:
            return "medium"
        return "low"
