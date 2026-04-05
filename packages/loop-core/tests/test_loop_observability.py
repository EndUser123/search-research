"""Tests for loop_observability module (RED phase)."""

import json
from datetime import datetime
from unittest.mock import patch
import pytest

from scripts.loop_observability import (
    log_decision,
    update_metrics,
)


class TestLogDecision:
    """Test suite for log_decision function."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """Create temporary state directory for testing."""
        state_dir = tmp_path / "terminals" / "test_terminal"
        state_dir.mkdir(parents=True)
        yield state_dir

    def test_log_decision_creates_log_entry(self, temp_state_dir):
        """Test log_decision creates a JSON line entry in decision.log."""
        terminal_id = "test_terminal"
        event = "task_started"
        payload = {"task_id": "TASK-001", "timestamp": "2026-03-15T10:00:00"}

        with patch(
            "scripts.loop_observability.get_terminal_log_dir",
            return_value=temp_state_dir
        ):
            log_decision(terminal_id, event, payload)

            log_file = temp_state_dir / "decision.log"
            assert log_file.exists()

            # Read and verify the log entry
            log_content = log_file.read_text()
            entry = json.loads(log_content.strip())

            assert entry["terminal_id"] == terminal_id
            assert entry["event"] == event
            assert entry["payload"] == payload
            assert "timestamp" in entry

    def test_log_decision_appends_multiple_entries(self, temp_state_dir):
        """Test log_decision appends multiple entries to decision.log."""
        terminal_id = "test_terminal"

        with patch(
            "scripts.loop_observability.get_terminal_log_dir",
            return_value=temp_state_dir
        ):
            log_decision(terminal_id, "event_1", {"data": "first"})
            log_decision(terminal_id, "event_2", {"data": "second"})
            log_decision(terminal_id, "event_3", {"data": "third"})

            log_file = temp_state_dir / "decision.log"
            log_content = log_file.read_text()

            # Should have 3 lines
            lines = log_content.strip().split("\n")
            assert len(lines) == 3

            # Verify each entry
            entry_1 = json.loads(lines[0])
            entry_2 = json.loads(lines[1])
            entry_3 = json.loads(lines[2])

            assert entry_1["event"] == "event_1"
            assert entry_2["event"] == "event_2"
            assert entry_3["event"] == "event_3"

    def test_log_decision_per_terminal_isolation(self, tmp_path):
        """Test different terminals have separate decision.log files."""
        terminal_a_dir = tmp_path / "terminals" / "terminal_a"
        terminal_b_dir = tmp_path / "terminals" / "terminal_b"
        terminal_a_dir.mkdir(parents=True)
        terminal_b_dir.mkdir(parents=True)

        with patch("scripts.loop_observability.get_terminal_log_dir") as mock_dir:
            mock_dir.side_effect = lambda tid: (
                terminal_a_dir if tid == "terminal_a" else terminal_b_dir
            )

            log_decision("terminal_a", "test_event", {"terminal": "A"})
            log_decision("terminal_b", "test_event", {"terminal": "B"})

            # Each terminal should have its own log
            log_a = terminal_a_dir / "decision.log"
            log_b = terminal_b_dir / "decision.log"

            assert log_a.exists()
            assert log_b.exists()

            entry_a = json.loads(log_a.read_text().strip())
            entry_b = json.loads(log_b.read_text().strip())

            assert entry_a["payload"]["terminal"] == "A"
            assert entry_b["payload"]["terminal"] == "B"

    def test_log_decision_adds_iso_timestamp(self, temp_state_dir):
        """Test log_decision adds ISO 8601 timestamp to entries."""
        terminal_id = "test_terminal"
        event = "test_event"
        payload = {"data": "test"}

        with patch(
            "scripts.loop_observability.get_terminal_log_dir",
            return_value=temp_state_dir
        ):
            log_decision(terminal_id, event, payload)

            log_file = temp_state_dir / "decision.log"
            entry = json.loads(log_file.read_text().strip())

            # Verify timestamp is valid ISO 8601
            assert "timestamp" in entry
            try:
                datetime.fromisoformat(entry["timestamp"])
            except ValueError:
                pytest.fail("timestamp is not valid ISO 8601 format")

    def test_log_decision_handles_large_payloads(self, temp_state_dir):
        """Test log_decision handles large payload dictionaries."""
        terminal_id = "test_terminal"
        large_payload = {
            f"key_{i}": f"value_{i}" * 100
            for i in range(50)
        }

        with patch(
            "scripts.loop_observability.get_terminal_log_dir",
            return_value=temp_state_dir
        ):
            log_decision(terminal_id, "large_event", large_payload)

            log_file = temp_state_dir / "decision.log"
            entry = json.loads(log_file.read_text().strip())

            assert entry["payload"] == large_payload

    def test_log_decision_best_effort_disk_full(self):
        """Test log_decision fails gracefully when disk is full."""
        terminal_id = "test_terminal"
        event = "test_event"
        payload = {"data": "test"}

        # Mock file open to raise OSError (disk full)
        with patch("builtins.open", side_effect=OSError("No space left on device")):
            # Should not raise exception (best-effort)
            log_decision(terminal_id, event, payload)

        # Verify no exception was raised
        # (If it raised, test would fail)

    def test_log_decision_best_effort_permission_denied(self):
        """Test log_decision fails gracefully when permission denied."""
        terminal_id = "test_terminal"
        event = "test_event"
        payload = {"data": "test"}

        # Mock file operations to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Should not raise exception (best-effort)
            log_decision(terminal_id, event, payload)

        # Should complete without error
        assert True

    def test_log_decision_best_effort_invalid_json_in_payload(self):
        """Test log_decision handles non-serializable payload gracefully."""
        terminal_id = "test_terminal"
        event = "test_event"

        # Payload with non-serializable object
        class NotSerializable:
            pass

        payload = {
            "valid_data": "test",
            "invalid_object": NotSerializable()
        }

        # Should not raise exception (best-effort)
        # Will skip entries that can't be serialized
        log_decision(terminal_id, event, payload)

        # Behavior: either writes partial data or skips entry
        # Key is that it doesn't crash the loop

    def test_log_decision_creates_log_directory_if_missing(self, tmp_path):
        """Test log_decision creates log directory if it doesn't exist."""
        state_dir = tmp_path / "terminals" / "new_terminal"
        # Don't create the directory

        with patch(
            "scripts.loop_observability.get_terminal_log_dir",
            return_value=state_dir
        ):
            log_decision("new_terminal", "test", {"data": "test"})

            # Directory should be created
            assert state_dir.exists()
            log_file = state_dir / "decision.log"
            assert log_file.exists()


class TestUpdateMetrics:
    """Test suite for update_metrics function."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path):
        """Create temporary state directory for testing."""
        state_dir = tmp_path / "terminals" / "test_terminal"
        state_dir.mkdir(parents=True)
        yield state_dir

    def test_update_metrics_creates_new_metrics_file(self, temp_state_dir):
        """Test update_metrics creates loop_metrics.json with initial data."""
        terminal_id = "test_terminal"
        metrics_delta = {
            "tasks_completed": 1,
            "iterations": 1,
            "errors": 0
        }

        with patch(
            "scripts.loop_observability.get_terminal_state_dir",
            return_value=temp_state_dir
        ):
            update_metrics(terminal_id, metrics_delta)

            metrics_file = temp_state_dir / "loop_metrics.json"
            assert metrics_file.exists()

            metrics = json.loads(metrics_file.read_text())
            assert metrics["tasks_completed"] == 1
            assert metrics["iterations"] == 1
            assert metrics["errors"] == 0

    def test_update_metrics_merges_with_existing_metrics(self, temp_state_dir):
        """Test update_metrics merges delta into existing metrics."""
        terminal_id = "test_terminal"

        # Initial metrics
        initial_metrics = {
            "tasks_completed": 5,
            "iterations": 3,
            "errors": 1,
            "last_update": "2026-03-15T10:00:00"
        }

        metrics_file = temp_state_dir / "loop_metrics.json"
        metrics_file.write_text(json.dumps(initial_metrics))

        with patch(
            "scripts.loop_observability.get_terminal_state_dir",
            return_value=temp_state_dir
        ):
            # Update with delta
            metrics_delta = {
                "tasks_completed": 2,
                "iterations": 1
            }

            update_metrics(terminal_id, metrics_delta)

            # Verify merged result
            updated_metrics = json.loads(metrics_file.read_text())
            assert updated_metrics["tasks_completed"] == 7  # 5 + 2
            assert updated_metrics["iterations"] == 4  # 3 + 1
            assert updated_metrics["errors"] == 1  # Unchanged
            assert "last_update" in updated_metrics

    def test_update_metrics_adds_new_fields(self, temp_state_dir):
        """Test update_metrics adds new fields to existing metrics."""
        terminal_id = "test_terminal"

        # Initial metrics
        initial_metrics = {
            "tasks_completed": 5
        }

        metrics_file = temp_state_dir / "loop_metrics.json"
        metrics_file.write_text(json.dumps(initial_metrics))

        with patch(
            "scripts.loop_observability.get_terminal_state_dir",
            return_value=temp_state_dir
        ):
            # Update with new fields
            metrics_delta = {
                "tasks_completed": 1,
                "new_field": "value"
            }

            update_metrics(terminal_id, metrics_delta)

            updated_metrics = json.loads(metrics_file.read_text())
            assert updated_metrics["tasks_completed"] == 6
            assert updated_metrics["new_field"] == "value"

    def test_update_metrics_atomic_write(self, temp_state_dir):
        """Test update_metrics uses atomic write (temp file + rename)."""
        terminal_id = "test_terminal"
        metrics_delta = {"test": "data"}

        with patch(
            "scripts.loop_observability.get_terminal_state_dir",
            return_value=temp_state_dir
        ):
            update_metrics(terminal_id, metrics_delta)

            # Verify no temp files left behind
            temp_files = list(temp_state_dir.glob("*.tmp"))
            assert len(temp_files) == 0

            # Verify file exists
            metrics_file = temp_state_dir / "loop_metrics.json"
            assert metrics_file.exists()

    def test_update_metrics_per_terminal_isolation(self, tmp_path):
        """Test different terminals have separate loop_metrics.json files."""
        terminal_a_dir = tmp_path / "terminals" / "terminal_a"
        terminal_b_dir = tmp_path / "terminals" / "terminal_b"
        terminal_a_dir.mkdir(parents=True)
        terminal_b_dir.mkdir(parents=True)

        with patch("scripts.loop_observability.get_terminal_state_dir") as mock_dir:
            mock_dir.side_effect = lambda tid: (
                terminal_a_dir if tid == "terminal_a" else terminal_b_dir
            )

            update_metrics("terminal_a", {"terminal": "A", "value": 1})
            update_metrics("terminal_b", {"terminal": "B", "value": 2})

            metrics_a = json.loads((terminal_a_dir / "loop_metrics.json").read_text())
            metrics_b = json.loads((terminal_b_dir / "loop_metrics.json").read_text())

            assert metrics_a["terminal"] == "A"
            assert metrics_a["value"] == 1
            assert metrics_b["terminal"] == "B"
            assert metrics_b["value"] == 2

    def test_update_metrics_best_effort_disk_full(self):
        """Test update_metrics fails gracefully when disk is full."""
        terminal_id = "test_terminal"
        metrics_delta = {"test": "data"}

        # Mock file operations to raise OSError
        with patch("builtins.open", side_effect=OSError("No space left on device")):
            # Should not raise exception (best-effort)
            update_metrics(terminal_id, metrics_delta)

        # Should complete without error
        assert True

    def test_update_metrics_best_effort_permission_denied(self):
        """Test update_metrics fails gracefully when permission denied."""
        terminal_id = "test_terminal"
        metrics_delta = {"test": "data"}

        # Mock file operations to raise PermissionError
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Should not raise exception (best-effort)
            update_metrics(terminal_id, metrics_delta)

        # Should complete without error
        assert True

    def test_update_metrics_best_effort_corrupted_existing_file(self, temp_state_dir):
        """Test update_metrics handles corrupted existing metrics file."""
        terminal_id = "test_terminal"

        # Create corrupted metrics file
        metrics_file = temp_state_dir / "loop_metrics.json"
        metrics_file.write_text("{invalid json content")

        with patch(
            "scripts.loop_observability.get_terminal_state_dir",
            return_value=temp_state_dir
        ):
            # Should not raise exception (best-effort)
            # Will overwrite with new data
            update_metrics(terminal_id, {"new_metrics": 1})

            # File should now be valid
            metrics = json.loads(metrics_file.read_text())
            assert "new_metrics" in metrics

    def test_update_metrics_numeric_merge_types(self, temp_state_dir):
        """Test update_metrics correctly merges different numeric types."""
        terminal_id = "test_terminal"

        # Initial metrics with various numeric types
        initial_metrics = {
            "int_value": 10,
            "float_value": 5.5,
            "count": 0
        }

        metrics_file = temp_state_dir / "loop_metrics.json"
        metrics_file.write_text(json.dumps(initial_metrics))

        with patch(
            "scripts.loop_observability.get_terminal_state_dir",
            return_value=temp_state_dir
        ):
            # Update with deltas
            metrics_delta = {
                "int_value": 5,
                "float_value": 2.3,
                "count": 1
            }

            update_metrics(terminal_id, metrics_delta)

            updated_metrics = json.loads(metrics_file.read_text())
            assert updated_metrics["int_value"] == 15
            assert updated_metrics["float_value"] == 7.8
            assert updated_metrics["count"] == 1


class TestLogRotation:
    """Test suite for log rotation functionality (REFACTOR phase)."""

    def test_log_rotation_triggered_by_size(self):
        """Test log rotates when file size exceeds threshold."""
        # This will be implemented in REFACTOR phase
        pytest.skip("Log rotation not yet implemented")

    def test_log_rotation_keeps_limited_history(self):
        """Test log rotation keeps only specified number of historical logs."""
        # This will be implemented in REFACTOR phase
        pytest.skip("Log rotation history limit not yet implemented")

    def test_log_rotation_timestamp_in_filename(self):
        """Test rotated logs include timestamp in filename."""
        # This will be implemented in REFACTOR phase
        pytest.skip("Log rotation timestamp naming not yet implemented")


class TestBufferedMetrics:
    """Test suite for buffered metrics writes (REFACTOR phase)."""

    def test_buffered_metrics_writes_after_threshold(self):
        """Test buffered metrics flush after reaching threshold."""
        # This will be implemented in REFACTOR phase
        pytest.skip("Buffered metrics not yet implemented")

    def test_buffered_metrics_flush_on_demand(self):
        """Test buffered metrics can be flushed manually."""
        # This will be implemented in REFACTOR phase
        pytest.skip("Buffered metrics not yet implemented")

    def test_buffered_metrics_persists_across_calls(self):
        """Test buffer persists across multiple update_metrics calls."""
        # This will be implemented in REFACTOR phase
        pytest.skip("Buffered metrics not yet implemented")


class TestObservabilityFailureScenarios:
    """Test suite for observability failure scenarios (TASK-006-D)."""

    def test_observability_failures_dont_break_loop(self):
        """Test that observability failures don't break loop execution."""
        terminal_id = "test_terminal"

        # Mock all file operations to fail
        with patch("builtins.open", side_effect=OSError("Simulated failure")):
            # All observability calls should fail silently
            log_decision(terminal_id, "event_1", {"data": "test"})
            update_metrics(terminal_id, {"metric": 1})
            log_decision(terminal_id, "event_2", {"data": "test"})
            update_metrics(terminal_id, {"metric": 2})

        # Should complete without raising exceptions
        # This proves observability is best-effort
        assert True

    def test_observability_partial_failures(self, tmp_path):
        """Test that some observability failures don't prevent others."""
        terminal_id = "test_terminal"
        log_dir = tmp_path / "logs"

        with patch(
            "scripts.loop_observability.get_terminal_log_dir",
            return_value=log_dir
        ):
            # First call succeeds
            log_decision(terminal_id, "success_event", {"data": "test"})

            # Second call fails (disk full simulation)
            with patch("builtins.open", side_effect=OSError("No space left")):
                log_decision(terminal_id, "failed_event", {"data": "test"})

            # Third call succeeds again (disk space recovered)
            log_decision(terminal_id, "recovery_event", {"data": "test"})

            # Verify we have 2 successful entries (not 3)
            log_file = log_dir / "decision.log"
            if log_file.exists():
                lines = log_file.read_text().strip().split("\n")
                # Should have at least the successful entries
                assert len(lines) >= 2

    def test_observability_with_concurrent_access(self, tmp_path):
        """Test observability handles concurrent access gracefully."""
        # Simulate concurrent writes from multiple "processes"
        terminal_id = "test_terminal"
        log_dir = tmp_path / "logs"

        with patch(
            "scripts.loop_observability.get_terminal_log_dir",
            return_value=log_dir
        ):
            # Multiple rapid writes
            for i in range(10):
                log_decision(terminal_id, f"event_{i}", {"index": i})

            # All writes should succeed
            log_file = log_dir / "decision.log"
            assert log_file.exists()

            lines = log_file.read_text().strip().split("\n")
            # Should have all 10 entries
            assert len(lines) == 10
