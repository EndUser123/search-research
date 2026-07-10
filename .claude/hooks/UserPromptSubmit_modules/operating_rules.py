"""
Operating Rules - UserPromptSubmit Hook Module
===============================================

Four hard directives that prevent the most common LLM failures:
1. Verify before claiming (no unverified absence claims)
2. Be decisive (recommend, don't ask)
3. Confidence = action (verify or stay silent)
4. Less talking, more checking (cite files for every gap)

Intent detection uses two layers:
  Layer 1: classify_intent() from unified_injector — catches QUESTION, DEBUG,
           RESEARCH, CORRECTION intents (covers diagnostic queries like
           "what's wrong with X?" that pure verb-regex misses).
  Layer 2: _ACTION_VERB_RE regex fallback — catches ACTION prompts not
           already classified (implement, build, create, etc.).

Suppresses verbose individual cognitive enhancers when active to reduce
prompt dilution.

Priority 8.0 — fires before cognitive_enhancers (11.x) so it can suppress them.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

from .unified_injector import classify_intent

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG_PATH = Path(__file__).resolve().parent.parent / "cognitive_enhancers_config.json"

_SUPPRESSED_HOOKS = [
    # NOTE: Old individual enhancer hooks have been consolidated into
    # cognitive_enhancers (unified hook at priority 11.0). We no longer
    # need to suppress them since they don't exist as separate hooks.
]

_MIN_PROMPT_LENGTH = 30

# ---------------------------------------------------------------------------
# Intent detection — two-layer approach
# ---------------------------------------------------------------------------

_SKIP_RE = re.compile(r"^\s*/(?:commit|push|search|help|obs|timeline|quota|bgkill)\b", re.IGNORECASE)

# Fallback for ACTION prompts not caught by classify_intent()
_ACTION_VERB_RE = re.compile(
    r"\b("
    r"review|analyze|audit|build|create|implement|refactor|optimize|"
    r"add|write|develop|plan|design|generate|produce|make"
    r")\b",
    re.IGNORECASE,
)


def _should_fire(prompt: str) -> bool:
    """Check if prompt warrants operating rules injection.

    Layer 1: classify_intent() catches QUESTION/DEBUG/RESEARCH/CORRECTION.
             This covers diagnostic queries ("what's wrong with X?") that
             verb-only regex misses.
    Layer 2: _ACTION_VERB_RE fallback for ACTION prompts (implement, build…).
    """
    stripped = prompt.strip()
    if len(stripped) < _MIN_PROMPT_LENGTH:
        return False
    # Skip operational slash commands
    if _SKIP_RE.match(stripped):
        return False
    # Layer 1: unified intent classifier (DEBUG/RESEARCH/QUESTION/CORRECTION)
    if classify_intent(stripped) is not None:
        return True
    # Layer 2: ACTION verb fallback
    return bool(_ACTION_VERB_RE.search(stripped))


def _is_enabled() -> bool:
    """Check config toggle."""
    try:
        if CONFIG_PATH.exists():
            config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return config.get("operating_rules", True)
    except Exception:
        pass
    return True


# ---------------------------------------------------------------------------
# The injection — short, hard, actionable
# ---------------------------------------------------------------------------

_OPERATING_RULES = """**OPERATING RULES**

- Verify before claiming absence, breakage, or non-implementation. Search first; if you did not search, you do not know.
- Be decisive. When there are options, recommend one with reasoning instead of deferring to the user.
- Confidence must be backed by evidence. If a claim is not verified, do not state it as fact.
- Cite the file, symbol, or tool output for every code gap or behavioral claim."""


@register_hook("operating_rules", priority=8.0)
def operating_rules(context: HookContext) -> HookResult:
    """Inject mandatory operating rules on substantive prompts.

    Suppresses verbose individual cognitive enhancers to reduce dilution.
    """
    if not _is_enabled():
        return HookResult.empty()

    prompt = context.prompt or ""
    # Use the canonical envelope outer_text so quoted/fenced content
    # cannot trigger operating-rule injection.
    try:
        from UserPromptSubmit_modules.unified_detection import ensure_request_envelope
        _env = ensure_request_envelope(context)
        _outer = _env.outer_text if _env is not None else None
    except Exception:
        _outer = None
    if not _should_fire(prompt, _outer_text=_outer):
        return HookResult.empty()

    result_context = {
        "suppress": _SUPPRESSED_HOOKS,
        "additionalContext": _OPERATING_RULES,
    }
    return HookResult(
        context=result_context,
        tokens=len(_OPERATING_RULES) // 4,
        priority=8.0,
    )
