#!/usr/bin/env python3
from __future__ import annotations

"""
File Activity Tracker - In-process adapter.

Tracks file operations (Read/Edit/Write/Bash/Grep/Glob) for session-based scoping.
Absorbed from PostToolUse_file_activity_tracker.py.

Original matcher: ^(Read|Edit|Write|Grep|Glob|Bash)$
"""

import os
import re
import sys
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

# Add project src to path
_project_src = Path(__file__).resolve().parent.parent.parent.parent / "__csf" / "src"
if str(_project_src) not in sys.path:
    sys.path.insert(0, str(_project_src))


class FileActivityTrackerHook(PostToolUseHook):
    """Tracks file operations for session-based scoping."""

    tool_matcher = {"Read", "Edit", "Write", "Grep", "Glob", "Bash"}

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        wt_session = os.environ.get("WT_SESSION")
        if wt_session:
            session_id = f"wt_{wt_session[:8]}"
        else:
            try:
                session_id = f"pid_{os.getppid()}"
            except Exception:
                return {"passed": True}

        if not isinstance(tool_input, dict):
            return {"passed": True}

        operation = None
        file_path = None
        metadata = {"tool_name": tool_name}

        if tool_name == "Read":
            operation = "read"
            file_path = tool_input.get("file_path")
        elif tool_name == "Edit":
            operation = "edit"
            file_path = tool_input.get("file_path")
        elif tool_name == "Write":
            operation = "write"
            file_path = tool_input.get("file_path")
        elif tool_name == "Bash":
            operation = "bash"
            command = tool_input.get("command", "")
            metadata["command"] = command[:200]
            file_path = self._extract_file_path(command)
        elif tool_name == "Grep":
            operation = "grep"
            file_path = tool_input.get("path")
        elif tool_name == "Glob":
            operation = "glob"
            file_path = tool_input.get("path")

        if operation and file_path:
            try:
                from src.modules.session_management.session_activity_tracker import (
                    track_file_access,
                )
                track_file_access(operation, file_path, session_id, metadata)
            except Exception:
                pass

        return {"passed": True}

    @staticmethod
    def _extract_file_path(command: str) -> str | None:
        """Extract file path from common bash commands."""
        quoted = re.search(r'["\']([^"\']+\.[^"\']+)["\']', command)
        if quoted:
            potential = quoted.group(1)
            if "/" in potential or "\\" in potential:
                return potential
        for prefix in ["cat ", "less ", "head ", "tail ", "python ", "node "]:
            if command.startswith(prefix):
                rest = command[len(prefix):].strip()
                first_arg = rest.split()[0] if rest else None
                if first_arg and ("/" in first_arg or "\\" in first_arg):
                    return first_arg
        return None
