"""TDD Tests for CHS v2 Indexer.

RED phase: Write failing tests first.
These tests define the expected behavior - implementation follows.

Test file: P:\\\\__csf/src/knowledge/systems/chs/v2/tests/test_indexer.py

Implementation target: P:\\\\__csf/src/knowledge/systems/chs/v2/indexer.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest

SAMPLE_JSONL_CONTENT = '{"timestamp": 1738838400, "role": "user", "content": "How do I fix the index.lock problem?", "message_id": "msg_001"}\n{"timestamp": 1738838401, "role": "assistant", "content": "You can use rm -f .git/index.lock", "message_id": "msg_002"}\n{"timestamp": 1738838402, "role": "user", "content": "What about concurrency?", "message_id": "msg_003"}\n{"timestamp": 1738838403, "role": "assistant", "content": "Implement a lock retry mechanism", "message_id": "msg_004"}\n{"timestamp": 1738838404, "role": "user", "content": "Thanks!", "message_id": "msg_005"}\n'
DUPLICATE_JSONL_CONTENT = '{"timestamp": 1738838400, "role": "user", "content": "How do I fix the index.lock problem?", "message_id": "msg_001"}\n{"timestamp": 1738838401, "role": "assistant", "content": "You can use rm -f .git/index.lock", "message_id": "msg_002"}\n{"timestamp": 1738838402, "role": "user", "content": "What about concurrency?", "message_id": "msg_003"}\n{"timestamp": 1738838403, "role": "assistant", "content": "Implement a lock retry mechanism", "message_id": "msg_004"}\n{"timestamp": 1738838404, "role": "user", "content": "Thanks!", "message_id": "msg_005"}\n'
TRAILING_MESSAGE_JSONL = '{"timestamp": 1738838400, "role": "user", "content": "First question", "message_id": "msg_001"}\n{"timestamp": 1738838401, "role": "assistant", "content": "First answer", "message_id": "msg_002"}\n{"timestamp": 1738838402, "role": "user", "content": "Second question (trailing)", "message_id": "msg_003"}\n'
SAMPLE_SCHEMA = "\n-- Chat History Search System Schema\n-- Version: 2.0\n\nPRAGMA journal_mode = WAL;\nPRAGMA foreign_keys = ON;\n\n-- Projects: one per repository/workspace root\nCREATE TABLE IF NOT EXISTS projects (\n    id INTEGER PRIMARY KEY,\n    path TEXT NOT NULL UNIQUE,\n    label TEXT,\n    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))\n);\n\n-- Sessions: logical conversation threads\nCREATE TABLE IF NOT EXISTS sessions (\n    id INTEGER PRIMARY KEY,\n    session_key TEXT NOT NULL,\n    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,\n    started_at INTEGER NOT NULL,\n    ended_at INTEGER,\n    is_closed INTEGER NOT NULL DEFAULT 0,\n    message_count INTEGER NOT NULL DEFAULT 0,\n    summary_short TEXT,\n    summary_long TEXT,\n    embedding BLOB,\n    embedding_model TEXT,\n    embedding_dim INTEGER,\n    last_turn_built_message_id INTEGER,\n    last_message_timestamp INTEGER,\n    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),\n    updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))\n);\n\nCREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_project_session_key\nON sessions(project_id, session_key);\n\n-- Messages: atomic conversation units\nCREATE TABLE IF NOT EXISTS messages (\n    id INTEGER PRIMARY KEY,\n    message_id TEXT NOT NULL UNIQUE,\n    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,\n    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,\n    timestamp INTEGER NOT NULL,\n    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'tool', 'system')),\n    content TEXT NOT NULL,\n    has_code INTEGER NOT NULL DEFAULT 0,\n    has_error INTEGER NOT NULL DEFAULT 0,\n    raw_json TEXT,\n    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))\n);\n\nCREATE INDEX IF NOT EXISTS idx_messages_session_time\nON messages(session_id, timestamp);\n\n-- Turns: conversational retrieval units\nCREATE TABLE IF NOT EXISTS turns (\n    id INTEGER PRIMARY KEY,\n    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,\n    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,\n    start_message_id INTEGER NOT NULL REFERENCES messages(id),\n    end_message_id INTEGER NOT NULL REFERENCES messages(id),\n    timestamp_start INTEGER NOT NULL,\n    timestamp_end INTEGER NOT NULL,\n    content TEXT NOT NULL,\n    has_code INTEGER NOT NULL DEFAULT 0,\n    has_error INTEGER NOT NULL DEFAULT 0,\n    length_chars INTEGER,\n    embedding BLOB,\n    embedding_model TEXT,\n    embedding_dim INTEGER,\n    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),\n    UNIQUE(session_id, start_message_id, end_message_id)\n);\n\nCREATE INDEX IF NOT EXISTS idx_turns_session_time\nON turns(session_id, timestamp_start);\n\n-- Checkpoint tracking for incremental indexing\nCREATE TABLE IF NOT EXISTS indexer_checkpoint (\n    file_identity TEXT PRIMARY KEY,\n    file_position INTEGER NOT NULL,\n    last_processed_at INTEGER NOT NULL,\n    updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))\n);\n"


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Create temporary SQLite database for testing."""
    db_path = tmp_path / "test_chs.db"
    return db_path


@pytest.fixture
def initialized_db(temp_db_path: Path) -> sqlite3.Connection:
    """Create and initialize database with schema."""
    conn = sqlite3.connect(temp_db_path)
    conn.executescript(SAMPLE_SCHEMA)
    conn.commit()
    return conn


@pytest.fixture
def temp_jsonl_file(tmp_path: Path) -> Path:
    """Create temporary JSONL file with sample content."""
    jsonl_path = tmp_path / "test_chat.jsonl"
    jsonl_path.write_text(SAMPLE_JSONL_CONTENT)
    return jsonl_path


@pytest.fixture
def temp_jsonl_with_trailing(tmp_path: Path) -> Path:
    """Create temporary JSONL file with trailing user message."""
    jsonl_path = tmp_path / "test_trailing.jsonl"
    jsonl_path.write_text(TRAILING_MESSAGE_JSONL)
    return jsonl_path


@pytest.fixture
def sample_project(temp_db_path: Path) -> dict:
    """Create a sample project in the database."""
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute(
        "INSERT INTO projects (path, label) VALUES (?, ?)", ("P:\\\\test_project", "Test Project")
    )
    project_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": project_id, "path": "P:\\\\test_project", "label": "Test Project"}


@pytest.fixture
def sample_session(temp_db_path: Path, sample_project: dict) -> dict:
    """Create a sample session in the database."""
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute(
        "INSERT INTO sessions (session_key, project_id, started_at)\n           VALUES (?, ?, ?)",
        ("test_session_001", sample_project["id"], 1738838400),
    )
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": session_id, "session_key": "test_session_001", "project_id": sample_project["id"]}


class TestChatIndexer:
    """Tests for ChatIndexer class."""

    def test_index_file_increments_file_position(
        self,
        initialized_db: sqlite3.Connection,
        temp_jsonl_file: Path,
        sample_project: dict,
        sample_session: dict,
    ) -> None:
        """
        Test that _index_file() increments file position after processing.

        Given: A JSONL file with 5 messages
        When: _index_file() processes the file
        Then: File position should advance to end of file
        """
        from core.chs.indexer import ChatIndexer

        indexer = ChatIndexer(conn=initialized_db)
        with patch.object(indexer, "_get_or_create_session", return_value=sample_session):
            with patch.object(indexer, "_ingest_message"):
                initial_pos = 0
                final_pos = indexer._index_file(
                    file_path=str(temp_jsonl_file),
                    project_id=sample_project["id"],
                    session_key="test_session_001",
                    start_position=initial_pos,
                )
                assert final_pos > initial_pos, "File position should increment"
                assert final_pos == temp_jsonl_file.stat().st_size, "Should reach end of file"

    def test_get_or_create_project_returns_existing(
        self, initialized_db: sqlite3.Connection, sample_project: dict
    ) -> None:
        """
        Test that _get_or_create_project() returns existing project.

        Given: A project already exists in database
        When: _get_or_create_project() is called with same path
        Then: Should return existing project ID, not create duplicate
        """
        from core.chs.indexer import ChatIndexer

        indexer = ChatIndexer(conn=initialized_db)
        project_id_1 = indexer._get_or_create_project(path=sample_project["path"])
        project_id_2 = indexer._get_or_create_project(path=sample_project["path"])
        assert project_id_1 == project_id_2, "Should return same project ID"
        assert project_id_1 == sample_project["id"], "Should match existing project"

    def test_get_or_create_session_returns_existing(
        self, initialized_db: sqlite3.Connection, sample_project: dict, sample_session: dict
    ) -> None:
        """
        Test that _get_or_create_session() returns existing session.

        Given: A session already exists in database
        When: _get_or_create_session() is called with same key
        Then: Should return existing session ID, not create duplicate
        """
        from core.chs.indexer import ChatIndexer

        indexer = ChatIndexer(conn=initialized_db)
        session_id_1 = indexer._get_or_create_session(
            project_id=sample_project["id"], session_key=sample_session["session_key"]
        )
        session_id_2 = indexer._get_or_create_session(
            project_id=sample_project["id"], session_key=sample_session["session_key"]
        )
        assert session_id_1 == session_id_2, "Should return same session ID"
        assert session_id_1 == sample_session["id"], "Should match existing session"

    def test_ingest_message_skips_duplicates(
        self, initialized_db: sqlite3.Connection, sample_project: dict, sample_session: dict
    ) -> None:
        """
        Test that _ingest_message() skips duplicate messages.

        Given: A message already exists in database
        When: _ingest_message() is called with same message_id
        Then: Should skip insertion, not create duplicate
        """
        from core.chs.indexer import ChatIndexer

        indexer = ChatIndexer(conn=initialized_db)
        message_data = {
            "message_id": "msg_001",
            "timestamp": 1738838400,
            "role": "user",
            "content": "Test message",
        }
        message_id_1 = indexer._ingest_message(
            session_id=sample_session["id"],
            project_id=sample_project["id"],
            message_data=message_data,
        )
        message_id_2 = indexer._ingest_message(
            session_id=sample_session["id"],
            project_id=sample_project["id"],
            message_data=message_data,
        )
        assert message_id_1 == message_id_2, "Should return same message ID for duplicate"
        conn = initialized_db
        cursor = conn.execute("SELECT COUNT(*) FROM messages WHERE message_id = ?", ("msg_001",))
        count = cursor.fetchone()[0]
        assert count == 1, "Should have exactly one message"

    def test_build_turns_creates_complete_turns(
        self,
        initialized_db: sqlite3.Connection,
        temp_jsonl_file: Path,
        sample_project: dict,
        sample_session: dict,
    ) -> None:
        """
        Test that _build_turns_for_session() creates complete turns.

        Given: A session with 5 messages (user, assistant, user, assistant, user)
        When: _build_turns_for_session() processes the session
        Then: Should create 2 complete turns (user+assistant pairs)
        """
        from core.chs.indexer import ChatIndexer

        indexer = ChatIndexer(conn=initialized_db)
        messages = [
            {"message_id": "msg_001", "timestamp": 1738838400, "role": "user", "content": "Q1"},
            {
                "message_id": "msg_002",
                "timestamp": 1738838401,
                "role": "assistant",
                "content": "A1",
            },
            {"message_id": "msg_003", "timestamp": 1738838402, "role": "user", "content": "Q2"},
            {
                "message_id": "msg_004",
                "timestamp": 1738838403,
                "role": "assistant",
                "content": "A2",
            },
            {"message_id": "msg_005", "timestamp": 1738838404, "role": "user", "content": "Q3"},
        ]
        for msg in messages:
            indexer._ingest_message(
                session_id=sample_session["id"], project_id=sample_project["id"], message_data=msg
            )
        turns_created = indexer._build_turns_for_session(
            session_id=sample_session["id"], project_id=sample_project["id"]
        )
        assert turns_created == 2, f"Should create 2 complete turns, got {turns_created}"
        conn = initialized_db
        cursor = conn.execute(
            "SELECT COUNT(*) FROM turns WHERE session_id = ?", (sample_session["id"],)
        )
        turn_count = cursor.fetchone()[0]
        assert turn_count == 2, f"Database should have 2 turns, got {turn_count}"

    def test_build_turns_handles_trailing_message(
        self,
        initialized_db: sqlite3.Connection,
        temp_jsonl_with_trailing: Path,
        sample_project: dict,
        sample_session: dict,
    ) -> None:
        """
        Test that _build_turns_for_session() handles trailing user message.

        Given: A session with 3 messages (user, assistant, user)
        When: _build_turns_for_session() processes the session
        Then: Should create 1 complete turn and track trailing message
        """
        from core.chs.indexer import ChatIndexer

        indexer = ChatIndexer(conn=initialized_db)
        messages = [
            {"message_id": "msg_001", "timestamp": 1738838400, "role": "user", "content": "Q1"},
            {
                "message_id": "msg_002",
                "timestamp": 1738838401,
                "role": "assistant",
                "content": "A1",
            },
            {
                "message_id": "msg_003",
                "timestamp": 1738838402,
                "role": "user",
                "content": "Q2 (trailing)",
            },
        ]
        for msg in messages:
            indexer._ingest_message(
                session_id=sample_session["id"], project_id=sample_project["id"], message_data=msg
            )
        turns_created = indexer._build_turns_for_session(
            session_id=sample_session["id"], project_id=sample_project["id"]
        )
        assert turns_created == 1, f"Should create 1 complete turn, got {turns_created}"
        conn = initialized_db
        cursor = conn.execute(
            "SELECT last_turn_built_message_id FROM sessions WHERE id = ?", (sample_session["id"],)
        )
        last_turn_msg_id = cursor.fetchone()[0]
        assert last_turn_msg_id is not None, "Should track last turn built"
        assert last_turn_msg_id > 0, "Should have valid message ID"

    def test_checkpoint_saved_after_turn_building(
        self,
        initialized_db: sqlite3.Connection,
        temp_jsonl_file: Path,
        sample_project: dict,
        sample_session: dict,
    ) -> None:
        """
        Test that checkpoint is saved after turn building.

        Given: A file is processed and turns are built
        When: Turn building completes
        Then: Checkpoint should be saved with file position
        """
        from core.chs.indexer import ChatIndexer

        indexer = ChatIndexer(conn=initialized_db)
        with patch.object(indexer, "_get_or_create_session", return_value=sample_session):
            with patch.object(indexer, "_ingest_message"):
                with patch.object(indexer, "_build_turns_for_session"):
                    indexer._index_file(
                        file_path=str(temp_jsonl_file),
                        project_id=sample_project["id"],
                        session_key="test_session_001",
                        start_position=0,
                    )
        conn = initialized_db
        cursor = conn.execute(
            "SELECT file_position FROM indexer_checkpoint WHERE file_identity = ?",
            (str(temp_jsonl_file),),
        )
        checkpoint_position = cursor.fetchone()
        assert checkpoint_position is not None, "Checkpoint should exist"
        assert checkpoint_position[0] > 0, "Checkpoint position should be positive"

    def test_indexer_resumes_from_checkpoint(
        self,
        initialized_db: sqlite3.Connection,
        temp_jsonl_file: Path,
        sample_project: dict,
        sample_session: dict,
    ) -> None:
        """
        Test that indexer resumes from checkpoint on restart.

        Given: A previous indexing run stopped at position 100
        When: Indexer runs again
        Then: Should resume from position 100, not start from 0
        """
        from core.chs.indexer import ChatIndexer

        indexer = ChatIndexer(conn=initialized_db)
        file_identity = str(temp_jsonl_file)
        checkpoint_position = 100
        conn = initialized_db
        conn.execute(
            "INSERT INTO indexer_checkpoint (file_identity, file_position, last_processed_at)\n               VALUES (?, ?, ?)",
            (file_identity, checkpoint_position, 1738838400),
        )
        conn.commit()
        cursor = conn.execute(
            "SELECT file_position FROM indexer_checkpoint WHERE file_identity = ?", (file_identity,)
        )
        resume_position = cursor.fetchone()[0]
        assert resume_position == checkpoint_position, "Should resume from checkpoint"
        with patch.object(indexer, "_get_or_create_session", return_value=sample_session):
            with patch.object(indexer, "_ingest_message"):
                final_position = indexer._index_file(
                    file_path=str(temp_jsonl_file),
                    project_id=sample_project["id"],
                    session_key="test_session_001",
                    start_position=resume_position,
                )
        assert final_position > checkpoint_position, "Should advance from checkpoint position"


class TestFailingIndexerBehavior:
    """Tests that verify actual expected behavior (will FAIL until implemented)."""

    def test_ingest_message_stores_content(
        self, initialized_db: sqlite3.Connection, sample_project: dict, sample_session: dict
    ) -> None:
        """
        After ingesting a message, it should be queryable in the database.

        This test WILL FAIL until _ingest_message is properly implemented.
        """
        from core.chs.indexer import ChatIndexer

        indexer = ChatIndexer(conn=initialized_db)
        message_data = {
            "message_id": "msg_test_001",
            "timestamp": 1738838400,
            "role": "user",
            "content": "This is test content that should be stored",
        }
        _ = indexer._ingest_message(
            session_id=sample_session["id"],
            project_id=sample_project["id"],
            message_data=message_data,
        )
        conn = initialized_db
        cursor = conn.execute(
            "SELECT content FROM messages WHERE message_id = ?", ("msg_test_001",)
        )
        result = cursor.fetchone()
        assert result is not None, "Message should be stored in database"
        assert result[0] == "This is test content that should be stored", "Content should match"

    def test_build_turns_combines_messages(
        self, initialized_db: sqlite3.Connection, sample_project: dict, sample_session: dict
    ) -> None:
        """
        After building turns, turn content should combine user and assistant messages.

        This test WILL FAIL until _build_turns_for_session is properly implemented.
        """
        from core.chs.indexer import ChatIndexer

        indexer = ChatIndexer(conn=initialized_db)
        messages = [
            {
                "message_id": "msg_q",
                "timestamp": 1738838400,
                "role": "user",
                "content": "What is Python?",
            },
            {
                "message_id": "msg_a",
                "timestamp": 1738838401,
                "role": "assistant",
                "content": "Python is a programming language.",
            },
        ]
        for msg in messages:
            indexer._ingest_message(
                session_id=sample_session["id"], project_id=sample_project["id"], message_data=msg
            )
        indexer._build_turns_for_session(
            session_id=sample_session["id"], project_id=sample_project["id"]
        )
        conn = initialized_db
        cursor = conn.execute(
            "SELECT content FROM turns WHERE session_id = ?", (sample_session["id"],)
        )
        result = cursor.fetchone()
        assert result is not None, "Turn should be created"
        assert "What is Python?" in result[0], "Turn should contain user message"
        assert (
            "Python is a programming language" in result[0]
        ), "Turn should contain assistant message"
