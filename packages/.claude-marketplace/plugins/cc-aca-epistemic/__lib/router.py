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
    "PreToolUse_recent_evidence_gate.py",
]

POSTTOOLUSE_HOOKS = [
    "PostToolUse_artifact_validator.py",
    "PostToolUse_recent_evidence_tracker.py",
]

DISPATCH = {
    "PreToolUse": PRETOOLUSE_HOOKS,
    "PostToolUse": POSTTOOLUSE_HOOKS,
}


def _emit_block(out: str, hook_name: str, child_stderr: str = "") -> None:
    """Emit a block on both channels, then exit(2).

    The harness surfaces ONLY stderr for exit-2 blocks; stdout JSON is ignored
    by the harness UI. Without the stderr line the user sees a bare
    "Blocked by hook" with no reason (see blocking_stderr_standard). We still
    print the JSON to stdout for any downstream consumer / logging.
    """
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
    msg = f"BLOCKED [{hook_name}]: {reason}\n"
    try:
        sys.stderr.write(msg)
    except UnicodeEncodeError:
        sys.stderr.buffer.write(msg.encode("utf-8", "replace"))
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
                child_stderr = result.stderr.decode(errors="replace")
                _emit_block(out, hook_name, child_stderr)

            # Check for block in JSON output
            out = result.stdout.decode(errors="replace").strip()
            if out:
                try:
                    parsed = json.loads(out)
                    if isinstance(parsed, dict) and parsed.get("decision") == "block":
                        _emit_block(out, hook_name)
                except json.JSONDecodeError:
                    pass
        except subprocess.TimeoutExpired:
            pass  # Fail open
        except Exception:
            pass  # Fail open

    # All hooks passed
    print(json.dumps({"decision": "approve"}))


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
