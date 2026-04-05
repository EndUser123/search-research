"""
Constants for batch_downloader.py.

Magic numbers extracted to named constants for better maintainability.
"""
from __future__ import annotations

# Database operations
BATCH_COMMIT_INTERVAL = 50

# Timeouts (seconds)
DB_CONNECTION_TIMEOUT = 10.0
DB_CONNECTION_SHORT_TIMEOUT = 5.0
RSS_CHECK_TIMEOUT = 10.0
RSS_CHECK_SHORT_TIMEOUT = 5.0

# Display formatting
DISPLAY_COLUMN_WIDTH = 40
HEADER_SEPARATOR_WIDTH = 60

# Subscriber count thresholds (for formatting)
SUBSCRIBER_COUNT_MILLION = 1_000_000
SUBSCRIBER_COUNT_TEN_THOUSAND = 10_000

# Time conversion
SECONDS_PER_HOUR = 3600

# Progress display
DEFAULT_QUOTA_PERCENTAGE = 50

# String markers
INVALID_CHANNEL_MARKER = "__INVALID_CHANNEL__"
