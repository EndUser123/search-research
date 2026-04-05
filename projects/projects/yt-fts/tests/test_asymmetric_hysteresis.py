"""
Tests for asymmetric hysteresis in RateLimitTracker.

Asymmetric hysteresis means that when a rate limit occurs at a specific worker level,
returning to that level requires MORE successes than it originally took to leave it.
This prevents oscillation between levels when a worker count is marginally unstable.
"""

import pytest


class TestAsymmetricHysteresis:
    """Test suite for asymmetric hysteresis - higher threshold to return to problematic levels."""

    def test_rate_limit_at_level_marks_it_as_problematic(self):
        """
        Test that a rate limit at level N marks that level as problematic.

        Given: A RateLimitTracker at 4 workers
        When: A rate limit occurs (dropping to 3)
        Then: Level 4 should be marked as problematic
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=4)

        # Act - Rate limit occurs, dropping from 4 to 3
        tracker.on_rate_limit(channel_id="test_channel", error_msg="429 Too Many Requests")

        # Assert - Should now be at level 3
        assert tracker.current_jobs == 3

        # Level 4 should be marked as problematic
        assert 4 in tracker.get_problematic_levels(), \
            "Level 4 should be marked as problematic after rate limit"

    def test_problematic_level_requires_doubled_success_threshold(self):
        """
        Test that returning to a problematic level requires 2x the normal success threshold.

        Given: A RateLimitTracker at 3 workers after rate limit at 4
              With success_threshold=10 (normal)
        When: Accumulating successes to return to level 4
        Then: Should require 20 successes (2x normal) to increase back to 4
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=4, success_threshold=10)

        # Rate limit at level 4, drops to 3
        tracker.on_rate_limit(channel_id="test", error_msg="429")
        assert tracker.current_jobs == 3

        # Act - Add exactly the normal threshold (10) successes
        for i in range(10):
            tracker.on_success(channel_id=f"channel_{i}")

        # Assert - Should NOT increase yet because level 4 is problematic
        # Requires 2x threshold = 20 successes
        assert tracker.current_jobs == 3, \
            "Should NOT return to problematic level 4 with only normal threshold (10) successes"

        # Add 10 more successes (total 20 = 2x threshold)
        for i in range(10, 20):
            tracker.on_success(channel_id=f"channel_{i}")

        # Now should increase to 4
        assert tracker.current_jobs == 4, \
            "Should return to level 4 after 2x threshold (20) successes"

    def test_non_problematic_level_uses_normal_threshold(self):
        """
        Test that levels without rate limit history use normal success threshold.

        Given: A RateLimitTracker at 2 workers that never hit a rate limit
              With success_threshold=10
        When: Accumulating successes to increase to level 3
        Then: Should require only 10 successes (normal threshold)
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=2, success_threshold=10)

        # Act - Add exactly the normal threshold (10) successes
        for i in range(10):
            tracker.on_success(channel_id=f"channel_{i}")

        # Assert - Should increase to 3 with normal threshold
        assert tracker.current_jobs == 3, \
            "Non-problematic levels should use normal success threshold"

    def test_penalty_clears_after_sustained_success_at_lower_level(self):
        """
        Test that the penalty on a problematic level clears after sustained success at lower level.

        Given: A RateLimitTracker at 3 workers after rate limit at 4
              With penalty_clear_threshold=30 (successes needed to clear penalty)
        When: 30 successes occur at level 3 (without trying to increase)
        Then: Level 4 penalty should clear, requiring normal threshold to return
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        # Use high unique_channel_threshold to prevent increases during test
        tracker = RateLimitTracker(
            start_jobs=4,
            success_threshold=10,
            unique_channel_threshold=100,  # Require 100 unique channels to increase
            penalty_clear_threshold=30
        )

        # Rate limit at level 4, drops to 3
        tracker.on_rate_limit(channel_id="test", error_msg="429")
        assert tracker.current_jobs == 3
        assert 4 in tracker.get_problematic_levels(), \
            "Level 4 should be marked problematic"

        # Act - Accumulate 30 successes at level 3 using one channel
        # (won't increase due to high unique_channel_threshold)
        for _ in range(30):
            tracker.on_success(channel_id="stable_channel")

        # After sustained success, penalty should clear
        # This requires implementation of penalty clearing mechanism
        # For now, we manually check if the penalty cleared
        # The assertion below will fail until the feature is implemented

        # After penalty clears, level 4 should no longer be problematic
        assert 4 not in tracker.get_problematic_levels(), \
            "Level 4 penalty should clear after sustained success at lower level"

    def test_multiple_levels_can_be_marked_problematic(self):
        """
        Test that multiple levels can be marked as problematic independently.

        Given: A RateLimitTracker that hits rate limits at levels 5 and 4
        When: Checking problematic levels
        Then: Both 4 and 5 should be marked as problematic
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=5)

        # Act - Rate limit at 5, drops to 4
        tracker.on_rate_limit(channel_id="test1", error_msg="429")
        assert tracker.current_jobs == 4

        # Another rate limit at 4, drops to 3
        tracker.on_rate_limit(channel_id="test2", error_msg="429")
        assert tracker.current_jobs == 3

        # Assert - Both levels should be marked problematic
        problematic = tracker.get_problematic_levels()
        assert 4 in problematic, "Level 4 should be marked problematic"
        assert 5 in problematic, "Level 5 should be marked problematic"

    def test_successful_run_at_problematic_level_clears_its_penalty(self):
        """
        Test that successfully operating at a previously problematic level clears its penalty.

        Given: A RateLimitTracker where level 4 was problematic
              But we successfully returned to level 4 and sustained it
        When: Checking problematic levels after sustained success at level 4
        Then: Level 4 should no longer be marked as problematic
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=4, success_threshold=10)

        # Rate limit at level 4, drops to 3
        tracker.on_rate_limit(channel_id="test", error_msg="429")
        assert tracker.current_jobs == 3
        assert 4 in tracker.get_problematic_levels()

        # Return to level 4 with 2x threshold (20 successes)
        for i in range(20):
            tracker.on_success(channel_id=f"channel_{i}")
        assert tracker.current_jobs == 4

        # Sustain at level 4 with enough successes to clear penalty
        for i in range(20, 40):
            tracker.on_success(channel_id=f"channel_{i}")

        # Assert - Level 4 should no longer be problematic after sustained success
        assert 4 not in tracker.get_problematic_levels(), \
            "Level 4 penalty should clear after sustained successful operation at that level"
