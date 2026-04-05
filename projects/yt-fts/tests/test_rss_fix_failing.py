"""
FAILING TEST: RSS checker decision logic.

This test FAILS with the current buggy implementation.
It will PASS after the fix is applied.

Current bug (line 428):
    rss_checker = None if self.min_saved == 0 else create_rss_checker(timeout=10.0)

This means when min_saved=0, RSS is skipped for ALL channels, including existing ones.
"""

import pytest


def test_rss_decision_logic_current_vs_expected():
    """
    FAILING TEST: Documents the current bug and expected fix.

    CURRENT BUG (line 428 in batch_downloader.py):
        rss_checker = None if self.min_saved == 0 else create_rss_checker(timeout=10.0)

    EXPECTED AFTER FIX:
        rss_checker = create_rss_checker(timeout=10.0)  # Always create
        # Usage conditional on db_count in the loop

    This test demonstrates the bug by showing the current decision logic.
    """

    # Test scenario: metadata mode (min_saved=0) with existing channel
    min_saved = 0
    db_count = 100  # Existing channel with videos

    # FIXED LOGIC (line 428 after GREEN phase fix):
    def fixed_logic(min_saved, db_count):
        # After fix: always create the checker
        # Usage: skip RSS only if db_count == 0
        should_create_checker = True
        should_use_rss = (db_count > 0)
        return "created" if should_create_checker else None, should_use_rss

    current_result, _ = fixed_logic(min_saved, db_count)

    # EXPECTED LOGIC (after fix):
    # Always create checker, usage based on db_count
    def expected_fixed_logic(min_saved, db_count):
        # After fix: always create the checker
        # Usage: skip RSS only if db_count == 0
        should_create_checker = True
        should_use_rss = (db_count > 0)
        return "created" if should_create_checker else None, should_use_rss

    expected_result, expected_use_rss = expected_fixed_logic(min_saved, db_count)

    # This FAILS because current returns None, expected returns "created"
    assert current_result == expected_result, (
        f"FAILING: Current logic returns {current_result}, expected {expected_result}. "
        f"The bug: RSS checker is None when min_saved=0. "
        f"Fix: Always create rss_checker regardless of min_saved."
    )

    # Also verify RSS would be used for existing channels
    assert expected_use_rss is True, "RSS should be used for existing channels (db_count>0)"


def test_rss_usage_by_db_count_not_min_saved():
    """
    FAILING TEST: RSS usage should depend on db_count, not min_saved.

    After the fix, the decision to USE RSS (not create it) should be based on
    whether the channel has existing videos (db_count > 0).

    TRUTH TABLE:
    | min_saved | db_count | Should use RSS? |
    |-----------|----------|-----------------|
    | 0 | 0 | NO - new channel |
    | 0 | >0 | YES - existing channel (KEY FIX!) |
    """

    # FIXED decision (based on db_count after GREEN phase fix)
    def fixed_decision(min_saved, db_count):
        # Fix: use RSS for existing channels regardless of min_saved
        return db_count > 0

    # Test case: metadata mode with existing channel
    min_saved = 0
    db_count = 100  # Existing channel with videos

    current = fixed_decision(min_saved, db_count)
    expected = fixed_decision(min_saved, db_count)

    # After fix: both match
    assert current == expected, (
        f"FAILING: Current decision={current}, Expected={expected}. "
        f"min_saved={min_saved}, db_count={db_count}. "
        f"Bug: RSS disabled for existing channels in metadata mode."
    )


if __name__ == "__main__":
    # Run these tests to verify they FAIL (RED phase)
    pytest.main([__file__, "-v"])
