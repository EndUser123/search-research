'''Tests for ChannelStatisticsManager database statistics formatting.

This test module verifies the new format structure with:
- Section separators using |
- Prefixes: + for vt/nt, - for shorts (exclusion indicator)
'''
import pytest

from yt_fts.download.channel_statistics_manager import ChannelStatisticsManager


class TestFormatForDisplayNewStructure:
    """Tests for the new database statistics format structure.
    
    The new format should:
    - Separate sections with |
    - Use + prefix for vt (video transcripts) and nt (no transcripts)
    - Use - prefix for shorts (negative to indicate exclusion)
    
    Example: "123 total, 122 mt, 0 dt | +122 vt, +123 nt | -1 shorts | 50.4K subs"
    """

    @pytest.fixture
    def manager(self):
        """Return a ChannelStatisticsManager instance."""
        return ChannelStatisticsManager()

    def test_format_uses_pipe_separator_between_sections(self, manager):
        """Test that the format uses | as section separator.
        
        Given: Sample channel statistics data
        When: format_for_display() is called
        Then: Output contains | separators between main sections
        """
        # Arrange
        db_count = 245
        db_with_subs = 122
        db_no_subs = 123
        db_scheduled = 0
        db_members = 0
        db_unavail_deleted = 0
        db_unavail_private = 0
        db_unavail_geo = 0
        db_unavailable = 0
        db_shorts = 1
        db_cc_available = 122
        db_no_subtitles_available = 0
        db_subscriber_count = 50400

        # Act
        result = manager.format_for_display(
            db_count=db_count,
            db_with_subs=db_with_subs,
            db_no_subs=db_no_subs,
            db_scheduled=db_scheduled,
            db_members=db_members,
            db_unavail_deleted=db_unavail_deleted,
            db_unavail_private=db_unavail_private,
            db_unavail_geo=db_unavail_geo,
            db_unavailable=db_unavailable,
            db_shorts=db_shorts,
            db_cc_available=db_cc_available,
            db_no_subtitles_available=db_no_subtitles_available,
            db_subscriber_count=db_subscriber_count,
        )

        # Assert
        # Should have | separating sections
        assert "|" in result, f"Expected pipe separator in output: {result}"

    def test_format_uses_plus_prefix_for_vt_and_nt(self, manager):
        """Test that the format uses + prefix for vt and nt.
        
        Given: Sample channel statistics with transcripts
        When: format_for_display() is called
        Then: Output contains +122 vt and +123 nt format
        """
        # Arrange
        db_count = 245
        db_with_subs = 122
        db_no_subs = 123
        db_scheduled = 0
        db_members = 0
        db_unavail_deleted = 0
        db_unavail_private = 0
        db_unavail_geo = 0
        db_unavailable = 0
        db_shorts = 1
        db_cc_available = 122
        db_no_subtitles_available = 0
        db_subscriber_count = 50400

        # Act
        result = manager.format_for_display(
            db_count=db_count,
            db_with_subs=db_with_subs,
            db_no_subs=db_no_subs,
            db_scheduled=db_scheduled,
            db_members=db_members,
            db_unavail_deleted=db_unavail_deleted,
            db_unavail_private=db_unavail_private,
            db_unavail_geo=db_unavail_geo,
            db_unavailable=db_unavailable,
            db_shorts=db_shorts,
            db_cc_available=db_cc_available,
            db_no_subtitles_available=db_no_subtitles_available,
            db_subscriber_count=db_subscriber_count,
        )

        # Assert
        # New format uses + prefix for vt and nt
        assert "+122 vt" in result, f"Expected '+122 vt' in output: {result}"
        assert "+123 nt" in result, f"Expected '+123 nt' in output: {result}"

    def test_format_uses_minus_prefix_for_shorts(self, manager):
        """Test that the format uses - prefix for shorts (exclusion indicator).
        
        Given: Sample channel statistics with shorts
        When: format_for_display() is called
        Then: Output contains -1 shorts format
        """
        # Arrange
        db_count = 245
        db_with_subs = 122
        db_no_subs = 123
        db_scheduled = 0
        db_members = 0
        db_unavail_deleted = 0
        db_unavail_private = 0
        db_unavail_geo = 0
        db_unavailable = 0
        db_shorts = 1
        db_cc_available = 122
        db_no_subtitles_available = 0
        db_subscriber_count = 50400

        # Act
        result = manager.format_for_display(
            db_count=db_count,
            db_with_subs=db_with_subs,
            db_no_subs=db_no_subs,
            db_scheduled=db_scheduled,
            db_members=db_members,
            db_unavail_deleted=db_unavail_deleted,
            db_unavail_private=db_unavail_private,
            db_unavail_geo=db_unavail_geo,
            db_unavailable=db_unavailable,
            db_shorts=db_shorts,
            db_cc_available=db_cc_available,
            db_no_subtitles_available=db_no_subtitles_available,
            db_subscriber_count=db_subscriber_count,
        )

        # Assert
        # New format uses - prefix for shorts to indicate exclusion
        assert "-1 shorts" in result, f"Expected '-1 shorts' in output: {result}"

    def test_format_complete_new_structure(self, manager):
        """Test the complete new format structure.
        
        Given: Full sample channel statistics
        When: format_for_display() is called
        Then: Output matches expected new format with all separators and prefixes
        """
        # Arrange
        db_count = 245
        db_with_subs = 122
        db_no_subs = 123
        db_scheduled = 0
        db_members = 0
        db_unavail_deleted = 0
        db_unavail_private = 0
        db_unavail_geo = 0
        db_unavailable = 0
        db_shorts = 1
        db_cc_available = 122
        db_no_subtitles_available = 0
        db_subscriber_count = 50400

        # Act
        result = manager.format_for_display(
            db_count=db_count,
            db_with_subs=db_with_subs,
            db_no_subs=db_no_subs,
            db_scheduled=db_scheduled,
            db_members=db_members,
            db_unavail_deleted=db_unavail_deleted,
            db_unavail_private=db_unavail_private,
            db_unavail_geo=db_unavail_geo,
            db_unavailable=db_unavailable,
            db_shorts=db_shorts,
            db_cc_available=db_cc_available,
            db_no_subtitles_available=db_no_subtitles_available,
            db_subscriber_count=db_subscriber_count,
        )

        # Assert - verify all key elements of new format
        # Section 1: Basic counts (should have total, mt, dt)
        assert "245 total" in result
        assert " mt" in result or "mt," in result
        assert " dt" in result or "dt," in result
        
        # Section 2: Transcript availability with + prefix
        assert "+122 vt" in result, f"Missing '+122 vt' in: {result}"
        assert "+123 nt" in result, f"Missing '+123 nt' in: {result}"
        
        # Section 3: Shorts with - prefix (exclusion indicator)
        assert "-1 shorts" in result, f"Missing '-1 shorts' in: {result}"
        
        # Section 4: Extras (subscriber count)
        assert "50.4K subs" in result
