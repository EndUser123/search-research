"""
Constants for download_handler.py.

Magic numbers extracted to named constants for better maintainability.
"""
from __future__ import annotations

# Default values
DEFAULT_NUMBER_OF_JOBS = 8
DEFAULT_PER_VIDEO_DELAY = 0.0

# Time-based multipliers
MILLISECONDS_PER_SECOND = 1000
SECONDS_PER_MINUTE = 60

# Time thresholds (milliseconds)
FAST_RESOLUTION_THRESHOLD_MS = 1000
SLOW_RESOLUTION_THRESHOLD_MS = 5000

# Channel ID validation
CHANNEL_ID_PREFIX = "UC"
CHANNEL_ID_LENGTH = 24
CHANNEL_ID_SHORT_DISPLAY_LENGTH = 8

# Logging levels
LOG_LEVEL_WARNING = 30
LOG_LEVEL_DEBUG = 10
