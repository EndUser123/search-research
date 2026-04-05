"""
Tests for SessionEnd_tldr.py — Session summary generation hook.

Tests cover:
- Atomic write durability (os.replace instead of shutil.move)
- Duration calculation from ISO timestamps
- Terminal-scoped path isolation
- Graceful degradation on missing files
- JSON output format for hook system

Run with: pytest P:/.claude/hooks/tests/test_session_end_tldr.py -v
"""

from __future__ import annotations

import io
import json
import sys
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the module under test
from SessionEnd_tldr import (
    _atomic_write,
    _calculate_duration,
    _get_session_start_path,
    _get_state_path,
    _safe_id,
)
from SessionEnd_tldr import (
    main as session_end_main,
)


class TestCalculateDuration:
    """Tests for _calculate_duration function."""

    def test_valid_iso_timestamp_same_minute(self):
        """Duration is ~0m when start and end are within same minute."""
        now = datetime.now(UTC)
        start = (now - timedelta(minutes=5)).isoformat()
        result = _calculate_duration(start)
        assert result is not None
        assert "~" in result
        assert "m" in result

    def test_valid_iso_timestamp_hours_minutes(self):
        """Duration shows hours and minutes for longer sessions."""
        now = datetime.now(UTC)
        start = (now - timedelta(hours=2, minutes=30)).isoformat()
        result = _calculate_duration(start)
        assert result is not None
        assert "~2h" in result
        assert "30m" in result

    def test_invalid_timestamp_returns_none(self):
        """Invalid ISO format returns None gracefully."""
        assert _calculate_duration("not-a-timestamp") is None
        assert _calculate_duration("") is None
        assert _calculate_duration(None) is None

    def test_timestamp_with_z_suffix(self):
        """Timestamp with Z suffix parses correctly."""
        now = datetime.now(UTC)
        start = (now - timedelta(minutes=10)).isoformat().replace("+00:00", "Z")
        result = _calculate_duration(start)
        assert result is not None

    def test_clock_skew_negative_duration(self):
        """Negative duration (end before start) returns 'unknown (clock skew)'."""
        future = datetime.now(UTC) + timedelta(hours=1)
        start = future.isoformat()
        result = _calculate_duration(start)
        assert "clock skew" in result


class TestSafeId:
    """Tests for _safe_id function."""

    def test_normal_id_unchanged(self):
        """Normal terminal IDs pass through unchanged."""
        assert _safe_id("console_abc123") == "console_abc123"
        assert _safe_id("env_xyz") == "env_xyz"

    def test_special_chars_replaced(self):
        """Special characters are replaced with underscores."""
        assert _safe_id("console:abc") == "console_abc"
        assert _safe_id("env/xyz") == "env_xyz"
        assert _safe_id("term@home!") == "term_home_"

    def test_spaces_replaced(self):
        """Spaces are replaced with underscores."""
        assert _safe_id("console abc") == "console_abc"


class TestAtomicWrite:
    """Tests for _atomic_write function — verifies os.replace atomicity."""

    def test_write_creates_file(self, tmp_path):
        """Atomic write creates the target file."""
        target = tmp_path / "summary.md"
        _atomic_write(target, "## Session Summary\nContent here")
        assert target.exists()
        assert target.read_text(encoding="utf-8") == "## Session Summary\nContent here"

    def test_write_overwrites_existing(self, tmp_path):
        """Atomic write overwrites existing file."""
        target = tmp_path / "summary.md"
        target.write_text("old content")
        _atomic_write(target, "new content")
        assert target.read_text(encoding="utf-8") == "new content"

    def test_write_creates_parent_dirs(self, tmp_path):
        """Atomic write creates parent directories if missing."""
        target = tmp_path / "deep" / "nested" / "dir" / "summary.md"
        _atomic_write(target, "content")
        assert target.exists()
        assert target.read_text(encoding="utf-8") == "content"

    def test_atomic_write_no_temp_leak_on_success(self, tmp_path):
        """No .tmp files remain after successful write."""
        target = tmp_path / "summary.md"
        _atomic_write(target, "content")

        # Check no .tldr_ temp files remain
        temp_files = list(tmp_path.glob(".tldr_*"))
        assert len(temp_files) == 0, f"Temp files leaked: {temp_files}"

    def test_atomic_write_no_temp_leak_on_failure(self, tmp_path):
        """No temp files remain after a failed rename operation.

        We simulate a failure by pointing to a path that cannot be written to
        as a regular file. On Windows, trying to rename a temp file to a
        path that is an existing directory raises OSError.
        """
        target = tmp_path / "summary.md"
        target.mkdir()  # It's a directory — os.replace will fail
        with pytest.raises(Exception):
            _atomic_write(target, "content")

        # Verify no leaked temp files
        temp_files = list(tmp_path.glob(".tldr_*"))
        assert len(temp_files) == 0, f"Temp files leaked: {temp_files}"


class TestStatePath:
    """Tests for terminal-scoped state paths."""

    def test_get_state_path_format(self):
        """State path includes terminal_id and has correct suffix."""
        path = _get_state_path("console_abc123")
        assert "_last_session.md" in path.name
        assert "console_abc123" in path.name

    def test_get_session_start_path_format(self):
        """Session start path includes terminal_id and has correct suffix."""
        path = _get_session_start_path("env_xyz")
        assert "_session_start.txt" in path.name
        assert "env_xyz" in path.name

    def test_state_path_is_terminal_scoped(self):
        """Different terminal IDs produce different paths."""
        path_a = _get_state_path("terminal_A")
        path_b = _get_state_path("terminal_B")
        assert path_a != path_b


class TestMainJsonOutput:
    """Tests for main() hook JSON output format."""

    def test_main_outputs_json_to_stdout(self, capsys):
        """Hook must output JSON to stdout, not stderr."""
        # Provide minimal input
        with patch.object(sys, "stdin", io.StringIO("{}")):
            session_end_main()

        captured = capsys.readouterr()
        # stdout should be valid JSON (the "{}" print)
        result = json.loads(captured.out.strip())
        assert isinstance(result, dict)

    def test_main_returns_zero_exit_code(self):
        """Hook must exit 0 to indicate success."""
        with patch.object(sys, "stdin", io.StringIO("{}")):
            exit_code = session_end_main()
        assert exit_code == 0


# Import for StringIO mock


class TestConcurrentWrite:
    """Tests for concurrent write safety with FileLock."""

    def test_concurrent_writes_all_succeed(self, tmp_path):
        """Multiple threads writing to same path — all writes eventually visible."""
        target = tmp_path / "concurrent.md"
        lock_path = tmp_path / "concurrent.md.lock"

        errors = []

        def write_content(n: int):
            try:
                from __lib.file_lock import FileLock

                content = f"content from thread {n}\n"
                with FileLock(lock_path, timeout=10.0):
                    # Read existing content
                    existing = target.read_text(encoding="utf-8") if target.exists() else ""
                    # Write combined
                    target.write_text(existing + content, encoding="utf-8")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=write_content, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors during concurrent writes: {errors}"
        # All 5 threads wrote their content
        content = target.read_text(encoding="utf-8")
        for i in range(5):
            assert f"thread {i}" in content


class TestJsonOutputFormat:
    """Tests that verify the hook output format matches hook system requirements."""

    def test_output_is_valid_json(self, capsys):
        """Hook output must be parseable as JSON."""
        with patch.object(sys, "stdin", io.StringIO("{}")):
            session_end_main()

        captured = capsys.readouterr()
        # Must not raise — if it does, test fails
        parsed = json.loads(captured.out.strip())
        assert isinstance(parsed, dict)
