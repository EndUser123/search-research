#!/usr/bin/env python3
"""
SessionStart Hook: CHS Delta Reindex

Fires on startup and resume. Performs incremental reindex of new entries
from Claude Code history.jsonl into the CHS v2 database.

Terminal-scoped paths prevent cross-terminal state collision.
Uses INSERT OR IGNORE for atomic duplicate detection.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# Add search-research package to path for core.chs imports
_SEARCH_RESEARCH_DIR = (
    Path(__file__).resolve().parent.parent.parent / "packages" / "search-research"
)
if _SEARCH_RESEARCH_DIR.exists():
    sys.path.insert(0, str(_SEARCH_RESEARCH_DIR))

HOOKS_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOKS_DIR.parent / "state" / "chs_delta_reindex"

# Source: Claude Code system-owned (never moves)
HISTORY_JSONL = Path.home() / ".claude" / "history.jsonl"

# Target: Project-managed derived data
DEFAULT_DB_PATH = Path("P:/__csf/data/chat_history.db")

# Project label for Claude Code history
CLAUDE_CODE_PROJECT_LABEL = "Claude Code"
CLAUDE_CODE_PROJECT_PATH = "~/.claude"

# Performance: batch size for commits
BATCH_SIZE = 100


def _resolve_terminal_id(data: dict | None = None) -> str:
    """Resolve terminal_id from hook input or environment."""
    if data:
        for key in ("terminal_id", "terminalId", "CLAUDE_TERMINAL_ID"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return os.environ.get("CLAUDE_TERMINAL_ID", "").strip() or "terminal_unknown"


def _safe_id(value: str) -> str:
    """Sanitize terminal_id for use in file paths."""
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _get_state_path(terminal_id: str) -> Path:
    """Return terminal-scoped path to last indexed line count."""
    safe_tid = _safe_id(terminal_id)
    return STATE_DIR / f"{safe_tid}_last_line_count.json"


def _read_last_line_count(state_path: Path) -> int:
    """Read the last indexed line count from state file."""
    if not state_path.exists():
        return 0
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return data.get("last_line_count", 0)
    except Exception:
        return 0


def _write_last_line_count(state_path: Path, line_count: int) -> None:
    """Write the current line count to state file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"last_line_count": line_count, "updated_at": datetime.now(UTC).isoformat()}),
        encoding="utf-8",
    )


def extract_text_content(message) -> str:
    """Extract text content from complex message structures."""
    if isinstance(message, str):
        return message

    if isinstance(message, dict):
        if message.get("type") == "tool_use":
            name = message.get("name", "")
            input_data = message.get("input", {})
            return f"[Tool: {name}] {json.dumps(input_data, separators=(',', ':'))}"

        if message.get("type") == "thinking":
            return f"[Thinking] {message.get('thinking', '')}"

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
                            name = block.get("name", "")
                            parts.append(f"[Tool: {name}]")
                        elif block.get("type") == "tool_result":
                            content = block.get("content", "")
                            if isinstance(content, list):
                                content = extract_text_content(content)
                            parts.append(str(content) if content else "")
                        elif block.get("type") == "thinking":
                            parts.append(f"[Thinking] {block.get('thinking', '')}")
                        else:
                            parts.append(json.dumps(block, separators=(",", ":")))
                    elif isinstance(block, str):
                        parts.append(block)
                return " ".join(parts)
            return str(content)

        return json.dumps(message, separators=(",", ":"))

    if isinstance(message, list):
        parts = []
        for block in message:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    name = block.get("name", "")
                    parts.append(f"[Tool: {name}]")
                elif block.get("type") == "thinking":
                    parts.append("[Thinking]")
                else:
                    parts.append(json.dumps(block, separators=(",", ":")))
            elif isinstance(block, str):
                parts.append(block)
        return " ".join(parts)

    return str(message)


def parse_claude_timestamp(ts) -> int:
    """Parse Claude timestamp (milliseconds since epoch) to Unix seconds."""
    if ts and isinstance(ts, (int, float)):
        return int(ts / 1000)
    return 0


class DeltaReindexer:
    """Incremental reindexer for Claude Code history.jsonl."""

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self._conn = None

    def _get_connection(self):
        if self._conn is None:
            from core.chs.db import get_connection

            self._conn = get_connection(self.db_path)
        return self._conn

    def init_schema(self) -> None:
        """Initialize the v2 schema if database doesn't exist."""
        from core.chs.db import init_db

        if not self.db_path.exists():
            init_db(self.db_path)

    def get_or_create_project(self) -> int:
        """Get or create the Claude Code project."""
        conn = self._get_connection()
        cursor = conn.execute("SELECT id FROM projects WHERE path = ?", (CLAUDE_CODE_PROJECT_PATH,))
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor = conn.execute(
            "INSERT INTO projects (path, label) VALUES (?, ?)",
            (CLAUDE_CODE_PROJECT_PATH, CLAUDE_CODE_PROJECT_LABEL),
        )
        conn.commit()
        return cursor.lastrowid

    def get_or_create_session(self, project_id: int, session_key: str, started_at: int) -> int:
        """Get or create a session."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND session_key = ?",
            (project_id, session_key),
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor = conn.execute(
            "INSERT INTO sessions (session_key, project_id, started_at) VALUES (?, ?, ?)",
            (session_key, project_id, started_at),
        )
        conn.commit()
        return cursor.lastrowid

    def ingest_message(
        self,
        project_id: int,
        session_id: int,
        message_id: str,
        timestamp: int,
        role: str,
        content: str,
    ) -> bool:
        """Ingest a single message. Returns True if inserted, False if skipped (duplicate)."""
        conn = self._get_connection()
        has_code = 1 if "```" in content or "def " in content or "class " in content else 0
        has_error = 1 if "error" in content.lower() or "exception" in content.lower() else 0
        cursor = conn.execute(
            """INSERT OR IGNORE INTO messages
               (message_id, session_id, project_id, timestamp, role, content, has_code, has_error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (message_id, session_id, project_id, timestamp, role, content, has_code, has_error),
        )
        return cursor.rowcount > 0

    def build_turns_for_session(self, session_id: int, project_id: int) -> int:
        """Build turn pairs (user+assistant) for a session."""
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT last_turn_built_message_id FROM sessions WHERE id = ?", (session_id,)
        )
        row = cursor.fetchone()
        last_built_id = row[0] if row and row[0] else 0

        cursor = conn.execute(
            """SELECT id, role, content, timestamp FROM messages
               WHERE session_id = ? AND id > ? ORDER BY timestamp""",
            (session_id, last_built_id),
        )
        messages = cursor.fetchall()
        turns_created = 0
        i = 0
        last_turn_message_id = None

        while i < len(messages):
            msg_id, role, content, timestamp = messages[i]
            if role == "user" and i + 1 < len(messages):
                next_msg_id, next_role, next_content, next_timestamp = messages[i + 1]
                if next_role == "assistant":
                    turn_content = f"User: {content}\nAssistant: {next_content}"
                    cursor = conn.execute(
                        """INSERT INTO turns
                           (session_id, project_id, start_message_id, end_message_id,
                            timestamp_start, timestamp_end, content)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            session_id,
                            project_id,
                            msg_id,
                            next_msg_id,
                            timestamp,
                            next_timestamp,
                            turn_content,
                        ),
                    )
                    last_turn_message_id = next_msg_id
                    turns_created += 1
                    i += 2
                else:
                    i += 1
            else:
                i += 1

        if last_turn_message_id:
            conn.execute(
                "UPDATE sessions SET last_turn_built_message_id = ? WHERE id = ?",
                (last_turn_message_id, session_id),
            )
            conn.commit()
        return turns_created

    def reindex_entries(self, entries: list[dict], project_id: int) -> dict:
        """Reindex a list of pre-parsed entries.

        Args:
            entries: List of history.jsonl entry dicts
            project_id: Project ID for ingestion

        Returns:
            Dict with stats: entries_processed, messages_ingested, turns_built
        """
        stats = {
            "entries_processed": 0,
            "messages_ingested": 0,
            "turns_built": 0,
        }

        # Group by session for turn pairing
        sessions: dict[str, list] = {}
        for entry in entries:
            sid = entry.get("sessionId")
            if sid:
                if sid not in sessions:
                    sessions[sid] = []
                sessions[sid].append(entry)

        # Process each session
        for sid, session_entries in sessions.items():
            session_entries.sort(key=lambda x: parse_claude_timestamp(x.get("timestamp", 0)))

            first_ts = (
                parse_claude_timestamp(session_entries[0].get("timestamp", 0))
                if session_entries
                else 0
            )
            session_id = self.get_or_create_session(project_id, sid, first_ts)

            pending_commit = 0

            for entry in session_entries:
                etype = entry.get("type", "")
                if etype not in ("user", "assistant", "tool", "system"):
                    continue

                raw_message = entry.get("message", "")
                content = extract_text_content(raw_message)
                if not content or not content.strip():
                    continue

                message_id = entry.get("uuid", "")
                if not message_id:
                    continue

                timestamp = parse_claude_timestamp(entry.get("timestamp", 0))

                if self.ingest_message(
                    project_id=project_id,
                    session_id=session_id,
                    message_id=message_id,
                    timestamp=timestamp,
                    role=etype,
                    content=content,
                ):
                    stats["messages_ingested"] += 1
                    pending_commit += 1

                    if pending_commit >= BATCH_SIZE:
                        self._get_connection().commit()
                        pending_commit = 0

            # Build turns for this session
            turns = self.build_turns_for_session(session_id, project_id)
            stats["turns_built"] += turns

            stats["entries_processed"] += len(session_entries)

            if pending_commit > 0:
                self._get_connection().commit()

        return stats

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        data: dict = {}
    else:
        try:
            data = json.loads(raw.lstrip("\ufeff"))
        except json.JSONDecodeError:
            data = {}

    terminal_id = _resolve_terminal_id(data)
    state_path = _get_state_path(terminal_id)

    # Check if history.jsonl exists
    if not HISTORY_JSONL.exists():
        print(
            json.dumps(
                {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}}
            )
        )
        return 0

    # Count current lines in history.jsonl
    try:
        with open(HISTORY_JSONL, encoding="utf-8") as f:
            current_line_count = sum(1 for _ in f)
    except Exception:
        current_line_count = 0

    last_line_count = _read_last_line_count(state_path)

    # No new entries
    if current_line_count <= last_line_count:
        print(
            json.dumps(
                {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}}
            )
        )
        return 0

    # Read only new entries
    new_entries = []
    try:
        with open(HISTORY_JSONL, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i < last_line_count:
                    continue
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    new_entries.append(entry)
                except json.JSONDecodeError:
                    continue
    except Exception:
        new_entries = []

    if not new_entries:
        _write_last_line_count(state_path, current_line_count)
        print(
            json.dumps(
                {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}}
            )
        )
        return 0

    # Perform delta reindex
    start_time = time.time()
    try:
        with DeltaReindexer(DEFAULT_DB_PATH) as reindexer:
            reindexer.init_schema()
            project_id = reindexer.get_or_create_project()
            stats = reindexer.reindex_entries(new_entries, project_id)
    except Exception as e:
        stats = {"error": str(e)}

    elapsed = time.time() - start_time

    # Update state with new line count
    _write_last_line_count(state_path, current_line_count)

    # Format output
    if "error" in stats:
        additional_context = f"CHS delta reindex: {stats['error']}"
    else:
        additional_context = (
            f"CHS delta reindex: +{stats.get('messages_ingested', 0)} messages, "
            f"+{stats.get('turns_built', 0)} turns in {elapsed:.1f}s"
        )

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": additional_context,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
