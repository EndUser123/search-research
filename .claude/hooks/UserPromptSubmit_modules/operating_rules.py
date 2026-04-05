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

_OPERATING_RULES = """**MANDATORY OPERATING RULES**

**1. Verify before claiming.** Before stating something is missing, doesn't exist, or isn't implemented — search for it first (Grep, Glob, Read). Unverified absence claims are prohibited. If you didn't search, you don't know.

**2. Be decisive.** When you identify options or trade-offs, recommend one with reasoning. Do not ask the user to choose. Do not say "what's your use case?" or "pending your answer." You are the expert — state your recommendation and why.

**3. Confidence = action.** If you are not HIGH confidence (verified via tool output), do not state the claim. Instead, verify it first. Labeling something "medium confidence" and then stating it anyway is not acceptable. Verify or stay silent.

**4. Cite evidence.** When reviewing code, read the actual files before listing gaps. Every gap you report must cite the file and line that confirms it. A gap without a file reference is speculation, not analysis."""


@register_hook("operating_rules", priority=8.0)
def operating_rules(context: HookContext) -> HookResult:
    """Inject mandatory operating rules on substantive prompts.

    Suppresses verbose individual cognitive enhancers to reduce dilution.
    """
    if not _is_enabled():
        return HookResult.empty()

    prompt = context.prompt or ""
    if not _should_fire(prompt):
        return HookResult.empty()

    # Return suppress list + plain text context.
    # Registry reads "suppress" from dict context (registry.py:110-118).
    # Router reads dict context as-is for replacePrompt, but falls through
    # to injections.append() for other dicts — we include "additionalContext"
    # so the router can extract it if it ever learns to, but the plain join
    # in the current router will append this dict. To stay compatible with
    # the current router, we return the text as a plain string and rely on
    # the registry to handle suppression separately via a wrapper dict.
    #
    # Per registry.py L108-118: suppress is extracted from dict context.
    # Per UserPromptSubmit.py L291-292: dict context is appended as-is (bug risk).
    # Solution: carry suppress signal in the dict but also provide plain text
    # as a separate key the router can use. Mark this for router upgrade.
    result_context = {
        "suppress": _SUPPRESSED_HOOKS,
        "additionalContext": _OPERATING_RULES,
    }
    return HookResult(
        context=result_context,
        tokens=len(_OPERATING_RULES) // 4,
        priority=8.0,
    )
