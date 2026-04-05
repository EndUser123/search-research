# tests/test_logging_config.py

import logging
import queue
from unittest.mock import patch

import pytest
from yt_sync.logging_config import ErrorAnalysisHandler, TUIQueueHandler, setup_logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def temp_dir(tmp_path):
    """Fixture for creating a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def log_queue():
    """Fixture for creating a queue for TUI logging."""
    return queue.Queue()


def test_tui_queue_handler_emit(log_queue):
    """Test TUIQueueHandler emit method with structured log data."""
    handler = TUIQueueHandler(log_queue)
    record = logging.LogRecord("root", logging.INFO, "test_path", 1, None, None, None)
    record.msg = {"event": "test_event", "data": "test_data"}

    handler.emit(record)

    assert not log_queue.empty()
    log_entry = log_queue.get_nowait()
    assert log_entry == {"event": "test_event", "data": "test_data"}


def test_tui_queue_handler_emit_non_dict(log_queue):
    """Test TUIQueueHandler emit method with non-dict log data."""
    handler = TUIQueueHandler(log_queue)
    record = logging.LogRecord("root", logging.INFO, "test_path", 1, None, None, None)
    record.msg = "plain text message"

    handler.emit(record)

    assert log_queue.empty()


def test_error_analysis_handler_emit():
    """Test ErrorAnalysisHandler emit method with warning level log."""
    handler = ErrorAnalysisHandler()
    record = logging.LogRecord(
        "root", logging.WARNING, "test_path", 1, None, None, None
    )
    record.msg = {"event": "warning_event", "channel_id": "channel1"}

    handler.emit(record)

    assert len(handler.errors) == 1
    assert handler.errors[0] == {"event": "warning_event", "channel_id": "channel1"}


def test_error_analysis_handler_emit_below_warning():
    """Test ErrorAnalysisHandler emit method with info level log."""
    handler = ErrorAnalysisHandler()
    record = logging.LogRecord("root", logging.INFO, "test_path", 1, None, None, None)
    record.msg = {"event": "info_event", "channel_id": "channel1"}

    handler.emit(record)

    assert len(handler.errors) == 0


def test_error_analysis_handler_get_errors_for_channel():
    """Test ErrorAnalysisHandler get_errors_for_channel method."""
    handler = ErrorAnalysisHandler()
    record1 = logging.LogRecord(
        "root", logging.WARNING, "test_path", 1, None, None, None
    )
    record1.msg = {"event": "error1", "channel_id": "channel1"}
    record2 = logging.LogRecord("root", logging.ERROR, "test_path", 2, None, None, None)
    record2.msg = {"event": "error2", "channel_id": "channel2"}
    record3 = logging.LogRecord(
        "root", logging.WARNING, "test_path", 3, None, None, None
    )
    record3.msg = {"event": "error3", "channel_id": "channel1"}

    handler.emit(record1)
    handler.emit(record2)
    handler.emit(record3)

    channel1_errors = handler.get_errors_for_channel("channel1")
    assert len(channel1_errors) == 2
    assert channel1_errors[0]["event"] == "error1"
    assert channel1_errors[1]["event"] == "error3"


def test_error_analysis_handler_clear_channel_errors():
    """Test ErrorAnalysisHandler clear_channel_errors method."""
    handler = ErrorAnalysisHandler()
    record1 = logging.LogRecord(
        "root", logging.WARNING, "test_path", 1, None, None, None
    )
    record1.msg = {"event": "error1", "channel_id": "channel1"}
    record2 = logging.LogRecord("root", logging.ERROR, "test_path", 2, None, None, None)
    record2.msg = {"event": "error2", "channel_id": "channel2"}
    record3 = logging.LogRecord(
        "root", logging.WARNING, "test_path", 3, None, None, None
    )
    record3.msg = {"event": "error3", "channel_id": "channel1"}

    handler.emit(record1)
    handler.emit(record2)
    handler.emit(record3)

    handler.clear_channel_errors("channel1")
    assert len(handler.errors) == 1
    assert handler.errors[0]["event"] == "error2"


def test_setup_logging_basic(temp_dir):
    """Test basic setup_logging functionality without TUI."""
    with (
        patch("logging.getLogger") as mock_get_logger,
        patch("pathlib.Path.mkdir") as mock_mkdir,
    ):
        setup_logging(log_level="INFO", tui_enabled=False)

        assert mock_get_logger.call_count > 0
        mock_mkdir.assert_called_once_with(exist_ok=True)


def test_setup_logging_tui_enabled(temp_dir):
    """Test setup_logging functionality with TUI enabled."""
    with (
        patch("logging.getLogger") as mock_get_logger,
        patch("pathlib.Path.mkdir") as mock_mkdir,
    ):
        setup_logging(log_level="INFO", tui_enabled=True)

        assert mock_get_logger.call_count > 0
        mock_mkdir.assert_called_once_with(exist_ok=True)


@pytest.fixture(autouse=True)
def mock_logging_handlers(mocker):
    """Fixture to automatically mock logging handlers with necessary attributes."""
    mock_stream = mocker.patch("logging.StreamHandler", autospec=True)
    mock_stream.return_value.level = logging.NOTSET
    mock_rotating = mocker.patch("logging.handlers.RotatingFileHandler", autospec=True)
    mock_rotating.return_value.level = logging.NOTSET


def test_setup_logging_level(temp_dir):
    """Test setup_logging with different log levels."""
    with patch("pathlib.Path.mkdir"):
        setup_logging(log_level="DEBUG", tui_enabled=False)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
