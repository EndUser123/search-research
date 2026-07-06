"""Session chain traversal for Claude Code.

Provides a unified interface for finding all session transcript files in a
session chain, given any session ID.

Strategy 1 — session_registry.jsonl (cross-terminal + cross-compaction):
  1. Query P:/.claude/.artifacts/session_registry.jsonl by session_id
     (written by the PreCompact hook; same session_id aggregates across all
     terminals and all compactions in the session's lifetime).
  2. Deduplicate by transcript_path; emit oldest-first (append order).

Strategy 2 — identity.json scan (fallback for pre-registry data):
  1. Scan all identity.json files under .claude/.artifacts/
  2. Build index: session_id -> [identity_records]
  3. For the target session_id:
     - If any record has transcript_chain (from snapshot restore), use it
     - Otherwise, return single-entry chain (session itself)
  4. Resolve each session_id to its .jsonl transcript path

The registry strategy is authoritative when present — it is the only source
that links a session across terminals and compaction boundaries. The identity
scan is retained because the registry only contains rows the PreCompact hook
wrote (sessions that predate the hook, or ran without it wired, are absent).
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def _claude_base() -> Path:
    # On Windows, Claude Code may store state on a project drive (P:)
    # before the user home directory. Check P:\\\\\\.claude first.
    p_drive_claude = Path("P:") / ".claude"
    if p_drive_claude.exists():
        return p_drive_claude
    return Path.home() / ".claude"


def _projects_dir() -> Path:
    # Transcript files live in the Windows user profile, not on P: drive.
    # P:\\\\\\.claude is used for state (handoff files), but projects live in HOME.
    return Path.home() / ".claude" / "projects"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SessionChainEntry:
    session_id: str
    transcript_path: Path
    parent_transcript_path: Path | None  # older -> newer link
    created: datetime | None = None
    first_user_message: str | None = None


@dataclass
class SessionChainResult:
    entries: list[SessionChainEntry] = field(default_factory=list)
    depth: int = 0
    origin_session_id: str | None = None


# ---------------------------------------------------------------------------
# Identity.json scan
# ---------------------------------------------------------------------------


def _scan_identity_files() -> dict[str, list[dict[str, Any]]]:
    """Scan all identity.json files under .claude/.artifacts/.

    Returns dict: {session_id: [identity_records]} where each record has:
      terminal_id, transcript_path, transcript_chain, captured_at
    """
    index: dict[str, list[dict[str, Any]]] = {}

    artifacts_root = _claude_base() / ".artifacts"
    if not artifacts_root.exists():
        return index

    for identity_file in artifacts_root.glob("*/identity.json"):
        try:
            data = json.loads(identity_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, PermissionError):
            continue

        claude = data.get("claude", {})
        session_id = claude.get("session_id", "")
        if not session_id:
            continue

        terminal_id = data.get("terminal", {}).get("id", "")
        transcript_path = claude.get("transcript_path", "")
        transcript_chain = claude.get("transcript_chain")
        captured_at = data.get("captured_at", "")

        record = {
            "terminal_id": terminal_id,
            "transcript_path": transcript_path,
            "transcript_chain": transcript_chain,
            "captured_at": captured_at,
        }

        index.setdefault(session_id, []).append(record)

    return index


def _resolve_transcript_path(session_id: str) -> Path | None:
    """Find the .jsonl path for a session ID by scanning projects directory.

    SECURITY: Rejects session_ids containing path traversal sequences before glob
    interpolation to prevent directory traversal attacks.
    """
    # Reject path traversal attempts before using in glob
    if ".." in session_id or "/" in session_id or "\\" in session_id:
        logger.warning("Invalid session_id (path traversal attempt): %s", session_id)
        return None
    for jsonl_file in _projects_dir().rglob(f"{session_id}.jsonl"):
        if jsonl_file.exists():
            return jsonl_file
    return None


# ---------------------------------------------------------------------------
# Registry strategy (cross-terminal + cross-compaction)
# ---------------------------------------------------------------------------

_REGISTRY_LIB = Path(
    "P:/packages/.claude-marketplace/plugins/snapshot/scripts/hooks/__lib"
)


def _walk_via_registry(
    session_id: str,
    max_depth: int,
) -> list[SessionChainEntry] | None:
    """Query session_registry.jsonl for the terminal-wide session chain.

    Two-step expansion (session → terminal → all sibling sessions):
      1. Query by session_id to find the terminal_id.
      2. Query by terminal_id to find ALL sessions that ran in that terminal.
      3. Bound to sessions whose first appearance is at or before the current
         session's first appearance (excludes sessions started after the
         current one — e.g. a later parallel invocation in the same terminal).
      4. Emit oldest-first (registry append order), deduplicated by
         transcript_path.

    This is the terminal-chain semantics /recap and /export-session need
    ("every session that ran in this terminal, leading up to the current
    one"). A single session_id query is insufficient because compaction
    rewrites the same transcript file — all rows for one session_id dedup to
    a single transcript, yielding depth=1.

    Returns None if the registry has no rows for this session (caller falls
    back to identity.json scan).
    """
    registry_path = _claude_base() / ".artifacts" / "session_registry.jsonl"
    if not registry_path.exists() or not _REGISTRY_LIB.exists():
        return None

    sys.path.insert(0, str(_REGISTRY_LIB))
    try:
        from session_registry import query_registry  # type: ignore[import-not-found]
    except ImportError:
        return None
    finally:
        sys.path.pop(0)

    # Step 1: find terminal_id(s) for this session.
    try:
        seed = query_registry(
            session_id=session_id, limit=10_000, registry_path=registry_path
        )
    except Exception:
        return None
    if not seed:
        return None

    terminal_ids = {r.get("terminal_id") for r in seed if r.get("terminal_id")}
    if not terminal_ids:
        return None

    # Bound: the current session's first appearance timestamp.
    current_first_ts = min(
        (r.get("ts") or "" for r in seed if r.get("ts")), default=""
    )

    # Step 2: gather every row across the session's terminal(s).
    all_rows: list[dict[str, Any]] = []
    try:
        for tid in terminal_ids:
            all_rows.extend(
                query_registry(
                    terminal_id=tid, limit=10_000, registry_path=registry_path
                )
            )
    except Exception:
        return None

    # Step 3: classify in-bounds sessions (first appearance <= current first).
    sessions_first: dict[str, str] = {}
    for raw in all_rows:
        sid = raw.get("session_id")
        ts = raw.get("ts") or ""
        if sid and ts:
            if sid not in sessions_first or ts < sessions_first[sid]:
                sessions_first[sid] = ts
    in_bounds = {
        sid
        for sid, ts in sessions_first.items()
        if not current_first_ts or ts <= current_first_ts
    }

    # Step 4: collect transcript paths oldest-first (all_rows is append-order).
    projects_root = _projects_dir().resolve()
    seen_paths: set[str] = set()
    entries: list[SessionChainEntry] = []
    for raw in all_rows:
        sid = raw.get("session_id")
        if sid not in in_bounds:
            continue
        tp = raw.get("transcript_path")
        if not tp or tp in seen_paths:
            continue
        path = Path(tp)
        try:
            path.resolve().relative_to(projects_root)
        except (ValueError, OSError):
            continue
        if not path.exists():
            continue
        seen_paths.add(tp)
        entries.append(
            SessionChainEntry(
                session_id=sid or session_id,
                transcript_path=path,
                parent_transcript_path=None,
                created=None,
            )
        )

    if not entries:
        return None

    entries = entries[:max_depth]
    for i, entry in enumerate(entries):
        if i > 0:
            entry.parent_transcript_path = entries[i - 1].transcript_path
    return entries


# ---------------------------------------------------------------------------
# Identity.json scan strategy
# ---------------------------------------------------------------------------


def walk_session_chain(
    session_id: str,
    project_path: Path | None = None,
    max_depth: int = 50,
    newest_first: bool = False,
) -> SessionChainResult:
    """Walk the session chain for the given session_id.

    Strategy 1: session_registry.jsonl (cross-terminal + cross-compaction).
    Strategy 2 (fallback): identity.json scan with snapshot-restore chains.

    Args:
        session_id: The target session ID to find the chain for.
        project_path: Ignored (kept for backward compatibility).
        max_depth: Maximum chain depth.
        newest_first: If True, reverse the chain order.

    Returns:
        SessionChainResult with ordered chain entries.
    """
    # Strategy 1: registry
    registry_entries = _walk_via_registry(session_id, max_depth)
    if registry_entries:
        entries = registry_entries
        if newest_first:
            entries = list(reversed(entries))
        return SessionChainResult(
            entries=entries,
            depth=len(entries),
            origin_session_id=entries[0].session_id,
        )

    # Strategy 2: identity.json scan
    index = _scan_identity_files()

    # Find the transcript_chain from any identity record for this session
    chain_ids: list[str] | None = None
    records = index.get(session_id, [])
    for record in records:
        tc = record.get("transcript_chain")
        if tc and isinstance(tc, list):
            chain_ids = tc
            break

    # If we have a pre-computed chain, use it
    if chain_ids:
        entries: list[SessionChainEntry] = []
        visited: set[str] = set()
        for chain_sid in chain_ids:
            if len(entries) >= max_depth:
                break
            chain_transcript = _resolve_transcript_path(chain_sid)
            if chain_transcript and str(chain_transcript) not in visited:
                entries.append(
                    SessionChainEntry(
                        session_id=chain_sid,
                        transcript_path=chain_transcript,
                        parent_transcript_path=None,
                        created=None,
                    )
                )
                visited.add(str(chain_transcript))

        # Append the current session as the newest
        current_transcript = _resolve_transcript_path(session_id)
        if current_transcript and str(current_transcript) not in visited:
            entries.append(
                SessionChainEntry(
                    session_id=session_id,
                    transcript_path=current_transcript,
                    parent_transcript_path=None,
                    created=None,
                )
            )

        # Fill parent links (oldest -> ... -> current)
        for i, entry in enumerate(entries):
            if i > 0:
                entry.parent_transcript_path = entries[i - 1].transcript_path

        if newest_first:
            entries.reverse()

        return SessionChainResult(
            entries=entries,
            depth=len(entries),
            origin_session_id=entries[0].session_id if entries else None,
        )

    # No transcript_chain: single-entry chain
    current_transcript = _resolve_transcript_path(session_id)
    if not current_transcript:
        return SessionChainResult()

    entries = [
        SessionChainEntry(
            session_id=session_id,
            transcript_path=current_transcript,
            parent_transcript_path=None,
            created=None,
        )
    ]

    return SessionChainResult(
        entries=entries,
        depth=1,
        origin_session_id=session_id,
    )


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def get_all_chain_files(
    session_id: str,
    project_path: Path | None = None,
    newest_first: bool = False,
) -> list[Path]:
    """Get all transcript file paths in a session chain."""
    result = walk_session_chain(session_id, project_path, newest_first=newest_first)
    return [e.transcript_path for e in result.entries]
