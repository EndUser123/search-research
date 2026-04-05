"""
Integration tests for PRD Verifier observability.

Tests that verification events are logged at the right times and metrics
are updated correctly during the verification process.
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


class TestVerificationObservability:
    """Integration tests for verification observability."""

    @pytest.fixture
    def temp_state_dirs(self, tmp_path):
        """Create temporary state directories for testing."""

        class TempDirs:
            def __init__(self, base_path):
                self.base_path = base_path

            def get_log_dir(self, terminal_id: str) -> Path:
                """Get a temporary log dir for a terminal."""
                log_dir = self.base_path / "logs" / terminal_id
                log_dir.mkdir(parents=True, exist_ok=True)
                return log_dir

            def get_state_dir(self, terminal_id: str) -> Path:
                """Get a temporary state dir for a terminal."""
                state_dir = self.base_path / "state" / terminal_id
                state_dir.mkdir(parents=True, exist_ok=True)
                return state_dir

        yield TempDirs(tmp_path)

    def get_metrics_from_dir(self, state_dir: Path) -> dict | None:
        """Helper function to read terminal metrics from a specific state directory."""
        metrics_file = state_dir / "loop_metrics.json"

        if not metrics_file.exists():
            return None

        try:
            with metrics_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def test_verification_triggered_event_logged(self, temp_state_dirs):
        """Test that VERIFICATION_TRIGGERED event is logged when verification starts."""
        terminal_id = "test_verification_trigger"

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
            # Simulate verification being triggered
            log_decision(
                terminal_id,
                "VERIFICATION_TRIGGERED",
                {"reason": "all_tasks_complete", "verifier_skill": "prd-verifier"},
            )

            # Verify event was logged
            log_file = temp_state_dirs.get_log_dir(terminal_id) / "decision.log"
            assert log_file.exists()

            content = log_file.read_text()
            entries = [json.loads(line) for line in content.strip().split("\n")]

            assert len(entries) == 1
            assert entries[0]["event"] == "VERIFICATION_TRIGGERED"
            assert entries[0]["payload"]["reason"] == "all_tasks_complete"
            assert entries[0]["payload"]["verifier_skill"] == "prd-verifier"
            assert "timestamp" in entries[0]

    def test_verification_start_event_logged(self, temp_state_dirs):
        """Test that VERIFICATION_START event is logged with context."""
        terminal_id = "test_verification_start"

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
            # Simulate verification start
            log_decision(
                terminal_id,
                "VERIFICATION_START",
                {
                    "verifier": "prd-verifier",
                    "plan_path": "plan.md",
                    "prd_path": "PRD.md",
                },
            )

            # Verify event was logged
            log_file = temp_state_dirs.get_log_dir(terminal_id) / "decision.log"
            content = log_file.read_text()
            entries = [json.loads(line) for line in content.strip().split("\n")]

            assert len(entries) == 1
            assert entries[0]["event"] == "VERIFICATION_START"
            assert entries[0]["payload"]["verifier"] == "prd-verifier"
            assert entries[0]["payload"]["plan_path"] == "plan.md"
            assert entries[0]["payload"]["prd_path"] == "PRD.md"

    def test_verification_progress_events_logged(self, temp_state_dirs):
        """Test that verification progress events are logged for each dimension."""
        terminal_id = "test_verification_progress"

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
            # Simulate verification progress events
            log_decision(
                terminal_id,
                "VERIFICATION_PRD_COVERAGE_CHECK",
                {
                    "total_requirements": 12,
                    "covered_requirements": 11,
                    "coverage_percentage": 92,
                    "missing_requirements": ["Multi-factor authentication"],
                    "threshold": 80,
                    "passed": True,
                },
            )

            log_decision(
                terminal_id,
                "VERIFICATION_SPEC_COMPLIANCE_CHECK",
                {
                    "total_specs": 8,
                    "compliant_specs": 8,
                    "compliance_percentage": 100,
                    "deviations": [],
                    "threshold": 80,
                    "passed": True,
                },
            )

            log_decision(
                terminal_id,
                "VERIFICATION_QUALITY_CHECK",
                {
                    "quality_score": 9,
                    "user_concerns": [],
                    "issues": [],
                    "recommendations": ["Add integration tests"],
                    "threshold": 7,
                    "passed": True,
                },
            )

            # Verify all events were logged
            log_file = temp_state_dirs.get_log_dir(terminal_id) / "decision.log"
            content = log_file.read_text()
            entries = [json.loads(line) for line in content.strip().split("\n")]

            assert len(entries) == 3

            # Check PRD coverage event
            assert entries[0]["event"] == "VERIFICATION_PRD_COVERAGE_CHECK"
            assert entries[0]["payload"]["coverage_percentage"] == 92
            assert entries[0]["payload"]["passed"] is True

            # Check spec compliance event
            assert entries[1]["event"] == "VERIFICATION_SPEC_COMPLIANCE_CHECK"
            assert entries[1]["payload"]["compliance_percentage"] == 100
            assert entries[1]["payload"]["passed"] is True

            # Check quality event
            assert entries[2]["event"] == "VERIFICATION_QUALITY_CHECK"
            assert entries[2]["payload"]["quality_score"] == 9
            assert entries[2]["payload"]["passed"] is True

    def test_verification_complete_event_logged(self, temp_state_dirs):
        """Test that VERIFICATION_COMPLETE event is logged with results."""
        terminal_id = "test_verification_complete"

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
            # Simulate verification complete
            log_decision(
                terminal_id,
                "VERIFICATION_COMPLETE",
                {
                    "passed": True,
                    "report_path": ".claude/loop/verification-report.md",
                    "duration_seconds": 3,
                },
            )

            # Verify event was logged
            log_file = temp_state_dirs.get_log_dir(terminal_id) / "decision.log"
            content = log_file.read_text()
            entries = [json.loads(line) for line in content.strip().split("\n")]

            assert len(entries) == 1
            assert entries[0]["event"] == "VERIFICATION_COMPLETE"
            assert entries[0]["payload"]["passed"] is True
            assert entries[0]["payload"]["duration_seconds"] == 3
            assert "report_path" in entries[0]["payload"]

    def test_verification_metrics_updated(self, temp_state_dirs):
        """Test that verification metrics are updated correctly."""
        terminal_id = "test_verification_metrics"

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
            # Initialize metrics
            update_metrics(
                terminal_id,
                {
                    "verification_runs": 0,
                    "verification_passes": 0,
                    "verification_failures": 0,
                },
            )

            # Update metrics after verification
            update_metrics(
                terminal_id,
                {
                    "verification_runs": 1,
                    "verification_passes": 1,
                    "last_verification": datetime.now().isoformat(),
                    "verification_passed": True,
                },
            )

            # Verify metrics were updated
            metrics = self.get_metrics_from_dir(
                temp_state_dirs.get_state_dir(terminal_id)
            )
            assert metrics is not None
            assert metrics["verification_runs"] == 1
            assert metrics["verification_passes"] == 1
            assert metrics["verification_failures"] == 0
            assert metrics["verification_passed"] is True
            assert "last_verification" in metrics

    def test_full_verification_lifecycle_observability(self, temp_state_dirs):
        """Test complete verification lifecycle with observability."""
        terminal_id = "test_verification_lifecycle"

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
            # Phase 1: Trigger verification
            log_decision(
                terminal_id,
                "VERIFICATION_TRIGGERED",
                {"reason": "all_tasks_complete", "verifier_skill": "prd-verifier"},
            )

            # Phase 2: Start verification
            log_decision(
                terminal_id,
                "VERIFICATION_START",
                {
                    "verifier": "prd-verifier",
                    "plan_path": "plan.md",
                    "prd_path": "PRD.md",
                },
            )

            # Phase 3: Progress events
            log_decision(
                terminal_id,
                "VERIFICATION_PRD_COVERAGE_CHECK",
                {
                    "total_requirements": 10,
                    "covered_requirements": 9,
                    "coverage_percentage": 90,
                    "missing_requirements": [],
                    "threshold": 80,
                    "passed": True,
                },
            )

            log_decision(
                terminal_id,
                "VERIFICATION_SPEC_COMPLIANCE_CHECK",
                {
                    "total_specs": 5,
                    "compliant_specs": 5,
                    "compliance_percentage": 100,
                    "deviations": [],
                    "threshold": 80,
                    "passed": True,
                },
            )

            log_decision(
                terminal_id,
                "VERIFICATION_QUALITY_CHECK",
                {
                    "quality_score": 8,
                    "user_concerns": [],
                    "issues": [],
                    "recommendations": [],
                    "threshold": 7,
                    "passed": True,
                },
            )

            # Phase 4: Complete verification
            log_decision(
                terminal_id,
                "VERIFICATION_COMPLETE",
                {
                    "passed": True,
                    "report_path": ".claude/loop/verification-report.md",
                    "duration_seconds": 2,
                },
            )

            # Phase 5: Update metrics
            update_metrics(
                terminal_id,
                {
                    "verification_runs": 1,
                    "verification_passes": 1,
                    "last_verification": datetime.now().isoformat(),
                    "verification_passed": True,
                },
            )

            # Verify complete lifecycle
            log_file = temp_state_dirs.get_log_dir(terminal_id) / "decision.log"
            content = log_file.read_text()
            entries = [json.loads(line) for line in content.strip().split("\n")]

            assert len(entries) == 6

            # Verify event sequence
            event_sequence = [e["event"] for e in entries]
            expected_sequence = [
                "VERIFICATION_TRIGGERED",
                "VERIFICATION_START",
                "VERIFICATION_PRD_COVERAGE_CHECK",
                "VERIFICATION_SPEC_COMPLIANCE_CHECK",
                "VERIFICATION_QUALITY_CHECK",
                "VERIFICATION_COMPLETE",
            ]
            assert event_sequence == expected_sequence

            # Verify metrics
            metrics = self.get_metrics_from_dir(
                temp_state_dirs.get_state_dir(terminal_id)
            )
            assert metrics["verification_runs"] == 1
            assert metrics["verification_passes"] == 1
            assert metrics["verification_passed"] is True

    def test_verification_failure_observability(self, temp_state_dirs):
        """Test observability when verification fails."""
        terminal_id = "test_verification_failure"

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
            # Log failed verification
            log_decision(
                terminal_id,
                "VERIFICATION_PRD_COVERAGE_CHECK",
                {
                    "total_requirements": 10,
                    "covered_requirements": 7,
                    "coverage_percentage": 70,
                    "missing_requirements": ["Feature A", "Feature B", "Feature C"],
                    "threshold": 80,
                    "passed": False,
                },
            )

            log_decision(
                terminal_id,
                "VERIFICATION_COMPLETE",
                {
                    "passed": False,
                    "report_path": ".claude/loop/verification-report.md",
                    "duration_seconds": 2,
                },
            )

            update_metrics(
                terminal_id,
                {
                    "verification_runs": 1,
                    "verification_failures": 1,
                    "last_verification": datetime.now().isoformat(),
                    "verification_passed": False,
                },
            )

            # Verify failure was recorded
            log_file = temp_state_dirs.get_log_dir(terminal_id) / "decision.log"
            content = log_file.read_text()
            entries = [json.loads(line) for line in content.strip().split("\n")]

            # Check that failure is evident in events
            assert any(e["payload"]["passed"] is False for e in entries)

            # Check metrics reflect failure
            metrics = self.get_metrics_from_dir(
                temp_state_dirs.get_state_dir(terminal_id)
            )
            assert metrics["verification_runs"] == 1
            assert metrics["verification_failures"] == 1
            assert metrics["verification_passed"] is False

    def test_multiple_verification_runs_observability(self, temp_state_dirs):
        """Test observability across multiple verification runs."""
        terminal_id = "test_multiple_verifications"

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
            # First verification (fails)
            log_decision(
                terminal_id, "VERIFICATION_TRIGGERED", {"reason": "iteration_complete"}
            )
            log_decision(
                terminal_id,
                "VERIFICATION_COMPLETE",
                {"passed": False, "duration_seconds": 2},
            )
            update_metrics(
                terminal_id, {"verification_runs": 1, "verification_failures": 1}
            )

            # Second verification (fails)
            log_decision(
                terminal_id, "VERIFICATION_TRIGGERED", {"reason": "iteration_complete"}
            )
            log_decision(
                terminal_id,
                "VERIFICATION_COMPLETE",
                {"passed": False, "duration_seconds": 2},
            )
            update_metrics(
                terminal_id, {"verification_runs": 1, "verification_failures": 1}
            )

            # Third verification (passes)
            log_decision(
                terminal_id, "VERIFICATION_TRIGGERED", {"reason": "iteration_complete"}
            )
            log_decision(
                terminal_id,
                "VERIFICATION_COMPLETE",
                {"passed": True, "duration_seconds": 2},
            )
            update_metrics(
                terminal_id,
                {
                    "verification_runs": 1,
                    "verification_passes": 1,
                    "verification_passed": True,
                },
            )

            # Verify all runs are recorded
            log_file = temp_state_dirs.get_log_dir(terminal_id) / "decision.log"
            content = log_file.read_text()
            entries = [json.loads(line) for line in content.strip().split("\n")]

            # Should have 6 events (3 runs × 2 events each)
            assert len(entries) == 6

            # Count verification triggers and completions
            triggers = [e for e in entries if e["event"] == "VERIFICATION_TRIGGERED"]
            completions = [e for e in entries if e["event"] == "VERIFICATION_COMPLETE"]

            assert len(triggers) == 3
            assert len(completions) == 3

            # Verify metrics show total runs
            metrics = self.get_metrics_from_dir(
                temp_state_dirs.get_state_dir(terminal_id)
            )
            assert metrics["verification_runs"] == 3
            assert metrics["verification_failures"] == 2
            assert metrics["verification_passes"] == 1
            assert metrics["verification_passed"] is True  # Last verification passed

    def test_verification_chronological_ordering(self, temp_state_dirs):
        """Test that verification events are logged in chronological order."""
        terminal_id = "test_verification_ordering"

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
            # Log events in sequence
            events = [
                ("VERIFICATION_TRIGGERED", {}),
                ("VERIFICATION_START", {}),
                ("VERIFICATION_PRD_COVERAGE_CHECK", {}),
                ("VERIFICATION_SPEC_COMPLIANCE_CHECK", {}),
                ("VERIFICATION_QUALITY_CHECK", {}),
                ("VERIFICATION_COMPLETE", {}),
            ]

            for event, payload in events:
                log_decision(terminal_id, event, payload)
                # Small delay to ensure different timestamps
                import time

                time.sleep(0.001)

            # Verify chronological order
            log_file = temp_state_dirs.get_log_dir(terminal_id) / "decision.log"
            content = log_file.read_text()
            entries = [json.loads(line) for line in content.strip().split("\n")]

            timestamps = [e["timestamp"] for e in entries]
            assert timestamps == sorted(timestamps)

            # Verify event order is preserved
            logged_events = [e["event"] for e in entries]
            expected_events = [e[0] for e in events]
            assert logged_events == expected_events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
