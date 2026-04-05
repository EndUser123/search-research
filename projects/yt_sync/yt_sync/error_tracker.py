# yt_sync/error_tracker.py - New file for clean error reporting

import logging
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


class ErrorTracker:
    """Tracks and reports errors in a clean, organized format."""

    def __init__(self):
        # Maps error type to a list of video IDs
        self.errors_by_type: dict[str, list[str]] = defaultdict(list)
        # Maps video ID to a list of error details (type and message)
        self.errors_by_video: dict[str, list[dict[str, str]]] = defaultdict(list)
        self.error_counts: Counter = Counter()

    def add_error(self, video_id: str, error_type: str, error_message: str = ""):
        """Add a detailed error for tracking and later reporting."""
        if not video_id:
            logger.debug(
                f"Attempted to log error with empty video ID. Type: {error_type}, Msg: {error_message}"
            )
            return

        self.errors_by_type[error_type].append(video_id)
        self.errors_by_video[video_id].append(
            {"type": error_type, "message": error_message}
        )
        self.error_counts[error_type] += 1

        log_message = f"[{video_id}] {error_type}: {error_message}"
        logger.debug(log_message)

    def has_errors(self) -> bool:
        """Check if any errors were recorded."""
        return len(self.error_counts) > 0

    def get_errors_by_video(self) -> dict[str, list[dict[str, str]]]:
        """Returns the dictionary mapping video IDs to their list of detailed errors."""
        return self.errors_by_video

    def clear(self):
        """Reset the error tracker."""
        self.errors_by_type.clear()
        self.errors_by_video.clear()
        self.error_counts.clear()
