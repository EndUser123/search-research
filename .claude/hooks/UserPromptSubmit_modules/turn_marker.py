#!/usr/bin/env python3
"""turn_marker.py - Ensure UserPromptSubmit has an active DB-backed turn."""

from __future__ import annotations

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from evidence_store import get_active_turn, start_turn
from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook


@register_hook("turn_marker", priority=0.5)
def write_turn_marker(context: HookContext) -> HookResult:
    """Ensure a DB-backed turn exists for downstream hooks."""
    terminal_id = str(context.terminal_id or "").strip()
    session_id = str(context.session_id or "").strip()
    if not terminal_id:
        return HookResult.empty()

    try:
        turn_id = str(context.data.get("turn_id") or "").strip()
        if not turn_id:
            turn_id = get_active_turn(session_id, terminal_id) or ""
        if not turn_id:
            turn_id = start_turn(
                terminal_id=terminal_id,
                prompt=context.prompt,
                session_id=session_id,
                transcript_path=str(context.data.get("transcript_path", "") or ""),
            )
        if turn_id:
            context.data["turn_id"] = turn_id
    except Exception:
        pass  # Non-fatal

    return HookResult.empty()
