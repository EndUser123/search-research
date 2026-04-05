# tests/test_filtering.py

import pytest
from yt_sync.filtering import VideoFilterer


class TestVideoFilterer:
    """Test suite for VideoFilterer class."""

    @pytest.fixture
    def sample_metadata(self):
        """Fixture providing sample video metadata for testing."""
        return {
            "video1": {
                "title": "Test Video One",
                "description": "This is a test description for video one.",
                "tags": ["test", "video"],
                "duration": 300,
                "view_count": 1000,
                "like_count": 100,
                "upload_date": "20230101",
                "is_live": False,
                "was_live": False,
                "categories": ["Education"],
            },
            "video2": {
                "title": "Live Stream Video",
                "description": "A live stream event.",
                "tags": ["live", "event"],
                "duration": 1800,
                "view_count": 5000,
                "like_count": 500,
                "upload_date": "20221201",
                "is_live": True,
                "was_live": True,
                "categories": ["Entertainment"],
            },
            "video3": {
                "title": "Short Clip",
                "description": "A quick short clip.",
                "tags": ["short"],
                "duration": 60,
                "view_count": 200,
                "like_count": 20,
                "upload_date": "20230215",
                "is_live": False,
                "was_live": False,
                "categories": ["Shorts"],
            },
        }

    @pytest.fixture
    def empty_filter(self):
        """Fixture for a filter with no rules."""
        return VideoFilterer({})

    @pytest.fixture
    def complex_filter(self):
        """Fixture for a filter with multiple rules."""
        return VideoFilterer(
            {
                "require_title": ["Test"],
                "reject_title": ["Banned"],
                "require_description": ["test"],
                "reject_description": ["forbidden"],
                "require_tags": ["test"],
                "reject_tags": ["bad"],
                "min_duration": 120,
                "max_duration": 3600,
                "min_views": 500,
                "max_views": 10000,
                "min_likes": 50,
                "max_likes": 1000,
                "after_date": "20221231",
                "before_date": "20231231",
                "require_live": False,
                "reject_live": False,
                "require_category": "Education",
                "reject_category": "Gaming",
            }
        )

    def test_init_empty_filters(self, empty_filter):
        """Test initialization with no filters."""
        assert empty_filter.rules == {}
        assert empty_filter.skip is False

    def test_init_with_skip(self):
        """Test initialization with skip flag."""
        filterer = VideoFilterer({"skip": True})
        assert filterer.skip is True

    def test_init_with_rules(self, complex_filter):
        """Test initialization with multiple filter rules."""
        assert len(complex_filter.rules) > 0
        assert "require_title" in complex_filter.rules
        assert complex_filter.rules["min_duration"] == 120

    def test_apply_filters_no_rules(self, empty_filter, sample_metadata):
        """Test apply_filters with no rules; all videos should pass."""
        ids_to_check = set(sample_metadata.keys())
        result = empty_filter.apply_filters(ids_to_check, sample_metadata)
        assert result == ids_to_check

    def test_apply_filters_with_rules(self, complex_filter, sample_metadata):
        """Test apply_filters with rules; only matching videos should pass."""
        ids_to_check = set(sample_metadata.keys())
        result = complex_filter.apply_filters(ids_to_check, sample_metadata)
        assert "video1" in result
        assert "video2" not in result  # Fails due to live status or other rules
        assert "video3" not in result  # Fails due to duration or views

    def test_video_passes_all_rules(self, complex_filter, sample_metadata):
        """Test _video_passes_all_rules with a specific video."""
        assert complex_filter._video_passes_all_rules(sample_metadata["video1"]) is True
        assert (
            complex_filter._video_passes_all_rules(sample_metadata["video2"]) is False
        )

    def test_check_text_fail_required_missing(self):
        """Test _check_text_fail when required text is missing."""
        filterer = VideoFilterer({"require_title": ["Missing"]})
        assert filterer._check_text_fail("Test Video", ["Missing"], None) is True

    def test_check_text_fail_rejected_present(self):
        """Test _check_text_fail when rejected text is present."""
        filterer = VideoFilterer({"reject_title": ["Test"]})
        assert filterer._check_text_fail("Test Video", None, ["Test"]) is True

    def test_check_text_fail_passes(self):
        """Test _check_text_fail when text passes filters."""
        filterer = VideoFilterer({})
        assert filterer._check_text_fail("Test Video", ["Test"], None) is False

    def test_check_tags_fail_required_missing(self):
        """Test _check_tags_fail when required tags are missing."""
        filterer = VideoFilterer({"require_tags": ["missing"]})
        assert filterer._check_tags_fail(["test"], ["missing"], None) is True

    def test_check_tags_fail_rejected_present(self):
        """Test _check_tags_fail when rejected tags are present."""
        filterer = VideoFilterer({"reject_tags": ["test"]})
        assert filterer._check_tags_fail(["test"], None, ["test"]) is True

    def test_check_tags_fail_passes(self):
        """Test _check_tags_fail when tags pass filters."""
        filterer = VideoFilterer({})
        assert filterer._check_tags_fail(["test"], ["test"], None) is False

    def test_check_numeric_fail_below_min(self):
        """Test _check_numeric_fail when value is below minimum."""
        filterer = VideoFilterer({"min_duration": 100})
        assert filterer._check_numeric_fail(50, 100, None) is True

    def test_check_numeric_fail_above_max(self):
        """Test _check_numeric_fail when value is above maximum."""
        filterer = VideoFilterer({"max_duration": 100})
        assert filterer._check_numeric_fail(150, None, 100) is True

    def test_check_numeric_fail_passes(self):
        """Test _check_numeric_fail when value passes filters."""
        filterer = VideoFilterer({})
        assert filterer._check_numeric_fail(75, 50, 100) is False

    def test_check_date_fail_before_after_date(self):
        """Test _check_date_fail when date is before the after_date."""
        filterer = VideoFilterer({"after_date": "20230101"})
        assert filterer._check_date_fail("20221201", "20230101", None) is True

    def test_check_date_fail_after_before_date(self):
        """Test _check_date_fail when date is after the before_date."""
        filterer = VideoFilterer({"before_date": "20230101"})
        assert filterer._check_date_fail("20230201", None, "20230101") is True

    def test_check_date_fail_passes(self):
        """Test _check_date_fail when date passes filters."""
        filterer = VideoFilterer({})
        assert filterer._check_date_fail("20230101", "20221201", "20231201") is False

    def test_check_live_status_fail_require_not_live(self):
        """Test _check_live_status_fail when live status is required but not live."""
        filterer = VideoFilterer({"require_live": True})
        metadata = {"is_live": False, "was_live": False}
        assert filterer._check_live_status_fail(metadata, True, None) is True

    def test_check_live_status_fail_reject_live(self):
        """Test _check_live_status_fail when live status is rejected and is live."""
        filterer = VideoFilterer({"reject_live": True})
        metadata = {"is_live": True, "was_live": True}
        assert filterer._check_live_status_fail(metadata, None, True) is True

    def test_check_live_status_fail_passes(self):
        """Test _check_live_status_fail when live status passes filters."""
        filterer = VideoFilterer({})
        metadata = {"is_live": False, "was_live": False}
        assert filterer._check_live_status_fail(metadata, False, False) is False

    def test_check_category_fail_required_missing(self):
        """Test _check_category_fail when required category is missing."""
        filterer = VideoFilterer({"require_category": "Missing"})
        assert filterer._check_category_fail(["Other"], "Missing", None) is True

    def test_check_category_fail_rejected_present(self):
        """Test _check_category_fail when rejected category is present."""
        filterer = VideoFilterer({"reject_category": "Other"})
        assert filterer._check_category_fail(["Other"], None, "Other") is True

    def test_check_category_fail_passes(self):
        """Test _check_category_fail when category passes filters."""
        filterer = VideoFilterer({})
        assert filterer._check_category_fail(["Education"], "Education", None) is False
