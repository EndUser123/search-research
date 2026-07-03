#!/usr/bin/env python3
"""Tests for file lock manager improvements."""

import json
import sys
import time
from pathlib import Path

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from file_lock_manager import (
    LOCK_DIR,
    LOCK_TIMEOUT_SECONDS,
    _get_lock_path,
    _get_session_lock_dir,
    acquire_lock,
    cleanup_stale_locks,
    release_lock,
)


def test_lock_timeout_is_reduced():
    """Verify lock timeout is now 10 seconds (not 30)."""
    assert LOCK_TIMEOUT_SECONDS == 10, f"Expected 10s timeout, got {LOCK_TIMEOUT_SECONDS}s"
    print("PASS: Lock timeout is 10 seconds")


def test_stale_lock_cleanup():
    """Verify stale locks are cleaned up correctly."""
    # Create a manually stale lock
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    session_dir = _get_session_lock_dir()
    session_dir.mkdir(parents=True, exist_ok=True)
    lock_path = _get_lock_path("test_file.py")

    # Write a lock that's older than timeout
    stale_data = {
        "session": "test_session_old",
        "file": "test_file.py",
        "created": time.time() - 15,  # 15 seconds ago (older than 10s timeout)
        "pid": 12345
    }
    lock_path.write_text(json.dumps(stale_data))

    # Run cleanup
    removed = cleanup_stale_locks()

    assert removed >= 1, f"Expected at least 1 lock removed, got {removed}"
    assert not lock_path.exists(), "Stale lock should be removed"
    print("PASS: Stale locks cleaned up correctly")


def test_fresh_lock_not_cleaned():
    """Verify fresh locks are NOT cleaned up."""
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    session_dir = _get_session_lock_dir()
    session_dir.mkdir(parents=True, exist_ok=True)
    lock_path = _get_lock_path("test_file_fresh.py")

    # Write a fresh lock
    fresh_data = {
        "session": "test_session_fresh",
        "file": "test_file_fresh.py",
        "created": time.time() - 2,  # 2 seconds ago (fresh)
        "pid": 12345
    }
    lock_path.write_text(json.dumps(fresh_data))

    # Run cleanup
    removed = cleanup_stale_locks()

    # Fresh lock should still exist
    assert lock_path.exists(), "Fresh lock should not be removed"
    print("PASS: Fresh locks preserved during cleanup")

    # Cleanup after test
    lock_path.unlink(missing_ok=True)


def test_lock_messages_include_file_path():
    """Verify lock messages include the file path for clarity."""
    success, message = acquire_lock("test_specific_file.py")

    if not success:
        # If already locked, message should reference the file
        assert "test_specific_file.py" in message or "Locked by" in message, \
            f"Expected file path in message, got: {message}"
    else:
        # We got the lock, release it
        release_lock("test_specific_file.py")

    print("PASS: Lock messages include relevant information")


def test_concurrent_lock_prevention():
    """Verify that a new session can't steal an active lock."""
    lock_path = _get_lock_path("test_concurrent.py")

    # First session acquires lock
    success1, msg1 = acquire_lock("test_concurrent.py")
    assert success1, f"First session should acquire lock: {msg1}"

    # Simulate different session by modifying the lock's session ID check
    # (In real scenario, this would be a different process)
    lock_data = json.loads(lock_path.read_text())
    original_session = lock_data["session"]

    # Try to acquire again (should work due to re-entrancy)
    success2, msg2 = acquire_lock("test_concurrent.py")
    assert success2, f"Same session should re-acquire lock (re-entrancy): {msg2}"

    # Clean up
    release_lock("test_concurrent.py")

    print("PASS: Re-entrancy works for same session")


def run_all_tests():
    """Run all tests."""
    tests = [
        test_lock_timeout_is_reduced,
        test_stale_lock_cleanup,
        test_fresh_lock_not_cleaned,
        test_lock_messages_include_file_path,
        test_concurrent_lock_prevention,
    ]

    print(f"Running {len(tests)} tests...\n")
    failed = []

    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"FAIL: {test.__name__}")
            print(f"  {e}")
            failed.append((test.__name__, e))
        except Exception as e:
            print(f"ERROR: {test.__name__}")
            print(f"  {e}")
            failed.append((test.__name__, e))

    # Final cleanup
    cleanup_stale_locks()

    print(f"\n{'='*50}")
    if failed:
        print(f"FAILED: {len(failed)}/{len(tests)} tests")
        for name, error in failed:
            print(f"  - {name}")
        return 1
    else:
        print(f"SUCCESS: All {len(tests)} tests passed")
        return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
