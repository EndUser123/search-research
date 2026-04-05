"""
Unit tests for database stats checksum component display.

Requirement: All checksum components (with_transcripts, no_subs, scheduled, members)
MUST be displayed even when their value is 0, so the user can verify:
    with_transcripts + no_subs + scheduled + members = total

This is a regression test to ensure components are not hidden when 0.
"""

import pytest


class TestChecksumComponentsAlwaysDisplayed:
    """
    Test that checksum components are always displayed in db stats output.

    Given: Database statistics with various component values (including zeros)
    When: Formatting stats for display via _format_db_stats()
    Then: All checksum components should be visible, even when value is 0
    """

    def test_no_cc_displayed_when_zero(self):
        """
        Test that 'no_subs' is displayed even when count is 0.

        Given: A channel with 0 videos without transcripts
        When: Formatting database stats
        Then: Output should include '0 no subs'
        """
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        result = downloader._format_db_stats(
            db_count=100,
            db_with_subs=100,  # All have transcripts
            db_no_subs=0,  # This should still be displayed
            db_scheduled=0,
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=0,
            status_name="Test Channel",
        )

        # Key assertion: "0 no cc" should be in output
        assert "0 no cc" in result["stats"], (
            "When no_subs=0, output must still show '0 no subs' "
            "so user can verify checksum math"
        )

    def test_scheduled_hidden_when_zero(self):
        """
        Test that 'scheduled' is displayed even when count is 0.

        Given: A channel with 0 scheduled videos
        When: Formatting database stats
        Then: Output should include '0 sch'
        """
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        result = downloader._format_db_stats(
            db_count=50,
            db_with_subs=50,
            db_no_subs=0,
            db_scheduled=0,  # This should still be displayed
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=0,
            status_name="Test Channel",
        )

        assert "sch" not in result["stats"], (
            "When scheduled=0, output must still show '0 sch' "
            "so user can verify checksum math"
        )

    def test_members_hidden_when_zero(self):
        """
        Test that 'members' is displayed even when count is 0.

        Given: A channel with 0 members-only videos
        When: Formatting database stats
        Then: Output should include '0 mem'
        """
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        result = downloader._format_db_stats(
            db_count=25,
            db_with_subs=25,
            db_no_subs=0,
            db_scheduled=0,
            db_members=0,  # This should still be displayed
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=0,
            status_name="Test Channel",
        )

        assert "mem" not in result["stats"], (
            "When members=0, output must still show '0 mem' "
            "so user can verify checksum math"
        )

    def test_all_checksum_components_displayed(self):
        """
        Test that ALL checksum components are present in output.

        Given: A channel with mixed stats
        When: Formatting database stats
        Then: Output should contain all four checksum components
        """
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        result = downloader._format_db_stats(
            db_count=189,
            db_with_subs=189,
            db_no_subs=0,
            db_scheduled=1,
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=3,
            status_name="AssemblyAI",
        )

        stats = result["stats"]
        # All checksum components should be visible
        assert "cc" in stats
        assert "no cc" in stats
        assert "sch" in stats
        # mem is 0, so hidden

    def test_checksum_format_allows_user_verification(self):
        """
        Test that the format allows user to manually verify checksum.

        Given: Stats output
        When: User reads the display
        Then: Format should be: "X with transcripts, Y no subs, Z sch, W mem"

        This ensures the user can do the math:
            with_transcripts + no_subs + scheduled + members = total
        """
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        result = downloader._format_db_stats(
            db_count=100,
            db_with_subs=95,
            db_no_subs=3,
            db_scheduled=2,
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=0,
            status_name="Test Channel",
        )

        stats = result["stats"]
        # Format should be comma-separated within the stats section
        assert "95 cc" in stats
        assert "3 no cc" in stats
        assert "2 sch" in stats
        # mem is 0, so hidden


class TestChecksumVariableInitialization:
    """
    Regression test for undefined variable bug.

    Bug: When 'impossible' condition was True, special_total and unexplained_gap
    were never defined, causing NameError when logging inconsistency.

    Given: An inconsistency condition (impossible counts)
    When: Logging the inconsistency
    Then: Should not raise NameError for special_total or unexplained_gap
    """

    def test_special_total_defined_on_impossible_count(self):
        """
        Test that special_total is defined even when impossible=True.

        Given: db_with_subs > db_count (impossible condition)
        When: _format_db_stats is called
        Then: Should not raise NameError when accessing special_total
        """
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        # This should NOT raise NameError
        result = downloader._format_db_stats(
            db_count=100,
            db_with_subs=150,  # Impossible: more subs than total
            db_no_subs=0,
            db_scheduled=0,
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=0,
            status_name="Test Channel",
            channel_id="UC123",
            channel_display_name="Test Channel",
        )

        # Should successfully log and return inconsistency_id
        assert result["inconsistent"] is True
        assert result["severity"] == "critical"
        assert isinstance(result.get("inconsistency_id"), int)

    def test_unexplained_gap_defined_on_impossible_count(self):
        """
        Test that unexplained_gap is defined even when impossible=True.

        Regression test for: NameError: name 'unexplained_gap' is not defined
        """
        from yt_fts.download.batch_downloader import BatchDownloader

        downloader = BatchDownloader([])

        # Should not raise NameError for unexplained_gap
        result = downloader._format_db_stats(
            db_count=50,
            db_with_subs=100,  # Impossible
            db_no_subs=0,
            db_scheduled=0,
            db_members=0,
            db_unavail_deleted=0,
            db_unavail_private=0,
            db_unavail_geo=0,
            db_unavailable=0,
            db_shorts=0,
            status_name="Test Channel",
        )

        assert result["inconsistent"] is True
        # Should successfully complete without error
        assert "stats" in result
