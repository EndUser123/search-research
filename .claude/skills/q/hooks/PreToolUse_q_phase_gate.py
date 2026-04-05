#!/usr/bin/env python3
"""
PreToolUse hook for /q skill - phase gate enforcement.

Blocks Bash/Task tool use when attempting to skip /q phases (q1..q6).
"""

import json
import os
import re
import sys
from pathlib import Path

STATE_DIR = Path(os.environ.get("CLAUDE_STATE_DIR", ".claude/state"))


def get_terminal_id() -> str:
    if "CLAUDE_TERMINAL_ID" in os.environ:
        return os.environ["CLAUDE_TERMINAL_ID"]

    import hashlib

    unique_str = f"{Path.cwd()}_{os.getpid()}"
    return hashlib.md5(unique_str.encode()).hexdigest()[:8]


def get_state_file() -> Path:
    return STATE_DIR / f"q-pipeline-{get_terminal_id()}.json"


def load_state() -> dict:
    state_file = get_state_file()
    if not state_file.exists():
        return {"max_passed_phase": 0, "last_result": None, "last_action": None}
    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, OSError):
        return {"max_passed_phase": 0, "last_result": None, "last_action": None}


def extract_phase(command_text: str) -> int:
    # Match both /q1..q6 and /q --phase=N patterns
    old_pattern = re.search(r"/q([1-6])\b", command_text, re.IGNORECASE)
    if old_pattern:
        return int(old_pattern.group(1))

    new_pattern = re.search(r"/q\s+--phase=(\d+)", command_text, re.IGNORECASE)
    if new_pattern:
        return int(new_pattern.group(1))

    return 0


def main() -> None:
    input_data = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not input_data.strip():
        sys.exit(0)

    try:
        hook_input = json.loads(input_data)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input") or hook_input.get("toolInput", {})

    if tool_name not in ["Bash", "Task"]:
        sys.exit(0)

    command = ""
    if tool_name == "Bash":
        command = str(tool_input.get("command", ""))
    else:
        command = str(tool_input.get("prompt", ""))

    phase = extract_phase(command)
    if phase == 0:
        sys.exit(0)

    if "--phase=" in command or "--force" in command:
        sys.exit(0)

    state = load_state()
    max_passed = int(state.get("max_passed_phase", 0))
    last_result = str(state.get("last_result", "") or "")

    if phase > max_passed + 1:
        print(
            f"[BLOCK] Q phase gate violation: requested /q{phase} "
            f"but max completed is /q{max_passed}. "
            f"Run /q{max_passed + 1} first (or use --phase={phase} to force)."
        )
        sys.exit(1)

    if last_result == "fail" and phase != max_passed + 1:
        print(
            f"[BLOCK] Previous /q phase failed. Resume at /q{max_passed + 1} "
            f"before running /q{phase}."
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()

