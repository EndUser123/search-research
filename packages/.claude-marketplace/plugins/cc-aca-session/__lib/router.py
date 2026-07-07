#!/usr/bin/env python3
"""cc-aca-session router — dispatches to plugin hooks based on event type.

Registered in settings.json. Works around GitHub issue #16288
(plugin hooks.json not loaded from external files).

Usage:
    python router.py <EventName>
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = PLUGIN_ROOT / "hooks"

PHASE_DIR = {'SessionStart': 'sessionstart', 'SessionEnd': 'sessionend'}

SESSIONSTART_HOOKS = ['aca_session_verification_cleanup.py', 'aca_session_breadcrumb_init.py', 'aca_session_ground_truth_inject.py']
SESSIONEND_HOOKS = ['aca_session_cleanup.py', 'aca_session_breadcrumb_cleanup.py', 'aca_session_tdd_cleanup.py']

DISPATCH = {
    "SessionStart": SESSIONSTART_HOOKS,
    "SessionEnd": SESSIONEND_HOOKS
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

    completed_children: list[tuple[str, subprocess.CompletedProcess]] = []
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

            if result.returncode == 2:
                out = result.stdout.decode(errors="replace").strip()
                child_stderr = result.stderr.decode(errors="replace")
                _emit_block(out, hook_name, child_stderr)

            out = result.stdout.decode(errors="replace").strip()
            if out:
                try:
                    parsed = json.loads(out)
                    if isinstance(parsed, dict) and parsed.get("decision") == "block":
                        _emit_block(out, hook_name)
                except json.JSONDecodeError:
                    pass
            completed_children.append((hook_name, result))
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass

    # FORWARDING BRANCH (Phase 2 of close-the-loop).
    # Cloned from cc-model-router __lib/router.py:80-90 (systemMessage
    # forwarding). One delta: this branch forwards additionalContext from
    # the SessionStart hookSpecificOutput envelope, not systemMessage.
    # Block-decision parsing above is byte-identical to the prior router.
    additional_contexts: list[str] = []
    for hook_name, result in completed_children:
        out = result.stdout.decode(errors="replace").strip()
        if not out:
            continue
        try:
            parsed = json.loads(out)
            if not isinstance(parsed, dict):
                continue
            hso = parsed.get("hookSpecificOutput")
            ctx = hso.get("additionalContext") if isinstance(hso, dict) else None
            if ctx:
                additional_contexts.append(str(ctx))
        except json.JSONDecodeError:
            pass

    if additional_contexts:
        # SessionStart additionalContext envelope. Mirror cc-model-router's
        # ` | `.join(msgs) merge; same shape, different key.
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": "\n\n".join(additional_contexts),
            }
        }))
        sys.exit(0)

    # Allow = emit {} — "decision: approve" is not a valid hook output enum
    # (see stop_hook_output_schema memory / hooks CLAUDE.md output table).
    print("{}")


if __name__ == "__main__":
    main()
