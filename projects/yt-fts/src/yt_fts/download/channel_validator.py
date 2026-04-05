from __future__ import annotations

"""
Channel validation utilities for batch downloader.

Extracted from batch_downloader.py to separate concerns.
"""

import logging
import re

logger = logging.getLogger(__name__)


class ChannelValidator:
    """
    Validates YouTube channel IDs, handles, and URLs.

    Provides validation logic for different YouTube channel input formats:
    - Channel IDs: UC prefix, exactly 24 chars, alphanumeric only
    - Handles: @ prefix, alphanumeric and underscore only, no spaces
    - URLs: must be youtube.com domain
    """

    def is_raw_channel_id(self, name: str) -> bool:
        """
        Check if a name is a raw channel ID rather than a human-readable name.

        Args:
            name: The channel name to check

        Returns:
            True if the name appears to be a raw channel ID
        """
        return (
            name.startswith("Channel UC")
            or (name.startswith("UC") and len(name) >= 20)
            or name == "__INVALID_CHANNEL__"
        )

    def validate_channel_input(self, url_or_id: str) -> bool:
        """
        Validate channel ID, handle, or URL.

        Args:
            url_or_id: Channel ID, handle, or URL to validate

        Returns:
            True if input is valid, False otherwise

        Validation rules:
        - Channel IDs: UC prefix, exactly 24 chars, alphanumeric only
        - Handles: @ prefix, alphanumeric and underscore only, no spaces
        - URLs: must be youtube.com domain
        """
        # YouTube channel ID: UC + 22 alphanumeric characters (24 total)
        if url_or_id.startswith("UC"):
            if len(url_or_id) != 24:
                return False
            if not re.match(r"^UC[A-Za-z0-9_-]{22}$", url_or_id):
                return False
            return True

        # YouTube handle: @ + username (alphanumeric, underscore, hyphen)
        if url_or_id.startswith("@"):
            if not re.match(r"^@[A-Za-z0-9_-]+$", url_or_id):
                return False
            if len(url_or_id) < 2:
                return False
            return True

        # Full URL - must be youtube.com domain
        if url_or_id.startswith("http"):
            if "youtube.com" not in url_or_id:
                return False
            if not re.match(r"^https?://", url_or_id):
                return False
            return True

        return False
