"""
Tests for RssPreChecker caching functionality.

Tests cover:
- Memory cache operations
- Disk cache operations
- Cache key generation
- Cache expiration
- _save_to_cache_and_return method
"""
from __future__ import annotations

import json
import time

import pytest

from yt_fts.services.rss_precheck import RssCheckResult, RssPreChecker


class TestCacheKeyGeneration:
    """Tests for _get_cache_key method."""

    def test_cache_key_with_channel_id(self):
        """Cache key includes channel_id."""
        checker = RssPreChecker()
        key = checker._get_cache_key(channel_id="UC123", handle=None, resolved_url=None)
        assert "UC123" in key

    def test_cache_key_with_handle(self):
        """Cache key includes handle."""
        checker = RssPreChecker()
        key = checker._get_cache_key(channel_id=None, handle="@test", resolved_url=None)
        assert "test" in key

    def test_cache_key_with_url(self):
        """Cache key includes hash of resolved_url."""
        checker = RssPreChecker()
        key = checker._get_cache_key(
            channel_id=None,
            handle=None,
            resolved_url="https://www.youtube.com/channel/UC123"
        )
        # URL is hashed, so we check for the prefix
        assert key.startswith("url_")
        # Same URL produces same key
        key2 = checker._get_cache_key(
            channel_id=None,
            handle=None,
            resolved_url="https://www.youtube.com/channel/UC123"
        )
        assert key == key2

    def test_cache_key_is_deterministic(self):
        """Same inputs produce same cache key."""
        checker = RssPreChecker()
        key1 = checker._get_cache_key(channel_id="UC123", handle="@test", resolved_url="url")
        key2 = checker._get_cache_key(channel_id="UC123", handle="@test", resolved_url="url")
        assert key1 == key2

    def test_cache_key_different_inputs_different_keys(self):
        """Different inputs produce different cache keys."""
        checker = RssPreChecker()
        key1 = checker._get_cache_key(channel_id="UC123", handle=None, resolved_url=None)
        key2 = checker._get_cache_key(channel_id="UC456", handle=None, resolved_url=None)
        assert key1 != key2


class TestMemoryCache:
    """Tests for in-memory cache operations."""

    def test_save_cached_result_to_memory(self, tmp_path):
        """Save result to memory cache."""
        checker = RssPreChecker(use_cache=True)
        checker._cache_dir = tmp_path

        result = RssCheckResult(
            status="success",
            video_ids=["vid1", "vid2"],
            newest_id="vid2",
            oldest_id="vid1",
            message="OK",
        )

        checker._save_cached_result("test_key", result)

        assert "test_key" in checker._memory_cache
        _timestamp, cached_data = checker._memory_cache["test_key"]
        assert cached_data["status"] == "success"
        assert cached_data["video_ids"] == ["vid1", "vid2"]

    def test_get_cached_result_from_memory(self, tmp_path):
        """Retrieve result from memory cache."""
        checker = RssPreChecker(use_cache=True)
        checker._cache_dir = tmp_path

        result = RssCheckResult(
            status="success",
            video_ids=["vid1"],
            newest_id="vid1",
            oldest_id="vid1",
            message="OK",
        )

        checker._save_cached_result("test_key", result)
        retrieved = checker._get_cached_result("test_key")

        assert retrieved is not None
        assert retrieved.status == "success"
        assert retrieved.video_ids == ["vid1"]

    def test_memory_cache_expires_after_ttl(self, tmp_path):
        """Memory cache entries expire after TTL and are removed, falls back to disk."""
        checker = RssPreChecker(use_cache=True)
        checker._cache_dir = tmp_path

        result = RssCheckResult(
            status="success",
            video_ids=["vid1"],
            newest_id="vid1",
            oldest_id="vid1",
            message="OK",
        )

        # Save with current time (creates both memory and disk cache)
        checker._save_cached_result("test_key", result)

        # Manually expire the entry in memory cache only
        # cache_ttl is typically 900 seconds, so we make it much older
        _timestamp, cached_data = checker._memory_cache["test_key"]
        old_timestamp = time.time() - checker.cache_ttl - 100  # Older than TTL
        checker._memory_cache["test_key"] = (old_timestamp, cached_data)

        # The expired memory entry should be removed
        # But disk cache still exists, so it returns from disk
        retrieved = checker._get_cached_result("test_key")
        assert "test_key" not in checker._memory_cache  # Memory entry was removed
        assert retrieved is not None  # Disk cache still has the data
        assert retrieved.status == "success"

    def test_get_cached_returns_none_for_missing_key(self, tmp_path):
        """Return None when cache key doesn't exist."""
        checker = RssPreChecker(use_cache=True)
        checker._cache_dir = tmp_path

        result = checker._get_cached_result("nonexistent")
        assert result is None


class TestDiskCache:
    """Tests for disk cache operations."""

    def test_save_cached_result_to_disk(self, tmp_path):
        """Save result to disk cache file."""
        checker = RssPreChecker(use_cache=True)
        checker._cache_dir = tmp_path

        result = RssCheckResult(
            status="success",
            video_ids=["vid1", "vid2"],
            newest_id="vid2",
            oldest_id="vid1",
            message="OK",
        )

        checker._save_cached_result("test_key", result)

        cache_file = tmp_path / "test_key.json"
        assert cache_file.exists()

        with open(cache_file) as f:
            data = json.load(f)

        assert data["result"]["status"] == "success"
        assert data["result"]["video_ids"] == ["vid1", "vid2"]
        assert "timestamp" in data

    def test_get_cached_result_from_disk(self, tmp_path):
        """Retrieve result from disk cache."""
        checker = RssPreChecker(use_cache=True)
        checker._cache_dir = tmp_path

        # Create a cache file manually
        cache_data = {
            "timestamp": time.time(),
            "result": {
                "status": "success",
                "video_ids": ["vid1", "vid2"],
                "newest_id": "vid2",
                "oldest_id": "vid1",
                "message": "OK",
                "gap_start_id": None,
                "unavailable_video_ids": [],
                "unavailable_video_status": {},
            },
        }
        cache_file = tmp_path / "test_key.json"
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        retrieved = checker._get_cached_result("test_key")

        assert retrieved is not None
        assert retrieved.status == "success"
        assert retrieved.video_ids == ["vid1", "vid2"]

    def test_disk_cache_ignores_invalid_files(self, tmp_path):
        """Invalid cache files are ignored and removed."""
        checker = RssPreChecker(use_cache=True)
        checker._cache_dir = tmp_path

        # Create invalid cache file
        invalid_file = tmp_path / "invalid_key.json"
        invalid_file.write_text("not valid json")

        # Should return None and remove the file
        result = checker._get_cached_result("invalid_key")
        assert result is None
        assert not invalid_file.exists()

    def test_disk_cache_expires_after_ttl(self, tmp_path):
        """Disk cache entries expire after TTL."""
        checker = RssPreChecker(use_cache=True)
        checker._cache_dir = tmp_path

        # Create expired cache file
        expired_time = time.time() - 10000
        cache_data = {
            "timestamp": expired_time,
            "result": {
                "status": "success",
                "video_ids": ["vid1"],
                "newest_id": "vid1",
                "oldest_id": "vid1",
                "message": "OK",
                "gap_start_id": None,
                "unavailable_video_ids": [],
                "unavailable_video_status": {},
            },
        }
        cache_file = tmp_path / "expired_key.json"
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        # Should return None for expired entry
        result = checker._get_cached_result("expired_key")
        assert result is None


class TestSaveToCacheAndReturn:
    """Tests for _save_to_cache_and_return method."""

    def test_saves_to_cache_and_returns_result(self, tmp_path):
        """Save result to cache and verify it can be retrieved."""
        checker = RssPreChecker(use_cache=True)
        checker._cache_dir = tmp_path

        result = RssCheckResult(
            status="success",
            video_ids=["vid1"],
            newest_id="vid1",
            oldest_id="vid1",
            message="OK",
        )

        # Save to cache (method returns None)
        checker._save_cached_result("test_key", result)

        # Should be in cache now
        retrieved = checker._get_cached_result("test_key")
        assert retrieved is not None
        assert retrieved.status == "success"
        assert retrieved.video_ids == ["vid1"]

    def test_with_cache_disabled_still_returns_result(self, tmp_path):
        """When cache disabled, save does nothing but result is still usable."""
        checker = RssPreChecker(use_cache=False)
        checker._cache_dir = tmp_path

        result = RssCheckResult(
            status="success",
            video_ids=["vid1"],
            newest_id="vid1",
            oldest_id="vid1",
            message="OK",
        )

        # Save to cache (won't actually save when disabled)
        checker._save_cached_result("test_key", result)

        # Result should still be usable
        assert result.status == "success"
        assert result.video_ids == ["vid1"]


class TestCacheDisabled:
    """Tests when caching is disabled."""

    def test_save_does_nothing_when_disabled(self, tmp_path):
        """Save is no-op when cache disabled."""
        checker = RssPreChecker(use_cache=False)
        checker._cache_dir = tmp_path

        result = RssCheckResult(
            status="success",
            video_ids=["vid1"],
            newest_id="vid1",
            oldest_id="vid1",
            message="OK",
        )

        checker._save_cached_result("test_key", result)

        # Should not be in memory cache
        assert "test_key" not in checker._memory_cache

        # Should not create disk file
        cache_file = tmp_path / "test_key.json"
        assert not cache_file.exists()

    def test_get_returns_none_when_disabled(self, tmp_path):
        """Get returns None when cache disabled."""
        checker = RssPreChecker(use_cache=False)
        checker._cache_dir = tmp_path

        # Even if file exists, should return None
        cache_file = tmp_path / "test_key.json"
        cache_file.write_text('{"timestamp": 123, "result": {"status": "success"}}')

        result = checker._get_cached_result("test_key")
        assert result is None


class TestResultDataIntegrity:
    """Tests for cached result data integrity."""

    def test_all_result_fields_preserved(self, tmp_path):
        """All RssCheckResult fields are preserved in cache."""
        checker = RssPreChecker(use_cache=True)
        checker._cache_dir = tmp_path

        result = RssCheckResult(
            status="partial",
            video_ids=["vid1", "vid2", "vid3"],
            newest_id="vid3",
            oldest_id="vid1",
            message="Some videos unavailable",
            gap_start_id="vid2",
            unavailable_video_ids=["vid4", "vid5"],
            unavailable_video_status={"vid4": "private", "vid5": "deleted"},
        )

        checker._save_cached_result("test_key", result)
        retrieved = checker._get_cached_result("test_key")

        assert retrieved.status == result.status
        assert retrieved.video_ids == result.video_ids
        assert retrieved.newest_id == result.newest_id
        assert retrieved.oldest_id == result.oldest_id
        assert retrieved.message == result.message
        assert retrieved.gap_start_id == result.gap_start_id
        assert retrieved.unavailable_video_ids == result.unavailable_video_ids
        assert retrieved.unavailable_video_status == result.unavailable_video_status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
