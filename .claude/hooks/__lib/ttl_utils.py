"""TTL utilities with hybrid monotonic/wall-clock safety.

Problem: time.time() is wall-clock and vulnerable to NTP adjustments.
time.monotonic() is monotonic but:
- Old files with wall-clock timestamps checked with monotonic -> always not expired (IMMORTAL)
- System sleep pauses monotonic() -> TTL extends by sleep duration

Solution: Detect clock source from timestamp magnitude and use appropriate clock.
Monotonic timestamps are small (< 1e9). Wall-clock timestamps are large (>= 1e9).
A hybrid approach handles both old (pre-fix) files and new files correctly.

Usage:
    from __lib.ttl_utils import is_expired_monotonic, write_ts, TTL_TOLERANCE

    # Write timestamp (use monotonic for new files)
    data["ts"] = write_ts()

    # Check expiration (hybrid: detects clock source automatically)
    if is_expired_monotonic(data.get("ts", 0), ttl_seconds):
        # expired
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Timestamps below this are assumed to be monotonic (seconds, not epoch)
# Monotonic is typically ~30-300k seconds after boot.
# Wall-clock epoch is ~1.7e9 (2020+).
# Use 1e12 as threshold (1 million seconds ~= 12 days for monotonic,
# but >> 1e9 for any wall-clock timestamp from the past 30 years).
MONOTONIC_THRESHOLD = 1e9

# Tolerance for future-time detection (5 seconds)
# Prevents immortal-state attacks where created_at is set far in the future.
FUTURE_TOLERANCE_SECONDS = 5.0


def is_monotonic_timestamp(ts: float) -> bool:
    """Return True if timestamp appears to be from time.monotonic().

    Detects clock source by magnitude.
    Monotonic timestamps are small (< 1e12).
    Wall-clock timestamps are large (>= 1e9).
    """
    return 0 < ts < MONOTONIC_THRESHOLD


def write_monotonic_ts() -> float:
    """Write a monotonic timestamp for new state files."""
    return time.monotonic()


def write_wallclock_ts() -> float:
    """Write a wall-clock timestamp (for backward compat with old readers).

    Prefer write_monotonic_ts() for new code.
    """
    return time.time()


def get_elapsed(ts: float) -> float:
    """Get elapsed seconds since timestamp, using appropriate clock.

    Detects clock source from timestamp magnitude and uses matching clock.
    Returns negative value if clock source detection fails or ts is invalid.
    """
    if ts <= 0:
        return 0.0

    if is_monotonic_timestamp(ts):
        # Timestamp is from monotonic -> use monotonic for comparison
        return time.monotonic() - ts
    else:
        # Timestamp is from wall-clock -> use wall-clock for comparison
        return time.time() - ts


def is_expired(ts: float, ttl_seconds: float) -> bool:
    """Check if a timestamp is expired based on TTL.

    Uses hybrid clock detection:
    - If ts appears monotonic (small value), uses time.monotonic()
    - If ts appears wall-clock (large value), uses time.time()

    This allows mixing old (wall-clock) and new (monotonic) state files
    during migration without immortal-stale-state bugs.

    Returns True if expired, False if valid or if ts is invalid/zero.
    """
    if ts <= 0:
        return False
    elapsed = get_elapsed(ts)
    return elapsed > ttl_seconds


def sanitize_future_ts(ts: float, clock_fn: callable = time.time) -> float:
    """Prevent immortal-state attacks via future timestamps.

    If ts is significantly in the future (beyond FUTURE_TOLERANCE_SECONDS),
    clamps it to current time. This prevents malicious/misconfigured
    code from writing timestamps that make state effectively immortal.

    Args:
        ts: The timestamp to sanitize
        clock_fn: Clock function to use (default: time.time)

    Returns:
        Sanitized timestamp (capped at current time + tolerance)
    """
    if ts <= 0:
        return clock_fn()
    current = clock_fn()
    if ts > current + FUTURE_TOLERANCE_SECONDS:
        return current
    return ts
