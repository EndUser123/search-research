"""Tests for channel data repair utility."""

import sqlite3

import pytest

from yt_fts.db.repair import ChannelRepairer


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

    # Insert test data with various malformations
    # Real YouTube channel IDs are 24 characters starting with UC
    test_data = [
        # Malformed: @ prefix in channel_id (realistic UC ID)
        ("@UCuE6iwZKgGz8s6kznBRI9LQ", "Test Channel 1", "https://www.youtube.com/@UCuE6iwZKgGz8s6kznBRI9LQ", 10, "2024-01-01"),
        # Malformed: URL stored as channel_id (realistic UC ID)
        ("https://www.youtube.com/@UCBa659QWEk1AI4Tg--mrJ2A", "Test Channel 2", "https://www.youtube.com/@UCBa659QWEk1AI4Tg--mrJ2A", 20, "2024-01-02"),
        # Valid entry (realistic UC ID)
        ("UCYO_jab_esuFRV4b17AJtAw", "Good Channel", "https://www.youtube.com/@UCYO_jab_esuFRV4b17AJtAw", 30, "2024-01-03"),
        # Malformed: @handle in channel_id field (too short to be UC ID)
        ("@testchannel", "Test Channel 3", "https://www.youtube.com/@testchannel", 0, None),
    ]

    cursor.executemany(
        "INSERT INTO channels VALUES (?, ?, ?, ?, ?)",
        test_data
    )

    conn.commit()
    conn.close()

    return db_path


def test_extract_channel_id_from_url():
    """Test extracting channel_id from various URL formats."""
    repairer = ChannelRepairer(":memory:")

    # Real YouTube channel IDs are 24 characters starting with UC
    test_cases = [
        ("https://www.youtube.com/@UCuE6iwZKgGz8s6kznBRI9LQ", "UCuE6iwZKgGz8s6kznBRI9LQ"),
        ("https://www.youtube.com/channel/UCBa659QWEk1AI4Tg--mrJ2A", "UCBa659QWEk1AI4Tg--mrJ2A"),
        ("https://www.youtube.com/c/UCYO_jab_esuFRV4b17AJtAw", "UCYO_jab_esuFRV4b17AJtAw"),
        ("https://youtu.be/UCXR7Xkq8s2m6x7jJn5L0kQ", "UCXR7Xkq8s2m6x7jJn5L0kQ"),
        # Already valid channel_id (24 chars)
        ("UCuE6iwZKgGz8s6kznBRI9LQ", "UCuE6iwZKgGz8s6kznBRI9LQ"),
        # @ prefix removal
        ("@UCuE6iwZKgGz8s6kznBRI9LQ", "UCuE6iwZKgGz8s6kznBRI9LQ"),
        # Handle that's too short - shouldn't extract
        ("@short", None),
        # URL with short ID - shouldn't extract
        ("https://www.youtube.com/@short", None),
    ]

    for url, expected in test_cases:
        result = repairer._extract_channel_id(url)
        assert result == expected, f"Failed for {url}: got {result}, expected {expected}"


def test_detect_malformed_entries(temp_db):
    """Test detection of malformed channel entries."""
    repairer = ChannelRepairer(str(temp_db))

    # Should detect 3 malformed entries
    malformed = repairer.detect_malformed()

    assert len(malformed) == 3
    channel_ids = [m["channel_id"] for m in malformed]
    assert "@UCuE6iwZKgGz8s6kznBRI9LQ" in channel_ids
    assert "https://www.youtube.com/@UCBa659QWEk1AI4Tg--mrJ2A" in channel_ids
    assert "@testchannel" in channel_ids


def test_repair_malformed_entry_dry_run(temp_db):
    """Test dry-run mode doesn't modify data."""
    repairer = ChannelRepairer(str(temp_db))

    # Count before
    conn = sqlite3.connect(temp_db)
    before = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
    conn.close()

    # Repair in dry-run mode
    repaired = repairer.repair_all(dry_run=True)

    # Count after (should be same)
    conn = sqlite3.connect(temp_db)
    after = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
    conn.close()

    assert before == after
    assert len(repaired) == 2  # Found 2 to repair (not @testchannel)


def test_repair_malformed_entry_actual(temp_db):
    """Test actual repair modifies data correctly."""
    repairer = ChannelRepairer(str(temp_db))

    # Repair the entries
    repaired = repairer.repair_all(dry_run=False)

    # Verify repairs
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    # @UCuE6iwZKgGz8s6kznBRI9LQ should become UCuE6iwZKgGz8s6kznBRI9LQ
    cursor.execute("SELECT channel_id FROM channels WHERE channel_id = ?", ("UCuE6iwZKgGz8s6kznBRI9LQ",))
    assert cursor.fetchone() is not None

    # URL should be extracted to UCBa659QWEk1AI4Tg--mrJ2A
    cursor.execute("SELECT channel_id FROM channels WHERE channel_id = ?", ("UCBa659QWEk1AI4Tg--mrJ2A",))
    assert cursor.fetchone() is not None

    # @testchannel should remain (can't be fixed)
    cursor.execute("SELECT channel_id FROM channels WHERE channel_id = ?", ("@testchannel",))
    assert cursor.fetchone() is not None

    conn.close()

    assert len(repaired) == 2  # Only 2 could be fixed


def test_repair_log(temp_db, tmp_path):
    """Test that repair operations are logged."""
    log_path = tmp_path / "repair.log"
    repairer = ChannelRepairer(str(temp_db), log_path=str(log_path))

    repairer.repair_all(dry_run=False)

    # Check log file exists and has content
    assert log_path.exists()
    log_content = log_path.read_text()
    assert "UCuE6iwZKgGz8s6kznBRI9LQ" in log_content or "UCBa659QWEk1AI4Tg--mrJ2A" in log_content


def test_preserves_valid_entries(temp_db):
    """Test that valid entries are not modified."""
    repairer = ChannelRepairer(str(temp_db))

    # Get the valid entry before repair
    conn = sqlite3.connect(temp_db)
    before = conn.execute(
        "SELECT * FROM channels WHERE channel_id = ?",
        ("UCYO_jab_esuFRV4b17AJtAw",)
    ).fetchone()
    conn.close()

    # Repair
    repairer.repair_all(dry_run=False)

    # Check it's unchanged
    conn = sqlite3.connect(temp_db)
    after = conn.execute(
        "SELECT * FROM channels WHERE channel_id = ?",
        ("UCYO_jab_esuFRV4b17AJtAw",)
    ).fetchone()
    conn.close()

    assert before == after
