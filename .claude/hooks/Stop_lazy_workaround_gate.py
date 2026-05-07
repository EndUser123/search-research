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
    (r"accept\s+.+?\s+as\s+(?:a\s+)?(?:visible\s+logging|feature|design|intentional|expected)", "accepting_bug_as_feature"),

    # "Live with it" patterns
    (r"live\s+with\s+((the|this)\s+)?(bug|issue|problem|limitation|behavior|race\s+condition)", "accepting_technical_debt"),

    # "That's fine/acceptable/expected" for actual problems
    (r"(duplicates?|redundant|extra|double).*(is\s+)?(fine|acceptable|expected|normal|ok)", "ignoring_duplication"),

    # "Cosmetic" dismissal of functional issues
    (r"(cosmetic|minor|trivial).*(bug|issue|problem|error)", "dismissing_functional_bug"),

    # "Not worth fixing" - lazy prioritization
    (r"n[o']t\s+worth\s+(fixing|addressing|investigating)", "avoiding_necessary_work"),

    # "Workaround is fine" instead of fixing
    (r"workaround\s+(is\s+)?(fine|acceptable|sufficient|good)", "accepting_workaround_over_fix"),

    # ANTI-PATTERN-4: "Fix" that is actually a try/except wrapper (error suppression)
    (
        r"added?\s+(?:a\s+)?try\s*/\s*except\s+(?:to\s+)?suppress",
        "try_except_error_suppression",
    ),
    (
        r"wrapped?\s+(?:it\s+)?in\s+try\s*/\s*except\s+(?:to\s+)?hide",
        "try_except_error_suppression",
    ),
    (r"catch\s+the\s+exception\s+(?:and\s+)?(ignore|suppress|hide|pass)", "exception_suppression"),
    (r"except\s*\([^)]*\)\s*:\s*pass\s*(?:#|$)", "bare_except_pass"),

    # ANTI-PATTERN-4: "Fix" that reduces timeout to hide slowness
    (r"reduced?\s+(?:the\s+)?timeout\s+(?:to|from)\s+\d+", "reducing_timeout"),
    (r"shortened?\s+timeout", "shortening_timeout"),

    # ANTI-PATTERN-4: "Fix" that adds skip/bypass logic
    (r"skip(?:ped)?\s+(?:the\s+)?(?:check|validation|verification)\s+(?:to\s+)?(?:fix|handle)", "skipping_validation"),
    (r"bypass(?:ed)?\s+(?:the\s+)?(?:check|validation)", "bypassing_checks"),
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


def _strip_quoted_blocks(text: str) -> str:
    """Remove quoted/attributed sections that are not the LLM's own words.

    Strips:
    - Markdown blockquotes (lines starting with '> ')
    - Stop-hook feedback blocks (after 'Stop hook' or 'Stop says:')
    - system-reminder blocks
    """
    lines = text.split("\n")
    result: list[str] = []
    skip = False

    for line in lines:
        stripped = line.strip()

        # Skip markdown blockquote lines
        if stripped.startswith("> "):
            continue

        # Skip system-reminder blocks (begin/end)
        if stripped.startswith("<system-reminder") or stripped == "</system-reminder>":
            skip = not stripped.endswith(">")
            if stripped.endswith(">") and stripped.startswith("<system-reminder"):
                continue
            continue
        if skip:
            continue

        # Skip Stop-hook feedback artifacts and their continuation lines
        if re.match(
            r"(?:Stop (?:hook|says)|⎿|Stop\s+hook\s+feedback|LAZY WORKAROUND|EPISTEMIC FORMAT REPAIR|Pattern matched:|Required approach:|Remember:|This suggests)",
            stripped,
        ):
            skip = True
            continue
        # Skip continuation of Stop feedback blocks (indented text or short advisory lines)
        if skip and (not stripped or stripped.startswith(("⚠", "1.", "2.", "3.", "4.", "✓", "✗", "Do NOT"))):
            continue
        if skip:
            skip = False  # End of stop block — keep this line

        result.append(line)

    return "\n".join(result)


def check_lazy_workarounds(response: str) -> dict:
    """
    Check if response contains lazy workaround suggestions.

    Args:
        response: The assistant's response text

    Returns:
        dict with 'decision' ('allow' or 'block') and optional 'message'
    """
    # Preprocess: strip quoted blocks and Stop-hook artifacts
    clean = _strip_quoted_blocks(response)
    clean_lower = clean.lower()

    # Check for lazy patterns
    for pattern, label in LAZY_PATTERNS:
        if re.search(pattern, clean_lower, re.IGNORECASE):
            # Check if this is actually explaining the problem (not suggesting it)
            # Allow if it's followed by root cause investigation
            if any(re.search(phrase, clean_lower) for phrase in ROOT_CAUSE_PHRASES):
                continue  # This is proper investigation, not lazy acceptance

            # Report/implementation context: allow phrases describing intended system behavior.
            # Excludes any pattern containing "bug", "acceptable", or "intentional as" to avoid
            # overlapping with the bug-as-feature lazy patterns.
            _REPORT_ALLOW_PATTERNS = [
                r"\btwo\b.*\bsignals?\b.*\bsuppress",
                r"\bthe\s+advisory\b.*\bsuppress",
                r"\bsuppression\s+is\b.*\bcorrect\b",
                r"\bthe\s+edge\s+case\b.*\bto\s+monitor\b",
            ]
            if any(re.search(p, clean_lower) for p in _REPORT_ALLOW_PATTERNS):
                continue  # Describing intended behavior, not accepting a bug

            return {
                "decision": "block",
                "message": f"LAZY WORKAROUND DETECTED: {label.replace('_', ' ')}\n\n"
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
