from collections import deque
from dataclasses import dataclass, field
from typing import Deque

try:
    import tiktoken
except ImportError:  # pragma: no cover - fallback for environments not yet installed
    tiktoken = None

@dataclass
class RunMemory:
    max_history: int = 10

    # Bounded buffers automatically evict the oldest entries when full.
    planner_outputs: Deque[str] = field(default_factory=lambda: deque(maxlen=10))
    coding_outputs: Deque[str] = field(default_factory=lambda: deque(maxlen=10))
    review_outputs: Deque[str] = field(default_factory=lambda: deque(maxlen=10))
    reflection_outputs: Deque[str] = field(default_factory=lambda: deque(maxlen=10))
    evaluation_outputs: Deque[str] = field(default_factory=lambda: deque(maxlen=10))

    def __post_init__(self) -> None:
        """Ensure all memory buffers use the configured max_history value.

        The default factories provide a sensible default for normal construction,
        while this hook keeps custom max_history values and any list-like inputs
        bounded consistently.
        """
        for attr in self._memory_buffer_names():
            items = getattr(self, attr)
            if not isinstance(items, deque) or items.maxlen != self.max_history:
                setattr(self, attr, deque(items, maxlen=self.max_history))

    @staticmethod
    def _memory_buffer_names() -> tuple[str, ...]:
        """Return all output buffer attribute names."""
        return (
            "planner_outputs",
            "coding_outputs",
            "review_outputs",
            "reflection_outputs",
            "evaluation_outputs",
        )

    def _last_or_empty(self, items: Deque[str]) -> str:
        """Return the last item or empty string."""
        return items[-1] if items else ""

    def _get_recent(self, items: Deque[str], count: int) -> list[str]:
        """Get the last N items as a list."""
        return list(items)[-count:] if items else []

    def build_context_snapshot(self, history_count: int = 3) -> str:
        """Build a bounded context snapshot including recent history.

        Args:
            history_count: Number of recent items to include per agent.
        """
        plans = self._get_recent(self.planner_outputs, history_count)
        codes = self._get_recent(self.coding_outputs, history_count)
        reviews = self._get_recent(self.review_outputs, history_count)
        reflections = self._get_recent(self.reflection_outputs, history_count)

        def format_history(items: list[str], label: str) -> str:
            if not items:
                return f"- {label}: (none)"
            lines = [f"  [{i + 1}] {item}" for i, item in enumerate(items)]
            return f"- {label}:\n" + "\n".join(lines)

        return (
            "MEMORY_CONTEXT:\n"
            f"{format_history(plans, 'RecentPlans')}\n"
            f"{format_history(codes, 'RecentCodingOutputs')}\n"
            f"{format_history(reviews, 'RecentReviews')}\n"
            f"{format_history(reflections, 'RecentReflections')}"
        )

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count for a text string.

        Uses tiktoken with cl100k_base encoding. Falls back to a rough
        character-based estimate if tokenizer loading fails.
        """
        try:
            if tiktoken is None:
                raise ImportError("tiktoken is not installed")
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception:
            return len(text) // 4

    def get_total_memory_tokens(self) -> int:
        """Estimate total tokens across all memory output buffers."""
        return sum(
            self.estimate_tokens(item)
            for attr in self._memory_buffer_names()
            for item in getattr(self, attr)
        )

    def get_token_breakdown(self) -> dict[str, int]:
        """Get token count breakdown per memory output buffer."""
        return {
            attr: sum(self.estimate_tokens(item) for item in getattr(self, attr))
            for attr in self._memory_buffer_names()
        }
