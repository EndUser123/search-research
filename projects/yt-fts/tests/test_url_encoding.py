"""
Tests for URL encoding/decoding to prevent double-encoding issues.

The bug: When a channel URL with special characters (like pipe) is:
1. First encoded and stored in database
2. Then passed through validate_channel_url again
3. Gets double-encoded (percent sign becomes %25)
"""

import pytest
from yt_fts.download.url_utils import validate_channel_url


class TestURLEncoding:
    """Test URL encoding to prevent double-encoding bugs."""

    def test_handle_with_pipe_gets_encoded(self):
        """First pass: pipe character should be encoded."""
        result = validate_channel_url("https://www.youtube.com/@Marvomatic|AIAutomations")
        assert result is not None
        encoded_pipe = "%7C"  # URL-encoded pipe
        double_encoded = "%257C"  # Double-encoded pipe (wrong!)
        assert encoded_pipe in result
        assert double_encoded not in result

    def test_already_encoded_handle_does_not_double_encode(self):
        """Second pass: already-encoded URL should not be encoded again.
        
        This simulates loading from database where URL was already encoded.
        """
        # This is what would be stored in DB after first encoding
        already_encoded = "https://www.youtube.com/@Marvomatic%7CAIAutomations"
        result = validate_channel_url(already_encoded)
        assert result is not None
        # Should remain as %7C, NOT become %257C
        double_encoded = "%257C"
        assert double_encoded not in result, f"Got double-encoded: {result}"

    def test_normal_handle_unchanged(self):
        """Normal handles without special characters work as before."""
        result = validate_channel_url("https://www.youtube.com/@PaulDickson")
        assert result == "https://www.youtube.com/@PaulDickson/videos"

    def test_channel_id_format_unchanged(self):
        """Channel ID format should not be affected by encoding logic."""
        result = validate_channel_url("https://www.youtube.com/channel/UCxxxxxx")
        assert result == "https://www.youtube.com/channel/UCxxxxxx/videos"

    def test_multiple_special_chars(self):
        """Handles with multiple special characters are encoded once."""
        result = validate_channel_url("https://www.youtube.com/@test|handle&more")
        assert result is not None
        # Should encode both pipe and ampersand
        assert "%7C" in result  # pipe encoded
        assert "%26" in result  # ampersand encoded
        # Should NOT double-encode
        assert "%257C" not in result
        assert "%2526" not in result
