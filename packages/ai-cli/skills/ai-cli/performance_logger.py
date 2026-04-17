"""CLI performance logger for tracking execution metrics.

Thread-safe append-only JSONL logging for CLI performance tracking.
Multi-terminal safe: no shared state, no TTL caches, immune to stale data.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from task_classifier import TaskType


@dataclass
class CliExecutionRecord:
    """Single CLI execution record.

    Attributes:
        timestamp: ISO format timestamp of execution
        cli_name: CLI identifier (qwen, gemini, codex, vibe, opencode, glm-4.7-flash)
        task_type: Classified task type
        query_preview: First 100 chars of query (for storage efficiency)
        duration_seconds: Execution time in seconds
        outcome: Execution outcome (success, timeout, error, empty_output)
        output_length: Response character count
        error_message: Error message if outcome is "error"
        quality_score: Optional 1-5 manual rating (future enhancement)
    """

    timestamp: str
    cli_name: str
    task_type: str
    query_preview: str
    duration_seconds: float
    outcome: Literal["success", "timeout", "error", "empty_output"]
    output_length: int
    error_message: str | None = None
    quality_score: int | None = None

    def to_jsonl(self) -> str:
        """Convert record to JSONL line string.

        Returns:
            JSON-formatted string suitable for append-only file writing
        """
        return json.dumps(asdict(self))


class CliPerformanceLogger:
    """Thread-safe append-only logger for CLI performance tracking.

    Uses JSONL format for simplicity and git-friendliness.
    Thread-safe for multi-terminal concurrent access via threading.Lock.

    Design principles:
    - Append-only: No read-modify-write operations
    - Thread-safe: threading.Lock() for concurrent writes
    - No TTL: No caching, immune to stale data issues
    - Multi-terminal: Each terminal writes independently, no shared state

    Log format: One JSON object per line (JSONL)
    """

    def __init__(self, log_path: str | None = None):
        """Initialize logger with optional custom log path.

        Args:
            log_path: Path to JSONL log file. Defaults to P:/__csf/data/llm_cli_performance.jsonl
        """
        if log_path is None:
            log_path = "P:/__csf/data/llm_cli_performance.jsonl"

        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()  # Thread-safe writes

    def log_execution(
        self,
        cli_name: str,
        task_type: TaskType,
        query: str,
        duration_seconds: float,
        outcome: Literal["success", "timeout", "error", "empty_output"],
        output_length: int,
        error_message: str | None = None,
    ) -> None:
        """Log a CLI execution record.

        Thread-safe for concurrent writes from multiple terminals.

        Args:
            cli_name: CLI identifier (qwen, gemini, codex, vibe, opencode, glm-4.7-flash)
            task_type: Classified task type
            query: Original query (truncated to 100 chars for storage)
            duration_seconds: Execution time
            outcome: Execution outcome
            output_length: Response character count
            error_message: Error message if outcome is "error"
        """
        record = CliExecutionRecord(
            timestamp=datetime.now().isoformat(),
            cli_name=cli_name,
            task_type=task_type.value,
            query_preview=query[:100],
            duration_seconds=duration_seconds,
            outcome=outcome,
            output_length=output_length,
            error_message=error_message,
        )

        # Thread-safe append (critical for multi-terminal safety)
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(record.to_jsonl() + "\n")

    def get_all_records(self) -> list[CliExecutionRecord]:
        """Read all records from log file.

        Returns:
            List of CliExecutionRecord objects (empty list if file doesn't exist)
        """
        if not self.log_path.exists():
            return []

        records = []
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    records.append(CliExecutionRecord(**data))
                except (json.JSONDecodeError, TypeError):
                    # Skip corrupt lines (graceful degradation)
                    continue

        return records

    def get_records_for_task(self, task_type: TaskType) -> list[CliExecutionRecord]:
        """Get all records for a specific task type.

        Args:
            task_type: Task type to filter by

        Returns:
            List of records for this task type
        """
        all_records = self.get_all_records()
        return [r for r in all_records if r.task_type == task_type.value]

    def get_records_for_cli(self, cli_name: str) -> list[CliExecutionRecord]:
        """Get all records for a specific CLI.

        Args:
            cli_name: CLI name to filter by (qwen, gemini, codex, etc.)

        Returns:
            List of records for this CLI
        """
        all_records = self.get_all_records()
        return [r for r in all_records if r.cli_name == cli_name]

    def get_performance_stats(self, task_type: TaskType | None = None) -> dict:
        """Calculate performance statistics for CLI execution.

        Args:
            task_type: Optional task type filter. If None, stats for all tasks.

        Returns:
            Dictionary with performance metrics:
            {
                "cli_name": {
                    "total_executions": int,
                    "success_rate": float (0-1),
                    "avg_duration": float (seconds),
                    "avg_output_length": int,
                }
            }
        """
        records = self.get_records_for_task(task_type) if task_type else self.get_all_records()

        if not records:
            return {}

        stats = {}
        for cli in ["qwen", "gemini", "codex", "vibe", "opencode", "glm-4.7-flash"]:
            cli_records = [r for r in records if r.cli_name == cli]
            if not cli_records:
                continue

            successful = [r for r in cli_records if r.outcome == "success"]
            stats[cli] = {
                "total_executions": len(cli_records),
                "success_rate": len(successful) / len(cli_records),
                "avg_duration": sum(r.duration_seconds for r in cli_records) / len(cli_records),
                "avg_output_length": sum(r.output_length for r in cli_records) / len(cli_records),
            }

        return stats


# Test function for development
def _test_performance_logger():
    """Test performance logger functionality."""
    import os
    import tempfile

    # Create temporary log file for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_log = os.path.join(tmpdir, "test_performance.jsonl")
        logger = CliPerformanceLogger(test_log)

        print("Performance Logger Tests:")
        print("=" * 80)

        # Test 1: Log some executions
        print("\n1. Logging test executions...")
        logger.log_execution(
            cli_name="qwen",
            task_type=TaskType.CODE_REVIEW,
            query="review this code for bugs",
            duration_seconds=63.5,
            outcome="success",
            output_length=1500,
        )

        logger.log_execution(
            cli_name="gemini",
            task_type=TaskType.PLANNING,
            query="create a plan for X",
            duration_seconds=160.2,
            outcome="success",
            output_length=2300,
        )

        logger.log_execution(
            cli_name="codex",
            task_type=TaskType.DEBUG,
            query="debug this error",
            duration_seconds=45.0,
            outcome="error",
            output_length=0,
            error_message="Connection timeout",
        )

        print("   ✓ Logged 3 test records")

        # Test 2: Read all records
        print("\n2. Reading all records...")
        records = logger.get_all_records()
        print(f"   ✓ Read {len(records)} records")

        # Test 3: Filter by task type
        print("\n3. Filtering by task type...")
        code_review_records = logger.get_records_for_task(TaskType.CODE_REVIEW)
        print(f"   ✓ Found {len(code_review_records)} code_review records")

        # Test 4: Calculate stats
        print("\n4. Calculating performance stats...")
        stats = logger.get_performance_stats()
        for cli, metrics in stats.items():
            print(f"   {cli}:")
            print(f"     - Total executions: {metrics['total_executions']}")
            print(f"     - Success rate: {metrics['success_rate']:.1%}")
            print(f"     - Avg duration: {metrics['avg_duration']:.1f}s")
            print(f"     - Avg output length: {metrics['avg_output_length']:.0f} chars")

        # Test 5: Verify JSONL format
        print("\n5. Verifying JSONL format...")
        with open(test_log) as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                try:
                    data = json.loads(line)
                    assert "timestamp" in data
                    assert "cli_name" in data
                    assert "task_type" in data
                except (json.JSONDecodeError, AssertionError) as e:
                    print(f"   ✗ Line {i} failed: {e}")
                    return
        print(f"   ✓ All {len(records)} lines are valid JSON")

        print("\n" + "=" * 80)
        print("All tests passed!")


if __name__ == "__main__":
    _test_performance_logger()
