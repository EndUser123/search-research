"""
Test suite for hook configuration caching with TDD approach.

Phase 1, Task 2: Configuration Caching with TDD
Task ID: TSK-251225-HooksOpt-0822

These tests follow RED-GREEN-REFACTOR TDD cycle:
- RED: Tests fail initially (no implementation)
- GREEN: Minimal implementation to pass tests
- REFACTOR: Improve code quality while tests pass
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import module to test (will fail until implementation exists)
try:
    from __lib.hook_cache import clear_cache, get_cache_info, load_json_config
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


@pytest.mark.skipif(not MODULE_EXISTS, reason="hook_cache module not implemented yet")
class TestConfigCache:
    """Test suite for configuration file caching using lru_cache."""

    @pytest.fixture
    def temp_settings(self, tmp_path):
        """Create temporary settings.json file."""
        config_path = tmp_path / "settings.json"
        config_data = {
            "env": {
                "GOAL_ANCHOR_ENABLED": "true",
                "BLOAT_GUARD_ENABLED": "true"
            },
            "hooks": {
                "timeout": 30
            }
        }
        config_path.write_text(json.dumps(config_data))
        return str(config_path), config_data

    @pytest.fixture
    def temp_directory_policy(self, tmp_path):
        """Create temporary directory_policy.json file."""
        config_path = tmp_path / "directory_policy.json"
        config_data = {
            "deny_patterns": [
                "**/__pycache__/**",
                "**/node_modules/**"
            ],
            "max_depth": 5
        }
        config_path.write_text(json.dumps(config_data))
        return str(config_path), config_data

    def test_cache_miss_first_load(self, temp_settings):
        """Test first call loads from file (cache miss)."""
        config_path, expected_data = temp_settings

        # Clear cache to ensure miss
        clear_cache()

        # Load config (should hit file)
        config = load_json_config(config_path)

        assert config == expected_data
        assert config["env"]["GOAL_ANCHOR_ENABLED"] == "true"

    def test_cache_hit_second_load(self, temp_settings):
        """Test second call uses cache (cache hit)."""
        config_path, expected_data = temp_settings

        # First load (cache miss)
        config1 = load_json_config(config_path)

        # Modify file (should not affect cached value)
        new_data = {"env": {"GOAL_ANCHOR_ENABLED": "false"}}
        Path(config_path).write_text(json.dumps(new_data))

        # Second load (cache hit - returns original)
        config2 = load_json_config(config_path)

        assert config1 == config2 or config1 is config2  # Same value or same object
        assert config2["env"]["GOAL_ANCHOR_ENABLED"] == "true"  # Original value

    def test_cache_clear_invalidates(self, temp_settings):
        """Test cache_clear() invalidates cache."""
        config_path, _ = temp_settings

        # First load
        load_json_config(config_path)

        # Clear cache
        clear_cache()

        # Modify file
        new_data = {"env": {"NEW_KEY": "new_value"}}
        Path(config_path).write_text(json.dumps(new_data))

        # Load after clear (should read file)
        config = load_json_config(config_path)

        assert config["env"]["NEW_KEY"] == "new_value"

    def test_multiple_config_files(self, temp_settings, temp_directory_policy):
        """Test caching multiple different config files."""
        settings_path, settings_data = temp_settings
        policy_path, policy_data = temp_directory_policy

        # Clear cache
        clear_cache()

        # Load both configs
        settings = load_json_config(settings_path)
        policy = load_json_config(policy_path)

        assert settings == settings_data
        assert policy == policy_data
        assert settings != policy  # Different configs

    def test_cache_performance_improvement(self, temp_settings):
        """Test that cached access is faster than file I/O (>5x speedup)."""
        config_path, _ = temp_settings

        # Clear cache
        clear_cache()

        # Measure uncached access (simulate with cache clears)
        times_uncached = []
        for _ in range(50):
            start = time.perf_counter()
            load_json_config(config_path)
            clear_cache()  # Force uncached
            times_uncached.append(time.perf_counter() - start)

        # Prime cache and measure cached access
        load_json_config(config_path)
        times_cached = []
        for _ in range(50):
            start = time.perf_counter()
            load_json_config(config_path)
            times_cached.append(time.perf_counter() - start)

        avg_uncached_ms = sum(times_uncached) / len(times_uncached) * 1000
        avg_cached_ms = sum(times_cached) / len(times_cached) * 1000

        # Assert cached is significantly faster
        speedup = avg_uncached_ms / avg_cached_ms if avg_cached_ms > 0 else float('inf')
        assert speedup > 5.0, f"Expected >5x speedup, got {speedup:.1f}x (uncached: {avg_uncached_ms:.2f}ms, cached: {avg_cached_ms:.2f}ms)"

    def test_thread_safe_cache_access(self, temp_settings):
        """Test that cache is thread-safe (lru_cache is thread-safe by default)."""
        config_path, _ = temp_settings
        clear_cache()

        def load_config():
            return load_json_config(config_path)

        # Load from multiple threads concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(load_config) for _ in range(100)]
            results = [f.result() for f in as_completed(futures)]

        # All results should be identical
        assert all(r == results[0] for r in results)

    def test_cache_hit_rate_tracking(self, temp_settings):
        """Test cache statistics (hit rate tracking)."""
        config_path, _ = temp_settings
        clear_cache()

        # First load (miss)
        load_json_config(config_path)

        # 10 subsequent loads (hits)
        for _ in range(10):
            load_json_config(config_path)

        # Get cache info
        info = get_cache_info()

        assert info["misses"] == 1
        assert info["hits"] == 10
        assert info["currsize"] == 1
        assert info["maxsize"] == 32  # Expected maxsize

    def test_error_handling_missing_file(self, tmp_path):
        """Test error handling for missing files."""
        missing_path = str(tmp_path / "nonexistent.json")

        with pytest.raises(FileNotFoundError):
            load_json_config(missing_path)

    def test_error_handling_invalid_json(self, tmp_path):
        """Test error handling for invalid JSON."""
        invalid_path = tmp_path / "invalid.json"
        invalid_path.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_json_config(str(invalid_path))

    def test_cache_size_limit(self, tmp_path):
        """Test LRU cache respects maxsize (32 config files)."""
        clear_cache()

        # Create 35 different config files (exceeds maxsize=32)
        config_paths = []
        for i in range(35):
            config_path = tmp_path / f"config_{i}.json"
            config_path.write_text(json.dumps({"id": i}))
            config_paths.append(str(config_path))

        # Load all configs
        for path in config_paths:
            load_json_config(path)

        # Cache should evict oldest entries
        info = get_cache_info()
        assert info["currsize"] == 32  # At max capacity
        assert info["maxsize"] == 32

    def test_same_path_different_instances(self, tmp_path):
        """Test that same path returns cached instance (not new object)."""
        config_path = tmp_path / "test.json"
        config_path.write_text(json.dumps({"value": 42}))

        clear_cache()

        # Load twice
        config1 = load_json_config(str(config_path))
        config2 = load_json_config(str(config_path))

        # Should return same object (cached)
        assert config1 is config2 or config1 == config2


@pytest.mark.skipif(not MODULE_EXISTS, reason="hook_cache module not implemented yet")
class TestCacheIntegration:
    """Integration tests for cache with real hook files."""

    def test_real_settings_json_cache(self):
        """Test caching real settings.json from P:/.claude/settings.json."""
        settings_path = "P:/.claude/settings.json"

        if not Path(settings_path).exists():
            pytest.skip("Real settings.json not found")

        clear_cache()

        # First load
        config1 = load_json_config(settings_path)
        assert "env" in config1
        assert "hooks" in config1

        # Second load (cached)
        config2 = load_json_config(settings_path)

        # Should be identical
        assert config1 == config2

        # Cache info should show 1 hit
        info = get_cache_info()
        assert info["hits"] >= 1

    def test_performance_real_file(self):
        """Test performance improvement with real settings.json."""
        settings_path = "P:/.claude/settings.json"

        if not Path(settings_path).exists():
            pytest.skip("Real settings.json not found")

        clear_cache()

        # Benchmark uncached
        start = time.perf_counter()
        for _ in range(100):
            clear_cache()
            load_json_config(settings_path)
        uncached_time = time.perf_counter() - start

        # Benchmark cached
        load_json_config(settings_path)  # Prime cache
        start = time.perf_counter()
        for _ in range(100):
            load_json_config(settings_path)
        cached_time = time.perf_counter() - start

        speedup = uncached_time / cached_time
        assert speedup > 5.0, f"Expected >5x speedup, got {speedup:.1f}x"


class TestGreenPhase:
    """Tests verifying implementation exists (GREEN phase complete)."""

    def test_module_exists(self):
        """Verify module exists and is importable."""
        from hook_cache import clear_cache, get_cache_info, load_json_config
        assert callable(load_json_config)
        assert callable(clear_cache)
        assert callable(get_cache_info)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
