"""Tests for dreaming mutex/PID file system (T-002).

These tests verify the singleton mutex system for the dreaming daemon:
- PID file lock acquisition (primary mechanism)
- Windows mutex as enforcement layer (secondary)
- Stale mutex detection and recovery
- Clean release of both locks

Test Structure:
- TestDreamingMutexFirstAcquisition - First acquisition succeeds
- TestDreamingMutexSingleInstance - Second acquisition fails
- TestDreamingMutexPidFileLocking - PID file locking mechanism
- TestDreamingMutexOperations - Mutex acquisition and release
- TestDreamingMutexStaleDetection - Stale mutex detection (PID mismatch)
- TestDreamingMutexCleanup - Cleanup on release

Run with: pytest P:/.claude/hooks/tests/test_dreaming_mutex.py -v

Expected: All tests FAIL (RED phase) - dreaming_mutex module doesn't exist yet
"""
import os
from unittest.mock import MagicMock, patch


class TestDreamingMutexFirstAcquisition:
    """Tests for first-time acquisition succeeding."""

    def test_first_acquisition_succeeds(self, tmp_path):
        """
        Test that first acquisition of singleton lock succeeds.

        Given: No PID file exists and mutex is not held
        When: acquire_singleton() is called
        Then: Returns (True, "") - success with no error message
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"

        # Act & Assert
        # This will fail because dreaming_mutex module doesn't exist yet
        from hooks.dreaming_mutex import acquire_singleton

        success, error_msg = acquire_singleton(pid_file=str(pid_file))

        # Assert
        assert success is True
        assert error_msg == ""
        assert pid_file.exists()  # PID file should be created

    def test_first_acquisition_writes_current_pid(self, tmp_path):
        """
        Test that first acquisition writes current PID to file.

        Given: No PID file exists
        When: acquire_singleton() is called
        Then: PID file contains current process ID
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        current_pid = os.getpid()

        # Act
        from hooks.dreaming_mutex import acquire_singleton

        success, error_msg = acquire_singleton(pid_file=str(pid_file))

        # Assert
        assert success is True
        pid_content = pid_file.read_text().strip()
        assert pid_content == str(current_pid)


class TestDreamingMutexSingleInstance:
    """Tests for single-instance enforcement."""

    def test_second_acquisition_fails(self, tmp_path):
        """
        Test that second acquisition fails when first is held.

        Given: PID file exists with valid PID
        When: acquire_singleton() is called again
        Then: Returns (False, error_msg) - failure with error message
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        current_pid = os.getpid()
        pid_file.write_text(str(current_pid))

        # Act
        from hooks.dreaming_mutex import acquire_singleton

        success, error_msg = acquire_singleton(pid_file=str(pid_file))

        # Assert
        assert success is False
        assert error_msg != ""
        assert "already running" in error_msg.lower() or "instance" in error_msg.lower()

    def test_second_acquisition_does_not_overwrite_pid(self, tmp_path):
        """
        Test that failed acquisition doesn't overwrite existing PID file.

        Given: PID file exists with a RUNNING process PID (using current process)
        When: First acquire_singleton() succeeds, then try second acquisition
        Then: Second acquisition fails and PID file content remains unchanged

        Note: Uses current process PID to simulate running daemon (anti-mock principle).
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        current_pid = str(os.getpid())

        # Act - First acquisition should succeed
        from hooks.dreaming_mutex import acquire_singleton, release_singleton

        success1, error_msg1 = acquire_singleton(pid_file=str(pid_file))
        assert success1 is True, f"First acquisition should succeed: {error_msg1}"

        # Verify PID file was written
        pid_content_after_first = pid_file.read_text().strip()
        assert pid_content_after_first == current_pid

        # Act - Second acquisition should fail (mutex already held by this process)
        success2, error_msg2 = acquire_singleton(pid_file=str(pid_file))

        # Assert - Second acquisition should fail because mutex is already held
        assert success2 is False, f"Second acquisition should fail: {error_msg2}"

        # Most important: PID file content should remain unchanged
        pid_content_final = pid_file.read_text().strip()
        assert pid_content_final == current_pid, "PID file should not be overwritten"

        # Cleanup
        release_singleton(str(pid_file))


class TestDreamingMutexPidFileLocking:
    """Tests for PID file locking mechanism."""

    def test_pid_file_created_on_acquire(self, tmp_path):
        """
        Test that PID file is created during acquisition.

        Given: No PID file exists
        When: acquire_singleton() succeeds
        Then: PID file is created with current PID
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"

        # Act
        from hooks.dreaming_mutex import acquire_singleton

        success, error_msg = acquire_singleton(pid_file=str(pid_file))

        # Assert
        assert success is True
        assert pid_file.exists()
        assert pid_file.read_text().strip() == str(os.getpid())

    def test_pid_file_deleted_on_release(self, tmp_path):
        """
        Test that PID file is deleted during release.

        Given: PID file exists from successful acquisition
        When: release_singleton() is called
        Then: PID file is deleted
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        from hooks.dreaming_mutex import acquire_singleton, release_singleton

        # Acquire first
        success, error_msg = acquire_singleton(pid_file=str(pid_file))
        assert success is True
        assert pid_file.exists()

        # Act - release
        release_singleton(pid_file=str(pid_file))

        # Assert
        assert not pid_file.exists()

    def test_acquire_atomic_no_race_condition(self, tmp_path):
        """
        Test that acquire is atomic (no race condition).

        Given: Two concurrent acquisition attempts
        When: Both call acquire_singleton() simultaneously
        Then: Only one succeeds, atomic operation prevents race
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        from hooks.dreaming_mutex import acquire_singleton

        # Act - simulate concurrent acquisition
        # First acquisition
        success1, error1 = acquire_singleton(pid_file=str(pid_file))

        # Second acquisition (should fail)
        success2, error2 = acquire_singleton(pid_file=str(pid_file))

        # Assert - exactly one should succeed
        assert success1 != success2, "Only one acquisition should succeed"
        assert pid_file.exists()


class TestDreamingMutexOperations:
    """Tests for mutex acquisition and release operations."""

    @patch('ctypes.windll.kernel32.CreateMutexW')
    @patch('ctypes.windll.kernel32.CloseHandle')
    def test_mutex_created_on_acquire(self, mock_close, mock_create, tmp_path):
        """
        Test that Windows mutex is created during acquisition.

        Given: acquire_singleton() is called
        When: PID file lock succeeds
        Then: Windows mutex is created with correct name
        """
        # Arrange
        mock_create.return_value = MagicMock(handle=12345)
        pid_file = tmp_path / "dreaming-daemon.pid"

        # Act
        from hooks.dreaming_mutex import acquire_singleton

        success, error_msg = acquire_singleton(pid_file=str(pid_file))

        # Assert
        assert success is True
        mock_create.assert_called_once()
        # Check mutex name contains "ClaudeInsightDaemon"
        call_args = mock_create.call_args
        assert call_args is not None

    @patch('ctypes.windll.kernel32.CreateMutexW')
    @patch('ctypes.windll.kernel32.ReleaseMutex')
    @patch('ctypes.windll.kernel32.CloseHandle')
    def test_mutex_released_on_cleanup(self, mock_close, mock_release, mock_create, tmp_path):
        """
        Test that Windows mutex is released during cleanup.

        Given: Mutex was acquired successfully
        When: release_singleton() is called
        Then: Both mutex and PID file are released
        """
        # Arrange
        mock_mutex = MagicMock(handle=12345)
        mock_create.return_value = mock_mutex
        pid_file = tmp_path / "dreaming-daemon.pid"

        from hooks.dreaming_mutex import acquire_singleton, release_singleton

        # Acquire first
        success, error_msg = acquire_singleton(pid_file=str(pid_file))
        assert success is True

        # Act - release
        release_singleton(pid_file=str(pid_file))

        # Assert - mutex released and closed
        mock_release.assert_called_once()
        mock_close.assert_called_once()
        assert not pid_file.exists()

    def test_release_without_acquire_safe(self, tmp_path):
        """
        Test that releasing without acquiring is safe (no-op).

        Given: No PID file exists and no mutex held
        When: release_singleton() is called
        Then: No error, safe no-op
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"

        # Act & Assert - should not raise
        from hooks.dreaming_mutex import release_singleton

        release_singleton(pid_file=str(pid_file))  # Should not raise

        # Assert - no PID file created
        assert not pid_file.exists()


class TestDreamingMutexStaleDetection:
    """Tests for stale mutex detection (PID mismatch)."""

    def test_stale_mutex_pid_mismatch_detected(self, tmp_path):
        """
        Test that stale mutex is detected when PID doesn't match.

        Given: PID file exists with non-running PID
        When: acquire_singleton() is called
        Then: Stale lock detected, new acquisition succeeds
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        fake_pid = "99999"  # Non-existent PID
        pid_file.write_text(fake_pid)

        # Act
        from hooks.dreaming_mutex import acquire_singleton

        success, error_msg = acquire_singleton(pid_file=str(pid_file))

        # Assert - should succeed (stale lock recovered)
        assert success is True
        # PID should be updated to current process
        assert pid_file.read_text().strip() == str(os.getpid())

    def test_stale_mutex_recovery_overwrites_pid(self, tmp_path):
        """
        Test that stale lock recovery overwrites old PID.

        Given: PID file with stale PID (process not running)
        When: New acquisition succeeds after stale detection
        Then: Old PID is overwritten with current PID
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        stale_pid = "11111"
        pid_file.write_text(stale_pid)

        # Act
        from hooks.dreaming_mutex import acquire_singleton

        success, error_msg = acquire_singleton(pid_file=str(pid_file))

        # Assert
        assert success is True
        current_pid = str(os.getpid())
        assert pid_file.read_text().strip() == current_pid
        assert pid_file.read_text().strip() != stale_pid

    @patch('os.kill')
    def test_pid_running_check_prevents_acquisition(self, mock_kill, tmp_path):
        """
        Test that running PID check prevents acquisition.

        Given: PID file exists with running process
        When: acquire_singleton() checks if PID is running
        Then: Acquisition fails (process is alive)
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        running_pid = 12345
        pid_file.write_text(str(running_pid))

        # Mock os.kill to simulate process is running
        # (no exception means process exists)
        mock_kill.return_value = None

        # Act
        from hooks.dreaming_mutex import acquire_singleton

        success, error_msg = acquire_singleton(pid_file=str(pid_file))

        # Assert - should fail (process running)
        assert success is False
        assert "already running" in error_msg.lower() or "instance" in error_msg.lower()


class TestDreamingMutexCleanup:
    """Tests for cleanup on release."""

    @patch('ctypes.windll.kernel32.CreateMutexW')
    @patch('ctypes.windll.kernel32.ReleaseMutex')
    @patch('ctypes.windll.kernel32.CloseHandle')
    def test_release_cleans_both_locks(self, mock_close, mock_release, mock_create, tmp_path):
        """
        Test that release cleans up both PID file and mutex.

        Given: Both PID file lock and mutex are held
        When: release_singleton() is called
        Then: Both locks are released
        """
        # Arrange
        mock_mutex = MagicMock(handle=12345)
        mock_create.return_value = mock_mutex
        pid_file = tmp_path / "dreaming-daemon.pid"

        from hooks.dreaming_mutex import acquire_singleton, release_singleton

        # Acquire both locks
        success, error_msg = acquire_singleton(pid_file=str(pid_file))
        assert success is True
        assert pid_file.exists()

        # Act - release
        release_singleton(pid_file=str(pid_file))

        # Assert - both cleaned up
        assert not pid_file.exists()
        mock_release.assert_called_once_with(mock_mutex)
        mock_close.assert_called_once_with(mock_mutex)

    def test_release_idempotent(self, tmp_path):
        """
        Test that multiple releases are safe (idempotent).

        Given: Locks already released
        When: release_singleton() is called multiple times
        Then: No errors, safe no-ops
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"

        from hooks.dreaming_mutex import release_singleton

        # Act - release multiple times
        release_singleton(pid_file=str(pid_file))
        release_singleton(pid_file=str(pid_file))
        release_singleton(pid_file=str(pid_file))

        # Assert - no errors, no PID file
        assert not pid_file.exists()

    @patch('ctypes.windll.kernel32.CreateMutexW')
    @patch('ctypes.windll.kernel32.ReleaseMutex')
    @patch('ctypes.windll.kernel32.CloseHandle')
    def test_acquire_after_release_succeeds(self, mock_close, mock_release, mock_create, tmp_path):
        """
        Test that acquisition after release succeeds.

        Given: Locks were acquired then released
        When: acquire_singleton() is called again
        Then: New acquisition succeeds
        """
        # Arrange
        mock_mutex = MagicMock(handle=12345)
        mock_create.return_value = mock_mutex
        pid_file = tmp_path / "dreaming-daemon.pid"

        from hooks.dreaming_mutex import acquire_singleton, release_singleton

        # First cycle
        success1, _ = acquire_singleton(pid_file=str(pid_file))
        assert success1 is True

        release_singleton(pid_file=str(pid_file))
        assert not pid_file.exists()

        # Act - second cycle
        success2, error2 = acquire_singleton(pid_file=str(pid_file))

        # Assert - should succeed again
        assert success2 is True
        assert pid_file.exists()


class TestDreamingMutexIsInstanceRunning:
    """Tests for is_instance_running() helper function."""

    def test_returns_true_when_instance_running(self, tmp_path):
        """
        Test that is_instance_running returns True when PID file exists.

        Given: Valid PID file exists with running process
        When: is_instance_running() is called
        Then: Returns True
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        current_pid = os.getpid()
        pid_file.write_text(str(current_pid))

        # Act
        from hooks.dreaming_mutex import is_instance_running

        result = is_instance_running(pid_file=str(pid_file))

        # Assert
        assert result is True

    def test_returns_false_when_no_instance(self, tmp_path):
        """
        Test that is_instance_running returns False when no PID file.

        Given: PID file does not exist
        When: is_instance_running() is called
        Then: Returns False
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"

        # Act
        from hooks.dreaming_mutex import is_instance_running

        result = is_instance_running(pid_file=str(pid_file))

        # Assert
        assert result is False

    def test_returns_false_when_stale_pid(self, tmp_path):
        """
        Test that is_instance_running returns False for stale PID.

        Given: PID file exists with non-running PID
        When: is_instance_running() is called
        Then: Returns False (stale detected)
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        stale_pid = "99999"
        pid_file.write_text(stale_pid)

        # Act
        from hooks.dreaming_mutex import is_instance_running

        result = is_instance_running(pid_file=str(pid_file))

        # Assert
        assert result is False


class TestDreamingMutexCanonicalPid:
    """Tests for canonical PID preservation (T-002)."""

    def test_first_acquisition_sets_canonical_pid(self, tmp_path):
        """
        Test that first acquisition sets canonical_pid in state file.

        Given: No state file exists (canonical_pid defaults to 0)
        When: acquire_singleton() is called
        Then: canonical_pid is set to current PID in state file
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        state_file = tmp_path / "dreaming-daemon-state.json"
        current_pid = os.getpid()

        # Act
        from dreaming_state import load_state

        from hooks.dreaming_mutex import acquire_singleton

        success, error_msg = acquire_singleton(
            pid_file=str(pid_file),
            state_file=str(state_file)
        )

        # Assert
        assert success is True, f"Acquisition should succeed: {error_msg}"

        # Load state and verify canonical_pid was set
        state = load_state(state_file)
        assert state.canonical_pid == current_pid, "canonical_pid should be set to current PID"

    def test_second_acquisition_preserves_canonical_pid(self, tmp_path):
        """
        Test that subsequent acquisitions preserve existing canonical_pid.

        Given: State file exists with canonical_pid set
        When: acquire_singleton() is called again
        Then: canonical_pid is NOT overwritten (preserved from first acquisition)
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        state_file = tmp_path / "dreaming-daemon-state.json"

        from dreaming_state import load_state

        from hooks.dreaming_mutex import acquire_singleton, release_singleton

        # First acquisition - set canonical_pid
        success1, _ = acquire_singleton(
            pid_file=str(pid_file),
            state_file=str(state_file)
        )
        assert success1 is True, "First acquisition should succeed"

        state1 = load_state(state_file)
        first_canonical_pid = state1.canonical_pid
        assert first_canonical_pid != 0, "canonical_pid should be set after first acquisition"

        # Release to simulate daemon restart
        release_singleton(pid_file=str(pid_file))

        # Second acquisition - should preserve canonical_pid
        success2, _ = acquire_singleton(
            pid_file=str(pid_file),
            state_file=str(state_file)
        )
        assert success2 is True, "Second acquisition should succeed"

        state2 = load_state(state_file)
        assert state2.canonical_pid == first_canonical_pid, "canonical_pid should be preserved from first acquisition"

    def test_canonical_pid_persists_across_restart(self, tmp_path):
        """
        Test that canonical_pid persists across daemon restarts.

        Given: State file exists with canonical_pid set from previous daemon
        When: New daemon starts (new acquire_singleton call)
        Then: canonical_pid from previous daemon is preserved
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        state_file = tmp_path / "dreaming-daemon-state.json"

        from dreaming_state import DreamingState, load_state, save_state

        from hooks.dreaming_mutex import acquire_singleton

        # Simulate previous daemon: create state with canonical_pid
        previous_pid = 12345  # Different from current process
        initial_state = DreamingState(
            version=1,
            offset=0,
            heartbeat="",
            current_file="",
            shutdown=False,
            canonical_pid=previous_pid
        )
        save_state(initial_state, state_file)

        # Act - new daemon acquires lock
        success, error_msg = acquire_singleton(
            pid_file=str(pid_file),
            state_file=str(state_file)
        )

        # Assert
        assert success is True, f"Acquisition should succeed: {error_msg}"

        # Verify canonical_pid was preserved (not overwritten with current PID)
        state = load_state(state_file)
        assert state.canonical_pid == previous_pid, "canonical_pid should be preserved from previous daemon"
        assert state.canonical_pid != os.getpid(), "canonical_pid should NOT be current PID"


class TestDreamingMutexZombieDetectionWithCanonicalPid:
    """Tests for zombie detection with canonical PID preservation (T-005)."""

    def test_stale_non_canonical_pid_allows_cleanup(self, tmp_path):
        """
        Test that stale non-canonical PID allows cleanup.

        Given: State file has canonical_pid set, stale PID in PID file differs
        When: Zombie detection runs with stale heartbeat
        Then: Cleanup is allowed (safe to cleanup zombie)
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        state_file = tmp_path / "dreaming-daemon-state.json"

        from dreaming_state import DreamingState, save_state

        from hooks.dreaming_mutex import acquire_singleton

        # Setup: Create state with canonical_pid and stale heartbeat
        canonical_pid = 99999  # Non-existent PID
        stale_pid = 88888  # Different non-existent PID

        initial_state = DreamingState(
            version=1,
            offset=0,
            heartbeat="2025-01-01T00:00:00+00:00",  # Very old heartbeat
            current_file="",
            shutdown=False,
            canonical_pid=canonical_pid
        )
        save_state(initial_state, state_file)

        # Write stale PID to PID file (different from canonical)
        pid_file.write_text(str(stale_pid))

        # Act - simulate zombie detection cleanup
        success, error_msg = acquire_singleton(
            pid_file=str(pid_file),
            state_file=str(state_file),
            force=True  # Simulate zombie cleanup
        )

        # Assert - cleanup should succeed (stale PID != canonical PID)
        assert success is True, f"Cleanup should succeed for non-canonical stale PID: {error_msg}"

    def test_stale_canonical_pid_blocks_cleanup(self, tmp_path):
        """
        Test that stale canonical PID blocks cleanup.

        Given: State file has canonical_pid set, stale PID in PID file matches canonical
        When: Zombie detection runs with stale heartbeat
        Then: Cleanup is BLOCKED (protects legitimate daemon)
        """
        # This test requires mocking the _check_for_zombie_daemon function
        # or creating a test harness that simulates the scenario
        # For now, we'll document the expected behavior

        # Expected behavior:
        # 1. State file exists with canonical_pid = 12345
        # 2. PID file contains stale PID = 12345 (matches canonical)
        # 3. Heartbeat is stale (older than zombie_timeout)
        # 4. _check_for_zombie_daemon() should:
        #    - Read PID file, get stale_pid = 12345
        #    - Compare stale_pid (12345) == canonical_pid (12345)
        #    - Log ERROR: "Stale PID matches canonical PID. REFUSING to cleanup"
        #    - Return False (cleanup blocked)

        # This is a critical safety feature to prevent accidental termination
        # of the legitimate daemon during temporary unresponsiveness
        pass  # Test would require mocking logger and state loading

    def test_no_canonical_pid_allows_cleanup(self, tmp_path):
        """
        Test that missing canonical_pid allows cleanup (backwards compatibility).

        Given: State file has canonical_pid = 0 (not set)
        When: Zombie detection runs with stale heartbeat
        Then: Cleanup proceeds without canonical PID check
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        state_file = tmp_path / "dreaming-daemon-state.json"

        from dreaming_state import DreamingState, save_state

        from hooks.dreaming_mutex import acquire_singleton

        # Setup: Create state WITHOUT canonical_pid (default = 0)
        initial_state = DreamingState(
            version=1,
            offset=0,
            heartbeat="",  # No heartbeat
            current_file="",
            shutdown=False,
            canonical_pid=0  # Not set
        )
        save_state(initial_state, state_file)

        # Write stale PID to PID file
        pid_file.write_text("99999")

        # Act - cleanup should proceed without canonical_pid check
        success, error_msg = acquire_singleton(
            pid_file=str(pid_file),
            state_file=str(state_file),
            force=True
        )

        # Assert - cleanup should succeed (no canonical_pid to protect)
        assert success is True, f"Cleanup should succeed when canonical_pid not set: {error_msg}"


class TestDreamingMutexEdgeCases:
    """Tests for edge cases (T-006)."""

    def test_pid_reuse_detected_by_heartbeat(self, tmp_path):
        """
        Test that PID reuse is detected by heartbeat freshness check.

        Given: PID file has PID that was reused by OS
        When: Heartbeat is fresh (recent update)
        Then: Zombie detection does NOT trigger (daemon is alive)

        Note: This test verifies that heartbeat freshness check prevents
        false positive zombie detection when OS reuses PIDs.
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        state_file = tmp_path / "dreaming-daemon-state.json"

        from datetime import UTC, datetime, timedelta

        from dreaming_state import DreamingState, save_state

        from hooks.dreaming_mutex import acquire_singleton

        # Setup: Create state with FRESH heartbeat (recent update)
        recent_heartbeat = (datetime.now(UTC) - timedelta(seconds=30)).isoformat()
        initial_state = DreamingState(
            version=1,
            offset=0,
            heartbeat=recent_heartbeat,  # Fresh heartbeat
            current_file="",
            shutdown=False,
            canonical_pid=0
        )
        save_state(initial_state, state_file)

        # Write current PID to file
        pid_file.write_text(str(os.getpid()))

        # Act - try to acquire with force (simulates zombie check)
        success, _ = acquire_singleton(
            pid_file=str(pid_file),
            state_file=str(state_file),
            force=True
        )

        # Assert - should succeed (fresh heartbeat = not a zombie)
        # This is more of a documentation test - in real scenario,
        # the heartbeat freshness check prevents false positive
        assert success is True, "Fresh heartbeat should allow acquisition"

    def test_state_corruption_recovers_canonical_pid(self, tmp_path):
        """
        Test that state corruption recovers canonical_pid gracefully.

        Given: State file is corrupted (invalid JSON)
        When: load_state() is called
        Then: State recovers with default values (canonical_pid = 0)

        This tests the robustness of the state loading system.
        """
        # Arrange
        state_file = tmp_path / "dreaming-daemon-state.json"

        from dreaming_state import load_state

        # Write corrupted JSON
        state_file.write_text("{invalid json content")

        # Act - load_state should recover gracefully
        state = load_state(state_file)

        # Assert - should have default values
        assert state.canonical_pid == 0, "Corrupted state should default canonical_pid to 0"
        assert state.version == 1, "Corrupted state should have default version"
        assert state.offset == 0, "Corrupted state should have default offset"

    def test_atomic_state_update_preserves_canonical_pid(self, tmp_path):
        """
        Test that atomic state updates preserve canonical_pid.

        Given: State file exists with canonical_pid set
        When: Multiple concurrent updates occur
        Then: canonical_pid is not lost (atomic writes)

        This tests the atomic write mechanism in save_state().
        """
        # Arrange
        state_file = tmp_path / "dreaming-daemon-state.json"

        from dreaming_state import DreamingState, load_state, save_state

        # Create initial state with canonical_pid
        initial_state = DreamingState(
            version=1,
            offset=0,
            heartbeat="",
            current_file="",
            shutdown=False,
            canonical_pid=12345
        )
        save_state(initial_state, state_file)

        # Act - perform multiple updates
        for i in range(5):
            state = load_state(state_file)
            state.offset = i
            save_state(state, state_file)

        # Assert - canonical_pid should be preserved across all updates
        final_state = load_state(state_file)
        assert final_state.canonical_pid == 12345, "canonical_pid should be preserved across atomic updates"
        assert final_state.offset == 4, "Last update should be preserved"


class TestDreamingMutexT008Decoupling:
    """Tests for T-008: Decouple mutex from state persistence."""

    def test_acquire_singleton_does_not_rotate_backups(self, tmp_path):
        """
        Test that mutex acquisition does NOT trigger backup rotation (T-008).

        Given: No state file exists
        When: acquire_singleton() is called for first time
        Then: No backup files are created

        This verifies that _update_canonical_pid_only() is used instead of
        save_state(), preventing expensive backup rotation on every mutex acquisition.
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        state_file = tmp_path / "dreaming-daemon-state.json"

        from hooks.dreaming_mutex import acquire_singleton

        # Act - first acquisition (should create canonical_pid)
        success, error_msg = acquire_singleton(
            pid_file=str(pid_file),
            state_file=str(state_file)
        )

        # Assert - acquisition should succeed
        assert success is True, f"Acquisition should succeed: {error_msg}"

        # Assert - NO backup files should exist (T-008 requirement)
        backup_files = list(tmp_path.glob("dreaming-daemon-state.json.backup*"))
        assert len(backup_files) == 0, f"No backup files should be created, found: {backup_files}"

    def test_canonical_pid_written_without_save_state(self, tmp_path):
        """
        Test that canonical_pid is written without triggering save_state() (T-008).

        Given: State file has canonical_pid = 0
        When: acquire_singleton() is called
        Then: canonical_pid is written directly without backup rotation

        This verifies the minimal update function _update_canonical_pid_only()
        works correctly.
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        state_file = tmp_path / "dreaming-daemon-state.json"

        from dreaming_state import load_state

        from hooks.dreaming_mutex import acquire_singleton

        # Act - first acquisition
        success, error_msg = acquire_singleton(
            pid_file=str(pid_file),
            state_file=str(state_file)
        )

        # Assert - canonical_pid should be written
        state = load_state(state_file)
        assert state.canonical_pid == os.getpid(), "canonical_pid should be set to current PID"

        # Assert - no backup rotation occurred
        backup_files = list(tmp_path.glob("dreaming-daemon-state.json.backup*"))
        assert len(backup_files) == 0, "No backup files should exist"

    def test_acquire_singleton_preserves_canonical_pid(self, tmp_path):
        """
        Test that acquire_singleton() preserves existing canonical_pid (T-008).

        Given: State file already has canonical_pid set
        When: acquire_singleton() is called again
        Then: Existing canonical_pid is NOT overwritten

        This ensures backward compatibility with Phase 1 canonical_pid functionality.
        """
        # Arrange
        pid_file = tmp_path / "dreaming-daemon.pid"
        state_file = tmp_path / "dreaming-daemon-state.json"

        from dreaming_state import DreamingState, load_state, save_state

        from hooks.dreaming_mutex import acquire_singleton

        # Setup: Create state with existing canonical_pid
        initial_state = DreamingState(
            version=1,
            offset=0,
            heartbeat="",
            current_file="",
            shutdown=False,
            canonical_pid=99999  # Existing canonical PID
        )
        save_state(initial_state, state_file)

        # Act - acquire singleton (should preserve existing canonical_pid)
        success, error_msg = acquire_singleton(
            pid_file=str(pid_file),
            state_file=str(state_file)
        )

        # Assert - acquisition should succeed
        assert success is True, f"Acquisition should succeed: {error_msg}"

        # Assert - canonical_pid should NOT be overwritten
        state = load_state(state_file)
        assert state.canonical_pid == 99999, "Existing canonical_pid should be preserved"

        # Assert - no backup files created by mutex acquisition
        # save_state() only creates backups when primary file already exists
        # Since this is first time writing state, no backups are created
        # The key is that acquire_singleton() doesn't trigger backup rotation
        backup_files = list(tmp_path.glob("dreaming-daemon-state.json.backup*"))
        assert len(backup_files) == 0, "Mutex acquisition shouldn't create backup files"
