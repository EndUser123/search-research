"""
Test suite for SessionFileCache class with TDD approach.

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
from typing import Any

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import module to test (will fail until implementation exists)
try:
    from session_file_cache import SessionFileCache
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


@pytest.mark.skipif(not MODULE_EXISTS, reason="session_file_cache module not implemented yet")
class TestSessionFileCache:
    """Test suite for SessionFileCache class."""

    @pytest.fixture
    def temp_json_file(self, tmp_path: Path) -> tuple[Path, dict[str, Any]]:
        """Create temporary JSON file for testing."""
        file_path = tmp_path / "test.json"
        data = {"key": "value", "number": 42, "nested": {"a": 1}}
        file_path.write_text(json.dumps(data))
        return file_path, data

    @pytest.fixture
    def cache(self) -> SessionFileCache:
        """Create fresh cache instance for each test."""
        return SessionFileCache()

    def test_cache_miss_first_load(self, cache: SessionFileCache, temp_json_file: tuple[Path, dict[str, Any]]) -> None:
        """Test first call loads from file (cache miss)."""
        file_path, expected_data = temp_json_file

        result = cache.get(file_path)

        assert result == expected_data
        assert result["key"] == "value"

    def test_cache_hit_second_load(self, cache: SessionFileCache, temp_json_file: tuple[Path, dict[str, Any]]) -> None:
        """Test second call uses cache (cache hit)."""
        file_path, expected_data = temp_json_file

        # First load (cache miss)
        result1 = cache.get(file_path)

        # Second load WITHOUT modifying file (cache hit)
        result2 = cache.get(file_path)

        assert result1 == result2
        assert result2["key"] == "value"  # Original value

    def test_cache_expiration(self, cache: SessionFileCache, temp_json_file: tuple[Path, dict[str, Any]]) -> None:
        """Test cache expires after TTL."""
        file_path, _ = temp_json_file

        # Set very short TTL
        cache.set_ttl(0)  # Immediate expiration

        # First load
        result1 = cache.get(file_path)

        # Modify file
        new_data = {"modified": True}
        Path(file_path).write_text(json.dumps(new_data))

        # Second load (should read file due to expiration)
        result2 = cache.get(file_path)

        assert result2 == new_data
        assert result2.get("modified") is True

    def test_file_modification_invalidation(self, cache: SessionFileCache, temp_json_file: tuple[Path, dict[str, Any]]) -> None:
        """Test cache invalidates when file mtime changes."""
        file_path, _ = temp_json_file

        # First load
        result1 = cache.get(file_path)

        # Wait to ensure different mtime
        time.sleep(0.01)

        # Modify file
        new_data = {"key": "new_value"}
        Path(file_path).write_text(json.dumps(new_data))

        # Set TTL to very high to ensure mtime check is tested
        cache.set_ttl(3600)

        # Force mtime mismatch by getting fresh mtime
        # This tests that mtime comparison works
        result2 = cache.get(file_path)

        # Should reflect file modification
        assert result2["key"] == "new_value"

    def test_clear_specific_file(self, cache, temp_json_file):
        """Test clear() for specific file."""
        file_path, _ = temp_json_file

        # Load into cache
        cache.get(file_path)

        # Clear specific file
        cache.clear(file_path)

        # Modify file
        new_data = {"cleared": True}
        Path(file_path).write_text(json.dumps(new_data))

        # Should read new data
        result = cache.get(file_path)
        assert result == new_data

    def test_clear_all_files(self, cache, temp_json_file, tmp_path):
        """Test clear() without argument clears all cache."""
        file_path1, _ = temp_json_file

        # Create second file
        file_path2 = tmp_path / "test2.json"
        data2 = {"key2": "value2"}
        file_path2.write_text(json.dumps(data2))

        # Load both files
        cache.get(file_path1)
        cache.get(file_path2)

        # Clear all
        cache.clear()

        # Modify files
        new_data1 = {"new1": True}
        new_data2 = {"new2": True}
        Path(file_path1).write_text(json.dumps(new_data1))
        Path(file_path2).write_text(json.dumps(new_data2))

        # Should read new data
        assert cache.get(file_path1) == new_data1
        assert cache.get(file_path2) == new_data2

    def test_set_and_get_ttl(self, cache):
        """Test set_ttl() and get_ttl()."""
        assert cache.get_ttl() == 60  # Default

        cache.set_ttl(120)
        assert cache.get_ttl() == 120

        cache.set_ttl(0)
        assert cache.get_ttl() == 0

    def test_missing_file_returns_default(self, cache, tmp_path):
        """Test get() returns default for missing files."""
        missing_file = tmp_path / "nonexistent.json"

        result = cache.get(missing_file)

        assert result is None

        result_with_default = cache.get(missing_file, default={"default": True})
        assert result_with_default == {"default": True}

    def test_invalid_json_returns_default(self, cache, tmp_path):
        """Test get() returns default for invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ not valid json }")

        result = cache.get(invalid_file)

        assert result is None

        result_with_default = cache.get(invalid_file, default={})
        assert result_with_default == {}

    def test_thread_safe_cache_access(self, cache, temp_json_file):
        """Test that cache is thread-safe."""
        file_path, _ = temp_json_file

        def read_cache():
            return cache.get(file_path)

        # Read from multiple threads concurrently
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(read_cache) for _ in range(100)]
            results = [f.result() for f in as_completed(futures)]

        # All results should be identical
        assert all(r == results[0] for r in results)

    def test_multiple_files_cached_separately(self, cache, tmp_path):
        """Test caching multiple different files."""
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"

        data1 = {"id": 1, "name": "first"}
        data2 = {"id": 2, "name": "second"}

        file1.write_text(json.dumps(data1))
        file2.write_text(json.dumps(data2))

        result1 = cache.get(file1)
        result2 = cache.get(file2)

        assert result1 == data1
        assert result2 == data2
        assert result1 != result2

    def test_path_object_support(self, cache, tmp_path):
        """Test get() accepts Path objects."""
        file_path = tmp_path / "test.json"
        data = {"path": "object"}
        file_path.write_text(json.dumps(data))

        result = cache.get(file_path)

        assert result == data

    def test_string_path_support(self, cache, tmp_path):
        """Test get() accepts string paths."""
        file_path = tmp_path / "test.json"
        data = {"path": "string"}
        file_path.write_text(json.dumps(data))

        result = cache.get(str(file_path))

        assert result == data


class TestGreenPhase:
    """Tests verifying implementation exists (GREEN phase complete)."""

    def test_module_exists(self):
        """Verify module exists and is importable."""
        from session_file_cache import SessionFileCache
        assert SessionFileCache is not None

    def test_class_has_required_attributes(self):
        """Verify class has required attributes."""
        cache = SessionFileCache()
        assert hasattr(cache, '_cache')
        assert hasattr(cache, '_mtimes')
        assert hasattr(cache, '_timestamps')
        assert hasattr(cache, '_ttl')
        assert hasattr(cache, '_lock')

    def test_class_has_required_methods(self):
        """Verify class has required methods."""
        cache = SessionFileCache()
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'clear')
        assert hasattr(cache, 'set_ttl')
        assert hasattr(cache, 'get_ttl')
        assert callable(cache.get)
        assert callable(cache.clear)
        assert callable(cache.set_ttl)
        assert callable(cache.get_ttl)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
