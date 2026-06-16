#!/usr/bin/env python3
"""cc-aca-safety router - dispatches package safety hooks by event.

This is the active settings-routed entrypoint. It intentionally does not rely
on plugin hooks.json loading.
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
    "UserPromptSubmit": "userpromptsubmit",
}

PRETOOLUSE_HOOKS = [
    "PreToolUse_win32_path_gate.py",
    "PreToolUse_directory_policy.py",
    "PreToolUse_protected_file_recovery_gate.py",
    "PreToolUse_git_auto_stage.py",
    "PreToolUse_ownership_colocation_gate.py",
    "PreToolUse_bulk_delete_gate.py",
    "PreToolUse_repo_visibility_guard.py",
    "PreToolUse_path_validator.py",
]

USERPROMPTSUBMIT_HOOKS = [
    "ownership_colocation_nudge.py",
]

DISPATCH = {
    "PreToolUse": PRETOOLUSE_HOOKS,
    "UserPromptSubmit": USERPROMPTSUBMIT_HOOKS,
}


def _emit_block(out: str, hook_name: str, child_stderr: str = "") -> None:
    reason = ""
    if out:
        print(out)
        try:
            parsed = json.loads(out)
            if isinstance(parsed, dict):
                reason = str(parsed.get("reason") or parsed.get("systemMessage") or "").strip()
        except json.JSONDecodeError:
            reason = out.strip()
    if not reason:
        reason = child_stderr.strip() or f"Blocked by {hook_name}"
        if not out:
            print(json.dumps({"decision": "block", "reason": reason}))
    sys.stderr.write(f"BLOCKED [{hook_name}]: {reason}\n")
    sys.exit(2)


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
        hook_path = HOOKS_DIR / phase / hook_name if phase else HOOKS_DIR / hook_name
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
            out = result.stdout.decode(errors="replace").strip()
            if result.returncode == 2:
                _emit_block(out, hook_name, result.stderr.decode(errors="replace"))
            if out:
                try:
                    parsed = json.loads(out)
                    if isinstance(parsed, dict) and parsed.get("decision") == "block":
                        _emit_block(out, hook_name)
                except json.JSONDecodeError:
                    pass
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass

    print(json.dumps({"decision": "approve"}))


if __name__ == "__main__":
    main()
