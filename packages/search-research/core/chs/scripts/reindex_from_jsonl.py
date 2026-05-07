#!/usr/bin/env python3
"""Reindex CHS v2 from Claude Code history.jsonl.

Reads from ~/.claude/history.jsonl (source of truth) and populates
P:\\\\__csf/data/chat_history.db using the v2 schema.

Usage:
    python -m core.chs.scripts.reindex_from_jsonl [--dry-run] [--limit N]

The source data (~/.claude/history.jsonl) is NOT moved - it's system-owned.
The derived database (P:\\\\__csf/data/chat_history.db) is project-managed.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Source: Claude Code system-owned (never moves)
HISTORY_JSONL = Path.home() / ".claude" / "history.jsonl"

# Target: Project-managed derived data
DEFAULT_DB_PATH = Path("P:\\\\__csf/data/chat_history.db")

# Project label for Claude Code history
CLAUDE_CODE_PROJECT_LABEL = "Claude Code"
CLAUDE_CODE_PROJECT_PATH = "~/.claude"

# Performance: batch size for commits
BATCH_SIZE = 1000


def extract_text_content(message) -> str:
    """Extract text content from complex message structures.

    Handles:
    - Simple string messages
    - Dict messages (tool_use, thinking, etc.)
    - Array of content blocks

    Args:
        message: Message content (str, dict, or list)

    Returns:
        Extracted text as string
    """
    if isinstance(message, str):
        return message

    if isinstance(message, dict):
        # Handle tool_use
        if message.get("type") == "tool_use":
            name = message.get("name", "")
            input_data = message.get("input", {})
            return f"[Tool: {name}] {json.dumps(input_data, separators=(',', ':'))}"

        # Handle thinking
        if message.get("type") == "thinking":
            return f"[Thinking] {message.get('thinking', '')}"

        # Handle generic text field (OpenAI format: {"text": "..."})
        if "text" in message:
            return message["text"]

        # Handle content field (Claude Code format: {"role": "user", "content": "..."})
        if "content" in message:
            content = message["content"]
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                # Array of content blocks
                parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            name = block.get("name", "")
                            parts.append(f"[Tool: {name}]")
                        elif block.get("type") == "tool_result":
                            # CRIT-002 fix: extract content field, don't JSON-encode
                            # Content can be a string or a list of content blocks
                            content = block.get("content", "")
                            if isinstance(content, list):
                                # Recursively extract nested content blocks
                                content = extract_text_content(content)
                            parts.append(str(content) if content else "")
                        elif block.get("type") == "thinking":
                            # Include thinking content for searchability
                            parts.append(f"[Thinking] {block.get('thinking', '')}")
                        else:
                            parts.append(json.dumps(block, separators=(",", ":")))
                    elif isinstance(block, str):
                        parts.append(block)
                return " ".join(parts)
            return str(content)

        # Fallback: stringify the dict
        return json.dumps(message, separators=(",", ":"))

    if isinstance(message, list):
        # Array of content blocks
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
    """Parse Claude timestamp (milliseconds since epoch) to Unix seconds.

    Args:
        ts: Timestamp in milliseconds since epoch, or None

    Returns:
        Unix timestamp in seconds, or 0 if invalid
    """
    if ts and isinstance(ts, (int, float)):
        return int(ts / 1000)
    return 0


class HistoryReindexer:
    """Reindexer for Claude Code history.jsonl to CHS v2 schema."""

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
        from core.chs.db import database_is_initialized, init_db

        if not self.db_path.exists() or not database_is_initialized(self.db_path):
            logger.info(f"Initializing CHS schema at {self.db_path}")
            init_db(self.db_path)
        else:
            logger.info(f"Using existing database at {self.db_path}")

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
        logger.info(f"Created project id={cursor.lastrowid} for Claude Code")
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
        """Ingest a single message. Returns True if inserted, False if skipped (duplicate).

        Uses INSERT OR IGNORE for atomic duplicate detection (eliminates TOCTOU race).
        Does NOT commit - caller batches commits for performance.
        """
        conn = self._get_connection()
        # Has code detection
        has_code = 1 if "```" in content or "def " in content or "class " in content else 0
        has_error = 1 if "error" in content.lower() or "exception" in content.lower() else 0
        cursor = conn.execute(
            """INSERT OR IGNORE INTO messages
               (message_id, session_id, project_id, timestamp, role, content, has_code, has_error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (message_id, session_id, project_id, timestamp, role, content, has_code, has_error),
        )
        # INSERT OR IGNORE returns 0 if duplicate (row unchanged)
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

    def reindex(
        self,
        history_path: Path,
        dry_run: bool = False,
        limit: int | None = None,
        commit_every: int = BATCH_SIZE,
    ) -> dict:
        """Reindex history.jsonl into the v2 schema.

        Args:
            history_path: Path to history.jsonl
            dry_run: If True, parse and show stats without writing
            limit: If set, only process first N entries
            commit_every: Number of messages between commits (default BATCH_SIZE)

        Returns:
            Dict with stats: entries_read, sessions_found, messages_ingested, turns_built
        """
        stats = {
            "entries_read": 0,
            "entries_skipped": 0,
            "sessions_found": 0,
            "messages_ingested": 0,
            "turns_built": 0,
        }

        if not history_path.exists():
            logger.error(f"History file not found: {history_path}")
            return stats

        # Initialize schema and project (for dry_run too, to get accurate stats)
        if not dry_run:
            self.init_schema()
            project_id = self.get_or_create_project()
        else:
            project_id = 0

        # Stream entries, grouping by session for turn pairing
        logger.info(f"Streaming entries from {history_path}")
        sessions: dict[str, list] = {}
        entries_read = 0
        pending_commit = 0

        with open(history_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entries_read += 1
                if limit and entries_read > limit:
                    break

                sid = entry.get("sessionId")
                if not sid:
                    stats["entries_skipped"] += 1
                    continue

                if sid not in sessions:
                    sessions[sid] = []
                sessions[sid].append(entry)

        stats["entries_read"] = entries_read
        stats["sessions_found"] = len(sessions)
        logger.info(f"Read {entries_read} entries, found {len(sessions)} sessions")

        if dry_run:
            logger.info("[DRY RUN] Would ingest:")
            for sid, entries in list(sessions.items())[:5]:
                logger.info(f"  Session {sid}: {len(entries)} messages")
            if len(sessions) > 5:
                logger.info(f"  ... and {len(sessions) - 5} more sessions")
            return stats

        # Process each session (session data cleared after processing to free memory)
        # Iterate over a list of keys to allow deletion during iteration
        for sid in list(sessions.keys()):
            entries = sessions[sid]
            # Sort by timestamp
            entries.sort(key=lambda x: parse_claude_timestamp(x.get("timestamp", 0)))

            # Get or create session
            first_ts = parse_claude_timestamp(entries[0].get("timestamp", 0)) if entries else 0
            session_id = self.get_or_create_session(project_id, sid, first_ts)

            # Ingest messages with batch commits
            for entry in entries:
                etype = entry.get("type", "")
                if etype not in ("user", "assistant", "tool", "system"):
                    stats["entries_skipped"] += 1
                    continue

                raw_message = entry.get("message", "")
                content = extract_text_content(raw_message)
                if not content or not content.strip():
                    stats["entries_skipped"] += 1
                    continue

                message_id = entry.get("uuid", "")
                if not message_id:
                    stats["entries_skipped"] += 1
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

                    # Batch commit every commit_every messages
                    if pending_commit >= commit_every:
                        self._get_connection().commit()
                        pending_commit = 0

            # Build turns for this session (includes its own commit)
            turns = self.build_turns_for_session(session_id, project_id)
            stats["turns_built"] += turns

            # Free session memory after processing
            del entries
            del sessions[sid]

            if stats["messages_ingested"] % 10000 == 0 and stats["messages_ingested"] > 0:
                logger.info(f"Processed {stats['messages_ingested']:,} messages...")

        # Final commit for any remaining messages
        if pending_commit > 0:
            self._get_connection().commit()

        logger.info(f"Reindex complete: {stats}")
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
    parser = argparse.ArgumentParser(description="Reindex CHS v2 from Claude Code history.jsonl")
    parser.add_argument(
        "--db-path",
        type=str,
        default=str(DEFAULT_DB_PATH),
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--history-path",
        type=str,
        default=str(HISTORY_JSONL),
        help=f"Path to history.jsonl (default: {HISTORY_JSONL})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and show stats without writing to database",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of entries to process (for testing)",
    )
    args = parser.parse_args()

    history_path = Path(args.history_path).expanduser()
    db_path = Path(args.db_path).expanduser()

    if not history_path.exists():
        logger.error(f"History file not found: {history_path}")
        logger.error("Cannot reindex without source data.")
        return 1

    start_time = time.time()
    with HistoryReindexer(db_path) as reindexer:
        stats = reindexer.reindex(history_path, dry_run=args.dry_run, limit=args.limit)

    elapsed = time.time() - start_time
    logger.info(f"Reindex completed in {elapsed:.1f}s")
    logger.info(f"Stats: {stats}")

    if args.dry_run:
        logger.info("[DRY RUN] No data was written.")
    else:
        # Verify counts
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("SELECT COUNT(*) FROM messages")
        msg_count = cursor.fetchone()[0]
        cursor = conn.execute("SELECT COUNT(*) FROM turns")
        turn_count = cursor.fetchone()[0]
        conn.close()
        logger.info(f"Database verification: {msg_count:,} messages, {turn_count:,} turns")

    return 0


if __name__ == "__main__":
    sys.exit(main())
