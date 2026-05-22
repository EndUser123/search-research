"""Session chain traversal for Claude Code.

Provides a unified interface for finding all session transcript files in a
session chain, given any session ID.

Single strategy: identity.json scan.

Algorithm:
  1. Scan all identity.json files under .claude/.artifacts/
  2. Build index: session_id -> [identity_records]
  3. For the target session_id:
     - If any record has transcript_chain (from snapshot restore), use it
     - Otherwise, return single-entry chain (session itself)
  4. Resolve each session_id to its .jsonl transcript path
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


def walk_session_chain(
    session_id: str,
    project_path: Path | None = None,
    max_depth: int = 50,
    newest_first: bool = False,
) -> SessionChainResult:
    """Walk session chain using identity.json scan.

    Scans all identity.json files to find terminal associations and
    pre-computed transcript chains (from snapshot restore).

    Args:
        session_id: The target session ID to find the chain for.
        project_path: Ignored (kept for backward compatibility).
        max_depth: Maximum chain depth.
        newest_first: If True, reverse the chain order.

    Returns:
        SessionChainResult with ordered chain entries.
    """
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
