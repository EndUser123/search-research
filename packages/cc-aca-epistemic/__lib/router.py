#!/usr/bin/env python3
"""cc-aca-epistemic router - dispatches to plugin hooks based on event type.

Registered in settings.json alongside the main router. Runs after local hooks.
Dispatches to all epistemic plugin hooks for the given event.

Usage:
    python router.py <EventName>

Where EventName is PreToolUse or PostToolUse.
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
    "PostToolUse": "posttool",
}

# Hooks per event — each hook self-filters by tool_name internally
PRETOOLUSE_HOOKS = [
    "PreToolUse_file_existence_guard.py",
    "PreToolUse_verification_router.py",
    "PreToolUse_evidence_hierarchy_gate.py",
    "PreToolUse_investigation_gate.py",
    "PreToolUse_command_intent_gate.py",
    "PreToolUse_type_validator.py",
    "PreToolUse_dependency_verification_gate.py",
    "fact-guard_PreToolUse.py",
]

POSTTOOLUSE_HOOKS = [
    "PostToolUse_artifact_validator.py",
    "fact-guard_PostToolUse.py",
]

DISPATCH = {
    "PreToolUse": PRETOOLUSE_HOOKS,
    "PostToolUse": POSTTOOLUSE_HOOKS,
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
