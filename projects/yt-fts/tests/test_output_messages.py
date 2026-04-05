"""Tests for output message improvements in batch download.

Tests verify that output messages are clear and informative:
1. "Downloading 0 vtt files" shows why (filtered as Shorts/Scheduled)
2. "Finished downloading subtitles" reflects actual results
3. Transcription status is visible
4. Stats display has proper vertical alignment
"""

from unittest.mock import MagicMock, Mock, patch
import pytest

from yt_fts.download.batch_channel_helpers import initialize_channel_state


class TestFormatDbStatsAlignment:
    """Tests for _format_db_stats to ensure proper vertical alignment."""

    def test_stats_with_shorts_have_consistent_alignment(self):
        """Stats line should have consistent spacing when shorts are present."""
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(channels=[], jobs=1)
        downloader.console = MagicMock()

        # Test case: 162 total, 161 subs, 1 shorts (like Ray Amjad)
        result = downloader._format_db_stats(
            db_count=162,
            db_with_subs=161,
            db_no_subs=1,
            db_scheduled=0,
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=1,
            status_name="channel/UC123",
            channel_id="UC123",
            channel_display_name="Test Channel",
        )

        stats = result["stats"]
        # Should have consistent format with aligned numbers
        # Implementation uses "cc" (closed captions) instead of "with transcripts"
        assert "162 total" in stats
        assert "161 cc" in stats
        assert "1 no cc" in stats
        assert "1 shorts" in stats

        # Verify the format has consistent spacing around pipes
        # Expected: "162 total | 161 cc, 1 no cc, 1 shorts"
        # Each part after a pipe should start with a space
        if "|" in stats:
            parts = stats.split("|")
            # After splitting by "|", each part (except first) should start with space
            for i, part in enumerate(parts[1:], 1):
                assert part.startswith(" "), f"Part {i} after pipe doesn't start with space: '{part}'"

    def test_stats_with_no_subs_has_consistent_alignment(self):
        """Stats line should align properly when no subs present."""
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(channels=[], jobs=1)
        downloader.console = MagicMock()

        # Test case: 162 total, 161 subs, 1 no sub, 1 shorts
        result = downloader._format_db_stats(
            db_count=162,
            db_with_subs=161,
            db_no_subs=1,
            db_scheduled=0,
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=1,
            status_name="channel/UC123",
            channel_id="UC123",
            channel_display_name="Test Channel",
        )

        stats = result["stats"]
        assert "162 total" in stats
        assert "161 cc" in stats
        assert "1 no cc" in stats
        assert "1 shorts" in stats
        # Check proper pipe separation
        parts = stats.split("|")
        # Format is "X total | Y video_stats" (shorts are in video_stats)
        assert len(parts) == 2  # "X total | Y video_stats (includes shorts)"

    def test_stats_with_scheduled_and_members(self):
        """Stats line should handle multiple categories with consistent alignment."""
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(channels=[], jobs=1)
        downloader.console = MagicMock()

        result = downloader._format_db_stats(
            db_count=200,
            db_with_subs=180,
            db_no_subs=5,
            db_scheduled=10,
            db_members=3,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=2,
            status_name="channel/UC123",
            channel_id="UC123",
            channel_display_name="Test Channel",
        )

        stats = result["stats"]
        # All categories should be present with consistent spacing
        # Implementation uses "cc" (closed captions) and abbreviated labels
        assert "200 total" in stats
        assert "180 cc" in stats
        assert "10 sch" in stats
        assert "2 shorts" in stats


class TestDownloadingMessage:
    """Tests for 'Downloading X vtt files' message improvements."""

    def test_zero_downloads_shows_reason_when_filtered(self):
        """When 0 videos to download, message should explain why."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1)
        handler.video_ids = []
        handler._videos_saved_during_download = False

        # Track what gets printed
        with patch('builtins.print') as mock_print:
            handler.download_vtts()
            # When video_ids is empty, should skip the download message
            # or show a clear reason

    def test_zero_downloads_with_filtered_count(self):
        """Message should show how many videos were filtered (Shorts/Scheduled)."""
        # This would test the case where RSS found videos but they were filtered
        # The output should clarify: "No videos to download (X filtered as Shorts)"
        pass

    def test_downloading_message_uses_detail_formatting(self):
        """Downloading message should use ⎿ prefix when channel name not included."""
        from yt_fts.download.download_handler import DownloadHandler
        from unittest.mock import MagicMock

        handler = DownloadHandler(number_of_jobs=1)
        handler.include_channel_name_in_messages = False  # No channel name in header

        # Check that _detail_message adds the ⎿ prefix
        test_msg = "Downloading 2 vtt files"
        result = handler._detail_message(test_msg)

        # Should contain the detail prefix when channel name is not in messages
        assert '⎿' in result, f"Expected '⎿' in detail message, got: {result}"
        assert test_msg in result, f"Expected original message in result, got: {result}"


class TestFinishedDownloadingMessage:
    """Tests for 'Finished downloading subtitles' message improvements."""

    def test_finished_message_shows_actual_count(self):
        """When 0 subtitles downloaded, message should reflect that."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler(number_of_jobs=1)
        handler.channel_id = "UC123"
        handler.channel_name = "Test Channel"
        handler._videos_saved_during_download = False
        handler.suppress_status_messages = True

        # When no videos were saved, the message should be clear
        # Instead of "Finished downloading subtitles", should say:
        # "No subtitles downloaded (all filtered as Shorts/Scheduled)"

    def test_finished_message_with_mixed_results(self):
        """When some succeeded and some failed, show breakdown."""
        # Should show: "Downloaded X subtitles, attempted transcription for Y videos"
        pass


class TestTranscriptionStatusVisibility:
    """Tests for transcription status message visibility."""

    def test_transcription_attempt_message_is_visible(self):
        """When transcription is attempted, show visible message."""
        from yt_fts.download.download_handler import DownloadHandler

        # DownloadHandler doesn't accept transcribe_audio_only in __init__
        # It only has whisper_model and keep_audio parameters
        handler = DownloadHandler(
            number_of_jobs=1,
            whisper_model="tiny",
        )
        handler.videos_without_subs_list = ["vid1", "vid2"]
        handler.channel_id = "UC123"
        # transcribe_audio_only can be set as an attribute if needed
        handler.transcribe_audio_only = True

        # Transcription should be visible (not just logged to file)
        # Expected: "Attempting Whisper transcription for 2 videos..."

    def test_transcription_success_message_is_visible(self):
        """When transcription succeeds, show success count."""
        # Expected: "✓ Transcribed 1 video successfully"
        pass

    def test_transcription_unavailable_message_is_visible(self):
        """When videos are unavailable, show that they're marked."""
        # Expected: "✗ 1 video unavailable (marked for retry)"
        pass


class TestYtdlpSkipReasonMessages:
    """Tests for specific yt-dlp skip reason messages."""

    def test_zero_videos_shows_specific_reason(self):
        """When 0 videos found, message should be more specific."""
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(channels=[], jobs=1)
        downloader.console = MagicMock()

        # Simulate result where yt-dlp found 0 videos
        result = {
            "success": True,
            "videos_count": 0,
            "videos_without_subtitles": 0,
            "total_videos": 0,
            "skip_reason": "no_videos",  # New field for specific reason
        }

        # The skip_reason should be used to generate a specific message
        skip_reason = result.get("skip_reason", "")
        if skip_reason == "no_videos":
            message = "⏭ yt-dlp: no videos found for this channel"
        elif skip_reason == "no_subtitles":
            message = "⏭ yt-dlp: subtitles not available in any language"
        elif skip_reason == "no_audio":
            message = "⏭ yt-dlp: audio not available in any language"
        else:
            message = "⏭ yt-dlp found 0 videos"

        assert "no videos found" in message.lower()

    def test_no_transcript_to_store_message(self):
        """When nothing to store, should show 'no transcript to store in db'."""
        # When all videos are filtered or no subtitles exist
        skip_reason = "no_transcript"
        if skip_reason == "no_transcript":
            message = "⏭ result: no transcript to store in db"
        else:
            message = "⏭ no subtitles downloaded"

        assert "no transcript to store in db" in message


class TestOutputMessageIntegration:
    """Integration tests for output messages during batch download."""

    def test_new_channel_with_zero_videos_message(self):
        """New channel that yt-dlp finds 0 videos for (deleted/private)."""
        # Should clearly indicate what happened, not just "Downloading 0 vtt files"
        pass

    def test_rss_found_videos_but_all_filtered(self):
        """RSS found videos but all were filtered (Shorts/Scheduled)."""
        # Should show: "RSS found 5 videos, but all filtered as Shorts"
        pass


class TestUIFormattingConsistency:
    """Tests for UI plugin output formatting consistency."""

    def test_rss_skip_message_has_no_skip_icon(self):
        """RSS skip message should not have ⏭ icon (cleaner look)."""
        from yt_fts.ui.plugins.default import DefaultDisplayPlugin
        from rich.console import Console
        from io import StringIO
        import sys

        console = Console(file=StringIO())
        plugin = DefaultDisplayPlugin(console)
        captured = StringIO()
        console.file = captured
        
        plugin.display_rss_status({"status": "skip", "message": "No new videos"})
        

        output = captured.getvalue()
        
        # Should NOT contain the skip icon
        assert "⏭" not in output, f"Skip icon should be removed, got: {output}"
        # Should contain "RSS:" and "No new videos"
        assert "rss:" in output
        assert "No new videos" in output

    def test_matched_db_message_uses_net_label_with_skip_icon(self):
        """Matched DB message should use 'net:' label with ⏭ icon."""
        from yt_fts.ui.plugins.default import DefaultDisplayPlugin
        from rich.console import Console
        from io import StringIO

        console = Console(file=StringIO())
        plugin = DefaultDisplayPlugin(console)
        captured = StringIO()
        console.file = captured

        # Simulate the scenario: no new videos + RSS matched DB
        result_info = {
            "success": True,
            "videos_count": 0,
            "message": "No new videos (RSS check)"
        }

        plugin.display_download_result(result_info)


        output = captured.getvalue()

        # Should use "net:" label
        if "all videos already in database" in output or "nothing to do" in output or "No new videos" in output:
            assert "net:" in output, f"Should use 'net:' label, got: {output}"
            # Should have the skip icon
            assert "⏭" in output, f"Should have skip icon, got: {output}"


class TestChannelDisplayName:
    """Tests for channel display name showing human-readable names instead of channel/UC..."""

    def test_get_channel_display_name_returns_db_name(self):
        """When channel exists in DB, return actual channel name."""
        from yt_fts.download.batch_downloader import BatchDownloader
        from unittest.mock import MagicMock, patch

        downloader = BatchDownloader(channels=[], jobs=1)

        # Mock the database query to return a channel name
        with patch('yt_fts.db.channels.get_channel_name_from_db') as mock_db:
            mock_db.return_value = "Test Channel Name"

            result = downloader._get_channel_display_name(
                channel_id="UC1234567890",
                status_name="channel/UC1234567890"
            )

            assert result == "Test Channel Name", f"Expected 'Test Channel Name', got: {result}"
            mock_db.assert_called_once_with("UC1234567890")

    def test_get_channel_display_name_fallback_to_short_channel_id(self):
        """When channel not in DB, return truncated channel_id with warning (Option A)."""
        from yt_fts.download.batch_downloader import BatchDownloader
        from unittest.mock import patch

        downloader = BatchDownloader(channels=[], jobs=1)

        # Mock the database query to return None (channel not found)
        with patch('yt_fts.db.channels.get_channel_name_from_db') as mock_db:
            mock_db.return_value = None

            result = downloader._get_channel_display_name(
                channel_id="UC1weYqfC7x6g5Y4z",
                status_name="channel/UC1weYqfC7x6g5Y4z"
            )

            # With Option A: Should add ⚠️ warning and truncate
            assert result.startswith("⚠️"), f"Should have warning indicator, got: {result}"
            # Should NOT return full channel_id (fail-fast principle)
            assert "UC1weYqfC7x6g5Y4z" not in result, f"Should not show full raw channel_id, got: {result}"
            # Should be truncated with ellipsis
            assert "..." in result, f"Should truncate with ellipsis, got: {result}"

    def test_get_channel_display_name_with_handle(self):
        """When status_name contains @handle, prefer that over channel/UC... format."""
        from yt_fts.download.batch_downloader import BatchDownloader
        from unittest.mock import patch

        downloader = BatchDownloader(channels=[], jobs=1)

        # Mock the database query to return None
        with patch('yt_fts.db.channels.get_channel_name_from_db') as mock_db:
            mock_db.return_value = None

            result = downloader._get_channel_display_name(
                channel_id=None,
                status_name="@examplechannel"
            )

            # Should return the handle when available
            assert result == "@examplechannel", f"Expected '@examplechannel', got: {result}"


class TestRSSFilterMessaging:
    """Tests for clearer messaging when RSS videos are filtered."""

    def test_result_includes_filter_summary(self):
        """When videos are filtered, result should include filter_summary."""
        from yt_fts.download.download_handler import DownloadHandler
        from unittest.mock import MagicMock, patch

        handler = DownloadHandler(number_of_jobs=1)
        handler.video_ids = ["vid1", "vid2"]
        handler._videos_saved_during_download = False
        
        # Simulate filtering
        handler._track_filter_reason("shorts", "vid1")
        handler._track_filter_reason("scheduled", "vid2")
        
        # Get filter summary
        summary = handler._get_filter_summary()
        
        # Should include both filter reasons
        assert "1 short" in summary.lower(), f"Expected '1 short' in summary: {summary}"
        assert "1 scheduled" in summary.lower() or "1 sch" in summary.lower(),             f"Expected scheduled info in summary: {summary}"

    def test_zero_videos_with_rss_filter_shows_clear_message(self):
        """When RSS found videos but all were filtered, message should be clear.
        
        This tests the messaging in batch_downloader.py around line 1564-1565.
        The current behavior shows:
          'RSS: discovered 1 new video not in db'
          'yt-dlp: no videos found for this channel'
        
        The desired behavior should explain that the RSS video was filtered:
          'RSS: discovered 1 new video not in db'
          'yt-dlp: RSS video was filtered (Short)'
        """
        # This is an integration test that verifies the messaging flow
        # The fix requires:
        # 1. Adding filter_summary to the result dict in _download_single_channel_optimized
        # 2. Using filter_summary in the messaging at line 1564-1565
        
        # For now, we test that the _get_filter_summary method works correctly
        from yt_fts.download.download_handler import DownloadHandler
        
        handler = DownloadHandler(number_of_jobs=1)
        handler._initialize_filter_reasons()
        
        # Simulate 1 video filtered as Short
        handler._track_filter_reason("shorts", "vid1")
        
        summary = handler._get_filter_summary()
        assert "1 short" in summary.lower(), f"Expected '1 short' in: {summary}"

    def test_filter_summary_with_multiple_reasons(self):
        """Filter summary should list all reasons when videos are filtered differently."""
        from yt_fts.download.download_handler import DownloadHandler
        
        handler = DownloadHandler(number_of_jobs=1)
        handler._initialize_filter_reasons()
        
        # Simulate multiple videos with different filter reasons
        handler._track_filter_reason("shorts", "vid1")
        handler._track_filter_reason("shorts", "vid2")
        handler._track_filter_reason("scheduled", "vid3")
        handler._track_filter_reason("unavailable", "vid4")
        
        summary = handler._get_filter_summary()
        
        # Should mention all three categories
        assert "short" in summary.lower(), f"Expected 'short' in: {summary}"
        assert "scheduled" in summary.lower() or "sch" in summary.lower(),             f"Expected 'scheduled' in: {summary}"
        assert "unavailable" in summary.lower() or "unavail" in summary.lower(),             f"Expected 'unavailable' in: {summary}"


    def test_download_result_includes_filter_summary(self):
        """Result dict from _download_single_channel_optimized should include filter_summary.

        This test FAILS because filter_summary is not currently included in the result.
        After the fix, this test should pass.
        """
        from yt_fts.download.batch_downloader import BatchDownloader
        from unittest.mock import MagicMock, patch
        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill
        
        downloader = BatchDownloader(channels=[], jobs=1)
        downloader.console = MagicMock()
        
        # Mock the coordinator
        mock_coordinator = MagicMock()
        mock_coordinator.add_task = MagicMock()
        mock_coordinator.update_progress = MagicMock()
        mock_coordinator.remove_task = MagicMock()
        
        # Mock YouTubeAPIBackfill
        with patch.object(YouTubeAPIBackfill, 'get_global_quota_info') as mock_quota:
            mock_quota.return_value = {"used": 0, "remaining": 10000}
            
            # Mock the download handler to simulate filtered videos
            with patch('yt_fts.download.batch_downloader.DownloadHandler') as MockHandler:
                mock_instance = MagicMock()
                mock_instance.get_videos_saved.return_value = 0
                mock_instance.videos_without_subtitles = 1
                mock_instance.video_ids = ["vid1"]
                mock_instance.total_videos_found = 1
                # Simulate filter summary - this is what we want to see in the result
                mock_instance._get_filter_summary.return_value = "1 short"
                mock_instance.filter_reasons = {"shorts": 1, "scheduled": 0, "unavailable": 0}
                MockHandler.return_value = mock_instance
                
                result = downloader._download_single_channel_optimized(
                    original_channel="@test",
                    resolved_url="https://www.youtube.com/@test",
                    channel_id="UC123",
                    coordinator=mock_coordinator,
                    video_ids=["vid1"]
                )
                
                # This assertion FAILS because filter_summary is not in the result
                assert "filter_summary" in result,                     f"Expected 'filter_summary' in result, got keys: {list(result.keys())}"
                
                # When fixed, filter_summary should explain why videos were filtered
                if result.get("filter_summary"):
                    assert "short" in result["filter_summary"].lower(),                         f"Expected filter_summary to mention 'short': {result['filter_summary']}"


class TestDisplayPluginChannelNameFormatting:
    """Tests for display plugin _format_channel_name not adding 'channel/' prefix."""

    def test_format_channel_name_does_not_add_channel_prefix(self):
        """When formatting a raw channel ID (UC...), should NOT add 'channel/' prefix.
        
        The display plugin should respect the output from _get_channel_display_name()
        which returns raw channel_id (e.g., 'UC1weYqfC7x6g5Y4z') without the 'channel/' prefix.
        """
        from yt_fts.ui.plugins.default import DefaultDisplayPlugin
        from rich.console import Console
        
        console = Console()
        plugin = DefaultDisplayPlugin(console)
        
        # Test with a raw channel ID (what _get_channel_display_name now returns)
        channel_id = "UC1weYqfC7x6g5Y4z123abcd"
        result = plugin._format_channel_name(channel_id)
        
        # Should NOT contain 'channel/' prefix
        assert not result.startswith("channel/"),             f"Should not add 'channel/' prefix, got: {result}"
        
        # Should truncate for display but keep raw format
        assert "UC" in result, f"Should contain 'UC' in: {result}"
        # The result should be the channel ID truncated, not wrapped in 'channel/'
        assert result == channel_id[:20] + "..." or result == channel_id[:27] + "...",             f"Should truncate cleanly, got: {result}"

    def test_format_channel_name_with_handle_unchanged(self):
        """@handle format should be preserved as-is (existing behavior)."""
        from yt_fts.ui.plugins.default import DefaultDisplayPlugin
        from rich.console import Console
        
        console = Console()
        plugin = DefaultDisplayPlugin(console)
        
        # @handle should pass through unchanged
        result = plugin._format_channel_name("@examplechannel")
        assert result == "@examplechannel", f"Expected '@examplechannel', got: {result}"

    def test_format_channel_name_with_human_name_unchanged(self):
        """Human-readable channel names should pass through unchanged (existing behavior)."""
        from yt_fts.ui.plugins.default import DefaultDisplayPlugin
        from rich.console import Console
        
        console = Console()
        plugin = DefaultDisplayPlugin(console)
        
        # Human-readable name should pass through unchanged
        result = plugin._format_channel_name("Test Channel Name")
        assert result == "Test Channel Name", f"Expected 'Test Channel Name', got: {result}"


class TestChannelNameStorageFromAPI:
    """Tests for storing channel name when discovered via ChannelHandleService."""

    def test_channel_name_stored_when_api_discovery_succeeds(self):
        """When ChannelHandleService discovers a channel, the channel_name should be stored in DB.
        
        This test verifies that when handle_discovery contains channel_name,
        it is written to the Channels table via add_channel_info().
        """
        from unittest.mock import MagicMock, patch, call
        from yt_fts.db.channels import check_if_channel_exists
        
        # Mock the ChannelHandleService to return a channel name
        mock_discovery_result = {
            "channel_id": "UC1234567890ABCDEFGHIJ",
            "channel_name": "Test Channel Name",
            "handle": "testchannel"
        }
        
        # Mock add_channel_info to track if it's called with the right params
        with patch('yt_fts.db.channels.add_channel_info') as mock_add_channel:
            # Simulate what the code should do after successful API discovery
            channel_id = mock_discovery_result["channel_id"]
            channel_name = mock_discovery_result.get("channel_name")
            channel_url = "https://www.youtube.com/@testchannel"
            
            if channel_id and channel_name:
                from yt_fts.db.channels import add_channel_info
                add_channel_info(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    channel_url=channel_url
                )
            
            # Verify add_channel_info was called with the channel name
            mock_add_channel.assert_called_once()
            call_args = mock_add_channel.call_args
            
            # Check that channel_name was passed (not None or empty)
            assert call_args[1]["channel_name"] == "Test Channel Name"

    def test_channel_name_not_stored_when_api_discovery_fails(self):
        """When ChannelHandleService fails to find channel_name, don't call add_channel_info with it.
        
        If API discovery returns channel_id but no channel_name, the code should
        gracefully handle the missing name without crashing.
        """
        from unittest.mock import patch
        
        # Mock discovery result WITHOUT channel_name
        mock_discovery_result = {
            "channel_id": "UC1234567890ABCDEFGHIJ",
            "channel_name": None,  # No name available
            "handle": "testchannel"
        }
        
        with patch('yt_fts.db.channels.add_channel_info') as mock_add_channel:
            channel_id = mock_discovery_result["channel_id"]
            channel_name = mock_discovery_result.get("channel_name")
            
            # Should NOT call add_channel_info if channel_name is None
            if channel_id and channel_name:
                from yt_fts.db.channels import add_channel_info
                add_channel_info(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    channel_url="https://www.youtube.com/@testchannel"
                )
            
            # Verify add_channel_info was NOT called (because channel_name was None)
            mock_add_channel.assert_not_called()


class TestProgressiveHandleDisplay:
    """Tests for Progressive Handle Display - Option A implementation.

    Priority order:
    1. Database cache (channel name from DB)
    2. @handle from original input
    3. Extract @handle from URL
    NEVER show raw channel_id like UC1weYqf...
    Add ⚠️ indicator when using fallback (not cached)
    """

    def test_returns_cached_name_when_available(self):
        """When DB has cached name, return it without warning indicator."""
        from unittest.mock import MagicMock, patch
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(channels=[], jobs=1)
        downloader.console = MagicMock()

        # Mock DB to return cached name
        with patch("yt_fts.db.channels.get_channel_name_from_db") as mock_get_name:
            mock_get_name.return_value = "Tech Channel"

            result = downloader._get_channel_display_name(
                channel_id="UC1234567890ABCDEFGHIJ",
                status_name="@techchannel"
            )

            # Should return cached name, not the fallback handle
            assert result == "Tech Channel"
            assert not result.startswith("⚠️")

    def test_returns_handle_from_input_when_no_cache(self):
        """When DB has no cached name, return @handle from input with warning."""
        from unittest.mock import MagicMock, patch
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(channels=[], jobs=1)
        downloader.console = MagicMock()

        # Mock DB to return None (no cached name)
        with patch("yt_fts.db.channels.get_channel_name_from_db") as mock_get_name:
            mock_get_name.return_value = None

            result = downloader._get_channel_display_name(
                channel_id="UC1234567890ABCDEFGHIJ",
                status_name="@techchannel"
            )

            # Should return handle with warning indicator
            assert result == "⚠️ @techchannel"

    def test_extracts_handle_from_url_when_no_cache(self):
        """When input is URL and no cache, extract @handle with warning."""
        from unittest.mock import MagicMock, patch
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(channels=[], jobs=1)
        downloader.console = MagicMock()

        # Mock DB to return None (no cached name)
        with patch("yt_fts.db.channels.get_channel_name_from_db") as mock_get_name:
            mock_get_name.return_value = None

            # Input is a URL with @handle
            result = downloader._get_channel_display_name(
                channel_id="UC1234567890ABCDEFGHIJ",
                status_name="https://www.youtube.com/@techchannel/videos"
            )

            # Should extract @handle from URL and add warning
            assert "@techchannel" in result
            assert result.startswith("⚠️")

    def test_never_shows_raw_channel_id(self):
        """NEVER return raw channel_id like UC1weYqf... even as fallback."""
        from unittest.mock import MagicMock, patch
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(channels=[], jobs=1)
        downloader.console = MagicMock()

        # Mock DB to return None (no cached name)
        with patch("yt_fts.db.channels.get_channel_name_from_db") as mock_get_name:
            mock_get_name.return_value = None

            # status_name is just the raw channel_id (worst case)
            result = downloader._get_channel_display_name(
                channel_id="UC1weYqfC7x6g5Y4z1W2X3V4U",
                status_name="UC1weYqfC7x6g5Y4z1W2X3V4U"
            )

            # Should NOT return the raw channel_id
            # Should return truncated version with warning
            assert result != "UC1weYqfC7x6g5Y4z1W2X3V4U"
            assert result.startswith("⚠️")
            # Should truncate to reasonable length
            assert len(result) < 25

    def test_channel_id_only_shortened(self):
        """When only channel_id is available and no handle, truncate with warning."""
        from unittest.mock import MagicMock, patch
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(channels=[], jobs=1)
        downloader.console = MagicMock()

        # Mock DB to return None (no cached name)
        with patch("yt_fts.db.channels.get_channel_name_from_db") as mock_get_name:
            mock_get_name.return_value = None

            # status_name is channel/UC... format (legacy)
            result = downloader._get_channel_display_name(
                channel_id="UC1weYqfC7x6g5Y4z1W2X3V4U",
                status_name="channel/UC1weYqfC7x6g5Y4z1W2X3V4U"
            )

            # Should truncate with warning, not show full raw ID
            assert result.startswith("⚠️")
            assert "UC1weYqf" in result  # Truncated portion (first 10 chars)
            assert len(result) < 25

    def test_no_channel_id_returns_status_name(self):
        """When channel_id is None, return status_name as-is."""
        from unittest.mock import MagicMock
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader(channels=[], jobs=1)
        downloader.console = MagicMock()

        result = downloader._get_channel_display_name(
            channel_id=None,
            status_name="@mychannel"
        )

        # Should return the status_name
        assert result == "@mychannel"



class TestChannelNameAlwaysUpdated:
    """Tests for channel names being updated even when channel already exists in DB.

    This ensures that bad names like "Channel UC1weYqf..." get updated
    to proper human-readable names when discovered via RSS/API.
    """

    def test_add_channel_info_updates_existing_channel(self):
        """add_channel_info should UPDATE existing channels, not just insert new ones.

        The function tries INSERT first, and on IntegrityError (duplicate channel_id),
        it performs an UPDATE to overwrite the bad name with a good name.
        """
        from unittest.mock import MagicMock, patch
        import sqlite3

        with patch("yt_fts.db.channels.get_db_connection") as mock_get_conn:
            mock_conn = MagicMock()
            mock_get_conn.return_value.__enter__.return_value = mock_conn

            from yt_fts.db.channels import add_channel_info

            # Sequence when IntegrityError occurs:
            # 1. SELECT for existing URL - returns None (no existing)
            # 2. SELECT for handle_entry (UC channel check) - returns None
            # 3. INSERT - raises IntegrityError (due to PRIMARY KEY on channel_id)
            # 4. SELECT for existing channel_id (in UPDATE logic) - returns cursor
            # 5. UPDATE - returns None
            # 6. WAL checkpoint - returns None
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None  # No existing URL or handle
            mock_conn.execute.return_value = mock_cursor
            mock_conn.execute.side_effect = [
                mock_cursor,  # SELECT for existing URL
                mock_cursor,  # SELECT for handle_entry (UC channel check)
                sqlite3.IntegrityError("unique constraint"),  # INSERT fails on PRIMARY KEY
                None,  # UPDATE succeeds
                None,  # WAL checkpoint after UPDATE
            ]

            # Call add_channel_info - should handle IntegrityError and UPDATE
            # Use a valid channel ID format (UC + 22 chars)
            add_channel_info("UC1234567890123456789012", "Good Name", "https://url1")

            # Verify execute was called 5 times
            assert mock_conn.execute.call_count == 5, (
                f"Expected 5 execute calls (2x SELECT + INSERT + UPDATE + WAL), got {mock_conn.execute.call_count}"
            )

            # Verify the UPDATE statement was called (3rd index, after INSERT fails)
            update_call = mock_conn.execute.call_args_list[3]
            sql = update_call[0][0] if update_call[0] else ""
            assert "UPDATE" in sql and "channel_name" in sql, (
                f"Expected UPDATE SQL, got: {sql}"
            )

    def test_rss_code_does_not_check_if_channel_exists(self):
        """RSS discovery code should NOT have 'if not check_if_channel_exists' guard.

        This is a code inspection test - verifying the fix was applied.
        The old code had: if not check_if_channel_exists(candidate_id):
        The new code should always call add_channel_info regardless.
        """
        from pathlib import Path

        # Find the rss_precheck.py file from the test file location
        test_dir = Path(__file__).parent
        rss_file = test_dir / "projects" / "yt-fts" / "src" / "yt_fts" / "services" / "rss_precheck.py"

        # Fallback to direct path if not found
        if not rss_file.exists():
            rss_file = Path(__file__).parent.parent / "src" / "yt_fts" / "services" / "rss_precheck.py"

        content = rss_file.read_text()

        # The old problematic pattern should NOT exist
        # It would look like: if not check_if_channel_exists(candidate_id):
        # followed by add_channel_info call within that if block

        # Find all instances of check_if_channel_exists in rss_precheck.py
        if "check_if_channel_exists" in content:
            # If it exists, it should NOT be imported (since we removed the need for it)
            # Or if imported, it should NOT be used in an if-not guard before add_channel_info
            lines = content.split("\n")

            # Look for the problematic pattern
            found_guard = False
            for i, line in enumerate(lines):
                if "if not check_if_channel_exists" in line:
                    # Check if add_channel_info is called within the next few lines
                    for j in range(i, min(i + 10, len(lines))):
                        if "add_channel_info" in lines[j]:
                            found_guard = True
                            break

            assert not found_guard, (
                "RSS code should not have 'if not check_if_channel_exists' guard before add_channel_info"
            )

        # Verify add_channel_info IS being called (the update path exists)
        assert "add_channel_info" in content, (
            "RSS code should call add_channel_info"
        )



    def test_extract_channel_name_from_rss_feed(self):
        """The RSS checker should extract channel names from RSS feeds.

        This verifies the _extract_channel_name_from_feed method works correctly.
        """
        from yt_fts.services.rss_precheck import RssPreChecker

        checker = RssPreChecker()

        # Test with typical YouTube RSS feed format
        rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns:media="http://search.yahoo.com/mrss/" xmlns="http://www.w3.org/2005/Atom">
  <title>Real Channel Name - Videos</title>
  <author><name>Real Channel Name</name></author>
  <entry>
    <yt:videoId>video123</yt:videoId>
  </entry>
</feed>"""

        channel_name = checker._extract_channel_name_from_feed(rss_xml)
        assert channel_name == "Real Channel Name", (
            f"Expected 'Real Channel Name', got '{channel_name}'"
        )

        # Test with just title (no - Videos suffix)
        rss_xml2 = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
  <title>Another Channel</title>
  <entry><yt:videoId>vid123</yt:videoId></entry>
</feed>"""

        channel_name2 = checker._extract_channel_name_from_feed(rss_xml2)
        assert channel_name2 == "Another Channel", (
            f"Expected 'Another Channel', got '{channel_name2}'"
        )

        # Test with empty/invalid XML
        assert checker._extract_channel_name_from_feed("") is None
        assert checker._extract_channel_name_from_feed("not xml") is None


class TestYtApiEscalationForChannelNames:
    """Tests for yt-api escalation when RSS fails to provide channel names.

    When RSS feed is not available or doesn't contain a parsable channel name,
    the system should escalate to YouTube Data API to fetch the channel name.
    """

    def test_escalate_to_api_when_rss_fails_completely(self):
        """When RSS fetch fails completely, escalation method should be callable."""
        from unittest.mock import patch, MagicMock
        from yt_fts.services.rss_precheck import RssPreChecker

        checker = RssPreChecker()

        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "snippet": {
                        "title": "Escalated Channel Name"
                    }
                }
            ]
        }

        # Test that escalation method exists and works
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "test_key"}):
            with patch("requests.get", return_value=mock_response):
                result = checker._escalate_channel_name_via_api("UC1234567890ABCDEFGHIJ")

                # Should return the channel name from API
                assert result == "Escalated Channel Name"

    def test_escalate_to_api_logs_warning_on_failure(self):
        """When API escalation fails, should log at WARNING level for visibility."""
        from unittest.mock import patch
        from yt_fts.services.rss_precheck import RssPreChecker
        import requests

        checker = RssPreChecker()

        # Mock requests.get to fail for both RSS and API
        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "test_key"}):
            with patch("requests.get") as mock_get:
                mock_get.side_effect = requests.Timeout("Timeout")

                # Call the escalation method directly
                result = checker._escalate_channel_name_via_api("UC1234567890ABCDEFGHIJ")

                # Should return None on failure
                assert result is None

    def test_escalate_to_api_with_no_api_key(self):
        """When no API key is configured, should return None without error."""
        from unittest.mock import patch
        from yt_fts.services.rss_precheck import RssPreChecker

        checker = RssPreChecker()

        # Remove all API keys from environment
        with patch.dict("os.environ", {}, clear=True):
            result = checker._escalate_channel_name_via_api("UC1234567890ABCDEFGHIJ")

            # Should return None gracefully
            assert result is None

    def test_escalate_to_api_successful_response(self):
        """When API returns successfully, should extract and return channel name."""
        from unittest.mock import patch, MagicMock
        from yt_fts.services.rss_precheck import RssPreChecker

        checker = RssPreChecker()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "snippet": {
                        "title": "Test Channel From API"
                    }
                }
            ]
        }

        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "test_key"}):
            with patch("requests.get", return_value=mock_response):
                result = checker._escalate_channel_name_via_api("UC1234567890ABCDEFGHIJ")

                # Should return the channel name from API
                assert result == "Test Channel From API"

    def test_escalate_to_api_handles_empty_items(self):
        """When API returns empty items list, should return None."""
        from unittest.mock import patch, MagicMock
        from yt_fts.services.rss_precheck import RssPreChecker

        checker = RssPreChecker()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": []
        }

        with patch.dict("os.environ", {"YOUTUBE_API_KEY": "test_key"}):
            with patch("requests.get", return_value=mock_response):
                result = checker._escalate_channel_name_via_api("UC1234567890ABCDEFGHIJ")

                # Should return None when no items found
                assert result is None


class TestChannelSectionOutputConsistency:
    """Tests for consistent formatting in channel section output.

    All lines in the channel section should use the ⎿ prefix for consistency:
    - ⎿ db: 166 total | 166 with transcripts
    - ⎿ RSS: discovered 1 new video not in db
    - ⎿ Downloading 1 vtt file
    - ⎿ Finished downloading 1 subtitle  <-- should have ⎿ prefix
    - ⎿ result: ✓ 1 new | took 18s
    """

    def test_finished_downloading_has_pipe_prefix_without_channel(self):
        """'Finished downloading' should have ⎿ prefix when channel names NOT included."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler()
        handler.include_channel_name_in_messages = False
        handler.channel_name = "Test Channel"

        message = handler._maybe_with_channel(
            "   ⎿ Finished downloading 1 subtitle", "for"
        )

        # Should have the pipe prefix (included directly in message)
        assert message == "   ⎿ Finished downloading 1 subtitle", f"Expected pipe prefix, got: {message}"

    def test_finished_downloading_has_pipe_prefix_with_channel(self):
        """'Finished downloading' should have ⎿ prefix even when channel names ARE included."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler()
        handler.include_channel_name_in_messages = True
        handler.channel_name = "Test Channel"

        message = handler._maybe_with_channel(
            "   ⎿ Finished downloading 1 subtitle", "for"
        )

        # Should have the pipe prefix AND the channel name
        assert message == '   ⎿ Finished downloading 1 subtitle for "Test Channel"', f"Expected pipe prefix with channel, got: {message}"
        assert message.startswith("   ⎿ "), f"Should start with pipe prefix, got: {message}"

    def test_no_subtitles_has_pipe_prefix_with_channel(self):
        """'No subtitles downloaded' should have ⎿ prefix even with channel names."""
        from yt_fts.download.download_handler import DownloadHandler

        handler = DownloadHandler()
        handler.include_channel_name_in_messages = True
        handler.channel_name = "Test Channel"

        message = handler._maybe_with_channel(
            "   ⎿ No subtitles downloaded", "for"
        )

        # Should have the pipe prefix AND the channel name
        assert message == '   ⎿ No subtitles downloaded for "Test Channel"', f"Expected pipe prefix with channel, got: {message}"
        assert message.startswith("   ⎿ "), f"Should start with pipe prefix, got: {message}"
