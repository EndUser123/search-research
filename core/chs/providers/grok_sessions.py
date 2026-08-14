"""grok_sessions provider — reads from ~/.grok/sessions/<encoded-cwd>/<session-id>/chat_history.jsonl.

Grok Build stores session transcripts as JSONL with a different schema than
Claude Code or Codex. This provider walks the Grok session directory tree,
extracts searchable messages, and normalizes them into the CHS event format.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote

from filelock import FileLock

from ..archive import append_raw_event
from .base import ProviderCapabilities

_SESSIONS_DIR = Path.home() / ".grok" / "sessions"
_ARCHIVE_BASE = Path("P:/__csf/data/chs_archive")
_WATERMARK_DIR = _ARCHIVE_BASE / "watermarks" / "grok_sessions"
_LOCK_TIMEOUT = 30
_STALE_LOCK_THRESHOLD = 300

_ROLE_MAP: dict[str, str | None] = {
    "user": "user",
    "assistant": "assistant",
    "tool_result": "tool",
    "system": "system",
    "reasoning": None,
}


def _resolve_terminal_id(terminal_id: str | None) -> str:
    if terminal_id:
        return terminal_id
    from core.terminal_id import canonical_terminal_id
    return canonical_terminal_id()


def _compute_content_hash(provider_id, source_id, msg_type, content, line_num):
    raw = f"{provider_id}:{source_id}:{msg_type}:{content}:{line_num}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _extract_text_content(obj):
    content = obj.get("content")
    if content is None:
        summary = obj.get("summary", "")
        return f"[Reasoning] {summary}" if summary else ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                bt = block.get("type", "")
                if bt == "text":
                    parts.append(block.get("text", ""))
                elif bt == "tool_use":
                    parts.append(f"[Tool: {block.get('name', '')}]")
                else:
                    parts.append(json.dumps(block, separators=(",", ":")))
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return json.dumps(content, separators=(",", ":"))


def _format_tool_calls(obj):
    tcs = obj.get("tool_calls")
    if not tcs or not isinstance(tcs, list):
        return None
    parts = []
    for tc in tcs:
        if isinstance(tc, dict):
            name = tc.get("name", "unknown")
            args = tc.get("arguments", "")
            if isinstance(args, str) and len(args) > 200:
                args = args[:200] + "..."
            parts.append(f"[Tool: {name}] {args}")
    return "\n".join(parts) if parts else None


def _parse_timestamp(obj, line_num):
    ts = obj.get("timestamp")
    if ts:
        try:
            dt = datetime.fromtimestamp(int(ts), tz=UTC)
            return dt.isoformat()
        except (ValueError, OSError):
            pass
    return f"line:{line_num}"


def _session_dir_to_source(session_dir):
    session_id = session_dir.name
    cwd_encoded = session_dir.parent.name
    cwd = unquote(cwd_encoded)
    project = Path(cwd).name if cwd else "unknown"
    return {"source_id": session_id, "session_id": session_id, "cwd": cwd, "project": project}


def _discover_session_files():
    if not _SESSIONS_DIR.exists():
        return []
    results = []
    for chat_file in _SESSIONS_DIR.rglob("chat_history.jsonl"):
        if chat_file.stat().st_size == 0:
            continue
        results.append(chat_file)
    return sorted(results, key=lambda p: p.stat().st_mtime, reverse=True)


# Per-process index: session uuid -> chat_history.jsonl path.
# Avoids re-walking the sessions tree per fetch_session call (O(n^2) otherwise).
_FILE_INDEX: dict[str, Path] | None = None


def _file_for_source(source_id: str) -> Path | None:
    """Locate a session's chat_history.jsonl via the cached uuid->path index."""
    global _FILE_INDEX
    if _FILE_INDEX is None:
        _FILE_INDEX = {}
        for chat_file in _discover_session_files():
            sid = chat_file.parent.name
            if sid not in _FILE_INDEX:
                _FILE_INDEX[sid] = chat_file
    return _FILE_INDEX.get(source_id)


def _stale_lock_recovery(lock_path):
    try:
        if lock_path.exists():
            mtime = lock_path.stat().st_mtime
            if time.time() - mtime > _STALE_LOCK_THRESHOLD:
                lock_path.unlink()
    except OSError:
        pass


class GrokSessionsProvider:
    """Provider for Grok Build session transcripts."""

    provider_id: str = "grok_sessions"

    capabilities: ProviderCapabilities = ProviderCapabilities(
        supports_incremental=True,
        supports_backfill=True,
        has_task_events=True,
        has_tool_events=True,
    )

    def discover(self):
        sources = []
        for chat_file in _discover_session_files():
            session_dir = chat_file.parent
            info = _session_dir_to_source(session_dir)
            mtime = datetime.fromtimestamp(chat_file.stat().st_mtime, tz=UTC)
            sources.append({
                "source_id": info["source_id"],
                "occurred_at": mtime.isoformat(),
                "type": "session",
                "cwd": info["cwd"],
                "project": info["project"],
                "path": str(chat_file),
            })
        return sources

    def ingest_since(self, watermark=None, terminal_id=None):
        terminal_id = _resolve_terminal_id(
            watermark.get("terminal_id") if watermark else terminal_id
        )
        last_line_by_source = {}
        if watermark and watermark.get("processed_sources"):
            last_line_by_source = watermark["processed_sources"]

        lock_dir = _WATERMARK_DIR / "locks"
        lock_dir.mkdir(parents=True, exist_ok=True)
        safe_tid = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id)
        lock_path = lock_dir / f"{safe_tid}.lock"
        _stale_lock_recovery(lock_path)

        events = []
        try:
            with FileLock(lock_path, timeout=_LOCK_TIMEOUT):
                for chat_file in _discover_session_files():
                    session_dir = chat_file.parent
                    info = _session_dir_to_source(session_dir)
                    source_id = info["source_id"]
                    last_line = last_line_by_source.get(source_id, 0)
                    line_num = 0
                    new_last_line = last_line

                    try:
                        with open(chat_file, encoding="utf-8") as f:
                            for line in f:
                                line_num += 1
                                if line_num <= last_line:
                                    continue
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    obj = json.loads(line)
                                except json.JSONDecodeError:
                                    continue

                                msg_type = obj.get("type", "")
                                role = _ROLE_MAP.get(msg_type)
                                if role is None:
                                    continue

                                content = _extract_text_content(obj)
                                tool_text = _format_tool_calls(obj)
                                if tool_text:
                                    content = (content + "\n" + tool_text).strip() if content else tool_text
                                if not content or not content.strip():
                                    continue

                                event_id = f"{source_id}_{line_num}"
                                content_hash = _compute_content_hash(
                                    self.provider_id, source_id, msg_type, content, line_num)
                                occurred_at = _parse_timestamp(obj, line_num)
                                raw_payload_path = append_raw_event(self.provider_id, source_id, obj)

                                metadata = {
                                    "msg_type": msg_type,
                                    "sessionId": source_id,
                                    "cwd": info["cwd"],
                                    "project": info["project"],
                                    "line_num": line_num,
                                    "model": obj.get("model_id"),
                                    "tool_call_id": obj.get("tool_call_id"),
                                    "prompt_index": obj.get("prompt_index"),
                                    "synthetic_reason": obj.get("synthetic_reason"),
                                }
                                metadata = {k: v for k, v in metadata.items() if v is not None}

                                events.append({
                                    "provider_id": self.provider_id,
                                    "source_id": source_id,
                                    "event_id": event_id,
                                    "conversation_id": None,
                                    "session_id": source_id,
                                    "terminal_id": terminal_id,
                                    "turn_id": None,
                                    "occurred_at": occurred_at,
                                    "content_hash": content_hash,
                                    "raw_payload_path": raw_payload_path,
                                    "metadata": metadata,
                                })
                                new_last_line = line_num
                    except OSError:
                        continue
                    if new_last_line > last_line:
                        last_line_by_source[source_id] = new_last_line
        except Exception:
            pass
        return events

    def fetch_session(self, source_id):
        chat_file = _file_for_source(source_id)
        if chat_file is None:
            return {}
        session_dir = chat_file.parent
        info = _session_dir_to_source(session_dir)
        entries = []
        try:
            with open(chat_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    msg_type = obj.get("type", "")
                    role = _ROLE_MAP.get(msg_type)
                    if role is None:
                        continue
                    content = _extract_text_content(obj)
                    if not content.strip():
                        continue
                    entries.append({
                        "type": msg_type, "role": role, "content": content,
                        "tool_calls": obj.get("tool_calls"),
                        "tool_call_id": obj.get("tool_call_id"),
                    })
        except OSError:
            return {}
        if not entries:
            return {}
        mtime = chat_file.stat().st_mtime
        return {
            "session_id": source_id, "entries": entries,
            "message_count": len(entries),
            "started_at": datetime.fromtimestamp(mtime, tz=UTC).isoformat(),
            "cwd": info["cwd"], "project": info["project"],
        }

    def fetch_message(self, source_id, message_id):
        parts = message_id.rsplit("_", 1)
        if len(parts) != 2:
            return {}
        try:
            target_line = int(parts[1])
        except ValueError:
            return {}
        for chat_file in _discover_session_files():
            session_dir = chat_file.parent
            info = _session_dir_to_source(session_dir)
            if info["source_id"] != source_id:
                continue
            line_num = 0
            try:
                with open(chat_file, encoding="utf-8") as f:
                    for line in f:
                        line_num += 1
                        if line_num != target_line:
                            continue
                        line = line.strip()
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            return {}
                        msg_type = obj.get("type", "")
                        role = _ROLE_MAP.get(msg_type, "system")
                        content = _extract_text_content(obj)
                        return {
                            "message_id": message_id, "session_id": source_id,
                            "type": msg_type, "role": role, "content": content,
                            "tool_calls": obj.get("tool_calls"),
                            "cwd": info["cwd"], "project": info["project"],
                        }
            except OSError:
                return {}
        return {}
