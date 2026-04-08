#!/usr/bin/env python3
"""
Extended E2E tracker tests against the current tracker contracts.

These tests validate:
1. `track_workflow(...)` persistence and session isolation
2. log rotation / cleanup helpers
3. `E2ETrackerHook.process(...)` hook-level behavior
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


def _read_workflow_records(state_dir: Path, session_id: str) -> list[dict]:
    log_file = state_dir / f"e2e_executions_{session_id}.jsonl"
    if not log_file.exists():
        return []
    return [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines() if line.strip()]


class TestE2ETrackerSessionIsolation:
    def test_session_id_isolation(self, tmp_path):
        from PostToolUse_e2e_tracker import track_workflow

        state_dir = tmp_path / "state"
        track_workflow(
            workflow_type="tool_chain",
            target="session-one",
            session_id="test-session-1",
            terminal_id="terminal-A",
            stages=[{"stage": "run", "status": "passed", "duration_ms": 1}],
            overall="success",
            state_dir=state_dir,
        )
        track_workflow(
            workflow_type="tool_chain",
            target="session-two",
            session_id="test-session-2",
            terminal_id="terminal-B",
            stages=[{"stage": "run", "status": "passed", "duration_ms": 1}],
            overall="success",
            state_dir=state_dir,
        )

        records1 = _read_workflow_records(state_dir, "test-session-1")
        records2 = _read_workflow_records(state_dir, "test-session-2")

        assert len(records1) == 1
        assert len(records2) == 1
        assert records1[0]["session_id"] == "test-session-1"
        assert records2[0]["session_id"] == "test-session-2"

    def test_terminal_id_isolation(self, tmp_path):
        from PostToolUse_e2e_tracker import track_workflow

        state_dir = tmp_path / "state"
        session_id = "shared-session"
        track_workflow(
            workflow_type="tool_chain",
            target="first",
            session_id=session_id,
            terminal_id="terminal-A",
            stages=[{"stage": "run", "status": "passed", "duration_ms": 1}],
            overall="success",
            state_dir=state_dir,
        )
        track_workflow(
            workflow_type="tool_chain",
            target="second",
            session_id=session_id,
            terminal_id="terminal-B",
            stages=[{"stage": "run", "status": "passed", "duration_ms": 1}],
            overall="success",
            state_dir=state_dir,
        )

        records = _read_workflow_records(state_dir, session_id)
        assert len(records) == 2
        assert {record["terminal_id"] for record in records} == {"terminal-A", "terminal-B"}


class TestE2ETrackerPerformance:
    def test_tracker_overhead_per_event(self, tmp_path):
        from PostToolUse_e2e_tracker import track_workflow

        state_dir = tmp_path / "state"
        session_id = f"perf-test-{int(time.time())}"
        event_count = 100

        start_time = time.perf_counter()
        for i in range(event_count):
            track_workflow(
                workflow_type="tool_chain",
                target=f"step-{i}",
                session_id=session_id,
                terminal_id="perf-terminal",
                stages=[{"stage": "run", "status": "passed", "duration_ms": 1}],
                overall="success",
                state_dir=state_dir,
            )
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 2500, f"Tracker too slow: {elapsed_ms:.2f}ms for {event_count} events"
        assert len(_read_workflow_records(state_dir, session_id)) == event_count

    def test_concurrent_tracking_performance(self, tmp_path):
        from PostToolUse_e2e_tracker import track_workflow

        state_dir = tmp_path / "state"
        terminal_count = 5
        events_per_terminal = 20

        start_time = time.perf_counter()
        for terminal_id in range(terminal_count):
            session_id = f"concurrent-session-{terminal_id}"
            for i in range(events_per_terminal):
                track_workflow(
                    workflow_type="tool_chain",
                    target=f"step-{i}",
                    session_id=session_id,
                    terminal_id=f"terminal-{terminal_id}",
                    stages=[{"stage": "run", "status": "passed", "duration_ms": 1}],
                    overall="success",
                    state_dir=state_dir,
                )
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        assert elapsed_ms < 3000, f"Concurrent tracking too slow: {elapsed_ms:.2f}ms"


class TestE2ETrackerLogRotation:
    def test_log_file_creation(self, tmp_path):
        from PostToolUse_e2e_tracker import track_workflow

        state_dir = tmp_path / "state"
        session_id = "log-test"
        track_workflow(
            workflow_type="tool_chain",
            target="test",
            session_id=session_id,
            terminal_id="test-terminal",
            stages=[{"stage": "run", "status": "passed", "duration_ms": 1}],
            overall="success",
            state_dir=state_dir,
        )

        log_file = state_dir / f"e2e_executions_{session_id}.jsonl"
        assert log_file.exists()


class TestE2ETrackerIntegration:
    def test_track_workflow_persists_expected_fields(self, tmp_path):
        from PostToolUse_e2e_tracker import track_workflow

        state_dir = tmp_path / "state"
        session_id = "integration-test"
        track_workflow(
            workflow_type="tool_chain",
            target="pytest tests test py v",
            session_id=session_id,
            terminal_id="test-terminal",
            stages=[{"stage": "run", "status": "passed", "duration_ms": 5}],
            overall="success",
            state_dir=state_dir,
        )

        records = _read_workflow_records(state_dir, session_id)
        assert len(records) == 1
        assert records[0]["workflow_type"] == "tool_chain"
        assert records[0]["terminal_id"] == "test-terminal"


class TestE2ETrackerHookAPI:
    def test_hook_instantiation(self):
        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        hook = E2ETrackerHook()
        assert hook is not None
        assert hook.enabled is True
        assert hook.tool_matcher is None

    def test_hook_process_method(self, monkeypatch):
        from posttooluse.e2e_tracker_hook import E2ETrackerHook
        import posttooluse.e2e_tracker_hook as hook_module

        captured: list[dict] = []

        def fake_post_tool_use_hook(*, tool_name, tool_input, tool_output, context):
            captured.append(
                {
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "tool_output": tool_output,
                    "context": context,
                }
            )

        monkeypatch.setattr(hook_module, "post_tool_use_hook", fake_post_tool_use_hook)

        hook = E2ETrackerHook()
        result = hook.process(
            tool_name="Bash",
            tool_input={"command": "echo test"},
            tool_response={"success": True, "context": {"session_id": "test", "terminal_id": "test"}},
        )

        assert result["passed"] is True
        assert result["tracked"] is True
        assert result["workflow_type"] == "tool_chain"
        assert captured[0]["context"]["session_id"] == "test"

    def test_hook_skill_detection(self, monkeypatch):
        from posttooluse.e2e_tracker_hook import E2ETrackerHook
        import posttooluse.e2e_tracker_hook as hook_module

        monkeypatch.setattr(
            hook_module,
            "post_tool_use_hook",
            lambda **kwargs: None,
        )

        hook = E2ETrackerHook()
        result = hook.process(
            tool_name="Skill",
            tool_input={"skill": "test-skill"},
            tool_response={"success": True},
        )

        assert result["workflow_type"] == "skill_invocation"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
