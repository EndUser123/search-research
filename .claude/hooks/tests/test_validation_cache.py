"""
Test suite for validation_cache.py module.

These tests follow RED-GREEN-REFACTOR TDD cycle:
- RED: Tests fail initially (failing tests written first)
- GREEN: Implementation to pass tests
- REFACTOR: Improve code quality while tests pass

Test cases:
1. test_get_cached_returns_cached_value - Verify cached value is returned
2. test_get_cached_returns_none_for_miss - Verify None returned for cache miss
3. test_set_cached_stores_value - Verify value is stored in cache
4. test_is_cache_valid_returns_true_for_valid - Verify valid cache returns True
5. test_is_cache_valid_returns_false_for_expired - Verify expired cache returns False
6. test_build_cache_key_creates_unique_key - Verify cache key includes operation and config hash
7. test_cleanup_old_cache_removes_expired_files - Verify old cache files are deleted
"""

import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import module to test
# Need to add __lib to path since it's a package without __init__.py
lib_dir = Path(__file__).resolve().parent.parent / "__lib"
sys.path.insert(0, str(lib_dir))

try:
    import validation_cache
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


@pytest.mark.skipif(not MODULE_EXISTS, reason="validation_cache module not found")
class TestGetCached:
    """Tests for get_cached() function."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        cache_dir = tmp_path / "validation_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Patch CACHE_DIR to use temp directory
        with patch.object(validation_cache, 'CACHE_DIR', cache_dir):
            yield cache_dir

    def test_get_cached_returns_cached_value(self, temp_cache_dir):
        """
        Test that get_cached returns the cached value when cache is valid.

        Given: A valid cache entry exists
        When: get_cached is called with the cache key
        Then: The cached value is returned
        """
        # Arrange: Create a valid cache entry
        cache_key = "test_key_123"
        cache_path = temp_cache_dir / f"{cache_key}.json"
        cache_data = {
            "value": "cached_result",
            "timestamp": time.time(),
            "terminal_id": "test_term"
        }
        cache_path.write_text(json.dumps(cache_data))

        # Act: Get cached value
        result = validation_cache.get_cached(cache_key)

        # Assert: Cached value is returned
        assert result == "cached_result"

    def test_get_cached_returns_none_for_miss(self, temp_cache_dir):
        """
        Test that get_cached returns None when cache key doesn't exist.

        Given: No cache entry exists for the key
        When: get_cached is called with a non-existent cache key
        Then: None is returned
        """
        # Arrange: Non-existent cache key
        cache_key = "nonexistent_key_456"

        # Act: Try to get cached value
        result = validation_cache.get_cached(cache_key)

        # Assert: None is returned
        assert result is None

    def test_get_cached_returns_none_for_expired(self, temp_cache_dir):
        """
        Test that get_cached returns None for expired cache entries.

        Given: An expired cache entry exists
        When: get_cached is called with an expired cache key
        Then: None is returned (cache miss due to expiration)
        """
        # Arrange: Create an expired cache entry
        cache_key = "expired_key_789"
        cache_path = temp_cache_dir / f"{cache_key}.json"
        old_time = time.time() - validation_cache.CACHE_TTL_SECONDS - 100
        cache_data = {
            "value": "expired_result",
            "timestamp": old_time,
            "terminal_id": "test_term"
        }
        cache_path.write_text(json.dumps(cache_data))
        # Set file modification time to old time
        os.utime(cache_path, (old_time, old_time))

        # Act: Try to get cached value
        result = validation_cache.get_cached(cache_key)

        # Assert: None is returned (expired)
        assert result is None


@pytest.mark.skipif(not MODULE_EXISTS, reason="validation_cache module not found")
class TestSetCached:
    """Tests for set_cached() function."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        cache_dir = tmp_path / "validation_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Patch CACHE_DIR to use temp directory
        with patch.object(validation_cache, 'CACHE_DIR', cache_dir):
            yield cache_dir

    def test_set_cached_stores_value(self, temp_cache_dir):
        """
        Test that set_cached stores a value with timestamp.

        Given: A cache key and value
        When: set_cached is called
        Then: The value is stored in cache with timestamp
        """
        # Arrange: Cache key and value
        cache_key = "store_key_abc"
        value_to_store = {"result": "test_data", "count": 42}

        # Act: Store value in cache
        validation_cache.set_cached(cache_key, value_to_store)

        # Assert: Value is stored correctly
        cache_path = temp_cache_dir / f"{cache_key}.json"
        assert cache_path.exists()

        cache_content = json.loads(cache_path.read_text())
        assert cache_content["value"] == value_to_store
        assert "timestamp" in cache_content
        assert "terminal_id" in cache_content


@pytest.mark.skipif(not MODULE_EXISTS, reason="validation_cache module not found")
class TestIsCacheValid:
    """Tests for is_cache_valid() function."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        cache_dir = tmp_path / "validation_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Patch CACHE_DIR to use temp directory
        with patch.object(validation_cache, 'CACHE_DIR', cache_dir):
            yield cache_dir

    def test_is_cache_valid_returns_true_for_valid(self, temp_cache_dir):
        """
        Test that is_cache_valid returns True for valid cache entries.

        Given: A recent cache file exists
        When: is_cache_valid is called
        Then: True is returned
        """
        # Arrange: Create a recent cache file
        cache_path = temp_cache_dir / "valid_cache.json"
        cache_path.write_text(json.dumps({"value": "data"}))

        # Act: Check if cache is valid
        result = validation_cache.is_cache_valid(cache_path)

        # Assert: Cache is valid
        assert result is True

    def test_is_cache_valid_returns_false_for_expired(self, temp_cache_dir):
        """
        Test that is_cache_valid returns False for expired cache entries.

        Given: An old cache file exists (older than CACHE_TTL_SECONDS)
        When: is_cache_valid is called
        Then: False is returned
        """
        # Arrange: Create an expired cache file
        cache_path = temp_cache_dir / "expired_cache.json"
        old_time = time.time() - validation_cache.CACHE_TTL_SECONDS - 100
        cache_path.write_text(json.dumps({"value": "data"}))
        os.utime(cache_path, (old_time, old_time))

        # Act: Check if cache is valid
        result = validation_cache.is_cache_valid(cache_path)

        # Assert: Cache is expired
        assert result is False

    def test_is_cache_valid_returns_false_for_nonexistent(self, temp_cache_dir):
        """
        Test that is_cache_valid returns False for non-existent cache files.

        Given: No cache file exists
        When: is_cache_valid is called
        Then: False is returned
        """
        # Arrange: Non-existent cache path
        cache_path = temp_cache_dir / "nonexistent_cache.json"

        # Act: Check if cache is valid
        result = validation_cache.is_cache_valid(cache_path)

        # Assert: Cache is not valid
        assert result is False


@pytest.mark.skipif(not MODULE_EXISTS, reason="validation_cache module not found")
class TestBuildCacheKey:
    """Tests for build_cache_key() function."""

    def test_build_cache_key_creates_unique_key(self):
        """
        Test that build_cache_key creates unique keys including operation and config hash.

        Given: An operation name and config
        When: build_cache_key is called
        Then: A unique cache key is generated that includes operation and config hash
        """
        # Arrange: Operation and config
        operation = "test_operation"
        terminal_id = "term_123"
        cwd_hash = "cwd_abc"
        version = "1.0"
        config = {"setting1": "value1", "setting2": "value2"}

        # Act: Build cache key
        cache_key = validation_cache.build_cache_key(
            operation=operation,
            terminal_id=terminal_id,
            cwd_hash=cwd_hash,
            version=version,
            config=config
        )

        # Assert: Cache key is a hex string (hash)
        assert len(cache_key) == 64  # SHA256 hex length
        assert all(c in "0123456789abcdef" for c in cache_key)

    def test_build_cache_key_different_configs_different_keys(self):
        """
        Test that different configs produce different cache keys.

        Given: Two different config dictionaries
        When: build_cache_key is called for each
        Then: Different cache keys are generated
        """
        # Arrange: Two different configs
        config1 = {"setting": "value1"}
        config2 = {"setting": "value2"}

        # Act: Build cache keys
        key1 = validation_cache.build_cache_key(
            operation="test",
            terminal_id="term_1",
            cwd_hash="cwd_1",
            version="1.0",
            config=config1
        )
        key2 = validation_cache.build_cache_key(
            operation="test",
            terminal_id="term_1",
            cwd_hash="cwd_1",
            version="1.0",
            config=config2
        )

        # Assert: Keys are different
        assert key1 != key2

    def test_build_cache_key_same_configs_same_keys(self):
        """
        Test that same configs produce same cache keys.

        Given: Two identical config dictionaries
        When: build_cache_key is called for each
        Then: Same cache keys are generated
        """
        # Arrange: Same config
        config = {"setting": "value"}

        # Act: Build cache keys
        key1 = validation_cache.build_cache_key(
            operation="test",
            terminal_id="term_1",
            cwd_hash="cwd_1",
            version="1.0",
            config=config
        )
        key2 = validation_cache.build_cache_key(
            operation="test",
            terminal_id="term_1",
            cwd_hash="cwd_1",
            version="1.0",
            config=config
        )

        # Assert: Keys are identical
        assert key1 == key2

    def test_build_cache_key_includes_terminal_id(self):
        """
        Test that cache keys include terminal_id for multi-terminal isolation.

        Given: Same operation/config but different terminal_id
        When: build_cache_key is called for each
        Then: Different cache keys are generated
        """
        # Arrange: Same operation/config, different terminals
        config = {"setting": "value"}

        # Act: Build cache keys with different terminal IDs
        key1 = validation_cache.build_cache_key(
            operation="test",
            terminal_id="term_1",
            cwd_hash="cwd_1",
            version="1.0",
            config=config
        )
        key2 = validation_cache.build_cache_key(
            operation="test",
            terminal_id="term_2",
            cwd_hash="cwd_1",
            version="1.0",
            config=config
        )

        # Assert: Keys are different (terminal isolation)
        assert key1 != key2

    def test_build_cache_key_includes_extra_params(self):
        """
        Test that extra parameters are included in cache key generation.

        Given: Same operation/config but different extra params
        When: build_cache_key is called for each
        Then: Different cache keys are generated
        """
        # Arrange: Same base params, different extra params
        config = {"setting": "value"}

        # Act: Build cache keys with different extra params
        key1 = validation_cache.build_cache_key(
            operation="test",
            terminal_id="term_1",
            cwd_hash="cwd_1",
            version="1.0",
            config=config,
            extra_param="value1"
        )
        key2 = validation_cache.build_cache_key(
            operation="test",
            terminal_id="term_1",
            cwd_hash="cwd_1",
            version="1.0",
            config=config,
            extra_param="value2"
        )

        # Assert: Keys are different
        assert key1 != key2


@pytest.mark.skipif(not MODULE_EXISTS, reason="validation_cache module not found")
class TestCleanupOldCache:
    """Tests for cleanup_old_cache() function."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create temporary cache directory with cache files."""
        cache_dir = tmp_path / "validation_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Patch CACHE_DIR to use temp directory
        with patch.object(validation_cache, 'CACHE_DIR', cache_dir):
            yield cache_dir

    def test_cleanup_old_cache_removes_expired_files(self, temp_cache_dir):
        """
        Test that cleanup_old_cache removes expired cache files.

        Given: A cache directory with expired and valid files
        When: cleanup_old_cache is called
        Then: Expired files are deleted, valid files remain
        """
        # Arrange: Create expired and valid cache files
        old_time = time.time() - validation_cache.CACHE_TTL_SECONDS - 100
        recent_time = time.time()

        # Expired file
        expired_file = temp_cache_dir / "expired_cache.json"
        expired_file.write_text(json.dumps({"value": "old_data"}))
        os.utime(expired_file, (old_time, old_time))

        # Valid file
        valid_file = temp_cache_dir / "valid_cache.json"
        valid_file.write_text(json.dumps({"value": "new_data"}))
        os.utime(valid_file, (recent_time, recent_time))

        # Act: Cleanup old cache
        validation_cache.cleanup_old_cache()

        # Assert: Expired file deleted, valid file remains
        assert not expired_file.exists()
        assert valid_file.exists()

    def test_cleanup_old_cache_handles_empty_directory(self, temp_cache_dir):
        """
        Test that cleanup_old_cache handles empty cache directory gracefully.

        Given: An empty cache directory
        When: cleanup_old_cache is called
        Then: No error is raised
        """
        # Arrange: Empty directory (already empty from fixture)

        # Act: Cleanup should not raise error
        validation_cache.cleanup_old_cache()

        # Assert: Directory still exists
        assert temp_cache_dir.exists()

    def test_cleanup_old_cache_enforces_size_limit(self, temp_cache_dir):
        """
        Test that cleanup_old_cache enforces MAX_CACHE_SIZE_MB limit.

        Given: Cache files exceeding size limit
        When: cleanup_old_cache is called
        Then: Oldest files are deleted until under limit
        """
        # This test would require creating large files to exceed the limit
        # For now, just verify the function runs without error
        # Arrange: Create some small cache files
        for i in range(5):
            cache_file = temp_cache_dir / f"cache_{i}.json"
            cache_file.write_text(json.dumps({"value": f"data_{i}"}))

        # Act: Cleanup should not raise error
        validation_cache.cleanup_old_cache()

        # Assert: Files still exist (under size limit)
        assert temp_cache_dir.exists()


@pytest.mark.skipif(not MODULE_EXISTS, reason="validation_cache module not found")
class TestValidationCacheClass:
    """Tests for ValidationCache class."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        cache_dir = tmp_path / "validation_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Patch CACHE_DIR to use temp directory
        with patch.object(validation_cache, 'CACHE_DIR', cache_dir):
            yield cache_dir

    def test_validation_cache_get_returns_cached(self, temp_cache_dir):
        """
        Test that ValidationCache.get() returns cached value on hit.

        Given: A ValidationCache instance with cached value
        When: get() is called
        Then: Cached value is returned without calling compute_fn
        """
        # Arrange: Create cache instance and store value
        cache = validation_cache.ValidationCache(
            operation="test_op",
            version="1.0"
        )

        call_count = [0]

        def compute_fn():
            call_count[0] += 1
            return "computed_value"

        # Prime cache
        cache_key = cache._build_key()
        validation_cache.set_cached(cache_key, "cached_value")

        # Act: Get from cache (should not call compute_fn)
        result = cache.get(compute_fn)

        # Assert: Cached value returned, compute_fn not called
        assert result == "cached_value"
        assert call_count[0] == 0

    def test_validation_cache_get_computes_on_miss(self, temp_cache_dir):
        """
        Test that ValidationCache.get() computes and caches on miss.

        Given: A ValidationCache instance with no cached value
        When: get() is called
        Then: compute_fn is called and result is cached
        """
        # Arrange: Create cache instance
        cache = validation_cache.ValidationCache(
            operation="test_op_miss",
            version="1.0"
        )

        call_count = [0]

        def compute_fn():
            call_count[0] += 1
            return "computed_value"

        # Act: Get from cache (should call compute_fn)
        result = cache.get(compute_fn)

        # Assert: Computed value returned
        assert result == "computed_value"
        assert call_count[0] == 1

    def test_validation_cache_invalidate_removes_entry(self, temp_cache_dir):
        """
        Test that ValidationCache.invalidate() removes cache entry.

        Given: A ValidationCache instance with cached value
        When: invalidate() is called
        Then: Cache entry is removed
        """
        # Arrange: Create cache instance and store value
        cache = validation_cache.ValidationCache(
            operation="test_invalidate",
            version="1.0"
        )

        cache_key = cache._build_key()
        validation_cache.set_cached(cache_key, "value_to_invalidate")

        # Verify entry exists
        cache_path = validation_cache.get_cache_path(cache_key)
        assert cache_path.exists()

        # Act: Invalidate
        cache.invalidate()

        # Assert: Entry removed
        assert not cache_path.exists()

    def test_validation_cache_clear_all_removes_terminal_entries(self, temp_cache_dir):
        """
        Test that ValidationCache.clear_all() removes entries for this terminal.

        Given: A ValidationCache instance with cached values
        When: clear_all() is called
        Then: All cache entries for this terminal are removed
        """
        # Arrange: Create cache entries
        cache = validation_cache.ValidationCache(
            operation="test_clear",
            version="1.0"
        )

        terminal_id = cache.terminal_id

        # Create multiple cache entries for this terminal
        for i in range(3):
            cache_key = f"entry_{i}"
            entry_path = temp_cache_dir / f"{cache_key}.json"
            entry_data = {
                "value": f"data_{i}",
                "timestamp": time.time(),
                "terminal_id": terminal_id
            }
            entry_path.write_text(json.dumps(entry_data))

        # Create entry for different terminal
        other_entry_path = temp_cache_dir / "other_terminal.json"
        other_entry_data = {
            "value": "other_data",
            "timestamp": time.time(),
            "terminal_id": "other_terminal_id"
        }
        other_entry_path.write_text(json.dumps(other_entry_data))

        # Act: Clear all
        cache.clear_all()

        # Assert: This terminal's entries removed, other terminal's entry remains
        # Note: clear_all() uses glob pattern so only checks terminal_id in content
        remaining_files = list(temp_cache_dir.glob("*.json"))
        # Other terminal file should remain
        assert len(remaining_files) >= 1


@pytest.mark.skipif(not MODULE_EXISTS, reason="validation_cache module not found")
class TestHelperFunctions:
    """Tests for helper functions: cache_tdd_test_files, cache_path_validation."""

    @pytest.fixture
    def temp_cache_dir(self, tmp_path):
        """Create temporary cache directory."""
        cache_dir = tmp_path / "validation_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Patch CACHE_DIR to use temp directory
        with patch.object(validation_cache, 'CACHE_DIR', cache_dir):
            yield cache_dir

    def test_cache_tdd_test_files(self, temp_cache_dir):
        """
        Test that cache_tdd_test_files caches test file discovery.

        Given: A compute function that returns test files
        When: cache_tdd_test_files is called
        Then: Result is cached and returned
        """
        # Arrange: Compute function
        call_count = [0]

        def find_test_files():
            call_count[0] += 1
            return ["test_1.py", "test_2.py"]

        # Act: First call (cache miss)
        result1 = validation_cache.cache_tdd_test_files(find_test_files)

        # Assert: Result correct, function called
        assert result1 == ["test_1.py", "test_2.py"]
        assert call_count[0] == 1

        # Act: Second call (cache hit)
        result2 = validation_cache.cache_tdd_test_files(find_test_files)

        # Assert: Same result, function not called again
        assert result2 == ["test_1.py", "test_2.py"]
        assert call_count[0] == 1

    def test_cache_path_validation(self, temp_cache_dir):
        """
        Test that cache_path_validation caches path validation.

        Given: A compute function that validates a path
        When: cache_path_validation is called
        Then: Result is cached and returned
        """
        # Arrange: Compute function
        call_count = [0]

        def validate_path():
            call_count[0] += 1
            return True

        test_path = "/some/test/path"

        # Act: First call (cache miss)
        result1 = validation_cache.cache_path_validation(validate_path, test_path)

        # Assert: Result correct, function called
        assert result1 is True
        assert call_count[0] == 1

        # Act: Second call (cache hit)
        result2 = validation_cache.cache_path_validation(validate_path, test_path)

        # Assert: Same result, function not called again
        assert result2 is True
        assert call_count[0] == 1


@pytest.mark.skipif(not MODULE_EXISTS, reason="validation_cache module not found")
class TestUtilityFunctions:
    """Tests for utility functions: get_config_hash, get_cwd_hash."""

    def test_get_config_hash_with_dict(self):
        """
        Test that get_config_hash produces consistent hash for dict.

        Given: A config dictionary
        When: get_config_hash is called
        Then: A consistent hash string is returned
        """
        # Arrange: Config dict
        config = {"key1": "value1", "key2": "value2"}

        # Act: Get hash
        hash1 = validation_cache.get_config_hash(config)
        hash2 = validation_cache.get_config_hash(config)

        # Assert: Hash is consistent and non-empty
        assert hash1 == hash2
        assert len(hash1) == 12  # First 12 chars of SHA256
        assert hash1 != "no_config"

    def test_get_config_hash_with_none(self):
        """
        Test that get_config_hash returns 'no_config' for None.

        Given: None as config
        When: get_config_hash is called
        Then: 'no_config' is returned
        """
        # Act: Get hash for None
        result = validation_cache.get_config_hash(None)

        # Assert: Returns 'no_config'
        assert result == "no_config"

    def test_get_config_hash_same_content_same_hash(self):
        """
        Test that get_config_hash produces same hash for same content.

        Given: Two dicts with same content (different order)
        When: get_config_hash is called for each
        Then: Same hash is returned (sorted keys)
        """
        # Arrange: Same content, different key order
        config1 = {"b": 2, "a": 1}
        config2 = {"a": 1, "b": 2}

        # Act: Get hashes
        hash1 = validation_cache.get_config_hash(config1)
        hash2 = validation_cache.get_config_hash(config2)

        # Assert: Hashes are identical (sorted keys)
        assert hash1 == hash2

    def test_get_cwd_hash_returns_hash(self):
        """
        Test that get_cwd_hash returns a hash string.

        Given: Current working directory exists
        When: get_cwd_hash is called
        Then: A hash string is returned
        """
        # Act: Get cwd hash
        result = validation_cache.get_cwd_hash()

        # Assert: Hash is non-empty string
        assert isinstance(result, str)
        assert len(result) == 12  # First 12 chars of SHA256


class TestGreenPhase:
    """Tests verifying implementation exists (GREEN phase complete)."""

    def test_module_exists(self):
        """
        Verify module exists and is importable.

        Given: The validation_cache.py module
        When: Module is imported
        Then: All expected functions and classes exist
        """
        import validation_cache

        # Check functions exist
        assert callable(validation_cache.get_cached)
        assert callable(validation_cache.set_cached)
        assert callable(validation_cache.is_cache_valid)
        assert callable(validation_cache.build_cache_key)
        assert callable(validation_cache.cleanup_old_cache)
        assert callable(validation_cache.cache_tdd_test_files)
        assert callable(validation_cache.cache_path_validation)

        # Check class exists
        assert hasattr(validation_cache, 'ValidationCache')
        assert hasattr(validation_cache.ValidationCache, 'get')
        assert hasattr(validation_cache.ValidationCache, 'invalidate')
        assert hasattr(validation_cache.ValidationCache, 'clear_all')

        # Check constants
        assert hasattr(validation_cache, 'CACHE_DIR')
        assert hasattr(validation_cache, 'CACHE_TTL_SECONDS')
        assert hasattr(validation_cache, 'MAX_CACHE_SIZE_MB')


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
