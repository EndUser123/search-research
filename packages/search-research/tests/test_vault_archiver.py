"""Tests for vault_archiver module."""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from core.vault_archiver import VaultArchiver


@pytest.fixture
def temp_vault_db():
    """Create a temporary vault database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "vault.db"
        yield str(db_path)


@pytest.fixture
def temp_sessions_dir():
    """Create a temporary sessions directory with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sessions_dir = Path(tmpdir) / "sessions"
        sessions_dir.mkdir()

        # Create a test session
        session_dir = sessions_dir / "test-session-123"
        session_dir.mkdir()

        # Create transcript file
        transcript_file = session_dir / "transcript.jsonl"
        messages = [
            {"type": "user", "content": "Hello", "timestamp": datetime.utcnow().isoformat()},
            {
                "type": "assistant",
                "content": "Hi there!",
                "timestamp": datetime.utcnow().isoformat(),
            },
        ]

        with open(transcript_file, "w") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        yield sessions_dir


def test_archiver_initialization(temp_vault_db):
    """Test VaultArchiver initialization."""
    archiver = VaultArchiver(db_path=temp_vault_db)
    assert archiver.db_path == Path(temp_vault_db)


def test_schema_creation(temp_vault_db):
    """Test that schema is created correctly."""
    archiver = VaultArchiver(db_path=temp_vault_db)

    with sqlite3.connect(str(archiver.db_path)) as conn:
        archiver._ensure_schema(conn)

        cursor = conn.cursor()

        # Check sessions table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
        )
        assert cursor.fetchone() is not None

        # Check messages table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
        )
        assert cursor.fetchone() is not None


def test_archive_single_session(temp_vault_db, temp_sessions_dir):
    """Test archiving a single session."""
    archiver = VaultArchiver(db_path=temp_vault_db)

    transcript_path = temp_sessions_dir / "test-session-123" / "transcript.jsonl"
    result = archiver.archive_session(
        session_id="test-session-123",
        transcript_path=transcript_path,
        project="test-project",
        title="Test Session",
    )

    assert result is True

    # Verify data in database
    with sqlite3.connect(str(archiver.db_path)) as conn:
        cursor = conn.cursor()

        # Check session was inserted
        cursor.execute(
            "SELECT * FROM sessions WHERE session_id = ?",
            ("test-session-123",),
        )
        session = cursor.fetchone()
        assert session is not None

        # Check messages were inserted
        cursor.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = ?",
            ("test-session-123",),
        )
        count = cursor.fetchone()[0]
        assert count == 2  # Two messages in test data


def test_archive_nonexistent_transcript(temp_vault_db):
    """Test that archiving non-existent transcript returns False."""
    archiver = VaultArchiver(db_path=temp_vault_db)

    result = archiver.archive_session(
        session_id="fake-session",
        transcript_path=Path("/nonexistent/transcript.jsonl"),
    )

    assert result is False


def test_archive_duplicate_session(temp_vault_db, temp_sessions_dir):
    """Test that archiving same session twice returns False on second attempt."""
    archiver = VaultArchiver(db_path=temp_vault_db)

    transcript_path = temp_sessions_dir / "test-session-123" / "transcript.jsonl"

    # First archive should succeed
    result1 = archiver.archive_session(
        session_id="test-session-123",
        transcript_path=transcript_path,
    )
    assert result1 is True

    # Second archive should fail (already exists)
    result2 = archiver.archive_session(
        session_id="test-session-123",
        transcript_path=transcript_path,
    )
    assert result2 is False


def test_read_session_transcript(temp_sessions_dir):
    """Test reading session transcript from JSONL."""
    archiver = VaultArchiver()

    transcript_path = temp_sessions_dir / "test-session-123" / "transcript.jsonl"
    messages = archiver._read_session_transcript(transcript_path)

    assert messages is not None
    assert len(messages) == 2
    assert messages[0]["content"] == "Hello"
    assert messages[1]["content"] == "Hi there!"
