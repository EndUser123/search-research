"""
Tests for EmbeddingsHandler in get_embeddings.py.

These tests verify the behavior of the EmbeddingsHandler class.
Run with: pytest tests/test_llm_get_embeddings.py -v

RED PHASE: Tests written to verify expected behavior.
Some tests may fail initially - this is expected for TDD.
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from yt_fts.llm.get_embeddings import EmbeddingsHandler


@pytest.fixture
def handler():
    """Create EmbeddingsHandler instance for testing."""
    return EmbeddingsHandler(interval=10)


class TestAddMetaDataToText:
    """Tests for add_meta_data_to_text method."""

    @pytest.fixture
    def handler(self):
        return EmbeddingsHandler(interval=10)

    def test_metadata_prepended_to_text(self, handler):
        """
        Test that metadata is correctly prepended to text.

        Given: A handler, channel name, video title, video date, and segment
        When: add_meta_data_to_text is called
        Then: The returned text has metadata formatted correctly at the top
        """
        # Arrange
        channel_name = "Test Channel"
        video_title = "Test Video Title"
        video_date = date(2024, 1, 15)
        segment = {
            "start_time": "00:01:30.500",
            "text": "This is the subtitle content."
        }

        # Act
        result = handler.add_meta_data_to_text(
            channel_name, video_title, video_date, segment
        )

        # Assert - verify exact format
        assert "---" in result
        assert "video_title: Test Video Title" in result
        assert "channel_name: Test Channel" in result
        assert "video_date: 2024-01-15" in result
        assert "segment_start_time: 00:01:30.500" in result
        # Content section
        assert "Content:" in result
        assert "This is the subtitle content." in result


class TestSplitSubtitles:
    """Tests for split_subtitles method."""

    @pytest.fixture
    def handler(self):
        return EmbeddingsHandler(interval=10)

    def test_returns_none_if_video_too_short(self, handler):
        """
        Test that None is returned when video is shorter than interval.

        Given: A video with total duration less than the interval (10 seconds)
        When: split_subtitles is called
        Then: None is returned
        """
        # Arrange - Mock subtitles for a 5 second video
        mock_subs = [
            ("00:00:00.000", "00:00:02.500", "First text"),
            ("00:00:02.500", "00:00:05.000", "Second text"),
        ]

        with patch("yt_fts.llm.get_embeddings.get_subs_by_video_id") as mock_get_subs:
            mock_get_subs.return_value = mock_subs

            # Act
            result = handler.split_subtitles("test_video_id")

            # Assert
            assert result is None, f"Expected None for short video, got {result}"

    def test_returns_intervals_for_normal_video(self, handler):
        """
        Test that subtitle intervals are correctly computed.

        Given: A video with subtitles spanning multiple intervals
        When: split_subtitles is called
        Then: Correct list of combined subtitle intervals is returned
        """
        # Arrange - Mock subtitles for a 25 second video
        mock_subs = [
            ("00:00:00.000", "00:00:05.000", "Text in interval 0-10"),
            ("00:00:05.000", "00:00:10.000", "More text in interval 0-10"),
            ("00:00:10.000", "00:00:15.000", "Text in interval 10-20"),
            ("00:00:15.000", "00:00:20.000", "More text in interval 10-20"),
            ("00:00:20.000", "00:00:25.000", "Text in interval 20-30"),
            ("00:00:25.000", "00:00:30.000", "More text in interval 20-30"),
        ]

        with patch("yt_fts.llm.get_embeddings.get_subs_by_video_id") as mock_get_subs:
            mock_get_subs.return_value = mock_subs

            # Act
            result = handler.split_subtitles("test_video_id")

            # Assert
            assert result is not None, "Expected non-None result for normal video"
            assert len(result) == 3, f"Expected 3 intervals, got {len(result)}"
            assert result[0]["start_time"] == "00:00:00.000"
            assert "Text in interval 0-10" in result[0]["text"]
            assert "More text in interval 0-10" in result[0]["text"]
            assert result[1]["start_time"] == "00:00:10.000"
            assert "Text in interval 10-20" in result[1]["text"]

    def test_returns_none_when_no_subtitles_found(self, handler):
        """
        Test that None is returned when no subtitles exist for the video.

        Given: A video with no subtitles
        When: split_subtitles is called
        Then: None is returned
        """
        # Arrange
        with patch("yt_fts.llm.get_embeddings.get_subs_by_video_id") as mock_get_subs:
            mock_get_subs.return_value = []

            # Act
            result = handler.split_subtitles("test_video_id")

            # Assert
            assert result is None, "Expected None when no subtitles found"


class TestTimeToSeconds:
    """Tests for time_to_seconds method."""

    @pytest.fixture
    def handler(self):
        return EmbeddingsHandler(interval=10)

    def test_converts_timestamp_to_seconds(self, handler):
        """
        Test that H:M:S.%f timestamp is converted to seconds.

        Given: A timestamp string in HH:MM:SS.ffffff format
        When: time_to_seconds is called
        Then: The correct total seconds is returned
        """
        # Arrange & Act
        result = handler.time_to_seconds("00:01:30.500000")

        # Assert
        assert result == 90.5, f"Expected 90.5, got {result}"

    def test_converts_timestamp_with_hours(self, handler):
        """
        Test conversion with non-zero hours.

        Given: A timestamp string with hours
        When: time_to_seconds is called
        Then: The correct total seconds is returned
        """
        # Arrange & Act
        result = handler.time_to_seconds("01:02:03.123456")

        # Assert
        expected = 1 * 3600 + 2 * 60 + 3 + 0.123456
        assert result == expected, f"Expected {expected}, got {result}"

    def test_converts_timestamp_zero_microseconds(self, handler):
        """
        Test conversion with zero microseconds.

        Given: A timestamp string without fractional seconds
        When: time_to_seconds is called
        Then: The correct total seconds is returned
        """
        # Arrange & Act
        result = handler.time_to_seconds("00:00:30.000000")

        # Assert
        assert result == 30.0, f"Expected 30.0, got {result}"
