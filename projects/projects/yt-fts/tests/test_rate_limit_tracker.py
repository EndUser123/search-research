"""
Tests for RateLimitTracker - dynamic video_jobs auto-adjustment.

Tests verify that:
1. RateLimitTracker starts at default value (2 workers)
2. Decrements workers on rate limit (down to minimum 1)
3. Increments workers after threshold of successes (up to maximum 8)
4. Thread-safe operations work correctly
5. Callback mechanism notifies of worker count changes
6. Hysteresis prevents oscillation
"""

from threading import Thread
from time import sleep
from unittest.mock import MagicMock

import pytest


class TestRateLimitTrackerBasics:
    """Test suite for basic RateLimitTracker initialization and state."""

    def test_rate_limit_tracker_starts_at_default_workers(self):
        """
        Test that RateLimitTracker initializes with default 2 workers.

        Given: A RateLimitTracker is created
        When: No parameters are provided
        Then: current_jobs should be 2 (default starting point)
        """
        # Arrange & Act
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker()

        # Assert
        assert tracker.current_jobs == 2

    def test_rate_limit_tracker_accepts_custom_bounds(self):
        """
        Test that RateLimitTracker accepts custom min/max bounds.

        Given: A RateLimitTracker with min=1, max=4
        When: Created with these bounds
        Then: Bounds should be stored correctly
        """
        # Arrange & Act
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(min_jobs=1, max_jobs=4)

        # Assert
        assert tracker.min_jobs == 1
        assert tracker.max_jobs == 4
        assert tracker.current_jobs == 2  # Still starts at default

    def test_rate_limit_tracker_accepts_custom_start(self):
        """
        Test that RateLimitTracker accepts custom starting value.

        Given: A RateLimitTracker with start_jobs=3
        When: Created with start_jobs=3
        Then: current_jobs should be 3
        """
        # Arrange & Act
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=3)

        # Assert
        assert tracker.current_jobs == 3


class TestRateLimitDecrease:
    """Test suite for worker count decrease on rate limit detection."""

    def test_decrements_on_rate_limit(self):
        """
        Test that current_jobs decreases by 1 when rate limit is reported.

        Given: A RateLimitTracker with current_jobs=4
        When: on_rate_limit() is called
        Then: current_jobs should decrease to 3
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=4)

        # Act
        tracker.on_rate_limit(channel_id="test_channel", error_msg="429 Too Many Requests")

        # Assert
        assert tracker.current_jobs == 3

    def test_minimum_one_worker(self):
        """
        Test that current_jobs never goes below 1 (minimum floor).

        Given: A RateLimitTracker with current_jobs=1
        When: on_rate_limit() is called
        Then: current_jobs should remain at 1 (not go to 0 or negative)
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=1)

        # Act
        tracker.on_rate_limit(channel_id="test_channel", error_msg="429")

        # Assert
        assert tracker.current_jobs == 1

    def test_respects_custom_min_jobs(self):
        """
        Test that rate limit decrease respects custom min_jobs.

        Given: A RateLimitTracker with min_jobs=2, current_jobs=2
        When: on_rate_limit() is called
        Then: current_jobs should remain at 2 (custom minimum)
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=2, min_jobs=2)

        # Act
        tracker.on_rate_limit(channel_id="test", error_msg="rate limited")

        # Assert
        assert tracker.current_jobs == 2


class TestRateLimitIncrease:
    """Test suite for worker count increase after successful completions."""

    def test_increments_after_success_threshold(self):
        """
        Test that current_jobs increases after threshold of successful completions.

        Given: A RateLimitTracker with current_jobs=2
        When: on_success() is called 10 times (meeting threshold)
        Then: current_jobs should increase to 3
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=2)

        # Act - Call on_success 10 times (threshold)
        for _ in range(10):
            tracker.on_success(channel_id="test_channel")

        # Assert
        assert tracker.current_jobs == 3

    def test_maximum_eight_workers(self):
        """
        Test that current_jobs never exceeds 8 (maximum ceiling).

        Given: A RateLimitTracker with max_jobs=8, current_jobs=8
        When: on_success() is called 10 times
        Then: current_jobs should remain at 8
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=8, max_jobs=8)

        # Act
        for _ in range(10):
            tracker.on_success(channel_id="test")

        # Assert
        assert tracker.current_jobs == 8

    def test_respects_custom_max_jobs(self):
        """
        Test that increase respects custom max_jobs.

        Given: A RateLimitTracker with max_jobs=4, current_jobs=4
        When: on_success() is called 10 times
        Then: current_jobs should remain at 4 (custom maximum)
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=4, max_jobs=4)

        # Act
        for _ in range(10):
            tracker.on_success(channel_id="test")

        # Assert
        assert tracker.current_jobs == 4


class TestHysteresis:
    """Test suite for hysteresis - minimum channels between increases."""

    def test_requires_unique_channels_before_increase(self):
        """
        Test that at least 5 unique channels must complete before increase.

        Given: A RateLimitTracker with unique_channel_threshold=5
        When: Same channel completes successfully 10 times
        Then: current_jobs should NOT increase (needs 5 unique channels)
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=2, unique_channel_threshold=5)

        # Act - Same channel 10 times
        for _ in range(10):
            tracker.on_success(channel_id="same_channel")

        # Assert - Should not increase because only 1 unique channel
        assert tracker.current_jobs == 2

    def test_increases_after_five_unique_channels(self):
        """
        Test that worker count increases after 5 unique channels complete.

        Given: A RateLimitTracker with unique_channel_threshold=5, current_jobs=2
        When: 5 unique channels each complete successfully twice
        Then: current_jobs should increase to 3
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=2, unique_channel_threshold=5)

        # Act - 5 unique channels, each completing 2 times
        for i in range(5):
            for _ in range(2):
                tracker.on_success(channel_id=f"channel_{i}")

        # Assert - 5 unique channels met threshold
        assert tracker.current_jobs == 3

    def test_resets_unique_channels_after_increase(self):
        """
        Test that unique channel count resets after worker increase.

        Given: A RateLimitTracker with unique_channel_threshold=5 that just increased from 2 to 3
        When: Additional successes occur
        Then: Should need 5 new unique channels for next increase
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=2, unique_channel_threshold=5)

        # First increase - 5 unique channels
        for i in range(5):
            for _ in range(2):
                tracker.on_success(channel_id=f"channel_{i}")

        assert tracker.current_jobs == 3  # Increased

        # Act - Try to increase again with only 3 new unique channels
        for i in range(3):
            for _ in range(5):
                tracker.on_success(channel_id=f"new_channel_{i}")

        # Assert - Should still be at 3 (not enough unique channels)
        assert tracker.current_jobs == 3


class TestRateLimitResetsCounter:
    """Test suite for rate limit resetting success counter."""

    def test_rate_limit_resets_success_counter(self):
        """
        Test that a rate limit event resets the accumulated success count.

        Given: A RateLimitTracker with 9 successes (near threshold of 10)
        When: A rate limit occurs
        Then: Success counter should reset to 0 (requires 20 NEW successes to increase back to problematic level due to asymmetric hysteresis)
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=4)

        # 9 successes - one short of threshold
        for _ in range(9):
            tracker.on_success(channel_id="test")

        # Act - Rate limit occurs (decreases to 3, resets counter, marks level 4 as problematic)
        tracker.on_rate_limit(channel_id="test", error_msg="429")

        # Verify decreased and level 4 is marked problematic
        assert tracker.current_jobs == 3  # Decreased from rate limit
        assert 4 in tracker.get_problematic_levels()  # Level 4 is now problematic

        # 19 more successes should not be enough (counter was reset, and level 4 requires 2x threshold)
        for i in range(19):
            tracker.on_success(channel_id=f"test{i}")
        assert tracker.current_jobs == 3  # Still at decreased value

        # One more success reaches 2x threshold (20), should increase back to 4
        tracker.on_success(channel_id="test20")
        assert tracker.current_jobs == 4  # Recovered after sustained success
        assert 4 not in tracker.get_problematic_levels()  # Level 4 penalty cleared on successful return


class TestCallbackMechanism:
    """Test suite for callback when worker count changes."""

    def test_callback_invoked_on_decrease(self):
        """
        Test that callback is invoked when worker count decreases.

        Given: A RateLimitTracker with callback registered
        When: Rate limit causes worker decrease
        Then: Callback should be invoked with new count
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        callback = MagicMock()
        tracker = RateLimitTracker(start_jobs=3, on_jobs_changed=callback)

        # Act
        tracker.on_rate_limit(channel_id="test", error_msg="429")

        # Assert
        callback.assert_called_once_with(2)

    def test_callback_invoked_on_increase(self):
        """
        Test that callback is invoked when worker count increases.

        Given: A RateLimitTracker with callback registered
        When: Successes cause worker increase
        Then: Callback should be invoked with new count
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        callback = MagicMock()
        tracker = RateLimitTracker(start_jobs=2, on_jobs_changed=callback)

        # Act - 5 unique channels, threshold met
        for i in range(5):
            for _ in range(2):
                tracker.on_success(channel_id=f"channel_{i}")

        # Assert
        callback.assert_called_once_with(3)

    def test_callback_not_invoked_when_at_bounds(self):
        """
        Test that callback is NOT invoked when already at bound.

        Given: A RateLimitTracker at min_jobs=1
        When: Rate limit occurs
        Then: Callback should NOT be invoked (no change)
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        callback = MagicMock()
        tracker = RateLimitTracker(start_jobs=1, min_jobs=1, on_jobs_changed=callback)

        # Act
        tracker.on_rate_limit(channel_id="test", error_msg="429")

        # Assert - No callback since already at minimum
        callback.assert_not_called()


class TestThreadSafety:
    """Test suite for thread-safe operations."""

    def test_concurrent_rate_limits_safe(self):
        """
        Test that concurrent rate limit calls don't corrupt state.

        Given: A RateLimitTracker
        When: Multiple threads call on_rate_limit simultaneously
        Then: State should remain consistent
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=8)

        # Act - 10 threads each causing a rate limit
        threads = []
        for i in range(10):
            t = Thread(target=tracker.on_rate_limit, args=(f"channel_{i}", "429"))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Assert - Should be at minimum (8 - 10, capped at 1)
        assert tracker.current_jobs == 1

    def test_concurrent_successes_safe(self):
        """
        Test that concurrent success calls don't corrupt state.

        Given: A RateLimitTracker
        When: Multiple threads call on_success simultaneously
        Then: State should remain consistent and eventually increase
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=2)
        completed = []

        def worker_success(channel_id: str, count: int):
            for _ in range(count):
                tracker.on_success(channel_id=channel_id)
            completed.append(channel_id)

        # Act - 5 threads, each with a unique channel, 3 successes each
        threads = []
        for i in range(5):
            t = Thread(target=worker_success, args=(f"channel_{i}", 5))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Assert - Should have increased (5 unique channels, threshold met)
        assert tracker.current_jobs >= 3
        assert len(completed) == 5  # All threads completed


class TestStateTracking:
    """Test suite for state tracking and reporting."""

    def test_get_current_jobs_returns_current_value(self):
        """
        Test that get_current_jobs() returns the current worker count.

        Given: A RateLimitTracker
        When: get_current_jobs() is called
        Then: Should return the current_jobs value
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=5)

        # Act & Assert
        assert tracker.get_current_jobs() == 5

    def test_reset_restarts_to_default(self):
        """
        Test that reset() returns tracker to initial state.

        Given: A RateLimitTracker that has adjusted up and down
        When: reset() is called
        Then: Should return to start_jobs value with cleared counters
        """
        # Arrange
        from yt_fts.download.rate_limit_tracker import RateLimitTracker

        tracker = RateLimitTracker(start_jobs=4)

        # Modify state
        tracker.on_rate_limit(channel_id="test", error_msg="429")
        for i in range(5):
            tracker.on_success(channel_id=f"channel_{i}")

        # Act
        tracker.reset()

        # Assert - Back to start value
        assert tracker.current_jobs == 4
