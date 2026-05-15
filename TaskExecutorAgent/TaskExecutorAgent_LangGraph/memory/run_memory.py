from dataclasses import dataclass, field
from typing import List

@dataclass
class RunMemory:
    planner_outputs: List[str] = field(default_factory=list)
    coding_outputs: List[str] = field(default_factory=list)
    review_outputs: List[str] = field(default_factory=list)
    reflection_outputs: List[str] = field(default_factory=list)
    evaluation_outputs: List[str] = field(default_factory=list)

    def build_context_snapshot(self) -> str:
        return (
            f"Planner outputs: {len(self.planner_outputs)}\n"
            f"Coding outputs: {len(self.coding_outputs)}\n"
            f"Review outputs: {len(self.review_outputs)}\n"
            f"Reflection outputs: {len(self.reflection_outputs)}\n"
            f"Evaluation outputs: {len(self.evaluation_outputs)}"
        )
