#!/usr/bin/env python3
"""cc-aca-sdlc router - dispatches package SDLC hooks by event.

This is the active settings-routed entrypoint. It intentionally does not rely
on plugin hooks.json loading.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_SHARED_LIB = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / ".claude" / "hooks" / "__lib"
if str(_SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(_SHARED_LIB))
from stop_block_log import _extract_block_ctx, _log_stop_block  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = PLUGIN_ROOT / "hooks"

PHASE_DIR = {
    "PreToolUse": "pretool",
    "PostToolUse": "posttool",
    "Stop": "stop",
    "SessionStart": "start",
}

PRETOOLUSE_HOOKS = [
    "PreToolUse_tdd95_gate.py",
    "PreToolUse_tdd_contract_gate.py",
]

POSTTOOLUSE_HOOKS = [
    "PostToolUse_tdd_state.py",
    "PostToolUse_tdd_state_tracker.py",
]

STOP_HOOKS = [
    "StopHook_tdd_continuation.py",
    "Stop_task_completion_gate.py",
    "Stop_ralph_loop.py",
]

SESSIONSTART_HOOKS = [
    "preflight_require_tdd.py",
]

DISPATCH = {
    "PreToolUse": PRETOOLUSE_HOOKS,
    "PostToolUse": POSTTOOLUSE_HOOKS,
    "Stop": STOP_HOOKS,
    "SessionStart": SESSIONSTART_HOOKS,
}


def _emit_block(out: str, hook_name: str, child_stderr: str = "", ctx: dict | None = None) -> None:
    reason = ""
    if out:
        try:
            parsed = json.loads(out)
            if isinstance(parsed, dict):
                reason = str(parsed.get("reason") or parsed.get("systemMessage") or "").strip()
        except json.JSONDecodeError:
            reason = out.strip()
    if not reason:
        reason = child_stderr.strip() or f"Blocked by {hook_name}"
    # exit 2 → harness discards stdout and feeds stderr to Claude, so this
    # JSON is for downstream consumers/logging only. {"decision":"block",...}
    # is the canonical Stop block shape per the hooks reference.
    if out:
        print(out)
    else:
        print(json.dumps({"decision": "block", "reason": reason}))
    _log_stop_block(hook_name, reason, child_stderr, ctx)
    sys.stderr.write(f"BLOCKED [{hook_name}]: {reason}\n")
    sys.exit(2)


def _emit_approve(event: str) -> None:
    # Stop has no "approve" object — empty stdout is the universal allow. The
    # {"decision": "approve"} shape is PreToolUse-only and schema-invalid for Stop.
    if event != "Stop":
        print("{}")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(0)

    event = sys.argv[1]
    hooks = DISPATCH.get(event)
    if not hooks:
        sys.exit(0)

    phase = PHASE_DIR.get(event, "")
    input_data = sys.stdin.buffer.read()
    block_ctx = _extract_block_ctx(event, input_data)

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
                _emit_block(out, hook_name, result.stderr.decode(errors="replace"), block_ctx)
            if out:
                try:
                    parsed = json.loads(out)
                    if isinstance(parsed, dict) and parsed.get("decision") == "block":
                        _emit_block(out, hook_name, "", block_ctx)
                except json.JSONDecodeError:
                    pass
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass

    _emit_approve(event)


if __name__ == "__main__":
    main()
