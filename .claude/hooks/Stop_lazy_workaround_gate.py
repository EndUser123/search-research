#!/usr/bin/env python3
"""
Lazy Workaround Detection Gate

Blocks LLM responses that suggest accepting bugs as features instead of fixing root causes.

Pattern: "Accept X as Y" where X is a problem and Y is a euphemism.
Example: "Accept duplicate task bars as 'visible logging'"

This is LAZY and UNACCEPTABLE. Fix the actual problem.
"""

import json
import re
import sys

# Lazy workaround patterns to block
LAZY_PATTERNS = [
    # Accept-as-feature patterns
    (r"accept\s+.*\s+as\s+(visible\s+logging|feature|design|intentional|expected)", "accepting bug as feature"),

    # "Live with it" patterns
    (r"live\s+with\s+(the\s+)?(bug|issue|problem|limitation|behavior)", "accepting technical debt"),

    # "That's fine/acceptable/expected" for actual problems
    (r"(duplicates?|redundant|extra|double).*(is\s+)?(fine|acceptable|expected|normal|ok)", "ignoring duplication"),

    # "Cosmetic" dismissal of functional issues
    (r"(cosmetic|minor|trivial).*(bug|issue|problem|error)", "dismissing functional bug"),

    # "Not worth fixing" - lazy prioritization
    (r"not\s+worth\s+(fixing|addressing|investigating)", "avoiding necessary work"),

    # "Workaround is fine" instead of fixing
    (r"workaround\s+(is\s+)?(fine|acceptable|sufficient|good)", "accepting workaround over fix"),

    # ANTI-PATTERN-4: "Fix" that is actually a try/except wrapper (error suppression)
    (
        r"added?\s+(?:a\s+)?try\s*/\s*except\s+(?:to\s+)?suppress",
        "try/except error suppression is not a fix",
    ),
    (
        r"wrapped?\s+(?:it\s+)?in\s+try\s*/\s*except\s+(?:to\s+)?hide",
        "try/except error suppression is not a fix",
    ),
    (r"catch\s+the\s+exception\s+(?:and\s+)?(ignore|suppress|hide|pass)", "exception suppression is not a fix"),
    (r"except\s*\([^)]*\)\s*:\s*pass\s*(?:#|$)", "bare except:pass is error suppression, not fix"),

    # ANTI-PATTERN-4: "Fix" that reduces timeout to hide slowness
    (r"reduced?\s+(?:the\s+)?timeout\s+(?:to|from)\s+\d+", "reducing timeout hides slowness, doesn't fix it"),
    (r"shortened?\s+timeout", "shortening timeout hides slowness, doesn't fix it"),

    # ANTI-PATTERN-4: "Fix" that adds skip/bypass logic
    (r"skip(?:ped)?\s+(?:the\s+)?(?:check|validation|verification)\s+(?:to\s+)?(?:fix|handle)", "skipping validation is not a fix"),
    (r"bypass(?:ed)?\s+(?:the\s+)?(?:check|validation)", "bypassing checks is not a fix"),
]

# Root cause phrases that signal proper investigation
ROOT_CAUSE_PHRASES = [
    r"trace\s+(the\s+)?(source|cause|origin)",
    r"investigate\s+why",
    r"find\s+(the\s+)?(root\s+)?cause",
    r"identify\s+where",
    r"debug\s+(the\s+)?(issue|problem)",
    r"fix\s+(the\s+)?(underlying|root)",
    r"prevent\s+(the\s+)?duplication",
]

def check_lazy_workarounds(response: str) -> dict:
    """
    Check if response contains lazy workaround suggestions.

    Args:
        response: The assistant's response text

    Returns:
        dict with 'decision' ('allow' or 'block') and optional 'message'
    """
    response_lower = response.lower()

    # Check for lazy patterns
    for pattern, label in LAZY_PATTERNS:
        if re.search(pattern, response_lower, re.IGNORECASE):
            # Check if this is actually explaining the problem (not suggesting it)
            # Allow if it's followed by root cause investigation
            if any(re.search(phrase, response_lower) for phrase in ROOT_CAUSE_PHRASES):
                continue  # This is proper investigation, not lazy acceptance

            # Found lazy pattern without root cause investigation
            return {
                "decision": "block",
                "message": f"LAZY WORKAROUND DETECTED: {label}\n\n"
                          f"⚠️  This suggests accepting a problem instead of fixing the root cause.\n\n"
                          f"Required approach:\n"
                          f"1. TRACE: Find where the problem originates\n"
                          f"2. IDENTIFY: What's causing it\n"
                          f"3. FIX: Address the actual root cause\n"
                          f"4. VERIFY: Confirm the fix works\n\n"
                          f"Pattern matched: {pattern}\n\n"
                          f"Remember: 'Accepting bugs as features' creates technical debt.\n"
                          f"Fix the problem, don't document the workaround."
            }

    return {"decision": "allow"}

def main():
    """Main entry point for command-line testing"""
    if len(sys.argv) > 1:
        # Test mode: check a string
        test_response = " ".join(sys.argv[1:])
        result = check_lazy_workarounds(test_response)
        print(json.dumps(result, indent=2))
    else:
        # stdin mode
        response = sys.stdin.read()
        result = check_lazy_workarounds(response)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
