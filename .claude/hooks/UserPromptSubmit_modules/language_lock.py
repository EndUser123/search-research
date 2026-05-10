"""Language lock injector for UserPromptSubmit.

Prevents CJK drift from Chinese-trained models (GLM-5.1, etc.) by injecting
a hard language constraint every Nth turn. The Stop-hook cjk_drift_detector.py
is the post-generation backstop that catches anything this misses.

Injects every 5th substantive prompt (configurable via LANGUAGE_LOCK_INTERVAL).
Uses per-terminal counter files in ~/.claude/.artifacts/{terminal_id}/.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

_ENABLED_ENV = "LANGUAGE_LOCK_ENABLED"
_INTERVAL_ENV = "LANGUAGE_LOCK_INTERVAL"
_DEFAULT_INTERVAL = 5

_COUNTER_FILENAME = "language_lock_counter.json"

_INJECTION = (
    "SESSION CONSTRAINT (active until revoked): Output must be in English only. "
    "Do not use any other language in your response."
)

_CASUAL = frozenset({
    "ok", "okay", "thanks", "yes", "no", "got it", "done",
    "continue", "go ahead", "proceed",
})


def _is_enabled() -> bool:
    return os.environ.get(_ENABLED_ENV, "true").lower() in ("1", "true", "yes")


def _get_interval() -> int:
    try:
        return max(1, int(os.environ.get(_INTERVAL_ENV, str(_DEFAULT_INTERVAL))))
    except (ValueError, TypeError):
        return _DEFAULT_INTERVAL


def _artifacts_dir(terminal_id: str) -> Path:
    """Return the terminal-scoped artifacts directory."""
    d = Path.home() / ".claude" / ".artifacts" / terminal_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _counter_path(terminal_id: str) -> Path:
    return _artifacts_dir(terminal_id) / _COUNTER_FILENAME


def _increment_and_check(terminal_id: str, interval: int) -> bool:
    """Increment turn counter and return True if this turn should inject."""
    path = _counter_path(terminal_id)
    count = 0
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            count = data.get("count", 0)
    except (json.JSONDecodeError, OSError):
        count = 0

    count += 1
    try:
        path.write_text(json.dumps({"count": count}), encoding="utf-8")
    except OSError:
        pass

    return interval == 1 or count % interval == 1


@register_hook("language_lock", priority=2.0)
def language_lock(context: HookContext) -> HookResult:
    """Inject English-only constraint every Nth turn to prevent CJK drift."""
    if not _is_enabled():
        return HookResult.empty()

    prompt = context.prompt or ""
    stripped = prompt.strip().lower()

    if not stripped or stripped.startswith("/"):
        return HookResult.empty()

    if stripped in _CASUAL:
        return HookResult.empty()

    terminal_id = context.terminal_id or "default"
    if not _increment_and_check(terminal_id, _get_interval()):
        return HookResult.empty()

    return HookResult(context=_INJECTION, tokens=len(_INJECTION) // 4, priority=2.0)
