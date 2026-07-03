#!/usr/bin/env python3
"""improve-partner router — single dispatch + config gate for the 4 hooks.

Registered in P:/.claude/settings.json as:
    python <plugin>/__lib/router.py <EventName>

Convention note: per repo dispatch invariant, plugin hooks dispatch via this
router (NOT via hooks.json). hooks/hooks.json is kept at {"hooks": {}} and the
original upstream dispatch is preserved in hooks/hooks.original.json.

Gating: config.json "hooks.enabled" (default false). When false the router is
a silent no-op (exit 0, no stdout) so the 4 hooks ship inert. Flip to true to
enable; see HOOKS_AVAILABLE.md for the settings.json wiring snippet.

Usage:
    python router.py <EventName>   # EventName in {UserPromptSubmit,PostToolUse,Stop,SubagentStop}
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
CONFIG_FILE = PLUGIN_ROOT / "config.json"

DISPATCH = {
    "UserPromptSubmit": "user_prompt_signal.py",
    "PostToolUse": "capture_artifact_signal.py",
    "Stop": "stop_review_gate.py",
    "SubagentStop": "subagent_stop_postprocess.py",
}


def _hooks_enabled() -> bool:
    """Read config.json; default to False (inert) on any error."""
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return bool(cfg.get("hooks", {}).get("enabled", False))
    except Exception:
        return False


def main() -> int:
    event = sys.argv[1] if len(sys.argv) > 1 else ""
    # ponytail: gate first, before reading stdin or spawning anything.
    # When disabled the hooks must be invisible: exit 0, no stdout.
    if not _hooks_enabled():
        return 0
    script = DISPATCH.get(event)
    if not script:
        return 0  # unknown event -> no-op rather than error
    target = SCRIPTS_DIR / script
    if not target.exists():
        return 0
    # Forward stdin to the per-event script; surface its exit code.
    stdin_data = sys.stdin.buffer.read() if not sys.stdin.isatty() else None
    try:
        proc = subprocess.run(
            [sys.executable, str(target)],
            input=stdin_data,
            capture_output=True,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        return 0  # ponytail: never block the host on a hook timeout
    sys.stdout.buffer.write(proc.stdout)
    sys.stdout.flush()
    # stderr passthrough is informational; exit code reflects the child.
    if proc.stderr:
        sys.stderr.buffer.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
