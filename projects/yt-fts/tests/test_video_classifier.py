"""Tests for video classification module.

This module tests the video classifier which categorizes videos as:
- NORMAL: Standard video with subtitles available
- SHORT: YouTube Short
- SCHEDULED: Scheduled/upcoming video
- MEMBERS_ONLY: Members-only content
- UNAVAILABLE: Unavailable/private/deleted video
- NO_SUBTITLES: Video available but no captions
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from yt_fts.discovery.video_classifier import (
    VideoType,
    classify_video,
    is_short_video,
    is_scheduled_video,
    has_no_subtitles,
)


class TestVideoClassification:
    """Test video type classification logic."""

    def test_classify_normal_video(self):
        """NORMAL: Standard video with subtitles available."""
        info = {
            "url": "https://www.youtube.com/watch?v=abc123",
            "id": "abc123",
            "subtitles": {"en": [{"url": "..."}]},
            "automatic_captions": {},
        }

        result = classify_video(info)
        assert result["video_type"] == VideoType.NORMAL.value  # Compare to value
        assert result["downloadable"] is True
        assert result["retryable"] is False

    def test_classify_short_video_by_url(self):
        """SHORT: URL contains /shorts/."""
        info = {
            "url": "https://www.youtube.com/shorts/abc123",
            "id": "abc123",
            "subtitles": {"en": [{"url": "..."}]},
        }

        result = classify_video(info)
        assert result["video_type"] == VideoType.SHORT.value
        assert result["downloadable"] is True

    def test_classify_scheduled_video(self):
        """SCHEDULED: live_status=is_upcoming."""
        info = {
            "url": "https://www.youtube.com/watch?v=abc123",
            "id": "abc123",
            "live_status": "is_upcoming",
            "subtitles": {},
        }

        result = classify_video(info)
        assert result["video_type"] == VideoType.SCHEDULED.value
        assert result["downloadable"] is False

    def test_classify_members_only_video(self):
        """MEMBERS_ONLY: availability=members_only."""
        info = {
            "url": "https://www.youtube.com/watch?v=abc123",
            "id": "abc123",
            "availability": "members_only",
            "subtitles": {},
        }

        result = classify_video(info)
        assert result["video_type"] == VideoType.MEMBERS_ONLY.value
        assert result["downloadable"] is False

    def test_classify_unavailable_video(self):
        """UNAVAILABLE: Video unavailable or deleted."""
        info = {
            "url": "https://www.youtube.com/watch?v=abc123",
            "id": "abc123",
            "availability": "unavailable",
            "subtitles": {},
        }

        result = classify_video(info)
        assert result["video_type"] == VideoType.UNAVAILABLE.value
        assert result["downloadable"] is False

    def test_classify_no_subtitles(self):
        """NO_SUBTITLES: Video available but no captions."""
        info = {
            "url": "https://www.youtube.com/watch?v=abc123",
            "id": "abc123",
            "subtitles": {},
            "automatic_captions": {},
            "availability": "public",
        }

        result = classify_video(info)
        assert result["video_type"] == VideoType.NO_SUBTITLES.value
        assert result["downloadable"] is False


class TestClassificationHelpers:
    """Test classification helper functions."""

    def test_is_short_video_by_url(self):
        """Detects short videos by URL."""
        assert is_short_video("https://www.youtube.com/shorts/abc123") is True
        assert is_short_video("https://www.youtube.com/watch?v=abc123") is False

    def test_is_short_video_by_flag(self):
        """Detects short videos by is_short flag."""
        assert is_short_video("https://www.youtube.com/watch?v=abc123", is_short=1) is True
        assert is_short_video("https://www.youtube.com/watch?v=abc123", is_short=0) is False

    def test_is_scheduled_video(self):
        """Detects scheduled videos by live_status."""
        info = {"live_status": "is_upcoming"}
        assert is_scheduled_video(info) is True

        info = {"live_status": "was_live"}
        assert is_scheduled_video(info) is False

    def test_is_scheduled_video_utc_timestamp(self):
        """Scheduled video with UTC timestamp handles timezone correctly."""
        # Video scheduled for future (UTC timestamp)
        future_time = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        info = {
            "release_timestamp": future_time,
        }

        result = is_scheduled_video(info)
        assert result is True, "Future UTC timestamp should be classified as scheduled"

    def test_has_no_subtitles(self):
        """Detects videos with no subtitles."""
        info = {"subtitles": {}, "automatic_captions": {}}
        assert has_no_subtitles(info) is True

        info = {"subtitles": {"en": [...]}, "automatic_captions": {}}
        assert has_no_subtitles(info) is False


class TestEdgeCasesMalformedDicts:
    """Test edge cases with malformed or incomplete dictionaries."""

    def test_classify_empty_dict(self):
        """EMPTY: Empty info dict has no subtitles (fallback behavior)."""
        info = {}
        result = classify_video(info)
        # Empty dict has no subtitles key, falls through to NO_SUBTITLES
        assert result["video_type"] == VideoType.NO_SUBTITLES.value
        assert result["downloadable"] is False

    def test_classify_missing_url(self):
        """MISSING URL: Classifies with empty URL."""
        info = {"subtitles": {"en": [{"url": "..."}]}}
        result = classify_video(info)
        assert result["url"] == ""
        assert result["video_type"] == VideoType.NORMAL.value

    def test_classify_missing_id(self):
        """MISSING ID: Classifies with empty video_id."""
        info = {"subtitles": {"en": [{"url": "..."}]}}
        result = classify_video(info)
        assert result["video_id"] == ""

    def test_classify_none_subtitles(self):
        """NONE: Subtitles key present but None."""
        info = {"subtitles": None, "automatic_captions": None}
        result = classify_video(info)
        assert result["video_type"] == VideoType.NO_SUBTITLES.value

    def test_classify_subtitles_list_none_values(self):
        """NONE VALUES: Subtitles list contains None entries."""
        info = {"subtitles": {"en": [None, None]}, "automatic_captions": {}}
        result = classify_video(info)
        # Has subtitles key with entries, so treated as available
        assert result["video_type"] == VideoType.NORMAL.value

    def test_classify_invalid_release_timestamp(self):
        """INVALID TIMESTAMP: Malformed release_timestamp is handled gracefully."""
        info = {
            "subtitles": {},
            "automatic_captions": {},
            "release_timestamp": "invalid-iso-format",
        }
        # Should not crash, should fall through to NO_SUBTITLES
        result = classify_video(info)
        assert result["video_type"] == VideoType.NO_SUBTITLES.value

    def test_classify_availability_private(self):
        """PRIVATE: availability=private is treated as unavailable."""
        info = {"availability": "private", "subtitles": {}}
        result = classify_video(info)
        assert result["video_type"] == VideoType.UNAVAILABLE.value
        assert result["retryable"] is False


class TestBoundaryConditions:
    """Test boundary conditions and edge values."""

    def test_is_short_video_case_variations(self):
        """CASE VARIATIONS: Shorts detection is case-sensitive."""
        # Lowercase /shorts/ works
        assert is_short_video("https://www.youtube.com/shorts/abc123") is True
        # Uppercase /SHORTS/ should NOT match (URL is case-sensitive)
        assert is_short_video("https://www.youtube.com/SHORTS/abc123") is False

    def test_is_short_video_query_param(self):
        """QUERY PARAM: URL with shorts in query param (not path)."""
        # shorts in query param should NOT trigger short detection
        assert is_short_video("https://www.youtube.com/watch?v=abc123&shorts") is False

    def test_is_scheduled_video_exactly_now(self):
        """BOUNDARY: Release timestamp is exactly now."""
        now = datetime.now(timezone.utc).isoformat()
        info = {"release_timestamp": now}
        # Exactly now should NOT be scheduled (not in future)
        assert is_scheduled_video(info) is False

    def test_is_scheduled_video_one_second_future(self):
        """BOUNDARY: Release timestamp is 1 second in future."""
        future = (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat()
        info = {"release_timestamp": future}
        assert is_scheduled_video(info) is True

    def test_is_scheduled_video_one_second_past(self):
        """BOUNDARY: Release timestamp is 1 second in past."""
        past = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        info = {"release_timestamp": past}
        assert is_scheduled_video(info) is False

    def test_has_no_subtitles_empty_list(self):
        """EMPTY LIST: Subtitles exists but is empty list."""
        info = {"subtitles": [], "automatic_captions": []}
        # Empty list is falsy, should return True (no subtitles)
        result = has_no_subtitles(info)
        assert result is True

    def test_has_no_subtitles_autocaptions_only(self):
        """AUTOCAPTIONS ONLY: Has automatic captions but no manual subtitles."""
        info = {"subtitles": {}, "automatic_captions": {"en": [{"url": "..."}]}}
        result = has_no_subtitles(info)
        assert result is False  # Auto captions count as subtitles

    def test_classify_with_title_none(self):
        """NONE TITLE: Title is None or missing."""
        info = {"subtitles": {}, "automatic_captions": {}}
        result = classify_video(info)
        assert result["title"] == ""
        assert result["video_type"] == VideoType.NO_SUBTITLES.value

