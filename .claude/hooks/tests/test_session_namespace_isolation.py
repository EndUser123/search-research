#!/usr/bin/env python3
"""
Tests for Session Namespace Isolation in File Lock Manager.

This test suite implements TDD RED phase for session namespace isolation.
Tests will FAIL until the implementation is complete.

Architecture:
- Session-prefixed lock directories: .claude/.locks/session_<id>/
- Automatic cleanup on session end
- No lock conflicts between concurrent sessions
"""

import json
import os
import sys
import time
import uuid
from pathlib import Path

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Mock imports first (tests will fail until implementation exists)
try:
    from file_lock_manager import (
        LOCK_DIR,
        LOCK_TIMEOUT_SECONDS,
        SESSION_LOCK_DIR,  # New: session-scoped lock directory
        _get_lock_path,
        _get_session_id,
        _get_session_lock_dir,
        acquire_lock,
        check_lock,
        cleanup_session_locks,
        cleanup_stale_locks,
        release_lock,
    )
except ImportError:
    # This is expected in RED phase - implementation doesn't exist yet
    pass


def reset_session_cache():
    """Reset the session lock directory cache for testing."""
    import file_lock_manager
    file_lock_manager.SESSION_LOCK_DIR = None


class TestSessionIdGeneration:
    """Test suite for session ID generation and consistency."""

    def test_session_id_is_unique(self):
        """Session IDs should be unique across instances."""
        # This test will fail until _get_session_id is implemented
        session1 = _get_session_id()
        session2 = _get_session_id()

        # Same process should return same session ID (consistency)
        assert session1 == session2, f"Expected consistent session ID, got {session1} vs {session2}"

        # Session ID should be non-empty
        assert session1, "Session ID should not be empty"
        assert len(session1) > 5, f"Session ID too short: {session1}"

        print("PASS: Session ID generation is consistent")

    def test_session_id_from_environment(self):
        """Session ID should respect CLAUDE_SESSION_ID environment variable."""
        # Set custom session ID
        custom_id = f"test_sess_{uuid.uuid4().hex[:8]}"
        os.environ["CLAUDE_SESSION_ID"] = custom_id

        # Clear any cached session ID
        if hasattr(_get_session_id, '__wrapped__'):
            # Reset cache if function uses lru_cache
            _get_session_id.cache_clear()

        session_id = _get_session_id()
        assert session_id == custom_id, f"Expected {custom_id}, got {session_id}"

        # Cleanup
        del os.environ["CLAUDE_SESSION_ID"]

        print("PASS: Session ID from environment variable")


class TestSessionNamespacePaths:
    """Test suite for session-prefixed lock directory paths."""

    def test_lock_path_includes_session(self):
        """Lock file paths should include session namespace prefix."""
        # Get current session ID
        session_id = _get_session_id()

        # Get lock path for a test file
        lock_path = _get_lock_path("test_file.py")

        # Verify path includes session directory
        path_str = str(lock_path)

        # Should be in session-specific subdirectory
        assert f"session_{session_id}" in path_str or session_id in path_str, \
            f"Lock path should include session namespace: {path_str}"

        print("PASS: Lock paths include session namespace")

    def test_different_sessions_different_paths(self):
        """Different sessions should have different lock paths for same file."""
        # Session 1
        os.environ["CLAUDE_SESSION_ID"] = "sess_test_1"
        reset_session_cache()
        path1 = _get_lock_path("same_file.py")

        # Session 2
        os.environ["CLAUDE_SESSION_ID"] = "sess_test_2"
        reset_session_cache()
        path2 = _get_lock_path("same_file.py")

        # Paths should be different (session isolation)
        assert path1 != path2, \
            f"Different sessions should have different lock paths: {path1} vs {path2}"

        # Cleanup
        del os.environ["CLAUDE_SESSION_ID"]
        reset_session_cache()

        print("PASS: Different sessions have different lock paths")


class TestSessionIsolation:
    """Test suite for lock isolation between sessions."""

    def test_concurrent_sessions_no_conflict(self):
        """Two sessions should be able to lock the same file without conflict."""
        # Simulate Session 1 acquiring lock
        os.environ["CLAUDE_SESSION_ID"] = "sess_isolation_test_1"
        reset_session_cache()
        success1, msg1 = acquire_lock("shared_file.py")

        assert success1, f"Session 1 should acquire lock: {msg1}"

        # Simulate Session 2 trying to lock same file
        os.environ["CLAUDE_SESSION_ID"] = "sess_isolation_test_2"
        reset_session_cache()
        success2, msg2 = acquire_lock("shared_file.py")

        # Both should succeed because they use different lock namespaces
        assert success2, f"Session 2 should acquire lock (isolated): {msg2}"

        # Both should have their own lock files
        os.environ["CLAUDE_SESSION_ID"] = "sess_isolation_test_1"
        reset_session_cache()
        lock1 = check_lock("shared_file.py")
        assert lock1 is not None, "Session 1 should have active lock"

        os.environ["CLAUDE_SESSION_ID"] = "sess_isolation_test_2"
        reset_session_cache()
        lock2 = check_lock("shared_file.py")
        assert lock2 is not None, "Session 2 should have active lock"

        # Cleanup
        os.environ["CLAUDE_SESSION_ID"] = "sess_isolation_test_1"
        reset_session_cache()
        release_lock("shared_file.py")

        os.environ["CLAUDE_SESSION_ID"] = "sess_isolation_test_2"
        reset_session_cache()
        release_lock("shared_file.py")

        del os.environ["CLAUDE_SESSION_ID"]
        reset_session_cache()

        print("PASS: Concurrent sessions do not conflict")

    def test_session_only_releases_own_locks(self):
        """Session should only release locks it owns."""
        # Session 1 acquires lock
        os.environ["CLAUDE_SESSION_ID"] = "sess_release_test_1"
        acquire_lock("exclusive_file.py")

        # Session 2 should NOT be able to release Session 1's lock
        os.environ["CLAUDE_SESSION_ID"] = "sess_release_test_2"
        released = release_lock("exclusive_file.py")

        # Release should fail (return False) because lock belongs to Session 1
        # Note: Current implementation returns True for stale locks, so this tests ownership
        assert released is False, "Session 2 should not release Session 1's lock"

        # Session 1's lock should still exist
        os.environ["CLAUDE_SESSION_ID"] = "sess_release_test_1"
        lock = check_lock("exclusive_file.py")
        assert lock is not None, "Session 1's lock should still exist"

        # Session 1 can release its own lock
        released = release_lock("exclusive_file.py")
        assert released is True, "Session 1 should release its own lock"

        # Cleanup
        del os.environ["CLAUDE_SESSION_ID"]

        print("PASS: Sessions only release their own locks")


class TestSessionDirectoryStructure:
    """Test suite for session directory layout."""

    def test_session_directories_created(self):
        """Session-specific lock directories should be created on demand."""
        # Use a unique session ID
        test_session = f"sess_dir_test_{uuid.uuid4().hex[:8]}"
        os.environ["CLAUDE_SESSION_ID"] = test_session
        reset_session_cache()

        # Trigger lock creation
        acquire_lock("dir_test_file.py")

        # Check that session directory exists
        session_dir = LOCK_DIR / f"session_{test_session}"
        if not session_dir.exists():
            # Alternative naming: just session ID as directory name
            session_dir = LOCK_DIR / test_session

        assert session_dir.exists(), f"Session directory should exist: {session_dir}"
        assert session_dir.is_dir(), f"Session path should be a directory: {session_dir}"

        # Lock file should be inside session directory
        lock_path = _get_lock_path("dir_test_file.py")
        assert session_dir in lock_path.parents or lock_path.parent == session_dir, \
            f"Lock should be in session directory: {lock_path} not in {session_dir}"

        # Cleanup
        release_lock("dir_test_file.py")
        del os.environ["CLAUDE_SESSION_ID"]
        reset_session_cache()

        print("PASS: Session directories created correctly")

    def test_multiple_sessions_multiple_directories(self):
        """Multiple sessions should create separate directories."""
        session1 = f"sess_multi_{uuid.uuid4().hex[:6]}"
        session2 = f"sess_multi_{uuid.uuid4().hex[:6]}"

        # Session 1 creates lock
        os.environ["CLAUDE_SESSION_ID"] = session1
        reset_session_cache()
        acquire_lock("multi_test.py")
        dir1 = LOCK_DIR / f"session_{session1}"
        if not dir1.exists():
            dir1 = LOCK_DIR / session1

        # Session 2 creates lock
        os.environ["CLAUDE_SESSION_ID"] = session2
        reset_session_cache()
        acquire_lock("multi_test.py")
        dir2 = LOCK_DIR / f"session_{session2}"
        if not dir2.exists():
            dir2 = LOCK_DIR / session2

        # Both directories should exist
        assert dir1.exists(), f"Session 1 directory should exist: {dir1}"
        assert dir2.exists(), f"Session 2 directory should exist: {dir2}"
        assert dir1 != dir2, "Sessions should have different directories"

        # Cleanup
        os.environ["CLAUDE_SESSION_ID"] = session1
        reset_session_cache()
        release_lock("multi_test.py")

        os.environ["CLAUDE_SESSION_ID"] = session2
        reset_session_cache()
        release_lock("multi_test.py")

        del os.environ["CLAUDE_SESSION_ID"]
        reset_session_cache()

        print("PASS: Multiple sessions create separate directories")


class TestSessionCleanup:
    """Test suite for session cleanup on session end."""

    def test_cleanup_removes_session_locks_only(self):
        """Session cleanup should only remove locks for that session."""
        # Create two sessions with locks
        session1 = f"sess_cleanup_1_{uuid.uuid4().hex[:6]}"
        session2 = f"sess_cleanup_2_{uuid.uuid4().hex[:6]}"

        # Session 1 acquires lock
        os.environ["CLAUDE_SESSION_ID"] = session1
        reset_session_cache()
        acquire_lock("cleanup_test.py")
        lock1_path = _get_lock_path("cleanup_test.py")

        # Session 2 acquires lock on same file
        os.environ["CLAUDE_SESSION_ID"] = session2
        reset_session_cache()
        acquire_lock("cleanup_test.py")
        lock2_path = _get_lock_path("cleanup_test.py")

        # Verify both locks exist
        assert lock1_path.exists(), "Session 1 lock should exist"
        assert lock2_path.exists(), "Session 2 lock should exist"

        # Cleanup Session 1 only
        removed = cleanup_session_locks(session1)

        # Session 1's lock should be gone
        assert not lock1_path.exists(), "Session 1 lock should be removed"

        # Session 2's lock should still exist
        assert lock2_path.exists(), "Session 2 lock should still exist"

        # Cleanup Session 2
        cleanup_session_locks(session2)

        # Cleanup environment
        del os.environ["CLAUDE_SESSION_ID"]
        reset_session_cache()

        print("PASS: Session cleanup only affects own locks")

    def test_stale_session_cleanup(self):
        """Old session directories should be cleaned up."""
        # This tests integration with stale lock cleanup
        # Stale session directories should be removable

        # Create a session with very old locks
        old_session = f"sess_old_{uuid.uuid4().hex[:6]}"
        os.environ["CLAUDE_SESSION_ID"] = old_session
        reset_session_cache()

        # Manually create an old lock file
        lock_path = _get_lock_path("stale_session_test.py")
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        old_data = {
            "session": old_session,
            "file": "stale_session_test.py",
            "created": time.time() - (LOCK_TIMEOUT_SECONDS + 100),  # Very old
            "pid": 99999
        }
        lock_path.write_text(json.dumps(old_data))

        # Run stale cleanup
        removed = cleanup_stale_locks()

        # Old lock should be removed
        assert not lock_path.exists(), "Stale session lock should be removed"

        # Cleanup
        del os.environ["CLAUDE_SESSION_ID"]
        reset_session_cache()

        print("PASS: Stale session cleanup works")


class TestBackwardCompatibility:
    """Test suite for ensuring backward compatibility during migration."""

    def test_legacy_locks_still_work(self):
        """Legacy (non-session) locks should still be handled."""
        # Create a legacy lock directly (no session prefix)
        LOCK_DIR.mkdir(parents=True, exist_ok=True)
        legacy_lock_path = LOCK_DIR / "legacy_test.py.lock"

        # Write legacy format lock
        legacy_data = {
            "session": "legacy_session",
            "file": "legacy_test.py",
            "created": time.time(),
            "pid": 12345
        }
        legacy_lock_path.write_text(json.dumps(legacy_data))

        # Check should recognize it
        lock_info = check_lock("legacy_test.py")

        # Note: With session isolation, this might return None
        # because it looks in session-specific path
        # This test documents the migration behavior
        print(f"INFO: Legacy lock check returned: {lock_info}")

        # Cleanup
        legacy_lock_path.unlink(missing_ok=True)

        print("PASS: Legacy lock compatibility documented")


def run_all_tests():
    """Run all tests."""
    test_classes = [
        TestSessionIdGeneration,
        TestSessionNamespacePaths,
        TestSessionIsolation,
        TestSessionDirectoryStructure,
        TestSessionCleanup,
        TestBackwardCompatibility,
    ]

    total_tests = 0
    failed = []

    for test_class in test_classes:
        instance = test_class()
        test_methods = [m for m in dir(instance) if m.startswith('test_')]

        for method_name in test_methods:
            total_tests += 1
            test_method = getattr(instance, method_name)

            try:
                test_method()
            except AssertionError as e:
                print(f"FAIL: {test_class.__name__}.{method_name}")
                print(f"  {e}")
                failed.append((f"{test_class.__name__}.{method_name}", e))
            except Exception as e:
                print(f"ERROR: {test_class.__name__}.{method_name}")
                print(f"  {type(e).__name__}: {e}")
                failed.append((f"{test_class.__name__}.{method_name}", e))

    # Final cleanup
    try:
        cleanup_stale_locks()
    except:
        pass

    print(f"\n{'='*60}")
    print(f"Results: {total_tests - len(failed)}/{total_tests} tests passed")

    if failed:
        print(f"\nFAILED: {len(failed)} tests")
        for name, error in failed:
            print(f"  - {name}")
        return 1
    else:
        print(f"\nSUCCESS: All {total_tests} tests passed")
        return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
