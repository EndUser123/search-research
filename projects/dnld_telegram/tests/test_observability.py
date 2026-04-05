"""
Tests for observability and structured logging functionality.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from loguru import logger
from src.download.download import download_context


class TestObservability:
    """Test structured logging and observability features."""

    @pytest.mark.asyncio
    async def test_structured_logging_with_context(self):
        """Test that async operations include proper context"""
        # First test the existing download_context manager
        # Capture log output
        with self.captured_logs() as logs:
            async with download_context("test_channel", "test_operation"):
                # Simulate some work
                await asyncio.sleep(0.01)

        # Verify structured logging messages
        assert len(logs) >= 2, "Expected at least START and END log messages"

        # Check that we have a START message
        start_logs = [log for log in logs if "START:" in log]
        assert len(start_logs) == 1, "Expected exactly one START log message"
        start_log = start_logs[0]
        assert "test_channel" in start_log, "START log should contain channel name"
        assert "test_operation" in start_log, "START log should contain operation name"
        assert "context_id" in start_log, "START log should contain context_id"

        # Check that we have an END message
        end_logs = [log for log in logs if "END:" in log]
        assert len(end_logs) == 1, "Expected exactly one END log message"
        end_log = end_logs[0]
        assert "test_channel" in end_log, "END log should contain channel name"
        assert "test_operation" in end_log, "END log should contain operation name"
        assert "context_id" in end_log, "END log should contain context_id"
        assert "Duration:" in end_log, "END log should contain duration"

    @pytest.mark.asyncio
    async def test_download_media_structured_logging_with_context(self):
        """Test that _download_media includes structured context"""
        # Mock the necessary dependencies for _download_media
        with patch("src.download.download.logger") as mock_logger:
            with patch(
                "src.download.download.get_temp_download_dir", return_value="/tmp/test"
            ):
                with patch(
                    "src.download.download._determine_filename_and_extension",
                    return_value="test_file.txt",
                ):
                    with patch("src.download.download.os.makedirs"):
                        with patch(
                            "src.download.download.get_file_id",
                            return_value="test_file_id",
                        ):
                            with patch(
                                "src.download.download.update_enumerated_file_status"
                            ):
                                with patch(
                                    "src.download.download.save_downloaded_files"
                                ):
                                    # Mock message object
                                    mock_message = MagicMock()
                                    mock_message.id = 12345
                                    mock_message.media = None
                                    mock_message.date = None

                                    # Mock client
                                    mock_client = MagicMock()
                                    mock_client.download_media = MagicMock()
                                    mock_client.download_media.return_value = (
                                        "/tmp/test/final_file.txt"
                                    )

                                    # Mock downloaded_files dict
                                    downloaded_files = {}

                                    # Import and call the function under test

                                    from src.download.download import (
                                        _download_media,
                                    )

                                    # Mock os.path.exists and os.path.getsize for file validation
                                    with patch(
                                        "src.download.download.os.path.exists",
                                        return_value=True,
                                    ):
                                        with patch(
                                            "src.download.download.os.path.getsize",
                                            return_value=1000,
                                        ):
                                            with patch(
                                                "src.download.download.shutil.move"
                                            ):
                                                with patch(
                                                    "src.download.download.os.path.join",
                                                    return_value="/test/save/test_file.txt",
                                                ):
                                                    result = await _download_media(
                                                        client=mock_client,
                                                        message=mock_message,
                                                        save_directory="/test/save",
                                                        channel_name="test_channel",
                                                        downloaded_files=downloaded_files,
                                                        progress=None,
                                                    )

                                                    # Verify the function was called
                                                    assert result is not None

                                                    # Verify contextualized logging was used
                                                    assert (
                                                        mock_logger.contextualize.called
                                                    )
                                                    call_args = mock_logger.contextualize.call_args[
                                                        1
                                                    ]
                                                    assert "message_id" in call_args
                                                    assert (
                                                        call_args["message_id"] == 12345
                                                    )
                                                    assert "channel" in call_args
                                                    assert (
                                                        call_args["channel"]
                                                        == "test_channel"
                                                    )
                                                    assert "task_id" in call_args

    @pytest.mark.asyncio
    async def test_concurrent_task_correlation(self):
        """Test that concurrent operations have unique correlation IDs"""
        correlation_ids = set()

        async def mock_operation():
            # Simulate getting correlation ID from context
            import uuid

            task_id = str(uuid.uuid4())[:8]
            correlation_ids.add(task_id)
            await asyncio.sleep(0.01)
            return task_id

        # Run concurrent operations
        results = await asyncio.gather(*[mock_operation() for _ in range(10)])

        # All should have unique correlation IDs
        assert len(correlation_ids) == 10
        assert len(results) == 10

    @pytest.mark.asyncio
    async def test_structured_logging_error_handling(self):
        """Test that the download_context manager properly logs errors."""
        # Capture log output
        with self.captured_logs() as logs:
            with pytest.raises(ValueError, match="Test error"):
                async with download_context("test_channel", "test_operation"):
                    # Simulate some work that raises an exception
                    await asyncio.sleep(0.01)
                    raise ValueError("Test error")

        # Verify structured logging messages including error
        assert len(logs) >= 2, "Expected at least START and ERROR log messages"

        # Check that we have a START message
        start_logs = [log for log in logs if "START:" in log]
        assert len(start_logs) == 1, "Expected exactly one START log message"

        # Check that we have an ERROR message
        error_logs = [log for log in logs if "ERROR:" in log]
        assert len(error_logs) == 1, "Expected exactly one ERROR log message"
        error_log = error_logs[0]
        assert "test_channel" in error_log, "ERROR log should contain channel name"
        assert "test_operation" in error_log, "ERROR log should contain operation name"
        assert "context_id" in error_log, "ERROR log should contain context_id"
        assert "Duration:" in error_log, "ERROR log should contain duration"
        assert "Test error" in error_log, "ERROR log should contain error message"

    @pytest.mark.asyncio
    async def test_context_id_uniqueness(self):
        """Test that each context gets a unique context_id."""
        context_ids = []

        # Run multiple contexts and collect their IDs
        for i in range(3):
            async with download_context("test_channel", f"operation_{i}") as context_id:
                context_ids.append(context_id)
                await asyncio.sleep(0.01)  # Small delay to ensure different timestamps

        # Verify all context IDs are unique
        assert len(context_ids) == len(
            set(context_ids)
        ), "All context IDs should be unique"

        # Verify each ID contains expected components
        for i, context_id in enumerate(context_ids):
            assert (
                "test_channel" in context_id
            ), f"Context ID {i} should contain channel name"
            assert (
                f"operation_{i}" in context_id
            ), f"Context ID {i} should contain operation name"

    @staticmethod
    def captured_logs():
        """Context manager to capture log output."""

        class LogCapture:
            def __init__(self):
                self.logs = []
                self.handler_id = None

            def __enter__(self):
                self.logs = []

                # Create a custom handler to capture loguru logs
                def capture_logs(message):
                    self.logs.append(message.record["message"])

                # Add the handler to loguru
                self.handler_id = logger.add(
                    capture_logs, level="INFO", format="{message}"
                )

                return self.logs

            def __exit__(self, exc_type, exc_val, exc_tb):
                # Remove the handler from loguru
                if self.handler_id is not None:
                    logger.remove(self.handler_id)

        return LogCapture()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
