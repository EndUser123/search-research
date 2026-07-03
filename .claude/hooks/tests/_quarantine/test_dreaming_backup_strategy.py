"""Integration tests for dreaming backup strategy (T-013).

These tests verify end-to-end scenarios with:
- Checksum validation on save/load
- Corruption recovery with backup restoration
- Mutex decoupling from state persistence
- All components working together

Run with: pytest P:/.claude/hooks/tests/test_dreaming_backup_strategy.py -v
"""
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dreaming_mutex import acquire_singleton, release_singleton
from dreaming_state import BACKUP_COUNT, DreamingState, load_state, save_state


class TestBackupStrategyIntegration:
    """Integration tests for complete backup strategy improvements."""

    def test_full_lifecycle_with_checksum_and_backup(self, tmp_path):
        """
        Test full daemon lifecycle with checksum validation and backup rotation.

        Given: Daemon starts, runs, exits, restarts
        When: Full lifecycle with checksum validation and backup rotation
        Then: Checksums validated on every load, corruption detected, backups rotated
        """
        # Arrange: Create state file path in temp directory
        state_file = tmp_path / "dreaming-daemon-state.json"

        # Create initial state with test data
        state = DreamingState(
            version=1,
            offset=100,
            heartbeat=datetime.now(UTC).isoformat(),
            current_file="test.log",
            shutdown=False,
            canonical_pid=1234
        )

        # Act 1: Save state - verify checksum calculated
        save_state(state, state_file)

        # Assert 1: Checksum field populated in saved file
        with open(state_file, encoding='utf-8') as f:
            saved_data = json.load(f)
        assert 'checksum' in saved_data
        assert saved_data['checksum'] != ""
        assert len(saved_data['checksum']) == 64  # SHA256 hex length

        # Act 2: Modify state and save again - verify backup rotated
        state.offset = 200
        state.heartbeat = datetime.now(UTC).isoformat()
        save_state(state, state_file)

        # Assert 2: Backup file created (.json.1)
        backup_1 = state_file.with_suffix('.json.1')
        assert backup_1.exists()

        # Verify backup contains previous state
        with open(backup_1, encoding='utf-8') as f:
            backup_data = json.load(f)
        assert backup_data['offset'] == 100  # Old offset

        # Verify primary has new state
        with open(state_file, encoding='utf-8') as f:
            primary_data = json.load(f)
        assert primary_data['offset'] == 200  # New offset
        assert primary_data['checksum'] != backup_data['checksum']

        # Act 3: Load state - verify checksum validated
        loaded_state = load_state(state_file)

        # Assert 3: State loaded with correct values
        assert loaded_state.offset == 200
        assert loaded_state.checksum == primary_data['checksum']

        # Act 4: Corrupt primary file - load and verify backup restored
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump({"corrupted": "data", "checksum": "bad"}, f)

        # Load should detect corruption and restore from backup
        recovered_state = load_state(state_file)

        # Assert 4: Primary restored from backup
        assert recovered_state.offset == 100  # Restored from backup

        # Verify corrupted file preserved with timestamp suffix
        corrupted_files = list(tmp_path.glob("*.corrupted.*"))
        assert len(corrupted_files) >= 1  # At least one corrupted file preserved

        # Cleanup
        if state_file.exists():
            state_file.unlink()
        if backup_1.exists():
            backup_1.unlink()

    def test_checksum_validation_and_mutex_decoupling(self, tmp_path):
        """
        Test mutex decoupling from state persistence with checksum validation.

        Given: Mutex acquired without triggering backup rotation (T-008)
        When: State saved with checksum validation
        Then: Mutex operations decoupled, checksums validated
        """
        # Arrange: Create state and PID file paths
        state_file = tmp_path / "dreaming-daemon-state.json"
        pid_file = tmp_path / "dreaming-daemon.pid"

        # Mock process check to avoid "already running" errors
        with patch('dreaming_mutex._is_process_running', return_value=False):
            # Act 1: Acquire mutex - should NOT rotate backups
            success, error_msg = acquire_singleton(
                str(pid_file),
                str(state_file),
                force=True
            )

            # Assert 1: Mutex acquired successfully
            assert success, f"Failed to acquire mutex: {error_msg}"
            assert pid_file.exists()

            # Assert 2: No backup files created (mutex decoupling)
            backup_1 = state_file.with_suffix('.json.1')
            assert not backup_1.exists(), "Mutex acquisition should not create backup files"

            # Verify state file created with canonical_pid
            assert state_file.exists()
            loaded_state = load_state(state_file)
            assert loaded_state.canonical_pid == os.getpid()

            # Act 2: Save state with checksum - verify checksum calculated
            test_state = DreamingState(
                version=1,
                offset=50,
                heartbeat=datetime.now(UTC).isoformat(),
                current_file="test2.log",
                shutdown=False,
                canonical_pid=os.getpid()
            )
            save_state(test_state, state_file)

            # Assert 3: Checksum populated in state file
            with open(state_file, encoding='utf-8') as f:
                saved_data = json.load(f)
            assert saved_data['checksum'] != ""
            assert len(saved_data['checksum']) == 64

            # Act 3: Load state - verify checksum validated
            loaded_state = load_state(state_file)

            # Assert 4: Checksum matches and state loaded correctly
            assert loaded_state.checksum == saved_data['checksum']
            assert loaded_state.offset == 50

            # Cleanup: Release mutex
            release_singleton(str(pid_file))

    def test_corruption_recovery_preserves_canonical_pid(self, tmp_path):
        """
        Test that corruption recovery preserves canonical_pid.

        Given: State with canonical_pid set via mutex
        When: Primary file corrupted and recovered from backup
        Then: canonical_pid preserved through recovery
        """
        # Arrange: Create state and PID file paths
        state_file = tmp_path / "dreaming-daemon-state.json"
        pid_file = tmp_path / "dreaming-daemon.pid"
        test_pid = 9999

        # Create initial state with canonical_pid
        state = DreamingState(
            version=1,
            offset=100,
            heartbeat=datetime.now(UTC).isoformat(),
            current_file="test.log",
            shutdown=False,
            canonical_pid=test_pid
        )

        # Act 1: Save state with checksum
        save_state(state, state_file)

        # Assert 1: State saved with checksum and canonical_pid
        with open(state_file, encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data['canonical_pid'] == test_pid
        assert saved_data['checksum'] != ""

        # Act 2: Corrupt primary file (break checksum)
        with open(state_file, 'w', encoding='utf-8') as f:
            # Write valid JSON but with wrong checksum
            corrupted_data = saved_data.copy()
            corrupted_data['offset'] = 999  # Wrong offset
            corrupted_data['checksum'] = "bad_checksum_value_64_chars_xxxxxxxxxxxxxxxx"
            json.dump(corrupted_data, f)

        # Act 3: Load state - should detect corruption and recover from backup
        recovered_state = load_state(state_file)

        # Assert 3: Recovery successful, canonical_pid preserved
        assert recovered_state.canonical_pid == test_pid
        assert recovered_state.offset == 100  # Restored correct value

        # Verify corrupted file preserved
        corrupted_files = list(tmp_path.glob("*.corrupted.*"))
        assert len(corrupted_files) >= 1

    def test_multiple_corruption_recovery_cycles(self, tmp_path):
        """
        Test multiple corruption recovery cycles work correctly.

        Given: State file with backup
        When: Multiple corruption and recovery cycles occur
        Then: Each recovery succeeds from available backups
        """
        # Arrange: Create state file
        state_file = tmp_path / "dreaming-daemon-state.json"

        # Cycle 1: Create initial state
        state1 = DreamingState(
            version=1,
            offset=100,
            heartbeat=datetime.now(UTC).isoformat(),
            current_file="cycle1.log",
            shutdown=False,
            canonical_pid=1111
        )
        save_state(state1, state_file)

        # Verify backup 1 created
        backup_1 = state_file.with_suffix('.json.1')
        assert backup_1.exists()

        # Cycle 2: Corrupt primary, recover from backup
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump({"corrupted": "cycle1"}, f)

        recovered1 = load_state(state_file)
        assert recovered1.offset == 100  # Recovered from backup

        # Cycle 3: Save new state
        state2 = DreamingState(
            version=1,
            offset=200,
            heartbeat=datetime.now(UTC).isoformat(),
            current_file="cycle2.log",
            shutdown=False,
            canonical_pid=2222
        )
        save_state(state2, state_file)

        # Verify new backup contains old state
        with open(backup_1, encoding='utf-8') as f:
            backup_data = json.load(f)
        assert backup_data['offset'] == 100

        # Cycle 4: Corrupt primary again, recover
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump({"corrupted": "cycle2"}, f)

        recovered2 = load_state(state_file)
        assert recovered2.offset == 100  # Still recovered from backup

        # Verify multiple corrupted files preserved
        corrupted_files = list(tmp_path.glob("*.corrupted.*"))
        assert len(corrupted_files) >= 2  # At least 2 corruption cycles

    def test_backup_count_reduction_integration(self, tmp_path):
        """
        Test that backup count reduction (T-007) works end-to-end.

        Given: BACKUP_COUNT=1 (reduced from 3)
        When: State saved multiple times
        Then: Only 1 backup file exists (efficient for 60s heartbeat)
        """
        # Arrange: Create state file
        state_file = tmp_path / "dreaming-daemon-state.json"

        # Assert: BACKUP_COUNT is 1 (T-007 requirement)
        assert BACKUP_COUNT == 1, "BACKUP_COUNT should be 1 for efficient heartbeat interval"

        # Act 1: Save state multiple times
        for i in range(5):
            state = DreamingState(
                version=1,
                offset=i * 100,
                heartbeat=datetime.now(UTC).isoformat(),
                current_file=f"iteration_{i}.log",
                shutdown=False,
                canonical_pid=1000 + i
            )
            save_state(state, state_file)

        # Assert: Only 1 backup file exists (.json.1)
        backup_1 = state_file.with_suffix('.json.1')
        backup_2 = state_file.with_suffix('.json.2')
        backup_3 = state_file.with_suffix('.json.3')

        assert backup_1.exists(), "First backup should exist"
        assert not backup_2.exists(), "Second backup should NOT exist (BACKUP_COUNT=1)"
        assert not backup_3.exists(), "Third backup should NOT exist (BACKUP_COUNT=1)"

        # Verify backup has previous state (not the oldest)
        with open(backup_1, encoding='utf-8') as f:
            backup_data = json.load(f)
        # Should have offset=300 (4th iteration), not offset=0 (first iteration)
        assert backup_data['offset'] == 300

        # Verify primary has latest state
        with open(state_file, encoding='utf-8') as f:
            primary_data = json.load(f)
        assert primary_data['offset'] == 400  # Last iteration
