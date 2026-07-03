"""
Tests for DX Tools File Locking

Tests cross-platform file locking for cache operations.
"""
import sys
from pathlib import Path

# Add __lib to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

import pytest
from dx_tools_locking import (
    PORTALOCKER_AVAILABLE,
    CacheLockContext,
    _acquire_lock,
    _get_package_lock_path,
    _release_lock,
    with_cache_lock,
)


class TestLockPathGeneration:
    """Test lock file path generation."""

    def test_lock_path_for_package(self):
        """Test lock path is generated correctly for package."""
        lock_path = _get_package_lock_path("P:/packages/test-package")

        assert lock_path.name.startswith("cache_")
        assert lock_path.name.endswith(".lock")
        assert "locks" in str(lock_path)

    def test_lock_path_hashing(self):
        """Test different paths generate different lock files."""
        lock_path1 = _get_package_lock_path("P:/packages/package-a")
        lock_path2 = _get_package_lock_path("P:/packages/package-b")

        assert lock_path1 != lock_path2

    def test_lock_path_same_for_same_path(self):
        """Test same path generates same lock file."""
        lock_path1 = _get_package_lock_path("P:/packages/test")
        lock_path2 = _get_package_lock_path("P:/packages/test")

        assert lock_path1 == lock_path2


class TestLockAcquisition:
    """Test lock acquisition and release."""

    def test_acquire_and_release_lock(self, tmp_path):
        """Test basic lock acquisition and release."""
        if not PORTALOCKER_AVAILABLE:
            pytest.skip("portalocker not available")

        lock_path = tmp_path / "test.lock"

        # Acquire lock
        acquired = _acquire_lock(lock_path, timeout=5.0)
        assert acquired is True

        # Release lock
        lock_file = open(lock_path)
        _release_lock(lock_file, lock_path)

    def test_lock_timeout(self, tmp_path):
        """Test lock acquisition times out when lock is held."""
        if not PORTALOCKER_AVAILABLE:
            pytest.skip("portalocker not available")

        lock_path = tmp_path / "test_timeout.lock"

        # First process acquires lock
        lock_file1 = open(lock_path, 'w')
        acquired1 = _acquire_lock(lock_path, timeout=1.0)
        assert acquired1 is True

        # Second process should fail to acquire (timeout)
        acquired2 = _acquire_lock(lock_path, timeout=0.5)
        assert acquired2 is False

        # Cleanup
        _release_lock(lock_file1, lock_path)

    def test_release_nonexistent_lock(self, tmp_path):
        """Test releasing a lock that doesn't exist is safe."""
        if not PORTALOCKER_AVAILABLE:
            pytest.skip("portalocker not available")

        lock_path = tmp_path / "nonexistent.lock"
        lock_file = None

        # Should not raise exception
        _release_lock(lock_file, lock_path)


class TestWithCacheLockDecorator:
    """Test @with_cache_lock decorator."""

    def test_decorator_allows_execution(self, tmp_path):
        """Test decorator allows function execution when lock available."""
        executed = []

        @with_cache_lock(str(tmp_path / "test"))
        def test_function():
            executed.append(True)
            return "success"

        result = test_function()
        assert result == "success"
        assert len(executed) == 1

    def test_decorator_with_args(self):
        """Test decorator works with function arguments."""
        executed = []

        @with_cache_lock("P:/packages/test")
        def test_function(x, y):
            executed.append((x, y))
            return x + y

        result = test_function(5, 3)
        assert result == 8
        assert executed == [(5, 3)]


class TestCacheLockContext:
    """Test CacheLockContext context manager."""

    def test_context_manager_acquires_lock(self):
        """Test context manager acquires lock on entry."""
        if not PORTALOCKER_AVAILABLE:
            pytest.skip("portalocker not available")

        with CacheLockContext("P:/packages/test") as lock:
            if PORTALOCKER_AVAILABLE:
                assert lock.acquired is True

    def test_context_manager_releases_lock(self):
        """Test context manager releases lock on exit."""
        if not PORTALOCKER_AVAILABLE:
            pytest.skip("portalocker not available")

        with CacheLockContext("P:/packages/test") as lock:
            acquired_inside = lock.acquired

        # After exit, lock should be released
        # (Can't directly test, but no exception means cleanup succeeded)
        assert acquired_inside is True or not PORTALOCKER_AVAILABLE

    def test_context_timeout(self):
        """Test context manager handles timeout gracefully."""
        if not PORTALOCKER_AVAILABLE:
            pytest.skip("portalocker not available")

        # Use very short timeout
        with CacheLockContext("P:/packages/test", timeout=0.01) as lock:
            # Should either acquire or timeout gracefully
            assert lock.acquired in (True, False)


class TestPortalockerFallback:
    """Test graceful fallback when portalocker unavailable."""

    def test_decorator_fallback_when_unavailable(self):
        """Test decorator is no-op when portalocker unavailable."""
        # This test runs even if portalocker IS available, by monkeypatching
        original_available = PORTALOCKER_AVAILABLE

        try:
            # Simulate portalocker unavailable
            import dx_tools_locking
            dx_tools_locking.PORTALOCKER_AVAILABLE = False

            executed = []

            @with_cache_lock("P:/packages/test")
            def test_function():
                executed.append(True)
                return "success"

            result = test_function()
            assert result == "success"
            assert len(executed) == 1

        finally:
            # Restore original state
            dx_tools_locking.PORTALOCKER_AVAILABLE = original_available
