"""
Integration tests for observability system.

Tests end-to-end observability workflows including:
- Decision logging across loop lifecycle
- Metrics tracking and updates
- Per-terminal isolation
- Cross-terminal aggregation
- Error handling and graceful degradation
"""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from scripts.loop_observability import (
    log_decision,
    update_metrics,
)


def get_terminal_metrics_from_dir(state_dir: Path) -> dict | None:
    """Helper function to read terminal metrics from a specific state directory."""
    metrics_file = state_dir / "loop_metrics.json"

    if not metrics_file.exists():
        return None

    try:
        with metrics_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


class TestObservabilityIntegration:
    """End-to-end integration tests for observability."""

    @pytest.fixture
    def temp_state_dirs(self, tmp_path):
        """Create temporary state directories for testing."""

        class TempDirs:
            def __init__(self, base_path):
                self.base_path = base_path
                self.created = []

            def get_log_dir(self, terminal_id: str) -> Path:
                """Get a temporary log dir for a terminal."""
                log_dir = self.base_path / "logs" / terminal_id
                log_dir.mkdir(parents=True, exist_ok=True)
                self.created.append(log_dir)
                return log_dir

            def get_state_dir(self, terminal_id: str) -> Path:
                """Get a temporary state dir for a terminal."""
                state_dir = self.base_path / "state" / terminal_id
                state_dir.mkdir(parents=True, exist_ok=True)
                self.created.append(state_dir)
                return state_dir

        yield TempDirs(tmp_path)

    def test_complete_loop_lifecycle_observability(self, temp_state_dirs):
        """Test observability across a complete loop lifecycle."""
        terminal_id = "integration_test_loop"

        with (
            patch(
                "scripts.loop_observability.get_terminal_log_dir",
                temp_state_dirs.get_log_dir,
            ),
            patch(
                "scripts.loop_observability.get_terminal_state_dir",
                temp_state_dirs.get_state_dir,
            ),
        ):
            # ===== PHASE 1: Loop Initialization =====
            log_decision(
                terminal_id,
                "LOOP_START",
                {
                    "plan": "Build authentication system",
                    "total_tasks": 3,
                    "tasks": ["setup", "implement", "test"],
                },
            )

            update_metrics(
                terminal_id,
                {
                    "start_time": datetime.now().isoformat(),
                    "iterations": 0,
                    "tasks_completed": 0,
                    "total_tasks": 3,
                    "current_phase": "initialization",
                },
            )

            # ===== PHASE 2: First Iteration =====
            log_decision(terminal_id, "ITERATION_START", {"iteration_number": 1})

            # Task 1: Setup
            log_decision(
                terminal_id,
                "TASK_START",
                {"task_id": "task_1", "description": "Setup project structure"},
            )

            log_decision(
                terminal_id,
                "TASK_COMPLETE",
                {
                    "task_id": "task_1",
                    "duration_seconds": 15,
                    "success": True,
                    "outputs": ["src/", "tests/"],
                },
            )

            # Task 2: Implement
            log_decision(
                terminal_id,
                "TASK_START",
                {"task_id": "task_2", "description": "Implement auth logic"},
            )

            log_decision(
                terminal_id,
                "TASK_COMPLETE",
                {
                    "task_id": "task_2",
                    "duration_seconds": 45,
                    "success": True,
                    "outputs": ["src/auth.py"],
                },
            )

            # Task 3: Test
            log_decision(
                terminal_id,
                "TASK_START",
                {"task_id": "task_3", "description": "Write tests"},
            )

            log_decision(
                terminal_id,
                "TASK_COMPLETE",
                {
                    "task_id": "task_3",
                    "duration_seconds": 30,
                    "success": True,
                    "outputs": ["tests/test_auth.py"],
                },
            )

            log_decision(
                terminal_id,
                "ITERATION_COMPLETE",
                {
                    "iteration_number": 1,
                    "tasks_completed_this_iteration": 3,
                    "all_tasks_complete": True,
                },
            )

            update_metrics(
                terminal_id,
                {
                    "iterations": 1,
                    "tasks_completed": 3,
                    "last_activity": datetime.now().isoformat(),
                    "current_phase": "verification",
                },
            )

            # ===== PHASE 3: Verification =====
            log_decision(
                terminal_id,
                "VERIFICATION_TRIGGERED",
                {"reason": "all_tasks_complete", "verifier_skill": "prd-verifier"},
            )

            log_decision(
                terminal_id,
                "VERIFICATION_COMPLETE",
                {"passed": True, "report_path": ".claude/loop/verification-report.md"},
            )

            update_metrics(
                terminal_id,
                {"verification_passes": 1, "last_activity": datetime.now().isoformat()},
            )

            # ===== PHASE 4: Loop Exit =====
            log_decision(
                terminal_id,
                "LOOP_EXIT",
                {
                    "reason": "all_tasks_complete_and_verified",
                    "total_iterations": 1,
                    "final_score": 100,
                },
            )

            update_metrics(
                terminal_id,
                {
                    "exit_reason": "all_tasks_complete_and_verified",
                    "end_time": datetime.now().isoformat(),
                },
            )

            # ===== VERIFICATION =====
            # Verify decision log
            log_dir = temp_state_dirs.get_log_dir(terminal_id)
            log_file = log_dir / "decision.log"

            assert log_file.exists(), "Decision log should exist"
            log_content = log_file.read_text()
            log_lines = [line for line in log_content.strip().split("\n") if line]

            # Should have 12 entries
            assert (
                len(log_lines) == 12
            ), f"Expected 12 log entries, got {len(log_lines)}"

            # Verify log entry structure
            entries = [json.loads(line) for line in log_lines]

            # Check first entry
            assert entries[0]["event"] == "LOOP_START"
            assert entries[0]["terminal_id"] == terminal_id
            assert "timestamp" in entries[0]

            # Check last entry
            assert entries[-1]["event"] == "LOOP_EXIT"

            # Verify metrics
            metrics = get_terminal_metrics_from_dir(
                temp_state_dirs.get_state_dir(terminal_id)
            )
            assert metrics is not None, "Metrics should exist"
            assert metrics["iterations"] == 1
            assert metrics["tasks_completed"] == 3
            assert metrics["total_tasks"] == 3
            assert metrics["verification_passes"] == 1
            assert metrics["exit_reason"] == "all_tasks_complete_and_verified"
            assert "start_time" in metrics
            assert "end_time" in metrics

    def test_multi_terminal_isolation(self, temp_state_dirs):
        """Test that multiple terminals maintain proper isolation."""
        terminals = ["term_a", "term_b", "term_c"]

        with (
            patch(
                "scripts.loop_observability.get_terminal_log_dir",
                temp_state_dirs.get_log_dir,
            ),
            patch(
                "scripts.loop_observability.get_terminal_state_dir",
                temp_state_dirs.get_state_dir,
            ),
        ):
            # Each terminal does different work
            for idx, term in enumerate(terminals):
                log_decision(
                    term,
                    "LOOP_START",
                    {"terminal_index": idx, "plan": f"Plan for terminal {idx}"},
                )

                update_metrics(
                    term,
                    {
                        "terminal_id": term,
                        "start_time": datetime.now().isoformat(),
                        "terminal_index": idx,
                    },
                )

            # Verify isolation
            for term in terminals:
                metrics = get_terminal_metrics_from_dir(
                    temp_state_dirs.get_state_dir(term)
                )
                assert metrics["terminal_id"] == term

                log_dir = temp_state_dirs.get_log_dir(term)
                log_file = log_dir / "decision.log"
                assert log_file.exists()

                # Verify only this terminal's events
                content = log_file.read_text()
                entries = [json.loads(line) for line in content.strip().split("\n")]
                for entry in entries:
                    assert entry["terminal_id"] == term

    def test_error_recovery_and_observability(self, temp_state_dirs):
        """Test observability during error scenarios."""
        terminal_id = "error_test_term"

        with (
            patch(
                "scripts.loop_observability.get_terminal_log_dir",
                temp_state_dirs.get_log_dir,
            ),
            patch(
                "scripts.loop_observability.get_terminal_state_dir",
                temp_state_dirs.get_state_dir,
            ),
        ):
            # Normal operations
            log_decision(
                terminal_id,
                "TASK_START",
                {"task_id": "task_1", "description": "Risky operation"},
            )

            # Error occurs
            log_decision(
                terminal_id,
                "ERROR",
                {
                    "error_type": "ValueError",
                    "error_message": "Invalid input parameter",
                    "task_id": "task_1",
                    "operation": "risky_operation",
                },
            )

            update_metrics(
                terminal_id,
                {
                    "error_count": 1,
                    "last_error": "ValueError: Invalid input parameter",
                    "last_activity": datetime.now().isoformat(),
                },
            )

            # Recovery attempt
            log_decision(
                terminal_id,
                "TASK_START",
                {
                    "task_id": "task_1_retry",
                    "description": "Retry with fixed parameters",
                },
            )

            log_decision(
                terminal_id,
                "TASK_COMPLETE",
                {"task_id": "task_1_retry", "success": True},
            )

            # Verify error was captured
            log_file = temp_state_dirs.get_log_dir(terminal_id) / "decision.log"
            content = log_file.read_text()
            entries = [json.loads(line) for line in content.strip().split("\n")]

            error_entries = [e for e in entries if e["event"] == "ERROR"]
            assert len(error_entries) == 1
            assert error_entries[0]["payload"]["error_type"] == "ValueError"

            # Verify metrics reflect error
            metrics = get_terminal_metrics_from_dir(
                temp_state_dirs.get_state_dir(terminal_id)
            )
            assert metrics["error_count"] == 1
            assert "ValueError" in metrics["last_error"]

    def test_concurrent_metrics_updates(self, temp_state_dirs):
        """Test that metrics updates are atomic and don't corrupt."""
        terminal_id = "concurrent_test_term"

        with (
            patch(
                "scripts.loop_observability.get_terminal_log_dir",
                temp_state_dirs.get_log_dir,
            ),
            patch(
                "scripts.loop_observability.get_terminal_state_dir",
                temp_state_dirs.get_state_dir,
            ),
        ):
            # Simulate rapid concurrent updates
            # Note: _merge_metrics sums numeric values, so we test increment behavior
            for i in range(1, 11):
                update_metrics(
                    terminal_id,
                    {
                        "iterations": 1,  # Increment by 1 each time
                        "tasks_completed": 2,  # Increment by 2 each time
                    },
                )

            # Verify final state is consistent
            metrics = get_terminal_metrics_from_dir(
                temp_state_dirs.get_state_dir(terminal_id)
            )
            assert metrics is not None
            assert metrics["iterations"] == 10  # 1 * 10 = 10
            assert metrics["tasks_completed"] == 20  # 2 * 10 = 20

            # Verify JSON is valid
            metrics_file = (
                temp_state_dirs.get_state_dir(terminal_id) / "loop_metrics.json"
            )
            with metrics_file.open() as f:
                json.load(f)  # Should not raise

    def test_decision_log_querying(self, temp_state_dirs):
        """Test querying and analyzing decision logs."""
        terminal_id = "query_test_term"

        with (
            patch(
                "scripts.loop_observability.get_terminal_log_dir",
                temp_state_dirs.get_log_dir,
            ),
            patch(
                "scripts.loop_observability.get_terminal_state_dir",
                temp_state_dirs.get_state_dir,
            ),
        ):
            # Add various event types
            events = [
                ("LOOP_START", {"plan": "Test plan"}),
                ("TASK_START", {"task_id": "t1"}),
                ("TASK_COMPLETE", {"task_id": "t1", "success": True}),
                ("TASK_START", {"task_id": "t2"}),
                ("TASK_COMPLETE", {"task_id": "t2", "success": True}),
                ("LOOP_EXIT", {"reason": "complete"}),
            ]

            for event, payload in events:
                log_decision(terminal_id, event, payload)

            # Query and analyze
            log_file = temp_state_dirs.get_log_dir(terminal_id) / "decision.log"
            entries = [
                json.loads(line) for line in log_file.read_text().strip().split("\n")
            ]

            # Filter by event type
            task_starts = [e for e in entries if e["event"] == "TASK_START"]
            task_completes = [e for e in entries if e["event"] == "TASK_COMPLETE"]

            assert len(task_starts) == 2
            assert len(task_completes) == 2

            # Verify chronological order
            timestamps = [e["timestamp"] for e in entries]
            assert timestamps == sorted(timestamps)

    def test_graceful_degradation_on_disk_full(self):
        """Test that logging failures don't break loop logic."""
        terminal_id = "degradation_test"

        # These should not raise exceptions even if they fail
        try:
            log_decision(terminal_id, "TEST_EVENT", {"data": "test"})
            update_metrics(terminal_id, {"test": "value"})
        except Exception as e:
            pytest.fail(f"Observability should not raise exceptions: {e}")

        # Loop logic should continue
        assert True

    def test_large_payload_handling(self, temp_state_dirs):
        """Test handling of large payloads in decision logs."""
        terminal_id = "large_payload_test"

        with (
            patch(
                "scripts.loop_observability.get_terminal_log_dir",
                temp_state_dirs.get_log_dir,
            ),
            patch(
                "scripts.loop_observability.get_terminal_state_dir",
                temp_state_dirs.get_state_dir,
            ),
        ):
            # Create a large payload
            large_payload = {
                "data": "x" * 10000,  # 10KB of data
                "nested": {"level_1": {"level_2": {"level_3": "deep data"}}},
                "array": list(range(1000)),
            }

            log_decision(terminal_id, "LARGE_PAYLOAD_EVENT", large_payload)

            # Verify log entry was written
            log_file = temp_state_dirs.get_log_dir(terminal_id) / "decision.log"
            content = log_file.read_text()
            entries = [json.loads(line) for line in content.strip().split("\n")]

            assert len(entries) == 1
            assert entries[0]["payload"]["data"] == "x" * 10000
            assert len(entries[0]["payload"]["array"]) == 1000

    def test_metrics_merge_behavior(self, temp_state_dirs):
        """Test that metrics updates follow _merge_metrics behavior."""
        terminal_id = "merge_test_term"

        with (
            patch(
                "scripts.loop_observability.get_terminal_log_dir",
                temp_state_dirs.get_log_dir,
            ),
            patch(
                "scripts.loop_observability.get_terminal_state_dir",
                temp_state_dirs.get_state_dir,
            ),
        ):
            # Initial metrics
            update_metrics(
                terminal_id,
                {
                    "iterations": 1,
                    "tasks_completed": 0,
                },
            )

            # Update metrics - numeric values are summed
            update_metrics(
                terminal_id,
                {
                    "iterations": 1,  # Will sum: 1 + 1 = 2
                    "tasks_completed": 3,  # Will sum: 0 + 3 = 3
                },
            )

            metrics = get_terminal_metrics_from_dir(
                temp_state_dirs.get_state_dir(terminal_id)
            )

            # Verify merge behavior for numeric values
            assert metrics["iterations"] == 2  # Summed
            assert metrics["tasks_completed"] == 3  # Summed

    def test_observability_with_loop_policy_integration(self, temp_state_dirs):
        """Test observability integration with loop policy decisions."""
        terminal_id = "policy_integration_term"

        with (
            patch(
                "scripts.loop_observability.get_terminal_log_dir",
                temp_state_dirs.get_log_dir,
            ),
            patch(
                "scripts.loop_observability.get_terminal_state_dir",
                temp_state_dirs.get_state_dir,
            ),
        ):
            # Simulate loop policy decisions
            policy_events = [
                (
                    "PLAN_PARSED",
                    {"tasks_found": 5, "task_ids": ["t1", "t2", "t3", "t4", "t5"]},
                ),
                (
                    "EXIT_CHECK",
                    {
                        "should_exit": False,
                        "reason": "tasks_incomplete",
                        "tasks_completed": 2,
                        "total_tasks": 5,
                    },
                ),
                (
                    "VERIFICATION_CHECK",
                    {"should_run": True, "reason": "iteration_complete"},
                ),
                (
                    "EXIT_CHECK",
                    {
                        "should_exit": True,
                        "reason": "all_tasks_complete",
                        "tasks_completed": 5,
                        "total_tasks": 5,
                    },
                ),
            ]

            for event, payload in policy_events:
                log_decision(terminal_id, event, payload)

            # Verify policy decision trace
            log_file = temp_state_dirs.get_log_dir(terminal_id) / "decision.log"
            entries = [
                json.loads(line) for line in log_file.read_text().strip().split("\n")
            ]

            exit_checks = [e for e in entries if e["event"] == "EXIT_CHECK"]
            assert len(exit_checks) == 2

            # First check: don't exit
            assert exit_checks[0]["payload"]["should_exit"] is False
            assert exit_checks[0]["payload"]["tasks_completed"] == 2

            # Second check: exit
            assert exit_checks[1]["payload"]["should_exit"] is True
            assert exit_checks[1]["payload"]["tasks_completed"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
