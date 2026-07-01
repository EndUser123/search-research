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

_SHARED_LIB = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / ".claude" / "hooks" / "__lib"
if str(_SHARED_LIB) not in sys.path:
    sys.path.insert(0, str(_SHARED_LIB))
from stop_block_log import _extract_block_ctx, _log_stop_block  # noqa: E402

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
    "Stop_behavior_gates.py",
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


def _emit_block(
    out: str, hook_name: str, child_stderr: str = "", ctx: dict | None = None
) -> None:
    """Emit a block on both channels, then exit(2).

    The harness surfaces ONLY stderr for exit-2 blocks; stdout JSON is ignored
    by the harness UI. Without the stderr line the user sees a bare
    "Blocked by hook" with no reason (see blocking_stderr_standard). We still
    print the JSON to stdout for any downstream consumer / logging.
    """
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
    msg = f"BLOCKED [{hook_name}]: {reason}\n"
    try:
        sys.stderr.write(msg)
    except UnicodeEncodeError:
        sys.stderr.buffer.write(msg.encode("utf-8", "replace"))
    sys.exit(2)


def _emit_approve(event: str) -> None:
    # Stop has no "approve" object — empty stdout is the universal allow. The
    # {"decision": "approve"} shape is PreToolUse-only and schema-invalid for Stop.
    if event != "Stop":
        print(json.dumps({"decision": "approve"}))


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

            # exit code 2 = block
            if result.returncode == 2:
                out = result.stdout.decode(errors="replace").strip()
                child_stderr = result.stderr.decode(errors="replace")
                _emit_block(out, hook_name, child_stderr, block_ctx)

            # Check for block in JSON output (child exits 0 with block decision)
            out = result.stdout.decode(errors="replace").strip()
            if out:
                try:
                    parsed = json.loads(out)
                    if isinstance(parsed, dict) and parsed.get("decision") == "block":
                        _emit_block(out, hook_name, "", block_ctx)
                except json.JSONDecodeError:
                    pass
        except subprocess.TimeoutExpired:
            pass  # Fail open
        except Exception:
            pass  # Fail open

    # All hooks passed
    _emit_approve(event)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import sys, traceback as _tb
        from pathlib import Path as _P
        try:
            _lib = _P(__file__).resolve().parent.parent.parent / "__lib"
            if str(_lib) not in sys.path:
                sys.path.insert(0, str(_lib))
            from hook_error_sink import log_hook_error
            log_hook_error(__file__, str(_e), _tb.format_exc())
        except Exception:
            pass
        sys.exit(1)
