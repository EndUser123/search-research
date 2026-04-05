"""Unit tests for performance_logger module.

Tests CLI performance tracking, JSONL logging, thread-safety, and multi-terminal safety.
"""

from threading import Thread

from performance_logger import CliExecutionRecord, CliPerformanceLogger
from task_classifier import TaskType


class TestCliExecutionRecord:
    """Test CliExecutionRecord dataclass."""

    def test_record_creation(self):
        """Test creating a record with all fields."""
        record = CliExecutionRecord(
            timestamp="2026-02-28T12:00:00",
            cli_name="qwen",
            task_type="code_review",
            query_preview="review this code",
            duration_seconds=63.5,
            outcome="success",
            output_length=1500,
            error_message=None,
        )
        assert record.cli_name == "qwen"
        assert record.task_type == "code_review"
        assert record.duration_seconds == 63.5

    def test_to_jsonl(self):
        """Test record serializes to valid JSON."""
        record = CliExecutionRecord(
            timestamp="2026-02-28T12:00:00",
            cli_name="gemini",
            task_type="planning",
            query_preview="create a plan",
            duration_seconds=160.2,
            outcome="success",
            output_length=2300,
        )
        jsonl = record.to_jsonl()
        assert isinstance(jsonl, str)
        assert '"cli_name": "gemini"' in jsonl
        assert '"task_type": "planning"' in jsonl


class TestPerformanceLogger:
    """Test CliPerformanceLogger functionality."""

    def test_logger_initialization(self, tmp_path):
        """Test logger initializes with custom path."""
        log_path = tmp_path / "test_perf.jsonl"
        logger = CliPerformanceLogger(str(log_path))
        assert logger.log_path == log_path
        assert logger.log_path.parent.exists()

    def test_logger_default_path(self):
        """Test logger uses default path when none provided."""
        logger = CliPerformanceLogger()
        assert str(logger.log_path).endswith("llm_cli_performance.jsonl")

    def test_log_execution_creates_file(self, tmp_path):
        """Test logging creates JSONL file."""
        log_path = tmp_path / "test_log.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        logger.log_execution(
            cli_name="qwen",
            task_type=TaskType.CODE_REVIEW,
            query="review this code",
            duration_seconds=63.5,
            outcome="success",
            output_length=1500,
        )

        assert log_path.exists()

    def test_log_execution_appends_record(self, tmp_path):
        """Test logging appends records to file."""
        log_path = tmp_path / "test_append.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        logger.log_execution(
            cli_name="qwen",
            task_type=TaskType.CODE_REVIEW,
            query="review this",
            duration_seconds=60.0,
            outcome="success",
            output_length=1000,
        )

        logger.log_execution(
            cli_name="gemini",
            task_type=TaskType.PLANNING,
            query="plan this",
            duration_seconds=120.0,
            outcome="success",
            output_length=2000,
        )

        # Verify 2 lines in file
        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2

    def test_get_all_records(self, tmp_path):
        """Test reading all records from log."""
        log_path = tmp_path / "test_read.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        logger.log_execution(
            cli_name="codex",
            task_type=TaskType.DEBUG,
            query="debug this",
            duration_seconds=45.0,
            outcome="success",
            output_length=800,
        )

        records = logger.get_all_records()
        assert len(records) == 1
        assert records[0].cli_name == "codex"
        assert records[0].task_type == "debug"

    def test_get_all_records_empty_file(self, tmp_path):
        """Test reading from nonexistent log returns empty list."""
        log_path = tmp_path / "nonexistent.jsonl"
        logger = CliPerformanceLogger(str(log_path))
        records = logger.get_all_records()
        assert records == []

    def test_get_records_for_task(self, tmp_path):
        """Test filtering records by task type."""
        log_path = tmp_path / "test_filter_task.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        logger.log_execution(
            cli_name="qwen",
            task_type=TaskType.CODE_REVIEW,
            query="review this",
            duration_seconds=60.0,
            outcome="success",
            output_length=1000,
        )

        logger.log_execution(
            cli_name="gemini",
            task_type=TaskType.PLANNING,
            query="plan this",
            duration_seconds=120.0,
            outcome="success",
            output_length=2000,
        )

        code_review_records = logger.get_records_for_task(TaskType.CODE_REVIEW)
        assert len(code_review_records) == 1
        assert code_review_records[0].cli_name == "qwen"

    def test_get_records_for_cli(self, tmp_path):
        """Test filtering records by CLI name."""
        log_path = tmp_path / "test_filter_cli.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        logger.log_execution(
            cli_name="qwen",
            task_type=TaskType.CODE_REVIEW,
            query="review",
            duration_seconds=60.0,
            outcome="success",
            output_length=1000,
        )

        logger.log_execution(
            cli_name="qwen",
            task_type=TaskType.PLANNING,
            query="plan",
            duration_seconds=120.0,
            outcome="success",
            output_length=2000,
        )

        logger.log_execution(
            cli_name="gemini",
            task_type=TaskType.DEBUG,
            query="debug",
            duration_seconds=45.0,
            outcome="success",
            output_length=800,
        )

        qwen_records = logger.get_records_for_cli("qwen")
        assert len(qwen_records) == 2

        gemini_records = logger.get_records_for_cli("gemini")
        assert len(gemini_records) == 1

    def test_get_performance_stats(self, tmp_path):
        """Test calculating performance statistics."""
        log_path = tmp_path / "test_stats.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        # Log 2 successful, 1 failed for qwen
        logger.log_execution(
            cli_name="qwen",
            task_type=TaskType.CODE_REVIEW,
            query="review",
            duration_seconds=60.0,
            outcome="success",
            output_length=1000,
        )

        logger.log_execution(
            cli_name="qwen",
            task_type=TaskType.CODE_REVIEW,
            query="review again",
            duration_seconds=70.0,
            outcome="success",
            output_length=1500,
        )

        logger.log_execution(
            cli_name="qwen",
            task_type=TaskType.DEBUG,
            query="debug",
            duration_seconds=45.0,
            outcome="error",
            output_length=0,
            error_message="Connection timeout",
        )

        stats = logger.get_performance_stats()
        assert "qwen" in stats
        assert stats["qwen"]["total_executions"] == 3
        assert stats["qwen"]["success_rate"] == 2 / 3
        assert stats["qwen"]["avg_duration"] == (60.0 + 70.0 + 45.0) / 3
        assert stats["qwen"]["avg_output_length"] == (1000 + 1500 + 0) / 3

    def test_get_performance_stats_with_task_filter(self, tmp_path):
        """Test stats calculation filters by task type."""
        log_path = tmp_path / "test_stats_filter.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        logger.log_execution(
            cli_name="qwen",
            task_type=TaskType.CODE_REVIEW,
            query="review",
            duration_seconds=60.0,
            outcome="success",
            output_length=1000,
        )

        logger.log_execution(
            cli_name="qwen",
            task_type=TaskType.PLANNING,
            query="plan",
            duration_seconds=120.0,
            outcome="success",
            output_length=2000,
        )

        stats = logger.get_performance_stats(task_type=TaskType.CODE_REVIEW)
        assert stats["qwen"]["total_executions"] == 1
        assert stats["qwen"]["avg_duration"] == 60.0

    def test_query_truncated_to_100_chars(self, tmp_path):
        """Test long queries are truncated to 100 chars."""
        log_path = tmp_path / "test_truncate.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        long_query = "x" * 200
        logger.log_execution(
            cli_name="vibe",
            task_type=TaskType.GENERAL,
            query=long_query,
            duration_seconds=30.0,
            outcome="success",
            output_length=500,
        )

        records = logger.get_all_records()
        assert len(records[0].query_preview) == 100


class TestJSONLFormat:
    """Test JSONL file format and parsing."""

    def test_each_line_is_valid_json(self, tmp_path):
        """Test each line in log file is valid JSON."""
        log_path = tmp_path / "test_json_valid.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        for i in range(5):
            logger.log_execution(
                cli_name="opencode",
                task_type=TaskType.REFACTOR,
                query=f"query {i}",
                duration_seconds=float(i),
                outcome="success",
                output_length=i * 100,
            )

        import json

        with open(log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    assert "timestamp" in data
                    assert "cli_name" in data
                    assert "task_type" in data

    def test_records_parsed_from_jsonl(self, tmp_path):
        """Test records can be parsed from JSONL file."""
        log_path = tmp_path / "test_parse.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        logger.log_execution(
            cli_name="glm-4.7-flash",
            task_type=TaskType.RESEARCH,
            query="research this",
            duration_seconds=55.0,
            outcome="success",
            output_length=1200,
        )

        records = logger.get_all_records()
        assert len(records) == 1
        assert isinstance(records[0], CliExecutionRecord)
        assert records[0].cli_name == "glm-4.7-flash"


class TestThreadSafety:
    """Test thread-safety for concurrent writes (critical for multi-terminal safety)."""

    def test_concurrent_writes_no_corruption(self, tmp_path):
        """Test concurrent writes don't corrupt data.

        Simulates 10 terminals writing 50 records each = 500 total records.
        Verifies all records are written correctly with no data corruption.
        """
        log_path = tmp_path / "test_concurrent.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        num_threads = 10
        writes_per_thread = 50
        errors = []

        def write_records(thread_id: int):
            """Write records from a thread."""
            try:
                for i in range(writes_per_thread):
                    logger.log_execution(
                        cli_name=f"cli_{thread_id}",
                        task_type=TaskType.GENERAL,
                        query=f"thread {thread_id} query {i}",
                        duration_seconds=float(i),
                        outcome="success",
                        output_length=i * 10,
                    )
            except Exception as e:
                errors.append((thread_id, e))

        # Create and start threads
        threads = []
        for i in range(num_threads):
            t = Thread(target=write_records, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify all records were written
        records = logger.get_all_records()
        expected_records = num_threads * writes_per_thread
        assert (
            len(records) == expected_records
        ), f"Expected {expected_records} records, got {len(records)}"

        # Verify records are valid (no corruption)
        for record in records:
            assert isinstance(record.cli_name, str)
            assert isinstance(record.task_type, str)
            assert isinstance(record.duration_seconds, float)
            assert isinstance(record.output_length, int)

    def test_thread_lock_prevents_data_loss(self, tmp_path):
        """Test thread lock prevents data loss during rapid concurrent writes."""
        log_path = tmp_path / "test_lock.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        num_writes = 100
        threads = []
        errors = []

        def rapid_write(thread_id: int):
            try:
                for i in range(num_writes):
                    logger.log_execution(
                        cli_name="qwen",
                        task_type=TaskType.GENERAL,
                        query=f"query_{thread_id}_{i}",
                        duration_seconds=1.0,
                        outcome="success",
                        output_length=100,
                    )
            except Exception as e:
                errors.append(e)

        # Launch 5 threads doing rapid writes
        for i in range(5):
            t = Thread(target=rapid_write, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should have 5 threads × 100 writes = 500 records
        assert len(errors) == 0, f"Errors during concurrent writes: {errors}"
        records = logger.get_all_records()
        assert len(records) == 500, f"Expected 500 records, got {len(records)}"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_nonexistent_log_returns_empty_list(self, tmp_path):
        """Test reading from nonexistent log returns empty list."""
        log_path = tmp_path / "does_not_exist.jsonl"
        logger = CliPerformanceLogger(str(log_path))
        records = logger.get_all_records()
        assert records == []

    def test_corrupt_lines_skipped_gracefully(self, tmp_path):
        """Test corrupt JSON lines are skipped gracefully."""
        log_path = tmp_path / "test_corrupt.jsonl"

        # Create log with some corrupt lines
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(
                '{"timestamp": "2026-02-28T12:00:00", "cli_name": "qwen", "task_type": "code_review", "query_preview": "review", "duration_seconds": 60.0, "outcome": "success", "output_length": 1000}\n'
            )
            f.write("this is not valid json\n")
            f.write(
                '{"timestamp": "2026-02-28T12:01:00", "cli_name": "gemini", "task_type": "planning", "query_preview": "plan", "duration_seconds": 120.0, "outcome": "success", "output_length": 2000}\n'
            )
            f.write("also not valid\n")

        logger = CliPerformanceLogger(str(log_path))
        records = logger.get_all_records()

        # Should skip corrupt lines and return 2 valid records
        assert len(records) == 2
        assert records[0].cli_name == "qwen"
        assert records[1].cli_name == "gemini"

    def test_empty_lines_skipped(self, tmp_path):
        """Test empty lines in log file are skipped."""
        log_path = tmp_path / "test_empty.jsonl"

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(
                '{"timestamp": "2026-02-28T12:00:00", "cli_name": "qwen", "task_type": "debug", "query_preview": "debug", "duration_seconds": 45.0, "outcome": "success", "output_length": 800}\n'
            )
            f.write("\n")  # Empty line
            f.write(
                '{"timestamp": "2026-02-28T12:01:00", "cli_name": "vibe", "task_type": "refactor", "query_preview": "refactor", "duration_seconds": 50.0, "outcome": "success", "output_length": 900}\n'
            )
            f.write("\n")  # Another empty line

        logger = CliPerformanceLogger(str(log_path))
        records = logger.get_all_records()
        assert len(records) == 2

    def test_all_outcome_types_logged(self, tmp_path):
        """Test all outcome types can be logged."""
        log_path = tmp_path / "test_outcomes.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        outcomes = ["success", "timeout", "error", "empty_output"]
        for outcome in outcomes:
            logger.log_execution(
                cli_name="test_cli",
                task_type=TaskType.GENERAL,
                query="test",
                duration_seconds=1.0,
                outcome=outcome,
                output_length=100 if outcome == "success" else 0,
                error_message="Test error" if outcome == "error" else None,
            )

        records = logger.get_all_records()
        assert len(records) == 4

        logged_outcomes = {r.outcome for r in records}
        assert logged_outcomes == set(outcomes)

    def test_stats_empty_for_new_log(self, tmp_path):
        """Test stats return empty dict for new log file."""
        log_path = tmp_path / "test_new_stats.jsonl"
        logger = CliPerformanceLogger(str(log_path))
        stats = logger.get_performance_stats()
        assert stats == {}

    def test_error_message_in_record(self, tmp_path):
        """Test error messages are stored in records."""
        log_path = tmp_path / "test_error_msg.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        logger.log_execution(
            cli_name="codex",
            task_type=TaskType.DEBUG,
            query="debug this",
            duration_seconds=30.0,
            outcome="error",
            output_length=0,
            error_message="Connection timeout after 30s",
        )

        records = logger.get_all_records()
        assert len(records) == 1
        assert records[0].outcome == "error"
        assert records[0].error_message == "Connection timeout after 30s"

    def test_all_supported_clis_tracked(self, tmp_path):
        """Test all supported CLI names can be logged."""
        log_path = tmp_path / "test_all_clis.jsonl"
        logger = CliPerformanceLogger(str(log_path))

        supported_clis = [
            "qwen",
            "gemini",
            "codex",
            "vibe",
            "opencode",
            "glm-4.7-flash",
        ]

        for cli in supported_clis:
            logger.log_execution(
                cli_name=cli,
                task_type=TaskType.GENERAL,
                query="test",
                duration_seconds=1.0,
                outcome="success",
                output_length=100,
            )

        records = logger.get_all_records()
        logged_clis = {r.cli_name for r in records}
        assert logged_clis == set(supported_clis)
