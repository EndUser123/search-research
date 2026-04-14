"""Shared evidence-scope loading for Stop-time validators.

This module centralizes evidence retrieval policy so validators can ask for:
- turn_strict: only current-turn evidence
- session_fresh: recent session+terminal evidence
- session_fresh_mutation_safe: recent evidence excluding invalidated artifacts

It prevents each validator from inventing its own stale/turn/session semantics.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from evidence_store import (
    is_file_invalidated,
    load_tool_events,
    load_tool_events_for_context,
    normalize_session_id,
)

SCOPE_TURN_STRICT = "turn_strict"
SCOPE_SESSION_FRESH = "session_fresh"
SCOPE_SESSION_FRESH_MUTATION_SAFE = "session_fresh_mutation_safe"

VALID_SCOPES = {
    SCOPE_TURN_STRICT,
    SCOPE_SESSION_FRESH,
    SCOPE_SESSION_FRESH_MUTATION_SAFE,
}

ARTIFACT_TOOLS = {"Read", "Grep", "Glob"}
DEFAULT_LIMIT = 500
DEFAULT_FRESH_TTL_SECONDS = 7200


def _dedupe_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate events while preserving order."""
    seen: set[tuple[str, str, str, str]] = set()
    merged: list[dict[str, Any]] = []
    for evt in events:
        key = (
            str(evt.get("id", "")),
            str(evt.get("name", "")),
            str(evt.get("command", "")),
            str(evt.get("terminal_id", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(evt)
    return merged


def _extract_artifact_path(command: str) -> str | None:
    """Extract a path-like token from a tool command."""
    if not command:
        return None

    tokens = command.strip().split()
    candidates = tokens[1:] if len(tokens) > 1 else tokens
    for token in candidates:
        token = token.rstrip(",")
        if token in ("-r", "-i", "-n", "-E", "-F", "-l", "-h", "--", "-w", "skill"):
            continue
        if "/" in token or token.startswith(("P:", "p:", "C:", "c:", "~")):
            return token
        if re.match(r"[\w\-./]+\.(?:py|md|json|yml|yaml|txt|SKILL)$", token, re.IGNORECASE):
            return token
    return None


def _is_event_fresh_for_mutable_artifact(event: dict[str, Any]) -> bool:
    """Return False when event points at an artifact currently marked invalidated."""
    if str(event.get("name", "")) not in ARTIFACT_TOOLS:
        return True

    path = _extract_artifact_path(str(event.get("command", "") or ""))
    if not path:
        return True

    normalized = os.path.realpath(path)
    return not is_file_invalidated(normalized)


def load_scoped_tool_events(
    *,
    session_id: str,
    terminal_id: str = "",
    scope: str,
    limit: int = DEFAULT_LIMIT,
    ttl_seconds: int | None = None,
    current_turn_events: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Load tool events according to a validator's evidence scope.

    Args:
        session_id: Claude session id.
        terminal_id: Terminal/worktree id.
        scope: One of VALID_SCOPES.
        limit: Maximum persisted events to load.
        ttl_seconds: Optional freshness TTL. Defaults apply for session scopes.
        current_turn_events: Optional transient events from the current hook payload.

    Returns:
        Chronological list of deduplicated tool events.
    """
    normalized_session = normalize_session_id(session_id)
    if not normalized_session:
        return current_turn_events or []

    if scope not in VALID_SCOPES:
        raise ValueError(f"Unsupported evidence scope: {scope}")

    base_events: list[dict[str, Any]] = []
    if scope == SCOPE_TURN_STRICT:
        if terminal_id:
            base_events = load_tool_events_for_context(
                normalized_session,
                terminal_id,
                limit=limit,
                within_seconds=ttl_seconds,
                use_turn_scoping=True,
            )
    else:
        if ttl_seconds is None:
            ttl_seconds = DEFAULT_FRESH_TTL_SECONDS

        if terminal_id:
            base_events = load_tool_events_for_context(
                normalized_session,
                terminal_id,
                limit=limit,
                within_seconds=ttl_seconds,
                use_turn_scoping=False,
            )
        else:
            base_events = load_tool_events(
                normalized_session,
                limit=limit,
                within_seconds=ttl_seconds,
            )

        if scope == SCOPE_SESSION_FRESH_MUTATION_SAFE:
            base_events = [evt for evt in base_events if _is_event_fresh_for_mutable_artifact(evt)]

    merged = _dedupe_events([*(current_turn_events or []), *base_events])
    return merged
