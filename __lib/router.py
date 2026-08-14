#!/usr/bin/env python3
"""search-research router - settings-routed archival hook entrypoint."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIR = PLUGIN_ROOT / "hooks"

PHASE_DIR = {"PreCompact": "", "SessionEnd": ""}
PRECOMPACT_HOOKS = ["search-research_PreCompact.py"]
SESSIONEND_HOOKS = ["search-research_SessionEnd.py"]
DISPATCH = {
    "PreCompact": PRECOMPACT_HOOKS,
    "SessionEnd": SESSIONEND_HOOKS,
}


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(0)
    event = sys.argv[1]
    hooks = DISPATCH.get(event)
    if not hooks:
        sys.exit(0)
    input_data = sys.stdin.buffer.read()
    for hook_name in hooks:
        hook_path = HOOKS_DIR / hook_name
        if not hook_path.exists():
            continue
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = subprocess.run(
                [sys.executable, str(hook_path)],
                input=input_data,
                capture_output=True,
                timeout=30,
                creationflags=flags,
            )
            out = result.stdout.decode(errors="replace").strip()
            if out:
                print(out)
            if result.returncode == 2:
                sys.exit(2)
        except subprocess.TimeoutExpired:
            pass
        except Exception:
            pass
    print("{}")


if __name__ == "__main__":
    main()
