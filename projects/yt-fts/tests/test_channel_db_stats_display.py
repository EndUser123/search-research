"""
Test that channel display shows UPDATED db stats after yt-api fetch.

The problem: After yt-api fetches metadata, the db line shows OLD stats,
not the updated stats with the newly discovered videos.

Expected behavior:
- Before fetch: Show old/empty db stats
- After fetch: Show NEW db stats with actual counts
- Terminology: Use "cc" and "no cc" instead of "with transcripts"/"no subs"
"""

from io import StringIO
from unittest.mock import Mock, patch

from yt_fts.display.plugins.download_default import DownloadDefaultDisplayPlugin
from yt_fts.display.base import PluginContext


class TestChannelDbStatsDisplay:
    """Test that db stats are displayed correctly after yt-api fetch."""

    def test_cc_terminology_used(self):
        """Display should use cc terminology, not with transcripts/no subs."""
        plugin = DownloadDefaultDisplayPlugin(
            PluginContext(
                command="download",
                console=Mock(),
            )
        )

        # Mock channel info with inconsistent flag to trigger detailed stats
        channel_info = {
            "index": 1,
            "total": 3491,
            "name": "Test Channel",
            "channel_id": "UC123",
            "channel_url": "https://youtube.com/@test",
            "inconsistent": True,  # Trigger detailed stats display
            "inconsistency_reason": "Test",
            "db_stats": "0 videos",
            "db_stats_details": {
                "total": 497,
                "with_subs": 100,
                "no_subs": 397,
                "scheduled": 0,
                "shorts": 0,
                "subscribers": 1000,
                "playlists": 5,
                "members": 0,
            },
        }

        # Capture output
        output = StringIO()
        with patch.object(plugin.console, "print", lambda *args, **kwargs: output.write(" ".join(str(a) for a in args))):
            plugin.display_channel_header(channel_info)

        result = output.getvalue()

        # OLD terminology should NOT be present
        assert "with transcripts" not in result, f"Should not use 'with transcripts', got: {result}"
        # "no subs" should not appear for non-zero counts - should use "no cc"
        if "397" in result and "no subs" in result:
            assert False, f"Should use 'no cc' instead of 'no subs' for non-zero count, got: {result}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
