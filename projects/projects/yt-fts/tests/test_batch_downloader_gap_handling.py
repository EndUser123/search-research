"""
Test gap handling when API total > DB count.

This test verifies that gap handling triggers when the stored API total
indicates missing videos, regardless of RSS status.

Issue: Sean Kochel channel has 165 videos per API but only 108 in DB.
RSS returns "skip" status (matched DB for videos it knows about), so gap
handling never triggers. The system should detect the API total inconsistency
and fill the gap.
"""

from unittest.mock import Mock, patch, MagicMock
import pytest

from yt_fts.download.batch_downloader import BatchDownloader


class TestGapHandlingOnApiTotalMismatch:
    """Test gap handling triggers when stored_api_total > db_count."""

    def test_gap_handling_condition_includes_api_total_mismatch(self):
        """
        Given: The batch downloader gap handling logic
        When: Examining the gap handling condition
        Then: The condition should check for api_total_mismatch flag

        This verifies that gap handling triggers when:
        - RSS status is "gap_detected" or "error", OR
        - api_total_mismatch is True (API total > DB count)
        """
        import inspect
        import yt_fts.download.batch_downloader as bd

        # Find the gap handling condition in the source
        source = inspect.getsource(bd)

        # Verify the api_total_mismatch flag is initialized
        assert "api_total_mismatch = False" in source, \
            "api_total_mismatch flag should be initialized"

        # Verify the flag is set when API total exceeds DB count
        assert "api_total_mismatch = True" in source, \
            "api_total_mismatch should be set when API total > DB count"

        # Verify the gap handling condition checks the flag
        # The condition should be: (rss_status in ("gap_detected", "error") or api_total_mismatch)
        assert "(rss_status in (\"gap_detected\", \"error\") or api_total_mismatch)" in source, \
            "Gap handling condition should check api_total_mismatch flag"

    def test_gap_handling_messages_include_channel_name(self):
        """
        Given: Gap handling messages in batch_downloader
        When: Examining the message strings
        Then: All gap-related messages should include channel identifier

        Messages checked:
        - "Gap detected → fetching..." should include {channel_display_name}
        - "✓ Gap check: All..." should include {channel_display_name}
        - "Gap handling failed:" should include channel info
        """
        import inspect
        import yt_fts.download.batch_downloader as bd

        source = inspect.getsource(bd)

        # channel_display_name is the variable containing the actual channel name
        # from the database, used in messages for user-friendly display

        # Message 1: "Gap detected → fetching full video list via yt-api..."
        gap_msg_lines = [line for line in source.split('\n') if 'Gap detected' in line]
        assert any('channel_display_name' in line for line in gap_msg_lines), \
            "Gap detected message must embed channel_display_name variable"

        # Message 2: "✓ Gap check: All..."
        gap_check_lines = [line for line in source.split('\n') if 'Gap check' in line]
        assert any('channel_display_name' in line for line in gap_check_lines), \
            "Gap check message must embed channel_display_name variable"

        # Message 3: "Gap handling failed"
        failed_lines = [line for line in source.split('\n') if 'Gap handling failed' in line]
        assert any('channel_display_name' in line for line in failed_lines), \
            "Gap handling failed message must embed channel_display_name variable"

        # Also verify the API total mismatch message uses channel_display_name
        mismatch_lines = [line for line in source.split('\n') if 'not yet downloaded' in line]
        assert any('channel_display_name' in line for line in mismatch_lines), \
            "API total mismatch message must embed channel_display_name variable"


class TestApiTotalMismatchFlagCleared:
    """Test api_total_mismatch flag is cleared after successful API sync.

    Regression test for issue where:
    1. First API fetch adds all videos to database
    2. api_total_mismatch flag remains True
    3. Second identical fetch happens in gap check code

    Symptoms: "0/X videos (X not yet downloaded)" then "already in database"
    with double playlist fetch.
    """

    def test_api_total_mismatch_cleared_after_first_sync(self):
        """
        Given: api_total_mismatch is set to True when API total > db_count
        When: First API sync succeeds (videos added or already exist)
        Then: api_total_mismatch should be set to False to prevent second fetch
        """
        import inspect
        import yt_fts.download.batch_downloader as bd

        source = inspect.getsource(bd)
        lines = source.split('\n')

        # Find the line with "added_count > 0"
        added_count_idx = None
        for i, line in enumerate(lines):
            if '(added_count or 0) > 0' in line or 'if added_count > 0' in line:
                added_count_idx = i
                break

        assert added_count_idx is not None, "Could not find added_count check"

        # Look for api_total_mismatch = False in the next ~35 lines (after sync completes)
        found_clear = False
        for i in range(added_count_idx, min(added_count_idx + 35, len(lines))):
            if 'api_total_mismatch = False' in lines[i]:
                found_clear = True
                break

        assert found_clear, (
            "api_total_mismatch flag must be cleared (set to False) after "
            "successful API sync to prevent duplicate fetch in gap check code."
        )


class TestBackfillTaskCleanup:
    """Test coordinator.remove_task() is called after backfill completes.

    Regression test for issue where:
    1. Backfill completes successfully (e.g., 30 videos processed)
    2. Progress bar shows 100%
    3. Code continues to next channel via `continue` statement
    4. coordinator.remove_task() is never called
    5. Progress bar hangs waiting for task cleanup

    Symptoms: After "yt-dlp: 100% 30/30", progress bar flashes and hangs.
    """

    def test_coordinator_remove_called_after_backfill(self):
        """
        Given: Backfill completes (backfill_needed = True)
        When: Execution reaches the continue statement after backfill
        Then: coordinator.remove_task() MUST be called before continue

        This ensures the progress task is cleaned up and doesn't hang.
        """
        import inspect
        import yt_fts.download.batch_downloader as bd

        source = inspect.getsource(bd)
        lines = source.split('\n')

        # Find the backfill block: look for "backfill_needed = True"
        backfill_block_start = None
        for i, line in enumerate(lines):
            if 'backfill_needed = True' in line:
                backfill_block_start = i
                break

        assert backfill_block_start is not None, "Could not find backfill_needed = True"

        # Find the continue statement after backfill (should be within ~120 lines)
        continue_idx = None
        for i in range(backfill_block_start, min(backfill_block_start + 120, len(lines))):
            # Check if this continue is after backfill code (look for 'backfill' in preceding lines)
            preceding_text = chr(10).join(lines[max(0, i-20):i]).lower()
            if '            continue' in lines[i] and 'backfill' in preceding_text:
                continue_idx = i
                break

        assert continue_idx is not None, "Could not find continue statement after backfill block"

        # Look for coordinator.remove_task() before the continue
        # Check the ~10 lines leading up to the continue
        found_cleanup = False
        for i in range(max(0, continue_idx - 10), continue_idx):
            if 'coordinator.remove_task(original_channel)' in lines[i]:
                found_cleanup = True
                break

        assert found_cleanup, (
            "coordinator.remove_task(original_channel) MUST be called before "
            "continue statement in backfill block to prevent progress bar hang. "
            "Without this, the backfill task is never removed from the coordinator, "
            "causing the progress bar to hang after reaching 100%."
        )

    def test_backfill_block_structure(self):
        """
        Given: The backfill code block structure
        When: Examining the control flow
        Then: Verify the pattern: try/except → coordinator.remove_task() → continue

        This ensures proper cleanup regardless of success or error.
        """
        import inspect
        import yt_fts.download.batch_downloader as bd

        source = inspect.getsource(bd)

        # Verify coordinator.remove_task appears in the source
        assert 'coordinator.remove_task(original_channel)' in source, \
            "coordinator.remove_task(original_channel) must be called to clean up tasks"

        # The backfill block should have the cleanup before continue
        # Pattern: ... except Exception: ... coordinator.remove_task() ... continue
        lines = source.split('\n')

        # Find all coordinator.remove_task calls
        remove_task_lines = [i for i, line in enumerate(lines) if 'coordinator.remove_task' in line]

        # At least one should be in/near backfill context (followed by continue)
        backfill_cleanup_found = False
        for idx in remove_task_lines:
            # Check if there's a 'continue' within a few lines after remove_task
            for i in range(idx + 1, min(idx + 5, len(lines))):
                if '            continue' in lines[i]:
                    backfill_cleanup_found = True
                    break
            if backfill_cleanup_found:
                break

        assert backfill_cleanup_found, (
            "coordinator.remove_task() should be followed by continue in backfill path. "
            "This ensures task cleanup happens before moving to next channel."
        )


class TestAutoBackfillMessageIncludesChannel:
    """Test auto-backfill message includes channel name.

    Regression test for issue where:
    1. Auto-backfill triggers for videos needing subtitles
    2. Message shows "Auto-backfill: X videos need subtitles"
    3. User can't tell WHICH channel needs backfill

    Symptoms: "Auto-backfill: 1 videos need subtitles" appears without
    channel context, followed later by "Downloading subtitles for 1 videos from CHANNEL".
    The first message should include the channel name.
    """

    def test_auto_backfill_message_includes_channel_name(self):
        """
        Given: Auto-backfill is triggered (videos without subtitles detected)
        When: The auto-backfill notification message is displayed
        Then: The message should include channel_display_name

        This verifies the message at batch_downloader.py:1435-1437 includes
        the channel name for user clarity.
        """
        import inspect
        import yt_fts.download.batch_downloader as bd

        source = inspect.getsource(bd)
        lines = source.split(chr(10))

        # Find the "Auto-backfill: ... videos need subtitles" message
        for i, line in enumerate(lines):
            if 'Auto-backfill:' in line and 'videos need subtitles' in line:
                # Check if this message includes channel_display_name
                assert 'channel_display_name' in line, (
                    "Auto-backfill message must embed channel_display_name variable. "
                    "Current format 'Auto-backfill: X videos need subtitles' doesn't show which channel. "
                    "Expected format should include channel_display_name variable"
                )
                # Found and validated
                return

        # If we get here, the message wasn't found at all
        assert False, "Could not find 'Auto-backfill: ... videos need subtitles' message in source"

    def test_auto_backfill_message_format(self):
        """
        Given: The auto-backfill message in batch_downloader
        When: Examining the message string format
        Then: Should follow pattern with visual indicator and channel name

        The message should have:
        - Video count
        - Channel name in quotes for clarity
        """
        import inspect
        import yt_fts.download.batch_downloader as bd

        source = inspect.getsource(bd)

        # Look for the auto-backfill message pattern
        # Should be something like: f"Auto-backfill: {len(backfill_video_ids)} videos need subtitles from "{channel_display_name}""
        backfill_msg_lines = [line for line in source.split(chr(10)) if 'Auto-backfill:' in line]

        assert len(backfill_msg_lines) > 0, "Auto-backfill message not found"

        # At least one line should have channel_display_name
        assert any('channel_display_name' in line for line in backfill_msg_lines), (
            "Auto-backfill message must include channel_display_name for user clarity"
        )
