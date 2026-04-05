"""Tests for DownloadHandler _print_message method (RED Phase).

These tests verify the _print_message method that is called by validate_channel_url
during the backfill flow in batch_downloader.py.

Run with: pytest tests/test_download_handler_backfill.py -v
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
from io import StringIO


class TestDownloadHandlerPrintMessage:
    """Tests for the _print_message method on DownloadHandler."""

    @pytest.fixture
    def handler(self):
        """Create a DownloadHandler instance for testing."""
        from yt_fts.download.download_handler import DownloadHandler
        
        # Minimal configuration for testing
        console = Mock()
        console.stderr = True
        
        return DownloadHandler(
            console=console,
            rich_mode=True,  # Suppress actual console output
        )

    def test_print_message_method_exists(self, handler):
        """
        Test that DownloadHandler has a _print_message method.

        Given: A DownloadHandler instance
        When: Checking if _print_message method exists
        Then: The method should exist on the instance

        This test FAILS because _print_message is missing from DownloadHandler,
        but is called by validate_channel_url at line 3347.
        """
        # This should fail because _print_message doesn't exist
        assert hasattr(handler, '_print_message'),             "DownloadHandler should have a _print_message method"

    def test_print_message_callable(self, handler):
        """
        Test that _print_message is callable.

        Given: A DownloadHandler instance
        When: Checking if _print_message is callable
        Then: It should be a callable method

        This test FAILS because _print_message is missing.
        """
        assert callable(getattr(handler, '_print_message', None)),             "_print_message should be a callable method"

    def test_print_message_with_formatter(self, handler):
        """
        Test that _print_message uses formatter.print_message when available.

        Given: A DownloadHandler with _formatter configured
        When: Calling _print_message with a message
        Then: The message should be passed to _formatter.print_message

        This test FAILS because _print_message doesn't exist yet.
        """
        # Mock the formatter's print_message method
        handler._formatter.print_message = Mock()
        
        # Call _print_message - this will fail because method doesn't exist
        handler._print_message("Test message")
        
        # Verify formatter.print_message was called
        handler._formatter.print_message.assert_called_once_with("Test message")

    def test_print_message_with_log_callback(self, handler):
        """
        Test that _print_message falls back to log_callback when formatter unavailable.

        Given: A DownloadHandler with log_callback but no _formatter
        When: Calling _print_message with a message
        Then: The message should be passed to log_callback

        This test FAILS because _print_message doesn't exist yet.
        """
        # Set up log_callback
        mock_callback = Mock()
        handler.log_callback = mock_callback
        
        # Remove formatter to test fallback
        handler._formatter = None
        
        # Call _print_message - this will fail because method doesn't exist
        handler._print_message("Test message via callback")
        
        # Verify log_callback was called
        mock_callback.assert_called_once_with("Test message via callback")

    def test_print_message_fallback_to_stderr(self, handler):
        """
        Test that _print_message falls back to stderr.write when no other option.

        Given: A DownloadHandler with no formatter or log_callback
        When: Calling _print_message with a message
        Then: The message should be written to stderr

        This test FAILS because _print_message doesn't exist yet.
        """
        # Remove formatter and log_callback to test stderr fallback
        handler._formatter = None
        handler.log_callback = None
        
        # Capture stderr
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            # Call _print_message - this will fail because method doesn't exist
            handler._print_message("Test message to stderr")
            
            # Verify message was written to stderr
            assert "Test message to stderr" in mock_stderr.getvalue()


class TestBackfillFlowPrintMessage:
    """Tests for _print_message usage in the backfill flow."""

    def test_validate_channel_url_triggers_print_message_access(self):
        """
        Test that handler.validate_channel_url tries to pass self._print_message as callback.

        Given: A DownloadHandler instance (as used in backfill flow)
        When: handler.validate_channel_url() is called
        Then: Accessing handler._print_message should work (method should exist)

        This documents the actual bug at line 3347:
            return validate_channel_url(channel_url, print_callback=self._print_message)

        The _print_message attribute doesn't exist, so passing it as a keyword
        argument raises AttributeError BEFORE validate_channel_url even executes.

        This test FAILS because _print_message doesn't exist.
        """
        from yt_fts.download.download_handler import DownloadHandler
        
        console = Mock()
        handler = DownloadHandler(console=console, rich_mode=True)
        
        # The bug occurs when trying to ACCESS handler._print_message to pass it
        # This happens at the call site in download_handler.py line 3347
        # We expect this to succeed once _print_message is implemented
        # For now it fails because the attribute doesn't exist
        assert hasattr(handler, '_print_message'),             "_print_message should exist to be passed as print_callback"

    def test_direct_access_to_print_message_attribute(self):
        """
        Direct test: accessing handler._print_message should work.

        Given: A DownloadHandler instance
        When: Trying to access the _print_message attribute
        Then: The attribute should exist and be accessible

        This is the most direct test of the bug.

        This test FAILS because _print_message doesn't exist.
        """
        from yt_fts.download.download_handler import DownloadHandler
        
        console = Mock()
        handler = DownloadHandler(console=console, rich_mode=True)
        
        # Simply accessing the attribute should succeed
        # The test fails because we expect the attribute to exist
        assert hasattr(handler, '_print_message'),             "_print_message attribute should exist on DownloadHandler"
