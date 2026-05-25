"""
Ownership-Colocation Nudge - UserPromptSubmit hook

Advisory by design — can't block prompts. The PreToolUse gate
(PreToolUse_ownership_colocation_gate.py) is the enforcement layer.
Two-tier: nudge = planning-time reminder, gate = write-time enforcement.

Injects the "Who Exclusively Owns This?" checklist before the model plans
infrastructure placement, preventing the default of sibling directories when
a single consumer exists.

Problem: LLMs default to peer/shared-looking directories (e.g., .claude/proxy/)
without asking "how many components consume this?" A directory placed at the
wrong level creates a false shared-ownership contract.

Solution: Detect infrastructure-placement intent and inject the three-question
ownership checklist so the model reasons about consumers before deciding location.
"""

from __future__ import annotations

import re

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Patterns that indicate WHERE to put something — placement decisions.
#
# Design rationale for broad keywords (\bproxy\b, \bvenv\b):
#   These are required to have placement-verb context to avoid false positives
#   on discussions of HTTP proxies, proxy servers, or venv activation.
#   Tighter patterns are combined via _has_placement_intent logic below.
#
# Patterns that are inherently placement-specific (no context needed):
#   - "where to put/place/store/create"  — explicit placement question
#   - "new directory/folder"             — creating a location
#   - "shared directory/location"        — explicitly placement-related
#   - "co-locate"                        — placement verb by definition
#   - "virtualenv", "site-packages"      — specific enough to be unambiguous

# Inherently placement-specific — fire on their own.
_PLACEMENT_SPECIFIC = [
    r"\bwhere\s+(?:to\s+)?(?:put|place|store|keep|add|create)\b",
    r"\bnew\s+(?:directory|folder|dir)\b",
    r"\bcreate\s+(?:a\s+)?(?:directory|folder|dir)\b",
    r"\bmake\s+(?:a\s+)?(?:directory|folder|dir)\b",
    r"\bshared\s+(?:directory|folder|location|path)\b",
    r"\bco[-\s]?locat",
    r"\bvirtualenv\b",
    r"\bsite[-_]packages\b",
    r"\binfrastructure\b",
    r"\binfra\b",
    r"\badapter\b",
]

# Context-dependent — only fire when combined with a placement verb nearby.
# Prevents false positives on "configure an HTTP proxy" or "activate the venv".
_PLACEMENT_CONTEXT_REQUIRED = [
    r"\bproxy\b",
    r"\bvenv\b",
]

# Placement verbs that must appear near context-dependent keywords.
_PLACEMENT_VERBS = re.compile(
    r"\b(?:set\s+up|create|build|put|place|add|move|install|"
    r"init(?:ialise|ialize)?|scaffold|bootstrap|structure|organise|organize)\b",
    re.IGNORECASE,
)

_COMPILED_SPECIFIC = [re.compile(p, re.IGNORECASE) for p in _PLACEMENT_SPECIFIC]
_COMPILED_CONTEXT = [re.compile(p, re.IGNORECASE) for p in _PLACEMENT_CONTEXT_REQUIRED]

_NUDGE = """
**OWNERSHIP-COLOCATION CHECK**

You are about to decide where to place infrastructure (proxy, config, venv, scripts, or similar support files).

Before choosing a location, answer:

1. **How many components consume this?**
   - Grep/Glob for imports, references, or usages
   - Count distinct consumers

2. **Decision:**
   - **Exactly one consumer** → Place it INSIDE that consumer's directory
   - **Multiple consumers** → Place it at the common ancestor level (shared location)

3. **Verify you're not defaulting to a sibling directory** without checking consumer count.
   - A peer directory implies shared use — don't create that contract when ownership is exclusive.

Apply Pattern 6 (questioning_patterns.md): *"Who Exclusively Owns This?"*
"""


def _has_placement_intent(prompt: str) -> bool:
    """Return True if the prompt contains infrastructure-placement keywords.

    Two-tier detection:
    - _COMPILED_SPECIFIC: inherently placement-specific, fire on their own
    - _COMPILED_CONTEXT: broad terms (proxy, venv) that require a placement
      verb nearby to avoid false positives on "configure HTTP proxy" etc.
    """
    if not prompt:
        return False
    if any(p.search(prompt) for p in _COMPILED_SPECIFIC):
        return True
    if any(p.search(prompt) for p in _COMPILED_CONTEXT):
        return bool(_PLACEMENT_VERBS.search(prompt))
    return False


@register_hook("ownership_colocation_nudge", priority=5.5)
def ownership_colocation_nudge_hook(context: HookContext) -> HookResult:
    """Inject the ownership-colocation checklist when placement intent is detected."""
    if not _has_placement_intent(context.prompt):
        return HookResult.empty()

    return HookResult(context=_NUDGE)
