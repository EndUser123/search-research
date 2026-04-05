"""Coach Note Reader - UserPromptSubmit Hook Module

Injects coach notes from previous Stop advisory into the current prompt.
Coach notes are written by Stop hooks when specific issues are detected
(e.g., "fixed without tests") and persist to the next turn for awareness.

Priority: 5.0 (runs early to provide context before other hooks)
Config: coach_note_reader (default: true)
"""
from __future__ import annotations

from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).resolve().parent.parent / "cognitive_enhancers_config.json"

_DEFAULT_CONFIG = {
    "coach_note_reader": True,
}


def _load_config() -> dict:
    """Load config with defaults. Fail open on any error."""
    config = dict(_DEFAULT_CONFIG)
    try:
        if CONFIG_PATH.exists():
            import json

            user_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            config.update(user_config)
    except Exception:
        pass
    return config


# ---------------------------------------------------------------------------
# Coach Note Reader Hook (priority 5.0)
# ---------------------------------------------------------------------------


@register_hook("coach_note_reader", priority=5.0)
def coach_note_reader(context: HookContext) -> HookResult:
    """Inject coach note from previous Stop advisory if present.

    Coach notes are written by Stop hooks when specific issues are detected
    (e.g., claiming "fixed" without verification). They persist to the next
    turn to ensure the AI is aware of previous concerns.

    Session-scoped: Uses CLAUDE_SESSION_ID and CLAUDE_TERMINAL_ID env vars
    to prevent cross-contamination between concurrent sessions.

    Read-and-clear pattern: Once read, the coach note file is deleted to
    prevent stale notes from persisting indefinitely.

    Config: coach_note_reader (default: true)
    """
    config = _load_config()

    # Master enable/disable
    if not config.get("coach_note_reader", True):
        return HookResult.empty()

    try:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Stop_advisory import read_and_clear_coach_note

        note = read_and_clear_coach_note()
        if not note:
            return HookResult.empty()

        injection = f"**Coach Note** (from previous turn): {note}"
        return HookResult(context=injection, tokens=len(injection) // 4, priority=5.0)
    except Exception:
        return HookResult.empty()
