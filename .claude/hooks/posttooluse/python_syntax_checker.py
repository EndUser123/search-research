#!/usr/bin/env python3
"""Post-Edit Python syntax verification.

Runs ast.parse() on .py files after Edit/Write/MultiEdit to catch SyntaxErrors
immediately. The PreToolUse_syntax_gate already covers Write before execution;
this hook catches errors introduced by Edit (partial content replacement) and
provides a safety net for any edge cases the PreToolUse gate misses.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook


class PythonSyntaxChecker(PostToolUseHook):
    """Verify Python files have valid syntax after Edit/Write/MultiEdit."""

    tool_matcher = {"Edit", "Write", "MultiEdit"}
    env_var = "PYTHON_SYNTAX_CHECKER_ENABLED"
    default_enabled = True

    def process(
        self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]
    ) -> dict[str, Any]:
        file_path = tool_input.get("file_path", "")
        if not file_path or not file_path.endswith(".py"):
            return {"passed": True, "skipped": True, "reason": "not_python"}

        path = Path(file_path)

        # For MultiEdit, file_path might be relative or have forward slashes
        if not path.exists():
            # Try resolving relative to CWD
            cwd = os.getcwd()
            resolved = Path(cwd) / file_path
            if resolved.exists():
                path = resolved
            else:
                return {"passed": True, "skipped": True, "reason": "file_not_found"}

        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            return {"passed": True, "skipped": True, "reason": "read_error"}

        try:
            ast.parse(content, filename=str(path))
        except SyntaxError as e:
            filename = path.name
            line_info = f":{e.lineno}" if e.lineno else ""
            msg = f"Python syntax error: {filename}{line_info} - {e.msg}"
            if e.text:
                msg += f"\n  -> {e.text.strip()}"

            return {
                "passed": True,  # PostToolUse is advisory — edit already happened
                "injection": f"**SYNTAX WARNING**: {msg}\nFix the syntax error before continuing.",
            }

        return {"passed": True}
