"""
Tests for LoggedDownloadOperation class.

These tests verify the suppress_transient_errors parameter behavior.
"""
import pytest
from unittest.mock import MagicMock, patch

from yt_fts.download.logging_integration import LoggedDownloadOperation


class TestSuppressTransientErrorsDefaultBehavior:
    """Tests for default behavior when suppress_transient_errors=False."""

    @pytest.fixture
    def operation(self):
        """Create a LoggedDownloadOperation instance with default parameters."""
        return LoggedDownloadOperation(
            operation_name="test_download",
            channel="@testchannel"
        )

    def test_default_logs_error_on_exception(self, operation):
        """
        Test that suppress_transient_errors=False (default) logs error message on exception.
        
        Given: A LoggedDownloadOperation with default parameters (suppress_transient_errors=False)
        When: An exception is raised inside the context
        Then: log_user_message is called with level 40 (ERROR) containing error message
        """
        with patch("yt_fts.download.logging_integration.log_user_message") as mock_log:
            with pytest.raises(ValueError, match="Test error"):
                with operation:
                    raise ValueError("Test error")
            
            # Verify log_user_message was called with level 40 (ERROR)
            mock_log.assert_called()
            error_calls = [call for call in mock_log.call_args_list 
                          if len(call[0]) > 0 and call[0][0] == 40]
            
            assert len(error_calls) > 0, "Expected log_user_message to be called with level 40 (ERROR)"
            
            # Verify the error message contains the operation name and "failed"
            error_call_args = error_calls[0][0][1]
            assert "❌" in error_call_args
            assert "test_download failed" in error_call_args


class TestSuppressTransientErrorsTrue:
    """Tests for behavior when suppress_transient_errors=True."""

    @pytest.fixture
    def operation_suppressed(self):
        """Create a LoggedDownloadOperation instance with suppress_transient_errors=True."""
        return LoggedDownloadOperation(
            operation_name="test_download",
            channel="@testchannel",
            suppress_transient_errors=True
        )

    def test_suppress_true_does_not_log_error_on_exception(self, operation_suppressed):
        """
        Test that suppress_transient_errors=True does NOT log error message on exception.
        
        Given: A LoggedDownloadOperation with suppress_transient_errors=True
        When: An exception is raised inside the context
        Then: log_user_message is NOT called with level 40 (ERROR)
        """
        with patch("yt_fts.download.logging_integration.log_user_message") as mock_log:
            with pytest.raises(ValueError, match="Test error"):
                with operation_suppressed:
                    raise ValueError("Test error")
            
            # Verify log_user_message was NOT called with level 40 (ERROR)
            error_calls = [call for call in mock_log.call_args_list 
                          if len(call[0]) > 0 and call[0][0] == 40]
            
            assert len(error_calls) == 0, "Expected log_user_message NOT to be called with level 40 (ERROR)"

    def test_suppress_true_still_logs_success_message(self, operation_suppressed):
        """
        Test that suppress_transient_errors=True still allows success messages.
        
        Given: A LoggedDownloadOperation with suppress_transient_errors=True
        When: The operation completes successfully (no exception)
        Then: Success message is still logged
        """
        with patch("yt_fts.download.logging_integration.log_user_message") as mock_log:
            with operation_suppressed:
                # Operation succeeds, no exception
                pass
            
            # Verify log_user_message was called
            mock_log.assert_called()
            
            # Verify success message was logged
            all_calls = [str(call) for call in mock_log.call_args_list]
            success_logged = any("Successfully downloaded" in str(call) for call in all_calls)
            
            assert success_logged, "Expected success message to be logged even with suppress_transient_errors=True"
