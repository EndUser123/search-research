#!/usr/bin/env python3
"""cc-aca-observability router — dispatches to plugin hooks based on event type.

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

PHASE_DIR = {'PostToolUse': 'posttool', 'SessionStart': 'sessionstart'}

POSTTOOLUSE_HOOKS = ['PostToolUse_router.py', 'PostToolUse_artifact_scraper.py', 'cjk_drift_detector.py']
SESSIONSTART_HOOKS = ['SessionStart_cc_health.py']

DISPATCH = {
    "PostToolUse": POSTTOOLUSE_HOOKS,
    "SessionStart": SESSIONSTART_HOOKS
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
    main()
