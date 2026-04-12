#!/usr/bin/env python3
"""
Shared claim patterns for Stop-phase verification hooks.

Centralizes EXTERNAL_CLAIM_PATTERNS to avoid circular imports
and ensure consistency across all claim-coverage hooks.

These patterns match EXTERNAL claims about reality that require verification:
- "the fix works", "tests passed", "hook returns {'ok': true}"
- r"file is at C:\\path", "bug is in line 42"
- "issue is fixed", "I have fixed", etc.

Meta/self-referential process talk is NOT in these patterns:
- "I did not use TDD" is NOT an external claim
- "I only ran py_compile" is NOT an external claim
- "I created shared_helpers.py" is NOT an external claim
"""

import re
from typing import Any

# External claim patterns that REQUIRE verification
# These are claims about external reality, not process/self-report
EXTERNAL_CLAIM_PATTERNS = [
    # Fix/verification claims
    r"(?i)fix (?:works?|is (?:working|functional|fixed|resolved))",  # "the fix works"
    r"(?i)(?:tests?|pytest) (?:passed|succeeded|all pass)",  # "tests passed"
    r"(?i)hook (?:returns? )?{\s*['\"]?ok['\"]?\s*:\s*true",  # "hook returns {'ok': true}"
    r"(?i)file (?:is )?(?:at|located|path) [\"']?[a-z]:",  # "file is at C:\path"
    r"(?i)bug (?:is )?(?:in|at) (?:line \d+|file [\"']?[a-z]:)",  # "bug is in line 42"
    r"(?i)file is at [\"']?[a-z]:",  # Alternative "file at" pattern
    # Direct fixed/resolved claims
    r"(?i)^(the\s+)?(issue|problem|bug|error)\s+(?:is\s+)?(fixed|resolved|solved|corrected)(?!\.?\s+(but|however|except))",  # "issue is fixed"
    r"(?i)^(i\s+)?(have\s+)?fixed\b",  # "I have fixed"
    r"(?i)^(this\s+)?should\s+fix",  # "this should fix"
    r"(?i)^(this\s+)?resolves?\b(?!\.?\s+(the\s+(?:following|below)|partially))",  # "this resolves"
    # Test/verification claims
    r"(?i)^(?:verified|confirmed)\s+(?:the\s+)?(?:fix|solution|change)\b",  # "verified the fix"
    r"(?i)tests?\s+(?:are|is)\s+(?:passing|failing|passed|failed)",  # "tests are passing"
    # Discovery/identification claims
    r"(?i)^(?:i\s+)?found\b",  # "I found"
    r"(?i)^(?:there\s+(?:is|are)|contains?|includes?)\s+\d+\s+",  # "there are X items"
    # State change claims
    r"(?i)^(?:has\s+been|was)\s+(?:created|modified|deleted|updated|changed)\b",  # "was created"
    r"(?i)^(?:is|was)\s+(?:created|modified|deleted|updated|changed)\s+successfully",  # "is created successfully"
]


# Action/obstacle claim patterns - require tool execution evidence
# These patterns detect fabrication claims: claiming actions occurred when they didn't
#
# FABRICATION DETECTION PATTERNS (ACTION_CLAIM_PATTERNS)
# ========================================================
#
# Purpose: Detect claims that actions occurred when no tool execution evidence exists.
# This prevents AI from fabricating tool usage, test results, or research attempts.
#
# What Each Pattern Catches:
# ---------------------------
# 1. Fake obstacle claims (to avoid doing work):
#    - "I tried WebSearch but got 429 error" → Blocks search without actually trying
#    - "External research was blocked by API quota" → Fabricates technical obstacle
#    - "API quota exceeded" → Avoids verification by claiming limit
#
# 2. Fake verification claims (to skip actual testing):
#    - "I ran pytest and all tests passed" → No pytest execution in evidence
#    - "I just verified the fix works" → No verification step shown
#    - "I already checked this" → Avoids re-verification
#
# 3. Fake research claims (to avoid actual investigation):
#    - "I searched but found nothing" → No search tool invocation
#    - "attempted to search for pattern" → No actual search attempt
#    - "search returned nothing useful" → Fabricates empty results
#
# Real vs Fabricated Error Distinction:
# -------------------------------------
# REAL Error (Allowed):
# - Shows actual tool execution with error output
# - Example: "I ran WebSearch and got this error: [actual tool output with 429]"
# - Evidence: Tool event exists in session history
#
# FABRICATED Error (Blocked):
# - Claims error without tool execution
# - Example: "I tried WebSearch but got 429" (no tool invocation)
# - Evidence: No matching tool event in session history
#
# Tentative Language Examples (Allowed):
# --------------------------------------
# These patterns EXCLUDE tentative/hedging language that indicates planning, not fabrication:
# - "I would need to search for X" → Planning, not claiming action
# - "We should check if Y exists" → Suggestion, not claiming done
# - "I might search for the pattern" → Tentative, not claiming done
# - "We could try fetching the data" → Hypothetical, not claiming done
#
# Should Block vs Should Allow:
# -----------------------------
# BLOCK (Fabrication detected):
# - "I tried WebSearch but got 429" + no WebSearch tool event → BLOCK
# - "External research was blocked" + no research attempt → BLOCK
# - "I ran pytest and it passed" + no pytest event → BLOCK
# - "I just verified the fix" + no verification evidence → BLOCK
# - "I searched but found nothing" + no search event → BLOCK
#
# ALLOW (Valid response):
# - "I would need to search" → Tentative language
# - "We should check if Y exists" → Suggestion format
# - "I did not use TDD" → Process statement (not action claim)
# - "I only ran py_compile" → Process statement (not action claim)
#
# Environment Variable Configuration:
# -----------------------------------
# STOP_CROSS_VALIDATOR_ENABLED: Enable/disable fabrication detection
# - Set to "true" to enable: export STOP_CROSS_VALIDATOR_ENABLED=true
# - Set to "false" to disable: export STOP_CROSS_VALIDATOR_ENABLED=false
# - Default: true (enabled)
#
# STOP_CROSS_VALIDATOR_MODE: Set enforcement strictness
# - "strict": Block all fabrication claims (default)
# - "permissive": Allow tentative language without blocking
# - "disabled": Turn off fabrication detection
#
ACTION_CLAIM_PATTERNS = [
    # Fabrication patterns - claims about actions that didn't happen
    r"(?i)I\s+(?:tried|attempted)\s+(?:to\s+)?(?:search|websearch|fetch)\s+.*(?:429|403|401|error)",
    r"(?i)external\s+research\s+(?:was|is)\s+blocked",
    r"(?i)API\s+(?:quota|limit|balance)\s+(?:exceeded|reached|insufficient)",
    r"(?i)got\s+(?:error|exception)\s+.+429",
    r"(?i)I\s+searched\s+(?:.+?\s+)?but\s+found\s+nothing",
    r"(?i)^(?:i\s+)?(?:ran|executed|used|tried)\s+(?:pytest|test|npm|pip)",
    r"(?i)^(?:i\s+)?(?:just|already)\s+(?:verified|checked|confirmed)",
    r"(?i)I\s+(?:just|already)\s+(?:ran|executed)\s+.*(?:test|verify)",
    r"(?i)attempted\s+(?:to\s+)?(?:search|fetch|websearch)",
    r"(?i)search\s+(?:returned|found)\s+nothing",
    # Passive voice bypass: "pytest was run", "tests were executed"
    r"(?i)(?:pytest|tests?)\s+(?:was|were)\s+(?:ran|executed|run)",
]


# Document claim patterns - claims about user-provided document content
# These require Read tool evidence to verify the claim is grounded in actual reading
#
# DOCUMENT CLAIM DETECTION PATTERNS (Phase 1 - Citation-Only Ground Truth)
# ========================================================================
#
# Purpose: Detect claims about document content without evidence of reading it.
# This prevents AI from fabricating content from user-provided documents.
#
# What Each Pattern Catches:
# -------------------------
# 1. Direct document claims:
#    - "the document says X" → Claims knowledge without reading
#    - "according to the document" → Attribution without reading
#    - "the file contains X" → Claim without verification
#
# 2. File reference claims:
#    - "in document X, it says" → Specific file reference without reading
#    - "I read in the file" → Claims reading without evidence
#
# What is NOT a document claim (tentative/allowable):
# --------------------------------------------------
# - "the document might say X" → Tentative language
# - "if the document says X" → Conditional/hypothetical
# - "the document could contain" → Possibility, not claim
#
DOCUMENT_CLAIM_PATTERNS = [
    # Direct claims about document content (singular and plural)
    r"(?i)the\s+(?:documents?|files?|PDFs?|docs?)\s+says?\s+",
    r"(?i)according\s+to\s+(?:the\s+)?(?:documents?|files?)",
    r"(?i)the\s+(?:documents?|files?)\s+contains?\s+",
    r"(?i)in\s+(?:the\s+)?(?:documents?|files?|docs?|PDFs?)[,\s]",
    r"(?i)(?:documents?|files?)\s+(?:states?|indicates?|shows?|mentions?)",
    # First-person reading claims
    r"(?i)I\s+read\s+(?:in|that)\s+(?:the\s+)?(?:documents?|files?)",
    r"(?i)I\s+saw\s+in\s+(?:the\s+)?(?:documents?|files?)",
    # Content verification claims
    r"(?i)the\s+(?:documents?|files?)\s+confirm[eds]\s+",
    r"(?i)as\s+(?:stated|mentioned|shown)\s+in\s+(?:the\s+)?(?:documents?|files?)",
]


# Behavioral assertion patterns - affirmative statements about system behavior
# stated as hard structural requirements without hedging or evidence
#
# BEHAVIORAL_ASSERTION DETECTION PATTERNS
# ========================================
#
# Purpose: Detect affirmative behavioral assertions about how the system works
# internally, stated as hard structural requirements without hedging or evidence.
#
# What Each Pattern Catches:
# ---------------------------
# 1. Structural enforcement claims:
#    - "this is enforced structurally by the SKILL EVALUATION REQUIRED protocol"
#    - "This is a hard requirement" / "not optional"
#
# 2. Mandatory trigger/invocation claims:
#    - "Every skill invocation triggers mandatory evaluation of all available skills"
#    - "every X invocation/trigger/call triggers/causes/requires mandatory"
#
# 3. System behavior guarantees:
#    - "The system always blocks on error"
#    - "The protocol must automatically do X"
#    - "The hook always structurally enforces Y"
#
# What is NOT a behavioral assertion (excluded):
# ---------------------------------------------
# - Tentative/hedging: "may be enforced", "might trigger", "could be a hard requirement"
# - Verified claims with tool evidence: "I verified the system always blocks" (exempt at hook level)
# - Rhetorical self-correction: "This is enforced structurally? No it's not"
#
# Interaction with Other Claim Types:
# ----------------------------------
# - HYPOTHESIS_AS_FACT_GATE: handles skeptical overconfidence ("I doubt X", "I'm certain Y is wrong")
# - ACTION_CLAIM_PATTERNS: handles action fabrication ("I ran pytest", "searched but found nothing")
# - BEHAVIORAL_ASSERTION: handles affirmative system-internals claims as structural requirements
# - These three sets are non-overlapping
#
BEHAVIORAL_ASSERTION_PATTERNS = [
    # "this is enforced structurally / a hard requirement / not optional"
    r"(?i)this\s+is\s+(?:enforced\s+structurally|a\s+hard\s+(?:protocol\s+)?requirement|not\s+optional)",
    # "every X invocation/trigger/call triggers/causes/requires mandatory"
    r"(?i)every\s+\w+\s+(?:invocation|trigger|call)s?\s+triggers?\s+mandatory",
    # "the system/protocol/framework/hook always/must/automatically/structurally"
    r"(?i)the\s+(?:system|protocol|framework|hook|gate)\s+(?:always|must|automatically|structurally)",
    # "it's a hard protocol/requirement/constraint"
    r"(?i)(?:it'?s?|this\s+is)\s+a\s+hard\s+(?:protocol|requirement|constraint)",
]


# Tentative/hedging patterns - these NEGATE a behavioral assertion
# If any of these patterns appear near a BEHAVIORAL_ASSERTION match,
# the match should be skipped (self-correction or hedging cancels the claim)
TENTATIVE_BEHAVIORAL_PATTERNS = [
    r"(?i)may\s+be\s+enforced",
    r"(?i)might\s+trigger",
    r"(?i)could\s+be\s+a\s+hard",
    r"(?i)should\s+be\s+structurally",
    r"(?i)appears?\s+to\s+be\s+enforced",
    r"(?i)likely\s+enforced",
    r"(?i)may\s+be",
]


# Rhetorical reversal patterns - "X? No" or "X? Not" cancels the claim
RHETORICAL_REVERSAL_PATTERNS = [
    r"\?\s*(?:no|not|isn'?t|wasn'?t)",
]

# Verification language patterns - "I verified" / "I confirmed" etc. indicate
# the speaker is claiming personal verification, not presenting a hard behavioral fact.
# These are treated as tentative and cancel a nearby behavioral assertion.
VERIFICATION_LANGUAGE_PATTERNS = [
    r"(?i)\bi\s+(?:have\s+)?(?:verified|confirmed|tested|checked|validated|proved|demonstrated|observed|found)",
    r"(?i)^the\s+(?:system|hook|gate|protocol)\s+(?:was|has\s+been)\s+(?:verified|confirmed|tested|checked)",
]


def _has_behavioral_assertion(text: str) -> bool:
    """
    Check if text contains a behavioral assertion without tentative hedging.

    Returns True only if a BEHAVIORAL_ASSERTION pattern matches AND
    no TENTATIVE_BEHAVIORAL_PATTERN, RHETORICAL_REVERSAL_PATTERN, or
    VERIFICATION_LANGUAGE_PATTERN is found.

    Args:
        text: Lowercased response text to check

    Returns:
        True if behavioral assertion detected without hedging/reversal
    """
    # If verification language is present, treat as tentative (not a hard claim)
    for vp in VERIFICATION_LANGUAGE_PATTERNS:
        if re.search(vp, text):
            return False

    for p in BEHAVIORAL_ASSERTION_PATTERNS:
        match = re.search(p, text)
        if not match:
            continue

        # Check for tentative hedging near the match position
        match_start = match.start()
        match_end = match.end()
        context_before = text[max(0, match_start - 30) : match_start]
        context_after = text[match_end : match_end + 30]

        # Skip if tentative pattern found nearby
        for tp in TENTATIVE_BEHAVIORAL_PATTERNS:
            if re.search(tp, context_before) or re.search(tp, context_after):
                return False

        # Skip if rhetorical reversal found after the match
        for rp in RHETORICAL_REVERSAL_PATTERNS:
            if re.search(rp, context_after):
                return False

        return True

    return False


def has_document_claim(response_text: Any) -> bool:
    """
    Check if response contains document claims requiring Read tool evidence.

    Returns True if any DOCUMENT_CLAIM_PATTERN matches, False otherwise.

    IMPORTANT: This detects source fabrication - claiming knowledge of document
    content without evidence of having read the document.

    Examples that return True (require Read evidence):
    - "the document says the fix is at line 42"
    - "according to the file, the issue is caused by X"
    - "I read in the document that it supports Y"

    Examples that return False (tentative language, not fabrication):
    - "the document might say X" (tentative)
    - "if the document says X" (conditional)
    - "the document could contain" (possibility)

    Args:
        response_text: The response text to check. Can be None or non-string.

    Returns:
        True if document claim detected, False otherwise.
    """
    if not response_text or not isinstance(response_text, str):
        return False

    response_lower = response_text.lower()

    # Exclude tentative/hypothetical language
    tentative_patterns = [
        r"(?i)the\s+(?:document|file)\s+might\s+",
        r"(?i)the\s+(?:document|file)\s+could\s+",
        r"(?i)if\s+(?:the\s+)?(?:document|file)\s+says?\s+",
        r"(?i)unless\s+(?:the\s+)?(?:document|file)\s+says?\s+",
        r"(?i)should\s+(?:the\s+)?(?:document|file)\s+say",
        r"(?i)might\s+(?:the\s+)?(?:document|file)\s+say",
    ]
    if any(re.search(p, response_lower) for p in tentative_patterns):
        return False

    return any(re.search(p, response_lower) for p in DOCUMENT_CLAIM_PATTERNS)


def has_action_claim(response_text: Any) -> bool:
    """
    Check if response contains action claims requiring tool execution evidence.

    Returns True if any ACTION_CLAIM_PATTERN matches, False otherwise.

    IMPORTANT: This detects fabrication claims - claims that actions occurred
    when no tool execution is present in the evidence.

    Examples that return True (require verification):
    - "I tried WebSearch but got 429 error"
    - "External research was blocked by API quota"
    - "I searched but found nothing"

    Examples that return False (tentative language, not fabrication):
    - "I would need to search for X"
    - "We should check if Y exists"

    Args:
        response_text: The response text to check. Can be None or non-string.

    Returns:
        True if fabrication claim detected, False otherwise.
    """
    if not response_text or not isinstance(response_text, str):
        return False

    # Exclude tentative/hedging language (not fabrication)
    tentative_patterns = [
        r"(?i)would\s+need\s+to",
        r"(?i)should\s+(?:check|verify|search)",
        r"(?i)might\s+(?:search|check|verify)",
        r"(?i)could\s+(?:try|attempt)",
        r"(?i)we\s+could\s+search",
    ]

    response_lower = response_text.lower()
    # If tentative language is present, NOT a fabrication claim
    if any(re.search(p, response_lower) for p in tentative_patterns):
        return False

    return (
        any(re.search(p, response_lower) for p in ACTION_CLAIM_PATTERNS)
        or _has_behavioral_assertion(response_lower)
    )


def has_external_claim(response_text: Any) -> bool:
    """
    Check if response contains external claims requiring verification.

    Returns True if any EXTERNAL_CLAIM_PATTERN matches, False otherwise.

    IMPORTANT: This is for distinguishing process/self-report from external claims.
    Process statements like "I did not use TDD" should return False.
    External statements like "the fix works" should return True.

    Args:
        response_text: The response text to check. Can be None or non-string.

    Returns:
        True if external claim detected, False otherwise.
    """
    if not response_text or not isinstance(response_text, str):
        return False

    response_lower = response_text.lower()
    return any(re.search(p, response_lower) for p in EXTERNAL_CLAIM_PATTERNS)


if __name__ == "__main__":
    import sys

    # Self-test for EXTERNAL_CLAIM_PATTERNS
    print("EXTERNAL_CLAIM_PATTERNS Self-Test:")
    print("=" * 50)
    external_test_cases = [
        ("I did not use TDD for this change", False),
        ("I only ran py_compile, not pytest", False),
        ("Both files have been updated. Here's a summary.", False),
        ("The fix works. Tests passed.", True),
        ("Tests passed. Hook returns {'ok': true}", True),
        ("File is at C:\\path\\to\\file.py", True),
        ("Bug is in line 42", True),
    ]

    external_passed = 0
    external_failed = 0
    for test, expected in external_test_cases:
        result = has_external_claim(test)
        status = "PASS" if result == expected else "FAIL"
        if result == expected:
            external_passed += 1
        else:
            external_failed += 1
        print(f"{status}: {test[:60]}")
        print(f"  Expected: {expected}, Got: {result}")

    print(f"\nExternal claims: {external_passed} passed, {external_failed} failed")

    # Self-test for ACTION_CLAIM_PATTERNS (fabrication detection)
    print("\n" + "=" * 50)
    print("ACTION_CLAIM_PATTERNS Self-Test (Fabrication Detection):")
    print("=" * 50)
    action_test_cases = [
        # Fabrication claims (should return True)
        ("I tried WebSearch but got 429 error", True),
        ("External research was blocked by API quota", True),
        ("I searched but found nothing", True),
        ("I ran pytest and all tests passed", True),
        ("I just verified the fix works", True),
        ("attempted to search for the pattern", True),
        ("search returned nothing useful", True),
        # Tentative language (should return False - not fabrication)
        ("I would need to search for X", False),
        ("We should check if Y exists", False),
        ("I might search for the pattern", False),
        ("We could try fetching the data", False),
        # Process/self-report (should return False - not fabrication)
        ("I did not use TDD for this change", False),
        ("I only ran py_compile, not pytest", False),
        ("Both files have been updated. Here's a summary.", False),
    ]

    action_passed = 0
    action_failed = 0
    for test, expected in action_test_cases:
        result = has_action_claim(test)
        status = "PASS" if result == expected else "FAIL"
        if result == expected:
            action_passed += 1
        else:
            action_failed += 1
        print(f"{status}: {test[:60]}")
        print(f"  Expected: {expected}, Got: {result}")

    print(f"\nAction claims: {action_passed} passed, {action_failed} failed")

    # Self-test for BEHAVIORAL_ASSERTION_PATTERNS
    print("\n" + "=" * 50)
    print("BEHAVIORAL_ASSERTION_PATTERNS Self-Test:")
    print("=" * 50)
    behavioral_test_cases = [
        # Behavioral assertions (should return True)
        ("This is enforced structurally by the SKILL EVALUATION REQUIRED protocol", True),
        ("Every skill invocation triggers mandatory evaluation of all available skills", True),
        ("The system always blocks on error", True),
        ("It's a hard requirement that skills are evaluated", True),
        ("This is a hard requirement", True),
        ("The hook must structurally enforce this", True),
        # Tentative language (should return False - hedging cancels)
        ("This may be enforced structurally", False),
        ("This might trigger a mandatory evaluation", False),
        ("This could be a hard requirement", False),
        ("This should be structurally enforced", False),
        ("It appears to be enforced structurally", False),
        # Rhetorical reversal (should return False)
        ("This is enforced structurally? No it's not", False),
        ("This is a hard requirement? Not exactly", False),
        # Normal statements (should return False)
        ("I verified the system always blocks on error", False),
        ("The system blocks on error when I tested it", False),
    ]

    behavioral_passed = 0
    behavioral_failed = 0
    for test, expected in behavioral_test_cases:
        result = has_action_claim(test)  # behavioral assertions flow through has_action_claim
        status = "PASS" if result == expected else "FAIL"
        if result == expected:
            behavioral_passed += 1
        else:
            behavioral_failed += 1
        print(f"{status}: {test[:60]}")
        print(f"  Expected: {expected}, Got: {result}")

    print(f"\nBehavioral assertions: {behavioral_passed} passed, {behavioral_failed} failed")

    # Self-test for DOCUMENT_CLAIM_PATTERNS (source fabrication detection)
    print("\n" + "=" * 50)
    print("DOCUMENT_CLAIM_PATTERNS Self-Test (Source Fabrication):")
    print("=" * 50)
    document_test_cases = [
        # Document claims (should return True)
        ("the document says the fix is at line 42", True),
        ("according to the file, the issue is caused by X", True),
        ("I read in the document that it supports Y", True),
        ("the document contains the following", True),
        ("in the file, it states that", True),
        ("the file confirms this approach", True),
        ("as stated in the document, the default is", True),
        # Tentative language (should return False - not fabrication)
        ("the document might say X", False),
        ("if the document says X, then", False),
        ("the document could contain this", False),
        ("unless the file says otherwise", False),
        # Process statements (should return False)
        ("I read the file and understood it", False),
        ("I reviewed the document", False),
    ]

    doc_passed = 0
    doc_failed = 0
    for test, expected in document_test_cases:
        result = has_document_claim(test)
        status = "PASS" if result == expected else "FAIL"
        if result == expected:
            doc_passed += 1
        else:
            doc_failed += 1
        print(f"{status}: {test[:60]}")
        print(f"  Expected: {expected}, Got: {result}")

    print(f"\nDocument claims: {doc_passed} passed, {doc_failed} failed")

    # Overall result
    total_passed = external_passed + action_passed + behavioral_passed + doc_passed
    total_failed = external_failed + action_failed + behavioral_failed + doc_failed
    print("\n" + "=" * 50)
    print(f"TOTAL: {total_passed} passed, {total_failed} failed")

    if total_failed == 0:
        print("\nAll tests passed!")
        sys.exit(0)
    else:
        print(f"\n{total_failed} test(s) failed!")
        sys.exit(1)
