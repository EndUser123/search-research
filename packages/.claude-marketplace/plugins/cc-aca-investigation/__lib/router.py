#!/usr/bin/env python3
"""cc-aca-investigation router - dispatches to plugin hooks based on event type.

Registered in settings.json alongside the main router. Runs after local hooks
and after the epistemic router.

Usage:
    python router.py <EventName>

Where EventName is PreToolUse.
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
}

# Hooks — each self-filters by tool_name internally
PRETOOLUSE_HOOKS = [
    "PreToolUse_observe_before_act_gate.py",
    "PreToolUse_discovery_tracker.py",
    "PreToolUse_arch_first_enforcer.py",
    "PreToolUse_require_plan_for_features.py",
    "PreToolUse_implementation_default_gate.py",
    "PreToolUse_breadcrumb_gate.py",
    "PreToolUse_breadcrumb_verifier.py",
]

DISPATCH = {
    "PreToolUse": PRETOOLUSE_HOOKS,
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

            if result.returncode == 2:
                out = result.stdout.decode(errors="replace").strip()
                if out:
                    print(out)
                else:
                    stderr_msg = result.stderr.decode(errors="replace").strip()
                    reason = stderr_msg if stderr_msg else f"Blocked by {hook_name}"
                    print(json.dumps({"decision": "block", "reason": reason}))
                sys.exit(2)

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
            pass
        except Exception:
            pass

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
