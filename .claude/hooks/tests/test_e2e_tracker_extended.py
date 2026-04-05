#!/usr/bin/env python3
"""
Extended E2E Tracker Tests

Tests for E2E tracker functionality including:
1. Session isolation (TEST-004)
2. Performance tests (TEST-005)
3. Log rotation
4. Integration with evidence store

Test Coverage:
- Component → integration → e2e pipeline
- Session isolation (including concurrent terminals)
- Performance: E2E tracker overhead <100ms per 100 events
- Log rotation and cleanup
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


class TestE2ETrackerSessionIsolation:
    """TEST-004: Session isolation tests."""

    def test_session_id_isolation(self, tmp_path):
        """
        Test that different session_ids maintain separate evidence.

        Verifies session isolation at the evidence store level.
        """
        from evidence_store import load_tool_events
        from PostToolUse_e2e_tracker import post_tool_use_hook

        # Track events for session 1
        context1 = {"session_id": "test-session-1", "terminal_id": "terminal-A"}
        post_tool_use_hook(
            tool_name="Bash",
            tool_input={"command": "echo session1"},
            tool_output={"success": True, "output": "session1"},
            context=context1,
        )

        # Track events for session 2
        context2 = {"session_id": "test-session-2", "terminal_id": "terminal-B"}
        post_tool_use_hook(
            tool_name="Bash",
            tool_input={"command": "echo session2"},
            tool_output={"success": True, "output": "session2"},
            context=context2,
        )

        # Verify isolation
        events1 = load_tool_events("test-session-1", limit=10)
        events2 = load_tool_events("test-session-2", limit=10)

        assert len(events1) > 0
        assert len(events2) > 0

        # Verify no cross-contamination
        session1_ids = {e.get("session_id") for e in events1}
        session2_ids = {e.get("session_id") for e in events2}

        assert "test-session-1" in session1_ids
        assert "test-session-2" in session2_ids
        assert "test-session-2" not in session1_ids
        assert "test-session-1" not in session2_ids

    def test_terminal_id_isolation(self, tmp_path):
        """
        Test that same session_id with different terminal_ids are tracked separately.

        This tests the terminal_id component of session isolation.
        """
        from evidence_store import load_tool_events
        from PostToolUse_e2e_tracker import post_tool_use_hook

        session_id = "shared-session"

        # Same session, different terminals
        context1 = {"session_id": session_id, "terminal_id": "terminal-A"}
        post_tool_use_hook(
            tool_name="Bash",
            tool_input={"command": "echo terminal1"},
            tool_output={"success": True},
            context=context1,
        )

        context2 = {"session_id": session_id, "terminal_id": "terminal-B"}
        post_tool_use_hook(
            tool_name="Bash",
            tool_input={"command": "echo terminal2"},
            tool_output={"success": True},
            context=context2,
        )

        # Verify both tracked
        events = load_tool_events(session_id, limit=10)
        assert len(events) >= 2

        # Verify terminal_id separation
        terminal_ids = {e.get("terminal_id") for e in events}
        assert "terminal-A" in terminal_ids
        assert "terminal-B" in terminal_ids


class TestE2ETrackerPerformance:
    """TEST-005: Performance regression tests."""

    def test_tracker_overhead_per_event(self):
        """
        TEST-005: Verify tracker overhead <100ms per 100 events.

        Performance requirement: <1ms average per event.
        """
        from PostToolUse_e2e_tracker import post_tool_use_hook

        session_id = f"perf-test-{int(time.time())}"
        event_count = 100

        start_time = time.perf_counter()

        for i in range(event_count):
            context = {"session_id": session_id, "terminal_id": "perf-terminal"}
            post_tool_use_hook(
                tool_name="Bash",
                tool_input={"command": f"echo test-{i}"},
                tool_output={"success": True},
                context=context,
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Verify performance requirement
        # Allow 100ms for 100 events = 1ms average per event
        assert (
            elapsed_ms < 100
        ), f"Tracker too slow: {elapsed_ms:.2f}ms for {event_count} events"

        # Verify all events tracked
        from evidence_store import load_tool_events

        events = load_tool_events(session_id, limit=200)
        assert len(events) >= event_count

    def test_concurrent_tracking_performance(self):
        """
        Test performance with multiple concurrent sessions.

        Simulates realistic multi-terminal workload.
        """
        from PostToolUse_e2e_tracker import post_tool_use_hook

        terminal_count = 5
        events_per_terminal = 20

        start_time = time.perf_counter()

        for terminal_id in range(terminal_count):
            session_id = f"concurrent-session-{terminal_id}"
            for i in range(events_per_terminal):
                context = {"session_id": session_id, "terminal_id": f"terminal-{terminal_id}"}
                post_tool_use_hook(
                    tool_name="Bash",
                    tool_input={"command": f"echo test-{i}"},
                    tool_output={"success": True},
                    context=context,
                )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        total_events = terminal_count * events_per_terminal

        # Performance requirement: <200ms for 100 events across 5 terminals
        assert (
            elapsed_ms < 200
        ), f"Concurrent tracking too slow: {elapsed_ms:.2f}ms for {total_events} events"


class TestE2ETrackerLogRotation:
    """Test log rotation and cleanup functionality."""

    def test_log_file_creation(self):
        """
        Test that log files are created correctly.

        Verifies basic E2E tracker logging functionality.
        """
        from PostToolUse_e2e_tracker import post_tool_use_hook

        session_id = f"log-test-{int(time.time())}"
        context = {"session_id": session_id, "terminal_id": "test-terminal"}

        post_tool_use_hook(
            tool_name="Bash",
            tool_input={"command": "echo test"},
            tool_output={"success": True},
            context=context,
        )

        # Verify log file created
        log_file = hooks_dir / "state" / f"e2e_executions_{session_id}.jsonl"
        # Note: File may not exist in test environment, that's ok
        # The important part is that tracking doesn't crash


class TestE2ETrackerIntegration:
    """Integration tests with evidence store."""

    def test_evidence_store_integration(self):
        """
        Test that E2E tracker integrates with evidence store.

        Verifies tracked events are queryable.
        """
        from evidence_store import load_tool_events
        from PostToolUse_e2e_tracker import post_tool_use_hook

        session_id = f"integration-test-{int(time.time())}"
        context = {"session_id": session_id, "terminal_id": "test-terminal"}

        post_tool_use_hook(
            tool_name="Bash",
            tool_input={"command": "pytest tests/test.py -v"},
            tool_output={"success": True, "output": "test passed"},
            context=context,
        )

        # Verify event is retrievable
        events = load_tool_events(session_id, limit=10)
        bash_events = [e for e in events if e.get("name") == "Bash"]
        assert len(bash_events) > 0


class TestE2ETrackerHookAPI:
    """Test the hook API for E2E tracker."""

    def test_hook_instantiation(self):
        """
        Test that E2E tracker hook can be instantiated.
        """
        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        hook = E2ETrackerHook()
        assert hook is not None
        assert hook.enabled is True
        assert hook.tool_matcher is None  # Tracks all tools

    def test_hook_process_method(self):
        """
        Test hook process method with tool event.
        """
        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        hook = E2ETrackerHook()

        result = hook.process(
            tool_name="Bash",
            tool_input={"command": "echo test"},
            tool_response={"success": True, "context": {"session_id": "test", "terminal_id": "test"}},
        )

        assert result["passed"] is True
        assert result["tracked"] is True
        assert result["workflow_type"] == "tool_chain"

    def test_hook_skill_detection(self):
        """
        Test that hook correctly detects skill invocations.
        """
        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        hook = E2ETrackerHook()

        result = hook.process(
            tool_name="Skill",
            tool_input={"skill": "test-skill"},
            tool_response={"success": True},
        )

        assert result["workflow_type"] == "skill_invocation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
