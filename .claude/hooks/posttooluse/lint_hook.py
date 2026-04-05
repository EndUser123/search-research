#!/usr/bin/env python3
from __future__ import annotations

"""
Auto-Lint Hook
==============

Auto-formats files after Edit/Write operations with language-specific linters.
- Python: ruff format
- JS/TS/JSON/MD/YAML: prettier

Re-entrancy guard: Prevents infinite loops via marker file.
Graceful degrade: Skips silently if linter is not installed.
"""

import subprocess
import sys
from pathlib import Path

from posttooluse.base import PostToolUseHook


class LintHook(PostToolUseHook):
    """Auto-format files after Edit/Write operations."""

    env_var = "LINT_ROUTER_ENABLED"
    default_enabled = False  # DISABLED: runs ruff --fix on Edit/Write, risk of stripping code between sequential edits

    # Language-specific linters with capability detection
    LINTERS = {
        ".py": {
            "command": ["ruff", "check", "--fix", "--"],
            "check_cmd": ["ruff", "--version"],
            "name": "ruff",
        },
        ".ts": {
            "command": ["prettier", "--write", "--"],
            "check_cmd": ["prettier", "--version"],
            "name": "prettier",
        },
        ".tsx": {
            "command": ["prettier", "--write", "--"],
            "check_cmd": ["prettier", "--version"],
            "name": "prettier",
        },
        ".js": {
            "command": ["prettier", "--write", "--"],
            "check_cmd": ["prettier", "--version"],
            "name": "prettier",
        },
        ".jsx": {
            "command": ["prettier", "--write", "--"],
            "check_cmd": ["prettier", "--version"],
            "name": "prettier",
        },
        ".json": {
            "command": ["prettier", "--write", "--"],
            "check_cmd": ["prettier", "--version"],
            "name": "prettier",
        },
        ".md": {
            "command": ["prettier", "--write", "--"],
            "check_cmd": ["prettier", "--version"],
            "name": "prettier",
        },
        ".yaml": {
            "command": ["prettier", "--write", "--"],
            "check_cmd": ["prettier", "--version"],
            "name": "prettier",
        },
        ".yml": {
            "command": ["prettier", "--write", "--"],
            "check_cmd": ["prettier", "--version"],
            "name": "prettier",
        },
    }

    # Re-entrancy guard: track linted files per session
    _linted_files: set[tuple[str, float]] = set()

    def __init__(self):
        super().__init__()
        self.hooks_dir = Path(__file__).resolve().parent.parent

    def process(self, tool_name: str, tool_input: dict, tool_response: dict) -> dict:
        """Auto-format file after Edit/Write."""
        # Only lint Edit and Write operations
        if tool_name not in ("Edit", "Write"):
            return {}

        file_path = tool_input.get("file_path", "")
        if not file_path:
            return {}

        # Check if we should lint this file
        ext = self._get_extension(file_path)
        if ext not in self.LINTERS:
            return {}

        # Re-entrancy guard: check if we already linted this file
        try:
            mtime = Path(file_path).stat().st_mtime
            key = (file_path, mtime)
            if key in self._linted_files:
                return {}  # Already linted
            self._linted_files.add(key)
        except Exception:
            pass  # Skip re-entrancy check if stat fails

        # Run linter
        linter = self.LINTERS[ext]
        if not self._is_linter_available(linter["check_cmd"]):
            return {}  # Linter not installed, skip silently

        success, message = self._run_linter(file_path, linter["command"])

        result = {}
        if success:
            result["injection"] = f"\n✨ Auto-formatted with {linter['name']}"
        else:
            # Only show error if it's not "not found"
            if "not found" not in message.lower():
                result["injection"] = f"\n⚠️ Auto-format failed: {message[:100]}"

        return result

    def _get_extension(self, file_path: str) -> str:
        """Get file extension."""
        return Path(file_path).suffix.lower()

    def _is_linter_available(self, check_cmd: list[str]) -> bool:
        """Check if linter is installed."""
        try:
            result = subprocess.run(
                check_cmd,
                capture_output=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_linter(self, file_path: str, command: list[str]) -> tuple[bool, str]:
        """Run linter on file."""
        full_cmd = command + [file_path]
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode == 0:
                return True, f"Formatted with {' '.join(command)}"
            else:
                stderr = result.stderr.decode() or result.stdout.decode()
                return False, f"Linter failed: {stderr[:200]}"
        except subprocess.TimeoutExpired:
            return False, "Linter timeout after 10s"
        except FileNotFoundError:
            return False, "Linter not found"
        except Exception as e:
            return False, f"Linter error: {str(e)[:100]}"
