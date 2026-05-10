"""claude-log provider — reads from ~/claude-log.jsonl (transcript diffs from log-hook.py)."""

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

# Source: claude-log hook output
HISTORY_JSONL = Path.home() / "claude-log.jsonl"

# Archive base for watermarks
_ARCHIVE_BASE = Path("P:\\\\\\__csf/data/chs_archive")
_WATERMARK_DIR = _ARCHIVE_BASE / "watermarks" / "claude_log"

# FileLock settings
_LOCK_TIMEOUT = 30
_STALE_LOCK_THRESHOLD = 300  # 5 minutes


def _resolve_terminal_id(terminal_id: str | None) -> str:
    """Resolve terminal_id from argument or canonical source.

    Uses canonical_terminal_id() to ensure consistent, collision-resistant IDs
    across all terminals. Falls back to 'default' only when called with an
    explicit None and no env var is set (legacy API compatibility).
    """
    if terminal_id:
        return terminal_id
    # Use canonical — never 'default' (prevents terminal collision)
    from core.terminal_id import canonical_terminal_id

    return canonical_terminal_id()


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
    if ts:
        try:
            dt = datetime.fromtimestamp(int(ts), tz=UTC)
            return dt.isoformat()
        except (ValueError, OSError):
            pass
    return datetime.now(UTC).isoformat()


def _extract_text_content(message) -> str:
    """Extract text content from complex message structures."""
    if isinstance(message, str):
        return message
    if isinstance(message, dict):
        if "text" in message:
            return message["text"]
        if "content" in message:
            content = message["content"]
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            parts.append(f"[Tool: {block.get('name', '')}]")
                        elif block.get("type") == "tool_result":
                            parts.append(str(block.get("content", "")))
                        elif block.get("type") == "thinking":
                            parts.append(f"[Thinking] {block.get('thinking', '')}")
                        else:
                            parts.append(json.dumps(block, separators=(",", ":")))
                    elif isinstance(block, str):
                        parts.append(block)
                return " ".join(parts)
            return str(content)
        return json.dumps(message, separators=((",", ":")))
    if isinstance(message, list):
        parts = []
        for block in message:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    parts.append(f"[Tool: {block.get('name', '')}]")
                elif block.get("type") == "thinking":
                    parts.append("[Thinking]")
                else:
                    parts.append(json.dumps(block, separators=(",", ":")))
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(parts)
    return str(message)


def _stale_lock_recovery(lock_path: Path) -> None:
    """Delete lock file if older than _STALE_LOCK_THRESHOLD seconds."""
    try:
        if lock_path.exists():
            mtime = lock_path.stat().st_mtime
            if time.time() - mtime > _STALE_LOCK_THRESHOLD:
                lock_path.unlink()
    except OSError:
        pass


class ClaudeLogProvider:
    """Provider for claude-log transcript diffs (log-hook.py output)."""

    provider_id: str = "claude_log"

    capabilities: ProviderCapabilities = ProviderCapabilities(
        supports_incremental=True,
        supports_backfill=True,
        has_task_events=False,
        has_tool_events=False,
    )

    def discover(self) -> list[dict]:
        """Discover available sources from claude-log.jsonl.

        Returns a list of dicts with source_id (session_id) for each unique
        session found in TRANSCRIPT_ITEM entries.
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
                    if entry.get("logEvent") != "TRANSCRIPT_ITEM":
                        continue
                    sid = entry.get("sessionId")
                    if sid and sid not in seen:
                        seen.add(sid)
                        ts = entry.get("logTimestamp")
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
        """Ingest TRANSCRIPT_ITEM events since watermark from claude-log.jsonl.

        Events are selected using numeric event_id tie-breaking per D7:
        - (occurred_at > last_occurred_at)
        - OR (occurred_at == last_occurred_at AND int(event_id.split("_")[1]) > last_event_num)

        Args:
            watermark: Watermark dict with last_event_id, last_occurred_at, terminal_id
            terminal_id: Optional terminal scope; uses watermark terminal_id if provided

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

                        if entry.get("logEvent") != "TRANSCRIPT_ITEM":
                            continue

                        sid = entry.get("sessionId")
                        if not sid:
                            continue

                        msg_type = entry.get("type", "")
                        if msg_type not in ("user", "assistant", "tool", "system"):
                            continue

                        raw_message = entry.get("message") or entry.get("content") or ""
                        content = _extract_text_content(raw_message)
                        if not content or not content.strip():
                            continue

                        # Build event_id from logTimestamp and index for uniqueness
                        ts = entry.get("logTimestamp")
                        ts_str = str(ts) if ts else "0"

                        # Use logTimestamp-based event_id: ts + idx to handle multiple items per second
                        event_id = entry.get("id") or entry.get("event_id") or f"log_{ts_str}"
                        if not entry.get("id") and not entry.get("event_id"):
                            # Deduplicate event_id within same second using index counter
                            idx_key = f"{sid}:{ts_str}"
                            idx = self._get_idx_counter(idx_key)
                            event_id = f"log_{ts_str}_{idx}"

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
                            "sessionId": sid,
                            "logEvent": "TRANSCRIPT_ITEM",
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

        except Exception:
            pass

        return events

    def _get_idx_counter(self, key: str) -> int:
        """Generate a per-key index for events with identical timestamps."""
        if not hasattr(self, "_idx_cache"):
            self._idx_cache: dict[str, int] = {}
        idx = self._idx_cache.get(key, 0) + 1
        self._idx_cache[key] = idx
        return idx

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
                    if entry.get("logEvent") == "TRANSCRIPT_ITEM" and entry.get("sessionId") == source_id:
                        session_entries.append(entry)
        except OSError:
            return {}

        if not session_entries:
            return {}

        session_entries.sort(key=lambda x: x.get("logTimestamp", 0) or 0)
        first_ts = session_entries[0].get("logTimestamp") if session_entries else None
        last_ts = session_entries[-1].get("logTimestamp") if session_entries else None

        return {
            "session_id": source_id,
            "entries": session_entries,
            "message_count": len(session_entries),
            "started_at": _parse_s_timestamp(first_ts) if first_ts else None,
            "ended_at": _parse_s_timestamp(last_ts) if last_ts else None,
        }

    def fetch_message(self, source_id: str, message_id: str) -> dict:
        """Fetch single message by source_id (session_id) and message_id (event_id)."""
        session = self.fetch_session(source_id)
        entries = session.get("entries", [])
        for entry in entries:
            eid = entry.get("id") or entry.get("event_id") or ""
            if eid == message_id or f"log_{entry.get('logTimestamp', '')}" == message_id:
                raw_message = entry.get("message") or entry.get("content") or ""
                return {
                    "message_id": message_id,
                    "session_id": source_id,
                    "type": entry.get("type"),
                    "message": raw_message,
                    "timestamp": entry.get("logTimestamp"),
                    "content": _extract_text_content(raw_message),
                }
        return {}
