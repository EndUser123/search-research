"""
Comprehensive unit tests for the Database Inconsistency Logging and Auto-Repair System.

Tests cover:
- InconsistencyLogger: logging, statistics, repair tracking
- AutoRepairManager: gap repair, count mismatch repair
- BatchDownloader: enhanced inconsistency detection
- Integration tests: end-to-end workflow
"""

import json
import sqlite3
import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from yt_fts.core.inconsistency_logger import AutoRepairManager, InconsistencyLogger


class TestInconsistencyLogger:
    """Test cases for InconsistencyLogger functionality."""

    def setup_method(self):
        """Set up test database for each test."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.logger = InconsistencyLogger(self.db_path)

    def teardown_method(self):
        """Clean up test database."""
        import os

        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_initialization_creates_tables(self):
        """Test that initialization creates required database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check db_inconsistencies table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='db_inconsistencies'"
        )
        assert cursor.fetchone() is not None

        # Check inconsistency_summary table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='inconsistency_summary'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    def test_log_inconsistency_success(self):
        """Test successful inconsistency logging."""
        channel_id = "UC123456789"
        channel_name = "Test Channel"
        inconsistency_type = "video_gap"
        severity = "high"
        details = "5 videos unaccounted for"
        stats = {"total": 100, "with_subs": 95}

        inconsistency_id = self.logger.log_inconsistency(
            channel_id=channel_id,
            channel_name=channel_name,
            inconsistency_type=inconsistency_type,
            severity=severity,
            details=details,
            stats=stats,
        )

        assert isinstance(inconsistency_id, int)
        assert inconsistency_id > 0

        # Verify data was stored
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM db_inconsistencies WHERE id = ?", (inconsistency_id,)
        )
        row = cursor.fetchone()

        assert row[1] == channel_id  # channel_id
        assert row[2] == channel_name  # channel_name
        assert row[3] == inconsistency_type  # inconsistency_type
        assert row[4] == severity  # severity
        assert row[5] == details  # details
        assert json.loads(row[6]) == stats  # stats_before

        conn.close()

    def test_log_inconsistency_with_none_values(self):
        """Test logging inconsistency with None channel name."""
        inconsistency_id = self.logger.log_inconsistency(
            channel_id="UC123",
            channel_name=None,
            inconsistency_type="count_mismatch",
            severity="medium",
            details="Minor count issue",
            stats={"total": 50},
        )

        assert isinstance(inconsistency_id, int)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT channel_name FROM db_inconsistencies WHERE id = ?",
            (inconsistency_id,),
        )
        row = cursor.fetchone()
        assert row[0] is None
        conn.close()

    def test_log_inconsistency_updates_summary(self):
        """Test that logging inconsistencies updates daily summary."""
        today = datetime.now().strftime("%Y-%m-%d")

        # Log first inconsistency
        self.logger.log_inconsistency(
            channel_id="UC1",
            channel_name="Channel 1",
            inconsistency_type="gap",
            severity="high",
            details="Test",
            stats={},
        )

        # Log second inconsistency
        self.logger.log_inconsistency(
            channel_id="UC2",
            channel_name="Channel 2",
            inconsistency_type="gap",
            severity="high",
            details="Test",
            stats={},
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT total_detected FROM inconsistency_summary WHERE date = ?", (today,)
        )
        row = cursor.fetchone()
        assert row[0] == 2
        conn.close()

    def test_log_repair_attempt_success(self):
        """Test logging successful repair attempt."""
        # First log an inconsistency
        inconsistency_id = self.logger.log_inconsistency(
            channel_id="UC123",
            channel_name="Test Channel",
            inconsistency_type="gap",
            severity="high",
            details="Gap detected",
            stats={"total": 100},
        )

        # Log successful repair
        self.logger.log_repair_attempt(
            inconsistency_id=inconsistency_id,
            repair_action="Fetched missing videos via API",
            success=True,
            notes="Added 5 missing videos",
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT auto_repaired, repair_action, resolved_at, notes FROM db_inconsistencies WHERE id = ?",
            (inconsistency_id,),
        )
        row = cursor.fetchone()

        assert row[0] == 1  # auto_repaired = True
        assert row[1] == "Fetched missing videos via API"
        assert row[2] is not None  # resolved_at set
        assert row[3] == "Added 5 missing videos"

        # Check summary was updated
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT auto_repaired FROM inconsistency_summary WHERE date = ?", (today,)
        )
        summary_row = cursor.fetchone()
        assert summary_row[0] == 1

        conn.close()

    def test_log_repair_attempt_failure(self):
        """Test logging failed repair attempt."""
        inconsistency_id = self.logger.log_inconsistency(
            channel_id="UC123",
            channel_name="Test Channel",
            inconsistency_type="gap",
            severity="high",
            details="Gap detected",
            stats={"total": 100},
        )

        self.logger.log_repair_attempt(
            inconsistency_id=inconsistency_id,
            repair_action="API call failed",
            success=False,
            notes="Rate limit exceeded",
        )

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT auto_repaired, repair_action, resolved_at, notes FROM db_inconsistencies WHERE id = ?",
            (inconsistency_id,),
        )
        row = cursor.fetchone()

        assert row[0] == 0  # auto_repaired = False
        assert row[1] == "FAILED: API call failed"
        assert row[2] is None  # resolved_at not set
        assert row[3] == "Rate limit exceeded"

        conn.close()

    def test_get_inconsistency_stats(self):
        """Test retrieving inconsistency statistics."""
        # Create some test data
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")

        # Insert test data directly
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Yesterday's data
        cursor.execute(
            """
            INSERT INTO inconsistency_summary (date, total_detected, auto_repaired, unresolved)
            VALUES (?, 5, 3, 2)
        """,
            (yesterday,),
        )

        # Today's data
        cursor.execute(
            """
            INSERT INTO inconsistency_summary (date, total_detected, auto_repaired, unresolved)
            VALUES (?, 8, 5, 3)
        """,
            (today,),
        )

        # Insert some inconsistencies with severity levels
        cursor.execute(
            """
            INSERT INTO db_inconsistencies
            (channel_id, inconsistency_type, severity, detected_at, auto_repaired)
            VALUES
            (?, ?, ?, ?, ?),
            (?, ?, ?, ?, ?),
            (?, ?, ?, ?, ?)
        """,
            [
                ("UC1", "gap", "critical", datetime.now().isoformat(), 1),
                ("UC2", "gap", "high", datetime.now().isoformat(), 0),
                ("UC3", "count", "high", datetime.now().isoformat(), 1),
                ("UC4", "count", "medium", datetime.now().isoformat(), 0),
            ],
        )

        conn.commit()
        conn.close()

        # Test stats for last 30 days (should include today)
        stats = self.logger.get_inconsistency_stats(days=30)

        assert stats["total_inconsistencies"] == 4
        assert stats["auto_repaired"] == 2
        assert stats["manually_resolved"] == 0  # No resolved_at set
        assert stats["critical_issues"] == 1
        assert stats["high_priority"] == 2
        assert stats["period_days"] == 30

    def test_get_unresolved_inconsistencies(self):
        """Test retrieving unresolved inconsistencies."""
        # Insert test data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO db_inconsistencies
            (channel_id, channel_name, inconsistency_type, severity, details, stats_before)
            VALUES
            (?, ?, ?, ?, ?, ?),
            (?, ?, ?, ?, ?, ?)
        """,
            [
                ("UC1", "Channel 1", "gap", "high", "Gap detected", '{"total": 100}'),
                (
                    "UC2",
                    "Channel 2",
                    "count",
                    "medium",
                    "Count mismatch",
                    '{"total": 50}',
                ),
            ],
        )

        conn.commit()
        conn.close()

        unresolved = self.logger.get_unresolved_inconsistencies()

        assert len(unresolved) == 2
        assert unresolved[0]["channel_id"] == "UC1"
        assert unresolved[0]["type"] == "gap"
        assert unresolved[0]["severity"] == "high"
        assert unresolved[0]["stats"]["total"] == 100
        assert unresolved[1]["channel_id"] == "UC2"


class TestAutoRepairManager:
    """Test cases for AutoRepairManager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.logger = InconsistencyLogger(self.db_path)
        self.repair_manager = AutoRepairManager(self.logger)

    def teardown_method(self):
        """Clean up test fixtures."""
        import os

        os.close(self.db_fd)
        os.unlink(self.db_path)

    @patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill")
    def test_repair_video_gap_success(self, mock_backfill_class):
        """Test successful video gap repair."""
        # Mock the backfill service
        mock_backfill = MagicMock()
        mock_backfill.fetch_all_videos_from_channel.return_value = [
            {
                "video_id": "vid1",
                "title": "Video 1",
                "url": "https://youtu.be/vid1",
                "date": "2024-01-01",
            },
            {
                "video_id": "vid2",
                "title": "Video 2",
                "url": "https://youtu.be/vid2",
                "date": "2024-01-02",
            },
        ]
        mock_backfill_class.return_value = mock_backfill

        # Mock database functions
        with patch("yt_fts.core.database.add_videos_bulk", return_value=2):
            # Log an inconsistency
            inconsistency_id = self.logger.log_inconsistency(
                channel_id="UC123",
                channel_name="Test Channel",
                inconsistency_type="video_gap",
                severity="high",
                details="2 videos missing",
                stats={"total": 10, "with_subs": 8},
            )

            # Attempt repair
            repair_data = {
                "type": "video_gap",
                "channel_id": "UC123",
                "stats": {"total": 10},
            }

            success = self.repair_manager.attempt_repair(inconsistency_id, repair_data)

            assert success is True

            # Verify repair was logged
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT auto_repaired, repair_action FROM db_inconsistencies WHERE id = ?",
                (inconsistency_id,),
            )
            row = cursor.fetchone()
            assert row[0] == 1  # auto_repaired = True
            assert "Fetched 2 videos" in row[1]
            conn.close()

    @patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill")
    def test_repair_video_gap_api_failure(self, mock_backfill_class):
        """Test video gap repair when API fails."""
        mock_backfill = MagicMock()
        mock_backfill.fetch_all_videos_from_channel.return_value = None
        mock_backfill_class.return_value = mock_backfill

        inconsistency_id = self.logger.log_inconsistency(
            channel_id="UC123",
            channel_name="Test Channel",
            inconsistency_type="video_gap",
            severity="high",
            details="Videos missing",
            stats={"total": 10},
        )

        repair_data = {
            "type": "video_gap",
            "channel_id": "UC123",
            "stats": {"total": 10},
        }

        success = self.repair_manager.attempt_repair(inconsistency_id, repair_data)

        assert success is False

        # Verify failure was logged
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT auto_repaired, repair_action FROM db_inconsistencies WHERE id = ?",
            (inconsistency_id,),
        )
        row = cursor.fetchone()
        assert row[0] == 0  # auto_repaired = False
        assert "FAILED:" in row[1]
        conn.close()

    @patch("yt_fts.core.database.update_channel_stats")
    @patch("yt_fts.core.database.get_channel_stats")
    def test_repair_count_mismatch_success(self, mock_get_stats, mock_update_stats):
        """Test successful count mismatch repair."""
        # Mock stats before and after
        mock_get_stats.side_effect = [
            {
                "total": 100,
                "with_transcripts": 95,
                "scheduled": 3,
                "members_only": 2,
            },  # Before
            {
                "total": 100,
                "with_transcripts": 95,
                "scheduled": 3,
                "members_only": 2,
            },  # After (consistent)
        ]

        inconsistency_id = self.logger.log_inconsistency(
            channel_id="UC123",
            channel_name="Test Channel",
            inconsistency_type="count_mismatch",
            severity="medium",
            details="Count inconsistency detected",
            stats={"total": 100, "with_transcripts": 95},
        )

        repair_data = {
            "type": "count_mismatch",
            "channel_id": "UC123",
            "stats": {"total": 100},
        }

        success = self.repair_manager.attempt_repair(inconsistency_id, repair_data)

        assert success is True
        mock_update_stats.assert_called_once_with("UC123")

    @patch("yt_fts.core.database.update_channel_stats")
    @patch("yt_fts.core.database.get_channel_stats")
    def test_repair_count_mismatch_still_inconsistent(
        self, mock_get_stats, mock_update_stats
    ):
        """Test count mismatch repair when issue persists."""
        # Mock stats - still inconsistent after repair
        mock_get_stats.return_value = {
            "total": 100,
            "with_transcripts": 110,
            "scheduled": 5,
            "members_only": 2,
        }  # with_subs > total

        inconsistency_id = self.logger.log_inconsistency(
            channel_id="UC123",
            channel_name="Test Channel",
            inconsistency_type="count_mismatch",
            severity="medium",
            details="Count inconsistency detected",
            stats={"total": 100},
        )

        repair_data = {
            "type": "count_mismatch",
            "channel_id": "UC123",
            "stats": {"total": 100},
        }

        success = self.repair_manager.attempt_repair(inconsistency_id, repair_data)

        assert success is False

        # Verify failure was logged
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT auto_repaired, repair_action FROM db_inconsistencies WHERE id = ?",
            (inconsistency_id,),
        )
        row = cursor.fetchone()
        assert row[0] == 0  # auto_repaired = False
        assert "did not resolve" in row[1]
        conn.close()

    def test_repair_unknown_type(self):
        """Test repair attempt for unknown inconsistency type."""
        inconsistency_id = self.logger.log_inconsistency(
            channel_id="UC123",
            channel_name="Test Channel",
            inconsistency_type="unknown_type",
            severity="low",
            details="Unknown issue",
            stats={},
        )

        repair_data = {"type": "unknown_type", "channel_id": "UC123"}

        success = self.repair_manager.attempt_repair(inconsistency_id, repair_data)

        assert success is False

        # Verify failure was logged
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT repair_action FROM db_inconsistencies WHERE id = ?",
            (inconsistency_id,),
        )
        row = cursor.fetchone()
        assert "Unknown inconsistency type" in row[0]
        conn.close()


class TestBatchDownloaderInconsistencyDetection:
    """Test cases for enhanced inconsistency detection in BatchDownloader."""

    def test_format_db_stats_consistent_data(self):
        """Test formatting stats for consistent data."""
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        result = downloader._format_db_stats(
            db_count=100,
            db_with_subs=95,
            db_no_subs=3,
            db_scheduled=2,
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=0,
            status_name="Test Channel",
        )

        assert result["inconsistent"] is False
        assert result["reason"] == ""
        assert result["severity"] == "low"
        assert "100 total" in result["stats"]
        # Checksum components are always displayed (even when 0)
        assert "95 with transcripts" in result["stats"]
        assert "3 no subs" in result["stats"]
        assert "2 sch" in result["stats"]
        assert "0 mem" in result["stats"]

    def test_format_db_stats_critical_inconsistency(self):
        """Test detection of critical inconsistency (impossible count)."""
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        result = downloader._format_db_stats(
            db_count=100,
            db_with_subs=150,  # Impossible: more subs than total
            db_no_subs=0,
            db_scheduled=0,
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=0,
            status_name="Test Channel",
        )

        assert result["inconsistent"] is True
        assert result["severity"] == "critical"
        assert result["type"] == "impossible_count"
        assert "with_subs (150) > total (100)" in result["reason"]
        assert "[red]" in result["stats"]  # Should be colored red

    def test_format_db_stats_high_priority_gap(self):
        """Test detection of high priority video gap."""
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        result = downloader._format_db_stats(
            db_count=100,
            db_with_subs=90,  # 10 videos unaccounted for
            db_no_subs=0,
            db_scheduled=0,
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=0,
            status_name="Test Channel",
        )

        assert result["inconsistent"] is True
        assert result["severity"] == "high"
        assert result["type"] == "video_gap"
        assert "10 videos not accounted for" in result["reason"]

    def test_format_db_stats_medium_priority_gap(self):
        """Test detection of medium priority small gap."""
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        result = downloader._format_db_stats(
            db_count=100,
            db_with_subs=97,  # 3 videos unaccounted for (medium priority)
            db_no_subs=0,
            db_scheduled=0,
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=0,
            status_name="Test Channel",
        )

        assert result["inconsistent"] is True
        assert result["severity"] == "medium"
        assert result["type"] == "video_gap"

    def test_format_db_stats_over_counting(self):
        """Test detection of over-counting issue."""
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        result = downloader._format_db_stats(
            db_count=100,
            db_with_subs=95,
            db_no_subs=10,
            db_scheduled=5,
            db_members=2,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=0,
            status_name="Test Channel",
            # Special total = 10 + 5 + 2 = 17, unexplained gap = 100 - 95 - 17 = -12 (over-counting)
        )

        assert result["inconsistent"] is True
        assert result["severity"] == "medium"
        assert result["type"] == "over_counting"
        assert "Over-accounting by 12 videos" in result["reason"]

    def test_format_db_stats_with_channel_info(self):
        """Test formatting with channel ID and name (for logging)."""
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        result = downloader._format_db_stats(
            db_count=100,
            db_with_subs=150,  # Critical inconsistency
            db_no_subs=0,
            db_scheduled=0,
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=0,
            status_name="Test Channel",
            channel_id="UC123456789",
            channel_display_name="Test Channel Name",
        )

        assert result["inconsistent"] is True
        assert result["severity"] == "critical"
        assert isinstance(
            result["inconsistency_id"], int
        )  # Should have logged the inconsistency
        assert result["inconsistency_id"] > 0


class TestIntegrationInconsistencySystem:
    """Integration tests for the complete inconsistency detection and repair system."""

    def setup_method(self):
        """Set up integration test environment."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.logger = InconsistencyLogger(self.db_path)
        self.repair_manager = AutoRepairManager(self.logger)

    def teardown_method(self):
        """Clean up integration test environment."""
        import os

        os.close(self.db_fd)
        os.unlink(self.db_path)

    @patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill")
    @patch("yt_fts.core.database.add_videos_bulk")
    def test_complete_gap_repair_workflow(self, mock_add_videos, mock_backfill_class):
        """Test complete workflow: detect gap -> log -> auto-repair -> verify."""
        # Mock successful API call and database addition
        mock_backfill = MagicMock()
        mock_backfill.fetch_all_videos_from_channel.return_value = [
            {
                "video_id": "vid1",
                "title": "Video 1",
                "url": "https://youtu.be/vid1",
                "date": "2024-01-01",
            },
            {
                "video_id": "vid2",
                "title": "Video 2",
                "url": "https://youtu.be/vid2",
                "date": "2024-01-02",
            },
        ]
        mock_backfill_class.return_value = mock_backfill
        mock_add_videos.return_value = 2

        # Step 1: Simulate inconsistency detection (normally done by BatchDownloader)
        inconsistency_id = self.logger.log_inconsistency(
            channel_id="UC123",
            channel_name="Test Channel",
            inconsistency_type="video_gap",
            severity="high",
            details="2 videos unaccounted for in special categories",
            stats={
                "total": 10,
                "with_subs": 8,
                "special_total": 0,
                "unexplained_gap": 2,
            },
        )

        # Step 2: Attempt auto-repair
        repair_data = {
            "type": "video_gap",
            "channel_id": "UC123",
            "stats": {"total": 10},
        }
        repair_success = self.repair_manager.attempt_repair(
            inconsistency_id, repair_data
        )

        # Step 3: Verify repair success
        assert repair_success is True

        # Step 4: Check final state
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT auto_repaired, resolved_at, repair_action
            FROM db_inconsistencies WHERE id = ?
        """,
            (inconsistency_id,),
        )
        row = cursor.fetchone()

        assert row[0] == 1  # auto_repaired
        assert row[1] is not None  # resolved_at set
        assert "Fetched 2 videos" in row[2]  # repair_action

        # Check summary was updated
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT auto_repaired FROM inconsistency_summary WHERE date = ?", (today,)
        )
        summary_row = cursor.fetchone()
        assert summary_row[0] == 1

        conn.close()

        # Verify API was called correctly
        mock_backfill.fetch_all_videos_from_channel.assert_called_once_with("UC123")
        mock_add_videos.assert_called_once()

    def test_statistics_tracking_over_time(self):
        """Test that statistics are properly tracked over multiple days."""
        # Create inconsistencies for different days
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert historical data
        cursor.execute(
            """
            INSERT INTO inconsistency_summary (date, total_detected, auto_repaired, unresolved)
            VALUES (?, 3, 2, 1)
        """,
            (yesterday,),
        )

        # Add today's inconsistencies
        for i in range(5):
            self.logger.log_inconsistency(
                channel_id=f"UC{i}",
                channel_name=f"Channel {i}",
                inconsistency_type="video_gap",
                severity="high",
                details=f"Gap {i}",
                stats={"total": 100},
            )

        # Repair 3 of them
        for i in range(3):
            cursor.execute(
                "SELECT id FROM db_inconsistencies WHERE channel_id = ?", (f"UC{i}",)
            )
            row = cursor.fetchone()
            if row:
                self.logger.log_repair_attempt(row[0], "Test repair", True)

        conn.commit()
        conn.close()

        # Check statistics
        stats = self.logger.get_inconsistency_stats(days=30)
        assert stats["total_inconsistencies"] == 5  # Today's only
        assert stats["auto_repaired"] == 3

        # Check unresolved list
        unresolved = self.logger.get_unresolved_inconsistencies()
        assert len(unresolved) == 2  # 5 - 3 = 2

    def test_error_handling_in_repair_system(self):
        """Test that the repair system handles errors gracefully."""
        # Log inconsistency
        inconsistency_id = self.logger.log_inconsistency(
            channel_id="UC123",
            channel_name="Test Channel",
            inconsistency_type="video_gap",
            severity="high",
            details="Gap detected",
            stats={"total": 100},
        )

        # Attempt repair with invalid data (should handle gracefully)
        repair_data = {
            "type": "video_gap",
            "channel_id": None,  # Invalid
            "stats": {"total": 100},
        }

        # This should not crash, even with invalid data
        success = self.repair_manager.attempt_repair(inconsistency_id, repair_data)
        assert success is False

        # Verify failure was logged
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT auto_repaired FROM db_inconsistencies WHERE id = ?",
            (inconsistency_id,),
        )
        row = cursor.fetchone()
        assert row[0] == 0  # Should still be False
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
