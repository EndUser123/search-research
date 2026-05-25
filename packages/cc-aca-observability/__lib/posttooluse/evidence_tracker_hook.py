#!/usr/bin/env python3
from __future__ import annotations

"""
Evidence Tracker - In-process adapter.

Tracks tool execution evidence in SQLite via audit_lib.
Absorbed from standalone evidence_tracker.py to reduce process spawning.

Original matcher: .* (all tools)
"""

import sys
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

# Ensure hooks dir is on path for audit_lib import
_hooks_dir = Path(__file__).resolve().parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))


class EvidenceTrackerHook(PostToolUseHook):
    """Tracks tool execution evidence in audit database."""

    tool_matcher = None  # All tools

    def run(self, data: dict[str, Any]) -> dict[str, Any]:
        """Override run() to capture session_id from the raw hook data."""
        self._session_id = data.get("session_id", "unknown")
        return super().run(data)

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        try:
            from audit_lib import classify_tool, insert_evidence, load_audit_config
        except Exception:
            return {"passed": True}

        config = load_audit_config()
        if not config.get("enabled", True):
            return {"passed": True}

        command = None
        if tool_name == "Bash":
            command = tool_input.get("command", "")
        elif tool_name in ("Read", "Write", "Edit"):
            command = tool_input.get("file_path", "")

        category = classify_tool(tool_name, command)

        evidence = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_response": tool_response,
            "command": command,
            "category": category,
            "timestamp": None,
        }

        try:
            insert_evidence(getattr(self, "_session_id", "unknown"), evidence)
        except Exception:
            # Never block or fail PostToolUse on evidence DB write problems.
            return {"passed": True}

        return {"passed": True}
