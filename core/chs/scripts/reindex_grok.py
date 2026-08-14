#!/usr/bin/env python3
"""Reindex CHS from Grok Build session transcripts.

Reads from ~/.grok/sessions/ via the GrokSessionsProvider and populates
the CHS database using the v2 schema.

Usage:
    python -m core.chs.scripts.reindex_grok [--limit N] [--db-path PATH]
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

_PKG_ROOT = Path(__file__).resolve().parents[4]
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

DEFAULT_DB_PATH = Path("P:/__csf/data/grok_chat_history.db")
SCHEMA_PATH = _PKG_ROOT / "core" / "chs" / "schema.sql"
BATCH_SIZE = 10


def init_db(db_path: Path) -> sqlite3.Connection:
    """Initialize the database with the CHS schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema)
    conn.commit()
    return conn


def reindex(db_path: Path, limit: int | None = None) -> int:
    """Index Grok sessions into the DB."""
    from core.chs.providers.grok_sessions import GrokSessionsProvider

    conn = init_db(db_path)
    provider = GrokSessionsProvider()
    sources = provider.discover()

    if limit:
        sources = sources[:limit]

    logger.info("Indexing %d Grok sessions into %s", len(sources), db_path)

    indexed = 0
    messages_inserted = 0

    for source in sources:
        source_id = source["source_id"]
        cwd = source.get("cwd", "unknown")
        project = source.get("project", "unknown")

        cursor = conn.execute("SELECT id FROM projects WHERE path = ?", (cwd,))
        row = cursor.fetchone()
        if row:
            project_id = row[0]
        else:
            cursor = conn.execute(
                "INSERT INTO projects (path, label) VALUES (?, ?)", (cwd, project)
            )
            project_id = cursor.lastrowid

        cursor = conn.execute(
            "SELECT id FROM sessions WHERE project_id = ? AND session_key = ?",
            (project_id, source_id),
        )
        row = cursor.fetchone()
        if row:
            session_id = row[0]
        else:
            cursor = conn.execute(
                "INSERT INTO sessions (session_key, project_id, started_at) VALUES (?, ?, ?)",
                (source_id, project_id, int(source.get("occurred_at_ts", time.time()))),
            )
            session_id = cursor.lastrowid

        session_data = provider.fetch_session(source_id)
        entries = session_data.get("entries", [])

        for i, entry in enumerate(entries):
            role = entry["role"]
            content = entry["content"]
            if not content or not content.strip():
                continue

            msg_id = f"{source_id}_msg{i}"

            try:
                conn.execute(
                    "INSERT OR IGNORE INTO messages "
                    "(message_id, session_id, project_id, timestamp, role, content) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (msg_id, session_id, project_id, int(time.time()), role, content),
                )
                messages_inserted += 1
            except sqlite3.IntegrityError:
                pass

        conn.execute(
            "UPDATE sessions SET message_count = ? WHERE id = ?",
            (len(entries), session_id),
        )

        indexed += 1
        if indexed % BATCH_SIZE == 0:
            conn.commit()
            logger.info("  Indexed %d/%d sessions, %d messages", indexed, len(sources), messages_inserted)

    conn.commit()
    conn.close()
    logger.info("Done: %d sessions, %d messages indexed", indexed, messages_inserted)
    return messages_inserted


def main():
    parser = argparse.ArgumentParser(description="Reindex Grok sessions into CHS DB")
    parser.add_argument("--limit", type=int, default=None, help="Max sessions to index")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Database path")
    args = parser.parse_args()

    reindex(args.db_path, args.limit)


if __name__ == "__main__":
    main()
