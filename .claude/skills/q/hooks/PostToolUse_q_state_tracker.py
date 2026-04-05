#!/usr/bin/env python3
"""
PostToolUse hook for /q skill - phase/state tracking.

Tracks /q phase progression (q1..q6) in terminal-isolated state.
"""

import datetime
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


def default_state() -> dict:
    return {
        "schema_version": 1,
        "max_passed_phase": 0,
        "current_phase": 0,
        "last_action": None,
        "last_result": None,
        "terminal_id": get_terminal_id(),
        "history": [],
    }


def load_state() -> dict:
    state_file = get_state_file()
    if not state_file.exists():
        return default_state()
    try:
        state = json.loads(state_file.read_text())
        if "history" not in state:
            state["history"] = []
        return state
    except (json.JSONDecodeError, OSError):
        return default_state()


def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state["terminal_id"] = get_terminal_id()
    state["last_activity"] = _now_iso()
    state_file = get_state_file()
    tmp_file = state_file.with_suffix(".tmp")
    tmp_file.write_text(json.dumps(state, indent=2))
    tmp_file.replace(state_file)


def extract_phase(command_text: str) -> int:
    # Match both /q1..q6 and /q --phase=N patterns
    old_pattern = re.search(r"/q([1-6])\b", command_text, re.IGNORECASE)
    if old_pattern:
        return int(old_pattern.group(1))

    new_pattern = re.search(r"/q\s+--phase=(\d+)", command_text, re.IGNORECASE)
    if new_pattern:
        return int(new_pattern.group(1))

    return 0


def is_success(hook_input: dict) -> bool:
    tool_result = hook_input.get("tool_result") or {}
    exit_code = tool_result.get("exit_code")
    if exit_code is not None:
        return exit_code == 0

    output = str(tool_result.get("output", "") or "")
    failure_indicators = ["FAILED", "ERROR", "Traceback", "exit code 1", "[BLOCK]"]
    return not any(ind in output for ind in failure_indicators)


def main() -> None:
    input_data = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not input_data.strip():
        print("{}")
        sys.exit(0)

    try:
        hook_input = json.loads(input_data)
    except json.JSONDecodeError:
        print("{}")
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input") or hook_input.get("toolInput", {})

    if tool_name not in ["Bash", "Task"]:
        print("{}")
        sys.exit(0)

    command = ""
    if tool_name == "Bash":
        command = str(tool_input.get("command", ""))
    else:
        command = str(tool_input.get("prompt", ""))

    if "/q" not in command.lower():
        print("{}")
        sys.exit(0)

    phase = extract_phase(command)
    state = load_state()
    success = is_success(hook_input)
    now = _now_iso()

    if phase > 0:
        state["current_phase"] = phase
        state["last_action"] = f"q{phase}"
        if success:
            state["max_passed_phase"] = max(int(state.get("max_passed_phase", 0)), phase)
            state["last_result"] = "pass"
        else:
            state["last_result"] = "fail"
    else:
        state["last_action"] = "q"
        state["last_result"] = "pass" if success else "fail"

    state["history"].append(
        {
            "timestamp": now,
            "action": state["last_action"],
            "result": state["last_result"],
            "phase": phase,
        }
    )
    state["last_action_timestamp"] = now
    save_state(state)

    print("{}")
    sys.exit(0)


if __name__ == "__main__":
    main()
