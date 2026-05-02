"""Tests for Stop_git_diff_reground.py v2 — self-edit exclusion, dedup, time-bound checks."""

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent


def _make_data(
    session_id: str = "test-session-001",
    events: list[dict] | None = None,
) -> dict:
    """Build hook input data with tool_events (realistic Stop hook stdin schema)."""
    return {
        "session_id": session_id,
        "sessionId": session_id,
        "tool_events": events or [],
    }


def _make_events(*paths_timestamps: tuple[str, str, float]) -> list[dict]:
    """Build tool_events: (tool_name, path, timestamp).

    Matches the real Stop hook stdin schema where events have:
    {name, input: {file_path}, timestamp}
    """
    return [
        {"name": tname, "input": {"file_path": path}, "timestamp": ts}
        for tname, path, ts in paths_timestamps
    ]


# --- Self-edit exclusion ---

class TestSelfEditExclusion:
    """Files the session itself edited should not trigger regrounding."""

    def test_edited_file_excluded_from_warning(self, tmp_path, monkeypatch):
        from Stop_git_diff_reground import check_git_diff_reground

        monkeypatch.setattr("Stop_git_diff_reground.STATE_DIR", tmp_path)

        events = _make_events(
            ("Read", "packages/foo/CLAUDE.md", 1000.0),
            ("Read", "packages/bar/CLAUDE.md", 1001.0),
            ("Read", "packages/baz/CLAUDE.md", 1002.0),
            ("Edit", "packages/foo/CLAUDE.md", 1003.0),
        )

        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value={"packages/foo/CLAUDE.md", "packages/bar/CLAUDE.md"},
            ),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            result = check_git_diff_reground(_make_data(events=events))

        # packages/foo was self-edited -> excluded
        # packages/bar was read-only and changed -> should warn
        assert result is not None
        assert "packages/bar/CLAUDE.md" in result["systemMessage"]
        assert "packages/foo/CLAUDE.md" not in result["systemMessage"]

    def test_all_files_self_edited_no_warning(self, tmp_path, monkeypatch):
        from Stop_git_diff_reground import check_git_diff_reground

        monkeypatch.setattr("Stop_git_diff_reground.STATE_DIR", tmp_path)

        events = _make_events(
            ("Read", "a.py", 1000.0),
            ("Read", "b.py", 1001.0),
            ("Read", "c.py", 1002.0),
            ("Edit", "a.py", 1003.0),
            ("Write", "b.py", 1004.0),
            ("Edit", "c.py", 1005.0),
        )

        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value={"a.py", "b.py", "c.py"},
            ),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            result = check_git_diff_reground(_make_data(events=events))

        assert result is None


# --- Dedup (warn once per file per session) ---

class TestDedup:
    """Each file should only produce one warning per session."""

    def test_second_call_no_duplicate_warning(self, tmp_path, monkeypatch):
        from Stop_git_diff_reground import check_git_diff_reground

        monkeypatch.setattr("Stop_git_diff_reground.STATE_DIR", tmp_path)

        events = _make_events(
            ("Read", "x.py", 1000.0),
            ("Read", "y.py", 1001.0),
            ("Read", "z.py", 1002.0),
        )
        diff_files = {"x.py", "y.py", "z.py"}

        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value=diff_files,
            ),
            patch("Stop_git_diff_reground._file_changed_after", return_value=True),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            result1 = check_git_diff_reground(_make_data(session_id="dedup-test", events=events))

        assert result1 is not None
        assert "x.py" in result1["systemMessage"]

        # Second call with same files -> should be suppressed
        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value=diff_files,
            ),
            patch("Stop_git_diff_reground._file_changed_after", return_value=True),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            result2 = check_git_diff_reground(_make_data(session_id="dedup-test", events=events))

        assert result2 is None

    def test_new_file_triggers_warning(self, tmp_path, monkeypatch):
        from Stop_git_diff_reground import check_git_diff_reground

        monkeypatch.setattr("Stop_git_diff_reground.STATE_DIR", tmp_path)

        events1 = _make_events(
            ("Read", "a.py", 1000.0),
            ("Read", "b.py", 1001.0),
            ("Read", "c.py", 1002.0),
        )
        events2 = _make_events(
            ("Read", "a.py", 1000.0),
            ("Read", "b.py", 1001.0),
            ("Read", "c.py", 1002.0),
            ("Read", "d.py", 1003.0),
        )

        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value={"a.py", "b.py", "c.py"},
            ),
            patch("Stop_git_diff_reground._file_changed_after", return_value=True),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            check_git_diff_reground(_make_data(session_id="dedup-new", events=events1))

        # Now d.py appears in diff
        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value={"a.py", "b.py", "c.py", "d.py"},
            ),
            patch("Stop_git_diff_reground._file_changed_after", return_value=True),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            result = check_git_diff_reground(_make_data(session_id="dedup-new", events=events2))

        assert result is not None
        # Only d.py should appear (a/b/c already warned)
        assert "d.py" in result["systemMessage"]
        assert "a.py" not in result["systemMessage"]

    def test_different_sessions_independent(self, tmp_path, monkeypatch):
        from Stop_git_diff_reground import check_git_diff_reground

        monkeypatch.setattr("Stop_git_diff_reground.STATE_DIR", tmp_path)

        events = _make_events(
            ("Read", "x.py", 1000.0),
            ("Read", "y.py", 1001.0),
            ("Read", "z.py", 1002.0),
        )

        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value={"x.py", "y.py", "z.py"},
            ),
            patch("Stop_git_diff_reground._file_changed_after", return_value=True),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            r1 = check_git_diff_reground(_make_data(session_id="sess-A", events=events))

        assert r1 is not None

        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value={"x.py", "y.py", "z.py"},
            ),
            patch("Stop_git_diff_reground._file_changed_after", return_value=True),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            r2 = check_git_diff_reground(_make_data(session_id="sess-B", events=events))

        assert r2 is not None  # Different session -> no dedup


# --- Time-bound checks ---

class TestTimeBound:
    """Only warn if file changed after the last Read."""

    def test_file_unchanged_since_read_no_warning(self, tmp_path, monkeypatch):
        from Stop_git_diff_reground import check_git_diff_reground

        monkeypatch.setattr("Stop_git_diff_reground.STATE_DIR", tmp_path)

        events = _make_events(
            ("Read", "stable.py", time.time() - 10),
            ("Read", "b.py", time.time() - 10),
            ("Read", "c.py", time.time() - 10),
        )

        # File mtime is OLDER than read -> file hasn't changed since read
        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value={"stable.py", "b.py", "c.py"},
            ),
            patch("Stop_git_diff_reground._file_changed_after", return_value=False),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            result = check_git_diff_reground(_make_data(events=events))

        assert result is None

    def test_file_changed_after_read_warns(self, tmp_path, monkeypatch):
        from Stop_git_diff_reground import check_git_diff_reground

        monkeypatch.setattr("Stop_git_diff_reground.STATE_DIR", tmp_path)

        events = _make_events(
            ("Read", "changed.py", 1000.0),
            ("Read", "b.py", 1001.0),
            ("Read", "c.py", 1002.0),
        )

        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value={"changed.py", "b.py", "c.py"},
            ),
            patch("Stop_git_diff_reground._file_changed_after", return_value=True),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            result = check_git_diff_reground(_make_data(events=events))

        assert result is not None
        assert "changed.py" in result["systemMessage"]

    def test_mixed_changed_and_unchanged_only_warns_changed(self, tmp_path, monkeypatch):
        from Stop_git_diff_reground import check_git_diff_reground

        monkeypatch.setattr("Stop_git_diff_reground.STATE_DIR", tmp_path)

        events = _make_events(
            ("Read", "old.py", 1000.0),
            ("Read", "fresh.py", 1001.0),
            ("Read", "c.py", 1002.0),
        )

        def selective_changed(file_path: str, after_ts: float) -> bool:
            return "fresh" in file_path

        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value={"old.py", "fresh.py", "c.py"},
            ),
            patch("Stop_git_diff_reground._file_changed_after", side_effect=selective_changed),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            result = check_git_diff_reground(_make_data(events=events))

        assert result is not None
        assert "fresh.py" in result["systemMessage"]
        assert "old.py" not in result["systemMessage"]


# --- Edge cases ---

class TestEdgeCases:
    def test_disabled_returns_none(self):
        from Stop_git_diff_reground import check_git_diff_reground

        with patch("Stop_git_diff_reground.GIT_DIFF_REGROUND_ENABLED", False):
            result = check_git_diff_reground(_make_data())
        assert result is None

    def test_no_session_id_returns_none(self):
        from Stop_git_diff_reground import check_git_diff_reground

        result = check_git_diff_reground({})
        assert result is None

    def test_fewer_than_min_files_returns_none(self, tmp_path, monkeypatch):
        from Stop_git_diff_reground import check_git_diff_reground

        monkeypatch.setattr("Stop_git_diff_reground.STATE_DIR", tmp_path)

        events = _make_events(
            ("Read", "a.py", 1000.0),
            ("Read", "b.py", 1001.0),
        )

        with patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError):
            result = check_git_diff_reground(_make_data(events=events))

        assert result is None

    def test_no_changed_files_returns_none(self, tmp_path, monkeypatch):
        from Stop_git_diff_reground import check_git_diff_reground

        monkeypatch.setattr("Stop_git_diff_reground.STATE_DIR", tmp_path)

        events = _make_events(
            ("Read", "a.py", 1000.0),
            ("Read", "b.py", 1001.0),
            ("Read", "c.py", 1002.0),
        )

        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value=set(),
            ),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            result = check_git_diff_reground(_make_data(events=events))

        assert result is None


# --- Path normalization ---

class TestPathNormalization:
    """Absolute paths from Read events must match relative paths from git diff."""

    def test_absolute_path_normalized(self, tmp_path, monkeypatch):
        from Stop_git_diff_reground import _make_relative

        # Paths should be stripped to repo-root-relative
        result = _make_relative("P:/packages/foo/CLAUDE.md")
        assert result == "packages/foo/CLAUDE.md"

    def test_already_relative_unchanged(self):
        from Stop_git_diff_reground import _make_relative

        result = _make_relative("packages/foo/CLAUDE.md")
        assert result == "packages/foo/CLAUDE.md"

    def test_absolute_read_matches_relative_diff(self, tmp_path, monkeypatch):
        from Stop_git_diff_reground import check_git_diff_reground

        monkeypatch.setattr("Stop_git_diff_reground.STATE_DIR", tmp_path)

        # Read events use absolute paths (as they come from Stop hook stdin)
        events = _make_events(
            ("Read", "P:/packages/foo/CLAUDE.md", 1000.0),
            ("Read", "P:/packages/bar/CLAUDE.md", 1001.0),
            ("Read", "P:/packages/baz/CLAUDE.md", 1002.0),
        )

        # git diff returns repo-root-relative paths
        with (
            patch(
                "Stop_git_diff_reground._get_git_diff_names",
                return_value={"packages/foo/CLAUDE.md", "packages/bar/CLAUDE.md"},
            ),
            patch("Stop_git_diff_reground._file_changed_after", return_value=True),
            patch("Stop_git_diff_reground.load_tool_events", side_effect=ImportError),
        ):
            result = check_git_diff_reground(_make_data(events=events))

        assert result is not None
        assert "packages/foo/CLAUDE.md" in result["systemMessage"]


# --- _parse_ts helper ---

class TestParseTs:
    def test_float_passthrough(self):
        from Stop_git_diff_reground import _parse_ts

        assert _parse_ts(1000.5) == 1000.5

    def test_int_to_float(self):
        from Stop_git_diff_reground import _parse_ts

        assert _parse_ts(1000) == 1000.0

    def test_string_parsed(self):
        from Stop_git_diff_reground import _parse_ts

        assert _parse_ts("1000.5") == 1000.5

    def test_none_returns_zero(self):
        from Stop_git_diff_reground import _parse_ts

        assert _parse_ts(None) == 0.0

    def test_invalid_string_returns_zero(self):
        from Stop_git_diff_reground import _parse_ts

        assert _parse_ts("not-a-number") == 0.0


# --- main() entry point ---

class TestMain:
    def test_empty_input_returns_empty_json(self):
        from Stop_git_diff_reground import main

        with patch("sys.stdin") as mock_stdin:
            mock_stdin.read.return_value = ""
            result = main()
        assert result == 0

    def test_invalid_json_returns_empty_json(self):
        from Stop_git_diff_reground import main

        with patch("sys.stdin") as mock_stdin:
            mock_stdin.read.return_value = "not json"
            result = main()
        assert result == 0
