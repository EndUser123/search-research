#!/usr/bin/env python3
"""Persistent regression tests for python_syntax_checker PostToolUse hook."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from posttooluse.python_syntax_checker import PythonSyntaxChecker


@pytest.fixture
def checker() -> PythonSyntaxChecker:
    return PythonSyntaxChecker()


@pytest.fixture
def valid_py_file(tmp_path: Path) -> Path:
    f = tmp_path / "valid.py"
    f.write_text("x = 1\nprint(x)\n", encoding="utf-8")
    return f


@pytest.fixture
def syntax_error_py_file(tmp_path: Path) -> Path:
    f = tmp_path / "broken.py"
    f.write_text("def foo(\n", encoding="utf-8")
    return f


class TestPythonSyntaxChecker:
    """Regression tests for python_syntax_checker hook."""

    def test_skip_non_python_file(self, checker: PythonSyntaxChecker) -> None:
        result = checker.process(
            "Edit",
            {"file_path": "readme.md"},
            {},
        )
        assert result["passed"] is True
        assert result.get("skipped") is True

    def test_skip_no_file_path(self, checker: PythonSyntaxChecker) -> None:
        result = checker.process("Edit", {}, {})
        assert result["passed"] is True
        assert result.get("skipped") is True

    def test_valid_python_passes(
        self, checker: PythonSyntaxChecker, valid_py_file: Path
    ) -> None:
        result = checker.process(
            "Edit",
            {"file_path": str(valid_py_file)},
            {},
        )
        assert result["passed"] is True
        assert "injection" not in result

    def test_syntax_error_detected(
        self, checker: PythonSyntaxChecker, syntax_error_py_file: Path
    ) -> None:
        result = checker.process(
            "Write",
            {"file_path": str(syntax_error_py_file)},
            {},
        )
        assert result["passed"] is True  # PostToolUse is advisory
        assert "SYNTAX WARNING" in result.get("injection", "")
        assert "broken.py" in result["injection"]

    def test_tool_matcher_includes_edit(self) -> None:
        assert "Edit" in PythonSyntaxChecker.tool_matcher

    def test_tool_matcher_includes_write(self) -> None:
        assert "Write" in PythonSyntaxChecker.tool_matcher

    def test_tool_matcher_includes_multiedit(self) -> None:
        assert "MultiEdit" in PythonSyntaxChecker.tool_matcher

    def test_missing_file_skipped(self, checker: PythonSyntaxChecker) -> None:
        result = checker.process(
            "Edit",
            {"file_path": "/nonexistent/path/file.py"},
            {},
        )
        assert result["passed"] is True
        assert result.get("skipped") is True

    def test_relative_path_resolved(
        self, checker: PythonSyntaxChecker, valid_py_file: Path, monkeypatch
    ) -> None:
        monkeypatch.chdir(valid_py_file.parent)
        result = checker.process(
            "MultiEdit",
            {"file_path": "valid.py"},
            {},
        )
        assert result["passed"] is True
        assert "injection" not in result

    def test_read_error_skipped(self, checker: PythonSyntaxChecker) -> None:
        """Windows doesn't enforce 0o000 so we test the OSError path indirectly."""
        import unittest.mock

        with unittest.mock.patch("pathlib.Path.read_text", side_effect=OSError("denied")):
            result = checker.process(
                "Edit",
                {"file_path": "some.py"},
                {},
            )
        assert result["passed"] is True
        assert result.get("skipped") is True

    def test_syntax_error_includes_line_number(
        self, checker: PythonSyntaxChecker, tmp_path: Path
    ) -> None:
        f = tmp_path / "multiline.py"
        f.write_text("x = 1\ny = 2\ndef foo(\n", encoding="utf-8")
        result = checker.process(
            "Edit",
            {"file_path": str(f)},
            {},
        )
        assert "SYNTAX WARNING" in result.get("injection", "")
        assert ":3" in result["injection"]

    def test_default_enabled(self) -> None:
        assert PythonSyntaxChecker.default_enabled is True

    def test_env_var_name(self) -> None:
        assert PythonSyntaxChecker.env_var == "PYTHON_SYNTAX_CHECKER_ENABLED"
