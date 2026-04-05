"""Tests for loop_metrics_summary module (RED phase - TDD)."""

import json


from scripts.loop_metrics_summary import (
    aggregate_metrics,
    collect_terminal_data,
    format_summary_report,
    parse_decision_log,
    parse_loop_metrics,
    validate_cross_terminal_isolation,
)


class TestParseDecisionLog:
    """Test suite for parsing decision.log files."""

    def test_parse_valid_log_file(self, tmp_path):
        """Test parsing a valid decision.log with JSON lines."""
        log_file = tmp_path / "decision.log"

        # Create test log entries
        entries = [
            {"terminal_id": "term_1", "event": "task_start", "payload": {"task": "A"}},
            {"terminal_id": "term_1", "event": "error", "payload": {"error": "failed"}},
            {"terminal_id": "term_1", "event": "exit", "payload": {"reason": "complete"}},
        ]

        log_content = "\n".join(json.dumps(entry) for entry in entries)
        log_file.write_text(log_content)

        # Parse and verify
        parsed = parse_decision_log(log_file)

        assert len(parsed) == 3
        assert parsed[0]["event"] == "task_start"
        assert parsed[1]["event"] == "error"
        assert parsed[2]["event"] == "exit"

    def test_parse_empty_log_file(self, tmp_path):
        """Test parsing an empty decision.log."""
        log_file = tmp_path / "decision.log"
        log_file.write_text("")

        parsed = parse_decision_log(log_file)

        assert parsed == []

    def test_parse_malformed_log_entries(self, tmp_path):
        """Test parsing log file with some malformed JSON lines."""
        log_file = tmp_path / "decision.log"

        # Mix of valid and invalid JSON
        log_content = """{"event": "valid", "payload": {}}
invalid json line
{"event": "another_valid", "payload": {}}
{incomplete json
"""
        log_file.write_text(log_content)

        # Should skip malformed entries
        parsed = parse_decision_log(log_file)

        assert len(parsed) == 2
        assert parsed[0]["event"] == "valid"
        assert parsed[1]["event"] == "another_valid"

    def test_parse_nonexistent_log_file(self, tmp_path):
        """Test parsing a non-existent log file returns empty list."""
        log_file = tmp_path / "nonexistent.log"

        parsed = parse_decision_log(log_file)

        assert parsed == []


class TestParseLoopMetrics:
    """Test suite for parsing loop_metrics.json files."""

    def test_parse_valid_metrics_file(self, tmp_path):
        """Test parsing a valid loop_metrics.json."""
        metrics_file = tmp_path / "loop_metrics.json"

        metrics = {
            "iterations": 5,
            "tasks_completed": 3,
            "errors": 2,
            "last_update": "2026-03-15T10:00:00",
            "total_duration": 300,
        }

        metrics_file.write_text(json.dumps(metrics))

        parsed = parse_loop_metrics(metrics_file)

        assert parsed["iterations"] == 5
        assert parsed["tasks_completed"] == 3
        assert parsed["errors"] == 2
        assert parsed["total_duration"] == 300

    def test_parse_minimal_metrics(self, tmp_path):
        """Test parsing metrics with minimal fields."""
        metrics_file = tmp_path / "loop_metrics.json"

        metrics = {"iterations": 1}
        metrics_file.write_text(json.dumps(metrics))

        parsed = parse_loop_metrics(metrics_file)

        assert parsed["iterations"] == 1

    def test_parse_corrupted_metrics_file(self, tmp_path):
        """Test parsing corrupted metrics returns None."""
        metrics_file = tmp_path / "loop_metrics.json"
        metrics_file.write_text("{invalid json content")

        parsed = parse_loop_metrics(metrics_file)

        assert parsed is None

    def test_parse_nonexistent_metrics_file(self, tmp_path):
        """Test parsing non-existent metrics returns None."""
        metrics_file = tmp_path / "nonexistent.json"

        parsed = parse_loop_metrics(metrics_file)

        assert parsed is None


class TestCollectTerminalData:
    """Test suite for collecting data from terminal directories."""

    def test_collect_from_multiple_terminals(self, tmp_path):
        """Test collecting data from multiple terminal directories."""
        # Create terminal directories
        term_a = tmp_path / "terminals" / "terminal_a"
        term_b = tmp_path / "terminals" / "terminal_b"
        term_a.mkdir(parents=True)
        term_b.mkdir(parents=True)

        # Create decision logs
        (term_a / "decision.log").write_text('{"event": "test_a"}\n')
        (term_b / "decision.log").write_text('{"event": "test_b"}\n')

        # Create metrics files
        (term_a / "loop_metrics.json").write_text('{"errors": 1}')
        (term_b / "loop_metrics.json").write_text('{"errors": 2}')

        # Collect data
        terminals_data = collect_terminal_data(tmp_path / "terminals")

        assert len(terminals_data) == 2

        # Verify both terminals present
        terminal_ids = {data["terminal_id"] for data in terminals_data}
        assert "terminal_a" in terminal_ids
        assert "terminal_b" in terminal_ids

    def test_collect_from_single_terminal(self, tmp_path):
        """Test collecting data from single terminal."""
        term_dir = tmp_path / "terminals" / "single_terminal"
        term_dir.mkdir(parents=True)

        (term_dir / "decision.log").write_text('{"event": "test"}')
        (term_dir / "loop_metrics.json").write_text('{"errors": 0}')

        terminals_data = collect_terminal_data(tmp_path / "terminals")

        assert len(terminals_data) == 1
        assert terminals_data[0]["terminal_id"] == "single_terminal"

    def test_collect_handles_missing_files(self, tmp_path):
        """Test collecting handles terminals with missing files."""
        term_dir = tmp_path / "terminals" / "incomplete_terminal"
        term_dir.mkdir(parents=True)

        # Only decision.log, no metrics
        (term_dir / "decision.log").write_text('{"event": "test"}')

        terminals_data = collect_terminal_data(tmp_path / "terminals")

        assert len(terminals_data) == 1
        assert terminals_data[0]["metrics"] is None

    def test_collect_from_empty_directory(self, tmp_path):
        """Test collecting from terminals directory with no terminals."""
        terminals_dir = tmp_path / "terminals"
        terminals_dir.mkdir(parents=True)

        terminals_data = collect_terminal_data(terminals_dir)

        assert terminals_data == []

    def test_collect_nonexistent_directory(self, tmp_path):
        """Test collecting from non-existent directory returns empty list."""
        terminals_data = collect_terminal_data(tmp_path / "nonexistent")

        assert terminals_data == []


class TestAggregateMetrics:
    """Test suite for aggregating metrics across terminals."""

    def test_aggregate_basic_metrics(self):
        """Test aggregating basic metrics from multiple terminals."""
        terminals_data = [
            {
                "terminal_id": "term_a",
                "metrics": {"errors": 2, "iterations": 5, "tasks_completed": 3},
                "decision_log": [{"event": "exit", "payload": {"reason": "complete"}}],
            },
            {
                "terminal_id": "term_b",
                "metrics": {"errors": 1, "iterations": 3, "tasks_completed": 2},
                "decision_log": [{"event": "exit", "payload": {"reason": "error"}}],
            },
        ]

        aggregated = aggregate_metrics(terminals_data)

        assert aggregated["total_terminals"] == 2
        assert aggregated["total_errors"] == 3
        assert aggregated["total_iterations"] == 8
        assert aggregated["total_tasks_completed"] == 5

    def test_aggregate_with_missing_metrics(self):
        """Test aggregating when some terminals have missing metrics."""
        terminals_data = [
            {
                "terminal_id": "term_a",
                "metrics": {"errors": 2, "iterations": 5},
                "decision_log": [],
            },
            {
                "terminal_id": "term_b",
                "metrics": None,  # Missing metrics
                "decision_log": [],
            },
        ]

        aggregated = aggregate_metrics(terminals_data)

        assert aggregated["total_terminals"] == 2
        assert aggregated["total_errors"] == 2
        assert aggregated["total_iterations"] == 5

    def test_aggregate_exit_reasons(self):
        """Test aggregating exit reasons from decision logs."""
        terminals_data = [
            {
                "terminal_id": "term_a",
                "metrics": {},
                "decision_log": [
                    {"event": "exit", "payload": {"reason": "complete"}},
                    {"event": "exit", "payload": {"reason": "timeout"}},
                ],
            },
            {
                "terminal_id": "term_b",
                "metrics": {},
                "decision_log": [
                    {"event": "exit", "payload": {"reason": "complete"}},
                ],
            },
        ]

        aggregated = aggregate_metrics(terminals_data)

        assert aggregated["exit_reasons"]["complete"] == 2
        assert aggregated["exit_reasons"]["timeout"] == 1

    def test_aggregate_error_events(self):
        """Test counting error events from decision logs."""
        terminals_data = [
            {
                "terminal_id": "term_a",
                "metrics": {"errors": 2},
                "decision_log": [
                    {"event": "error", "payload": {"type": "validation"}},
                    {"event": "error", "payload": {"type": "runtime"}},
                    {"event": "task_complete", "payload": {}},
                ],
            },
        ]

        aggregated = aggregate_metrics(terminals_data)

        assert aggregated["error_events"]["term_a"] == 2
        assert aggregated["total_errors"] == 2


class TestValidateCrossTerminalIsolation:
    """Test suite for cross-terminal isolation validation."""

    def test_validate_isolated_terminals(self):
        """Test validation passes for properly isolated terminals."""
        terminals_data = [
            {
                "terminal_id": "term_a",
                "metrics": {},
                "decision_log": [
                    {"event": "task_start", "payload": {"terminal": "term_a"}},
                    {"event": "task_complete", "payload": {"terminal": "term_a"}},
                ],
            },
            {
                "terminal_id": "term_b",
                "metrics": {},
                "decision_log": [
                    {"event": "task_start", "payload": {"terminal": "term_b"}},
                    {"event": "task_complete", "payload": {"terminal": "term_b"}},
                ],
            },
        ]

        validation = validate_cross_terminal_isolation(terminals_data)

        assert validation["is_isolated"] is True
        assert len(validation["violations"]) == 0

    def test_detect_cross_terminal_state_modification(self):
        """Test detection of cross-terminal state modifications."""
        terminals_data = [
            {
                "terminal_id": "term_a",
                "metrics": {},
                "decision_log": [
                    {"event": "state_modify", "payload": {"target_terminal": "term_b"}},
                ],
            },
            {
                "terminal_id": "term_b",
                "metrics": {},
                "decision_log": [],
            },
        ]

        validation = validate_cross_terminal_isolation(terminals_data)

        assert validation["is_isolated"] is False
        assert len(validation["violations"]) > 0
        assert "cross_terminal_modification" in validation["violations"][0]["type"]

    def test_validate_with_empty_logs(self):
        """Test validation with empty decision logs."""
        terminals_data = [
            {
                "terminal_id": "term_a",
                "metrics": {},
                "decision_log": [],
            },
            {
                "terminal_id": "term_b",
                "metrics": {},
                "decision_log": [],
            },
        ]

        validation = validate_cross_terminal_isolation(terminals_data)

        assert validation["is_isolated"] is True

    def test_validate_foreign_terminal_access(self):
        """Test detection of foreign terminal access patterns."""
        terminals_data = [
            {
                "terminal_id": "term_a",
                "metrics": {},
                "decision_log": [
                    {
                        "event": "file_access",
                        "payload": {"path": ".claude/state/terminals/term_b/state.json"},
                    },
                ],
            },
            {
                "terminal_id": "term_b",
                "metrics": {},
                "decision_log": [],
            },
        ]

        validation = validate_cross_terminal_isolation(terminals_data)

        assert validation["is_isolated"] is False
        assert len(validation["violations"]) > 0


class TestFormatSummaryReport:
    """Test suite for formatting summary report."""

    def test_format_basic_report(self):
        """Test formatting a basic summary report."""
        aggregated = {
            "total_terminals": 2,
            "total_errors": 3,
            "total_iterations": 10,
            "total_tasks_completed": 8,
            "exit_reasons": {"complete": 1, "error": 1},
            "error_events": {},
        }

        validation = {
            "is_isolated": True,
            "violations": [],
        }

        report = format_summary_report(aggregated, validation)

        assert "Terminal Summary" in report
        assert "Total terminals: 2" in report
        assert "Total errors: 3" in report
        assert "Total iterations: 10" in report
        assert "Total tasks completed: 8" in report
        assert "Cross-Terminal Validation" in report

    def test_format_report_with_validation_failures(self):
        """Test formatting report with isolation violations."""
        aggregated = {"total_terminals": 2, "exit_reasons": {}, "error_events": {}}

        validation = {
            "is_isolated": False,
            "violations": [
                {"type": "cross_terminal_modification", "terminal": "term_a", "details": "..."}
            ],
        }

        report = format_summary_report(aggregated, validation)

        assert "VIOLATIONS DETECTED" in report
        assert "cross_terminal_modification" in report

    def test_format_report_with_detailed_metrics(self):
        """Test formatting report with per-terminal metrics."""
        aggregated = {
            "total_terminals": 2,
            "total_errors": 0,
            "exit_reasons": {"complete": 2},
            "error_events": {},
            "per_terminal": [
                {"terminal_id": "term_a", "errors": 0, "exit_reason": "complete"},
                {"terminal_id": "term_b", "errors": 0, "exit_reason": "complete"},
            ],
        }

        validation = {"is_isolated": True, "violations": []}

        report = format_summary_report(aggregated, validation)

        assert "term_a" in report
        assert "term_b" in report


class TestIntegrationScenarios:
    """Integration tests for complete workflow."""

    def test_full_workflow_with_real_data(self, tmp_path):
        """Test complete workflow from scan to report."""
        # Create test terminal structure
        term_1 = tmp_path / "terminals" / "console_abc123"
        term_2 = tmp_path / "terminals" / "console_def456"
        term_1.mkdir(parents=True)
        term_2.mkdir(parents=True)

        # Write decision logs
        (term_1 / "decision.log").write_text(
            """{"terminal_id": "console_abc123", "event": "iteration_start", "payload": {}}
{"terminal_id": "console_abc123", "event": "task_complete", "payload": {"task_id": "TASK-001"}}
{"terminal_id": "console_abc123", "event": "error", "payload": {"type": "validation"}}
{"terminal_id": "console_abc123", "event": "exit", "payload": {"reason": "verification_passed"}}
"""
        )

        (term_2 / "decision.log").write_text(
            """{"terminal_id": "console_def456", "event": "task_complete", "payload": {"task_id": "TASK-002"}}
{"terminal_id": "console_def456", "event": "exit", "payload": {"reason": "tasks_complete"}}
"""
        )

        # Write metrics files
        (term_1 / "loop_metrics.json").write_text(
            """{"iterations": 3, "tasks_completed": 3, "errors": 1, "total_duration": 150}"""
        )

        (term_2 / "loop_metrics.json").write_text(
            """{"iterations": 1, "tasks_completed": 1, "errors": 0, "total_duration": 50}"""
        )

        # Execute workflow
        terminals_data = collect_terminal_data(tmp_path / "terminals")
        aggregated = aggregate_metrics(terminals_data)
        validation = validate_cross_terminal_isolation(terminals_data)
        report = format_summary_report(aggregated, validation)

        # Verify results
        assert len(terminals_data) == 2
        assert aggregated["total_terminals"] == 2
        assert aggregated["total_errors"] == 1
        assert aggregated["total_tasks_completed"] == 4
        assert validation["is_isolated"] is True
        assert "console_abc123" in report
        assert "console_def456" in report
        assert "1 errors" in report

    def test_workflow_handles_corrupted_data(self, tmp_path):
        """Test workflow handles corrupted files gracefully."""
        # Create terminal with corrupted data
        term_dir = tmp_path / "terminals" / "corrupted_term"
        term_dir.mkdir(parents=True)

        # Corrupted decision log
        (term_dir / "decision.log").write_text("invalid json\n{" "incomplete")

        # Corrupted metrics file
        (term_dir / "loop_metrics.json").write_text("{invalid")

        # Should not crash
        terminals_data = collect_terminal_data(tmp_path / "terminals")
        aggregated = aggregate_metrics(terminals_data)
        validation = validate_cross_terminal_isolation(terminals_data)
        report = format_summary_report(aggregated, validation)

        # Should produce report despite corruption
        assert isinstance(report, str)

    def test_workflow_with_no_terminals(self, tmp_path):
        """Test workflow when no terminals exist."""
        terminals_dir = tmp_path / "terminals"
        terminals_dir.mkdir(parents=True)

        terminals_data = collect_terminal_data(terminals_dir)
        aggregated = aggregate_metrics(terminals_data)
        validation = validate_cross_terminal_isolation(terminals_data)
        report = format_summary_report(aggregated, validation)

        assert "No terminal data found" in report
