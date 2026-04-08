"""Helpers for turn-scoped evidence loading."""

from __future__ import annotations

from evidence_scope import SCOPE_TURN_STRICT, load_scoped_tool_events
def load_turn_scoped_events(
    *, session_id: str, terminal_id: str, limit: int
) -> list[dict[str, object]] | None:
    """Load current-turn evidence from the shared scope layer."""
    if not session_id:
        return None

    try:
        return load_scoped_tool_events(
            session_id=session_id,
            terminal_id=terminal_id,
            scope=SCOPE_TURN_STRICT,
            limit=limit,
        )
    except Exception:
        return None
