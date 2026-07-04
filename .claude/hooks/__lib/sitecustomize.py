"""Auto-loaded by Python at interpreter startup when this dir is on PYTHONPATH.

Patches subprocess.Popen to inject CREATE_NO_WINDOW on Windows, killing the
console-window flash that every hook/router/script subprocess otherwise emits.
Defensive no-op on non-Windows or if the patch module is unavailable.

Sourced via settings.json env PYTHONPATH=P:/.claude/hooks/__lib so that every
Python process Claude Code spawns (hooks, plugin routers, skill scripts) gets
the patch before any user code runs.
"""
import sys

if sys.platform == "win32":
    try:
        from subprocess_patch import patch_subprocess
        patch_subprocess()
    except Exception:
        pass
