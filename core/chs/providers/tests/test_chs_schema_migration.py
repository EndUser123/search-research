"""Test CHS schema migration from old schema to new schema.

Old schema (pre multi-provider):
- events table with PRIMARY KEY on (provider_id, source_id, event_id)
- No content_hash column
- No tasks table
- No event_log table

New schema (post multi-provider change 004):
- events table with PRIMARY KEY on (provider_id, source_id, content_hash)
- content_hash column added
- tasks table added
- event_log table added
- Indexes: idx_events_provider_id, idx_events_provider_occurred
"""

import sqlite3
from pathlib import Path

import pytest


# Old schema (pre-change-004, before multi-provider support)
OLD_SCHEMA = """
CREATE TABLE events (
    provider_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    conversation_id TEXT,
    session_id TEXT,
    terminal_id TEXT,
    turn_id TEXT,
    occurred_at TEXT NOT NULL,
    raw_payload_path TEXT NOT NULL,
    cached_at TEXT NOT NULL,
    metadata_json TEXT,
    PRIMARY KEY (provider_id, source_id, event_id)
);
"""

# New schema additions (change-004) that get applied on top of old schema
NEW_SCHEMA_ADDITIONS = """
-- Add content_hash column (not in old schema)
ALTER TABLE events ADD COLUMN content_hash TEXT;

-- tasks table (new in multi-provider)
CREATE TABLE IF NOT EXISTS tasks (
    provider_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    conversation_id TEXT,
    session_id TEXT,
    terminal_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    status TEXT,
    priority INTEGER,
    metadata_json TEXT,
    PRIMARY KEY (provider_id, task_id)
);

-- event_log table (new in multi-provider)
CREATE TABLE IF NOT EXISTS event_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    raw_payload_path TEXT NOT NULL,
    cached_at TEXT NOT NULL,
    metadata_json TEXT
);

-- Indexes for events table
CREATE INDEX IF NOT EXISTS idx_events_provider_id ON events(provider_id);
CREATE INDEX IF NOT EXISTS idx_events_provider_occurred ON events(provider_id, occurred_at);
"""


class TestSchemaMigration:
    """Test schema migration from old CHS schema to new multi-provider schema."""

    def test_old_data_preserved_after_migration(self, tmp_path: Path) -> None:
        """Create DB with old schema, insert data, apply new schema, verify data preserved."""
        db_path = tmp_path / "test_migration.db"

        # Step 1: Create DB with old schema
        conn = sqlite3.connect(str(db_path))
        conn.executescript(OLD_SCHEMA)
        conn.commit()

        # Step 2: Insert a row into old schema
        conn.execute(
            """
            INSERT INTO events
            (provider_id, source_id, event_id, conversation_id, session_id,
             terminal_id, turn_id, occurred_at, raw_payload_path, cached_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "test_provider",
                "test_source",
                "test_event_123",
                "conv_456",
                "session_789",
                "term_abc",
                "turn_001",
                "2024-01-15T10:30:00Z",
                "/payloads/event_123.json",
                "2024-01-15T10:30:01Z",
                '{"key": "value"}',
            ),
        )
        conn.commit()

        # Verify old row exists before migration
        cursor = conn.execute(
            "SELECT provider_id, source_id, event_id, conversation_id FROM events"
        )
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "test_provider"
        assert row[1] == "test_source"
        assert row[2] == "test_event_123"
        conn.close()

        # Step 3: Apply new schema additions
        conn = sqlite3.connect(str(db_path))
        conn.executescript(NEW_SCHEMA_ADDITIONS)
        conn.commit()

        # Step 4: Verify old row still present and readable
        cursor = conn.execute(
            "SELECT provider_id, source_id, event_id, conversation_id, session_id FROM events"
        )
        row = cursor.fetchone()
        assert row is not None, "Old data should be preserved after migration"
        assert row[0] == "test_provider"
        assert row[1] == "test_source"
        assert row[2] == "test_event_123"
        assert row[3] == "conv_456"
        assert row[4] == "session_789"
        conn.close()

    def test_content_hash_column_added(self, tmp_path: Path) -> None:
        """Verify content_hash column exists after migration."""
        db_path = tmp_path / "test_content_hash.db"

        # Create with old schema
        conn = sqlite3.connect(str(db_path))
        conn.executescript(OLD_SCHEMA)
        conn.commit()
        conn.close()

        # Apply new schema
        conn = sqlite3.connect(str(db_path))
        conn.executescript(NEW_SCHEMA_ADDITIONS)
        conn.commit()

        # Verify content_hash column exists
        cursor = conn.execute("PRAGMA table_info(events)")
        columns = {row[1] for row in cursor.fetchall()}
        assert "content_hash" in columns, "content_hash column should be added"

        # Verify we can insert a row with content_hash
        conn.execute(
            """
            INSERT INTO events
            (provider_id, source_id, event_id, content_hash, occurred_at, raw_payload_path, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "new_provider",
                "new_source",
                "new_event_456",
                "hash_abc123",
                "2024-02-01T12:00:00Z",
                "/payloads/new_event.json",
                "2024-02-01T12:00:01Z",
            ),
        )
        conn.commit()

        # Verify the new row
        cursor = conn.execute(
            "SELECT content_hash FROM events WHERE event_id = ?", ("new_event_456",)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "hash_abc123"
        conn.close()

    def test_tasks_table_created(self, tmp_path: Path) -> None:
        """Verify tasks table exists and is writable after migration."""
        db_path = tmp_path / "test_tasks.db"

        # Create with old schema
        conn = sqlite3.connect(str(db_path))
        conn.executescript(OLD_SCHEMA)
        conn.commit()
        conn.close()

        # Apply new schema
        conn = sqlite3.connect(str(db_path))
        conn.executescript(NEW_SCHEMA_ADDITIONS)
        conn.commit()

        # Verify tasks table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
        )
        row = cursor.fetchone()
        assert row is not None, "tasks table should be created"

        # Insert a task
        conn.execute(
            """
            INSERT INTO tasks
            (provider_id, task_id, conversation_id, created_at, status, priority)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "task_provider",
                "task_001",
                "conv_task_123",
                "2024-03-01T09:00:00Z",
                "pending",
                1,
            ),
        )
        conn.commit()

        # Verify task
        cursor = conn.execute("SELECT task_id, status, priority FROM tasks")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "task_001"
        assert row[1] == "pending"
        assert row[2] == 1
        conn.close()

    def test_event_log_table_created(self, tmp_path: Path) -> None:
        """Verify event_log table exists and is writable after migration."""
        db_path = tmp_path / "test_event_log.db"

        # Create with old schema
        conn = sqlite3.connect(str(db_path))
        conn.executescript(OLD_SCHEMA)
        conn.commit()
        conn.close()

        # Apply new schema
        conn = sqlite3.connect(str(db_path))
        conn.executescript(NEW_SCHEMA_ADDITIONS)
        conn.commit()

        # Verify event_log table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='event_log'"
        )
        row = cursor.fetchone()
        assert row is not None, "event_log table should be created"

        # Insert an event log entry
        conn.execute(
            """
            INSERT INTO event_log
            (provider_id, source_id, event_id, event_type, occurred_at, raw_payload_path, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "log_provider",
                "log_source",
                "log_event_789",
                "message",
                "2024-04-01T14:00:00Z",
                "/payloads/log_event.json",
                "2024-04-01T14:00:01Z",
            ),
        )
        conn.commit()

        # Verify log entry
        cursor = conn.execute("SELECT event_type FROM event_log WHERE event_id = ?", ("log_event_789",))
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "message"
        conn.close()

    def test_indexes_created(self, tmp_path: Path) -> None:
        """Verify indexes are created on events table after migration."""
        db_path = tmp_path / "test_indexes.db"

        # Create with old schema
        conn = sqlite3.connect(str(db_path))
        conn.executescript(OLD_SCHEMA)
        conn.commit()
        conn.close()

        # Apply new schema
        conn = sqlite3.connect(str(db_path))
        conn.executescript(NEW_SCHEMA_ADDITIONS)
        conn.commit()

        # Verify indexes exist
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='events'"
        )
        index_names = {row[0] for row in cursor.fetchall()}

        assert "idx_events_provider_id" in index_names, "idx_events_provider_id should be created"
        assert "idx_events_provider_occurred" in index_names, "idx_events_provider_occurred should be created"
        conn.close()

    def test_old_pk_format_still_usable(self, tmp_path: Path) -> None:
        """Verify we can still query using old PK fields after migration."""
        db_path = tmp_path / "test_old_pk.db"

        # Create with old schema and insert data
        conn = sqlite3.connect(str(db_path))
        conn.executescript(OLD_SCHEMA)
        conn.execute(
            """
            INSERT INTO events
            (provider_id, source_id, event_id, occurred_at, raw_payload_path, cached_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy",
                "legacy_src",
                "legacy_event",
                "2023-12-01T08:00:00Z",
                "/payloads/legacy.json",
                "2023-12-01T08:00:01Z",
            ),
        )
        conn.commit()
        conn.close()

        # Apply new schema
        conn = sqlite3.connect(str(db_path))
        conn.executescript(NEW_SCHEMA_ADDITIONS)
        conn.commit()

        # Query using old PK fields (provider_id, source_id, event_id)
        cursor = conn.execute(
            """
            SELECT provider_id, source_id, event_id
            FROM events
            WHERE provider_id = ? AND source_id = ? AND event_id = ?
            """,
            ("legacy", "legacy_src", "legacy_event"),
        )
        row = cursor.fetchone()
        assert row is not None, "Old PK query should still work"
        assert row[0] == "legacy"
        assert row[1] == "legacy_src"
        assert row[2] == "legacy_event"
        conn.close()
