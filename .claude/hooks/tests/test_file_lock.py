"""
Tests for FileLock cross-platform file locking using portalocker.

This test file verifies the FileLock behavior for preventing concurrent
access to shared resources. FileLock will be implemented in:
.claude/hooks/__lib/file_lock.py

Run with: pytest .claude/hooks/tests/test_file_lock.py -v
"""

import sys
import threading
import time
from pathlib import Path as PathLib

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(PathLib(__file__).parent.parent))

# The FileLock class doesn't exist yet - this will cause ModuleNotFoundError
try:
    from __lib.file_lock import FileLock
except (ImportError, ModuleNotFoundError):
    # FileLock doesn't exist yet - this is expected in RED phase
    FileLock = None


@pytest.mark.skipif(FileLock is None, reason="FileLock not implemented yet")
def test_lock_prevents_concurrent_access(tmp_path):
    """
    Test that FileLock prevents concurrent access and lost updates.

    This test verifies that when multiple threads try to increment a counter
    concurrently using FileLock, all updates are preserved (no race conditions).

    Given: A lock file and a counter file starting at 0
    When: 5 threads each increment the counter 100 times using FileLock
    Then: The final counter value must be exactly 500 (no lost updates)

    Without proper locking, this test would fail because the read-modify-write
    operations would interleave, causing lost updates.
    """
    lock_file = tmp_path / "test.lock"
    counter_file = tmp_path / "counter.txt"
    counter_file.write_text("0")

    def increment():
        for _ in range(100):
            with FileLock(lock_file):
                count = int(counter_file.read_text())
                time.sleep(0.001)  # Simulate work
                counter_file.write_text(str(count + 1))

    threads = [threading.Thread(target=increment) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Without locking, this would be much less than 500 due to lost updates
    assert int(counter_file.read_text()) == 500


def test_file_lock_module_import():
    """
    Characterization test: Verify FileLock module can be imported.

    This test is expected to FAIL in the RED phase because:
    1. The file_lock.py module doesn't exist yet, OR
    2. The FileLock class hasn't been implemented yet

    Once FileLock is implemented, this test should pass.
    """
    from __lib.file_lock import FileLock

    # If we get here, the import succeeded
    assert FileLock is not None


def test_lock_timeout(tmp_path):
    """
    Test that FileLock times out if held too long by another process.

    This test verifies that when a lock is held by the main thread,
    attempting to acquire the same lock in another thread with a short
    timeout results in a TimeoutError.

    Given: A FileLock is held by the main thread with a long timeout
    When: Another thread tries to acquire the same lock with a short timeout
    Then: The second thread should receive a TimeoutError

    This test will FAIL because FileLock class does not exist yet.
    """
    import concurrent.futures

    from __lib.file_lock import FileLock

    lock_file = tmp_path / "test.lock"

    # Hold lock in main thread with 10 second timeout
    with FileLock(lock_file, timeout=10):
        # Try to acquire in another thread with 100ms timeout
        def try_lock():
            try:
                with FileLock(lock_file, timeout=0.1):
                    pass
                return "acquired"
            except TimeoutError:
                return "timeout"

        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = executor.submit(try_lock).result()

        # The lock should NOT be acquired (should timeout)
        assert result == "timeout"
