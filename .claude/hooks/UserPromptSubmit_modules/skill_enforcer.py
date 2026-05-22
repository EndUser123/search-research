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

_SKILL_GUARD_SRC = Path("P:/packages/skill-guard/src")
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
)

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
]
