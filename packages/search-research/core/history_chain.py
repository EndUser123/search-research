"""Session chain traversal via history.jsonl.

Walks the parent-UUID chain backward from any message to the origin session,
using history.jsonl as the persistent chain backbone (session .jsonl files
may be compacted away, but messages persist in history.jsonl).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths (platform-aware)
# ---------------------------------------------------------------------------


def _claude_base() -> Path:
    """Claude Code base directory (platform-specific).

    On Windows: C:\\Users\\brsth\\.claude
    On macOS/Linux: ~/.claude
    """
    return Path.home() / ".claude"


def _history_jsonl() -> Path:
    return _claude_base() / "history.jsonl"


def _sessions_index(project_path: str | Path | None = None) -> Path:
    """Sessions index for a project.

    Defaults to P:'s sessions-index.json.
    On Windows: C:/Users/<user>/.claude/projects/<project>/sessions-index.json
    """
    if project_path is None:
        project_path = "P:\\\\"
    pp = Path(project_path)

    # Find .claude/projects/<project> in the path and extract just <project>
    try:
        projects_idx = pp.parts.index("projects") + 1
        project_name = pp.parts[projects_idx]
    except (ValueError, IndexError):
        # .claude/projects/<project> not found — fall back
        project_name = "P--"

    return Path.home() / ".claude" / "projects" / project_name / "sessions-index.json"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ChainEntry:
    """A single entry in the parent chain."""

    uuid: str
    parent_uuid: str | None
    session_id: str
    entry_type: str  # "user" | "assistant" | "summary" | etc.
    message: str | dict | None  # str for summaries, dict for user/assistant entries
    summary: str | None  # Only set for type="summary" entries
    leaf_uuid: str | None  # Only set for type="summary" entries
    created: datetime | None
    is_origin: bool = False


@dataclass
class ChainWalkResult:
    """Result of walking a parent chain."""

    entries: list[ChainEntry]
    depth: int
    origin_session_id: str | None
    compacted_sessions: set[str]  # session IDs whose .jsonl is missing
    index_age: datetime | None  # When the UUID index was built


# ---------------------------------------------------------------------------
# UUID offset index
# ---------------------------------------------------------------------------


class UUIDIndex:
    """In-memory UUID → (file_offset, byte_length) index for history.jsonl.

    Built lazily on first access, validated against file mtime on subsequent
    accesses. Not persistent — rebuilt per-process.
    """

    def __init__(self, history_path: Path | None = None) -> None:
        self._history_path = history_path or _history_jsonl()
        self._index: dict[str, tuple[int, int]] = {}  # uuid → (offset, len)
        self._built_at: datetime | None = None
        self._file_mtime: float = 0.0

    @property
    def built_at(self) -> datetime | None:
        return self._built_at

    def _check_stale(self) -> bool:
        """Return True if the index is stale and should be rebuilt."""
        if not self._history_path.exists():
            return True
        current_mtime = self._history_path.stat().st_mtime
        return current_mtime != self._file_mtime

    def build(self) -> None:
        """Build the UUID offset index by scanning history.jsonl once."""
        self._index.clear()
        path = self._history_path
        if not path.exists():
            return

        self._file_mtime = path.stat().st_mtime
        offset = 0
        with path.open("rb") as fh:
            for line in fh:
                line_len = len(line)
                try:
                    entry = json.loads(line.decode("utf-8", errors="replace"))
                except json.JSONDecodeError:
                    offset += line_len
                    continue
                uuid = entry.get("uuid") or entry.get("leafUuid")
                if uuid:
                    self._index[uuid] = (offset, line_len)
                offset += line_len

        self._built_at = datetime.now()

    def get(self, uuid: str) -> dict[str, Any] | None:
        """Look up a UUID and return the full entry dict, or None if not found."""
        if self._built_at is None or self._check_stale():
            self.build()

        if uuid not in self._index:
            return None

        offset, length = self._index[uuid]
        with self._history_path.open("rb") as fh:
            fh.seek(offset)
            raw = fh.read(length)
        try:
            return json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return None


# ---------------------------------------------------------------------------
# Sessions index helpers
# ---------------------------------------------------------------------------


def load_sessions_index(
    project_path: str | Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Load sessions-index.json, return dict keyed by sessionId."""
    path = _sessions_index(project_path)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {entry["sessionId"]: entry for entry in data}
    if isinstance(data, dict) and "entries" in data:
        return {entry["sessionId"]: entry for entry in data["entries"]}
    if isinstance(data, dict) and "sessions" in data:
        return {entry["sessionId"]: entry for entry in data["sessions"]}
    if isinstance(data, dict) and "entries" not in data and "sessions" not in data and not isinstance(data, list):
        # Direct-key format: {"uuid": {"sessionId": "...", ...}, ...}
        return data
    return {}


def session_file_exists(
    session_id: str,
    project_path: str | Path | None = None,
    _sessions_index: dict[str, dict[str, Any]] | None = None,
) -> bool:
    """Return True if the session's .jsonl file still exists on disk.

    Args:
        session_id: Session ID to check.
        project_path: Project path (only used if _sessions_index not provided).
        _sessions_index: Pre-loaded sessions index to avoid N+1 disk reads.
    """
    index = _sessions_index if _sessions_index is not None else load_sessions_index(project_path)
    entry = index.get(session_id)
    if not entry:
        return False
    full_path = entry.get("fullPath")
    if not full_path:
        return False
    return Path(full_path).exists()


# ---------------------------------------------------------------------------
# Core chain walk
# ---------------------------------------------------------------------------


def walk_chain(
    start_uuid: str | None = None,
    session_id: str | None = None,
    index: UUIDIndex | None = None,
    project_path: str | Path | None = None,
    depth: int = 200,
    summary_only: bool = False,
) -> ChainWalkResult:
    """Walk the parent-UUID chain from a starting point back to origin.

    Args:
        start_uuid: UUID to start from. If None, uses the latest message
            from the given session_id.
        session_id: Session to start from (used only if start_uuid is None).
        index: Pre-built UUID index. If None, a new one is created.
        project_path: Project path for sessions-index.json. Defaults to P:.
        depth: Maximum number of hops to walk.
        summary_only: If True, only collect entries of type="summary".

    Returns:
        ChainWalkResult with all chain entries, depth, origin session, and
        set of compacted (missing .jsonl) sessions.
    """
    idx = index or UUIDIndex()
    if idx._built_at is None:
        idx.build()

    sessions_index = load_sessions_index(project_path)

    # Resolve start point
    if start_uuid is None:
        if session_id is None:
            raise ValueError("Either start_uuid or session_id must be provided")
        entry = sessions_index.get(session_id)
        if not entry:
            raise ValueError(f"Session {session_id} not found in sessions-index.json")
        # Find the latest uuid for this session in history.jsonl
        start_uuid = _latest_uuid_for_session(session_id)

    if start_uuid is None:
        raise ValueError("Could not resolve start point")

    entries: list[ChainEntry] = []
    compacted: set[str] = set()
    current_uuid: str | None = start_uuid
    depth_count = 0

    while current_uuid and depth_count < depth:
        raw = idx.get(current_uuid)
        if raw is None:
            break
        depth_count += 1

        # Collect only if it's a message entry type we care about
        entry_type = raw.get("type", "")

        if summary_only and entry_type != "summary":
            current_uuid = raw.get("parentUuid")
            continue

        is_origin = raw.get("parentUuid") is None

        # Determine session_id for this entry
        entry_session = raw.get("sessionId") or (
            sessions_index.get(session_id, {}).get("sessionId", "unknown")
            if session_id
            else "unknown"
        )

        chain_entry = ChainEntry(
            uuid=current_uuid,
            parent_uuid=raw.get("parentUuid"),
            session_id=entry_session,
            entry_type=entry_type,
            message=raw.get("message"),
            summary=raw.get("summary") if entry_type == "summary" else None,
            leaf_uuid=raw.get("leafUuid") if entry_type == "summary" else None,
            created=datetime.fromisoformat(raw["created"]) if "created" in raw else None,
            is_origin=is_origin,
        )
        entries.append(chain_entry)

        # Check if session file is missing (pass pre-loaded index to avoid N+1 reads)
        if not session_file_exists(chain_entry.session_id, project_path, sessions_index):
            compacted.add(chain_entry.session_id)

        if is_origin:
            break

        current_uuid = raw.get("parentUuid")

    # Reverse so we walk oldest → newest
    entries.reverse()

    # Find origin session
    origin_session: str | None = None
    if entries and entries[0].is_origin:
        origin_session = entries[0].session_id

    return ChainWalkResult(
        entries=entries,
        depth=depth_count,
        origin_session_id=origin_session,
        compacted_sessions=compacted,
        index_age=idx.built_at,
    )


def _latest_uuid_for_session(session_id: str) -> str | None:
    """Find the latest (most recent) message UUID for a session via single-pass scan."""
    latest_uuid: str | None = None
    latest_time: float = 0.0

    path = _history_jsonl()
    if not path.exists():
        return None

    with path.open("rb") as fh:
        for line in fh:
            try:
                entry = json.loads(line.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            if entry.get("sessionId") == session_id and entry.get("uuid"):
                created = entry.get("created", "")
                if created:
                    try:
                        ts = datetime.fromisoformat(created).timestamp()
                        if ts > latest_time:
                            latest_time = ts
                            latest_uuid = entry["uuid"]
                    except (ValueError, OSError):
                        pass
    return latest_uuid


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def format_chain_summary(result: ChainWalkResult) -> str:
    """Format a ChainWalkResult as a human-readable summary."""

    def _message_preview(msg: str | dict | None) -> str:
        """Extract a short preview string from a message field."""
        match msg:
            case None:
                return ""
            case str() as s:
                return s[:80] + ("..." if len(s) > 80 else "")
            case dict() as d:
                content = d.get("content")
                if isinstance(content, list):
                    parts = []
                    for block in content:
                        if isinstance(block, dict):
                            text = block.get("content") or block.get("text", "")
                            if isinstance(text, str):
                                parts.append(text[:60])
                    return " | ".join(parts)[:80]
                return str(content)[:80] if content else ""
            case _:
                # Defensive fallback for any future message types
                return ""  # type: ignore[unreachable]

    lines = ["=== Chain Path ==="]
    for i, entry in enumerate(result.entries):
        marker = " (ORIGIN)" if entry.is_origin else ""
        session = entry.session_id[:8] if entry.session_id else "?"
        if entry.summary:
            snippet = entry.summary[:80] + ("..." if len(entry.summary) > 80 else "")
            lines.append(
                f"  [{i}] {entry.entry_type} | session={session} | {entry.uuid[:8]}{marker}"
            )
            lines.append(f"       summary: {snippet}")
        elif entry.message:
            snippet = _message_preview(entry.message)
            lines.append(
                f"  [{i}] {entry.entry_type} | session={session} | {entry.uuid[:8]}{marker}"
            )
            lines.append(f"       message: {snippet}")
        else:
            lines.append(
                f"  [{i}] {entry.entry_type} | session={session} | {entry.uuid[:8]}{marker}"
            )

    lines.append(f"\nDepth: {result.depth} hops")
    if result.compacted_sessions:
        lines.append(f"Compacted sessions (no .jsonl): {len(result.compacted_sessions)}")
        for sid in sorted(result.compacted_sessions):
            lines.append(f"  - {sid}")
    if result.index_age:
        lines.append(f"Index built: {result.index_age.isoformat()}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

# Global shared index (built on first use, reused across calls within same process)
_global_index: UUIDIndex | None = None


def get_index() -> UUIDIndex:
    """Get the shared global UUID index (lazy singleton)."""
    global _global_index
    if _global_index is None:
        _global_index = UUIDIndex()
        _global_index.build()
    elif _global_index._check_stale():
        _global_index.build()
    return _global_index


def walk_chain_simple(
    session_id: str | None = None,
    start_uuid: str | None = None,
    depth: int = 200,
    summary_only: bool = True,
) -> ChainWalkResult:
    """Convenience wrapper using the global index.

    Use this when you don't need to manage index lifecycle manually.
    """
    return walk_chain(
        start_uuid=start_uuid,
        session_id=session_id,
        index=get_index(),
        depth=depth,
        summary_only=summary_only,
    )
