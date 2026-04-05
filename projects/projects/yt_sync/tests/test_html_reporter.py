# tests/test_html_reporter.py

import html
import logging
from unittest.mock import mock_open, patch

import pytest
from yt_sync.html_reporter import create_failed_downloads_report

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def temp_dir(tmp_path):
    """Fixture for creating a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def failed_videos():
    """Fixture for a dictionary of failed videos."""
    return {"video1": "Test Video 1", "video2": "Test Video 2"}


@pytest.fixture
def channel_name():
    """Fixture for channel name."""
    return "Test Channel"


def test_create_failed_downloads_report_empty_input(temp_dir, channel_name):
    """Test creating a report with an empty failed videos dictionary."""
    create_failed_downloads_report({}, channel_name, temp_dir)
    # No file should be created for empty input
    assert not any(temp_dir.glob("failed_downloads_*.html"))


def test_create_failed_downloads_report_success(temp_dir, failed_videos, channel_name):
    """Test creating a report with failed videos."""
    with patch("builtins.open", mock_open()) as mocked_file:
        create_failed_downloads_report(failed_videos, channel_name, temp_dir)
        report_path = temp_dir / "failed_downloads_Test Channel.html"
        mocked_file.assert_called_once_with(report_path, "w", encoding="utf-8")
        handle = mocked_file()
        written_content = "".join(call[0][0] for call in handle.write.call_args_list)
        assert f"Failed Downloads for {html.escape(channel_name)}" in written_content
        assert "Test Video 1" in written_content
        assert "Test Video 2" in written_content
        assert "https://www.youtube.com/watch?v=video1" in written_content
        assert "https://www.youtube.com/watch?v=video2" in written_content


def test_create_failed_downloads_report_html_escape(temp_dir, channel_name):
    """Test that HTML characters in video titles and channel name are properly escaped."""
    failed_videos = {"video1": "Test <Video> & 1"}
    escaped_channel_name = "Test <Channel> & Name"
    with patch("builtins.open", mock_open()) as mocked_file:
        create_failed_downloads_report(failed_videos, escaped_channel_name, temp_dir)
        report_path = temp_dir / "failed_downloads_Test Channel  Name.html"
        mocked_file.assert_called_once_with(report_path, "w", encoding="utf-8")
        handle = mocked_file()
        written_content = "".join(call[0][0] for call in handle.write.call_args_list)
        assert (
            f"Failed Downloads for {html.escape(escaped_channel_name)}"
            in written_content
        )
        assert html.escape("Test <Video> & 1") in written_content
        assert "<Video>" not in written_content
        assert "&" in written_content


def test_create_failed_downloads_report_filename_sanitization(temp_dir, failed_videos):
    """Test that the filename is sanitized based on channel name."""
    channel_name = "Test@#$%^&*Channel!"
    with patch("builtins.open", mock_open()) as mocked_file:
        create_failed_downloads_report(failed_videos, channel_name, temp_dir)
        report_path = temp_dir / "failed_downloads_TestChannel.html"
        mocked_file.assert_called_once_with(report_path, "w", encoding="utf-8")


def test_create_failed_downloads_report_io_error(temp_dir, failed_videos, channel_name):
    """Test handling of IOError when writing the report."""
    with patch("builtins.open", side_effect=OSError("Cannot write file")):
        create_failed_downloads_report(failed_videos, channel_name, temp_dir)
        # No assertion needed, just ensure no unhandled exception
