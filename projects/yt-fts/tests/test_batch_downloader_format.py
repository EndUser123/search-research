"""
Tests for _format_db_stats() display formatting in BatchDownloader.

Tests the formatting of database statistics for display.
"""

import pytest

from yt_fts.download.batch_downloader import BatchDownloader
from yt_fts.utils.rich_console import reset_console_cache


@pytest.fixture(autouse=True)
def reset_console_state():
    """Ensure each test gets a fresh console state."""
    reset_console_cache()
    yield
    reset_console_cache()


class TestFormatDbStatsDisplayFormatting:
    """Test database stats display formatting.

    Expected output format:
    {total} total | {cc} cc, {no_cc} no cc{, {unv} unv if >0}{, {sch} sch if >0}{, {mem} mem if >0}{, {shorts} shorts if >0} | {pl} pl if >0 | {subs} subs

    Rules:
    - Zero values should NOT display for: unv, sch, mem, pl, shorts
    - Order: cc, no cc, unv, sch, mem, shorts | pl, subs
    """

    @pytest.fixture
    def downloader(self):
        """Create a BatchDownloader instance for testing."""
        return BatchDownloader(channels=["@testchannel"])

    def test_basic_stats_format(self, downloader):
        """Test basic stats format with minimal categories.

        Given: total=100, cc=95, no_cc=5, unv=0, sch=0, mem=0, pl=3, subs=1000, shorts=0
        When: _format_db_stats is called
        Then: Output should be "100 total | 95 cc, 5 no cc | 3 pl | 1000 subs"
        """
        # Arrange
        db_count = 100
        db_with_subs = 95  # cc
        db_no_subs = 5  # no cc
        db_unavailable = 0  # unv
        db_scheduled = 0  # sch
        db_members = 0  # mem
        db_playlist_count = 3  # pl
        db_subscriber_count = 1000  # subs
        db_shorts = 0
        db_unavail_deleted = 0
        db_unavail_private = 0
        db_unavail_geo = 0

        # Act
        result = downloader._format_db_stats(
            db_count=db_count,
            db_with_subs=db_with_subs,
            db_no_subs=db_no_subs,
            db_unavailable=db_unavailable,
            db_scheduled=db_scheduled,
            db_members=db_members,
            db_unavail_deleted=db_unavail_deleted,
            db_unavail_private=db_unavail_private,
            db_unavail_geo=db_unavail_geo,
            db_shorts=db_shorts,
            status_name="test",
            channel_id=None,
            channel_display_name=None,
            db_subscriber_count=db_subscriber_count,
            db_playlist_count=db_playlist_count,
        )

        # Assert
        expected = "100 total | 95 cc, 5 no cc | 3 pl | 1000 subs"
        actual = result["stats"]
        assert actual == expected, f"Expected: {expected} | Got: {actual}"

    def test_stats_with_unavailable(self, downloader):
        """Test stats format with unavailable videos.

        Given: total=100, cc=90, no_cc=5, unv=5, sch=0, mem=0, pl=3, subs=1000, shorts=0
        When: _format_db_stats is called
        Then: Output should be "100 total | 90 cc, 5 no cc, 5 unv | 3 pl | 1000 subs"
        """
        # Arrange
        db_count = 100
        db_with_subs = 90
        db_no_subs = 5
        db_unavailable = 5  # unv - should display
        db_scheduled = 0
        db_members = 0
        db_playlist_count = 3
        db_subscriber_count = 1000
        db_shorts = 0
        db_unavail_deleted = 0
        db_unavail_private = 0
        db_unavail_geo = 0

        # Act
        result = downloader._format_db_stats(
            db_count=db_count,
            db_with_subs=db_with_subs,
            db_no_subs=db_no_subs,
            db_unavailable=db_unavailable,
            db_scheduled=db_scheduled,
            db_members=db_members,
            db_unavail_deleted=db_unavail_deleted,
            db_unavail_private=db_unavail_private,
            db_unavail_geo=db_unavail_geo,
            db_shorts=db_shorts,
            status_name="test",
            channel_id=None,
            channel_display_name=None,
            db_subscriber_count=db_subscriber_count,
            db_playlist_count=db_playlist_count,
        )

        # Assert
        expected = "100 total | 90 cc, 5 no cc, 5 unv | 3 pl | 1000 subs"
        actual = result["stats"]
        assert actual == expected, f"Expected: {expected} | Got: {actual}"

    def test_minimal_stats_format(self, downloader):
        """Test minimal stats format with only required values.

        Given: total=10, cc=0, no_cc=10, unv=0, sch=0, mem=0, pl=0, subs=0, shorts=0
        When: _format_db_stats is called
        Then: Output should be "10 total | 0 cc, 10 no cc"
        """
        # Arrange
        db_count = 10
        db_with_subs = 0
        db_no_subs = 10
        db_unavailable = 0
        db_scheduled = 0
        db_members = 0
        db_playlist_count = 0
        db_subscriber_count = 0
        db_shorts = 0
        db_unavail_deleted = 0
        db_unavail_private = 0
        db_unavail_geo = 0

        # Act
        result = downloader._format_db_stats(
            db_count=db_count,
            db_with_subs=db_with_subs,
            db_no_subs=db_no_subs,
            db_unavailable=db_unavailable,
            db_scheduled=db_scheduled,
            db_members=db_members,
            db_unavail_deleted=db_unavail_deleted,
            db_unavail_private=db_unavail_private,
            db_unavail_geo=db_unavail_geo,
            db_shorts=db_shorts,
            status_name="test",
            channel_id=None,
            channel_display_name=None,
            db_subscriber_count=db_subscriber_count,
            db_playlist_count=db_playlist_count,
        )

        # Assert
        expected = "10 total | 0 cc, 10 no cc"
        actual = result["stats"]
        assert actual == expected, f"Expected: {expected} | Got: {actual}"

    def test_stats_with_all_categories(self, downloader):
        """Test stats format with all categories present.

        Given: total=100, cc=70, no_cc=10, unv=5, sch=5, mem=5, pl=10, subs=50000, shorts=20
        When: _format_db_stats is called
        Then: Output should be "100 total | 70 cc, 10 no cc, 5 unv, 5 sch, 5 mem, 20 shorts | 10 pl | 50.0K subs"
        """
        # Arrange
        db_count = 100
        db_with_subs = 70
        db_no_subs = 10
        db_unavailable = 5
        db_scheduled = 5  # sch - should display
        db_members = 5  # mem - should display
        db_playlist_count = 10
        db_subscriber_count = 50000  # Should format as "50.0K"
        db_shorts = 20  # shorts - should display
        db_unavail_deleted = 0
        db_unavail_private = 0
        db_unavail_geo = 0

        # Act
        result = downloader._format_db_stats(
            db_count=db_count,
            db_with_subs=db_with_subs,
            db_no_subs=db_no_subs,
            db_unavailable=db_unavailable,
            db_scheduled=db_scheduled,
            db_members=db_members,
            db_unavail_deleted=db_unavail_deleted,
            db_unavail_private=db_unavail_private,
            db_unavail_geo=db_unavail_geo,
            db_shorts=db_shorts,
            status_name="test",
            channel_id=None,
            channel_display_name=None,
            db_subscriber_count=db_subscriber_count,
            db_playlist_count=db_playlist_count,
        )

        # Assert
        # Note: 50000 subs should format as "50.0K subs"
        # Note: mem and shorts are now in the video stats group, not after subs
        expected = "100 total | 70 cc, 10 no cc, 5 unv, 5 sch, 5 mem, 20 shorts | 10 pl | 50.0K subs"
        actual = result["stats"]
        assert actual == expected, f"Expected: {expected} | Got: {actual}"
