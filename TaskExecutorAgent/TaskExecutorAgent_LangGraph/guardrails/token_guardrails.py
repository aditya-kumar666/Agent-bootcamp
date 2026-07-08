import os

from memory.run_memory import RunMemory


DEFAULT_MEMORY_SNAPSHOT_TOKEN_BUDGET = 120
DEFAULT_HISTORY_COUNTS = (5, 3, 2, 1, 0)
GUARDRAIL_LOG_PREFIX = "[TOKEN_GUARDRAIL]"
TOKEN_BUDGET_ENV_VAR = "MEMORY_SNAPSHOT_TOKEN_BUDGET"


def _is_guardrail_logging_enabled() -> bool:
    """Return whether token guardrail decisions should be printed."""
    return os.getenv("TOKEN_GUARDRAIL_LOGS", "true").lower() == "true"


def _log_guardrail_decision(message: str) -> None:
    """Print a visible token guardrail decision line."""
    if _is_guardrail_logging_enabled():
        print(f"{GUARDRAIL_LOG_PREFIX} {message}", flush=True)


def _get_memory_snapshot_token_budget(default_budget: int) -> int:
    """Get memory snapshot token budget from env var or default."""
    raw_budget = os.getenv(TOKEN_BUDGET_ENV_VAR)
    if not raw_budget:
        return default_budget

    try:
        budget = int(raw_budget)
    except ValueError:
        _log_guardrail_decision(
            f"invalid {TOKEN_BUDGET_ENV_VAR}={raw_budget!r}; using default={default_budget}"
        )
        return default_budget

    if budget <= 0:
        _log_guardrail_decision(
            f"invalid {TOKEN_BUDGET_ENV_VAR}={budget}; using default={default_budget}"
        )
        return default_budget

    return budget


def build_context_snapshot_with_budget(
    memory: RunMemory,
    max_tokens: int = DEFAULT_MEMORY_SNAPSHOT_TOKEN_BUDGET,
    history_counts: tuple[int, ...] = DEFAULT_HISTORY_COUNTS,
) -> str:
    """Build the largest memory snapshot that fits within a token budget.

    The function starts with richer history and progressively reduces the
    included history until the snapshot is small enough for the next prompt.
    If even an empty-history snapshot is too large, it returns a compact
    omission notice.

    Args:
        memory: Run memory containing bounded agent output buffers.
        max_tokens: Maximum allowed estimated tokens for the snapshot.
        history_counts: History sizes to try, in descending preference order.

    Returns:
        A memory context snapshot that fits the requested token budget.
    """
    max_tokens = _get_memory_snapshot_token_budget(max_tokens)
    attempted: list[str] = []
    for history_count in history_counts:
        snapshot = memory.build_context_snapshot(history_count=history_count)
        token_count = RunMemory.estimate_tokens(snapshot)
        attempted.append(f"history={history_count}:tokens={token_count}")
        if token_count <= max_tokens:
            if history_count == history_counts[0]:
                decision = "full snapshot accepted"
            else:
                decision = "snapshot reduced"
            _log_guardrail_decision(
                f"{decision}; selected_history={history_count}; "
                f"snapshot_tokens={token_count}; budget={max_tokens}; "
                f"attempts={', '.join(attempted)}"
            )
            return snapshot

    _log_guardrail_decision(
        f"snapshot omitted; budget={max_tokens}; attempts={', '.join(attempted)}"
    )
    return (
        "MEMORY_CONTEXT:\n"
        f"- Recent history omitted because it exceeded the token budget "
        f"of {max_tokens} tokens."
    )