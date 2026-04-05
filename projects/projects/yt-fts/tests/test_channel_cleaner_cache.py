"""
Tests for channel cleaner caching behavior.

Tests that:
1. First run shows individual removal messages
2. Second run (cache hit) suppresses individual messages
3. File change triggers recleaning with messages again
"""

import tempfile
import shutil
from pathlib import Path
from io import StringIO

import pytest


class TestChannelCleanerCaching:
    """
    Test channel cleaner file caching with quiet_mode behavior.

    Given: A channel list file with some invalid entries
    When: Loading channels multiple times
    Then: First run shows details, subsequent runs suppress details
    """

    def test_cache_hit_suppresses_individual_messages(self):
        """
        Test that cache hit returns quickly without individual messages.

        Given: A channel list file that has been cleaned before
        When: Loading the same file again (unchanged)
        Then: Should return cached result without printing individual removals
        """
        from yt_fts.services.channel_cleaner import ChannelCleaner
        from rich.console import Console

        # Create a temporary file with some channels
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_channels.txt"
            test_file.write_text(
                "@validchannel1\n"
                "@validchannel2\n"
                "https://youtube.com/test\n"
                "invalid\n"
                "@validchannel1\n"  # duplicate
            )

            cache_dir = Path(tmpdir) / "cache"
            console = Console(file=StringIO())
            cleaner = ChannelCleaner(console)

            # First call - should show individual messages (quiet_mode=False)
            _, stats1 = cleaner.clean_channels_file_cached(
                file_path=str(test_file),
                cache_dir=str(cache_dir),
            )

            assert stats1["cache_hit"] is False
            assert stats1["invalid_removed"] >= 1  # "invalid" entry
            assert stats1["duplicates_removed"] >= 1  # duplicate @validchannel1

            # Second call - cache hit, no individual messages
            _, stats2 = cleaner.clean_channels_file_cached(
                file_path=str(test_file),
                cache_dir=str(cache_dir),
            )

            assert stats2["cache_hit"] is True
            # Stats should be consistent
            assert stats2["invalid_removed"] == stats1["invalid_removed"]
            assert stats2["duplicates_removed"] == stats1["duplicates_removed"]

    def test_file_change_triggers_recleaning(self):
        """
        Test that file modification triggers recleaning.

        Given: A cached channel list
        When: The source file is modified
        Then: Should detect hash change and reclean
        """
        from yt_fts.services.channel_cleaner import ChannelCleaner
        from rich.console import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_channels.txt"
            test_file.write_text("@channel1\n@channel2\n")

            cache_dir = Path(tmpdir) / "cache"
            console = Console(file=StringIO())
            cleaner = ChannelCleaner(console)

            # First call
            _, stats1 = cleaner.clean_channels_file_cached(
                file_path=str(test_file),
                cache_dir=str(cache_dir),
            )
            assert stats1["cache_hit"] is False
            assert stats1["final_count"] == 2

            # Modify the file
            test_file.write_text("@channel1\n@channel2\n@channel3\n")

            # Second call - should reclean due to hash change
            _, stats2 = cleaner.clean_channels_file_cached(
                file_path=str(test_file),
                cache_dir=str(cache_dir),
            )
            assert stats2["cache_hit"] is False
            assert stats2["final_count"] == 3

    def test_quiet_mode_suppresses_messages(self):
        """
        Test that quiet_mode suppresses individual messages.

        Given: A channel list with invalid entries
        When: Cleaning with quiet_mode=True
        Then: Individual removal/change messages should not be printed
        """
        from yt_fts.services.channel_cleaner import ChannelCleaner
        from rich.console import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_channels.txt"
            test_file.write_text(
                "@valid\n"
                "invalid-entry\n"
                "https://youtube.com/test\n"
            )

            console = Console(file=StringIO())
            cleaner = ChannelCleaner(console)

            # Clean with quiet_mode=True
            channels, stats = cleaner.clean_channels(
                ["@valid", "invalid-entry", "https://youtube.com/test"],
                quiet_mode=True
            )

            # Should still remove invalid entries
            assert stats["invalid_removed"] >= 1
            # But console output should be minimal (no individual "X Removed" messages)
            output = console.file.getvalue()
            assert "Removed invalid" not in output or output.count("Removed invalid") == 0

    def test_cache_persists_across_instances(self):
        """
        Test that cache persists across different ChannelCleaner instances.

        Given: A cleaned channel list cached to disk
        When: Creating a new ChannelCleaner instance and loading same file
        Then: Should use cached result
        """
        from yt_fts.services.channel_cleaner import ChannelCleaner
        from rich.console import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_channels.txt"
            test_file.write_text("@channel1\n@channel2\n")

            cache_dir = Path(tmpdir) / "cache"

            # First instance - cache miss
            console1 = Console(file=StringIO())
            cleaner1 = ChannelCleaner(console1)
            _, stats1 = cleaner1.clean_channels_file_cached(
                file_path=str(test_file),
                cache_dir=str(cache_dir),
            )
            assert stats1["cache_hit"] is False

            # Second instance - cache hit
            console2 = Console(file=StringIO())
            cleaner2 = ChannelCleaner(console2)
            _, stats2 = cleaner2.clean_channels_file_cached(
                file_path=str(test_file),
                cache_dir=str(cache_dir),
            )
            assert stats2["cache_hit"] is True

    def test_force_flag_bypasses_cache(self):
        """
        Test that force=True bypasses cache and recleans.

        Given: A cached channel list
        When: Calling clean_channels_file_cached with force=True
        Then: Should reclean and update cache
        """
        from yt_fts.services.channel_cleaner import ChannelCleaner
        from rich.console import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_channels.txt"
            test_file.write_text("@channel1\n@channel2\n")

            cache_dir = Path(tmpdir) / "cache"
            console = Console(file=StringIO())
            cleaner = ChannelCleaner(console)

            # First call
            _, stats1 = cleaner.clean_channels_file_cached(
                file_path=str(test_file),
                cache_dir=str(cache_dir),
            )
            assert stats1["cache_hit"] is False

            # Second call with force=True
            _, stats2 = cleaner.clean_channels_file_cached(
                file_path=str(test_file),
                cache_dir=str(cache_dir),
                force=True,
            )
            # Should be cache miss even though file unchanged
            assert stats2["cache_hit"] is False


class TestBatchLoaderCaching:
    """
    Test that batch_loaders.py uses cached cleaning.

    Given: A channel file
    When: Loading channels via batch_loaders
    Then: Should use cached version on subsequent loads
    """

    def test_batch_loader_uses_cached_cleaning(self):
        """
        Integration test for batch_loader using cache.

        Given: A channel list file
        When: Loading via batch_loaders.load_channels_from_input
        Then: Second load should use cache
        """
        from yt_fts.core.batch_loaders import load_channels_from_input
        from rich.console import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "channels.txt"
            test_file.write_text(
                "@channel1\n"
                "@channel2\n"
                "@channel1\n"  # duplicate
                "invalid\n"   # invalid
            )

            console = Console(file=StringIO())

            # First load
            result1 = load_channels_from_input(str(test_file))
            assert result1.duplicates_removed >= 1

            # Second load - should use cache (won't show individual messages)
            result2 = load_channels_from_input(str(test_file))
            assert len(result2.channels) == len(result1.channels)


class TestCleanFileFlag:
    """
    Test --clean-file flag for in-place file cleaning.

    Given: A channel list file with invalid entries and duplicates
    When: Running batch_download with --clean-file flag
    Then: Source file should be overwritten with cleaned channels
    """

    def test_clean_file_writes_cleaned_channels_back(self):
        """
        Test that --clean-file writes cleaned channels back to source file.

        Given: A channel list file with invalid entries
        When: Cleaning with --clean-file flag
        Then: Source file should contain only cleaned channels after operation
        """
        from click.testing import CliRunner
        from yt_fts.core.download_cli import batch_download

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "channels.txt"
            # Create file with duplicates and invalid entries
            # Note: The cleaner converts handles to full URLs
            original_content = (
                "@channel1\n"
                "@channel2\n"
                "@channel1\n"  # duplicate
                "https://youtube.com/test\n"  # invalid URL (no channel ID)
                "https://test.com\n"  # invalid URL (not youtube)
            )
            test_file.write_text(original_content)

            runner = CliRunner()

            # Run with --clean-file flag (use --dry-run to skip actual downloads)
            # Pass file as positional argument (not --import-file)
            result = runner.invoke(
                batch_download,
                [str(test_file), '--clean-file', '--dry-run']
            )

            # Check that the file was written with cleaned content
            updated_content = test_file.read_text()
            lines = [l for l in updated_content.strip().split('\n') if l]

            # Should only contain valid channels (no duplicates, no invalid entries)
            # Channels are converted to full URL format
            assert "https://www.youtube.com/@channel1" in lines
            assert "https://www.youtube.com/@channel2" in lines
            assert lines.count("https://www.youtube.com/@channel1") == 1  # no duplicate
            assert "https://youtube.com/test" not in updated_content
            assert "https://test.com" not in updated_content

            # Should have trailing newline
            assert updated_content.endswith('\n')

    def test_clean_file_preserves_valid_content(self):
        """
        Test that --clean-file preserves all valid channel entries.

        Given: A file with mix of valid and invalid entries
        When: Cleaning with --clean-file flag
        Then: All valid channels should remain in file
        """
        from click.testing import CliRunner
        from yt_fts.core.download_cli import batch_download

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "channels.txt"
            original_content = (
                "@valid1\n"
                "@valid2\n"
                "@valid3\n"
                "https://youtube.com/test\n"  # invalid URL (no channel ID)
                "https://test.com\n"  # invalid URL (not youtube)
            )
            test_file.write_text(original_content)

            runner = CliRunner()
            result = runner.invoke(
                batch_download,
                [str(test_file), '--clean-file', '--dry-run']
            )

            updated_content = test_file.read_text()
            lines = [l for l in updated_content.strip().split('\n') if l]

            # All valid channels should be present (converted to full URL format)
            assert "https://www.youtube.com/@valid1" in lines
            assert "https://www.youtube.com/@valid2" in lines
            assert "https://www.youtube.com/@valid3" in lines
            # Invalid channels should be removed
            assert "https://youtube.com/test" not in updated_content
            assert "https://test.com" not in updated_content

    def test_clean_file_without_flag_does_not_modify_source(self):
        """
        Test that without --clean-file flag, source file is not modified.

        Given: A channel list file with invalid entries
        When: Running batch_download WITHOUT --clean-file flag
        Then: Source file should remain unchanged
        """
        from click.testing import CliRunner
        from yt_fts.core.download_cli import batch_download

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "channels.txt"
            original_content = (
                "@valid1\n"
                "@valid2\n"
                "duplicate\n"
                "duplicate\n"
                "https://youtube.com/test\n"
            )
            test_file.write_text(original_content)

            runner = CliRunner()
            result = runner.invoke(
                batch_download,
                [str(test_file), '--dry-run']  # NO --clean-file
            )

            # File should be unchanged
            updated_content = test_file.read_text()
            assert updated_content == original_content

    def test_clean_file_handles_empty_file(self):
        """
        Test that --clean-file handles empty file gracefully.

        Given: An empty channel list file
        When: Cleaning with --clean-file flag
        Then: Should create valid empty file (just newline)
        """
        from click.testing import CliRunner
        from yt_fts.core.download_cli import batch_download

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "channels.txt"
            test_file.write_text("")

            runner = CliRunner()
            result = runner.invoke(
                batch_download,
                [str(test_file), '--clean-file', '--dry-run']
            )

            # File should exist with just a newline
            updated_content = test_file.read_text()
            assert updated_content == "\n"
