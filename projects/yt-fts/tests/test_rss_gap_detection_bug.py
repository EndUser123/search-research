"""
Tests for RSS gap detection logic bug.

Bug: When newest video is in DB but some RSS videos are missing, the code
had a missing return statement that caused fall-through to new_videos even
when gap_detected was intended.

Expected behavior:
- Small gaps (1-10 videos depending on DB size) with available videos should return 'new_videos'
- Large gaps OR failed availability checks should return 'gap_detected' (triggering full yt-api fetch)
"""

from unittest.mock import MagicMock, patch
import pytest


class TestRssGapDetectionBug:
    """
    Test the gap detection logic fix in RssPreChecker.check method.
    
    Scenario: RSS returns 15 videos, 14 are in DB, 1 is new.
    Expected: Return 'new_videos' with small gap message (not gap_detected).
    """

    def test_small_gap_with_available_videos_should_not_trigger_gap_detected(self):
        """
        Test that a small gap (1 video missing from 15 RSS videos) returns 'new_videos'.
        
        Given:
            - RSS returns 15 videos
            - 14 videos are in database (missing vid7)
            - 1 video is new (not in DB)
            - The new video is available (not scheduled/unavailable)
            - DB has 14 total videos (threshold = 3)
        
        When:
            check() is called
        
        Then:
            Should return 'new_videos' status (NOT 'gap_detected')
            Should NOT trigger expensive yt-api full fetch
        """
        from yt_fts.services.rss_precheck import RssPreChecker
        
        # Mock the availability check
        with patch.object(RssPreChecker, '_check_video_availability') as mock_avail:
            # Simulate: 1 missing video (vid7) that is available
            mock_avail.return_value = {"vid7": "available"}
            
            checker = RssPreChecker()
            
            # DB has 14 of 15 RSS videos (missing vid7, not the newest)
            # But vid0 IS in DB, so we enter the "newest in DB" gap detection path
            db_video_ids = {f"vid{i}" for i in range(15)} - {"vid7"}
            
            # Mock the HTTP response for RSS feed
            mock_response = MagicMock()
            mock_response.text = """
            <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
                <entry><yt:videoId>vid0</yt:videoId></entry>
                <entry><yt:videoId>vid1</yt:videoId></entry>
                <entry><yt:videoId>vid2</yt:videoId></entry>
                <entry><yt:videoId>vid3</yt:videoId></entry>
                <entry><yt:videoId>vid4</yt:videoId></entry>
                <entry><yt:videoId>vid5</yt:videoId></entry>
                <entry><yt:videoId>vid6</yt:videoId></entry>
                <entry><yt:videoId>vid7</yt:videoId></entry>
                <entry><yt:videoId>vid8</yt:videoId></entry>
                <entry><yt:videoId>vid9</yt:videoId></entry>
                <entry><yt:videoId>vid10</yt:videoId></entry>
                <entry><yt:videoId>vid11</yt:videoId></entry>
                <entry><yt:videoId>vid12</yt:videoId></entry>
                <entry><yt:videoId>vid13</yt:videoId></entry>
                <entry><yt:videoId>vid14</yt:videoId></entry>
            </feed>
            """
            mock_response.status_code = 200
            
            with patch('requests.get', return_value=mock_response):
                result = checker.check(
                    channel_id="UCxxx",
                    handle=None,
                    resolved_url="https://www.youtube.com/channel/UCxxx",
                    db_video_ids=db_video_ids
                )
            
            # Should return 'new_videos' with small gap message, NOT 'gap_detected'
            assert result.status == "new_videos", \
                f"Expected 'new_videos' for small gap, got '{result.status}': {result.message}"
            assert "small gap" in result.message.lower(), \
                f"Expected 'small gap' in message, got: {result.message}"

    def test_small_gap_with_empty_availability_should_trigger_gap_detected(self):
        """
        Test that a small gap with empty availability dict returns 'gap_detected'.
        
        When availability check returns empty dict (failure/timeout), the code
        should return 'gap_detected' to trigger the safe path (yt-api full fetch).
        
        This ensures we don't miss any videos when availability check fails.
        """
        from yt_fts.services.rss_precheck import RssPreChecker
        
        # Mock the availability check to return empty dict
        with patch.object(RssPreChecker, '_check_video_availability') as mock_avail:
            # Simulate: availability check returns empty (timeout/failure)
            mock_avail.return_value = {}
            
            checker = RssPreChecker()
            
            # DB has 14 of 15 RSS videos (missing vid7)
            db_video_ids = {f"vid{i}" for i in range(15)} - {"vid7"}
            
            # Mock the HTTP response for RSS feed
            mock_response = MagicMock()
            mock_response.text = """
            <feed xmlns:yt="http://www.youtube.com/xml/schemas/2015" xmlns="http://www.w3.org/2005/Atom">
                <entry><yt:videoId>vid0</yt:videoId></entry>
                <entry><yt:videoId>vid1</yt:videoId></entry>
                <entry><yt:videoId>vid2</yt:videoId></entry>
                <entry><yt:videoId>vid3</yt:videoId></entry>
                <entry><yt:videoId>vid4</yt:videoId></entry>
                <entry><yt:videoId>vid5</yt:videoId></entry>
                <entry><yt:videoId>vid6</yt:videoId></entry>
                <entry><yt:videoId>vid7</yt:videoId></entry>
                <entry><yt:videoId>vid8</yt:videoId></entry>
                <entry><yt:videoId>vid9</yt:videoId></entry>
                <entry><yt:videoId>vid10</yt:videoId></entry>
                <entry><yt:videoId>vid11</yt:videoId></entry>
                <entry><yt:videoId>vid12</yt:videoId></entry>
                <entry><yt:videoId>vid13</yt:videoId></entry>
                <entry><yt:videoId>vid14</yt:videoId></entry>
            </feed>
            """
            mock_response.status_code = 200
            
            with patch('requests.get', return_value=mock_response):
                result = checker.check(
                    channel_id="UCxxx",
                    handle=None,
                    resolved_url="https://www.youtube.com/channel/UCxxx",
                    db_video_ids=db_video_ids
                )
            
            # CORRECT: Returns 'gap_detected' to trigger safe yt-api full fetch
            # When availability check fails, we use the safe path to ensure we don't miss videos
            assert result.status == "gap_detected", \
                f"Expected 'gap_detected' for failed availability check, got '{result.status}'"
            assert "Gap detected" in result.message or "gap" in result.message.lower(), \
                f"Expected gap in message, got: {result.message}"
