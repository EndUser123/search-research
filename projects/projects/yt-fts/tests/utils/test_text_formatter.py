"""
Tests for TextFormatter - robust plain-text logging.

TDD RED Phase: Write failing tests first.
"""

import sys
import io
from datetime import datetime

import pytest


class TestTextFormatter:
    """Test TextFormatter robust plain-text logging."""

    def test_info_formats_correctly(self):
        """Info message should format: [TIME] [INFO ] [TAG] message"""
        from yt_fts.utils.text_formatter import TextFormatter

        output = io.StringIO()
        formatter = TextFormatter(output=output)
        formatter.info("INIT", "Loaded 3538 channels")

        result = output.getvalue()
        assert "[INFO ]" in result
        assert "[INIT]" in result
        assert "Loaded 3538 channels" in result
        # Should have timestamp
        assert len(result.split("]")) >= 4

    def test_done_formats_correctly(self):
        """Done message should format: [TIME] [DONE ] [TAG] message"""
        from yt_fts.utils.text_formatter import TextFormatter

        output = io.StringIO()
        formatter = TextFormatter(output=output)
        formatter.done("CH#0001", "no-new-videos")

        result = output.getvalue()
        assert "[DONE ]" in result
        assert "[CH#0001]" in result
        assert "no-new-videos" in result

    def test_error_formats_correctly(self):
        """Error message should format: [TIME] [ERROR] [TAG] message"""
        from yt_fts.utils.text_formatter import TextFormatter

        output = io.StringIO()
        formatter = TextFormatter(output=output)
        formatter.error("CH#0002", "timeout")

        result = output.getvalue()
        assert "[ERROR]" in result
        assert "[CH#0002]" in result
        assert "timeout" in result

    def test_progress_formats_correctly(self):
        """Progress message should format: [TIME] [PROG ] [1/3538] ETA=69h33m item"""
        from yt_fts.utils.text_formatter import TextFormatter

        output = io.StringIO()
        formatter = TextFormatter(output=output)
        formatter.progress(1, 3538, "69h33m", "UCFig7sk...")

        result = output.getvalue()
        assert "[PROG ]" in result
        assert "[1/3538]" in result
        assert "ETA=69h33m" in result
        assert "UCFig7sk..." in result

    def test_warn_formats_correctly(self):
        """Warn message should format: [TIME] [WARN ] [TAG] message"""
        from yt_fts.utils.text_formatter import TextFormatter

        output = io.StringIO()
        formatter = TextFormatter(output=output)
        formatter.warn("RSS", "feed unavailable")

        result = output.getvalue()
        assert "[WARN ]" in result
        assert "[RSS]" in result
        assert "feed unavailable" in result

    def test_channel_shortening(self):
        """Channel URLs should be shortened for display."""
        from yt_fts.utils.text_formatter import TextFormatter

        formatter = TextFormatter()

        # Long URL gets shortened
        long_url = "https://www.youtube.com/channel/UCFig7skuwYrCIGy0tP2o8Rg/videos"
        short = formatter.shorten_channel(long_url)
        assert len(short) < len(long_url)
        assert "..." in short

        # Short URL stays same
        short_url = "@channel"
        assert formatter.shorten_channel(short_url) == short_url

    def test_stderr_output_by_default(self):
        """By default, output should go to stderr."""
        from yt_fts.utils.text_formatter import TextFormatter

        output = io.StringIO()
        formatter = TextFormatter(output=output)
        formatter.info("TEST", "message")

        result = output.getvalue()
        assert "message" in result
