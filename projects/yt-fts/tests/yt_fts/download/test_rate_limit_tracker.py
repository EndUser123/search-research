"""
Unit tests for RateLimitTracker.

Tests cover:
- Initialization and configuration
- Worker count adjustment on rate limit
- Worker count increase on success
- Thread-safe operations
- Reset functionality
- Callback notification
- Problematic level tracking
"""

from unittest.mock import MagicMock

import pytest

from yt_fts.download.rate_limit_tracker import RateLimitTracker


class TestRateLimitTrackerInitialization:
    """Tests for RateLimitTracker initialization."""

    def test_initialization_with_defaults(self):
        """Default values are set correctly."""
        tracker = RateLimitTracker()
        assert tracker.current_jobs == 2
        assert tracker.min_jobs == 1
        assert tracker.max_jobs == 8

    def test_initialization_with_custom_values(self):
        """Custom values override defaults."""
        tracker = RateLimitTracker(
            start_jobs=4,
            min_jobs=2,
            max_jobs=10,
            success_threshold=15,
            unique_channel_threshold=3,
            penalty_clear_threshold=25,
        )
        assert tracker.current_jobs == 4
        assert tracker.min_jobs == 2
        assert tracker.max_jobs == 10

    def test_initialization_with_callback(self):
        """Callback is stored correctly."""
        callback = MagicMock()
        tracker = RateLimitTracker(on_jobs_changed=callback)
        assert tracker._on_jobs_changed is callback

    def test_get_current_jobs(self):
        """get_current_jobs returns current job count."""
        tracker = RateLimitTracker(start_jobs=5)
        assert tracker.get_current_jobs() == 5

    def test_repr(self):
        """Repr shows current state."""
        tracker = RateLimitTracker(start_jobs=3, min_jobs=1, max_jobs=8)
        repr_str = repr(tracker)
        assert "RateLimitTracker" in repr_str
        assert "current=3" in repr_str
        assert "min=1" in repr_str
        assert "max=8" in repr_str


class TestOnRateLimit:
    """Tests for on_rate_limit method."""

    def test_decrements_workers_on_rate_limit(self):
        """Rate limit decreases worker count."""
        tracker = RateLimitTracker(start_jobs=4, min_jobs=1)
        tracker.on_rate_limit("@test", "429")
        assert tracker.current_jobs == 3

    def test_never_goes_below_min_jobs(self):
        """Worker count never goes below min_jobs."""
        tracker = RateLimitTracker(start_jobs=2, min_jobs=2)
        tracker.on_rate_limit("@test", "429")
        assert tracker.current_jobs == 2  # Should stay at min

    def test_resets_success_count_on_rate_limit(self):
        """Success count is reset on rate limit."""
        tracker = RateLimitTracker()
        tracker._success_count = 5
        tracker.on_rate_limit("@test", "429")
        # Access through lock to check internal state
        with tracker._lock:
            assert tracker._success_count == 0

    def test_clears_unique_channels_on_rate_limit(self):
        """Unique channels set is cleared on rate limit."""
        tracker = RateLimitTracker()
        tracker._unique_channels.add("@test1")
        tracker._unique_channels.add("@test2")
        tracker.on_rate_limit("@test", "429")
        with tracker._lock:
            assert len(tracker._unique_channels) == 0

    def test_adds_to_problematic_levels(self):
        """Problematic level is recorded when decreasing."""
        tracker = RateLimitTracker(start_jobs=4)
        tracker.on_rate_limit("@test", "429")
        problematic = tracker.get_problematic_levels()
        assert 4 in problematic

    def test_calls_callback_when_decreasing(self):
        """Callback is called when worker count decreases."""
        callback = MagicMock()
        tracker = RateLimitTracker(start_jobs=4, on_jobs_changed=callback)
        tracker.on_rate_limit("@test", "429")
        callback.assert_called_once_with(3)

    def test_no_callback_when_no_change(self):
        """Callback is not called when at min_jobs."""
        callback = MagicMock()
        tracker = RateLimitTracker(start_jobs=1, min_jobs=1, on_jobs_changed=callback)
        tracker.on_rate_limit("@test", "429")
        callback.assert_not_called()


class TestOnSuccess:
    """Tests for on_success method."""

    def test_tracks_success_count(self):
        """Success count is incremented."""
        tracker = RateLimitTracker()
        tracker.on_success("@test1")
        with tracker._lock:
            assert tracker._success_count == 1

    def test_tracks_unique_channels(self):
        """Unique channels are tracked."""
        tracker = RateLimitTracker()
        tracker.on_success("@test1")
        tracker.on_success("@test2")
        tracker.on_success("@test1")  # Duplicate
        with tracker._lock:
            assert len(tracker._unique_channels) == 2

    def test_increases_workers_at_threshold(self):
        """Workers increase when success threshold is met."""
        tracker = RateLimitTracker(
            start_jobs=1,
            max_jobs=3,
            success_threshold=3,
            unique_channel_threshold=1,
        )
        tracker.on_success("@test1")
        tracker.on_success("@test2")
        tracker.on_success("@test3")
        assert tracker.current_jobs == 2

    def test_never_exceeds_max_jobs(self):
        """Worker count never exceeds max_jobs."""
        tracker = RateLimitTracker(
            start_jobs=3,
            max_jobs=3,
            success_threshold=2,
            unique_channel_threshold=1,
        )
        tracker.on_success("@test1")
        tracker.on_success("@test2")
        assert tracker.current_jobs == 3  # Should stay at max

    def test_resets_count_on_increase(self):
        """Success count is reset when workers increase."""
        tracker = RateLimitTracker(
            start_jobs=1,
            max_jobs=3,
            success_threshold=2,
            unique_channel_threshold=1,
        )
        tracker.on_success("@test1")
        tracker.on_success("@test2")
        assert tracker.current_jobs == 2
        with tracker._lock:
            assert tracker._success_count == 0

    def test_double_threshold_for_problematic_levels(self):
        """Higher threshold required for previously problematic levels."""
        tracker = RateLimitTracker(
            start_jobs=2,  # Start at 2 so we can mark level 2 as problematic
            max_jobs=4,
            success_threshold=3,
            unique_channel_threshold=1,
        )
        # Mark level 2 as problematic (goes from 2 to 1)
        tracker.on_rate_limit("@test", "429")
        assert 2 in tracker.get_problematic_levels()
        # Now need 2 * threshold = 6 successes to go back to 2
        for i in range(5):
            tracker.on_success(f"@test{i}")
        assert tracker.current_jobs == 1  # Still at 1, needs 6 successes
        tracker.on_success("@test5")
        assert tracker.current_jobs == 2  # Now increased after 6

    def test_clears_problematic_level_on_increase(self):
        """Level is removed from problematic when successfully increased to."""
        tracker = RateLimitTracker(
            start_jobs=2,
            max_jobs=4,
            success_threshold=2,
            unique_channel_threshold=1,
        )
        # Mark level 2 as problematic
        tracker.on_rate_limit("@test", "429")
        assert 2 in tracker.get_problematic_levels()
        # Need 2 * threshold = 4 successes to increase back to 2 (problematic level)
        tracker.on_success("@test1")
        tracker.on_success("@test2")
        tracker.on_success("@test3")
        tracker.on_success("@test4")
        assert 2 not in tracker.get_problematic_levels()


class TestReset:
    """Tests for reset method."""

    def test_resets_to_start_jobs(self):
        """Reset restores worker count to initial value."""
        tracker = RateLimitTracker(start_jobs=5)
        tracker._current_jobs = 3
        tracker.reset()
        assert tracker.current_jobs == 5

    def test_clears_success_count(self):
        """Reset clears success count."""
        tracker = RateLimitTracker()
        tracker._success_count = 10
        tracker.reset()
        with tracker._lock:
            assert tracker._success_count == 0

    def test_clears_unique_channels(self):
        """Reset clears unique channels."""
        tracker = RateLimitTracker()
        tracker._unique_channels.add("@test")
        tracker.reset()
        with tracker._lock:
            assert len(tracker._unique_channels) == 0

    def test_clears_problematic_levels(self):
        """Reset clears problematic levels."""
        tracker = RateLimitTracker()
        tracker._problematic_levels.add(3)
        tracker.reset()
        assert tracker.get_problematic_levels() == set()

    def test_clears_level_success_count(self):
        """Reset clears level success counts."""
        tracker = RateLimitTracker()
        tracker._level_success_count[2] = 5
        tracker.reset()
        with tracker._lock:
            assert tracker._level_success_count == {}

    def test_calls_callback_on_reset(self):
        """Callback is called on reset if jobs change."""
        callback = MagicMock()
        tracker = RateLimitTracker(start_jobs=5, on_jobs_changed=callback)
        tracker._current_jobs = 3
        tracker.reset()
        callback.assert_called_once_with(5)

    def test_no_callback_if_same_start_value(self):
        """Callback not called if already at start_jobs."""
        callback = MagicMock()
        tracker = RateLimitTracker(start_jobs=3, on_jobs_changed=callback)
        tracker.reset()
        callback.assert_not_called()


class TestGetProblematicLevels:
    """Tests for get_problematic_levels method."""

    def test_returns_copy_of_set(self):
        """Returns a copy, not the internal set."""
        tracker = RateLimitTracker()
        tracker.on_rate_limit("@test", "429")
        problematic = tracker.get_problematic_levels()
        problematic.clear()  # Modify the returned copy
        # Internal should be unchanged
        assert tracker.get_problematic_levels() != set()

    def test_empty_initially(self):
        """Initially returns empty set."""
        tracker = RateLimitTracker()
        assert tracker.get_problematic_levels() == set()


class TestThreadSafety:
    """Tests for thread-safe operations."""

    def test_property_is_thread_safe(self):
        """current_jobs property uses lock internally."""
        import threading
        tracker = RateLimitTracker(start_jobs=3)
        results = []

        def read_jobs():
            for _ in range(100):
                results.append(tracker.current_jobs)

        threads = [threading.Thread(target=read_jobs) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # Should complete without errors
        assert len(results) == 500


class TestNotifyChange:
    """Tests for _notify_change method."""

    def test_calls_callback_if_provided(self):
        """Callback is invoked when provided."""
        callback = MagicMock()
        tracker = RateLimitTracker(on_jobs_changed=callback)
        tracker._notify_change(5)
        callback.assert_called_once_with(5)

    def test_no_error_without_callback(self):
        """No error when callback is None."""
        tracker = RateLimitTracker(on_jobs_changed=None)
        tracker._notify_change(5)  # Should not raise

    def test_callback_exception_is_caught(self):
        """Exception in callback is caught and logged."""
        def bad_callback(new_jobs):
            msg = "Test error"
            raise ValueError(msg)

        tracker = RateLimitTracker(on_jobs_changed=bad_callback)
        # Should not raise, exception is caught
        tracker._notify_change(5)


class TestLevelSuccessCount:
    """Tests for level success count tracking."""

    def test_tracks_successes_per_level(self):
        """Successes are tracked per worker level."""
        tracker = RateLimitTracker()
        tracker.on_success("@test1")  # Level 2
        tracker.on_success("@test2")  # Level 2
        tracker.on_success("@test3")  # Level 2
        # Increase to level 3
        for i in range(10):
            tracker.on_success(f"@test{i}")
        with tracker._lock:
            assert tracker._level_success_count.get(2, 0) >= 3

    def test_clears_level_count_on_decrease(self):
        """Level count is cleared when decreasing from that level."""
        tracker = RateLimitTracker(start_jobs=3)
        tracker.on_success("@test1")
        tracker.on_success("@test2")
        # Decrease from 3 to 2
        tracker.on_rate_limit("@test", "429")
        with tracker._lock:
            assert 3 not in tracker._level_success_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
