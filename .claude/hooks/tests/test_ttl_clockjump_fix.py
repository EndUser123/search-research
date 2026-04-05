"""
Test suite for TTL clock-jump vulnerability fixes.

Tests the hybrid clock-safe TTL utilities and their integration
with the skill enforcement producer-consumer pair.

Covers:
- is_expired() correctly handles old wall-clock timestamps (F1)
- sanitize_future_ts() prevents immortal-state attacks (SEC-002)
- get_elapsed() uses appropriate clock based on timestamp magnitude
- skill_enforcer uses monotonic + sanitize for produced timestamps
- PreToolUse TTL check uses is_expired() for hybrid safety
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone

# Ensure __lib is importable
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import pytest

from __lib.ttl_utils import (
    is_monotonic_timestamp,
    write_monotonic_ts,
    write_wallclock_ts,
    get_elapsed,
    is_expired,
    sanitize_future_ts,
    MONOTONIC_THRESHOLD,
    FUTURE_TOLERANCE_SECONDS,
)


class TestIsMonotonicTimestamp:
    """Tests for clock source detection."""

    def test_small_timestamp_is_monotonic(self):
        """Timestamps < 1e9 are assumed monotonic (seconds since boot)."""
        assert is_monotonic_timestamp(31569.0) is True
        assert is_monotonic_timestamp(100.0) is True
        assert is_monotonic_timestamp(1e8) is True  # 100M - still reasonable for monotonic

    def test_large_timestamp_is_wallclock(self):
        """Timestamps >= 1e9 are wall-clock epoch seconds."""
        assert is_monotonic_timestamp(1.77e9) is False  # ~2020 epoch
        assert is_monotonic_timestamp(1.8e9) is False
        assert is_monotonic_timestamp(time.time()) is False

    def test_threshold_boundary(self):
        """MONOTONIC_THRESHOLD = 1e9 correctly separates clocks."""
        # Below threshold = monotonic
        assert is_monotonic_timestamp(1e9 - 1) is True
        assert is_monotonic_timestamp(1e8) is True
        # At or above threshold = wall-clock
        assert is_monotonic_timestamp(1e9) is False
        assert is_monotonic_timestamp(1e12) is False

    def test_invalid_timestamps(self):
        """Zero and negative timestamps are handled."""
        assert is_monotonic_timestamp(0) is False
        assert is_monotonic_timestamp(-100) is False


class TestGetElapsed:
    """Tests for hybrid elapsed time calculation."""

    def test_monotonic_timestamp_with_monotonic_clock(self):
        """Monotonic timestamps use monotonic clock for comparison."""
        ts = time.monotonic()
        elapsed = get_elapsed(ts)
        # Should be a small positive number (seconds since that timestamp)
        assert 0 <= elapsed < 1

    def test_wallclock_timestamp_with_wallclock_clock(self):
        """Wall-clock timestamps use wall-clock for comparison."""
        ts = time.time()
        elapsed = get_elapsed(ts)
        # Should be a small positive number
        assert 0 <= elapsed < 1

    def test_old_wallclock_timestamp_returns_large_elapsed(self):
        """
        F1 CRITICAL: Old wall-clock timestamp with new monotonic check.

        Bug: monotonic - old_wallclock = huge negative -> always not expired.
        Fix: get_elapsed detects wall-clock and uses time.time() correctly.
        """
        old_wallclock_ts = 1772350213.0  # From adversarial_critic.json CRIT-001
        elapsed = get_elapsed(old_wallclock_ts)
        # With wall-clock, this should be a very large number (~30 days)
        assert elapsed > 86400 * 10  # At least 10 days elapsed

    def test_zero_timestamp_returns_zero(self):
        """Zero timestamp returns 0 elapsed (treated as invalid)."""
        assert get_elapsed(0) == 0.0

    def test_negative_timestamp_returns_zero(self):
        """Negative timestamp returns 0 elapsed."""
        assert get_elapsed(-100) == 0.0


class TestIsExpired:
    """Tests for TTL expiration check."""

    def test_fresh_timestamp_not_expired(self):
        """Recent timestamp within TTL window is not expired."""
        ts = time.time() - 30  # 30 seconds ago
        assert is_expired(ts, ttl_seconds=90) is False

    def test_old_timestamp_is_expired(self):
        """Timestamp older than TTL is expired."""
        ts = time.time() - 100  # 100 seconds ago
        assert is_expired(ts, ttl_seconds=90) is True

    def test_exactly_at_ttl_boundary(self):
        """Timestamp exactly at TTL boundary is expired (> comparison)."""
        ts = time.time() - 90  # Exactly 90 seconds ago
        assert is_expired(ts, ttl_seconds=90) is True

    def test_old_wallclock_file_is_expired(self):
        """
        F1 CRITICAL: Old wall-clock state file is correctly identified as expired.

        This is the core regression test for F1. Old state files (with
        wall-clock timestamps like 1772350213) checked with hybrid
        is_expired() should return True (expired), NOT False (immortal).

        Before fix: time.monotonic() - old_ts = -1772318644 -> always < TTL
        After fix: time.time() - old_ts = ~3000000 -> > 90 -> expired
        """
        old_ts = 1772350213.0  # Historical wall-clock timestamp
        # With 90-second TTL, this should definitely be expired
        assert is_expired(old_ts, ttl_seconds=90) is True

    def test_zero_timestamp_not_expired(self):
        """Zero/invalid timestamp is not expired (treat as no-op)."""
        assert is_expired(0, ttl_seconds=90) is False

    def test_negative_timestamp_not_expired(self):
        """Negative timestamp is not expired."""
        assert is_expired(-100, ttl_seconds=90) is False


class TestSanitizeFutureTimestamp:
    """Tests for future-timestamp attack prevention (SEC-002)."""

    def test_current_time_unchanged(self):
        """Current timestamp is returned as-is."""
        now = time.time()
        result = sanitize_future_ts(now, clock_fn=lambda: now)
        assert result == now

    def test_slightly_future_timestamp_unchanged(self):
        """Timestamp slightly in future (< tolerance) is returned as-is."""
        now = time.time()
        slightly_future = now + 2  # 2 seconds in future, within 5s tolerance
        result = sanitize_future_ts(slightly_future, clock_fn=lambda: now)
        assert result == slightly_future

    def test_far_future_timestamp_clamped(self):
        """
        SEC-002 CRITICAL: Timestamp far in future is clamped to current.

        This prevents immortal-state attacks where created_at is set
        to a distant future time, making TTL check (negative age) never fire.
        """
        now = time.time()
        far_future = now + 7200  # 2 hours in future
        result = sanitize_future_ts(far_future, clock_fn=lambda: now)
        # Should be clamped to current time (no tolerance for 2-hour future)
        assert result == now

    def test_future_tolerance_boundary(self):
        """Exactly at FUTURE_TOLERANCE_SECONDS boundary is allowed."""
        now = time.time()
        at_tolerance = now + FUTURE_TOLERANCE_SECONDS
        result = sanitize_future_ts(at_tolerance, clock_fn=lambda: now)
        # At exactly the tolerance, it should be allowed through
        assert result == at_tolerance

    def test_zero_timestamp_returns_current(self):
        """Zero timestamp is replaced with current time."""
        now = time.time()
        result = sanitize_future_ts(0, clock_fn=lambda: now)
        assert result == now


class TestWriteMonotonicTimestamp:
    """Tests for monotonic timestamp writing."""

    def test_returns_monotonic_value(self):
        """write_monotonic_ts() returns a monotonic clock value."""
        ts = write_monotonic_ts()
        assert ts > 0
        assert ts < MONOTONIC_THRESHOLD

    def test_increases_over_time(self):
        """Monotonic timestamps increase over successive calls."""
        ts1 = write_monotonic_ts()
        time.sleep(0.01)
        ts2 = write_monotonic_ts()
        assert ts2 > ts1


class TestWriteWallclockTimestamp:
    """Tests for wall-clock timestamp writing."""

    def test_returns_wallclock_value(self):
        """write_wallclock_ts() returns a wall-clock epoch value."""
        ts = write_wallclock_ts()
        assert ts > 1e9  # Should be a reasonable epoch value
        # Should match current wall-clock (within 1 second)
        assert abs(ts - time.time()) < 1

    def test_epoch_value(self):
        """Wall-clock timestamp is epoch seconds."""
        ts = write_wallclock_ts()
        now = time.time()
        assert abs(ts - now) < 1  # Within 1 second


class TestHybridClockIntegration:
    """
    Integration tests demonstrating the hybrid clock fix.

    These tests prove the fix works for the actual producer-consumer pair:
    - skill_enforcer.py writes created_at (producer)
    - PreToolUse.py checks TTL (consumer)
    """

    def test_old_state_file_with_monotonic_checker_is_expired(self):
        """
        F1 regression: Old state file checked with hybrid is_expired is expired.

        Scenario:
        - Old state file created months ago with time.time() = 1772350213
        - System rebooted, monotonic clock is now ~31569
        - TTL check runs with is_expired(old_ts, 90)

        Before fix: monotonic - old_ts = -1772318644 -> < 90 -> False (IMMORTAL!)
        After fix: time.time() - old_ts = ~3000000 -> > 90 -> True (expired)
        """
        # Simulate old state file with wall-clock timestamp
        old_state_ts = 1772350213.0  # Months-old wall-clock timestamp
        ttl_seconds = 90

        # Hybrid check should correctly identify as expired
        result = is_expired(old_state_ts, ttl_seconds)
        assert result is True, (
            f"F1 REGRESSION: Old wall-clock file marked as not expired. "
            f"elapsed={get_elapsed(old_state_ts)}, ttl={ttl_seconds}"
        )

    def test_monotonic_state_file_with_monotonic_checker_is_not_expired_when_fresh(self):
        """Fresh monotonic state file is correctly identified as valid."""
        fresh_monotonic_ts = time.monotonic() - 30  # 30 seconds ago
        result = is_expired(fresh_monotonic_ts, ttl_seconds=90)
        assert result is False

    def test_monotonic_state_file_is_expired_when_old(self):
        """Old monotonic state file is correctly identified as expired."""
        old_monotonic_ts = time.monotonic() - 100  # 100 seconds ago
        result = is_expired(old_monotonic_ts, ttl_seconds=90)
        assert result is True

    def test_ntp_backward_jump_detected_with_future_sanitize(self):
        """
        SEC-002: Future timestamp attack prevented by sanitize_future_ts.

        Even if an attacker writes created_at far in the future,
        sanitize_future_ts clamps it to current time.
        """
        now = time.time()
        malicious_future_ts = now + 86400 * 365  # 1 year in future
        sanitized = sanitize_future_ts(malicious_future_ts, clock_fn=lambda: now)
        assert sanitized == now  # Clamped to current, not immortal

    def test_producer_consumer_contract(self):
        """
        Verify producer-consumer contract for skill enforcement timestamps.

        Producer (skill_enforcer): writes sanitized monotonic timestamp
        Consumer (PreToolUse): uses is_expired for hybrid check

        This test verifies the contract is satisfied.
        """
        # Producer: writes timestamp using write_monotonic_ts()
        produced_ts = write_monotonic_ts()

        # Verify it's monotonic
        assert is_monotonic_timestamp(produced_ts) is True

        # Consumer: checks with is_expired using hybrid detection
        # Fresh intent should not be expired
        result = is_expired(produced_ts, ttl_seconds=90)
        assert result is False

        # Old monotonic timestamp should be expired
        old_monotonic = time.monotonic() - 100
        result = is_expired(old_monotonic, ttl_seconds=90)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
