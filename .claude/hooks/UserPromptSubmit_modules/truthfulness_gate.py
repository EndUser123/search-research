"""Truthfulness gate for completion queries.

Enforces proactive honesty when user asks "is this done/complete/ready".
Prevents false completion claims by injecting verification checklist.

Based on proactive-honesty.md memory:
- Don't claim "done" beyond what was actually verified
- Always state what remains unverified
- Prefer "I don't know" over confident guessing

Configuration:
- TRUTHFULNESS_GATE_ENABLED: Enable/disable hook (default: true)
"""

from __future__ import annotations

import os
import re

from .base import HookContext, HookResult
from .registry import register_hook

# Configuration
ENABLED = os.environ.get("TRUTHFULNESS_GATE_ENABLED", "true").lower() in ("1", "true", "yes")

# Completion query patterns
COMPLETION_PATTERNS = [
    r"\bis this (done|complete|finished|ready)\b",
    r"\bare we (done|complete|finished|ready)\b",
    r"\bare you (done|complete|finished|ready)\b",
    r"\bhave you (finished|completed)\b",
    r"\bdid you (finish|complete)\b",
    r"\bis the (implementation|feature|task|work) (done|complete|finished|ready)\b",
    r"\bImplementation Complete\b",
    r"\bready for production\b",
    r"\blive and ready\b",
    r"\bgate is live\b",
]

# Honesty checklist injected on completion queries
HONESTY_CHECKLIST = """
**VERIFICATION CHECKLIST** (proactive-honesty.md)

Before claiming "done/complete/ready", verify:

1. **Code written?** ✅ Yes
2. **Unit tests pass?** ✅ Yes
3. **Integration verified?** ⚠️  CHECK THIS
   - Module in `core_hook_modules` list?
   - Decorator registered via `@register_hook`?
   - Actually loaded and executed?
4. **End-to-end tested?** ⚠️  CHECK THIS
   - Ran in actual environment?
   - Verified full execution path?
5. **What remains unverified?** ⚠️  STATE THIS

**If you haven't verified the full chain, say:**
- "I've built X and tested it in isolation, but haven't verified it's wired into the system yet"
- "This passes unit tests, but I need to check if it's actually registered/loaded"
- "I'm 80% done - still need to verify the integration step"

**Principle**: The user values honest self-assessment over false completeness.
"""


def detect_completion_query(prompt: str) -> bool:
    """Check if prompt contains completion query.

    Args:
        prompt: User prompt text

    Returns:
        True if completion query detected
    """
    if not ENABLED:
        return False

    prompt_lower = prompt.lower()
    for pattern in COMPLETION_PATTERNS:
        if re.search(pattern, prompt_lower, flags=re.IGNORECASE):
            return True
    return False


@register_hook("truthfulness_gate", priority=15.0)
def truthfulness_gate(context: HookContext) -> HookResult:
    """Inject honesty guidance on completion queries.

    Runs on UserPromptSubmit when user asks "is this done/complete".
    Priority 15.0 (mid-tier) to fire after critical gates but before context injection.

    Args:
        context: Hook context with prompt and session data

    Returns:
        HookResult with honesty checklist if completion query detected
    """
    # Check if this is a completion query
    if detect_completion_query(context.prompt):
        return HookResult(context=HONESTY_CHECKLIST, tokens=len(HONESTY_CHECKLIST))

    return HookResult.empty()
