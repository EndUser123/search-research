#!/usr/bin/env python3
"""cc-aca-authority router - dispatches to plugin hooks based on event type.

Registered in settings.json alongside the main router. Runs after local hooks
and after the epistemic/investigation routers.

Usage:
    python router.py <EventName>

Where EventName is PreToolUse, Stop, or UserPromptSubmit.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = PLUGIN_ROOT / "hooks"

PHASE_DIR = {
    "PreToolUse": "pretool",
    "Stop": "stop",
    "UserPromptSubmit": "userpromptsubmit",
}

# Hooks per event — each hook self-filters by tool_name internally.
PRETOOLUSE_HOOKS = [
    "PreToolUse_destructive_git_guard.py",
    "PreToolUse_authorization_gate.py",
    "PreToolUse_risk_tier_gate.py",
    "PreToolUse_ask_first_tool_gate.py",
    "PreToolUse_git_safety.py",
    "PreToolUse_delegation_gate.py",
    "PreToolUse_user_delegation_gate.py",
]

STOP_HOOKS = [
    "Stop_safety_gate.py",
    "Stop_approval_gate.py",
    "Stop_behavior_gates.py",
    "Stop_commit_gate.py",
    "Stop_lazy_workaround_gate.py",
    "stop_permission_stall.py",
]

UPS_HOOKS = [
    "UserPromptSubmit_approval.py",
    "delegation_prospector.py",
]

DISPATCH = {
    "PreToolUse": PRETOOLUSE_HOOKS,
    "Stop": STOP_HOOKS,
    "UserPromptSubmit": UPS_HOOKS,
}


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(0)

    event = sys.argv[1]
    hooks = DISPATCH.get(event)
    if not hooks:
        sys.exit(0)

    phase = PHASE_DIR.get(event, "")
    input_data = sys.stdin.buffer.read()

    for hook_name in hooks:
        hook_path = HOOKS_DIR / phase / hook_name
        if not hook_path.exists():
            continue

        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = subprocess.run(
                [sys.executable, str(hook_path)],
                input=input_data,
                capture_output=True,
                timeout=10,
                creationflags=flags,
            )

            # PreToolUse: exit code 2 = block
            if result.returncode == 2:
                out = result.stdout.decode(errors="replace").strip()
                if out:
                    print(out)
                else:
                    stderr_msg = result.stderr.decode(errors="replace").strip()
                    reason = stderr_msg if stderr_msg else f"Blocked by {hook_name}"
                    print(json.dumps({"decision": "block", "reason": reason}))
                sys.exit(2)

            # Check for block in JSON output
            out = result.stdout.decode(errors="replace").strip()
            if out:
                try:
                    parsed = json.loads(out)
                    if isinstance(parsed, dict) and parsed.get("decision") == "block":
                        print(out)
                        sys.exit(2)
                except json.JSONDecodeError:
                    pass
        except subprocess.TimeoutExpired:
            pass  # Fail open
        except Exception:
            pass  # Fail open

    # All hooks passed
    print(json.dumps({"decision": "approve"}))


if __name__ == "__main__":
    main()
