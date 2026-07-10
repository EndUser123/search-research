#!/usr/bin/env python3
"""cc-model-router router — dispatches SessionStart and UserPromptSubmit hooks.

Registered in settings.json. Replaces hooks.json-based dispatch.

Usage:
    python router.py <EventName>

Where EventName is SessionStart or UserPromptSubmit.

UPS hooks run in sequence: classify writes recommendation.json every prompt,
apply marks it consumed (audit-only), CCR consumes it at request time.
classify may emit {"systemMessage": ...} in warn mode — the router forwards it.
apply only writes to stderr (informational); its stdout is ignored.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = PLUGIN_ROOT / "hooks"

PHASE_DIR = {
    "SessionStart": "sessionstart",
    "UserPromptSubmit": "userpromptsubmit",
}

SESSION_START_HOOKS = [
    "model_router_init.py",
]

UPS_HOOKS = [
    "model_router_classify.py",
    "model_router_apply.py",
]

DISPATCH = {
    "SessionStart": SESSION_START_HOOKS,
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

    system_messages: list[str] = []

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
                timeout=15,
                creationflags=flags,
            )
        except subprocess.TimeoutExpired:
            continue  # Fail open
        except Exception:
            continue  # Fail open

        out = result.stdout.decode(errors="replace").strip()
        if out:
            try:
                parsed = json.loads(out)
                if isinstance(parsed, dict):
                    msg = parsed.get("systemMessage")
                    if msg:
                        system_messages.append(str(msg))
            except json.JSONDecodeError:
                pass

    if system_messages:
        print(json.dumps({"systemMessage": " | ".join(system_messages)}))

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as _e:
        import traceback as _tb
        try:
            _lib = Path(__file__).resolve().parent.parent.parent / "__lib"
            if str(_lib) not in sys.path:
                sys.path.insert(0, str(_lib))
            from hook_error_sink import log_hook_error  # type: ignore[import-not-found]
            log_hook_error(__file__, str(_e), _tb.format_exc())
        except Exception:
            pass
        sys.exit(0)  # Fail open — model routing is not safety-critical
