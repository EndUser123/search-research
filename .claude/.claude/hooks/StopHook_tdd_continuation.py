#!/usr/bin/env python3
"""
StopHook for /tdd - Advisory reminder for incomplete TDD workflow.

Exit codes:
- 0: Always allow stop (user sovereignty)
- Advisory message only (never blocks)
"""

import json
import sys
from pathlib import Path

# Add hooks directory to path for terminal detection
hooks_dir = Path("P:/.claude/hooks")
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

from terminal_detection import detect_terminal_id


def _get_state_file() -> Path:
    """Get terminal-isolated state file path."""
    terminal_id = detect_terminal_id()
    state_dir = Path.home() / ".claude" / ".state" / "tdd" / terminal_id
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "tdd_workflow.json"


def read_state() -> dict | None:
    state_file = _get_state_file()
    if not state_file.exists():
        return None
    try:
        return json.loads(state_file.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def main():
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        payload = {}

    state = read_state()

    # No workflow active - silent pass
    if state is None:
        sys.exit(0)

    # Workflow explicitly halted - silent pass
    if state.get("halted", False):
        sys.exit(0)

    # Workflow complete - silent pass
    if state.get("complete", False):
        sys.exit(0)

    current = state.get("current_stage", 0)
    max_stage = state.get("max_stage", 6)
    stages = {
        1: "DISCOVER",
        2: "RED",
        3: "GREEN",
        4: "VERIFY",
        5: "REGRESSION",
        6: "REFACTOR",
    }

    # Workflow incomplete - ADVISORY only (never blocks)
    # User sovereignty: allow stop anytime, state persists for resume
    if current < max_stage:
        next_stage = current + 1
        next_name = stages.get(next_stage, f"Stage {next_stage}")

        msg = "💡 TDD workflow incomplete (advisory).\n"
        msg += f"Current: Stage {current} ({stages.get(current, 'Unknown')})\n"
        msg += f"Next: Stage {next_stage} ({next_name})\n"
        msg += "State persists. Resume TDD cycle with /tdd when ready."

        print(msg, file=sys.stderr)

    # ALWAYS allow stop - user sovereignty over workflow completion
    sys.exit(0)


if __name__ == "__main__":
    main()
