#!/usr/bin/env python3
"""Write a task-type routing hint for ccr-custom-router.js.

Called by the cc-model-router classify hook (or any hook that can determine
the task type). The hint is consumed by ccr-custom-router.js on the next
CCR request and expires after 60s.

Usage:
    python write_routing_hint.py <task_type> [pin_model]

task_type: coding | reasoning | background | trivial-coding
pin_model: optional CC model label to pin (e.g. claude-opus-4-8)
"""
import json
import os
import sys
from datetime import datetime, timezone

STATE_DIR = "P:/.claude/state"
HINT_FILE = os.path.join(STATE_DIR, "ccr-routing-hint.json")
PIN_FILE = os.path.join(STATE_DIR, "ccr-pin-state.json")

VALID_TASK_TYPES = {"coding", "reasoning", "background", "trivial-coding", "local-coding"}


def write_hint(task_type: str, session_id: str = "", **extra) -> None:
    if task_type not in VALID_TASK_TYPES:
        print(f"warning: unknown task_type '{task_type}', accepting anyway", file=sys.stderr)
    os.makedirs(STATE_DIR, exist_ok=True)
    hint = {
        "taskType": task_type,
        "sessionId": session_id,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    hint.update(extra)
    with open(HINT_FILE, "w", encoding="utf-8") as f:
        json.dump(hint, f, indent=2)
    print(f"[routing-hint] taskType={task_type} confidence={extra.get('confidence', 'n/a')}")


def write_pin(model: str, session_id: str = "") -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    pin = {
        "model": model,
        "sessionId": session_id,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    with open(PIN_FILE, "w", encoding="utf-8") as f:
        json.dump(pin, f, indent=2)
    print(f"[routing-hint] pin={model}")


def clear_pin() -> None:
    """Clear pin state (called on session restart or explicit re-pin)."""
    try:
        os.remove(PIN_FILE)
        print("[routing-hint] pin cleared")
    except FileNotFoundError:
        pass


def main():
    if len(sys.argv) < 2:
        print("usage: write_routing_hint.py <task_type> [pin_model]", file=sys.stderr)
        sys.exit(1)

    task_type = sys.argv[1]
    session_id = sys.argv[2] if len(sys.argv) > 2 else ""

    if task_type == "__clear_pin__":
        clear_pin()
    elif task_type == "__pin__":
        pin_model = sys.argv[3] if len(sys.argv) > 3 else ""
        if not pin_model:
            print("usage: write_routing_hint.py __pin__ <session_id> <model>", file=sys.stderr)
            sys.exit(1)
        write_pin(pin_model, session_id)
    else:
        write_hint(task_type, session_id)


if __name__ == "__main__":
    main()
