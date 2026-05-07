"""codex_desktop provider — reads from ~/.codex/history.jsonl."""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path

from filelock import FileLock

from ..archive import append_raw_event
from .base import ProviderCapabilities

# Source: Codex Desktop system-owned history
HISTORY_JSONL = Path.home() / ".codex" / "history.jsonl"

# Archive base for watermarks
_ARCHIVE_BASE = Path("P:\\\\__csf/data/chs_archive")
_WATERMARK_DIR = _ARCHIVE_BASE / "watermarks" / "codex_desktop"

# FileLock settings
_LOCK_TIMEOUT = 30
_STALE_LOCK_THRESHOLD = 300  # 5 minutes


def _resolve_terminal_id(terminal_id: str | None) -> str:
    """Resolve terminal_id from argument or compute from current workspace.

    Per D3: terminal_id = codex_{workspace_hash[:8]} where workspace_hash
    is MD5 of the path string (first 8 hex chars).
    """
    if terminal_id:
        return terminal_id
    cwd = Path.cwd()
    cwd_hash = hashlib.md5(str(cwd).encode()).hexdigest()[:8]
    return f"codex_{cwd_hash}"


def _parse_event_num(event_id: str) -> int:
    """Parse numeric suffix from event_id for tie-breaking.

    Requires format event_NNNNN. Non-conforming IDs return -1.
    """
    try:
        return int(event_id.split("_")[1])
    except (IndexError, ValueError):
        return -1


def _compute_content_hash(provider_id: str, source_id: str, msg_type: str, content: str, timestamp: int) -> str:
    """Compute stable SHA-256 content hash for deduplication."""
    raw = f"{provider_id}:{source_id}:{msg_type}:{content}:{timestamp}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _parse_s_timestamp(ts: int | float | None) -> str:
    """Convert seconds-since-epoch to ISO 8601 string."""
    if ts is not None:
        try:
            dt = datetime.fromtimestamp(int(ts), tz=UTC)
            return dt.isoformat()
        except (ValueError, OSError):
            pass
    return datetime.now(UTC).isoformat()


def _stale_lock_recovery(lock_path: Path) -> None:
    """Delete lock file if older than _STALE_LOCK_THRESHOLD seconds."""
    try:
        if lock_path.exists():
            mtime = lock_path.stat().st_mtime
            if time.time() - mtime > _STALE_LOCK_THRESHOLD:
                lock_path.unlink()
    except OSError:
        pass


class CodexDesktopProvider:
    """Provider for Codex Desktop history (history.jsonl)."""

    provider_id: str = "codex_desktop"

    capabilities: ProviderCapabilities = ProviderCapabilities(
        supports_incremental=True,
        supports_backfill=True,
        has_task_events=True,
        has_tool_events=True,
    )

    def discover(self) -> list[dict]:
        """Discover available sources from history.jsonl.

        Returns a list of dicts with source_id (session_id) for each unique
        session found in history.jsonl.
        """
        sources = []
        if not HISTORY_JSONL.exists():
            return sources

        try:
            with open(HISTORY_JSONL, encoding="utf-8") as f:
                seen: set[str] = set()
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    sid = entry.get("session_id")
                    if sid and sid not in seen:
                        seen.add(sid)
                        # Get first timestamp as proxy for session start
                        ts = entry.get("ts")
                        occurred_at = _parse_s_timestamp(ts) if ts else datetime.now(UTC).isoformat()
                        sources.append({
                            "source_id": sid,
                            "occurred_at": occurred_at,
                            "type": "session",
                        })
        except OSError:
            pass

        return sources

    def ingest_since(
        self,
        watermark: dict | None = None,
        terminal_id: str | None = None,
    ) -> list[dict]:
        """Ingest events since watermark from history.jsonl.

        Events are selected using timestamp tie-breaking per D7:
        - (occurred_at > last_occurred_at)
        - OR (occurred_at == last_occurred_at AND event_num > last_event_num)

        Args:
            watermark: Watermark dict with last_event_id, last_occurred_at, terminal_id
            terminal_id: Optional terminal scope; uses computed codex_{hash} if not provided

        Returns:
            List of event dicts ready for normalized DB insertion
        """
        terminal_id = _resolve_terminal_id(watermark.get("terminal_id") if watermark else terminal_id)

        last_occurred_at = watermark.get("last_occurred_at") if watermark else None
        last_event_id = watermark.get("last_event_id") if watermark else None
        last_event_num = _parse_event_num(last_event_id) if last_event_id else -1

        if not HISTORY_JSONL.exists():
            return []

        lock_dir = _WATERMARK_DIR / "locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        safe_tid = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id)
        lock_path = lock_dir / f"{safe_tid}.lock"

        # Stale lock recovery on startup
        _stale_lock_recovery(lock_path)

        events: list[dict] = []
        processed_count = 0

        try:
            with FileLock(lock_path, timeout=_LOCK_TIMEOUT):
                with open(HISTORY_JSONL, encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        sid = entry.get("session_id")
                        if not sid:
                            continue

                        # Codex history.jsonl entries are all user messages
                        msg_type = "user"

                        text = entry.get("text", "")
                        content = text.strip() if isinstance(text, str) else ""
                        if not content:
                            continue

                        event_id = entry.get("uuid", "")
                        if not event_id:
                            continue

                        ts = entry.get("ts")
                        occurred_at = _parse_s_timestamp(ts) if ts else datetime.now(UTC).isoformat()

                        # Tie-breaking: occurred_at comparison
                        if last_occurred_at is not None:
                            if occurred_at < last_occurred_at:
                                continue
                            if occurred_at == last_occurred_at:
                                event_num = _parse_event_num(event_id)
                                if event_num <= last_event_num:
                                    continue

                        raw_payload_path = append_raw_event(self.provider_id, sid, entry)
                        content_hash = _compute_content_hash(
                            self.provider_id, sid, msg_type, content,
                            int(ts) if ts else 0,
                        )

                        metadata = {
                            "msg_type": msg_type,
                            "session_id": sid,
                        }

                        events.append({
                            "provider_id": self.provider_id,
                            "source_id": sid,
                            "event_id": event_id,
                            "conversation_id": None,
                            "session_id": sid,
                            "terminal_id": terminal_id,
                            "turn_id": None,
                            "occurred_at": occurred_at,
                            "content_hash": content_hash,
                            "raw_payload_path": raw_payload_path,
                            "metadata": metadata,
                        })

                        last_occurred_at = occurred_at
                        last_event_id = event_id
                        last_event_num = _parse_event_num(event_id)
                        processed_count += 1

        except Exception:
            pass

        return events

    def fetch_session(self, source_id: str) -> dict:
        """Fetch full session by source_id (session_id)."""
        if not HISTORY_JSONL.exists():
            return {}

        session_entries = []
        try:
            with open(HISTORY_JSONL, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if entry.get("session_id") == source_id:
                        session_entries.append(entry)
        except OSError:
            return {}

        if not session_entries:
            return {}

        session_entries.sort(key=lambda x: x.get("ts", 0) or 0)
        first_ts = session_entries[0].get("ts") if session_entries else None
        last_ts = session_entries[-1].get("ts") if session_entries else None

        return {
            "session_id": source_id,
            "entries": session_entries,
            "message_count": len(session_entries),
            "started_at": _parse_s_timestamp(first_ts) if first_ts else None,
            "ended_at": _parse_s_timestamp(last_ts) if last_ts else None,
        }

    def fetch_message(self, source_id: str, message_id: str) -> dict:
        """Fetch single message by source_id (session_id) and message_id (uuid)."""
        session = self.fetch_session(source_id)
        entries = session.get("entries", [])
        for entry in entries:
            if entry.get("uuid") == message_id:
                return {
                    "message_id": message_id,
                    "session_id": source_id,
                    "type": "user",
                    "text": entry.get("text"),
                    "ts": entry.get("ts"),
                    "content": entry.get("text", ""),
                }
        return {}
