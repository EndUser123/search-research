"""E2E Workflow Tracker Tests - TDD Approach

Tests for end-to-end workflow tracking via PostToolUse hook.
Following security fixes from SEC-001, SEC-002 and performance from PERF-002.
"""

import json
import os

# Import the hook we're testing
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "hooks"))
from PostToolUse_e2e_tracker import (
    MAX_LOG_RECORDS,
    SESSION_TTL_HOURS,
    _cleanup_expired_sessions,
    _rotate_log_if_needed,
    _validate_session_id,
    _validate_workflow_fields,
    track_workflow,
)


class TestSessionIdValidation:
    """SEC-001: Validate session_id before filename construction"""

    def test_valid_session_id_simple(self):
        """Accept simple alphanumeric session IDs"""
        valid_ids = ["abc123", "session-42", "my_session_2024"]
        for session_id in valid_ids:
            assert _validate_session_id(session_id) == session_id

    def test_valid_session_id_with_uuid_like(self):
        """Accept UUID-like session IDs"""
        valid_ids = ["a1b2c3d4-e5f6-7890-abcd-ef1234567890"]
        for session_id in valid_ids:
            assert _validate_session_id(session_id) == session_id

    def test_reject_path_traversal(self):
        """Reject path traversal attempts (SEC-001)"""
        malicious = ["../../../etc/passwd", "..\\..\\windows", "./.hidden", "/absolute/path"]
        for session_id in malicious:
            with pytest.raises(ValueError, match="Invalid session_id format"):
                _validate_session_id(session_id)

    def test_reject_null_bytes(self):
        """Reject null byte injection attempts"""
        malicious = ["session\x00", "abc\x00def"]
        for session_id in malicious:
            with pytest.raises(ValueError, match="Invalid session_id format"):
                _validate_session_id(session_id)

    def test_reject_special_chars(self):
        """Reject problematic special characters"""
        malicious = ["session<script>", "user;drop table", "file\x1b[0m"]
        for session_id in malicious:
            with pytest.raises(ValueError, match="Invalid session_id format"):
                _validate_session_id(session_id)


class TestWorkflowFieldValidation:
    """SEC-002: Validate all fields before JSONL write"""

    def test_valid_skill_invocation(self):
        """Accept valid skill invocation data"""
        data = {
            "workflow_type": "skill_invocation",
            "target": "commit",
            "stages": [{"stage": "UserPromptSubmit", "status": "passed", "duration_ms": 50}],
            "overall": "success",
        }
        assert _validate_workflow_fields(data) == data

    def test_valid_multi_step_workflow(self):
        """Accept valid multi-step workflow"""
        data = {
            "workflow_type": "multi_step",
            "target": "create and test feature",
            "stages": [
                {"stage": "file_write", "status": "passed", "duration_ms": 100},
                {"stage": "test_run", "status": "passed", "duration_ms": 500},
            ],
            "overall": "success",
        }
        assert _validate_workflow_fields(data) == data

    def test_reject_invalid_workflow_type(self):
        """Reject injection in workflow_type"""
        data = {
            "workflow_type": "skill_invocation<script>",
            "target": "commit",
            "stages": [],
            "overall": "success",
        }
        with pytest.raises(ValueError, match="Invalid workflow_type"):
            _validate_workflow_fields(data)

    def test_reject_invalid_target(self):
        """Reject injection in target field"""
        data = {
            "workflow_type": "skill_invocation",
            "target": "'; DROP TABLE workflows; --",
            "stages": [],
            "overall": "success",
        }
        with pytest.raises(ValueError, match="Invalid target"):
            _validate_workflow_fields(data)

    def test_reject_invalid_stage_name(self):
        """Reject injection in stage names"""
        data = {
            "workflow_type": "multi_step",
            "target": "test",
            "stages": [{"stage": "file'; INSERT", "status": "passed", "duration_ms": 100}],
            "overall": "success",
        }
        with pytest.raises(ValueError, match="Invalid stage name"):
            _validate_workflow_fields(data)

    def test_reject_invalid_stage_status(self):
        """Reject invalid stage status"""
        data = {
            "workflow_type": "multi_step",
            "target": "test",
            "stages": [{"stage": "file_write", "status": "hacked\x00", "duration_ms": 100}],
            "overall": "success",
        }
        with pytest.raises(ValueError, match="Invalid stage status"):
            _validate_workflow_fields(data)


class TestLogRotation:
    """PERF-002: Implement rolling log rotation"""

    def test_rotate_when_max_exceeded(self, tmp_path):
        """Auto-archive when MAX_LOG_RECORDS exceeded"""
        # Setup: Create state dir
        state_dir = tmp_path / ".claude" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Create log file with MAX_LOG_RECORDS + 1 entries
        session_id = "test_rotation"
        log_file = state_dir / f"e2e_executions_{session_id}.jsonl"

        # Write max records + 1
        lines = []
        for i in range(MAX_LOG_RECORDS + 1):
            entry = {
                "ts": datetime.now().isoformat(),
                "workflow_type": "test",
                "target": f"test_{i}",
                "session_id": session_id,
                "terminal_id": "test",
                "stages": [],
                "overall": "success",
            }
            lines.append(json.dumps(entry))
        log_file.write_text("\n".join(lines) + "\n")

        # Trigger rotation
        _rotate_log_if_needed(session_id, state_dir)

        # Verify: Original file rotated to .old
        archived = state_dir / f"e2e_executions_{session_id}.jsonl.old"
        assert archived.exists()

        # Verify: New empty log file created
        assert log_file.exists()
        assert log_file.stat().st_size < 100  # Should be empty or tiny

    def test_no_rotation_under_limit(self, tmp_path):
        """Don't rotate when under MAX_LOG_RECORDS"""
        state_dir = tmp_path / ".claude" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        session_id = "test_no_rotation"
        log_file = state_dir / f"e2e_executions_{session_id}.jsonl"

        # Write under max
        lines = []
        for i in range(MAX_LOG_RECORDS - 1):
            entry = {
                "ts": datetime.now().isoformat(),
                "workflow_type": "test",
                "target": f"test_{i}",
                "session_id": session_id,
                "terminal_id": "test",
                "stages": [],
                "overall": "success",
            }
            lines.append(json.dumps(entry))
        log_file.write_text("\n".join(lines) + "\n")

        # Trigger rotation check
        _rotate_log_if_needed(session_id, state_dir)

        # Verify: No rotation occurred
        archived = state_dir / f"e2e_executions_{session_id}.jsonl.old"
        assert not archived.exists()
        assert log_file.exists()


class TestSessionCleanup:
    """PERF-002: Session TTL cleanup"""

    def test_cleanup_expired_sessions(self, tmp_path):
        """Remove sessions older than SESSION_TTL_HOURS"""
        state_dir = tmp_path / ".claude" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Create expired session file (older than TTL)
        old_time = datetime.now() - timedelta(hours=SESSION_TTL_HOURS + 1)
        old_session = state_dir / "e2e_executions_old_session.jsonl"

        entry = {
            "ts": old_time.isoformat(),
            "workflow_type": "test",
            "target": "expired",
            "session_id": "old_session",
            "terminal_id": "test",
            "stages": [],
            "overall": "success",
        }
        old_session.write_text(json.dumps(entry) + "\n")

        # Set file modification time to old_time
        os.utime(old_session, (old_time.timestamp(), old_time.timestamp()))

        # Create active session file
        active_session = state_dir / "e2e_executions_active_session.jsonl"
        active_entry = {
            "ts": datetime.now().isoformat(),
            "workflow_type": "test",
            "target": "active",
            "session_id": "active_session",
            "terminal_id": "test",
            "stages": [],
            "overall": "success",
        }
        active_session.write_text(json.dumps(active_entry) + "\n")

        # Run cleanup
        _cleanup_expired_sessions(state_dir)

        # Verify: Expired session removed
        assert not old_session.exists()

        # Verify: Active session preserved
        assert active_session.exists()


class TestWorkflowTrackingIntegration:
    """End-to-end workflow tracking tests"""

    def test_track_skill_invocation(self, tmp_path):
        """Track complete skill invocation workflow"""
        state_dir = tmp_path / ".claude" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Track skill execution
        track_workflow(
            workflow_type="skill_invocation",
            target="commit",
            session_id="test_session",
            terminal_id="test_terminal",
            stages=[
                {"stage": "UserPromptSubmit", "status": "passed", "duration_ms": 50},
                {"stage": "skill_execution", "status": "passed", "duration_ms": 200},
                {"stage": "response_generation", "status": "passed", "duration_ms": 100},
            ],
            overall="success",
            state_dir=state_dir,
        )

        # Verify: Log file created
        log_file = state_dir / "e2e_executions_test_session.jsonl"
        assert log_file.exists()

        # Verify: Entry written correctly
        content = log_file.read_text()
        entry = json.loads(content.strip())
        assert entry["workflow_type"] == "skill_invocation"
        assert entry["target"] == "commit"
        assert entry["session_id"] == "test_session"
        assert entry["terminal_id"] == "test_terminal"
        assert len(entry["stages"]) == 3
        assert entry["overall"] == "success"

    def test_track_multi_step_workflow(self, tmp_path):
        """Track multi-step tool workflow"""
        state_dir = tmp_path / ".claude" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Track workflow
        track_workflow(
            workflow_type="multi_step",
            target="create feature",
            session_id="session_abc",
            terminal_id="terminal_123",
            stages=[
                {"stage": "Read", "status": "passed", "duration_ms": 20},
                {"stage": "Edit", "status": "passed", "duration_ms": 50},
                {"stage": "Bash", "status": "passed", "duration_ms": 100},
            ],
            overall="success",
            state_dir=state_dir,
        )

        # Verify
        log_file = state_dir / "e2e_executions_session_abc.jsonl"
        entry = json.loads(log_file.read_text().strip())
        assert entry["workflow_type"] == "multi_step"
        assert entry["target"] == "create feature"
        assert len(entry["stages"]) == 3

    def test_session_isolation(self, tmp_path):
        """Ensure no cross-terminal bleed (PERF-002)"""
        state_dir = tmp_path / ".claude" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Track same workflow in different sessions
        track_workflow(
            workflow_type="skill_invocation",
            target="commit",
            session_id="session_a",
            terminal_id="terminal_1",
            stages=[{"stage": "test", "status": "passed", "duration_ms": 10}],
            overall="success",
            state_dir=state_dir,
        )

        track_workflow(
            workflow_type="skill_invocation",
            target="commit",
            session_id="session_b",
            terminal_id="terminal_2",
            stages=[{"stage": "test", "status": "passed", "duration_ms": 10}],
            overall="success",
            state_dir=state_dir,
        )

        # Verify: Separate log files
        log_a = state_dir / "e2e_executions_session_a.jsonl"
        log_b = state_dir / "e2e_executions_session_b.jsonl"

        assert log_a.exists()
        assert log_b.exists()

        # Verify: No cross-contamination
        entry_a = json.loads(log_a.read_text().strip())
        entry_b = json.loads(log_b.read_text().strip())

        assert entry_a["session_id"] == "session_a"
        assert entry_a["terminal_id"] == "terminal_1"
        assert entry_b["session_id"] == "session_b"
        assert entry_b["terminal_id"] == "terminal_2"

    def test_append_to_existing_log(self, tmp_path):
        """Multiple workflows append to same session log"""
        state_dir = tmp_path / ".claude" / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Track multiple workflows in same session
        for i in range(3):
            track_workflow(
                workflow_type="skill_invocation",
                target=f"operation_{i}",
                session_id="multi_entry_session",
                terminal_id="terminal_x",
                stages=[{"stage": "test", "status": "passed", "duration_ms": 10}],
                overall="success",
                state_dir=state_dir,
            )

        # Verify: All entries in log
        log_file = state_dir / "e2e_executions_multi_entry_session.jsonl"
        lines = log_file.read_text().strip().split("\n")

        assert len(lines) == 3

        # Verify each entry
        for i, line in enumerate(lines):
            entry = json.loads(line)
            assert entry["target"] == f"operation_{i}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
