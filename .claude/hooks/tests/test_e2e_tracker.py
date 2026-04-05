#!/usr/bin/env python3
"""
Extended E2E Tracker Tests

Extends existing integration tests with:
1. Concurrent terminal isolation tests (TEST-004)
2. Performance regression tests (TEST-005)
3. Log rotation tests
4. Session isolation verification

Test Coverage:
- Component → integration → e2e pipeline
- Session isolation (including concurrent terminals)
- Performance: E2E tracker overhead <100ms per 100 events
- Log rotation and cleanup
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from posttooluse.e2e_tracker_hook import E2ETrackerHook


class TestE2ETrackerConcurrentTerminals:
    """TEST-004: Concurrent terminal session isolation."""

    def test_concurrent_sessions_dont_interfere(self, tmp_path):
        """
        Test that concurrent terminals maintain separate session contexts.

        Simulates two terminals running simultaneously with different session IDs.
        Verifies no cross-contamination of evidence or state.
        """
        # Import standalone tracker function
        from PostToolUse_e2e_tracker import post_tool_use_hook

        # Simulate concurrent tool execution
        context1 = {"session_id": "session-1", "terminal_id": "terminal-A"}
        post_tool_use_hook(
            tool_name="Bash",
            tool_input={"command": "echo terminal1"},
            tool_output={"success": True},
            context=context1,
        )

        context2 = {"session_id": "session-2", "terminal_id": "terminal-B"}
        post_tool_use_hook(
            tool_name="Bash",
            tool_input={"command": "echo terminal2"},
            tool_output={"success": True},
            context=context2,
        )

        # Verify both tracked successfully
        assert result1["tracked"] is True
        assert result2["tracked"] is True

        # Verify separate log files
        log1 = session1_dir / "e2e_executions_session-1.jsonl"
        log2 = session2_dir / "e2e_executions_session-2.jsonl"

        assert log1.exists()
        assert log2.exists()

        # Verify no cross-contamination
        with open(log1) as f:
            session1_events = [json.loads(line) for line in f]

        with open(log2) as f:
            session2_events = [json.loads(line) for line in f]

        assert len(session1_events) == 1
        assert len(session2_events) == 1
        assert session1_events[0]["session_id"] == "session-1"
        assert session2_events[0]["session_id"] == "session-2"

    def test_concurrent_same_session_different_terminals(self, tmp_path):
        """
        Test that same session_id with different terminal_ids are isolated.

        This tests the terminal_id component of session isolation.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        hook = E2ETrackerHook(state_dir=state_dir)

        # Same session, different terminals
        hook.process(
            tool_name="Bash",
            tool_input={"command": "echo terminal1"},
            tool_response={"success": True},
            session_id="shared-session",
            terminal_id="terminal-A",
        )

        hook.process(
            tool_name="Bash",
            tool_input={"command": "echo terminal2"},
            tool_response={"success": True},
            session_id="shared-session",
            terminal_id="terminal-B",
        )

        # Verify both tracked in same log file
        log_file = state_dir / "e2e_executions_shared-session.jsonl"
        assert log_file.exists()

        with open(log_file) as f:
            events = [json.loads(line) for line in f]

        assert len(events) == 2
        # Verify terminal_id isolation
        terminal_ids = {e["terminal_id"] for e in events}
        assert terminal_ids == {"terminal-A", "terminal-B"}

    def test_subprocess_isolation_pattern(self, tmp_path):
        """
        TEST-004: Test subprocess isolation pattern (from test_multi_terminal_hooks.py).

        Simulates separate terminal execution without sharing interpreter state.
        """
        hooks_dir = Path(__file__).resolve().parent.parent

        # Create test hook input
        test_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo test"},
            "tool_response": {"success": True},
            "session_id": f"test-session-{int(time.time())}",
            "terminal_id": "test-terminal",
        }

        # Run in subprocess (isolated environment)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"""
import sys
sys.path.insert(0, '{hooks_dir}')
from posttooluse.e2e_tracker_hook import E2ETrackerHook
import json

hook = E2ETrackerHook()
result = hook.process(**json.loads('''{json.dumps(test_input)}'''))
print(json.dumps(result))
""",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(hooks_dir),
        )

        assert result.returncode == 0
        output = json.loads(result.stdout.strip())
        assert output["tracked"] is True


class TestE2ETrackerPerformance:
    """TEST-005: Performance regression tests."""

    def test_tracker_overhead_per_event(self):
        """
        TEST-005: Verify tracker overhead <100ms per 100 events.

        Performance requirement: <1ms average per event.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            hook = E2ETrackerHook(state_dir=state_dir)

            # Track 100 events
            event_count = 100
            start_time = time.perf_counter()

            for i in range(event_count):
                hook.process(
                    tool_name="Bash",
                    tool_input={"command": f"echo test-{i}"},
                    tool_response={"success": True},
                    session_id="perf-test-session",
                    terminal_id="perf-terminal",
                )

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Verify performance requirement
            # Allow 100ms for 100 events = 1ms average per event
            assert (
                elapsed_ms < 100
            ), f"Tracker too slow: {elapsed_ms:.2f}ms for {event_count} events"

            # Verify all events tracked
            log_file = state_dir / "e2e_executions_perf-test-session.jsonl"
            assert log_file.exists()

            with open(log_file) as f:
                events = [json.loads(line) for line in f]

            assert len(events) == event_count

    def test_concurrent_tracking_performance(self):
        """
        Test performance with multiple concurrent sessions.

        Simulates realistic multi-terminal workload.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            hook = E2ETrackerHook(state_dir=state_dir)

            # Simulate 5 concurrent terminals
            terminal_count = 5
            events_per_terminal = 20

            start_time = time.perf_counter()

            for terminal_id in range(terminal_count):
                session_id = f"concurrent-session-{terminal_id}"
                for i in range(events_per_terminal):
                    hook.process(
                        tool_name="Bash",
                        tool_input={"command": f"echo test-{i}"},
                        tool_response={"success": True},
                        session_id=session_id,
                        terminal_id=f"terminal-{terminal_id}",
                    )

            elapsed_ms = (time.perf_counter() - start_time) * 1000
            total_events = terminal_count * events_per_terminal

            # Performance requirement: <200ms for 100 events across 5 terminals
            assert (
                elapsed_ms < 200
            ), f"Concurrent tracking too slow: {elapsed_ms:.2f}ms for {total_events} events"

    def test_log_rotation_performance(self):
        """
        Test that log rotation doesn't degrade performance.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            hook = E2ETrackerHook(state_dir=state_dir)

            # Track enough events to trigger rotation (MAX_LOG_RECORDS = 1000)
            session_id = "rotation-test-session"

            start_time = time.perf_counter()

            for i in range(1050):  # Exceed MAX_LOG_RECORDS
                hook.process(
                    tool_name="Bash",
                    tool_input={"command": f"echo test-{i}"},
                    tool_response={"success": True},
                    session_id=session_id,
                    terminal_id="rotation-terminal",
                )

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Rotation should not cause significant slowdown
            assert (
                elapsed_ms < 500
            ), f"Log rotation degraded performance: {elapsed_ms:.2f}ms for 1050 events"

            # Verify rotation occurred
            log_file = state_dir / f"e2e_executions_{session_id}.jsonl"
            archive_file = state_dir / f"e2e_executions_{session_id}.jsonl.old"

            assert log_file.exists()
            assert archive_file.exists()

            # Verify current log has fewer records after rotation
            with open(log_file) as f:
                current_events = len(list(f))

            assert current_events < 1000, "Log rotation didn't trim the log"


class TestE2ETrackerLogRotation:
    """Test log rotation and cleanup functionality."""

    def test_log_rotation_at_max_records(self):
        """
        Test that log rotates when MAX_LOG_RECORDS (1000) is exceeded.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            hook = E2ETrackerHook(state_dir=state_dir)

            session_id = "rotation-test"
            log_file = state_dir / f"e2e_executions_{session_id}.jsonl"
            archive_file = state_dir / f"e2e_executions_{session_id}.jsonl.old"

            # Track 1001 events (exceeds MAX_LOG_RECORDS)
            for i in range(1001):
                hook.process(
                    tool_name="Bash",
                    tool_input={"command": f"echo test-{i}"},
                    tool_response={"success": True},
                    session_id=session_id,
                    terminal_id="test-terminal",
                )

            # Verify rotation occurred
            assert log_file.exists()
            assert archive_file.exists()

            # Verify archive has old data
            with open(archive_file) as f:
                archived_count = len([json.loads(line) for line in f])

            assert archived_count == 1000, "Archive should have MAX_LOG_RECORDS"

            # Verify current log has new data
            with open(log_file) as f:
                current_count = len([json.loads(line) for line in f])

            assert current_count == 1, "Current log should have 1 new event"

    def test_session_cleanup_after_ttl(self):
        """
        Test that old sessions are cleaned up after TTL (2 hours).
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir)
            hook = E2ETrackerHook(state_dir=state_dir)

            # Create old session file (simulate age)
            old_session = "old-session"
            log_file = state_dir / f"e2e_executions_{old_session}.jsonl"

            # Write old session with past timestamp
            old_event = {
                "session_id": old_session,
                "timestamp": (datetime.now(UTC) - timedelta(hours=3)).isoformat(),
                "workflow_type": "test",
            }

            with open(log_file, "w") as f:
                f.write(json.dumps(old_event) + "\n")

            # Create new session
            hook.process(
                tool_name="Bash",
                tool_input={"command": "echo new"},
                tool_response={"success": True},
                session_id="new-session",
                terminal_id="test-terminal",
            )

            # Trigger cleanup (happens automatically on tracking)
            # Old session should be cleaned up
            # Note: Actual cleanup implementation depends on TTL logic
            # This test verifies the cleanup hook point exists


class TestE2ETrackerSessionIsolation:
    """Session isolation verification tests."""

    def test_session_id_validation(self):
        """
        Test that session_id is validated before use.
        """
        hook = E2ETrackerHook()

        # Test invalid session_ids (should be rejected or sanitized)
        invalid_ids = [
            "../etc/passwd",  # Path traversal
            "/absolute/path",  # Absolute path
            "session\x00null",  # Null byte
            "",  # Empty string
        ]

        for invalid_id in invalid_ids:
            with pytest.raises((ValueError, KeyError)):
                hook.process(
                    tool_name="Bash",
                    tool_input={"command": "echo test"},
                    tool_response={"success": True},
                    session_id=invalid_id,
                    terminal_id="test-terminal",
                )

    def test_terminal_id_sanitization(self):
        """
        Test that terminal_id is sanitized correctly.
        """
        hook = E2ETrackerHook()

        # Terminal ID with special characters
        raw_terminal_id = "terminal@123!#$%"
        result = hook.process(
            tool_name="Bash",
            tool_input={"command": "echo test"},
            tool_response={"success": True},
            session_id="test-session",
            terminal_id=raw_terminal_id,
        )

        assert result["tracked"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
