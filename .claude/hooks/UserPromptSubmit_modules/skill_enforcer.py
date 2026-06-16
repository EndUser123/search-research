"""Skill enforcer — re-export compatibility shim.

Enforcement logic lives in skill_guard.skill_enforcer and fires via the plugin's
UserPromptSubmit subprocess hook (hooks.json → skill-guard_UserPromptSubmit.py).

This file is kept for backward compatibility: local modules and tests that import
extract_command_name, should_block_command, build_command_context, etc. still work.
The @register_hook call has been removed — enforcement no longer runs through the
local registry.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# sys.path setup
# ---------------------------------------------------------------------------

import json as _json
def _skill_guard_src() -> Path:
    local_path = Path("P:/packages/.claude-marketplace/plugins/skill-guard/src")
    if local_path.exists():
        return local_path
    try:
        installed = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
        if installed.exists():
            data = _json.loads(installed.read_text(encoding="utf-8"))
            entries = data.get("plugins", data).get("skill-guard@local", [])
            if entries:
                return Path(entries[0]["installPath"]) / "src"
    except Exception:
        pass
    return local_path

_SKILL_GUARD_SRC = _skill_guard_src()
if _SKILL_GUARD_SRC.exists() and str(_SKILL_GUARD_SRC) not in sys.path:
    sys.path.insert(0, str(_SKILL_GUARD_SRC))

_HOOKS_DIR = Path(__file__).resolve().parent.parent
for _p in (Path(r"P:\.claude\hooks"), _HOOKS_DIR):
    if _p.exists() and str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# ---------------------------------------------------------------------------
# Re-exports from skill_guard (authoritative source)
# ---------------------------------------------------------------------------

from skill_guard.skill_enforcer import (  # noqa: E402
    COMMAND_BLOCKLIST,
    SLASH_EXECUTION_LANE,
    HELP_REQUEST_LANE,
    build_command_context,
    build_main_health_context,
    clear_command_intent,
    extract_command_name,
    extract_slash_command,
    is_command_directive,
    is_topic_inquiry,
    log_command_intent_telemetry,
    should_block_command,
    _safe_id,
    _health_report_paths,
    _hook_health_report,
    _fallback_hook_health_report,
    _load_enforcement_config,
)

HOOK_HEALTH_REPORT = _hook_health_report()
FALLBACK_HOOK_HEALTH_REPORT = _fallback_hook_health_report()

__all__ = [
    "COMMAND_BLOCKLIST",
    "SLASH_EXECUTION_LANE",
    "HELP_REQUEST_LANE",
    "build_command_context",
    "build_main_health_context",
    "clear_command_intent",
    "extract_command_name",
    "extract_slash_command",
    "is_command_directive",
    "is_topic_inquiry",
    "log_command_intent_telemetry",
    "should_block_command",
    "_health_report_paths",
    "HOOK_HEALTH_REPORT",
    "FALLBACK_HOOK_HEALTH_REPORT",
    "_load_enforcement_config",
]
