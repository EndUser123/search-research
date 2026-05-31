#!/usr/bin/env python3
"""
PreToolUse Hook: Windows Path Gate

Blocks Write/Edit operations that use backslash paths on Windows.
Backslash paths cause silent write failures where the tool reports success
but the file is not written or written to the wrong location.

Root Cause: Claude Code on Windows MINGW/Git Bash normalises paths differently
from the tool's internal resolver. Backslash paths produce silent failures
(GitHub #12805, #40227).

Fix: Use forward-slash paths with drive letter prefix.
  Wrong:  P:\\.claude\\skills\\specify\\SKILL.md
  Right:  P:/.claude/skills/specify/SKILL.md

Configuration:
    WIN32_PATH_GATE_ENABLED: "true" (default) or "false" to disable
"""

from __future__ import annotations

# --- plugin bootstrap ---
import sys
from pathlib import Path
_l = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in sys.path: sys.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import os

env_var = "WIN32_PATH_GATE_ENABLED"
default_enabled = True
tool_matcher = {"Write", "Edit", "MultiEdit"}


def run(data: dict) -> dict | None:
    """Block Write/Edit calls that use backslash paths.

    Args:
        data: Tool invocation data with tool_name and tool_input.

    Returns:
        None to allow, dict with continue=False to block.
    """
    enabled = os.environ.get(env_var, "true").lower() not in ("false", "0", "no")
    if not enabled:
        return None

    tool_name = data.get("tool_name", "")
    if tool_name not in tool_matcher:
        return None

    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path", "")
    if not file_path or not isinstance(file_path, str):
        return None

    if "\\" not in file_path:
        return None

    corrected = file_path.replace("\\", "/")
    return {
        "continue": False,
        "reason": (
            f"WIN32_PATH_GATE: Backslash path will cause a silent write failure.\n"
            f"  Received: {file_path!r}\n"
            f"  Use:      {corrected!r}\n\n"
            "Windows/MINGW Write and Edit tools silently fail when paths contain "
            "backslashes (GitHub issues #12805, #40227). Replace all backslashes "
            "with forward slashes and retry."
        ),
    }


if __name__ == "__main__":
    def check(desc: str, data: dict, expect_block: bool) -> None:
        result = run(data)
        blocked = result is not None and result.get("continue") is False
        status = "PASS" if blocked == expect_block else "FAIL"
        print(f"{status}: {desc}")
        if blocked != expect_block:
            print(f"  Expected block={expect_block}, got {result}")

    print("Testing PreToolUse_win32_path_gate.py\n")
    check("backslash Write blocked",
          {"tool_name": "Write", "tool_input": {"file_path": r"P:\.claude\skills\foo\SKILL.md"}},
          True)
    check("forward-slash Write allowed",
          {"tool_name": "Write", "tool_input": {"file_path": "P:/.claude/skills/foo/SKILL.md"}},
          False)
    check("backslash Edit blocked",
          {"tool_name": "Edit", "tool_input": {"file_path": r"P:\.claude\hooks\foo.py"}},
          True)
    check("Read tool ignored",
          {"tool_name": "Read", "tool_input": {"file_path": r"P:\.claude\foo.py"}},
          False)
    check("backslash MultiEdit blocked",
          {"tool_name": "MultiEdit", "tool_input": {"file_path": r"P:\.test\foo.md"}},
          True)
    check("empty path allowed",
          {"tool_name": "Write", "tool_input": {"file_path": ""}},
          False)
    print("\nAll tests completed")
