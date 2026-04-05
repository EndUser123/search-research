"""Tests for Windows file lock behavior.

Run with: pytest tests/test_windows_file_lock.py -v

Purpose: Test that FileLock.acquire() actually locks on Windows (fixes P1-5)
Issue: P1-5 - Windows file lock not implemented
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from yt_fts.db.infra import FileLock


class TestWindowsFileLock:
    """Tests for FileLock behavior on Windows platform."""

    @pytest.fixture
    def temp_lockfile(self):
        """Create a temporary lock file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".lock") as f:
            return f.name

    def test_windows_acquire_creates_lockfd(self, temp_lockfile):
        """
        Test that on Windows, acquire() creates actual file descriptor.

        DESIRED BEHAVIOR:
        - Uses os.open() to get file descriptor
        - Calls msvcrt.locking() with LK_NBLCK
        - Sets self.lockfd to the file descriptor (not None)
        """
        with patch("sys.platform", "win32"):
            lock = FileLock(temp_lockfile)
            result = lock.acquire()

            # Should return True on success
            assert result is True

            # Should have a real file descriptor (not None)
            assert lock.lockfd is not None

            # Should be an integer (file descriptor on Windows)
            assert isinstance(lock.lockfd, int)

            # Cleanup
            lock.release()

    def test_windows_acquire_fails_on_conflict(self, temp_lockfile):
        """
        Test that on Windows, second acquire() fails when lock is held.

        DESIRED BEHAVIOR:
        - First lock acquires successfully
        - Second lock fails (returns False) or times out
        - Actual exclusivity is enforced
        """
        # Skip on CI/mock environments where msvcrt might not work properly
        # This test would need real multi-process testing for full validation
        if not sys.platform == "win32":
            pytest.skip("Real Windows file lock only testable on Windows")

        lock1 = FileLock(temp_lockfile, timeout=0.5)
        lock2 = FileLock(temp_lockfile, timeout=0.5)

        # First should acquire
        assert lock1.acquire() is True
        assert lock1.lockfd is not None

        # Second should fail (timeout)
        assert lock2.acquire() is False

        # Cleanup
        lock1.release()

    def test_windows_release_clears_lockfd(self, temp_lockfile):
        """
        Test that on Windows, release() clears the lock.

        DESIRED BEHAVIOR:
        - Calls msvcrt.locking() with LK_UNLCK
        - Closes file descriptor with os.close()
        - Sets self.lockfd to None
        """
        with patch("sys.platform", "win32"):
            lock = FileLock(temp_lockfile)
            lock.acquire()
            original_fd = lock.lockfd

            # Should have a lockfd
            assert original_fd is not None

            lock.release()

            # lockfd should be None after release
            assert lock.lockfd is None

    def test_windows_context_manager_works(self, temp_lockfile):
        """
        Test that context manager works on Windows.

        DESIRED BEHAVIOR:
        - __enter__ acquires the lock
        - __exit__ releases the lock
        - lockfd is set inside context, None outside
        """
        with patch("sys.platform", "win32"):
            with FileLock(temp_lockfile) as lock:
                # Should have lockfd inside context
                assert lock.lockfd is not None
                assert isinstance(lock.lockfd, int)

            # lockfd should be None after context exits
            assert lock.lockfd is None

    def test_unix_behavior_still_works(self, temp_lockfile):
        """
        Test that Unix behavior is not broken.

        This test ensures Windows implementation didn't break Unix.
        """
        # Skip if actually on Windows (fcntl not available)
        if sys.platform == "win32":
            pytest.skip("fcntl not available on Windows for this test")

        lock = FileLock(temp_lockfile)
        result = lock.acquire()

        # Unix returns True AND has actual lockfd
        assert result is True
        assert lock.lockfd is not None

        # Cleanup
        lock.release()
