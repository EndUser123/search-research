"""Incremental FAISS Index Updater - Update index without full rebuild."""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from ...config import config

logger = logging.getLogger(__name__)
try:
    import faiss
    import numpy as np

    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False


class IncrementalIndexUpdater:
    """Incrementally update FAISS index with new messages only."""

    def __init__(
        self,
        db_path: str | None = None,
        index_path: str | None = None,
        state_path: str | None = None,
    ) -> None:
        """Initialize incremental updater.

        Args:
            db_path: Path to CHS database
            index_path: Path to FAISS index
            state_path: Path to incremental state file
        """
        if not HAS_FAISS:
            raise ImportError("faiss-cpu required: pip install faiss-cpu")
        if db_path is None:
            db_path = config.CHS_DB_PATH
        if index_path is None:
            index_path = config.CHS_INDEX_PATH
        if state_path is None:
            state_path = config.CHS_STATE_PATH
        self.db_path = Path(db_path)
        self.index_path = Path(index_path)
        self.state_path = Path(state_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def get_new_messages(self, limit: int = 1000) -> list[dict[str, Any]]:
        """
        Find new/modified messages since last update.

        Args:
            limit: Max messages to retrieve

        Returns:
            List of new messages with embeddings
        """
        state = self._load_state()
        last_timestamp = state.get("last_timestamp", 0)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "\n            SELECT name FROM sqlite_master\n            WHERE type='table' AND name='chat_messages'\n        "
        )
        if not cursor.fetchone():
            logger.warning(
                f"chat_messages table not found in database (path: {self.db_path}). Database may not be initialized. Returning empty results."
            )
            conn.close()
            return []
        cursor.execute(
            "\n            SELECT id, content, timestamp\n            FROM chat_messages\n            WHERE timestamp > ?\n            ORDER BY timestamp ASC\n            LIMIT ?\n        ",
            (last_timestamp, limit),
        )
        messages = []
        for row in cursor.fetchall():
            messages.append(
                {
                    "id": row["id"],
                    "content": row["content"],
                    "embedding": None,
                    "timestamp": row["timestamp"],
                }
            )
        conn.close()
        return messages

    def update_index(self, messages: list[dict[str, Any]]) -> dict:
        """
        Append new messages to existing FAISS index.

        Args:
            messages: List of messages with embeddings

        Returns:
            Update result with count and duration
        """
        import time

        start = time.time()
        if not messages:
            return {"count": 0, "duration": 0, "status": "no_new_messages"}
        try:
            index = faiss.read_index(str(self.index_path))
        except Exception:
            return {"count": 0, "duration": 0, "status": "index_not_found"}
        embeddings = np.array([msg["embedding"] for msg in messages], dtype=np.float32)
        index.add(embeddings)
        faiss.write_index(index, str(self.index_path))
        last_timestamp = max(msg["timestamp"] for msg in messages)
        self._save_state(last_timestamp, len(messages))
        duration = time.time() - start
        return {"count": len(messages), "duration": duration, "status": "success"}

    def _load_state(self) -> dict:
        """Load incremental update state."""
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text())
            except Exception:
                pass
        return {"last_timestamp": 0, "total_updates": 0}

    def _save_state(self, last_timestamp: float, count: int) -> None:
        """Save incremental update state."""
        state = self._load_state()
        state["last_timestamp"] = last_timestamp
        state["total_updates"] = state.get("total_updates", 0) + count
        state["last_update"] = datetime.now().isoformat()
        self.state_path.write_text(json.dumps(state, indent=2))

    def update_from_jsonl(self, session_path: str, watermark_pos: int) -> tuple[int, int]:
        """Parse new JSONL lines since watermark position.

        Reads a JSONL (JSON Lines) file starting from the given byte offset,
        parses valid JSON entries, and returns the updated watermark position
        along with the count of messages successfully parsed.

        This method gracefully handles:
        - Nonexistent files (returns original watermark, 0 messages)
        - Empty files (returns 0, 0)
        - Watermark beyond file size (returns original watermark, 0 messages)
        - Invalid JSON entries (skips them, counts only valid entries)

        Args:
            session_path: Absolute or relative path to the JSONL session file.
            watermark_pos: Byte offset indicating where to start reading.
                          Only reads content after this position.

        Returns:
            A tuple of (new_watermark, messages_added):
            - new_watermark: Updated byte offset (file size if messages added,
                           original watermark if no new messages)
            - messages_added: Count of valid JSON entries parsed since watermark

        Example:
            >>> updater = IncrementalIndexUpdater()
            >>> watermark, count = updater.update_from_jsonl("session.jsonl", 1024)
            >>> print(f"Added {count} messages, new watermark at {watermark}")
        """
        path = Path(session_path)
        if not path.exists():
            return (watermark_pos, 0)
        file_size = path.stat().st_size
        if file_size == 0:
            return (0, 0)
        content = path.read_text()
        content_length = len(content)
        if watermark_pos >= content_length:
            return (watermark_pos, 0)
        if watermark_pos > 0:
            content = content[watermark_pos:]
        messages_added = 0
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                json.loads(line)
                messages_added += 1
            except (json.JSONDecodeError, ValueError):
                continue
        if messages_added == 0:
            return (watermark_pos, 0)
        return (content_length, messages_added)

    def run_incremental_update(self, limit: int = 1000) -> dict:
        """
        Run incremental update: find new messages and add to index.

        Args:
            limit: Max messages to process

        Returns:
            Update result dict
        """
        messages = self.get_new_messages(limit)
        return self.update_index(messages)
