#!/usr/bin/env python3
"""Tests for unified log rotation system."""

from __future__ import annotations

import json

# Add hooks to path
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR / "__lib"))

from log_rotation import (
    _count_jsonl_entries,
    _truncate_jsonl,
    rotate_diagnostic_logs,
    rotate_log_file,
)


@pytest.fixture
def temp_log_file(tmp_path: Path) -> Path:
    """Create a temporary log file for testing."""
    return tmp_path / "test_log.jsonl"


@pytest.fixture
def sample_log_entries() -> list[dict]:
    """Sample log entries for testing."""
    return [
        {"ts": "2026-03-08T12:00:00", "session_id": "test-1", "event": "hook_start"},
        {"ts": "2026-03-08T12:00:01", "session_id": "test-1", "event": "hook_end"},
        {"ts": "2026-03-08T12:00:02", "session_id": "test-2", "event": "hook_start"},
    ]


class TestLogRotationIntegration:
    """Test that UPS execution trace log is included in rotation."""

    def test_rotate_diagnostic_logs_includes_ups_execution_trace(
        self, tmp_path: Path, sample_log_entries: list[dict], monkeypatch
    ) -> None:
        """Verify that ups_execution_trace.jsonl is rotated by the unified system."""
        # Mock get_hooks_dir to return tmp_path
        import log_rotation

        def mock_get_hooks_dir():
            return tmp_path

        monkeypatch.setattr(log_rotation, "get_hooks_dir", mock_get_hooks_dir)

        # Create a temporary diagnostics directory
        diag_dir = tmp_path / "logs" / "diagnostics"
        diag_dir.mkdir(parents=True)

        # Create ups_execution_trace.jsonl with sample entries
        log_file = diag_dir / "ups_execution_trace.jsonl"
        with open(log_file, "w", encoding="utf-8") as f:
            for entry in sample_log_entries:
                f.write(json.dumps(entry) + "\n")

        # Rotate with low max_entries to test truncation
        stats = rotate_diagnostic_logs(
            retention_days=30,
            compress_after_days=7,
            max_size_mb=10,
            max_entries=2,  # Truncate to 2 entries
        )

        # Verify the log was processed
        assert stats["total_logs_rotated"] >= 1
        assert stats["truncated"] >= 1

        # Verify file was truncated
        remaining_entries = _count_jsonl_entries(log_file)
        assert remaining_entries == 2

    def test_rotate_log_file_function_works_with_ups_trace(
        self, tmp_path: Path, sample_log_entries: list[dict]
    ) -> None:
        """Test that rotate_log_file() works with UPS execution trace."""
        # Create a log file
        log_file = tmp_path / "ups_execution_trace.jsonl"
        with open(log_file, "w", encoding="utf-8") as f:
            for entry in sample_log_entries:
                f.write(json.dumps(entry) + "\n")

        # Rotate the file
        stats = rotate_log_file(
            log_file,
            retention_days=30,
            compress_after_days=7,
            max_size_mb=10,
            max_entries=2,
        )

        # Verify rotation stats
        assert stats["truncated"] == 1
        assert _count_jsonl_entries(log_file) == 2

    def test_rotate_diagnostic_logs_includes_plain_text_logs(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Verify that diagnostic .log files are rotated too."""
        import log_rotation

        monkeypatch.setattr(log_rotation, "get_hooks_dir", lambda: tmp_path)

        diag_dir = tmp_path / "logs" / "diagnostics"
        diag_dir.mkdir(parents=True)
        log_file = diag_dir / "startup_probe.log"
        log_file.write_text(("probe line\n" * 2000), encoding="utf-8")

        stats = rotate_diagnostic_logs(
            retention_days=30,
            compress_after_days=7,
            max_size_mb=100,
            max_entries=10,
        )

        assert stats["total_logs_rotated"] >= 1
        assert log_file.exists()


class TestJSONLTruncation:
    """Test JSONL file truncation functionality."""

    def test_truncate_jsonl_keeps_last_n_entries(self, temp_log_file: Path) -> None:
        """Test that _truncate_jsonl keeps the last N entries."""
        # Create log file with 5 entries
        entries = [
            {"ts": f"2026-03-08T12:00:0{i}", "entry": i} for i in range(5)
        ]
        with open(temp_log_file, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        # Truncate to 3 entries
        _truncate_jsonl(temp_log_file, max_entries=3)

        # Verify only last 3 entries remain
        with open(temp_log_file, encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 3

        # Verify they are the last 3 entries
        for i, line in enumerate(lines):
            entry = json.loads(line)
            assert entry["entry"] == i + 2  # Entries 2, 3, 4

    def test_truncate_jsonl_handles_empty_file(self, temp_log_file: Path) -> None:
        """Test that _truncate_jsonl handles empty files gracefully."""
        # Create empty file
        temp_log_file.touch()

        # Should not raise exception
        _truncate_jsonl(temp_log_file, max_entries=10)

        # File should still be empty
        assert temp_log_file.stat().st_size == 0

    def test_count_jsonl_entries(self, temp_log_file: Path) -> None:
        """Test _count_jsonl_entries returns accurate count."""
        # Create file with 4 entries (one empty line)
        with open(temp_log_file, "w", encoding="utf-8") as f:
            f.write('{"entry": 1}\n')
            f.write("\n")  # Empty line
            f.write('{"entry": 2}\n')
            f.write('{"entry": 3}\n')
            f.write('{"entry": 4}\n')

        count = _count_jsonl_entries(temp_log_file)
        # Should count only non-empty lines
        assert count == 4


class TestLogRotationSettings:
    """Verify that UPS execution trace uses correct rotation settings."""

    def test_ups_trace_respects_max_entries_setting(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Verify that ups_execution_trace.jsonl respects 1000 entry limit."""
        from log_rotation import _LOG_MAX_ENTRIES

        assert _LOG_MAX_ENTRIES == 1000

        # Mock get_hooks_dir to return tmp_path
        import log_rotation

        def mock_get_hooks_dir():
            return tmp_path

        monkeypatch.setattr(log_rotation, "get_hooks_dir", mock_get_hooks_dir)

        # Create log with 1005 entries
        diag_dir = tmp_path / "logs" / "diagnostics"
        diag_dir.mkdir(parents=True)
        log_file = diag_dir / "ups_execution_trace.jsonl"

        with open(log_file, "w", encoding="utf-8") as f:
            for i in range(1005):
                f.write(json.dumps({"entry": i}) + "\n")

        # Rotate with default settings
        rotate_diagnostic_logs()

        # Should truncate to 1000 entries
        assert _count_jsonl_entries(log_file) == 1000

    def test_ups_trace_respects_max_size_setting(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Verify that ups_execution_trace.jsonl respects 10MB size limit."""
        from log_rotation import _LOG_MAX_SIZE_MB

        assert _LOG_MAX_SIZE_MB == 10

        # Mock get_hooks_dir to return tmp_path
        import log_rotation

        def mock_get_hooks_dir():
            return tmp_path

        monkeypatch.setattr(log_rotation, "get_hooks_dir", mock_get_hooks_dir)

        # Create log larger than 10MB
        diag_dir = tmp_path / "logs" / "diagnostics"
        diag_dir.mkdir(parents=True)
        log_file = diag_dir / "ups_execution_trace.jsonl"

        # Create 11MB of data
        large_entry = {"data": "x" * (1024 * 1024)}  # 1MB per entry
        with open(log_file, "w", encoding="utf-8") as f:
            for _ in range(11):
                f.write(json.dumps(large_entry) + "\n")

        # Rotate with default settings
        stats = rotate_diagnostic_logs()

        # Should compress the file
        assert stats["compressed"] >= 1
        assert not log_file.exists()  # Original should be gone
        assert (log_file.with_suffix(log_file.suffix + ".gz")).exists()


class TestLogRotationErrorHandling:
    """Test error handling in log rotation."""

    def test_rotate_diagnostic_logs_fails_silently_on_invalid_json(
        self, tmp_path: Path, caplog, monkeypatch
    ) -> None:
        """Test that invalid JSON in log files doesn't crash rotation."""
        # Mock get_hooks_dir to return tmp_path
        import log_rotation

        def mock_get_hooks_dir():
            return tmp_path

        monkeypatch.setattr(log_rotation, "get_hooks_dir", mock_get_hooks_dir)

        # Create diagnostics directory with invalid JSON
        diag_dir = tmp_path / "logs" / "diagnostics"
        diag_dir.mkdir(parents=True)
        log_file = diag_dir / "test_log.jsonl"

        with open(log_file, "w", encoding="utf-8") as f:
            f.write('{"valid": "entry"}\n')
            f.write('{"invalid": entry}\n')  # Invalid JSON
            f.write('{"another": "valid"}\n')

        # Should not raise exception
        stats = rotate_diagnostic_logs()

        # Should process the file despite invalid JSON
        assert stats["total_logs_rotated"] >= 1

    def test_rotate_diagnostic_logs_handles_nonexistent_directory(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Test that missing diagnostics directory is handled gracefully."""
        # Mock get_hooks_dir to return tmp_path
        import log_rotation

        def mock_get_hooks_dir():
            return tmp_path

        monkeypatch.setattr(log_rotation, "get_hooks_dir", mock_get_hooks_dir)

        # Don't create any logs directory
        stats = rotate_diagnostic_logs()

        # Should return early without errors
        assert stats["total_logs_rotated"] == 0
