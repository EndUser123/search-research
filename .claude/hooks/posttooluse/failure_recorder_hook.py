#!/usr/bin/env python3
from __future__ import annotations

"""
Failure Recorder - In-process adapter.

Records tool failures for Catch-22 detection via recursive_failure_detector.
Absorbed from standalone failure_recorder.py.

Original matcher: .* (all tools)
"""

import json
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

_hooks_dir = Path(__file__).resolve().parent.parent


def is_tool_failure(tool_response: dict[str, Any]) -> bool:
    """Classify a tool_response as a failure worth recording for loop detection.

    Claude Code signals failure via exit_code (Bash/python), is_error, error, or
    output containing a traceback/error line. The previous check only scanned the
    first 100 chars of output, which misses Python tracebacks — the actual error
    type appears well after the 'Traceback (most recent call last):' header.
    That left the Catch-22 detector with no data for repeated failed commands.
    """
    if not tool_response:
        return False
    if tool_response.get("is_error"):
        return True
    if tool_response.get("error"):
        return True
    exit_code = tool_response.get("exit_code")
    if isinstance(exit_code, int) and exit_code != 0:
        return True
    output = str(tool_response.get("output", "")).lower()
    # Scan full output: tracebacks surface the error type past 100 chars.
    return any(sig in output for sig in ("traceback", "error:", "exception"))


class FailureRecorderHook(PostToolUseHook):
    """Records tool failures for Catch-22 detection."""

    tool_matcher = None  # All tools

    def _import_detector_functions(self):
        """Lazily import from recursive_failure_detector."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "recursive_failure_detector",
            _hooks_dir / "recursive_failure_detector.py"
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            # Ensure the hook's module uses the same SESSION_DIR as the main module
            import recursive_failure_detector as rfd
            module.SESSION_DIR = rfd.SESSION_DIR
            return module.compute_command_hash, module.save_failure
        return None, None

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        """
        Record tool usage for Catch-22 and investigation loop detection.

        Strategy:
        - Read-only tools (Read, Grep, Glob): Always record (for investigation loop detection)
        - Other tools: Only record failures (for Catch-22 detection)
        """
        compute_hash, save_failure = self._import_detector_functions()
        if not compute_hash or not save_failure:
            return {"passed": True}

        # Check if this is a read-only tool (for investigation loop detection)
        read_only_tools = ("Read", "Grep", "Glob")
        is_read_only_tool = tool_name in read_only_tools

        # Check if this is an error (for Catch-22 detection)
        is_error = is_tool_failure(tool_response)

        # Record if: (1) read-only tool, OR (2) error occurred
        if not (is_read_only_tool or is_error):
            return {"passed": True}

        command = (tool_input.get("command") or
                   tool_input.get("content") or
                   tool_input.get("path") or
                   json.dumps(tool_input)[:500])

        # Use appropriate status message
        if is_read_only_tool and not is_error:
            status_msg = "Success (investigation loop tracking)"
        else:
            status_msg = str(
                tool_response.get("error") or
                tool_response.get("output", "")
            )[:200]

        cmd_hash = compute_hash(command)
        save_failure(tool_name, cmd_hash, status_msg)

        return {"passed": True}
