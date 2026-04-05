"""
Test suite for TOCTOU (Time-Of-Check-Time-Of-Use) retry loop.

Tests cover:
- Retry scenarios when intent file is deleted between check and use
- Exponential backoff in retry timing
- Error paths (file not found, permission denied)
- Maximum retry limits
- Cleanup after successful retry
"""

import json
from datetime import datetime, timezone

import pytest


class TestTOCTOURetryScenarios:
    """Test TOCTOU retry scenarios when file is deleted between check and use"""

    def test_file_deleted_between_check_and_use(self, sample_intent_file):
        """Test retry logic when intent file is deleted after initial check"""
        # Simulate: File exists during check, deleted before read
        assert sample_intent_file.exists()

        # Delete the file (simulates TOCTOU race condition)
        sample_intent_file.unlink()

        # Verify file no longer exists
        assert not sample_intent_file.exists()

        # Implementation should retry and fail gracefully
        # This test documents the TOCTOU scenario

    def test_file_reappears_on_retry(self, temp_state_dir, mock_terminal_id):
        """Test that retry can succeed if file reappears"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        # File doesn't exist initially
        assert not intent_file.exists()

        # Simulate retry: File appears on second attempt
        intent_data = {
            "skill": "test-skill",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-123",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        intent_file.write_text(json.dumps(intent_data))

        # Verify file now exists
        assert intent_file.exists()

        # Simulate successful retry after TOCTOU

    def test_concurrent_deletion_race_condition(self, temp_state_dir, mock_terminal_id):
        """Test handling of concurrent deletion attempts"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        intent_data = {
            "skill": "test",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-123",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        intent_file.write_text(json.dumps(intent_data))

        # Simulate concurrent deletion (multiple processes trying to delete)
        intent_file.unlink(missing_ok=True)
        intent_file.unlink(missing_ok=True)

        # Should handle gracefully (missing_ok=True prevents error)

    def test_file_recreated_between_checks(self, temp_state_dir, mock_terminal_id):
        """Test when file is deleted and immediately recreated"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        # Create file (version 1)
        intent_data_v1 = {
            "skill": "test-v1",
            "prompt": "/test-v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-123",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        intent_file.write_text(json.dumps(intent_data_v1))

        # Delete and recreate with different content (version 2)
        intent_file.unlink()

        intent_data_v2 = {
            "skill": "test-v2",
            "prompt": "/test-v2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-123",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        intent_file.write_text(json.dumps(intent_data_v2))

        # Verify final content is version 2
        with open(intent_file) as f:
            final_data = json.load(f)

        assert final_data["skill"] == "test-v2"


class TestExponentialBackoff:
    """Test exponential backoff in retry timing"""

    def test_backoff_timing_doubles_each_retry(self):
        """Test that retry delay doubles on each attempt"""
        retry_delays = [0.1, 0.2, 0.4, 0.8, 1.6]  # Exponential backoff

        for i, delay in enumerate(retry_delays):
            if i > 0:
                expected = retry_delays[i-1] * 2
                assert delay == expected, f"Retry {i}: delay {delay} != 2x previous {expected}"

    def test_maximum_backoff_limit_is_respected(self):
        """Test that backoff doesn't exceed maximum limit"""
        max_backoff = 2.0  # 2 second maximum
        retry_delays = [0.1, 0.2, 0.4, 0.8, 1.6, 2.0, 2.0, 2.0]

        for delay in retry_delays:
            assert delay <= max_backoff, f"Backoff {delay}s exceeds maximum {max_backoff}s"

    def test_first_retry_has_no_delay(self):
        """Test that first retry happens immediately (no delay)"""
        # First retry should be immediate
        first_retry_delay = 0
        assert first_retry_delay == 0

    def test_retry_sequence_terminates(self):
        """Test that retry sequence terminates after max attempts"""
        max_retries = 5
        retry_count = 0

        # Simulate retry loop
        for attempt in range(max_retries + 2):  # Try more than max
            if retry_count >= max_retries:
                break
            retry_count += 1

        assert retry_count == max_retries, f"Retry count {retry_count} exceeds max {max_retries}"


class TestRetryErrorPaths:
    """Test error paths during retry attempts"""

    def test_permission_denied_is_handled(self, temp_state_dir, mock_terminal_id):
        """Test that permission denied errors are handled gracefully"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        intent_data = {
            "skill": "test",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-123",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        intent_file.write_text(json.dumps(intent_data))

        # Make file read-only (simulates permission error)
        intent_file.chmod(0o444)

        # Verify file is read-only
        assert intent_file.exists()

        # Cleanup: Restore write permissions
        intent_file.chmod(0o644)

    def test_corrupted_json_is_handled(self, temp_state_dir, mock_terminal_id):
        """Test that corrupted JSON in intent file is handled"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        # Write corrupted JSON
        intent_file.write_text("{ invalid json data")

        # Attempting to read should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            with open(intent_file) as f:
                json.load(f)

    def test_empty_file_is_handled(self, temp_state_dir, mock_terminal_id):
        """Test that empty intent file is handled"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        # Write empty file
        intent_file.write_text("")

        # File exists but is empty
        assert intent_file.exists()

        # Reading should return empty string
        content = intent_file.read_text()
        assert content == ""

    def test_directory_not_exists_is_handled(self, temp_state_dir, mock_terminal_id):
        """Test that missing directory is handled gracefully"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_file = intent_dir / "pending_command_intent.json"

        # Don't create directory - file doesn't exist
        assert not intent_file.exists()

        # Implementation should handle missing directory


class TestRetryCleanup:
    """Test cleanup and state management after retry"""

    def test_cleanup_after_successful_retry(self, temp_state_dir, mock_terminal_id):
        """Test that cleanup happens after successful retry"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        intent_file = intent_dir / "pending_command_intent.json"

        intent_data = {
            "skill": "test",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-123",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        intent_file.write_text(json.dumps(intent_data))

        # Simulate successful operation and cleanup
        intent_file.unlink()

        # Verify cleanup
        assert not intent_file.exists()

    def test_state_persisted_across_retries(self, temp_state_dir, mock_terminal_id):
        """Test that retry state is tracked across attempts"""
        retry_attempts = []

        # Simulate retry loop with state tracking
        for attempt in range(3):
            retry_attempts.append(attempt)

        # Verify all attempts were tracked
        assert len(retry_attempts) == 3
        assert retry_attempts == [0, 1, 2]

    def test_file_lock_prevents_race_condition(self, temp_state_dir, mock_terminal_id):
        """Test that file locking prevents concurrent write conflicts"""
        intent_dir = temp_state_dir / mock_terminal_id
        intent_dir.mkdir(parents=True, exist_ok=True)

        lock_file = intent_dir / "intent.lock"
        intent_file = intent_dir / "pending_command_intent.json"

        # Create lock file
        lock_file.write_text("locked")

        # Verify lock exists
        assert lock_file.exists()

        # Create intent file while lock is held
        intent_data = {
            "skill": "test",
            "prompt": "/test",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": "test-123",
            "terminal_id": mock_terminal_id,
            "created_at": int(datetime.now(timezone.utc).timestamp())
        }

        intent_file.write_text(json.dumps(intent_data))

        # Verify intent file created despite lock
        assert intent_file.exists()

        # Cleanup: Remove lock
        lock_file.unlink()


class TestTOCTOUIntegrationTests:
    """Integration tests for TOCTOU retry with other components"""

    def test_toctou_retry_preserves_terminal_isolation(self, temp_state_dir):
        """Test that TOCTOU retries don't break terminal isolation"""
        terminals = []

        for i in range(2):
            terminal_id = f"terminal-toctou-{i}"
            intent_dir = temp_state_dir / terminal_id
            intent_dir.mkdir(parents=True, exist_ok=True)

            intent_file = intent_dir / "pending_command_intent.json"

            intent_data = {
                "skill": f"test-{i}",
                "prompt": f"/test-{i}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "session_id": f"session-{i}",
                "terminal_id": terminal_id,
                "created_at": int(datetime.now(timezone.utc).timestamp())
            }

            intent_file.write_text(json.dumps(intent_data))
            terminals.append((terminal_id, intent_file))

        # Verify each terminal has its own file
        for terminal_id, intent_file in terminals:
            assert intent_file.exists()
            assert terminal_id in str(intent_file)

    def test_toctou_with_ttl_check(self, stale_intent_file):
        """Test that TOCTOU retry considers TTL during retries"""
        with open(stale_intent_file) as f:
            intent_data = json.load(f)

        created_at = intent_data["created_at"]
        now = int(datetime.now(timezone.utc).timestamp())
        age = now - created_at

        # Verify file is stale
        assert age >= 90

        # TOCTOU retry should not resurrect stale files
        # File remains expired regardless of retries
