"""UserPromptSubmit Hook Modules.

Provides modular implementations of UserPromptSubmit hooks extracted from
the monolithic UserPromptSubmit_router.py.

Modules:
- base: Base classes and interfaces
- conversation_gate: Question/conversation intent guard
- unified_injector: Solo dev context, goal anchor, falsification
- skill_enforcer: Slash command detection and routing
- plan_injector: Plan context injection and disambiguation
- behavior_contract: Response grounding and self-check rubric
- diagnostic_guard: Speculative claims, quantitative checks
- intent_handlers: Research directives, diagnostic questions
- registry: Hook discovery and loading
"""

from __future__ import annotations

import sys

# Backward compatibility: Create alias for old package name
# This allows imports using "from UserPromptSubmit import ..." to continue working
if __name__ == "UserPromptSubmit_modules":
    legacy_pkg = sys.modules["UserPromptSubmit"] = sys.modules["UserPromptSubmit_modules"]
    if hasattr(sys.modules["UserPromptSubmit_modules"], "__path__"):
        legacy_pkg.__path__ = list(sys.modules["UserPromptSubmit_modules"].__path__)
    spec = getattr(legacy_pkg, "__spec__", None)
    if spec is not None:
        spec.submodule_search_locations = list(getattr(legacy_pkg, "__path__", []))

__all__ = [
    "base",
    "conversation_gate",
    "unified_injector",
    "skill_enforcer",
    "plan_injector",
    "behavior_contract",
    "diagnostic_guard",
    "intent_handlers",
    "registry",
]
