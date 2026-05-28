#!/usr/bin/env python3
"""Investigation Boundary Gate (v1.0)

Injects a one-time reflection prompt when transitioning from investigation
(read/grep/glob) to implementation (edit/write) tools. Fires once per session
when the first implementation tool is called after sufficient investigation.

No LLM calls, no persistence, fully stateless (uses tool_use_history).
"""

from __future__ import annotations

# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

import json
import sys

INVESTIGATION_TOOLS = frozenset({"Read", "Grep", "Glob", "LS", "LSP"})
IMPLEMENTATION_TOOLS = frozenset({"Edit", "Write", "MultiEdit"})
MIN_INVESTIGATION_COUNT = 2


def detect_investigation_to_impl_transition(
    tool_name: str, tool_use_history: list | None
) -> bool:
    """Return True when calling an implementation tool after investigation but
    before any prior implementation in this session."""
    if not tool_use_history:
        return False

    if tool_name not in IMPLEMENTATION_TOOLS:
        return False

    investigation_count = 0
    for entry in tool_use_history:
        hist_tool = entry.get("tool_name", "")
        if hist_tool in INVESTIGATION_TOOLS:
            investigation_count += 1
        if hist_tool in IMPLEMENTATION_TOOLS:
            return False

    return investigation_count >= MIN_INVESTIGATION_COUNT


def main() -> int:
    input_data = sys.stdin.read()
    if not input_data:
        print("{}")
        return 0

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError:
        print("{}")
        return 0

    tool_name = data.get("tool_name", "")
    tool_use_history = data.get("tool_use_history", [])

    if detect_investigation_to_impl_transition(tool_name, tool_use_history):
        output = {
            "decision": "approve",
            "systemMessage": (
                "[Investigation->Implementation] "
                "You are about to make your first edit after investigating. "
                "What assumption are you acting on? "
                "What evidence would falsify it?"
            ),
        }
        print(json.dumps(output))
    else:
        print("{}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"[Investigation boundary gate error: {e}]\n")
        print("{}")
        sys.exit(0)
