"""Tool-use artifact access tracker for PostToolUse phase.

Tracks which files/artifacts were accessed during a tool call.
This enables Stop enforcement to verify that mechanism claims
are backed by actual tool use against the relevant artifact.

Canonical source: cc-aca-observability plugin __lib/posttooluse/
Previously at: P:/.claude/hooks/PostToolUse_artifact_access_tracker.py

Output: tool_use_log_{terminal}.jsonl in hooks/.state/
(original path preserved for consumer compatibility)
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from hooks_resolver import get_hooks_dir

STATE_DIR = get_hooks_dir() / ".state"
STATE_DIR.mkdir(parents=True, exist_ok=True)


def _get_log_path(terminal_id: str) -> Path:
    """Return path to tool-use log file."""
    safe_id = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id or "unknown")
    return STATE_DIR / f"tool_use_log_{safe_id}.jsonl"


def _extract_file_paths(tool_name: str, tool_input: dict) -> list[str]:
    """Extract file paths from tool input.

    Handles: Read, Grep, Glob, Bash (git grep, jq, cat).
    """
    paths = []

    if tool_name in ("Read", "read_file", "ReadFile"):
        fp = tool_input.get("file_path") or tool_input.get("path")
        if fp:
            paths.append(fp)

    elif tool_name in ("Grep", "search_files", "SearchFiles"):
        path = tool_input.get("path") or tool_input.get("SearchPath")
        if path:
            paths.append(path)
        glob_pat = tool_input.get("glob") or tool_input.get("pattern")
        if glob_pat:
            paths.append(f"glob:{glob_pat}")

    elif tool_name in ("Glob", "list_files", "ListFiles"):
        path = tool_input.get("path") or tool_input.get("DirectoryPath")
        if path:
            paths.append(path)
        pattern = tool_input.get("pattern")
        if pattern:
            paths.append(f"pattern:{pattern}")

    elif tool_name in ("Bash", "execute_code"):
        command = tool_input.get("command", "")
        if not command:
            return paths
        if any(x in command for x in ["grep", "jq", "cat", "wc", "head", "tail"]):
            parts = command.split()
            for part in parts[1:]:
                if part.startswith("-") or part.startswith("|") or part.startswith(">"):
                    continue
                if "/" in part or "\\" in part or part.endswith(".jsonl") or part.endswith(".py"):
                    paths.append(part)
                quoted = re.findall(r'"([^"]+)"', command)
                for q in quoted:
                    if "/" in q or "\\" in q or ".jsonl" in q or ".py" in q:
                        paths.append(q)

    return paths


def track_tool_use(session_id: str, terminal_id: str, tool_name: str, tool_input: dict) -> None:
    """Write tool use entry to the log file.

    Called from PostToolUse router after each tool execution.
    """
    accessed = _extract_file_paths(tool_name, tool_input)
    if not accessed:
        return

    log_path = _get_log_path(terminal_id)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "terminal_id": terminal_id,
        "tool": tool_name,
        "accessed": accessed,
    }

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"[artifact_tracker] Failed to write log: {e}", file=__import__("sys").stderr)


# Standalone entry point for subprocess invocation
if __name__ == "__main__":
    import sys as _sys

    data = json.loads(_sys.stdin.read())

    session_id = data.get("session_id", "")
    terminal_id = data.get("terminal_id", "") or os.environ.get("CLAUDE_TERMINAL_ID", "")
    tool_name = data.get("name", "") or data.get("tool_name", "")
    tool_input = data.get("input", {}) or data.get("tool_input", {})

    if tool_name:
        track_tool_use(session_id, terminal_id, tool_name, tool_input)

    print("{}")
    _sys.exit(0)


__all__ = [
    "track_tool_use",
    "_extract_file_paths",
]
