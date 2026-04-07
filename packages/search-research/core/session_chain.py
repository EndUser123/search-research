"""Session chain traversal for Claude Code.

Provides a unified interface for finding all session transcript files in a
session chain, given any session ID.

The ONLY strategy is handoff-file chaining:
  - PreCompact hook writes handoff files at /compact time
  - Each handoff file references the PRIOR session's transcript path
  - Follow the chain backward through handoff files

sessions-index.json and semantic similarity are NOT used — they are
Claude Code internal state that can go stale. Handoff files are the
authoritative session chain for post-compaction sessions.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime | None
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def _claude_base() -> Path:
    return Path.home() / ".claude"


def _projects_dir() -> Path:
    return _claude_base() / "projects"


def _handoff_dir() -> Path:
    return _claude_base() / "state" / "handoff"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SessionChainEntry:
    session_id: str
    transcript_path: Path
    parent_transcript_path: Path | None  # older → newer link
    created: None  # deprecated — kept for API compatibility
    first_user_message: str | None = None


@dataclass
class SessionChainResult:
    entries: list[SessionChainEntry] = field(default_factory=list)
    depth: int = 0
    origin_session_id: str | None = None


# ---------------------------------------------------------------------------
# Handoff-file chain
# ---------------------------------------------------------------------------


def _get_prior_transcript_path(handoff_path: Path) -> Path | None:
    """Extract prior session transcript path from a handoff file.

    Handles gracefully:
      - Missing handoff file
      - JSON decode errors
      - Missing/inaccessible transcript paths (archived or deleted files)
    """
    try:
        with open(handoff_path, encoding="utf-8") as f:
            data = json.load(f)
        path_str = data.get("resume_snapshot", {}).get("transcript_path")
        if path_str:
            p = Path(path_str)
            try:
                if p.exists():
                    return p
            except (OSError, PermissionError) as e:
                logger.warning("Transcript path inaccessible %s: %s", p, e)
    except (OSError, json.JSONDecodeError, PermissionError) as e:
        logger.warning("Failed to read handoff file %s: %s", handoff_path, e)
    return None


def _find_handoff_referencing(transcript_path: Path) -> Path | None:
    """Find handoff file whose resume_snapshot.transcript_path == transcript_path."""
    handoff_dir = _handoff_dir()
    if not handoff_dir.exists():
        return None
    target = str(transcript_path)
    for hf in handoff_dir.glob("console_*_handoff.json"):
        try:
            with open(hf, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("resume_snapshot", {}).get("transcript_path") == target:
                return hf
        except (OSError, json.JSONDecodeError, PermissionError):
            continue
    return None


def _resolve_transcript_path(session_id: str) -> Path | None:
    """Find the .jsonl path for a session ID by scanning projects directory."""
    for jsonl_file in _projects_dir().rglob(f"{session_id}.jsonl"):
        if jsonl_file.exists():
            return jsonl_file
    return None


def walk_handoff_chain(session_id: str, max_depth: int = 50) -> SessionChainResult:
    """Walk session chain via handoff files.

    Finds the handoff file that references the current session's transcript,
    then follows prior transcript paths through handoff files recursively.
    Returns entries in oldest-to-newest order.
    """
    current_transcript = _resolve_transcript_path(session_id)
    if not current_transcript:
        return SessionChainResult()

    handoff_path = _find_handoff_referencing(current_transcript)
    if not handoff_path:
        # No prior handoff found — this is the origin session
        return SessionChainResult(
            entries=[
                SessionChainEntry(
                    session_id=session_id,
                    transcript_path=current_transcript,
                    parent_transcript_path=None,
                    created=None,
                )
            ],
            depth=1,
            origin_session_id=session_id,
        )

    entries: list[SessionChainEntry] = []
    visited: set[str] = set()
    chain_depth = 0

    while handoff_path and chain_depth < max_depth:
        try:
            prior_transcript = _get_prior_transcript_path(handoff_path)
            if not prior_transcript or str(prior_transcript) in visited:
                break
            visited.add(str(prior_transcript))

            prior_session_id = prior_transcript.stem
            prior_handoff = _find_handoff_referencing(prior_transcript)

            entries.append(
                SessionChainEntry(
                    session_id=prior_session_id,
                    transcript_path=prior_transcript,
                    parent_transcript_path=None,
                    created=None,
                )
            )

            handoff_path = prior_handoff
        except (OSError, PermissionError, RuntimeError) as e:
            logger.warning("Failed to traverse chain at %s: %s", handoff_path, e)
            break
        chain_depth += 1

    entries.reverse()

    # Fill in parent links (entries are oldest→newest, so previous entry is the parent)
    for i, entry in enumerate(entries):
        if i > 0:
            entry.parent_transcript_path = entries[i - 1].transcript_path
    return SessionChainResult(
        entries=entries,
        depth=chain_depth + 1,
        origin_session_id=entries[0].session_id if entries else None,
    )


# ---------------------------------------------------------------------------
# Public API — delegates to handoff-only chain
# ---------------------------------------------------------------------------


def walk_session_chain(
    session_id: str,
    project_path: Path | None = None,
    max_depth: int = 50,
    newest_first: bool = False,
) -> SessionChainResult:
    """Walk session chain via handoff files (the only strategy).

    Args:
        session_id: Session UUID to walk backward from.
        project_path: Unused — kept for API compatibility.
        max_depth: Maximum chain depth.
        newest_first: If True, return entries in newest-to-oldest order.

    Returns:
        SessionChainResult with entries ordered oldest-to-newest by default.
    """
    result = walk_handoff_chain(session_id, max_depth)
    if newest_first and result.entries:
        result.entries.reverse()
    return result


def get_all_chain_files(
    session_id: str,
    project_path: Path | None = None,
    newest_first: bool = False,
) -> list[Path]:
    """Get all transcript file paths in a session chain."""
    result = walk_session_chain(session_id, project_path, newest_first=newest_first)
    return [e.transcript_path for e in result.entries]