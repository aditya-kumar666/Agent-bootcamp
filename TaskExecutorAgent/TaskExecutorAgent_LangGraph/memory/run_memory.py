from dataclasses import dataclass, field
from typing import List

@dataclass
class RunMemory:
    planner_outputs: List[str] = field(default_factory=list)
    coding_outputs: List[str] = field(default_factory=list)
    review_outputs: List[str] = field(default_factory=list)
    reflection_outputs: List[str] = field(default_factory=list)
    evaluation_outputs: List[str] = field(default_factory=list)

    def _last_or_empty(self, items: List[str]) -> str:
        """Return the last item or empty string."""
        return items[-1] if items else ""

    def build_context_snapshot(self) -> str:
        """Build context snapshot matching C# version's format."""
        planner = self._last_or_empty(self.planner_outputs)
        coding = self._last_or_empty(self.coding_outputs)
        review = self._last_or_empty(self.review_outputs)
        reflection = self._last_or_empty(self.reflection_outputs)

        return (
            "MEMORY_CONTEXT:\n"
            f"- LatestPlan: {planner}\n"
            f"- LatestCodingOutput: {coding}\n"
            f"- LatestReviewOutput: {review}\n"
            f"- LatestReflectionOutput: {reflection}"
        )
