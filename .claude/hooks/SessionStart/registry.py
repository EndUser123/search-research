"""Hook registry for SessionStart modules."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HOOKS: dict[str, str] = {}
HOOK_PRIORITY: dict[str, float] = {}

def register_session_hook(name: str, priority: float = 10.0):
    def decorator(hook_file: str):
        HOOKS[name] = hook_file
        HOOK_PRIORITY[name] = priority
        return hook_file
    return decorator

def run_session_hooks(data: dict[str, Any]):
    HOOKS_DIR = Path(__file__).resolve().parent.parent

    sorted_hooks = sorted(HOOK_PRIORITY.items(), key=lambda x: x[1])

    for name, _ in sorted_hooks:
        hook_file = HOOKS[name]
        hook_path = HOOKS_DIR / hook_file
        if not hook_path.exists():
            continue

        try:
            # SessionStart hooks are often sequential and critical
            subprocess.run(
                [sys.executable, str(hook_path)],
                input=json.dumps(data).encode(),
                capture_output=True,
                timeout=15.0 # Setup tasks can be slower
            )
        except Exception as e:
            print(f"SessionStart Hook {name} failed: {e}", file=sys.stderr)
