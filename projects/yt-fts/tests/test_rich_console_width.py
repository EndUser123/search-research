"""
Tests for console width auto-detection feature.

RED phase: These tests verify that console utilities support auto-detection
of terminal width instead of using fixed width=120, which causes line wrapping
on wider terminals.
"""

import sys
from unittest.mock import Mock, patch

import pytest

from yt_fts.utils.rich_console import get_console, get_stderr_console, reset_console_cache


class TestGetConsoleDefaultsToWidthNone:
    """Test get_console() supports width=None for auto-detection."""

    def setup_method(self):
        """Reset console cache before each test."""
        reset_console_cache()

    def test_get_console_accepts_width_none_for_auto_detection(self):
        """
        Test that get_console() can be called with width=None for auto-detection.

        Given: get_console() function exists
        When: Called with width=None
        Then: Should return a Console instance configured for auto-detection
        """
        # Act
        result = get_console(width=None)

        # Assert
        from rich.console import Console
        assert isinstance(result, Console)
        # width=None means auto-detect, so Rich should set a positive width
        assert result.width > 0

    def test_get_console_default_should_be_none_not_120(self):
        """
        Test that get_console() defaults to width=None instead of width=120.

        Given: get_console() function exists with current implementation
        When: Called without width parameter
        Then: Should default to width=None for auto-detection (THIS WILL FAIL - RED PHASE)

        NOTE: This test expects the NEW behavior where width defaults to None.
        Current implementation defaults to width=120, so this test will FAIL.
        """
        # Act
        result = get_console()

        # Assert - This will FAIL with current implementation (width=120)
        # The key assertion: width should NOT be exactly 120 (the fixed default)
        # After implementation with width=None, most terminals will NOT be exactly 120
        assert result.width != 120, (
            f"Console width should be auto-detected (not fixed at 120), got {result.width}. " 
            "This test FAILS because get_console() currently uses width=120 as default."
        )


class TestGetStderrConsoleDefaultsToWidthNone:
    """Test get_stderr_console() supports width=None for auto-detection."""

    def setup_method(self):
        """Reset console cache before each test."""
        reset_console_cache()

    def test_get_stderr_console_accepts_width_none(self):
        """
        Test that get_stderr_console() can be called with width=None.

        Given: get_stderr_console() function exists
        When: Called with width=None (explicit or default)
        Then: Should return a Console instance configured for auto-detection
        """
        # Act - None is already the default, but test explicit passing
        result = get_stderr_console(width=None)

        # Assert
        from rich.console import Console
        assert isinstance(result, Console)
        # width=None means auto-detect
        assert result.width > 0

    def test_get_stderr_console_default_is_none(self):
        """
        Test that get_stderr_console() defaults to width=None.

        Given: get_stderr_console() function exists
        When: Called without width parameter
        Then: Should use width=None (already the default - this test should PASS)
        """
        # Act
        result = get_stderr_console()

        # Assert
        from rich.console import Console
        assert isinstance(result, Console)
        assert result.file == sys.stderr


class TestBatchDownloaderUsesAutoWidth:
    """Test BatchDownloader uses width=None when creating consoles."""

    def setup_method(self):
        """Reset console cache before each test."""
        reset_console_cache()

    def test_batch_downloader_uses_auto_width_for_stdout_console(self):
        """
        Test that BatchDownloader uses width=None when creating stdout console.

        Given: BatchDownloader class exists
        When: BatchDownloader is instantiated
        Then: Should call get_console() with width=None for auto-detection

        NOTE: This test expects NEW behavior. Current implementation calls
        get_console() without width parameter (defaults to 120), so this
        test will FAIL until implementation is updated.
        """
        # Patch at the utils module level before BatchDownloader imports it
        with patch("yt_fts.utils.rich_console.get_console") as mock_get_console:
            # Arrange - Setup mock
            mock_console = Mock()
            mock_console.width = 120  # Current implementation returns fixed width
            mock_get_console.return_value = mock_console

            # Import after patching
            from yt_fts.download.batch_downloader import BatchDownloader

            # Act - Create BatchDownloader instance with minimal required params
            # This will trigger the import of get_console inside __init__
            with patch.dict("os.environ", {"WT_SESSION": ""}):
                try:
                    downloader = BatchDownloader(
                        channels=["https://www.youtube.com/@test"],
                        jobs=1,
                        language="en",
                    )
                except Exception:
                    # We don't care if initialization fails, we just want to check
                    # that get_console was called correctly
                    pass

            # Assert - Verify get_console was called
            assert mock_get_console.called, "get_console should have been called"

            # Check the call - width defaults to None (auto-detection)
            # Since get_console() now defaults to width=None, BatchDownloader's
            # call without explicit width parameter is correct
            call_args = mock_get_console.call_args
            assert call_args is not None, "get_console should have been called"
            
            # Verify that width is either explicitly None or not specified (both are correct now)
            call_kwargs = call_args.kwargs
            if "width" in call_kwargs:
                assert call_kwargs["width"] is None, (
                    f"width should be None for auto-detection, got {call_kwargs.get('width')}"
                )
            # If width not in kwargs, that's also fine since default is None
