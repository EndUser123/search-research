"""Session chain traversal for Claude Code.

Provides a unified interface for finding all session transcript files in a
session chain, given any session ID.

Two strategies, tried in order:
  1. Handoff-file chain   — reliable when handoff files exist
  2. sessions-index scan  — fallback using mtime ordering

Limitations
-----------
Without handoff files (post-March 19 2026 sessions), chain traversal is
best-effort: sessions that were NOT created by /compact have no recorded
parentage and cannot be reliably chained. Only sessions that were created
by /compact have a deterministic prior-session link (stored in the handoff
file written at compaction time).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

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
    created: datetime | None
    first_user_message: str | None = None


@dataclass
class SessionChainResult:
    entries: list[SessionChainEntry] = field(default_factory=list)
    depth: int = 0
    origin_session_id: str | None = None


# ---------------------------------------------------------------------------
# Strategy 1: Handoff-file chain
# ---------------------------------------------------------------------------


def _get_prior_transcript_path(handoff_path: Path) -> Path | None:
    """Extract prior session transcript path from a handoff file."""
    try:
        with open(handoff_path, encoding="utf-8") as f:
            data = json.load(f)
        path_str = data.get("resume_snapshot", {}).get("transcript_path")
        if path_str:
            p = Path(path_str)
            if p.exists():
                return p
    except (OSError, json.JSONDecodeError, PermissionError):
        pass
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
    origin_session_id: str | None = None

    while handoff_path and chain_depth < max_depth:
        prior_transcript = _get_prior_transcript_path(handoff_path)
        if not prior_transcript or str(prior_transcript) in visited:
            break
        visited.add(str(prior_transcript))

        prior_session_id = prior_transcript.stem
        prior_handoff = _find_handoff_referencing(prior_transcript)
        if not prior_handoff:
            origin_session_id = prior_session_id

        entries.append(
            SessionChainEntry(
                session_id=prior_session_id,
                transcript_path=prior_transcript,
                parent_transcript_path=None,
                created=None,
            )
        )

        handoff_path = prior_handoff
        chain_depth += 1

    # Fill in parent links (entries are oldest→newest, so next entry is the parent)
    for i, entry in enumerate(entries):
        if i < len(entries) - 1:
            entry.parent_transcript_path = entries[i + 1].transcript_path

    entries.reverse()
    return SessionChainResult(
        entries=entries,
        depth=chain_depth + 1,
        origin_session_id=origin_session_id or (entries[0].session_id if entries else None),
    )


# ---------------------------------------------------------------------------
# Strategy 2: sessions-index scan (fallback for recent sessions without handoffs)
# ---------------------------------------------------------------------------

# Reverse-engineered from session-chain investigation:
# - Only /compact sessions have a recorded prior session (in handoff file)
# - Non-compact sessions have no parentage recorded
# - For compact sessions, the handoff file links to the PRIOR session's transcript
#   (the session that was running before /compact was invoked)
# - The NEW session (after /compact) starts with /compact as first message


def load_sessions_index(project_path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Load sessions-index.json as a dict keyed by sessionId."""
    if project_path is None:
        project_path = _projects_dir() / "P--"
    idx_path = Path(project_path) / "sessions-index.json"
    if not idx_path.exists():
        return {}
    try:
        with open(idx_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    # Handle both list and dict formats
    if isinstance(data, list):
        return {entry["sessionId"]: entry for entry in data}
    if isinstance(data, dict):
        if "entries" in data:
            return {e["sessionId"]: e for e in data["entries"]}
        if "sessions" in data:
            return {e["sessionId"]: e for e in data["sessions"]}
        # sessions-index.json format: {"<sessionId>": {...}}
        return data
    return {}


def _extract_first_user_message(jsonl_path: Path) -> str | None:
    """Read first user message text from a session transcript."""
    try:
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") == "user":
                    msg = entry.get("message", {})
                    content = msg.get("content", [])
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                return block.get("text", "")[:200]
                    return None
    except (OSError, PermissionError):
        pass
    return None


def walk_sessions_index_chain(
    session_id: str,
    project_path: Path | None = None,
) -> SessionChainResult:
    """Walk session chain using sessions-index.json mtime ordering.

    This is a best-effort fallback for recent sessions that have no handoff files.
    Heuristic: sessions whose first user message starts with "/compact" are continuations.
    The chain is inferred by sorting sessions by mtime and linking /compact sessions
    to the nearest prior session.

    Limitations:
      - Only /compact sessions can be chained (they have a prior session)
      - Non-compact sessions (e.g., new terminal starts) cannot be linked to prior sessions
      - Chain inference via mtime ordering is approximate, not deterministic
    """
    if project_path is None:
        project_path = _projects_dir() / "P--"

    sessions_index = load_sessions_index(project_path)

    # Collect sessions using createdAt from sessions-index (st_birthtime = session birth)
    # Fall back to st_birthtime if sessions-index lacks the entry
    sessions: dict[str, tuple[Path, datetime]] = {}
    project = Path(project_path)
    for sid, info in sessions_index.items():
        # Try fullPath first, then reconstruct path
        full_path = info.get("fullPath")
        if full_path:
            p = Path(full_path)
        else:
            p = project / f"{sid}.jsonl"
        if not p.exists():
            continue
        # Use createdAt (st_birthtime) for chronological ordering
        created_at_ms = info.get("createdAt")
        if created_at_ms:
            try:
                created = datetime.fromtimestamp(created_at_ms / 1000)
            except (ValueError, OSError):
                created = datetime.min
        else:
            try:
                stat_result = p.stat()
                # st_birthtime = session birth (Python 3.12+ / Windows); st_ctime = metadata change on Unix
                if hasattr(stat_result, "st_birthtime"):
                    created = datetime.fromtimestamp(stat_result.st_birthtime)
                else:
                    created = datetime.fromtimestamp(stat_result.st_ctime)  # pyright: ignore[deprecated]
            except OSError:
                created = datetime.min
        sessions[sid] = (p, created)

    if session_id not in sessions:
        return SessionChainResult()

    # Pre-compute first user messages for compact-marked sessions
    compact_sessions: dict[str, str] = {}
    for sid, (path, _) in sessions.items():
        msg = _extract_first_user_message(path)
        if msg:
            compact_sessions[sid] = msg

    # Determine if the target session is a /compact session
    target_msg = compact_sessions.get(session_id, "")
    target_is_compact = target_msg.startswith("/compact")

    if not target_is_compact:
        # Non-compact session — no recorded prior, cannot chain
        path, mtime = sessions[session_id]
        return SessionChainResult(
            entries=[
                SessionChainEntry(
                    session_id=session_id,
                    transcript_path=path,
                    parent_transcript_path=None,
                    created=mtime,
                    first_user_message=target_msg or None,
                )
            ],
            depth=1,
            origin_session_id=session_id,
        )

    # Walk backward through /compact sessions by createdAt ordering
    # Build ordered list once (sessions.items is already sorted by createdAt)
    sorted_ids = [sid for sid, _ in sorted(sessions.items(), key=lambda x: x[1][1])]
    sid_to_idx = {sid: i for i, sid in enumerate(sorted_ids)}

    chain: list[str] = []
    visited: set[str] = set()
    current = session_id

    while current and current not in visited:
        visited.add(current)
        chain.append(current)

        # Find predecessor: nearest older /compact session
        predecessor_id: str | None = None
        current_idx = sid_to_idx.get(current, -1)
        for i in range(current_idx - 1, -1, -1):
            pred_id = sorted_ids[i]
            if pred_id in visited:
                continue
            pred_msg = compact_sessions.get(pred_id, "")
            if pred_msg.startswith("/compact"):
                predecessor_id = pred_id
                break

        if predecessor_id is None:
            break

        current = predecessor_id

    chain.reverse()

    # Build entries
    entries: list[SessionChainEntry] = []
    for i, sid in enumerate(chain):
        path, mtime = sessions[sid]
        parent_path: Path | None = None
        if i < len(chain) - 1:
            parent_path = sessions[chain[i + 1]][0]
        entries.append(
            SessionChainEntry(
                session_id=sid,
                transcript_path=path,
                parent_transcript_path=parent_path,
                created=mtime,
                first_user_message=compact_sessions.get(sid, "") or None,
            )
        )

    return SessionChainResult(
        entries=entries,
        depth=len(entries),
        origin_session_id=chain[0] if chain else None,
    )


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------


def walk_session_chain(
    session_id: str,
    project_path: Path | None = None,
    max_depth: int = 50,
) -> SessionChainResult:
    """Walk session chain using the best available strategy.

    Args:
        session_id: Session UUID to walk backward from.
        project_path: Project directory. Defaults to P--.
        max_depth: Maximum chain depth (handoff strategy only).

    Returns:
        SessionChainResult with entries in oldest-to-newest order.

    Strategy selection:
      - If handoff files exist linking to prior sessions → handoff chain
      - Otherwise → sessions-index mtime heuristic (approximate for /compact sessions only)
    """
    if project_path is None:
        project_path = _projects_dir() / "P--"

    # Try handoff-file chain first (reliable for sessions with handoff files)
    handoff_result = walk_handoff_chain(session_id, max_depth)
    # Use entries[0].session_id != session_id (not depth > 1) to detect "found a prior":
    #   - No prior found: entries[0].session_id == session_id (returned self as origin)
    #   - Prior(s) found: entries[0].session_id != session_id (first entry is the prior)
    # depth==1 means "1 prior found"; depth>1 means "multiple priors found"
    # Both should use the handoff chain, not fall back to sessions-index
    if handoff_result.entries and handoff_result.entries[0].session_id != session_id:
        return handoff_result

    # Fall back to sessions-index mtime heuristic
    return walk_sessions_index_chain(session_id, project_path)


def get_all_chain_files(
    session_id: str,
    project_path: Path | None = None,
) -> list[Path]:
    """Get all transcript file paths in a session chain.

    Returns paths in oldest-to-newest order.
    """
    result = walk_session_chain(session_id, project_path)
    return [e.transcript_path for e in result.entries]
