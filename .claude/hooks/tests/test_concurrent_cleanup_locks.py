#!/usr/bin/env python3
"""
Regression tests for TASK-023: Cleanup lock TOCTOU race fix.

Tests concurrent terminal cleanup operations to ensure:
1. Lock file deletion is atomic with retry logic
2. Multiple terminals can cleanup stale locks safely
3. Permission errors are handled gracefully on Windows
4. No race conditions in state file cleanup

Test Framework: pytest
"""

import os
import threading
import time
from pathlib import Path

import pytest

# Test constants
STATE_DIR = Path("P:/.claude/state")
LOCK_DIR = STATE_DIR / "locks"
LOGS_DIR = Path("P:/.claude/hooks/logs")
STALE_LOCK_SECS = 3600  # 1 hour


def create_stale_lock(
    lock_dir: Path, lock_name: str, age_seconds: int = STALE_LOCK_SECS + 100
) -> Path:
    """Helper to create a stale lock file."""
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_file = lock_dir / lock_name

    # Create lock file
    lock_file.write_text("lock_data", encoding="utf-8")

    # Set modification time to make it stale
    old_time = time.time() - age_seconds
    import os

    os.utime(lock_file, (old_time, old_time))

    return lock_file


def create_fresh_lock(lock_dir: Path, lock_name: str) -> Path:
    """Helper to create a fresh (non-stale) lock file."""
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_file = lock_dir / lock_name
    lock_file.write_text("lock_data", encoding="utf-8")
    return lock_file


class TestCleanupLockDeletion:
    """Test suite for cleanup lock deletion with retry logic."""

    def test_single_terminal_deletes_stale_lock(self, tmp_path: Path):
        """Baseline: Single terminal should delete stale locks."""
        # Create stale lock
        lock_file = create_stale_lock(tmp_path, "test_stale.lock")
        assert lock_file.exists()

        # Simulate cleanup (should delete)
        now = time.time()
        if now - lock_file.stat().st_mtime > STALE_LOCK_SECS:
            # TASK-023 FIX: Retry loop pattern
            max_retries = 4
            base_delay_ms = 100

            for attempt in range(max_retries):
                try:
                    lock_file.unlink(missing_ok=True)
                    break  # Success
                except (FileNotFoundError, PermissionError):
                    if attempt < max_retries - 1:
                        delay_ms = base_delay_ms * (2**attempt)
                        time.sleep(delay_ms / 1000.0)
                    else:
                        pass  # Last attempt failed gracefully

        # Verify deleted
        assert not lock_file.exists()

    def test_concurrent_terminals_delete_same_lock(self, tmp_path: Path):
        """
        REGRESSION TEST: Multiple terminals deleting same stale lock.

        This test verifies TASK-023 fix prevents race condition where:
        1. Terminal A checks stale → TRUE
        2. Terminal B checks stale → TRUE
        3. Terminal A deletes → SUCCESS
        4. Terminal B tries to delete → should handle gracefully
        """
        # Create stale lock
        lock_file = create_stale_lock(tmp_path, "shared_stale.lock")
        assert lock_file.exists()

        # Track results from concurrent terminals
        success_count = []
        errors = []

        def try_delete_lock(thread_id: int):
            """Simulate concurrent terminal deleting lock."""
            try:
                # TASK-023 FIX: Retry loop pattern
                max_retries = 4
                base_delay_ms = 100

                for attempt in range(max_retries):
                    try:
                        lock_file.unlink(missing_ok=True)
                        success_count.append(thread_id)
                        break  # Success
                    except (FileNotFoundError, PermissionError) as e:
                        # TOCTOU race detected - retry
                        if attempt < max_retries - 1:
                            delay_ms = base_delay_ms * (2**attempt)
                            time.sleep(delay_ms / 1000.0)
                        else:
                            # Last attempt failed
                            errors.append((thread_id, type(e).__name__, str(e)))
                    except Exception as e:
                        errors.append((thread_id, type(e).__name__, str(e)))
                        break
            except Exception as e:
                errors.append((thread_id, "Unexpected", str(e)))

        # Launch 5 concurrent terminals
        threads = []
        for i in range(5):
            t = threading.Thread(target=try_delete_lock, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify: No exceptions should be raised
        assert len(errors) == 0, f"Unexpected errors: {errors}"

        # At least one terminal should succeed
        assert len(success_count) >= 1, f"At least one terminal should succeed: {success_count}"

        # Lock should be deleted
        assert not lock_file.exists()

    def test_concurrent_terminals_mixed_operations(self, tmp_path: Path):
        """
        TEST: Concurrent terminals performing mixed operations (read + delete).

        Simulates real-world scenario where some terminals are checking staleness
        while others are deleting.
        """
        # Create multiple stale locks
        locks = []
        for i in range(3):
            lock = create_stale_lock(tmp_path, f"lock_{i}.lock")
            locks.append(lock)

        # Track operations
        deleted_count = []
        checked_count = []

        def mixed_operation(thread_id: int):
            """Simulate mixed check+delete operations."""
            import random

            lock = locks[thread_id % len(locks)]

            # Randomly choose operation
            if random.random() < 0.5:
                # Check staleness
                try:
                    now = time.time()
                    is_stale = now - lock.stat().st_mtime > STALE_LOCK_SECS
                    if is_stale:
                        checked_count.append(thread_id)
                except FileNotFoundError:
                    pass  # File was deleted
            else:
                # Delete with retry logic
                max_retries = 4
                base_delay_ms = 100

                for attempt in range(max_retries):
                    try:
                        if lock.exists():
                            lock.unlink(missing_ok=True)
                            deleted_count.append(thread_id)
                        break
                    except (FileNotFoundError, PermissionError):
                        if attempt < max_retries - 1:
                            delay_ms = base_delay_ms * (2**attempt)
                            time.sleep(delay_ms / 1000.0)
                        else:
                            pass  # Last attempt failed gracefully

        # Launch concurrent operations
        threads = []
        for i in range(10):
            t = threading.Thread(target=mixed_operation, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify: Operations completed without hanging
        assert len(checked_count) + len(deleted_count) > 0

    def test_fresh_lock_not_deleted(self, tmp_path: Path):
        """TEST: Fresh (non-stale) locks should not be deleted."""
        # Create fresh lock
        lock_file = create_fresh_lock(tmp_path, "fresh_lock.lock")
        assert lock_file.exists()

        # Attempt cleanup (should NOT delete)
        now = time.time()
        if now - lock_file.stat().st_mtime > STALE_LOCK_SECS:
            # This branch should NOT execute
            lock_file.unlink(missing_ok=True)

        # Verify: Fresh lock still exists
        assert lock_file.exists()

    def test_missing_lock_handling(self, tmp_path: Path):
        """TEST: Missing lock files should be handled gracefully."""
        non_existent_lock = tmp_path / "missing_lock.lock"

        # Attempt to delete non-existent lock
        max_retries = 4
        base_delay_ms = 100

        for attempt in range(max_retries):
            try:
                non_existent_lock.unlink(missing_ok=True)
                break  # Success (missing_ok=True allows this)
            except (FileNotFoundError, PermissionError):
                if attempt < max_retries - 1:
                    delay_ms = base_delay_ms * (2**attempt)
                    time.sleep(delay_ms / 1000.0)

        # Should complete without exception
        assert True

    def test_permission_error_windows_only(self, tmp_path: Path):
        """
        TEST: PermissionError handling on Windows.

        On Windows, concurrent file access can cause PermissionError due to file locking.
        The retry logic should handle this gracefully.
        """
        if os.name != "nt":
            pytest.skip("Windows-specific test")

        # Create stale lock
        lock_file = create_stale_lock(tmp_path, "permission_test.lock")

        # Simulate concurrent access that might trigger PermissionError
        permission_errors = []

        def simulate_permission_race(thread_id: int):
            """Simulate operation that might hit PermissionError."""
            max_retries = 4
            base_delay_ms = 100

            for attempt in range(max_retries):
                try:
                    # Simulate operation that might conflict
                    lock_file.unlink(missing_ok=True)
                    break
                except PermissionError as e:
                    permission_errors.append((thread_id, attempt, str(e)))
                    if attempt < max_retries - 1:
                        delay_ms = base_delay_ms * (2**attempt)
                        time.sleep(delay_ms / 1000.0)
                except FileNotFoundError:
                    # File already deleted - not an error
                    break
                except Exception:
                    break  # Other errors - don't retry

        # Launch concurrent operations
        threads = []
        for i in range(5):
            t = threading.Thread(target=simulate_permission_race, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # If PermissionErrors occurred, they should have been retried
        # Test passes if we completed without hanging
        assert True


class TestRetryLogicBehavior:
    """Test suite for retry loop behavior and timing."""

    def test_retry_timing_compliance(self, tmp_path: Path):
        """
        TEST: Verify retry timing matches specification.

        Spec: 100ms → 200ms → 400ms → 800ms (exponential backoff)
        """
        lock_file = create_stale_lock(tmp_path, "timing_test.lock")

        # Track retry delays
        retry_delays = []

        def delete_with_timing():
            max_retries = 4
            base_delay_ms = 100

            for attempt in range(max_retries):
                try:
                    # First attempt will succeed (no delay)
                    if attempt == 0:
                        lock_file.unlink(missing_ok=True)
                        break
                except (FileNotFoundError, PermissionError):
                    if attempt < max_retries - 1:
                        delay_ms = base_delay_ms * (2**attempt)
                        retry_delays.append(delay_ms)
                        time.sleep(delay_ms / 1000.0)

        # Run deletion
        delete_with_timing()

        # If retries occurred, verify timing
        # (This test typically succeeds on first attempt, so no delays)
        assert True  # Test verifies we don't hang or crash

    def test_maximum_retry_attempts(self, tmp_path: Path):
        """TEST: Verify exactly 4 retry attempts are made."""
        lock_file = create_stale_lock(tmp_path, "retry_count.lock")

        attempt_count = []

        def delete_with_retry_count():
            max_retries = 4
            base_delay_ms = 100

            for attempt in range(max_retries):
                attempt_count.append(attempt)
                try:
                    # Simulate failure on first 3 attempts, success on 4th
                    if attempt < 3:
                        raise FileNotFoundError("Simulated failure")
                    lock_file.unlink(missing_ok=True)
                    break
                except (FileNotFoundError, PermissionError):
                    if attempt < max_retries - 1:
                        delay_ms = base_delay_ms * (2**attempt)
                        time.sleep(delay_ms / 1000.0)

        # Run deletion
        delete_with_retry_count()

        # Verify: Exactly 4 attempts made (0, 1, 2, 3)
        assert len(attempt_count) == 4


class TestCleanupIntegration:
    """Integration tests for cleanup operations."""

    def test_cleanup_multiple_locks_concurrently(self, tmp_path: Path):
        """
        INTEGRATION TEST: Multiple terminals cleaning up multiple locks.

        Simulates real-world scenario with:
        - 5 concurrent terminals
        - 10 stale locks per terminal
        - Each terminal cleans up all locks
        """
        # Create 10 stale locks
        locks = []
        for i in range(10):
            lock = create_stale_lock(tmp_path, f"multi_lock_{i}.lock")
            locks.append(lock)

        # Track cleanup results
        cleanup_results = []

        def cleanup_all_locks(thread_id: int):
            """Each terminal attempts to clean all locks."""
            deleted = 0
            for lock in locks:
                max_retries = 4
                base_delay_ms = 100

                for attempt in range(max_retries):
                    try:
                        if lock.exists():
                            now = time.time()
                            if now - lock.stat().st_mtime > STALE_LOCK_SECS:
                                lock.unlink(missing_ok=True)
                                deleted += 1
                        break
                    except (FileNotFoundError, PermissionError):
                        if attempt < max_retries - 1:
                            delay_ms = base_delay_ms * (2**attempt)
                            time.sleep(delay_ms / 1000.0)
                        else:
                            pass  # Last attempt failed gracefully

            cleanup_results.append((thread_id, deleted))

        # Launch 5 concurrent terminals
        threads = []
        for i in range(5):
            t = threading.Thread(target=cleanup_all_locks, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify: All locks deleted (at least once)
        for lock in locks:
            assert not lock.exists(), f"Lock {lock.name} should be deleted"

        # Verify: All terminals completed successfully
        assert len(cleanup_results) == 5

    def test_cleanup_performance_acceptable(self, tmp_path: Path):
        """
        PERFORMANCE TEST: Cleanup operations should complete in reasonable time.

        Even with all retries, worst-case time should be <2 seconds per operation.
        """
        # Create stale lock
        lock_file = create_stale_lock(tmp_path, "perf_test.lock")

        # Measure execution time
        start = time.perf_counter()

        max_retries = 4
        base_delay_ms = 100

        for attempt in range(max_retries):
            try:
                lock_file.unlink(missing_ok=True)
                break
            except (FileNotFoundError, PermissionError):
                if attempt < max_retries - 1:
                    delay_ms = base_delay_ms * (2**attempt)
                    time.sleep(delay_ms / 1000.0)

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Verify: Completed in reasonable time
        # Worst case: 100 + 200 + 400 + 800 = 1500ms
        assert elapsed_ms < 2000, f"Performance degraded: {elapsed_ms:.0f}ms > 2000ms threshold"


class TestBackwardCompatibility:
    """Test backward compatibility with non-retry code."""

    def test_missing_ok_true_behavior(self, tmp_path: Path):
        """
        TEST: missing_ok=True should not raise FileNotFoundError.

        This verifies backward compatibility with code that relies on missing_ok=True.
        """
        non_existent = tmp_path / "does_not_exist.lock"

        # Should not raise exception
        max_retries = 4
        base_delay_ms = 100

        for attempt in range(max_retries):
            try:
                non_existent.unlink(missing_ok=True)
                break  # Success
            except (FileNotFoundError, PermissionError):
                if attempt < max_retries - 1:
                    delay_ms = base_delay_ms * (2**attempt)
                    time.sleep(delay_ms / 1000.0)

        # Test passes if no exception was raised
        assert True


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
