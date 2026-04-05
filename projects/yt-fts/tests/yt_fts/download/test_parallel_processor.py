"""
Unit tests for ParallelBatchProcessor.

Tests cover:
- WorkerStatus thread-safe counter operations
- ETA formatting
- Rate limit checking
- Initialization and configuration
- Empty result creation
"""

import threading
from unittest.mock import MagicMock, patch

import pytest

from yt_fts.download.parallel_processor import (
    ParallelBatchProcessor,
    WorkerStatus,
)
from yt_fts.download.time_utils import format_eta


class TestWorkerStatus:
    """Tests for WorkerStatus thread-safe counter."""

    def test_initialization(self):
        """WorkerStatus initializes with zero counters."""
        status = WorkerStatus()
        ok, err, skip, current = status.get_counts()
        assert ok == 0
        assert err == 0
        assert skip == 0
        assert current == ""

    def test_add_ok_increments_counter(self):
        """add_ok increments the success counter."""
        status = WorkerStatus()
        status.add_ok()
        status.add_ok(3)
        ok, _, _, _ = status.get_counts()
        assert ok == 4

    def test_add_err_increments_counter(self):
        """add_err increments the error counter."""
        status = WorkerStatus()
        status.add_err()
        status.add_err(2)
        _, err, _, _ = status.get_counts()
        assert err == 3

    def test_add_skip_increments_counter(self):
        """add_skip increments the skip counter."""
        status = WorkerStatus()
        status.add_skip()
        status.add_skip(5)
        _, _, skip, _ = status.get_counts()
        assert skip == 6

    def test_set_current_updates_channel(self):
        """set_current updates the current channel."""
        status = WorkerStatus()
        status.set_current("@testchannel")
        _, _, _, current = status.get_counts()
        assert current == "@testchannel"

    def test_get_counts_thread_safety(self):
        """Multiple threads can update counters safely."""
        status = WorkerStatus()
        num_threads = 10
        increments_per_thread = 100

        def increment_ok():
            for _ in range(increments_per_thread):
                status.add_ok()

        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=increment_ok)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        ok, _, _, _ = status.get_counts()
        assert ok == num_threads * increments_per_thread


class TestFormatEta:
    """Tests for format_eta function."""

    def test_negative_seconds_returns_unknown(self):
        """Negative seconds return 'unknown'."""
        assert format_eta(-1) == "unknown"
        assert format_eta(-100) == "unknown"

    def test_less_than_60_seconds(self):
        """Seconds less than 60 show as 'Xs'."""
        assert format_eta(0) == "0s"
        assert format_eta(30) == "30s"
        assert format_eta(59) == "59s"

    def test_minutes_format(self):
        """Seconds between 60 and 3600 show as 'Xm Ys'."""
        assert format_eta(60) == "1m"
        assert format_eta(90) == "1m 30s"
        assert format_eta(125) == "2m 5s"
        assert format_eta(3599) == "59m 59s"

    def test_hours_format(self):
        """Seconds 3600+ show as 'Xh Ym'."""
        assert format_eta(3600) == "1h"
        assert format_eta(3661) == "1h 1m"
        assert format_eta(7200) == "2h"
        assert format_eta(7261) == "2h 1m"


class TestParallelBatchProcessorInitialization:
    """Tests for ParallelBatchProcessor initialization."""

    def test_initialization_with_defaults(self):
        """Default values are set correctly."""
        processor = ParallelBatchProcessor()
        assert processor.language == "en"
        assert processor.cookies_from_browser is None
        assert processor.delay_between_channels == 3.0
        assert processor.max_retries == 3
        assert processor.continue_on_error is True
        assert processor.time_per_channel is None
        assert processor.time_per_video is None
        assert processor.time_per_batch is None
        assert processor.min_saved is None
        assert processor.videos_download_per_batch is None
        assert processor.auto_backfill is False
        assert processor.freshness_hours == 6
        assert processor.quota_strategy is None
        assert processor.use_rich_progress is False
        assert processor.use_fzf is False
        assert processor.use_json is False
        assert processor.video_jobs == 1
        assert processor.auto_adjust_video_jobs is False

    def test_initialization_with_custom_options(self):
        """Custom options override defaults."""
        processor = ParallelBatchProcessor(
            language="es",
            cookies_from_browser="firefox",
            delay_between_channels=5.0,
            max_retries=5,
            continue_on_error=False,
            time_per_channel=600,
            time_per_video=300,
            auto_backfill=True,
            freshness_hours=24,
            use_rich_progress=True,
            use_fzf=True,
            use_json=True,
            video_jobs=4,
        )
        assert processor.language == "es"
        assert processor.cookies_from_browser == "firefox"
        assert processor.delay_between_channels == 5.0
        assert processor.max_retries == 5
        assert processor.continue_on_error is False
        assert processor.time_per_channel == 600
        assert processor.time_per_video == 300
        assert processor.auto_backfill is True
        assert processor.freshness_hours == 24
        assert processor.use_rich_progress is True
        assert processor.use_fzf is True
        assert processor.use_json is True
        assert processor.video_jobs == 4

    def test_auto_adjust_video_jobs_creates_rate_limit_tracker(self):
        """When auto_adjust_video_jobs is True, RateLimitTracker is created."""
        with patch("yt_fts.download.parallel_processor.RateLimitTracker") as mock_tracker:
            processor = ParallelBatchProcessor(
                video_jobs=4,
                auto_adjust_video_jobs=True,
            )
            assert processor._rate_limit_tracker is not None
            mock_tracker.assert_called_once()

    def test_rate_limit_tracker_not_created_by_default(self):
        """By default, RateLimitTracker is not created."""
        processor = ParallelBatchProcessor()
        assert processor._rate_limit_tracker is None


class TestRateLimitChecking:
    """Tests for rate limit detection."""

    def test_check_for_rate_limit_429(self):
        """Detects 429 status code."""
        processor = ParallelBatchProcessor()
        result = {"failed": [{"error": "HTTP Error 429: Too Many Requests"}]}
        error = processor._check_for_rate_limit(result)
        assert error is not None
        assert "429" in error

    def test_check_for_rate_limit_too_many_requests(self):
        """Detects 'Too Many Requests' message."""
        processor = ParallelBatchProcessor()
        result = {"failed": [{"error": "Too Many Requests"}]}
        error = processor._check_for_rate_limit(result)
        assert error is not None
        assert "Too Many Requests" in error

    def test_check_for_rate_limit_rate_limit_string(self):
        """Detects 'rate limit' in error message."""
        processor = ParallelBatchProcessor()
        result = {"failed": [{"error": "rate limit exceeded"}]}
        error = processor._check_for_rate_limit(result)
        assert error is not None

    def test_check_for_rate_limit_quota_exceeded(self):
        """Detects 'quota exceeded' message."""
        processor = ParallelBatchProcessor()
        result = {"failed": [{"error": "quota exceeded"}]}
        error = processor._check_for_rate_limit(result)
        assert error is not None

    def test_check_for_rate_limit_none_when_no_indicators(self):
        """Returns None when no rate limit indicators present."""
        processor = ParallelBatchProcessor()
        result = {"failed": [{"error": "network timeout"}]}
        error = processor._check_for_rate_limit(result)
        assert error is None

    def test_check_for_rate_limit_case_insensitive(self):
        """Detection is case-insensitive."""
        processor = ParallelBatchProcessor()
        result = {"failed": [{"error": "RATE LIMIT Exceeded"}]}
        error = processor._check_for_rate_limit(result)
        assert error is not None


class TestMakeEmptyResult:
    """Tests for _make_empty_result method."""

    def test_make_empty_result_structure(self):
        """Creates proper empty result structure."""
        processor = ParallelBatchProcessor()
        result = processor._make_empty_result()
        assert "successful" in result
        assert "failed" in result
        assert "skipped" in result
        assert result["successful"] == []
        assert result["failed"] == []
        assert result["skipped"] == []


class TestOnVideoJobsChanged:
    """Tests for _on_video_jobs_changed callback."""

    def test_updates_video_jobs_attribute(self):
        """Callback updates video_jobs attribute."""
        processor = ParallelBatchProcessor(video_jobs=2)
        processor._on_video_jobs_changed(5)
        assert processor.video_jobs == 5


class TestProcessChannels:
    """Tests for process_channels method routing."""

    def test_empty_channels_returns_empty_result(self):
        """Empty channel list returns empty result."""
        processor = ParallelBatchProcessor()
        result = processor.process_channels([])
        assert result == {"successful": [], "failed": [], "skipped": []}

    def test_process_channels_routes_to_fzf_mode(self):
        """Routes to fzf mode when use_fzf is True."""
        processor = ParallelBatchProcessor(use_fzf=True)
        with patch.object(processor, "_process_channels_fzf") as mock_fzf:
            mock_fzf.return_value = {"successful": [], "failed": [], "skipped": []}
            processor.process_channels(["@test"], num_workers=2)
            mock_fzf.assert_called_once()

    def test_process_channels_routes_to_json_mode(self):
        """Routes to JSON mode when use_json is True."""
        processor = ParallelBatchProcessor(use_json=True)
        with patch.object(processor, "_process_channels_json") as mock_json:
            mock_json.return_value = {"successful": [], "failed": [], "skipped": []}
            processor.process_channels(["@test"], num_workers=2)
            mock_json.assert_called_once()

    def test_process_channels_routes_to_rich_mode(self):
        """Routes to Rich mode when use_rich_progress is True."""
        processor = ParallelBatchProcessor(use_rich_progress=True)
        with patch.object(processor, "_process_channels_with_rich") as mock_rich:
            mock_rich.return_value = {"successful": [], "failed": [], "skipped": []}
            processor.process_channels(["@test"], num_workers=2)
            mock_rich.assert_called_once()

    def test_process_channels_routes_to_simple_mode_default(self):
        """Routes to simple mode by default."""
        processor = ParallelBatchProcessor()
        with patch.object(processor, "_process_channels_simple") as mock_simple:
            mock_simple.return_value = {"successful": [], "failed": [], "skipped": []}
            processor.process_channels(["@test"], num_workers=2)
            mock_simple.assert_called_once()


class TestProcessChannelsJson:
    """Tests for _process_channels_json method."""

    def test_empty_channels_returns_empty_and_prints_empty_array(self):
        """Empty channels print '[]' and return empty result."""
        processor = ParallelBatchProcessor(use_json=True)
        with patch("builtins.print") as mock_print:
            result = processor._process_channels_json([], num_workers=2)
            assert result == {"successful": [], "failed": [], "skipped": []}
            calls = [str(call) for call in mock_print.call_args_list]
            assert any("[]" in call for call in calls)


class TestNotifyChannelCompletion:
    """Tests for _notify_channel_completion method."""

    def test_notify_without_rate_limit_tracker_does_nothing(self):
        """Does nothing when RateLimitTracker is not configured."""
        processor = ParallelBatchProcessor(auto_adjust_video_jobs=False)
        processor._notify_channel_completion("@test", {}, "✓")

    def test_notify_success_calls_on_success(self):
        """Success status calls tracker.on_success."""
        processor = ParallelBatchProcessor(auto_adjust_video_jobs=True)
        mock_tracker = MagicMock()
        processor._rate_limit_tracker = mock_tracker

        processor._notify_channel_completion("@test", {"successful": [], "failed": []}, "✓")
        mock_tracker.on_success.assert_called_once_with("@test")

    def test_notify_failure_with_rate_limit_calls_on_rate_limit(self):
        """Failure with rate limit error calls tracker.on_rate_limit."""
        processor = ParallelBatchProcessor(auto_adjust_video_jobs=True)
        mock_tracker = MagicMock()
        processor._rate_limit_tracker = mock_tracker

        result = {"failed": [{"error": "HTTP Error 429: Too Many Requests"}]}
        processor._notify_channel_completion("@test", result, "✗")
        mock_tracker.on_rate_limit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
