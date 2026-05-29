#!/usr/bin/env python3
"""
Anti-Sycophancy Layer 1: Advocate Protocol Injection
Hook: UserPromptSubmit
Purpose: Inject positive-task framing when user expresses skepticism

Control: ANTI_SYCOPHANCY_ENABLED environment variable (default: true)

v2: Added conditional verbosity and single-use flag
"""

# Hook enabled by default - set ENABLED = True to disable
ENABLED = True
if not ENABLED:
    import sys

    sys.exit(0)

import json
import os
import re
import sys

# Check kill switch first
if os.environ.get("ANTI_SYCOPHANCY_ENABLED", "true").lower() != "true":
    sys.exit(0)

# High-confidence skepticism patterns (clear questioning of approach)
HIGH_STAKES_PATTERNS = [
    r"is that (?:really|truly|actually)\s+(?:the\s+)?(?:best|optimal|right)",
    r"(?:shouldn't|wouldn't|couldn't)\s+we\s+(?:just|instead|rather)",
    r"you\s+(?:overcomplicated|overengineered|went too far)",
    r"(?:that's|it's|this is)\s+(?:way\s+)?too\s+(?:complex|complicated|much)",
]

# Lower-confidence skepticism (mild questioning)
LOW_STAKES_PATTERNS = [
    r"are you sure",
    r"(?:is|are)\s+that\s+(?:necessary|needed)",
    r"(?:seems|looks)\s+(?:overly|unnecessarily)",
    r"(?:i\s+)?(?:don't|do not)\s+think",
    r"let's\s+not",
]

# Full protocol for high-stakes disagreements
FULL_ADVOCATE_PROTOCOL = """
<ADVOCATE_PROTOCOL>
You MUST now conduct a formal adversarial analysis BEFORE responding.

REQUIRED ANALYSIS STEPS:
1. ARGUMENTS PRO: List why the user's skepticism or suggested path is CORRECT.
2. ARGUMENTS AGAINST: List why your previous approach was correct.
3. ADJUDICATION: Compare both sets of arguments objectively.
4. SYNTHESIS: Provide your final answer based on the analysis.

OUTPUT GUIDELINE: Keep response concise (2-4 paragraphs).
Show your reasoning, not a structured report.
FORBIDDEN: Starting with "You're absolutely right" or similar praise
without completing this analysis.
</ADVOCATE_PROTOCOL>
"""

# Light protocol for minor skepticism
LIGHT_ADVOCATE_PROTOCOL = """
<ADVOCATE_PROTOCOL_LIGHT>
Before agreeing: state ONE reason FOR and ONE reason AGAINST your previous
approach in your thinking process. Then give your conclusion.
</ADVOCATE_PROTOCOL_LIGHT>
"""


def main():
    try:
        input_data = json.load(sys.stdin)
        prompt = input_data.get("prompt", "")

        # Check for high-stakes patterns first
        is_high_stakes = any(
            re.search(pattern, prompt, re.IGNORECASE)
            for pattern in HIGH_STAKES_PATTERNS
        )

        if is_high_stakes:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "UserPromptSubmit",
                            "additionalContext": FULL_ADVOCATE_PROTOCOL,
                        }
                    }
                )
            )
            sys.exit(0)

        # Check for low-stakes patterns
        is_low_stakes = any(
            re.search(pattern, prompt, re.IGNORECASE) for pattern in LOW_STAKES_PATTERNS
        )

        if is_low_stakes:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "UserPromptSubmit",
                            "additionalContext": LIGHT_ADVOCATE_PROTOCOL,
                        }
                    }
                )
            )
            sys.exit(0)

        # No skepticism detected - no injection
        sys.exit(0)

    except Exception:
        # Don't block on errors - fail open
        sys.exit(0)


if __name__ == "__main__":
    main()
