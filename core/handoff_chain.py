"""Handoff-chain session traversal.

Traverses session chains via handoff files (~/.claude/state/handoff/) instead of
sessions-index.json. This approach works for post-compaction sessions because
handoff files are written atomically at compaction time with the prior transcript
path baked in.

This is the PRIMARY chain traversal for sessions. The sessions-index-based
traversal in history_chain.py is a FALLBACK that fails for post-compaction sessions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any  # noqa: F401

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def _claude_base() -> Path:
    """Claude Code base directory (platform-specific)."""
    return Path.home() / ".claude"


def _handoff_dir() -> Path:
    """Directory containing handoff files."""
    return _claude_base() / "state" / "handoff"


def _projects_dir() -> Path:
    """Directory containing session transcript files."""
    return _claude_base() / "projects"


# ---------------------------------------------------------------------------
# Data models (compatible with history_chain.ChainWalkResult)
# ---------------------------------------------------------------------------


@dataclass
class HandoffChainEntry:
    """A single entry in the handoff chain."""

    session_id: str  # UUID from transcript filename
    transcript_path: Path
    parent_transcript_path: Path | None  # Next link in chain
    created: datetime | None


@dataclass
class HandoffChainResult:
    """Result of walking the handoff chain."""

    entries: list[HandoffChainEntry]
    depth: int
    origin_session_id: str | None  # First/oldest session in chain


# ---------------------------------------------------------------------------
# Core traversal
# ---------------------------------------------------------------------------


def _get_handoff_path(session_id: str) -> Path | None:
    """Get handoff file path for a session ID."""
    handoff_dir_path = _handoff_dir()
    if not handoff_dir_path.exists():
        return None

    # Try exact match first
    path = handoff_dir_path / f"console_{session_id}_handoff.json"
    if path.exists():
        return path

    # Try glob pattern as fallback
    for p in handoff_dir_path.glob(f"console_{session_id}_*handoff*.json"):
        return p
    return None


def _get_prior_transcript_path(handoff_path: Path) -> Path | None:
    """Extract prior session transcript path from handoff file.

    The handoff file contains resume_snapshot.transcript_path which points
    to the prior session's transcript JSONL.
    """
    try:
        with open(handoff_path, encoding="utf-8") as f:
            data = json.load(f)
        transcript_path_str = data.get("resume_snapshot", {}).get("transcript_path")
        if transcript_path_str:
            path = Path(transcript_path_str)
            if path.exists():
                return path
    except (OSError, json.JSONDecodeError, PermissionError):
        pass
    return None


def _find_handoff_referencing(transcript_path: Path) -> Path | None:
    """Find handoff file that has transcript_path as its source (prior session)."""
    handoff_dir_path = _handoff_dir()
    if not handoff_dir_path.exists():
        return None
    transcript_str = str(transcript_path)
    for handoff_file in handoff_dir_path.glob("console_*_handoff.json"):
        try:
            with open(handoff_file, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("resume_snapshot", {}).get("transcript_path") == transcript_str:
                return handoff_file
        except (OSError, json.JSONDecodeError, PermissionError):
            continue
    return None


def _resolve_current_transcript_path(session_id: str) -> Path | None:
    """Find the current session's transcript path from projects directory."""
    # The current session transcript is not yet registered in handoff,
    # so we find it by scanning the projects directory
    for jsonl_file in _projects_dir().rglob(f"{session_id}.jsonl"):
        if jsonl_file.exists():
            return jsonl_file
    return None


def walk_handoff_chain(
    session_id: str,
    terminal_id: str | None = None,
    max_depth: int = 20,
) -> HandoffChainResult:
    """Walk the session chain via handoff files.

    This traversal works for ALL sessions including post-compaction sessions,
    because handoff files are written atomically at compaction time.

    Args:
        session_id: Current session UUID
        terminal_id: Optional terminal ID for filtering (not currently used)
        max_depth: Maximum number of prior sessions to traverse

    Returns:
        HandoffChainResult with list of chain entries
    """
    entries: list[HandoffChainEntry] = []

    # Find starting point: current session's transcript
    current_transcript = _resolve_current_transcript_path(session_id)
    if not current_transcript:
        return HandoffChainResult(entries=[], depth=0, origin_session_id=None)

    # Find the handoff file that references this transcript
    # (the PRIOR session's handoff points to this transcript)
    handoff_path = _find_handoff_referencing(current_transcript)
    if not handoff_path:
        # No prior session - this IS the origin session
        entries.append(
            HandoffChainEntry(
                session_id=session_id,
                transcript_path=current_transcript,
                parent_transcript_path=None,
                created=None,
            )
        )
        return HandoffChainResult(entries=entries, depth=1, origin_session_id=session_id)

    visited: set[str] = set()
    chain_depth = 0
    origin_session_id: str | None = None

    while handoff_path and chain_depth < max_depth:
        prior_transcript = _get_prior_transcript_path(handoff_path)
        prior_session_id: str | None = None

        if prior_transcript and str(prior_transcript) not in visited:
            visited.add(str(prior_transcript))
            prior_session_id = prior_transcript.stem
        elif handoff_path:
            # Prior transcript missing (post-compaction) — extract session_id from
            # handoff filename as fallback: console_{session_id}_handoff.json
            prior_session_id = handoff_path.stem.replace("_handoff", "")
            prior_transcript = None

        # Check if this is the origin (no more prior handoffs)
        prior_handoff: Path | None = None
        if prior_transcript:
            try:
                prior_handoff = _find_handoff_referencing(prior_transcript)
            except (OSError, PermissionError, RuntimeError) as e:
                logger.warning("Failed to find handoff referencing %s: %s", prior_transcript, e)
                prior_handoff = None
        else:
            prior_handoff = None

        if not prior_handoff:
            origin_session_id = prior_session_id

        entries.append(
            HandoffChainEntry(
                session_id=prior_session_id or "unknown",
                transcript_path=prior_transcript or Path("."),
                parent_transcript_path=None,  # Set after we find next
                created=None,
            )
        )

        # Move to next in chain
        handoff_path = prior_handoff
        chain_depth += 1

    # Fill in parent_transcript_path links (reverse order)
    for i, entry in enumerate(entries):
        if i < len(entries) - 1:
            entry.parent_transcript_path = entries[i + 1].transcript_path

    # Reverse to oldest-first order
    entries.reverse()

    return HandoffChainResult(
        entries=entries,
        depth=chain_depth + 1,
        origin_session_id=origin_session_id or (entries[0].session_id if entries else None),
    )


def walk_handoff_chain_simple(
    session_id: str,
    terminal_id: str | None = None,
    max_depth: int = 20,
) -> HandoffChainResult:
    """Convenience wrapper for walk_handoff_chain.

    Use this as the PRIMARY chain walker. The sessions-index-based
    walk_chain_simple() is a fallback that fails for post-compaction sessions.
    """
    return walk_handoff_chain(
        session_id=session_id,
        terminal_id=terminal_id,
        max_depth=max_depth,
    )
