"""Tests for batch_channel_helpers module.

Characterization tests for extracted helpers from batch_downloader.py.
These tests verify the extracted functions maintain the same behavior.
"""

import threading
from unittest.mock import MagicMock, Mock

import pytest

from yt_fts.download.batch_channel_helpers import (
    ChannelDownloadContext,
    create_thread_db_connection,
    determine_rss_status,
    determine_status_name,
    extract_handle,
    format_rss_status_message,
    format_skip_message,
    get_unavailable_video_title,
    initialize_channel_state,
    load_channel_db_stats,
    perform_rss_check,
    process_unavailable_videos,
    recheck_unavailable_videos,
    should_skip_fresh_channel,
)


class TestInitializeChannelState:
    """Tests for initialize_channel_state function."""

    def test_returns_all_keys(self):
        """Result dict contains all expected keys."""
        result = initialize_channel_state()
        expected_keys = {
            "db_count",
            "db_video_ids",
            "db_with_subs",
            "db_scheduled",
            "db_members",
            "db_unavailable",
            "db_unavail_deleted",
            "db_unavail_private",
            "db_unavail_geo",
            "db_unavail_age",
            "db_unavail_generic",
            "db_shorts",
            "db_no_subs",
        }
        assert set(result.keys()) == expected_keys

    def test_default_values_are_zero_or_empty_set(self):
        """Default values are 0 for counts, empty set for video_ids."""
        result = initialize_channel_state()
        assert result["db_count"] == 0
        assert result["db_video_ids"] == set()
        assert result["db_with_subs"] == 0

    def test_custom_values_preserved(self):
        """Custom parameter values are preserved."""
        result = initialize_channel_state(
            db_count=100,
            db_with_subs=50,
            db_no_subs=30,
        )
        assert result["db_count"] == 100
        assert result["db_with_subs"] == 50
        assert result["db_no_subs"] == 30


class TestLoadChannelDbStats:
    """Tests for load_channel_db_stats function."""

    def test_successful_load(self):
        """Successfully loads stats from database functions."""
        mock_get_vid_ids = Mock(return_value=[("vid1",), ("vid2",)])
        # Mock dict that handles .get() calls for optional stats
        mock_stats_dict = {
            "total": 100,
            "with_transcripts": 80,
            "scheduled": 5,
            "members_only": 2,
            "unavailable": 10,
            "without_transcripts": 3,
            "unavailable_deleted": 0,
            "unavailable_private": 0,
            "unavailable_geo": 0,
            "unavailable_age": 0,
            "unavailable_generic": 0,
            "shorts": 0,
        }
        mock_get_stats = Mock(return_value=mock_stats_dict)
        mock_logger = MagicMock()

        result = load_channel_db_stats(
            "UC123",
            mock_get_vid_ids,
            mock_get_stats,
            mock_logger,
        )

        assert result["db_count"] == 100
        assert result["db_with_subs"] == 80
        assert result["db_scheduled"] == 5
        assert result["db_members"] == 2
        assert result["db_unavailable"] == 10
        assert result["db_no_subs"] == 3
        assert result["db_video_ids"] == {"vid1", "vid2"}
        mock_get_vid_ids.assert_called_once_with("UC123")
        mock_get_stats.assert_called_once_with("UC123")

    def test_error_returns_empty_state(self):
        """Returns empty state when database functions raise exception."""
        mock_get_vid_ids = Mock(side_effect=Exception("DB error"))
        mock_get_stats = Mock()
        mock_logger = MagicMock()

        result = load_channel_db_stats(
            "UC123",
            mock_get_vid_ids,
            mock_get_stats,
            mock_logger,
        )

        assert result["db_count"] == 0
        assert result["db_video_ids"] == set()
        assert result["db_with_subs"] == 0


class TestDetermineStatusName:
    """Tests for determine_status_name function."""

    def test_long_channel_id_truncated(self):
        """Long channel IDs are truncated (no prefix, just truncated ID)."""
        result = determine_status_name("UC" + "x" * 24, "https://youtube.com/channel/UC...")
        # Original code: long IDs >15 chars get truncated without "channel/" prefix
        # Function returns channel_id[:20] + "..." = first 20 chars + "..."
        assert result == "UC" + "x" * 18 + "..."  # 20 chars total, then "..."

    def test_short_channel_id_formatted(self):
        """Short channel IDs get channel/ prefix."""
        result = determine_status_name("UC123", "https://youtube.com/channel/UC123")
        assert result == "channel/UC123"

    def test_handle_extracted_from_url(self):
        """@handle extracted from URL."""
        result = determine_status_name(None, "https://youtube.com/@testchannel")
        assert result == "@testchannel"

    def test_fallback_to_url_truncation(self):
        """When no channel_id or handle, truncate URL."""
        long_url = "https://youtube.com/c/verylongchannelnamethatgoesonandon"
        result = determine_status_name(None, long_url)
        assert result == long_url[:40] + "..."

    def test_none_channel_id_with_handle(self):
        """None channel_id with @ in URL extracts handle."""
        result = determine_status_name(None, "https://youtube.com/@test/videos")
        assert result == "@test"


class TestExtractHandle:
    """Tests for extract_handle function."""

    def test_extract_handle_from_url(self):
        """Extract handle from URL with @."""
        result = extract_handle("https://youtube.com/@testchannel/videos")
        assert result == "testchannel"

    def test_extract_handle_simple(self):
        """Extract handle from simple @handle format."""
        result = extract_handle("@testchannel")
        assert result == "testchannel"

    def test_no_handle_returns_none(self):
        """Return None when no @ in URL."""
        result = extract_handle("https://youtube.com/channel/UC123")
        assert result is None

    def test_handle_with_trailing_slash(self):
        """Handle extraction handles trailing slashes."""
        result = extract_handle("https://youtube.com/@testchannel/")
        assert result == "testchannel"


class TestShouldSkipFreshChannel:
    """Tests for should_skip_fresh_channel function."""

    def test_skip_when_fresh(self):
        """Skip channel when freshness check passes."""
        mock_is_fresh = Mock(return_value=(True, "2025-01-10T10:00:00"))
        result, reason = should_skip_fresh_channel(
            "UC123",
            db_count=10,
            freshness_hours=6,
            is_channel_fresh=mock_is_fresh,
        )
        assert result is True
        assert "Recently checked" in reason

    def test_no_skip_when_not_fresh(self):
        """Don't skip when freshness check fails."""
        mock_is_fresh = Mock(return_value=(False, None))
        result, reason = should_skip_fresh_channel(
            "UC123",
            db_count=10,
            freshness_hours=6,
            is_channel_fresh=mock_is_fresh,
        )
        assert result is False
        assert reason is None

    def test_no_skip_when_db_empty(self):
        """Don't skip when database is empty (new channel)."""
        mock_is_fresh = Mock()
        result, reason = should_skip_fresh_channel(
            "UC123",
            db_count=0,
            freshness_hours=6,
            is_channel_fresh=mock_is_fresh,
        )
        assert result is False
        assert reason is None
        mock_is_fresh.assert_not_called()

    def test_no_skip_when_freshness_disabled(self):
        """Don't skip when freshness_hours is 0."""
        mock_is_fresh = Mock()
        result, reason = should_skip_fresh_channel(
            "UC123",
            db_count=10,
            freshness_hours=0,
            is_channel_fresh=mock_is_fresh,
        )
        assert result is False
        assert reason is None
        mock_is_fresh.assert_not_called()


class TestCreateThreadDbConnection:
    """Tests for create_thread_db_connection function."""

    def test_creates_new_connection_on_first_call(self):
        """Create new connection when none exists."""
        mock_get_conn = Mock(return_value=Mock())
        thread_local = threading.local()
        all_conns = []
        lock = threading.Lock()

        result = create_thread_db_connection(
            mock_get_conn, 10.0, thread_local, all_conns, lock
        )

        assert result is not None
        assert hasattr(thread_local, "conn")
        assert len(all_conns) == 1

    def test_reuses_existing_connection(self):
        """Reuse existing connection for same thread."""
        existing_conn = Mock()
        thread_local = threading.local()
        thread_local.conn = existing_conn
        all_conns = []
        lock = threading.Lock()

        result = create_thread_db_connection(
            Mock(), 10.0, thread_local, all_conns, lock
        )

        assert result is existing_conn

    def test_adds_connection_to_list(self):
        """New connection is added to all_conns list."""
        mock_conn = Mock()
        mock_get_conn = Mock(return_value=mock_conn)
        thread_local = threading.local()
        all_conns = []
        lock = threading.Lock()

        create_thread_db_connection(
            mock_get_conn, 30.0, thread_local, all_conns, lock
        )

        assert mock_conn in all_conns


class TestFormatSkipMessage:
    """Tests for format_skip_message function."""

    def test_rss_skip_with_unavailable(self):
        """Format skip message with unavailable videos tracked."""
        mock_result = Mock()
        mock_result.unavailable_video_ids = ["vid1", "vid2"]

        result = format_skip_message(rss_skip=True, should_skip_download=False, rss_result=mock_result)

        assert "all videos already in database" in result
        assert "tracking 2 unavailable" in result

    def test_rss_skip_without_unavailable(self):
        """Format skip message without unavailable videos."""
        mock_result = Mock()
        mock_result.unavailable_video_ids = []

        result = format_skip_message(rss_skip=True, should_skip_download=False, rss_result=mock_result)

        assert result == "all videos already in database"

    def test_download_skip_message(self):
        """Format skip message for download skip."""
        result = format_skip_message(rss_skip=False, should_skip_download=True, rss_result=None)

        assert "verified via API" in result


class TestChannelDownloadContext:
    """Tests for ChannelDownloadContext class."""

    def test_get_thread_conn_creates_connection(self):
        """get_thread_conn creates new connection."""
        mock_get_conn = Mock(return_value=Mock())

        context = ChannelDownloadContext(mock_get_conn, max_workers=1)
        conn = context.get_thread_conn()

        assert conn is not None
        mock_get_conn.assert_called_once()

    def test_executor_property(self):
        """Executor property returns ThreadPoolExecutor."""
        context = ChannelDownloadContext(Mock(), max_workers=2)

        executor = context.executor

        assert executor is not None
        assert executor._max_workers == 2

    def test_cleanup_closes_connections(self):
        """Cleanup closes all database connections."""
        mock_conn1 = Mock()
        mock_conn2 = Mock()
        mock_get_conn = Mock(return_value=mock_conn1)

        context = ChannelDownloadContext(mock_get_conn, max_workers=1)
        # Manually add connections to simulate multiple threads
        context._all_conns = [mock_conn1, mock_conn2]

        context.cleanup()

        mock_conn1.close.assert_called_once()
        mock_conn2.close.assert_called_once()

    def test_cleanup_shuts_down_executor(self):
        """Cleanup shuts down thread pool executor."""
        mock_get_conn = Mock(return_value=Mock())

        context = ChannelDownloadContext(mock_get_conn, max_workers=2)
        _ = context.executor  # Create executor

        context.cleanup()

        assert context._executor is None

    def test_multiple_calls_to_get_thread_conn_return_same(self):
        """Multiple calls return same connection for same thread."""
        mock_get_conn = Mock(return_value=Mock())

        context = ChannelDownloadContext(mock_get_conn, max_workers=1)
        conn1 = context.get_thread_conn()
        conn2 = context.get_thread_conn()

        assert conn1 is conn2
        mock_get_conn.assert_called_once()


class TestRecheckUnavailableVideos:
    """Tests for recheck_unavailable_videos function."""

    def test_returns_available_videos(self):
        """Return list of videos that became available."""
        mock_checker = Mock()
        mock_checker._check_video_availability = Mock(
            return_value={"vid1": "available", "vid2": "unavailable"}
        )
        mock_get_recheck = Mock(
            return_value=[("vid1", "UC123", "title1"), ("vid2", "UC123", "title2")]
        )
        mock_update = Mock()

        result = recheck_unavailable_videos(
            "UC123", mock_checker, mock_get_recheck, mock_update
        )

        assert result == ["vid1"]
        assert mock_update.call_count == 2  # Both videos updated

    def test_empty_when_no_unavailable(self):
        """Return empty list when no unavailable videos."""
        mock_checker = Mock()
        mock_get_recheck = Mock(return_value=[])
        mock_update = Mock()

        result = recheck_unavailable_videos(
            "UC123", mock_checker, mock_get_recheck, mock_update
        )

        assert result == []


class TestGetUnavailableVideoTitle:
    """Tests for get_unavailable_video_title function."""

    def test_scheduled_title(self):
        """Return correct title for scheduled videos."""
        assert get_unavailable_video_title("scheduled") == "[Scheduled]"

    def test_members_only_title(self):
        """Return correct title for members-only videos."""
        assert get_unavailable_video_title("members_only") == "[Members only]"

    def test_deleted_title(self):
        """Return correct title for deleted videos."""
        assert get_unavailable_video_title("unavailable/deleted") == "[Unavailable/Deleted]"

    def test_unknown_status_title(self):
        """Return default title for unknown status."""
        assert get_unavailable_video_title("unknown") == "[Unavailable]"


class TestProcessUnavailableVideos:
    """Tests for process_unavailable_videos function."""

    def test_processes_unavailable_list(self):
        """Process list of unavailable videos."""
        mock_add_video = Mock()
        unavailable_ids = ["vid1", "vid2"]
        status_dict = {"vid1": "scheduled", "vid2": "members_only"}

        process_unavailable_videos(
            "UC123", unavailable_ids, status_dict, mock_add_video
        )

        assert mock_add_video.call_count == 2

    def test_handles_add_video_errors(self):
        """Continue processing even if add_video fails."""
        mock_add_video = Mock(side_effect=[Exception("DB error"), None])
        unavailable_ids = ["vid1", "vid2"]
        status_dict = {"vid1": "scheduled", "vid2": "members_only"}

        # Should not raise exception
        process_unavailable_videos(
            "UC123", unavailable_ids, status_dict, mock_add_video
        )

        # Both calls attempted despite error on first
        assert mock_add_video.call_count == 2


class TestDetermineRssStatus:
    """Tests for determine_rss_status function."""

    def test_skip_when_missing_count_zero(self):
        """Return 'skip' when missing count is zero."""
        result = determine_rss_status(
            rss_result=None, rss_skip=False, rss_missing_count=0,
            new_channel_skipped_rss=False
        )
        assert result == "skip"

    def test_new_videos_for_new_channel(self):
        """Return 'new_videos' for new channel with missing videos."""
        mock_result = Mock()
        mock_result.status = "new_videos"
        result = determine_rss_status(
            rss_result=mock_result, rss_skip=False, rss_missing_count=5,
            new_channel_skipped_rss=True
        )
        assert result == "new_videos"

    def test_skip_when_rss_skip_true(self):
        """Return 'skip' when rss_skip flag is True."""
        mock_result = Mock()
        mock_result.status = "new_videos"
        result = determine_rss_status(
            rss_result=mock_result, rss_skip=True, rss_missing_count=5,
            new_channel_skipped_rss=False
        )
        assert result == "skip"

    def test_gap_detected_status(self):
        """Return 'gap_detected' from RSS result."""
        mock_result = Mock()
        mock_result.status = "gap_detected"
        result = determine_rss_status(
            rss_result=mock_result, rss_skip=False, rss_missing_count=5,
            new_channel_skipped_rss=False
        )
        assert result == "gap_detected"

    def test_error_when_no_result(self):
        """Return 'error' when no RSS result."""
        result = determine_rss_status(
            rss_result=None, rss_skip=False, rss_missing_count=5,
            new_channel_skipped_rss=False
        )
        assert result == "error"


class TestFormatRssStatusMessage:
    """Tests for format_rss_status_message function."""

    def test_skip_message_with_unavailable(self):
        """Format skip message with unavailable video count."""
        mock_result = Mock()
        mock_result.unavailable_video_ids = ["vid1", "vid2"]
        status, msg = format_rss_status_message(
            "skip", mock_result, rss_missing_count=0,
            rss_error_msg=None, new_channel_skipped_rss=False
        )
        assert status == "skip"
        assert "2 unavailable" in msg

    def test_new_videos_message(self):
        """Format new videos message."""
        mock_result = Mock()
        mock_result.unavailable_video_ids = ["vid1"]
        status, msg = format_rss_status_message(
            "new_videos", mock_result, rss_missing_count=10,
            rss_error_msg=None, new_channel_skipped_rss=False
        )
        assert status == "new_videos"
        # 10 available + 1 unavailable = 11 total
        assert msg == "discovered 11 new videos not in db (10 available, 1 unavailable)"

    def test_new_videos_new_channel(self):
        """Format message for new channel."""
        status, msg = format_rss_status_message(
            "new_videos", None, rss_missing_count=5,
            rss_error_msg=None, new_channel_skipped_rss=True
        )
        assert status == "new_videos"
        assert msg == "new channel, switching to yt-api for full scan"

    def test_gap_detected_message(self):
        """Format gap detected message."""
        status, msg = format_rss_status_message(
            "gap_detected", None, rss_missing_count=5,
            rss_error_msg=None, new_channel_skipped_rss=False
        )
        assert status == "gap_detected"
        assert "gaps detected" in msg

    def test_error_message(self):
        """Format error message - used when status is not a recognized type."""
        # rss_error_msg is only used when status is NOT skip/new_videos/gap_detected
        # and no rss_result.message exists
        status, msg = format_rss_status_message(
            "error", None, rss_missing_count=None,
            rss_error_msg="RSS request failed", new_channel_skipped_rss=False
        )
        assert status == "skip"
        assert "RSS request failed" in msg

    def test_rss_result_message(self):
        """Format message from RSS result message attribute."""
        mock_result = Mock()
        mock_result.message = "feed unavailable"
        mock_result.unavailable_video_ids = []
        # When rss_result has a message and status is not skip/new_videos/gap_detected,
        # the message should be used
        status, msg = format_rss_status_message(
            "error", mock_result, rss_missing_count=None,
            rss_error_msg=None, new_channel_skipped_rss=False
        )
        assert status == "skip"
        assert "feed unavailable" in msg


class TestRssMessageImprovedFormat:
    """Tests for improved RSS message format to be more descriptive."""

    def test_new_videos_single_uses_discovered_wording(self):
        """Single new video should say 'discovered 1 new video not in db'."""
        status, msg = format_rss_status_message(
            "new_videos", None, rss_missing_count=1,
            rss_error_msg=None, new_channel_skipped_rss=False
        )
        assert status == "new_videos"
        assert msg == "discovered 1 new video not in db"

    def test_new_videos_multiple_uses_discovered_wording(self):
        """Multiple new videos should say 'discovered X new videos not in db'."""
        status, msg = format_rss_status_message(
            "new_videos", None, rss_missing_count=5,
            rss_error_msg=None, new_channel_skipped_rss=False
        )
        assert status == "new_videos"
        assert msg == "discovered 5 new videos not in db"

    def test_new_videos_with_unavailable_shows_breakdown(self):
        """New videos with unavailable should show detailed breakdown."""
        mock_result = Mock()
        mock_result.unavailable_video_ids = ["vid1", "vid2"]
        status, msg = format_rss_status_message(
            "new_videos", mock_result, rss_missing_count=8,
            rss_error_msg=None, new_channel_skipped_rss=False
        )
        assert status == "new_videos"
        # 8 available + 2 unavailable = 10 total
        assert msg == "discovered 10 new videos not in db (8 available, 2 unavailable)"


class TestPerformRssCheck:
    """Tests for perform_rss_check function."""

    def test_new_channel_skips_rss(self):
        """Skip RSS check for new channels (db_count=0)."""
        mock_checker = Mock()
        mock_log = Mock()

        result, skipped = perform_rss_check(
            channel_id="UC123",
            handle=None,
            resolved_url="https://youtube.com/@test",
            db_video_ids=set(),
            db_count=0,
            rss_checker=mock_checker,
            log_operation=mock_log,
            original_channel="@test",
        )

        assert result is None
        assert skipped is True
        mock_checker.check.assert_not_called()

    def test_existing_channel_performs_check(self):
        """Perform RSS check for existing channels."""
        mock_result = Mock()
        mock_result.status = "skip"
        mock_result.video_ids = []
        mock_checker = Mock()
        mock_checker.check = Mock(return_value=mock_result)
        mock_log = Mock()

        result, skipped = perform_rss_check(
            channel_id="UC123",
            handle="@test",
            resolved_url="https://youtube.com/@test",
            db_video_ids={"vid1", "vid2"},
            db_count=2,
            rss_checker=mock_checker,
            log_operation=mock_log,
            original_channel="@test",
        )

        assert result is not None
        assert skipped is False
        mock_checker.check.assert_called_once()

    def test_no_channel_id_skips_check(self):
        """Skip RSS check when channel_id is None."""
        mock_checker = Mock()
        mock_log = Mock()

        result, skipped = perform_rss_check(
            channel_id=None,
            handle=None,
            resolved_url="https://youtube.com/@test",
            db_video_ids=set(),
            db_count=0,
            rss_checker=mock_checker,
            log_operation=mock_log,
            original_channel="@test",
        )

        assert result is None
        assert skipped is True  # db_count=0, so skipped=True

