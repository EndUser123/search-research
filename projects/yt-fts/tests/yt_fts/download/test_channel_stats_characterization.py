"""Characterization tests for _format_db_stats method in BatchDownloader.

These tests CAPTURE CURRENT BEHAVIOR before refactoring.
Run with: pytest tests/yt_fts/download/test_channel_stats_characterization.py -v
"""

from unittest.mock import MagicMock, patch
import pytest

from yt_fts.download.batch_downloader import BatchDownloader


@pytest.fixture
def downloader():
    return BatchDownloader(
        channels=["@testchannel"],
        suppress_quota_print=True,
        suppress_verbose=True,
    )


class TestFormatDbStatsBasicFormatting:
    """Tests for basic stats formatting."""

    def test_basic_stats_formatting(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=80, db_no_subs=20,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
        )
        assert result["stats"] == "100 total | 80 cc, 20 no cc"
        assert result["inconsistent"] is False
        assert result["severity"] == "low"

    def test_stats_with_unavailable(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=70, db_no_subs=20,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=10, db_shorts=0,
            status_name="test_status",
        )
        assert result["stats"] == "100 total | 70 cc, 20 no cc, 10 unv"
        assert result["inconsistent"] is False

    def test_stats_with_scheduled(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=70, db_no_subs=20,
            db_scheduled=10, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
        )
        assert result["stats"] == "100 total | 70 cc, 20 no cc, 10 sch"

    def test_stats_with_members(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=80, db_no_subs=15,
            db_scheduled=0, db_members=5,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
        )
        assert result["stats"] == "100 total | 80 cc, 15 no cc, 5 mem"

    def test_stats_with_shorts(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=80, db_no_subs=15,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=5,
            status_name="test_status",
        )
        assert result["stats"] == "100 total | 80 cc, 15 no cc, 5 shorts"

    def test_stats_millions_formatter(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=80, db_no_subs=20,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status", db_subscriber_count=2500000,
        )
        assert "2.5M subs" in result["stats"]

    def test_stats_thousands_formatter(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=80, db_no_subs=20,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status", db_subscriber_count=15000,
        )
        assert "15.0K subs" in result["stats"]

    def test_stats_small_subs_formatter(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=80, db_no_subs=20,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status", db_subscriber_count=500,
        )
        assert "500 subs" in result["stats"]

    def test_stats_with_playlist(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=80, db_no_subs=20,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status", db_playlist_count=25,
        )
        assert "25 pl" in result["stats"]


class TestFormatDbStatsImpossibleCounts:
    """Tests for impossible count detection (critical severity)."""

    def test_with_subs_exceeds_total(self, downloader):
        result = downloader._format_db_stats(
            db_count=50, db_with_subs=60, db_no_subs=0,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
            channel_id="UC123", channel_display_name="TestChannel",
        )
        assert result["inconsistent"] is True
        assert result["severity"] == "critical"
        assert result["type"] == "impossible_count"
        assert "with_subs (60) > total (50)" in result["reason"]

    def test_scheduled_exceeds_total(self, downloader):
        result = downloader._format_db_stats(
            db_count=50, db_with_subs=40, db_no_subs=0,
            db_scheduled=60, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
            channel_id="UC123", channel_display_name="TestChannel",
        )
        assert result["inconsistent"] is True
        assert result["severity"] == "critical"
        assert result["type"] == "impossible_count"

    def test_unavailable_exceeds_total(self, downloader):
        result = downloader._format_db_stats(
            db_count=50, db_with_subs=40, db_no_subs=0,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=60, db_shorts=0,
            status_name="test_status",
            channel_id="UC123", channel_display_name="TestChannel",
        )
        assert result["inconsistent"] is True
        assert result["severity"] == "critical"

    def test_shorts_exceeds_total(self, downloader):
        result = downloader._format_db_stats(
            db_count=50, db_with_subs=40, db_no_subs=0,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=60,
            status_name="test_status",
            channel_id="UC123", channel_display_name="TestChannel",
        )
        assert result["inconsistent"] is True
        assert result["severity"] == "critical"

    def test_members_exceeds_total(self, downloader):
        result = downloader._format_db_stats(
            db_count=50, db_with_subs=40, db_no_subs=0,
            db_scheduled=0, db_members=60,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
            channel_id="UC123", channel_display_name="TestChannel",
        )
        assert result["inconsistent"] is True
        assert result["severity"] == "critical"


class TestFormatDbStatsVideoGaps:
    """Tests for unexplained video gap detection."""

    def test_significant_gap_high_severity(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=50, db_no_subs=20,
            db_scheduled=5, db_members=5,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=10, db_shorts=0,
            status_name="test_status",
            channel_id="UC123", channel_display_name="TestChannel",
        )
        assert result["inconsistent"] is True
        assert result["severity"] == "high"
        assert result["type"] == "video_gap"
        assert "10 videos not accounted for" in result["reason"]

    def test_small_gap_medium_severity(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=70, db_no_subs=20,
            db_scheduled=2, db_members=2,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=4, db_shorts=0,
            status_name="test_status",
            channel_id="UC123", channel_display_name="TestChannel",
        )
        assert result["inconsistent"] is True
        assert result["severity"] == "medium"
        assert result["type"] == "video_gap"

    def test_no_gap_when_balanced(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=80, db_no_subs=20,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
        )
        assert result["inconsistent"] is False
        assert result["severity"] == "low"

    def test_gap_of_zero_is_consistent(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=75, db_no_subs=15,
            db_scheduled=5, db_members=5,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
        )
        assert result["inconsistent"] is False


class TestFormatDbStatsOverCounting:
    """Tests for over-counting detection."""

    def test_over_counting_medium_severity(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=90, db_no_subs=5,
            db_scheduled=5, db_members=5,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=5, db_shorts=0,
            status_name="test_status",
            channel_id="UC123", channel_display_name="TestChannel",
        )
        assert result["inconsistent"] is True
        assert result["severity"] == "medium"
        assert result["type"] == "over_counting"
        assert "Over-accounting by 10 videos" in result["reason"]

    def test_small_over_counting_within_tolerance(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=90, db_no_subs=5,
            db_scheduled=3, db_members=2,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=2, db_shorts=0,
            status_name="test_status",
        )
        assert result["inconsistent"] is False


class TestFormatDbStatsEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_total_count(self, downloader):
        result = downloader._format_db_stats(
            db_count=0, db_with_subs=0, db_no_subs=0,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
        )
        assert result["inconsistent"] is False
        assert result["stats"] == "0 total | 0 cc, 0 no cc"

    def test_none_metadata_values(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=80, db_no_subs=20,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
            db_subscriber_count=None, db_playlist_count=None,
        )
        assert "subs" not in result["stats"].lower()
        assert "pl" not in result["stats"].lower()

    def test_zero_metadata_not_shown(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=80, db_no_subs=20,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
            db_subscriber_count=0, db_playlist_count=0,
        )
        assert "subs" not in result["stats"]
        assert "pl" not in result["stats"]


class TestFormatDbStatsRichTagStripping:
    """Tests for Rich markup tag stripping."""

    def test_red_tags_stripped(self, downloader):
        result = downloader._format_db_stats(
            db_count=50, db_with_subs=60, db_no_subs=0,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
        )
        assert "[red]" not in result["stats"]
        assert "[/red]" not in result["stats"]
        assert result["inconsistent"] is True


class TestFormatDbStatsInconsistencyLogging:
    """Tests for inconsistency logging behavior."""

    @patch("yt_fts.core.inconsistency_logger.InconsistencyLogger")
    @patch("yt_fts.core.inconsistency_logger.AutoRepairManager")
    def test_logger_called_with_channel_id(
        self, mock_repair_class, mock_logger_class, downloader
    ):
        mock_logger = MagicMock()
        mock_logger.log_inconsistency.return_value = 1
        mock_logger_class.return_value = mock_logger
        mock_repair = MagicMock()
        mock_repair.attempt_repair.return_value = False
        mock_repair_class.return_value = mock_repair

        result = downloader._format_db_stats(
            db_count=50, db_with_subs=60, db_no_subs=0,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
            channel_id="UC123", channel_display_name="TestChannel",
        )

        mock_logger.log_inconsistency.assert_called_once()
        mock_repair.attempt_repair.assert_called_once()

    @patch("yt_fts.core.inconsistency_logger.InconsistencyLogger")
    def test_logger_not_called_without_channel_id(
        self, mock_logger_class, downloader
    ):
        mock_logger = MagicMock()
        mock_logger_class.return_value = mock_logger

        result = downloader._format_db_stats(
            db_count=50, db_with_subs=60, db_no_subs=0,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
        )

        assert result["inconsistent"] is True
        mock_logger.log_inconsistency.assert_not_called()
        assert result["inconsistency_id"] is None

    @patch("yt_fts.core.inconsistency_logger.InconsistencyLogger")
    def test_exception_in_logger_does_not_crash(
        self, mock_logger_class, downloader
    ):
        mock_logger = MagicMock()
        mock_logger.log_inconsistency.side_effect = Exception("error")
        mock_logger_class.return_value = mock_logger

        result = downloader._format_db_stats(
            db_count=50, db_with_subs=60, db_no_subs=0,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
            channel_id="UC123", channel_display_name="TestChannel",
        )

        assert result["inconsistent"] is True


class TestFormatDbStatsReturnValueStructure:
    """Tests for return value structure."""

    def test_return_dict_contains_all_keys(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=80, db_no_subs=20,
            db_scheduled=0, db_members=0,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=0, db_shorts=0,
            status_name="test_status",
        )
        expected_keys = {
            "stats", "inconsistent", "reason", "severity",
            "type", "details", "inconsistency_id",
        }
        assert set(result.keys()) == expected_keys

    def test_details_dict_contains_all_fields(self, downloader):
        result = downloader._format_db_stats(
            db_count=100, db_with_subs=80, db_no_subs=20,
            db_scheduled=5, db_members=2,
            db_unavail_deleted=0, db_unavail_private=0, db_unavail_geo=0,
            db_unavailable=3, db_shorts=1,
            status_name="test_status",
        )
        assert result["details"]["total"] == 100
        assert result["details"]["with_subs"] == 80
        assert result["details"]["no_subs"] == 20
        assert result["details"]["scheduled"] == 5
        assert result["details"]["members"] == 2
        assert result["details"]["unavailable"] == 3
        assert result["details"]["shorts"] == 1