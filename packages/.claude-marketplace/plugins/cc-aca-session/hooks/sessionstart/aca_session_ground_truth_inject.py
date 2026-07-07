#!/usr/bin/env python3
"""SessionStart injector — render runtime ground truth and emit additionalContext.

Reads `P:/.claude/hooks/analysis/runtime-ground-truth.md`, renders it through
`runtime_ground_truth.load_and_render()` (which self-caps at
BUDGET_PROTECTED_CHARS=800 and marks stale rows with their reverify command),
and emits the SessionStart additionalContext envelope. The cc-aca-session
router forwards this to the harness.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "__lib"))

import runtime_ground_truth as rgt  # noqa: E402


def main() -> None:
    try:
        rendered = rgt.load_and_render()
    except Exception:
        sys.exit(0)

    if not rendered:
        sys.exit(0)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": rendered,
        }
    }))


if __name__ == "__main__":
    main()
