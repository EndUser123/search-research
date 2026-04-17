"""T11: Watermark cross-restart persistence — write_watermark → read_watermark → values match.

Verifies: Watermarks survive process restart and return identical values.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from core.chs.archive import write_watermark, read_watermark

DB_PATH = Path("P:/__csf/data/chat_history.db")


@pytest.fixture
def temp_archive_base(tmp_path):
    """Fixture providing a temporary archive base directory."""
    archive_dir = tmp_path / "chs_archive"
    archive_dir.mkdir()
    return archive_dir


class TestWatermarkPersistence:
    """T11: Watermark cross-restart persistence tests."""

    def test_write_then_read_returns_identical_watermark(self, temp_archive_base):
        """Watermark written can be read back with identical values."""
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            watermark = {
                "last_event_id": "evt_12345",
                "last_occurred_at": "2026-04-02T10:00:00+00:00",
                "terminal_id": "test_terminal",
            }

            write_watermark(
                provider_id="test_provider",
                source_id="test_source",
                terminal_id="test_terminal",
                watermark=watermark,
            )

            read_back = read_watermark(
                provider_id="test_provider",
                source_id="test_source",
                terminal_id="test_terminal",
            )

            assert read_back is not None, "Watermark should be readable after write"
            assert read_back["last_event_id"] == "evt_12345"
            assert read_back["last_occurred_at"] == "2026-04-02T10:00:00+00:00"
            assert read_back["terminal_id"] == "test_terminal"

    def test_read_nonexistent_watermark_returns_none(self, temp_archive_base):
        """read_watermark returns None when no watermark file exists."""
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            result = read_watermark(
                provider_id="nonexistent_provider",
                source_id="nonexistent_source",
                terminal_id="nonexistent_terminal",
            )
            assert result is None

    def test_multiple_watermarks_for_different_terminals(self, temp_archive_base):
        """Multiple terminals can have their own watermarks independently."""
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            wm_a = {
                "last_event_id": "evt_a",
                "last_occurred_at": "2026-04-02T10:00:00+00:00",
                "terminal_id": "terminal_a",
            }
            wm_b = {
                "last_event_id": "evt_b",
                "last_occurred_at": "2026-04-02T11:00:00+00:00",
                "terminal_id": "terminal_b",
            }

            write_watermark("provider", "source", "terminal_a", wm_a)
            write_watermark("provider", "source", "terminal_b", wm_b)

            read_a = read_watermark("provider", "source", "terminal_a")
            read_b = read_watermark("provider", "source", "terminal_b")

            assert read_a["last_event_id"] == "evt_a"
            assert read_b["last_event_id"] == "evt_b"
            assert read_a["terminal_id"] == "terminal_a"
            assert read_b["terminal_id"] == "terminal_b"

    def test_watermark_overwrite_updates_correctly(self, temp_archive_base):
        """Writing a new watermark replaces the previous one for same terminal."""
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            wm_v1 = {
                "last_event_id": "evt_v1",
                "last_occurred_at": "2026-04-02T10:00:00+00:00",
                "terminal_id": "same_terminal",
            }
            wm_v2 = {
                "last_event_id": "evt_v2",
                "last_occurred_at": "2026-04-02T12:00:00+00:00",
                "terminal_id": "same_terminal",
            }

            write_watermark("provider", "source", "same_terminal", wm_v1)
            write_watermark("provider", "source", "same_terminal", wm_v2)

            read_back = read_watermark("provider", "source", "same_terminal")
            assert read_back["last_event_id"] == "evt_v2"
            assert read_back["last_occurred_at"] == "2026-04-02T12:00:00+00:00"
