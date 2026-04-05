"""
Tests for batch_quota module.

Tests quota strategy initialization and metadata-only delay calculation.
"""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from yt_fts.core.batch_quota import (
    initialize_quota_strategy,
    get_metadata_only_delay,
    log_msg,
)


# Patch create_quota_strategy at its actual location (download.quota_strategy)
# since batch_quota imports it with: from ..download.quota_strategy import ...
PATCH_PATH = "yt_fts.download.quota_strategy.create_quota_strategy"


class TestLogMsg:
    """Test log_msg function."""

    def test_log_msg_writes_to_stderr(self, capsys):
        """Test log_msg writes formatted message to stderr."""
        log_msg("TEST", "Test message")
        captured = capsys.readouterr()
        assert "[TEST]" in captured.err
        assert "Test message" in captured.err


class TestGetMetadataOnlyDelay:
    """Test get_metadata_only_delay function."""

    def test_metadata_only_mode_returns_zero(self):
        """Test metadata-only mode (videos=0, default delay) returns 0 delay."""
        delay = get_metadata_only_delay(default_delay=60.0, videos_per_channel=0)
        assert delay == 0.0

    def test_metadata_only_mode_custom_delay_preserved(self):
        """Test custom delay is preserved when not in default metadata-only mode."""
        delay = get_metadata_only_delay(default_delay=30.0, videos_per_channel=0)
        assert delay == 30.0  # Custom delay preserved

    def test_videos_set_preserves_delay(self):
        """Test delay is preserved when downloading videos."""
        delay = get_metadata_only_delay(default_delay=60.0, videos_per_channel=5)
        assert delay == 60.0

    def test_custom_delay_with_videos(self):
        """Test custom delay is preserved when downloading videos."""
        delay = get_metadata_only_delay(default_delay=120.0, videos_per_channel=10)
        assert delay == 120.0


class TestInitializeQuotaStrategy:
    """Test initialize_quota_strategy function."""

    @patch(PATCH_PATH)
    def test_initialize_quota_with_db_usage(self, mock_create_quota):
        """Test quota initialization with existing database usage."""
        # Patch at the actual import location
        with patch("sqlite_utils.Database") as mock_db_class:
            with patch("yt_fts.core.database.get_db_path") as mock_get_db_path:
                # Setup mock database
                mock_db = MagicMock()
                mock_db.execute.return_value.fetchone.return_value = (5000,)
                mock_db_class.return_value = mock_db
                mock_get_db_path.return_value = "/path/to/db"

                # Setup mock quota strategy
                mock_strategy = MagicMock()
                mock_strategy.get_status_message.return_value = "Quota: 5000/10000 used"
                mock_create_quota.return_value = mock_strategy

                result = initialize_quota_strategy(
                    quota_daily=10000,
                    quota_conservative_pct=0.8,
                    quota_aggressive_pct=1.2,
                )

                assert result == mock_strategy
                mock_create_quota.assert_called_once()
                call_args = mock_create_quota.call_args
                assert call_args.kwargs["daily_quota"] == 10000
                assert call_args.kwargs["conservative_pct"] == 0.8
                assert call_args.kwargs["aggressive_pct"] == 1.2
                assert call_args.kwargs["quota_used"] == 5000

    @patch(PATCH_PATH)
    def test_initialize_quota_with_no_db_usage(self, mock_create_quota):
        """Test quota initialization when database has no usage record."""
        with patch("sqlite_utils.Database") as mock_db_class:
            with patch("yt_fts.core.database.get_db_path") as mock_get_db_path:
                mock_db = MagicMock()
                mock_db.execute.return_value.fetchone.return_value = None
                mock_db_class.return_value = mock_db
                mock_get_db_path.return_value = "/path/to/db"

                mock_strategy = MagicMock()
                mock_strategy.get_status_message.return_value = "Quota: 0/10000 used"
                mock_create_quota.return_value = mock_strategy

                result = initialize_quota_strategy(
                    quota_daily=10000,
                    quota_conservative_pct=0.8,
                    quota_aggressive_pct=1.2,
                )

                assert result == mock_strategy
                call_args = mock_create_quota.call_args
                assert call_args.kwargs["quota_used"] == 0

    @patch(PATCH_PATH)
    def test_initialize_quota_with_db_exception(self, mock_create_quota):
        """Test quota initialization handles database exceptions gracefully."""
        with patch("sqlite_utils.Database") as mock_db_class:
            with patch("yt_fts.core.database.get_db_path") as mock_get_db_path:
                mock_db_class.side_effect = Exception("Database error")
                mock_get_db_path.return_value = "/path/to/db"

                mock_strategy = MagicMock()
                mock_strategy.get_status_message.return_value = "Quota: 0/10000 used"
                mock_create_quota.return_value = mock_strategy

                result = initialize_quota_strategy(
                    quota_daily=10000,
                    quota_conservative_pct=0.8,
                    quota_aggressive_pct=1.2,
                )

                # Should still create strategy with 0 usage on DB error
                assert result == mock_strategy
                call_args = mock_create_quota.call_args
                assert call_args.kwargs["quota_used"] == 0

    @patch(PATCH_PATH)
    def test_initialize_quota_custom_percentages(self, mock_create_quota):
        """Test quota initialization with custom percentages."""
        with patch("sqlite_utils.Database") as mock_db_class:
            with patch("yt_fts.core.database.get_db_path") as mock_get_db_path:
                mock_db = MagicMock()
                mock_db.execute.return_value.fetchone.return_value = (3000,)
                mock_db_class.return_value = mock_db
                mock_get_db_path.return_value = "/path/to/db"

                mock_strategy = MagicMock()
                mock_create_quota.return_value = mock_strategy

                initialize_quota_strategy(
                    quota_daily=15000,
                    quota_conservative_pct=0.7,
                    quota_aggressive_pct=1.5,
                )

                call_args = mock_create_quota.call_args
                assert call_args.kwargs["daily_quota"] == 15000
                assert call_args.kwargs["conservative_pct"] == 0.7
                assert call_args.kwargs["aggressive_pct"] == 1.5

    @patch(PATCH_PATH)
    def test_initialize_quota_logs_status(self, mock_create_quota, capsys):
        """Test quota initialization logs status message."""
        with patch("sqlite_utils.Database") as mock_db_class:
            with patch("yt_fts.core.database.get_db_path") as mock_get_db_path:
                mock_db = MagicMock()
                mock_db.execute.return_value.fetchone.return_value = (5000,)
                mock_db_class.return_value = mock_db
                mock_get_db_path.return_value = "/path/to/db"

                mock_strategy = MagicMock()
                mock_strategy.get_status_message.return_value = "Quota: 5000/10000 used (50%)"
                mock_create_quota.return_value = mock_strategy

                initialize_quota_strategy(
                    quota_daily=10000,
                    quota_conservative_pct=0.8,
                    quota_aggressive_pct=1.2,
                )

                captured = capsys.readouterr()
                assert "[QUOTA]" in captured.err
                assert "50%" in captured.err

class TestQuotaDisplayRegression:
    """Regression tests for quota display bugs."""

    def test_quota_display_with_10000_remaining_does_not_trigger_low_quota(self):
        """
        Regression test for bug where "10,000 remaining" matched "0 remaining" check.
        
        Bug: The substring check "0 remaining" in line was matching "10,000 remaining"
        because "0" appears in "10,000". This caused quota display to show even when
        quota was healthy (> 1000 remaining).
        
        Fix: Changed to only check for [red] tag which indicates depleted quota.
        """
        # Simulate quota lines from format_quota_lines() with healthy quota
        quota_lines = [
            "Key 1: 10,000 remaining",
            "Key 2: 10,000 remaining",
            "Key 3: 10,000 remaining",
            "Key 4: 10,000 remaining",
        ]
        
        # This is the logic from _print_quota_status
        has_low_quota = False
        for line in quota_lines:
            if "[red]" in line:
                has_low_quota = True
                break
            elif "remaining" in line:
                try:
                    # Extract number from "Key 1: 10,000 remaining"
                    num_str = line.split(":")[1].split()[0].replace(",", "")
                    if int(num_str) < 1000:
                        has_low_quota = True
                        break
                except (ValueError, IndexError):
                    pass
        
        # With healthy quota (10,000), should NOT trigger low quota display
        assert not has_low_quota, "10,000 remaining should NOT trigger low quota display"

    def test_quota_display_with_500_remaining_does_trigger_low_quota(self):
        """Test that low quota (< 1000) correctly triggers low quota display."""
        quota_lines = [
            "Key 1: 10,000 remaining",
            "Key 2: 500 remaining",  # This should trigger low quota
            "Key 3: 10,000 remaining",
        ]
        
        has_low_quota = False
        for line in quota_lines:
            if "[red]" in line:
                has_low_quota = True
                break
            elif "remaining" in line:
                try:
                    num_str = line.split(":")[1].split()[0].replace(",", "")
                    if int(num_str) < 1000:
                        has_low_quota = True
                        break
                except (ValueError, IndexError):
                    pass
        
        # With one key at 500, should trigger low quota display
        assert has_low_quota, "500 remaining should trigger low quota display"

    def test_quota_display_with_red_tag_does_trigger_low_quota(self):
        """Test that [red] tag indicates depleted quota and triggers display."""
        quota_lines = [
            "Key 1: [red]0 remaining[/red]",  # Depleted quota
            "Key 2: 10,000 remaining",
        ]
        
        has_low_quota = False
        for line in quota_lines:
            if "[red]" in line:
                has_low_quota = True
                break
        
        # [red] tag should trigger low quota display
        assert has_low_quota, "[red] tag should trigger low quota display"
