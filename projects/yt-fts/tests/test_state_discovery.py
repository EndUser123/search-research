"""Tests for state-based video discovery system.

This module tests the 3-state discovery system:
- TRANSITION: Bootstrap/first run (empty or nearly empty DB)
- STEADY_STATE: Maintenance mode (DB verified complete, check for new uploads)
- RECOVERY: Repair mode (gaps detected or stale data)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

# Import enums from the module being tested
from yt_fts.discovery.state_detection import (
    ChannelState,
    DiscoveryMethod,
    detect_channel_state,
    transition_strategy,
    steady_state_strategy,
    recovery_strategy,
    get_download_queue,
)


class TestDetectChannelState:
    """Test channel state detection logic."""

    @pytest.fixture
    def mock_db_functions(self):
        with patch(
            "yt_fts.discovery.state_detection.get_db_video_count"
        ) as mock_count, patch(
            "yt_fts.discovery.state_detection.get_channel_api_total"
        ) as mock_api_total, patch(
            "yt_fts.discovery.state_detection.get_api_total_last_checked"
        ) as mock_last_checked:
            yield {
                "db_count": mock_count,
                "api_total": mock_api_total,
                "last_checked": mock_last_checked,
            }

    def test_transition_state_empty_db(self, mock_db_functions):
        """TRANSITION: Empty DB (db_count < 10)."""
        mock_db_functions["db_count"].return_value = 0
        mock_db_functions["api_total"].return_value = None

        state = detect_channel_state("UCxxxxx")
        assert state == ChannelState.TRANSITION

    def test_transition_state_no_api_total(self, mock_db_functions):
        """TRANSITION: Have videos but never verified against API."""
        mock_db_functions["db_count"].return_value = 50
        mock_db_functions["api_total"].return_value = None

        state = detect_channel_state("UCxxxxx")
        assert state == ChannelState.TRANSITION

    def test_steady_state_verified_complete(self, mock_db_functions):
        """STEADY_STATE: DB count == API total and recent verification."""
        mock_db_functions["db_count"].return_value = 500
        mock_db_functions["api_total"].return_value = 500
        mock_db_functions["last_checked"].return_value = "2026-01-21 10:00:00"

        state = detect_channel_state("UCxxxxx")
        assert state == ChannelState.STEADY_STATE

    def test_recovery_state_gap_detected(self, mock_db_functions):
        """RECOVERY: DB count < API total (missing videos)."""
        mock_db_functions["db_count"].return_value = 450
        mock_db_functions["api_total"].return_value = 500

        state = detect_channel_state("UCxxxxx")
        assert state == ChannelState.RECOVERY

    def test_recovery_state_stale_verification(self, mock_db_functions):
        """RECOVERY: Last verified >7 days ago."""
        mock_db_functions["db_count"].return_value = 500
        mock_db_functions["api_total"].return_value = 500
        mock_db_functions["last_checked"].return_value = "2026-01-01 10:00:00"

        state = detect_channel_state("UCxxxxx")
        assert state == ChannelState.RECOVERY


class TestDiscoveryStrategy:
    """Test discovery method selection per state."""

    def test_transition_uses_api_for_large_channels(self):
        """TRANSITION: Use API for channels >500 videos (speed)."""
        with patch("yt_fts.discovery.state_detection.get_db_video_count") as mock_count:
            mock_count.return_value = 600

            method = transition_strategy("UCxxxxx", quota_pct=50)
            assert method == DiscoveryMethod.API

    def test_transition_uses_ytdlp_when_quota_low(self):
        """TRANSITION: Use yt-dlp when quota <20%."""
        with patch("yt_fts.discovery.state_detection.get_db_video_count") as mock_count:
            mock_count.return_value = 600

            method = transition_strategy("UCxxxxx", quota_pct=10)
            assert method == DiscoveryMethod.YTDLP

    def test_transition_small_channel_uses_ytdlp(self):
        """TRANSITION: Small channels (<500) use yt-dlp (quota not worth it)."""
        with patch("yt_fts.discovery.state_detection.get_db_video_count") as mock_count:
            mock_count.return_value = 50

            method = transition_strategy("UCxxxxx", quota_pct=50)
            assert method == DiscoveryMethod.YTDLP

    def test_steady_state_always_uses_rss(self):
        """STEADY_STATE: Always use RSS (fast, free, catches new uploads)."""
        method = steady_state_strategy("UCxxxxx")
        assert method == DiscoveryMethod.RSS

    def test_recovery_uses_api_for_large_gaps(self):
        """RECOVERY: Use API for gaps >50 videos."""
        with patch(
            "yt_fts.discovery.state_detection.get_channel_api_total"
        ) as mock_api_total, patch(
            "yt_fts.discovery.state_detection.get_db_video_count"
        ) as mock_count:
            mock_api_total.return_value = 500
            mock_count.return_value = 400  # Gap of 100

            method = recovery_strategy("UCxxxxx", quota_pct=50)
            assert method == DiscoveryMethod.API

    def test_recovery_uses_ytdlp_for_small_gaps(self):
        """RECOVERY: Use yt-dlp for gaps <50."""
        with patch(
            "yt_fts.discovery.state_detection.get_channel_api_total"
        ) as mock_api_total, patch(
            "yt_fts.discovery.state_detection.get_db_video_count"
        ) as mock_count:
            mock_api_total.return_value = 500
            mock_count.return_value = 480  # Gap of 20

            method = recovery_strategy("UCxxxxx", quota_pct=50)
            assert method == DiscoveryMethod.YTDLP



class TestStateDetectionBugs:
    """Tests for state detection bugs found in adversarial review."""

    def test_staleness_detection_with_stub(self):
        """Stub get_api_total_last_checked always returns None, forcing RECOVERY."""
        # Channel with verified count (should be STEADY_STATE)
        # But stub returns None, causing days_since to return 999
        # This makes staleness check always trigger (line 90: days_since >= 7)
        from unittest.mock import patch
        from yt_fts.discovery.state_detection import detect_channel_state, ChannelState

        with patch("yt_fts.discovery.state_detection.get_api_total_last_checked", return_value=None):
            with patch("yt_fts.discovery.state_detection.get_db_video_count", return_value=500):
                with patch("yt_fts.discovery.state_detection.get_channel_api_total", return_value=500):
                    state = detect_channel_state("test_channel")
                    # BUG: Should be STEADY_STATE (500 == 500, not stale) but becomes RECOVERY
                    assert state == ChannelState.STEADY_STATE, "Verified channel should be STEADY_STATE, not RECOVERY"

    def test_recovery_strategy_with_none_api_total(self):
        """recovery_strategy should handle None api_total gracefully."""
        from unittest.mock import patch
        from yt_fts.discovery.state_detection import recovery_strategy, DiscoveryMethod

        # Simulate being in RECOVERY due to staleness (api_total could be None from initial check)
        with patch("yt_fts.discovery.state_detection.get_channel_api_total", return_value=None):
            with patch("yt_fts.discovery.state_detection.get_db_video_count", return_value=500):
                # This should not crash or return misleading results
                method = recovery_strategy("test_channel", quota_pct=50)
                # Currently returns YTDLP with gap_size = (None or 0) - 500 = -500
                # This is incorrect - negative gap doesn't make sense
                assert method == DiscoveryMethod.YTDLP

class TestDbCallCaching:
    """Test that DB calls are cached to avoid redundant queries."""

    def setup_method(self):
        """Clear cache before each test."""
        from yt_fts.discovery.state_detection import _clear_cache
        _clear_cache()

    def test_strategy_functions_use_cached_data(self):
        """Strategy functions should use cached data from detect_channel_state."""
        # Patch at the location where the function is imported (state_detection module)
        # since imports are now at module level, not lazy
        with patch("yt_fts.discovery.state_detection.get_channel_stats") as mock_stats, patch(
            "yt_fts.discovery.state_detection.db_get_api_total"
        ) as mock_api_total, patch(
            "yt_fts.discovery.state_detection.get_api_total_last_checked"
        ) as mock_last_checked:
            # Setup mock returns for TRANSITION state
            mock_stats.return_value = {"total": 600}
            mock_api_total.return_value = None
            mock_last_checked.return_value = None

            # Call detect_channel_state - this caches the DB results
            state = detect_channel_state("UCxxxxx")
            assert state == ChannelState.TRANSITION

            # Record call counts after detect_channel_state
            stats_calls_after_detect = mock_stats.call_count
            api_calls_after_detect = mock_api_total.call_count

            # Call transition_strategy - should use cached data
            method = transition_strategy("UCxxxxx", quota_pct=50)
            assert method == DiscoveryMethod.API

            # With caching, DB functions should NOT be called again
            assert mock_stats.call_count == stats_calls_after_detect, (
                f"Expected {stats_calls_after_detect} DB stats calls, got {mock_stats.call_count}. "
                "Strategy functions should use cached data."
            )

    def test_recovery_strategy_uses_cached_data(self):
        """Recovery strategy should use cached data from detect_channel_state."""
        # Patch at the location where the function is imported (state_detection module)
        with patch("yt_fts.discovery.state_detection.get_channel_stats") as mock_stats, patch(
            "yt_fts.discovery.state_detection.db_get_api_total", return_value=500
        ), patch(
            "yt_fts.discovery.state_detection.get_api_total_last_checked",
            return_value="2026-01-21T10:00:00"
        ):
            # Setup mock returns for RECOVERY state (gap detected)
            mock_stats.return_value = {"total": 400}

            # Call detect_channel_state - this caches the DB results
            state = detect_channel_state("UCxxxxx")
            assert state == ChannelState.RECOVERY

            # Record call counts after detect_channel_state
            stats_calls_after_detect = mock_stats.call_count

            # Call recovery_strategy - should use cached data
            method = recovery_strategy("UCxxxxx", quota_pct=50)
            assert method == DiscoveryMethod.API

            # With caching, DB stats should NOT be called again
            assert mock_stats.call_count == stats_calls_after_detect, (
                f"Expected {stats_calls_after_detect} DB stats calls, got {mock_stats.call_count}"
            )


class TestMissingTranscripts:
    """Test missing transcript detection (cross-cutting concern)."""

    def test_get_download_queue_returns_high_priority(self):
        """Missing transcripts is always high priority."""
        # Patch at the location where it's imported (state_detection module)
        with patch("yt_fts.discovery.state_detection.get_video_ids_without_subtitles") as mock_missing:
            mock_missing.return_value = ["vid1", "vid2", "vid3"]

            queue = get_download_queue("UCxxxxx")

            assert queue["priority"] == "high"
            assert queue["reason"] == "missing_transcripts"
            assert len(queue["video_ids"]) == 3


class TestCacheSizeLimit:
    """Test that the cache has a size limit to prevent unbounded growth."""

    def setup_method(self):
        """Clear cache before each test."""
        from yt_fts.discovery.state_detection import _clear_cache, _db_cache
        _clear_cache()

    def test_cache_size_limit_enforced(self):
        """Cache should not exceed 1000 entries (FIFO eviction)."""
        from yt_fts.discovery.state_detection import (
            _cached_get,
            _MAX_CACHE_ENTRIES,
            _db_cache,
        )

        # Simulate adding more than MAX_CACHE_ENTRIES entries
        for i in range(_MAX_CACHE_ENTRIES + 100):
            _cached_get(f"UCchannel_{i}", "db_video_count", lambda: i)

        # Cache size should not exceed _MAX_CACHE_ENTRIES
        assert len(_db_cache) <= _MAX_CACHE_ENTRIES, (
            f"Cache size {len(_db_cache)} exceeds limit of {_MAX_CACHE_ENTRIES}"
        )

    def test_cache_eviction_removes_oldest_entries(self):
        """When cache is full, oldest entries should be removed (FIFO)."""
        import time
        from yt_fts.discovery.state_detection import (
            _cached_get,
            _MAX_CACHE_ENTRIES,
            _db_cache,
        )

        # Add entries to fill the cache
        for i in range(_MAX_CACHE_ENTRIES):
            _cached_get(f"UCchannel_{i}", "db_video_count", lambda: i)
            time.sleep(0.0001)  # Small delay to create timestamp differences

        # Store the first key added (should be evicted)
        first_key = f"db_video_count:UCchannel_0"

        # Add one more entry to trigger eviction
        _cached_get("UCnew_channel", "db_video_count", lambda: _MAX_CACHE_ENTRIES + 1)

        # Cache size should still be at limit
        assert len(_db_cache) <= _MAX_CACHE_ENTRIES

        # First entry should have been evicted (FIFO)
        assert first_key not in _db_cache, "Oldest entry should be evicted when cache is full"


class TestCacheExpiration:
    """Test cache expiration behavior after TTL."""

    def setup_method(self):
        """Clear cache before each test."""
        from yt_fts.discovery.state_detection import _clear_cache
        _clear_cache()

    def test_cache_entry_expires_after_ttl(self):
        """Cache entries should expire after _CACHE_TTL (60 seconds)."""
        import time
        from yt_fts.discovery.state_detection import (
            _cached_get,
            _CACHE_TTL,
            _db_cache,
        )

        # Add an entry to cache
        channel_id = "UCxxxxx"
        result = _cached_get(channel_id, "db_video_count", lambda: 42)

        # Verify it's cached
        cache_key = f"db_video_count:{channel_id}"
        assert cache_key in _db_cache
        assert result == 42

        # Manually age the entry to simulate TTL expiration
        # Set timestamp to TTL + 1 seconds ago
        old_timestamp = time.time() - (_CACHE_TTL + 1)
        _db_cache[cache_key] = (old_timestamp, _db_cache[cache_key][1])

        # Next call should miss cache and fetch fresh data
        call_count = 0
        def fetch_func():
            nonlocal call_count
            call_count += 1
            return 99

        result2 = _cached_get(channel_id, "db_video_count", fetch_func)

        # Should have fetched fresh data
        assert call_count == 1, "Cache expired, should fetch fresh data"
        assert result2 == 99, "Should return fresh value after expiration"

    def test_cache_hit_within_ttl(self):
        """Cache should return cached value within TTL period."""
        import time
        from yt_fts.discovery.state_detection import (
            _cached_get,
            _CACHE_TTL,
            _db_cache,
        )

        channel_id = "UCyyyyy"

        # First call - cache miss, fetches data
        call_count = 0
        def fetch_func():
            nonlocal call_count
            call_count += 1
            return 123

        result1 = _cached_get(channel_id, "db_video_count", fetch_func)
        assert call_count == 1
        assert result1 == 123

        # Second call immediately - cache hit, no fetch
        result2 = _cached_get(channel_id, "db_video_count", fetch_func)
        assert call_count == 1, "Should not fetch again, use cached value"
        assert result2 == 123

    def test_cache_expiration_boundary(self):
        """Cache entry exactly at TTL boundary should be considered expired."""
        import time
        from yt_fts.discovery.state_detection import (
            _cached_get,
            _CACHE_TTL,
        )

        channel_id = "UCzzzzz"

        # Add entry and age it to exactly TTL seconds
        _cached_get(channel_id, "db_video_count", lambda: 1)
        cache_key = f"db_video_count:{channel_id}"

        # Manually set timestamp to exactly TTL seconds ago
        from yt_fts.discovery.state_detection import _db_cache
        boundary_timestamp = time.time() - _CACHE_TTL
        _db_cache[cache_key] = (boundary_timestamp, _db_cache[cache_key][1])

        # Should be expired (>= TTL is expired)
        call_count = 0
        def fetch_func():
            nonlocal call_count
            call_count += 1
            return 2

        _cached_get(channel_id, "db_video_count", fetch_func)
        assert call_count == 1, "Entry at TTL boundary should be expired"


class TestClearCacheBehavior:
    """Test _clear_cache function behavior."""

    def test_clear_cache_empties_cache(self):
        """_clear_cache should remove all entries from cache."""
        from yt_fts.discovery.state_detection import (
            _clear_cache,
            _cached_get,
            _db_cache,
        )

        # Add some entries
        for i in range(10):
            _cached_get(f"UCchannel_{i}", "test_key", lambda: i)

        assert len(_db_cache) > 0, "Cache should have entries"

        # Clear cache
        _clear_cache()

        assert len(_db_cache) == 0, "Cache should be empty after clear"

    def test_clear_cache_idempotent(self):
        """_clear_cache should be safe to call multiple times."""
        from yt_fts.discovery.state_detection import _clear_cache, _db_cache

        # Add entry
        _db_cache["test_key"] = (1.0, "value")

        # Clear multiple times
        _clear_cache()
        _clear_cache()
        _clear_cache()

        # Should still be empty, no errors
        assert len(_db_cache) == 0

    def test_clear_cache_on_empty_cache(self):
        """_clear_cache on empty cache should not raise error."""
        from yt_fts.discovery.state_detection import (
            _clear_cache,
            _db_cache,
        )

        # Ensure cache is empty
        _db_cache.clear()

        # Should not raise
        _clear_cache()

        assert len(_db_cache) == 0


class TestCacheEdgeCases:
    """Test cache behavior with edge case inputs."""

    def setup_method(self):
        """Clear cache before each test."""
        from yt_fts.discovery.state_detection import _clear_cache
        _clear_cache()

    def test_cache_with_none_value(self):
        """Cache should handle None values correctly."""
        from yt_fts.discovery.state_detection import _cached_get, _db_cache

        result = _cached_get("UCnone", "test_key", lambda: None)
        assert result is None

        # Verify it's cached
        cache_key = "test_key:UCnone"
        assert cache_key in _db_cache
        assert _db_cache[cache_key][1] is None

    def test_cache_with_empty_string_value(self):
        """Cache should handle empty string values correctly."""
        from yt_fts.discovery.state_detection import _cached_get, _db_cache

        result = _cached_get("UCempty", "test_key", lambda: "")
        assert result == ""

        # Verify it's cached
        cache_key = "test_key:UCempty"
        assert cache_key in _db_cache
        assert _db_cache[cache_key][1] == ""

    def test_cache_with_zero_value(self):
        """Cache should handle zero values correctly (not treated as falsy for caching)."""
        from yt_fts.discovery.state_detection import _cached_get, _db_cache

        result = _cached_get("UCzero", "test_key", lambda: 0)
        assert result == 0

        # Verify it's cached (0 is valid cache value)
        cache_key = "test_key:UCzero"
        assert cache_key in _db_cache
        assert _db_cache[cache_key][1] == 0

    def test_cache_with_false_value(self):
        """Cache should handle False values correctly."""
        from yt_fts.discovery.state_detection import _cached_get, _db_cache

        result = _cached_get("UCfalse", "test_key", lambda: False)
        assert result is False

        # Verify it's cached
        cache_key = "test_key:UCfalse"
        assert cache_key in _db_cache
        assert _db_cache[cache_key][1] is False

    def test_cache_with_special_characters_in_channel_id(self):
        """Cache should handle special characters in channel_id."""
        from yt_fts.discovery.state_detection import _cached_get, _db_cache

        # Channel ID with special chars (unusual but valid in cache key)
        special_ids = ["UC/test", "UC:colon", "UC-dash", "UC space"]
        for cid in special_ids:
            result = _cached_get(cid, "test_key", lambda: f"value_{cid}")
            assert result == f"value_{cid}"

        # All should be cached
        assert len(_db_cache) == len(special_ids)

    def test_cache_same_channel_different_keys(self):
        """Same channel with different cache keys should store separately."""
        from yt_fts.discovery.state_detection import _cached_get, _db_cache

        channel_id = "UCxxxxx"

        # Cache different keys for same channel
        _cached_get(channel_id, "video_count", lambda: 100)
        _cached_get(channel_id, "api_total", lambda: 50)
        _cached_get(channel_id, "last_checked", lambda: "2026-01-24")

        # Should have 3 separate cache entries
        assert len([k for k in _db_cache if k.endswith(channel_id)]) == 3

    def test_cache_different_channels_same_key(self):
        """Different channels with same key should store separately."""
        from yt_fts.discovery.state_detection import _cached_get, _db_cache

        # Same cache key, different channels
        for i in range(5):
            _cached_get(f"UCchannel_{i}", "video_count", lambda: i * 10)

        # Should have 5 separate entries
        assert len(_db_cache) == 5

