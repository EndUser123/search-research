#!/usr/bin/env python3
"""
RCA Schema Injector - Prevents RCA contract validation failures

Injects the 9-field RCA schema into context when RCA intent is detected,
preventing block/regenerate cycles from missing required fields.

Architecture:
- Detects RCA intent via pattern matching on user message
- Loads schema template from canonical location (with embedded fallback)
- Injects schema as additionalContext before LLM generation

This follows the "Prevention Over Detection" principle:
- Detection (current): Hook validates after generation → block → regenerate
- Prevention (this): Schema injection guides generation before validation → first-try success
"""

from __future__ import annotations

import re
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Patterns that indicate RCA intent
# Covers explicit commands, aliases, and natural language descriptions
# Note: Command patterns use ^\s* or \s to avoid \b issues with / character
RCA_INTENT_PATTERNS = [
    r"(?:^|\s)/rca\b",                     # Explicit /rca command
    r"(?:^|\s)/debugRCA\b",                # debugRCA command
    r"\bdebugging\s+RCA\b",                # Debugging RCA
    r"\broot\s+cause\s+analysis\b",         # Root cause analysis phrase
    r"\bRCA:\b",                           # RCA: prefix
    r"\binvestigate\s+.*\b(error|bug|crash|issue)\b",  # Investigation phrases
    r"\btrace\s+.*\b(bug|error)\b",         # Trace phrases
    r"\b(debug|diagnose)\s+(this\s+)?(error|issue|problem)\b",  # Debug/diagnose phrases
    r"\bwhat\s+(is\s+the\s+)?(root\s+)?cause\b",  # Causal questions
]

# Canonical schema document location
SCHEMA_PATH = Path("P:/__csf/docs/rca-contract-schema.md")

# Embedded fallback schema (used if file not found)
_FALLBACK_SCHEMA = """
## RCA Required Fields (9 total)

All RCA responses MUST include these 9 sections. Missing any field will cause the StopHook_rca_contract to block.

### 1. Symptom
What is the problem? Describe the error, crash, or unexpected behavior.

### 2. Evidence
What data supports this investigation? Include:
- Current-turn tool citations (Read, Grep, Bash outputs)
- File paths and line numbers
- Tier labels: [current-state], [transcript-time], [inference]

### 3. Executed Path
Step-by-step execution trace showing:
- Function calls with line numbers
- Variable state at each step
- Resource acquisition/release
- All three scenarios: happy path, error path, edge case

### 4. Alternative Hypothesis
What other causes were considered? List >=2 hypotheses.

### 5. Falsifier
What evidence disproves each alternative hypothesis?

### 6. Ruled Out
**REQUIRED**: Document what alternatives were considered and why each was rejected.
This is a SEPARATE field from Falsifier. Most common RCA error is omitting this section.

### 7. Root Cause
What is the actual cause? Must be reachable from Executed Path.

### 8. Fix
What changes will resolve the issue? Include file paths and code.

### 9. Verification
How will we confirm the fix works? Include specific commands or tests.

## Common Pitfalls

1. **Missing "Ruled Out" section** - Most common block reason
2. **Root Cause not reachable from Executed Path** - Identifiers don't match
3. **No current-turn evidence** - All evidence is from transcript, not this turn
4. **Alternative Hypothesis missing** - Only presented one hypothesis
"""


def _is_rca_intent(text: str) -> bool:
    """Check if message indicates RCA intent.

    Args:
        text: User message to check

    Returns:
        True if any RCA intent pattern matches
    """
    if not text:
        return False

    text_lower = text.lower()
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in RCA_INTENT_PATTERNS)


def _load_schema_template() -> str:
    """Load schema template from canonical location.

    Returns:
        Schema template content, or embedded fallback if file not found
    """
    try:
        return SCHEMA_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        # Embedded fallback ensures hook works even if file is missing
        return _FALLBACK_SCHEMA
    except Exception:
        # Any other error (permissions, encoding, etc.) - fall back to embedded
        return _FALLBACK_SCHEMA


@register_hook("rca_schema_injector", priority=3.0)
def rca_schema_injector_hook(context: HookContext) -> HookResult:
    """Hook function that injects RCA schema when RCA intent is detected.

    Args:
        context: Hook context containing user message

    Returns:
        HookResult with schema injection if RCA detected, empty result otherwise
    """
    user_message = context.data.get("userMessage", "")

    if not _is_rca_intent(user_message):
        return HookResult.empty()

    schema_template = _load_schema_template()
    if not schema_template:
        return HookResult.empty()

    injection = f"""
---

## RCA Contract Schema Required

Your response must follow this 9-field structure for Root Cause Analysis:

{schema_template}

**CRITICAL**: All 9 fields are required. The most common error is omitting the "Ruled Out" section.

The StopHook_rca_contract will BLOCK your response if any field is missing.

---
"""
    return HookResult(context=injection, tokens=len(injection.split()) * 1.3)


# For testing
if __name__ == "__main__":
    import sys

    test_cases = [
        ("Should trigger: /rca test error", True),
        ("Should trigger: root cause analysis of the bug", True),
        ("Should trigger: investigate this crash", True),
        ("Should NOT trigger: what is the weather", False),
        ("Should NOT trigger: create a new file", False),
    ]

    print("RCA Schema Injector Self-Test")
    print("=" * 50)

    for msg, expected in test_cases:
        result = _is_rca_intent(msg)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{msg}' -> {result} (expected {expected})")

    print("\nSchema path:", SCHEMA_PATH)
    print("Schema exists:", SCHEMA_PATH.exists())
