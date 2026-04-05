"""Tests for quarantine and safer cleanup workflow."""

import sqlite3

import pytest

from yt_fts.db.quarantine import QuarantineSystem


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database with test data."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create channels table
    cursor.execute("""
        CREATE TABLE channels (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT,
            channel_url TEXT,
            api_total_video_count INTEGER,
            api_total_last_checked TEXT
        )
    """)

    # Insert test data
    test_data = [
        ("UCuE6iwZKgGz8s6kznBRI9LQ", "Good Channel 1", "https://www.youtube.com/@good1", 10, "2024-01-01"),
        ("UCBa659QWEk1AI4Tg--mrJ2A", "Good Channel 2", "https://www.youtube.com/@good2", 20, "2024-01-02"),
        ("@suspicious1", "Suspicious Channel", "https://www.youtube.com/@suspicious1", 0, None),
        ("https://www.youtube.com/@bad", "Bad Channel", "https://www.youtube.com/@bad", 0, None),
    ]

    cursor.executemany("INSERT INTO channels VALUES (?, ?, ?, ?, ?)", test_data)
    conn.commit()
    conn.close()

    return db_path


def test_quarantine_tables_created(temp_db):
    """Test that quarantine system creates required tables."""
    qs = QuarantineSystem(str(temp_db))

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Check channels_quarantine table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='channels_quarantine'
    """)
    assert cursor.fetchone() is not None

    # Check deletion_log table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='deletion_log'
    """)
    assert cursor.fetchone() is not None

    conn.close()


def test_quarantine_entry(temp_db):
    """Test quarantining a channel entry."""
    qs = QuarantineSystem(str(temp_db))

    # Quarantine a suspicious entry
    qs.quarantine_channel("@suspicious1", reason="Short channel_id")

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Check it's in quarantine
    cursor.execute("SELECT channel_id, reason FROM channels_quarantine WHERE channel_id = ?", ("@suspicious1",))
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == "Short channel_id"

    # Check it's removed from main table
    cursor.execute("SELECT channel_id FROM channels WHERE channel_id = ?", ("@suspicious1",))
    assert cursor.fetchone() is None

    conn.close()


def test_log_deletion(temp_db):
    """Test that deletions are logged."""
    qs = QuarantineSystem(str(temp_db))

    # Quarantine with logging
    qs.quarantine_channel("@suspicious1", reason="Test", quarantined_by="test_script")

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Check log entry
    cursor.execute("""
        SELECT channel_id, reason, deleted_by 
        FROM deletion_log 
        WHERE channel_id = ?
    """, ("@suspicious1",))
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "@suspicious1"
    assert row[1] == "Test"
    assert row[2] == "test_script"

    conn.close()


def test_list_quarantined(temp_db):
    """Test listing quarantined entries."""
    qs = QuarantineSystem(str(temp_db))

    # Quarantine two entries
    qs.quarantine_channel("@suspicious1", reason="Reason 1")
    qs.quarantine_channel("https://www.youtube.com/@bad", reason="Reason 2")

    # List them
    entries = qs.list_quarantined()

    assert len(entries) == 2
    channel_ids = [e["channel_id"] for e in entries]
    assert "@suspicious1" in channel_ids
    assert "https://www.youtube.com/@bad" in channel_ids


def test_restore_from_quarantine(temp_db):
    """Test restoring a quarantined entry."""
    qs = QuarantineSystem(str(temp_db))

    # Quarantine then restore
    qs.quarantine_channel("@suspicious1", reason="Test")
    restored = qs.restore_channel("@suspicious1")

    assert restored is True

    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # Check it's back in main table
    cursor.execute("SELECT channel_id FROM channels WHERE channel_id = ?", ("@suspicious1",))
    assert cursor.fetchone() is not None

    # Check it's removed from quarantine
    cursor.execute("SELECT channel_id FROM channels_quarantine WHERE channel_id = ?", ("@suspicious1",))
    assert cursor.fetchone() is None

    conn.close()


def test_permanent_delete_requires_confirmation(temp_db):
    """Test that permanent delete requires explicit confirmation."""
    qs = QuarantineSystem(str(temp_db))

    # Quarantine first
    qs.quarantine_channel("@suspicious1", reason="Test")

    # Try to delete without confirmation - should fail
    deleted = qs.permanent_delete("@suspicious1", confirmed=False)
    assert deleted is False

    # Delete with confirmation - should succeed
    deleted = qs.permanent_delete("@suspicious1", confirmed=True)
    assert deleted is True


def test_get_deletion_stats(temp_db):
    """Test getting deletion statistics."""
    qs = QuarantineSystem(str(temp_db))

    # Quarantine some entries
    qs.quarantine_channel("@suspicious1", reason="Reason 1")
    qs.quarantine_channel("https://www.youtube.com/@bad", reason="Reason 2")

    stats = qs.get_stats()

    assert stats["quarantined_count"] == 2
    assert stats["main_table_count"] == 2  # Two good channels remain
