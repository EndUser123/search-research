"""Chat Indexer for CHS v2.

Provides ChatIndexer class with incremental JSONL ingestion and turn building.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from search_research.core.chs.db import get_connection
from search_research.core.chs.utils import file_identity, parse_jsonl_line


class ChatIndexer:
    """Indexer for chat history JSONL files."""

    def __init__(self, db_path: str | Path = ":memory:", conn: sqlite3.Connection | None = None):
        self.db_path = str(db_path)
        self._conn: sqlite3.Connection | None = conn

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = get_connection(self.db_path)
        return self._conn

    def _index_file(
        self, file_path: str, project_id: int, session_key: str, start_position: int = 0
    ) -> int:
        path = Path(file_path)
        try:
            file_size = path.stat().st_size
        except OSError:
            return 0
        try:
            with open(path, encoding="utf-8") as f:
                f.seek(start_position)
                for line in f:
                message_data = parse_jsonl_line(line)
                if message_data:
                    session_id = self._get_or_create_session(
                        project_id=project_id, session_key=session_key
                    )
                    self._ingest_message(
                        session_id=session_id, project_id=project_id, message_data=message_data
                    )
        self._save_checkpoint(str(path), file_size)
        return file_size

    def _get_or_create_project(self, path: str) -> int:
        conn = self._get_connection()
        cursor = conn.execute("SELECT id FROM projects WHERE path = ?", (path,))
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor = conn.execute("INSERT INTO projects (path) VALUES (?)", (path,))
        conn.commit()
        return cursor.lastrowid

    def _get_or_create_session(self, project_id: int, session_key: str) -> int:
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
            (session_key, project_id, int(time.time())),
        )
        conn.commit()
        return cursor.lastrowid

    def _ingest_message(self, session_id: int, project_id: int, message_data: dict) -> int | None:
        conn = self._get_connection()
        message_id = message_data.get("message_id")
        if not message_id:
            return None
        cursor = conn.execute("SELECT id FROM messages WHERE message_id = ?", (message_id,))
        existing_row = cursor.fetchone()
        if existing_row:
            return existing_row[0]
        cursor = conn.execute(
            "INSERT INTO messages (message_id, session_id, project_id, timestamp, role, content) VALUES (?, ?, ?, ?, ?, ?)",
            (
                message_id,
                session_id,
                project_id,
                message_data.get("timestamp", 0),
                message_data.get("role", "user"),
                message_data.get("content", ""),
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def _build_turns_for_session(self, session_id: int, project_id: int) -> int:
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT last_turn_built_message_id FROM sessions WHERE id = ?", (session_id,)
        )
        row = cursor.fetchone()
        last_built_id = row[0] if row and row[0] else 0
        cursor = conn.execute(
            "SELECT id, role, content, timestamp FROM messages WHERE session_id = ? AND id > ? ORDER BY timestamp",
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
                    conn.execute(
                        "INSERT INTO turns (session_id, project_id, start_message_id, end_message_id, timestamp_start, timestamp_end, content) VALUES (?, ?, ?, ?, ?, ?, ?)",
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

    def _save_checkpoint(self, file_identity: str, file_position: int) -> None:
        conn = self._get_connection()
        conn.execute(
            "INSERT INTO indexer_checkpoint (file_identity, file_position, last_processed_at) VALUES (?, ?, ?) ON CONFLICT(file_identity) DO UPDATE SET file_position = excluded.file_position, last_processed_at = excluded.last_processed_at, updated_at = strftime('%s','now')",
            (file_identity, file_position, int(time.time())),
        )
        conn.commit()

    def _get_checkpoint(self, file_identity: str) -> int | None:
        conn = self._get_connection()
        cursor = conn.execute(
            "SELECT file_position FROM indexer_checkpoint WHERE file_identity = ?", (file_identity,)
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def daemon_loop(
        self, jsonl_dir: str | Path, poll_interval: float = 1.0, idle_timeout: int = 3600
    ) -> None:
        from search_research.core.chs.utils import discover_chat_logs

        while True:
            jsonl_files = discover_chat_logs(jsonl_dir)
            for jsonl_path in jsonl_files:
                identity = file_identity(jsonl_path)
                checkpoint = self._get_checkpoint(identity)
                start_pos = checkpoint if checkpoint is not None else 0
                self._index_file(
                    file_path=str(jsonl_path),
                    project_id=1,
                    session_key=jsonl_path.stem,
                    start_position=start_pos,
                )
            self._close_idle_sessions(timeout=idle_timeout)
            time.sleep(poll_interval)

    def _close_idle_sessions(self, timeout: int = 3600) -> None:
        conn = self._get_connection()
        cutoff_time = int(time.time()) - timeout
        conn.execute(
            "UPDATE sessions SET is_closed = 1, ended_at = ? WHERE is_closed = 0 AND last_message_timestamp < ?",
            (int(time.time()), cutoff_time),
        )
        conn.commit()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
