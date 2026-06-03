#!/usr/bin/env python3
"""PostToolUse advisory: catch dispatcher import breakage at edit time.

Fires after an Edit/Write/MultiEdit to a `.claude/hooks/**/*.py` file and
re-imports the top-level dispatchers. If a dispatcher (or the file just
edited) no longer imports, it warns in-session — immediately, at the point
the breakage is introduced — instead of letting a non-blocking traceback
spam every subsequent tool call until a human notices.

This is the enforcement half of the import-health check; the pytest-level
half lives in tests/test_hook_import_health.py. Both source the dispatcher
list and loader from __lib/hook_import_health.py so they cannot drift.

Design constraints:
  - Advisory only. PostToolUse must never block; this always exits 0.
  - Fail open. Any internal error => stay silent (an over-eager guard that
    breaks editing is worse than the spam it prevents).
  - Scoped. Only runs the (heavier) import pass when a hook source file was
    edited, so normal edits pay nothing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# __lib is a sibling of this file's directory's hooks root; this file lives
# directly in P:/.claude/hooks/, so __lib is HOOKS_DIR/__lib.
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR / "__lib"))


def _edited_hook_file(data: dict) -> str | None:
    """Return the edited file path if it is a .py file under .claude/hooks/."""
    tool = data.get("tool_name", "") or data.get("name", "")
    if tool not in ("Edit", "Write", "MultiEdit"):
        return None
    tool_input = data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path:
        return None
    normalized = str(file_path).replace("\\", "/")
    if not normalized.endswith(".py"):
        return None
    if "/.claude/hooks/" not in normalized:
        return None
    return normalized


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return  # malformed input -> stay silent

    edited = _edited_hook_file(data)
    if not edited:
        return

    try:
        from hook_import_health import DISPATCHER_HOOKS, check_dispatchers, try_load
    except ImportError:
        return  # shared module unavailable -> fail open

    failures = check_dispatchers()

    # Also surface breakage in the specific file just edited, in case it is a
    # standalone hook not transitively loaded by any dispatcher. Skip if it is
    # itself a dispatcher (already covered) or a test file (import side effects
    # from collection are noise, not signal).
    edited_name = Path(edited).name
    if edited_name not in DISPATCHER_HOOKS and "/tests/" not in edited:
        ok, err = try_load(edited)
        if not ok and all(name != edited_name for name, _ in failures):
            failures.append((edited_name, err))

    if not failures:
        return

    lines = [
        "⚠️ HOOK IMPORT HEALTH: a hook you just edited no longer imports.",
        "Until fixed, this fires a non-blocking error on every affected event:",
    ]
    lines += [f"  • {name}: {err}" for name, err in failures]
    lines.append("Fix the import before continuing (or this will spam the session).")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
