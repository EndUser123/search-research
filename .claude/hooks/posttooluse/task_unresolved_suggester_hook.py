#!/usr/bin/env python3
from __future__ import annotations

"""
PostToolUse Hook - Task Unresolved Suggester

Adds non-blocking unresolved-item suggestions after TaskList operations.
Uses .claude/skills/task/unresolved_items_detector.py as the detection engine.
"""

import importlib.util
import os
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook


def _detect_terminal_id() -> str:
    """Best-effort terminal id detection with safe fallback."""
    try:
        from __lib.terminal_detection import detect_terminal_id

        return detect_terminal_id()
    except Exception:
        return ""  # No PID fallback


def _load_detector_func():
    """Dynamically load detect_unresolved_items from the task skill module."""
    claude_home = Path(os.environ.get("CLAUDE_HOME", "P:/.claude"))
    detector_path = claude_home / "skills" / "task" / "unresolved_items_detector.py"
    if not detector_path.exists():
        return None

    spec = importlib.util.spec_from_file_location("task_unresolved_detector", detector_path)
    if not spec or not spec.loader:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "detect_unresolved_items", None)


def _extract_tasks(tool_response: Any) -> list[dict[str, Any]]:
    """Extract task-like dicts from common TaskList response shapes."""
    if isinstance(tool_response, list):
        return [t for t in tool_response if isinstance(t, dict)]
    if not isinstance(tool_response, dict):
        return []

    for key in ("tasks", "items", "results", "data"):
        value = tool_response.get(key)
        if isinstance(value, list):
            return [t for t in value if isinstance(t, dict)]

    return []


class TaskUnresolvedSuggesterHook(PostToolUseHook):
    """
    In-process PostToolUse hook for unresolved task suggestions.

    Non-blocking by design; only injects context for TaskList calls.
    """

    env_var = "TASK_UNRESOLVED_SUGGEST_ENABLED"
    default_enabled = True
    tool_matcher = {"TaskList"}

    def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]:
        detect_unresolved_items = _load_detector_func()
        if not detect_unresolved_items:
            return {}

        terminal_id = _detect_terminal_id()
        tasks = _extract_tasks(tool_response)
        completed = [t for t in tasks if str(t.get("status", "")).lower() == "completed"]

        try:
            unresolved = detect_unresolved_items(
                terminal_id=terminal_id,
                limit=5,
                max_age_days=14,
                completed_tasks=completed,
            )
        except Exception:
            return {}

        if not unresolved:
            return {}

        lines = [f"⚠️ Unresolved from Chat History ({len(unresolved)}):"]
        for item in unresolved:
            date = item.get("date", "Unknown")
            content = str(item.get("content", "")).strip()
            suggested = str(item.get("suggested_task", "")).strip()
            if not content:
                continue
            lines.append(f'  [CHS {date}] "{content}"')
            if suggested:
                lines.append(f'    -> /task add "{suggested}"')

        if len(lines) <= 1:
            return {}

        lines.append("Run /task-unresolved for a focused unresolved scan.")
        return {"injection": "\n".join(lines)}
