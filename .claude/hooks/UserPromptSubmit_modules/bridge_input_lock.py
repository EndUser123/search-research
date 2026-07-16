"""UserPromptSubmit hook: warn when the bridge holds the UIMutex.

When the bridge is injecting a message from ChatGPT into the Claude Code
terminal (via the terminal_adapter daemon), the lane-scoped UI mutex
(ui-input-<lane>.lock) exists with a live bridge PID.

This hook checks ALL mutex files.  If any is held, it injects a warning
message so the user (and the model) knows the bridge is active.

If the user wants to abort the bridge injection, they can:
1. Press Ctrl+C in the Claude Code terminal
2. Run: .\bridge-abort.ps1 -LaneId <lane>
   (this deletes the lock file; the bridge detects the loss and aborts)

Discriminator: checks P:/.ai-lanes/controller/locks/ui-input-*.lock
"""

from __future__ import annotations

import glob
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Canonical lock directory — matches input_mutex.py
LOCKS_DIR = Path("P:/.ai-lanes") / "controller" / "locks"
LOCK_GLOB = "ui-input-*.lock"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _process_exists(pid: int) -> bool:
    """Check if a process with this PID is running."""
    try:
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        return False
    except Exception:
        return False


def _check_bridge_locks() -> list[dict[str, Any]]:
    """Check all lane-scoped UI mutex files.

    Returns list of dicts for each active lock:
        {"lane_id": str, "bridge_pid": int, "held_since": str}
    """
    if not LOCKS_DIR.exists():
        return []

    active: list[dict[str, Any]] = []
    for lock_path in sorted(LOCKS_DIR.glob(LOCK_GLOB)):
        if not lock_path.is_file():
            continue
        try:
            data = json.loads(lock_path.read_text(encoding="utf-8"))
            pid = int(data.get("pid", 0))
            lane_id = str(data.get("lane_id", ""))
            bridge = bool(data.get("bridge", False))
            at = str(data.get("at", ""))
            if pid and _process_exists(pid) and bridge:
                active.append({
                    "lane_id": lane_id,
                    "bridge_pid": pid,
                    "held_since": at,
                })
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    return active


@register_hook("bridge_input_lock", priority=2.0)
def bridge_input_lock_hook(context: HookContext) -> HookResult:
    """Check for active bridge locks and warn the user if any are held.

    Runs early (priority 2.0) so the warning is visible before other hooks.
    """
    active_locks = _check_bridge_locks()
    if not active_locks:
        return HookResult.empty()

    # Build a human-readable warning
    lanes_desc = ", ".join(
        f"'{l['lane_id']}' (PID {l['bridge_pid']})"
        for l in active_locks
    )

    injection = (
        "[BRIDGE]\n"
        "⚠️ **Bridge Active**\n\n"
        "The ChatGPT↔Claude bridge is currently injecting a message "
        f"into lane(s): {lanes_desc}.  Your prompt will be processed\n"
        "after the bridge releases the input mutex.\n\n"
        "To abort the bridge injection now, run:\n"
        "    .\\bridge-abort.ps1 -LaneId <lane>\n"
        "or press Ctrl+C to interrupt the bridge process.\n"
    )

    return HookResult(
        context=injection,
        tokens=len(injection) // 4,
        priority=2.0,
    )