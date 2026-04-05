"""
Abstraction Clarity Gate - UserPromptSubmit Hook
================================================

Detects when user questions span multiple abstraction levels without
clear specification, enforcing clarification before execution.

Problem: AI often responds at wrong abstraction level (technical when user
wants process, implementation when user wants principles).

Solution: Detect ambiguous questions and request clarification.

Priority: 9.5 (runs early, before most other hooks)
"""

from __future__ import annotations

import re

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Patterns that signal abstraction ambiguity
# These questions COULD be answered at multiple levels (technical/process/principle)
AMBIGUOUS_PATTERNS = [
    # Process improvement questions
    r"how can (?:we|you|I) make (?:the|this|a) (?:process|workflow|results?) (?:better|more effective)",
    r"what can (?:we|you|I) do to (?:improve|optimize|fix) (?:the|this|a) (?:process|workflow|system)",
    r"how should (?:we|you|I) (?:approach|handle|tackle) (?:this|that)",

    # Meta-analysis questions
    r"analyze (?:the|this|a) (?:problems|issues|challenges)",
    r"what (?:are|were) the (?:main|primary|key) (?:problems|issues)",
    r"what's (?:wrong|broken|missing)",

    # Optimal solution questions
    r"what(?:'s| is)? the (?:optimal|best|right) (?:solution|approach|answer)",
    r"how should (?:we|you|I) (?:solve|address|fix) this",

    # "Better" questions without context
    r"how can (?:this|that|it) be (?:better|improved|optimized)",
    r"(?:what|how) can (?:we|you|I) (?:do|make) (?:this|that) (?:better|right)",
]

AMBIGUOUS_RE = re.compile(
    "|".join(f"(?:{pattern})" for pattern in AMBIGUOUS_PATTERNS),
    re.IGNORECASE
)

# Patterns that indicate user HAS specified abstraction level
# These override the ambiguity detection
CLARITY_PATTERNS = [
    # Technical level indicators (more specific)
    r"\b(?:file|code|function|class|implementation|api|database)\b",
    r"\b(?:write|writ|edit|read|grep|bash|test|deploy|build|debug)\w*\b",
    r"\b(?:fix|implement|refactor)\s+(?:the|this|a)?\s*?\b\w+\b",

    # Process level indicators (more specific - avoid broad terms)
    r"\b(?:decision|pattern|methodology)\b",
    r"\b(?:how (?:we|you|I) (?:work|decide|choose|respond))\b",

    # Principle level indicators (more specific)
    r"\b(?:why|principle|philosophy|underlying|fundamental)\b",
    r"\b(?:what (?:makes|causes|drives) (?:this|that))\b",
]

CLARITY_RE = re.compile(
    "|".join(f"(?:{pattern})" for pattern in CLARITY_PATTERNS),
    re.IGNORECASE
)

# Skip patterns - these are NOT ambiguous despite matching patterns above
SKIP_PATTERNS = [
    r"/(?:\w+)",  # Slash commands (have their own enforcement)
    r"^(?:yes|no|ok|sure|thanks|proceed)",  # Acceptances
    r"\b(?:show|list|display|get|find)\s+(?:me|us)?\s*(?:the|a)?\s*\b",  # Simple requests
]

SKIP_RE = re.compile("|".join(SKIP_PATTERNS), re.IGNORECASE)


# ---------------------------------------------------------------------------
# Gate Logic
# ---------------------------------------------------------------------------

def _is_ambiguous_question(prompt: str) -> bool:
    """Check if prompt has ambiguous abstraction level.

    Args:
        prompt: User prompt text

    Returns:
        True if ambiguous, False otherwise
    """
    # Skip short prompts
    if len(prompt.strip()) < 20:
        return False

    # Check skip patterns first
    if SKIP_RE.search(prompt):
        return False

    # Check if matches ambiguous pattern
    if not AMBIGUOUS_RE.search(prompt):
        return False

    # Check if user provided clarity
    if CLARITY_RE.search(prompt):
        return False

    return True


def process_prompt(ctx: HookContext) -> HookResult:
    """Check for abstraction ambiguity and request clarification if needed.

    Args:
        ctx: Hook context with prompt, data, etc.

    Returns:
        HookResult with clarification request if ambiguous
    """
    prompt = ctx.prompt

    if not _is_ambiguous_question(prompt):
        return HookResult.empty()

    # Build clarification request
    clarification = """
ABSTRACTION LEVEL CLARIFICATION NEEDED

Your question could be answered at multiple levels:

Technical Level (files, code, implementations)
  Example: "Which files need to change?" or "What's the bug in this code?"

Process Level (workflows, decisions, patterns)
  Example: "How should we approach this kind of problem?" or "What decision patterns led to this?"

Principle Level (why things work, fundamental concepts)
  Example: "Why does this keep happening?" or "What's the underlying issue?"

Before I execute, please specify:
1. What level of abstraction are you interested in?
2. What specific outcome are you optimizing for?

Example rephrasing:
  "At the process level, what patterns led to this outcome?"
  "From a technical perspective, what files need to change?"
  "At the principle level, why does this system keep producing this result?"

This prevents me from responding at the wrong level and wasting our time.
"""

    # Return warning (not blocking, per recommendation)
    return HookResult(
        context=clarification,
        tokens=len(clarification.split()),
    )


# Register the hook
# Priority: 9.5 (runs early, before most other hooks but after session init)
register_hook("abstraction_clarity_gate", priority=9.5)(process_prompt)
