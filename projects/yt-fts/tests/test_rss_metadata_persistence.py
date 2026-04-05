"""
Tests for RSS metadata persistence to database.

When RSS discovers a new video, it should save basic metadata (title, date, URL)
to the database so that subsequent runs don't treat it as "new" again.
"""

from unittest.mock import patch, MagicMock

import pytest


class TestRSSMetadataPersistence:
    """Test that RSS-discovered videos are saved to database with metadata."""

    def test_rss_check_result_has_video_metadata_field(self):
        """RSS check result should include video metadata field."""
        from yt_fts.services.rss_precheck import RssCheckResult

        # Test that video_metadata field exists and can be set
        result = RssCheckResult(
            status="new_videos",
            video_ids=["abc123"],
            newest_id="abc123",
            oldest_id="abc123",
            message="1 new videos found",
            video_metadata={"abc123": {"title": "Test", "date": "", "url": ""}}
        )

        assert hasattr(result, "video_metadata"), "RssCheckResult should include video_metadata"
        assert result.video_metadata is not None, "video_metadata should not be None"
        assert result.video_metadata["abc123"]["title"] == "Test"

    def test_rss_parser_extracts_video_titles(self):
        """RSS parser should extract video titles from feed XML."""
        from yt_fts.services.rss_precheck import RssPreChecker

        # Sample RSS feed XML matching real YouTube RSS format
        # Real YouTube RSS uses default namespace (xmlns="...") not atom: prefix
        rss_xml = """
        <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <yt:videoId>abc123</yt:videoId>
                <title>Test Video Title</title>
                <published>2026-01-12T10:00:00+00:00</published>
                <link rel="alternate" href="https://www.youtube.com/watch?v=abc123"/>
            </entry>
            <entry>
                <yt:videoId>def456</yt:videoId>
                <title>Another Video</title>
                <published>2026-01-11T10:00:00+00:00</published>
                <link rel="alternate" href="https://www.youtube.com/watch?v=def456"/>
            </entry>
        </feed>
        """

        checker = RssPreChecker()

        # After implementation, this should return metadata
        result = checker._parse_video_ids_with_metadata(rss_xml)

        assert result is not None, "Parser should return video metadata"
        assert "abc123" in result, "Should contain first video ID"
        assert result["abc123"]["title"] == "Test Video Title", "Should extract title"
        assert result["abc123"]["date"] == "2026-01-12T10:00:00+00:00", "Should extract date"
        assert result["abc123"]["url"] == "https://www.youtube.com/watch?v=abc123", "Should extract URL"

    def test_rss_parser_skips_shorts(self):
        """RSS parser should skip Shorts videos."""
        from yt_fts.services.rss_precheck import RssPreChecker

        rss_xml = """
        <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <yt:videoId>abc123</yt:videoId>
                <title>Regular Video</title>
                <link rel="alternate" href="https://www.youtube.com/watch?v=abc123"/>
            </entry>
            <entry>
                <yt:videoId>def456</yt:videoId>
                <title>A Short Video</title>
                <link rel="alternate" href="https://www.youtube.com/shorts/def456"/>
            </entry>
        </feed>
        """

        checker = RssPreChecker()
        result = checker._parse_video_ids_with_metadata(rss_xml)

        assert "abc123" in result, "Should include regular video"
        assert "def456" not in result, "Should skip Short"

    def test_save_rss_videos_to_db_saves_metadata(self):
        """Test _save_rss_videos_to_db function saves videos with metadata."""
        from unittest.mock import patch
        import yt_fts.db.videos

        # Create a mock database
        channel_id = "UCtest_rss_save"
        video_id = "rss123"
        video_metadata = {
            video_id: {
                "title": "RSS Test Video",
                "date": "2026-01-12T10:00:00+00:00",
                "url": "https://www.youtube.com/watch?v=rss123"
            }
        }

        # Patch add_video BEFORE importing _save_rss_videos_to_db
        # The function imports add_video internally, so patch must be in place first
        with patch("yt_fts.db.videos.add_video") as mock_add_video:
            # Import AFTER patch is active
            from yt_fts.services.rss_precheck import _save_rss_videos_to_db

            _save_rss_videos_to_db(channel_id, [video_id], video_metadata)

        # Verify the call
        assert mock_add_video.called, "add_video should be called"
        assert mock_add_video.call_count == 1, "Should save one video"

        # Check the keyword arguments (add_video uses kwargs, not positional args)
        call_kwargs = mock_add_video.call_args.kwargs
        assert call_kwargs["video_id"] == video_id, "Should save correct video_id"
        assert call_kwargs["video_title"] == "RSS Test Video", "Should save correct title"
        assert call_kwargs["channel_id"] == channel_id, "Should save correct channel_id"

    def test_full_rss_check_includes_metadata_in_result(self):
        """Integration: RSS check should return video_metadata."""
        from yt_fts.services.rss_precheck import create_rss_checker

        rss_xml = """
        <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <yt:videoId>test123</yt:videoId>
                <title>Test Video From RSS</title>
                <published>2026-01-12T10:00:00+00:00</published>
                <link rel="alternate" href="https://www.youtube.com/watch?v=test123"/>
            </entry>
        </feed>
        """

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = rss_xml

        checker = create_rss_checker()

        with patch("requests.get", return_value=mock_response):
            result = checker.check(
                channel_id="UCtest123",
                handle=None,
                resolved_url="https://www.youtube.com/channel/UCtest123",
                db_video_ids=set()  # Empty DB = all videos are new
            )

        # Should include video_metadata in result
        assert hasattr(result, "video_metadata")
        assert result.video_metadata is not None
        assert "test123" in result.video_metadata
        assert result.video_metadata["test123"]["title"] == "Test Video From RSS"
