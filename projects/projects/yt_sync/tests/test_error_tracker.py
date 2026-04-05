# tests/test_error_tracker.py

import logging
from collections import Counter, defaultdict

import pytest
from yt_sync.error_tracker import ErrorTracker

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def error_tracker():
    """Fixture for creating a fresh ErrorTracker instance."""
    return ErrorTracker()


def test_error_tracker_init(error_tracker):
    """Test initialization of ErrorTracker."""
    assert isinstance(error_tracker.errors_by_type, defaultdict)
    assert isinstance(error_tracker.errors_by_video, defaultdict)
    assert isinstance(error_tracker.error_counts, Counter)
    assert not error_tracker.has_errors()


def test_add_error(error_tracker):
    """Test adding an error to the tracker."""
    video_id = "video1"
    error_type = "DownloadError"
    error_message = "Failed to download video"

    error_tracker.add_error(video_id, error_type, error_message)

    assert video_id in error_tracker.errors_by_video
    assert error_type in error_tracker.errors_by_type
    assert error_tracker.errors_by_type[error_type] == [video_id]
    assert error_tracker.errors_by_video[video_id] == [
        {"type": error_type, "message": error_message}
    ]
    assert error_tracker.error_counts[error_type] == 1
    assert error_tracker.has_errors()


def test_add_error_empty_video_id(error_tracker):
    """Test adding an error with an empty video ID."""
    video_id = ""
    error_type = "DownloadError"
    error_message = "Failed to download video"

    error_tracker.add_error(video_id, error_type, error_message)

    assert len(error_tracker.errors_by_video) == 0
    assert len(error_tracker.errors_by_type) == 0
    assert len(error_tracker.error_counts) == 0
    assert not error_tracker.has_errors()


def test_add_multiple_errors_same_video(error_tracker):
    """Test adding multiple errors for the same video ID."""
    video_id = "video1"
    error_type1 = "DownloadError"
    error_message1 = "Failed to download video"
    error_type2 = "FormatError"
    error_message2 = "Invalid video format"

    error_tracker.add_error(video_id, error_type1, error_message1)
    error_tracker.add_error(video_id, error_type2, error_message2)

    assert video_id in error_tracker.errors_by_video
    assert error_type1 in error_tracker.errors_by_type
    assert error_type2 in error_tracker.errors_by_type
    assert error_tracker.errors_by_type[error_type1] == [video_id]
    assert error_tracker.errors_by_type[error_type2] == [video_id]
    assert len(error_tracker.errors_by_video[video_id]) == 2
    assert error_tracker.errors_by_video[video_id][0] == {
        "type": error_type1,
        "message": error_message1,
    }
    assert error_tracker.errors_by_video[video_id][1] == {
        "type": error_type2,
        "message": error_message2,
    }
    assert error_tracker.error_counts[error_type1] == 1
    assert error_tracker.error_counts[error_type2] == 1
    assert error_tracker.has_errors()


def test_add_multiple_errors_different_videos(error_tracker):
    """Test adding errors for different video IDs."""
    video_id1 = "video1"
    video_id2 = "video2"
    error_type = "DownloadError"
    error_message = "Failed to download video"

    error_tracker.add_error(video_id1, error_type, error_message)
    error_tracker.add_error(video_id2, error_type, error_message)

    assert video_id1 in error_tracker.errors_by_video
    assert video_id2 in error_tracker.errors_by_video
    assert error_type in error_tracker.errors_by_type
    assert error_tracker.errors_by_type[error_type] == [video_id1, video_id2]
    assert error_tracker.errors_by_video[video_id1] == [
        {"type": error_type, "message": error_message}
    ]
    assert error_tracker.errors_by_video[video_id2] == [
        {"type": error_type, "message": error_message}
    ]
    assert error_tracker.error_counts[error_type] == 2
    assert error_tracker.has_errors()


def test_get_errors_by_video(error_tracker):
    """Test retrieving errors by video ID."""
    video_id = "video1"
    error_type = "DownloadError"
    error_message = "Failed to download video"

    error_tracker.add_error(video_id, error_type, error_message)
    errors = error_tracker.get_errors_by_video()

    assert video_id in errors
    assert errors[video_id] == [{"type": error_type, "message": error_message}]


def test_clear_error_tracker(error_tracker):
    """Test clearing the error tracker."""
    video_id = "video1"
    error_type = "DownloadError"
    error_message = "Failed to download video"

    error_tracker.add_error(video_id, error_type, error_message)
    assert error_tracker.has_errors()

    error_tracker.clear()
    assert not error_tracker.has_errors()
    assert len(error_tracker.errors_by_type) == 0
    assert len(error_tracker.errors_by_video) == 0
    assert len(error_tracker.error_counts) == 0
