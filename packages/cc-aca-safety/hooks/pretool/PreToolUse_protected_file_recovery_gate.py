"""
Protected File Recovery Lockout Gate
===================================

PreToolUse gate that blocks Edit/Write operations on protected files
that are currently syntactically invalid, unless the operation is a git restore
(from git HEAD, which is the correct recovery path).
Exit codes:
  0 = Allow operation
  2 = Block operation (file is broken and not a recovery operation)
"""

from __future__ import annotations

# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import os
import sys


def _resolve_hooks_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _is_recovery_for_file(stdin_data: dict, file_path: str) -> bool:
    """Return True if stdin_data indicates git restore targeting file_path."""
    tool_name = stdin_data.get("tool_name", "")
    if tool_name != "Bash":
        return False
    command = stdin_data.get("tool_input", {}).get("command", "")
    if not command:
        return False
    norm = os.path.normpath(os.path.expanduser(file_path)).replace("\\", "/").lower()
    cmd_lower = command.lower()
    if "git restore" in cmd_lower and norm in cmd_lower:
        return True
    if "git checkout" in cmd_lower and norm in cmd_lower:
        return True
    return False


def run(data: dict) -> dict:
    """Block Edit/Write on broken protected files unless git restore is the recovery."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if tool_name not in ("Edit", "Write"):
        return {"decision": "allow"}
    if not file_path:
        return {"decision": "allow"}

    # Lazy import to avoid startup cost on non-protected files
    hooks_dir = _resolve_hooks_dir()
    if hooks_dir not in sys.path:
        sys.path.insert(0, hooks_dir)
    try:
        from __lib.protected_paths import is_protected_path, is_file_broken
    except ImportError:
        return {"decision": "allow"}  # Fail open

    if not is_protected_path(file_path):
        return {"decision": "allow"}
    if not is_file_broken(file_path):
        return {"decision": "allow"}
    if _is_recovery_for_file(data, file_path):
        return {"decision": "allow"}

    basename = os.path.basename(file_path)
    return {
        "decision": "block",
        "reason": (
            f"SYNTAX RECOVERY LOCKOUT: {basename} is syntactically invalid.\n"
            f"Continued edits are blocked until the file is restored.\n"
            f"Recovery: git restore {basename}\n"
            f"Do NOT patch a broken protected file — restore from HEAD first."
        ),
    }


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw else {}
    except Exception:
        sys.exit(0)
    result = run(data)
    if result.get("decision") == "block":
        print(result.get("reason", "BLOCKED"), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
