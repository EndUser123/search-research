#!/usr/bin/env python3
"""
claim_classifier.py - Claim classification and workload type detection

Centralizes claim classification for Stop-phase verification hooks:
- classify_claim_text(): Classify text into intent/meta/self_explanation/external_fact/other
- summarize_response_claim_kinds(): Holistic claim kind summary for full responses
- infer_workload_type(): Detect code vs docs vs mixed workload from touched paths

Purpose: Distinguish process/meta talk from external claims requiring verification.
"""

import re
from typing import Dict, Iterable, Literal

ClaimKind = Literal["intent", "meta", "self_explanation", "external_fact", "other"]
WorkloadType = Literal["code", "docs", "mixed", "unknown"]


# =============================================================================
# CLAIM CLASSIFICATION
# =============================================================================

def classify_claim_text(text: str) -> ClaimKind:
    """
    Classify short text snippets into claim kinds.

    Returns:
        - "intent": user goals/config ("I want the LLM to...", "We need to...")
        - "meta": process / discourse about work ("I did not use TDD", "I only ran py_compile")
        - "self_explanation": assistant explaining reasoning ("The reason I did that was...")
        - "external_fact": claims about code/system/files/tests ("The fix works", "All tests passed")
        - "other": everything else
    """
    if not isinstance(text, str) or not text.strip():
        return "other"

    lower = text.lower()

    # Intent patterns: user goals/config
    INTENT_PATTERNS = [
        r"\bi want (the )?llm to\b",
        r"\bwe need to\b",
        r"\bmy goal is\b",
        r"\bi prefer\b",
        r"\bplease make sure\b",
        r"\btreat .* as a hypothesis\b",
        r"\brespect my\b",
        # Research intent patterns - "I will search/check/look up/research"
        r"\bi will (search|check|look up|research)\b",
        r"\bi('m|am) going to (search|check|look up|research)\b",
    ]
    if any(re.search(p, lower) for p in INTENT_PATTERNS):
        return "intent"

    # Meta/process patterns: how work was done
    META_PATTERNS = [
        r"\bi did not use tdd\b",
        r"\bi only ran py_?compile\b",
        r"\bi (just )?edited\b",
        r"\bi created .*shared_helpers\.py\b",
        r"\bi modified (three|3|four|4|five|5) hooks?\b",
        r"\bi updated (the )?documentation\b",
        r"\bi (?:didn't|did not) (?:write|create) tests?\b",
        r"\bi added (?:a )?function\b",
    ]
    if any(re.search(p, lower) for p in META_PATTERNS):
        return "meta"

    # Self-explanation patterns: reasons for assistant behavior
    SELF_EXPLANATION_PATTERNS = [
        r"\bthe reason i\b",
        r"\bmy reasoning was\b",
        r"\bi did this because\b",
        r"\bi made that mistake because\b",
        r"\bi mis(?:read|understood|interpreted)\b",
        r"\bi (?:was|am) apologizing\b",
        r"\bi used (?:the |a )?\w+ (?:pattern|approach|method)\b",
    ]
    if any(re.search(p, lower) for p in SELF_EXPLANATION_PATTERNS):
        return "self_explanation"

    # External fact claim patterns: behavior / state of code/system/tests/files
    EXTERNAL_FACT_PATTERNS = [
        r"\bthe fix works\b",
        r"\bthis (?:change|fix) works\b",
        r"\ball tests? passed\b",
        r"\bpytest (?:passed|all green)\b",
        r"\bthe bug is (?:in|at) line \d+\b",
        r"\bfile (?:is )?(?:at|located|path)\b",
        r"\bthis resolves\b",
        r"\bthis should fix\b",
        r"\bhook returns?\b",
    ]
    if any(re.search(p, lower) for p in EXTERNAL_FACT_PATTERNS):
        return "external_fact"

    return "other"


def is_marked_as_hypothesis(text: str) -> bool:
    """
    Detect if text is explicitly marked as hypothetical / exploratory,
    not as a firm claim about the system.

    Examples:
        - "Possible gap: ..."
        - "Hypothesis: ..."
        - "Open question: ..."
        - "Needs verification: ..."
        - "To be confirmed: ..."

    Returns:
        True if explicitly marked as tentative/hypothetical
    """
    if not isinstance(text, str):
        return False

    lower = text.lower()

    PATTERNS = [
        r"\bpossible gap\b",
        r"\bneeds verification\b",
        r"\bhypothesis\b",
        r"\bopen question\b",
        r"\bto be confirmed\b",
    ]

    return any(re.search(p, lower) for p in PATTERNS)


def is_promoted_fact(text: str) -> bool:
    """
    Detect when language promotes something to a firm fact / judgment,
    often used for gaps, success, or conclusions.

    Examples:
        - "there is a real gap"
        - "this is definitely missing"
        - "the bug is now fixed"
        - "the fix works"
        - "this is already handled"
        - "this is pre-existing"

    This is intentionally broad and used as a signal, not a gate by itself.
    """
    if not isinstance(text, str):
        return False

    lower = text.lower()

    PATTERNS = [
        r"\bthere is (a|no) (real )?gap\b",
        r"\bthis (is|was) (definitely|clearly)\b",
        r"\b(the )?bug is (now )?fixed\b",
        r"\bthe fix (now )?works\b",
        r"\bsuccessfully (implemented|fixed|resolved)\b",
        r"\bthe fix (now )?works\b",
        r"\balready handled\b",
        r"\bpre[- ]existing\b",
        r"\balready (covered|addressed)\b",
        r"\bthere is no issue\b",
    ]

    return any(re.search(p, lower) for p in PATTERNS)


def is_test_report_context(text: str) -> bool:
    """
    Detect if text is part of a test/coverage report where classification
    language (e.g. "pre-existing gaps") is factual reporting, not blame.

    Returns True if the text contains strong test-report indicators.
    """
    if not isinstance(text, str):
        return False

    lower = text.lower()

    # Structural markers of test/coverage reports
    TEST_REPORT_MARKERS = [
        r"\bcoverage\b.*\b\d+%\b",           # "coverage ... 16%"
        r"\bpassed\b.*\bfailed\b",            # "4 passed, 2 failed"
        r"\b\d+/\d+\s+passed\b",             # "6/10 passed"
        r"\btest\s+health\s+check\b",         # "Test Health Check"
        r"\btest\s+coverage\s+report\b",       # "Test Coverage Report"
        r"\bgaps?\s+identified\b",             # "Gaps Identified"
        r"\bpriority\s+\d+\s*[-–:]\s*\w",    # "Priority 1 - ..."
        r"[✅❌⚠️]\s+\w",                     # emoji-prefixed test lines
    ]

    return sum(1 for p in TEST_REPORT_MARKERS if re.search(p, lower)) >= 2


def mentions_history_or_blame(text: str) -> bool:
    """
    Detect when text talks about history/blame rather than current state.

    Examples:
        - "pre-existing"
        - "introduced by this change"
        - "unrelated to my edits"
        - "the tool is wrong / blaming my changes"
    """
    if not isinstance(text, str):
        return False

    lower = text.lower()

    PATTERNS = [
        r"\bpre[- ]existing\b",
        r"\bintroduced by (this|my) change\b",
        r"\bunrelated to (my|these) (changes|edits)\b",
        r"\b(?:unrelated|not related) to my (changes|edits)\b",
        r"\bthe tool is wrong\b",
        r"\bthe tool is incorrectly blaming\b",
        r"\bblaming my (edits|changes)\b",
    ]

    return any(re.search(p, lower) for p in PATTERNS)


def summarize_response_claim_kinds(response_text: str) -> Dict[str, bool]:
    """
    Summarize claim kinds present in a full assistant response.

    Returns flags like:
    {
        "has_intent": bool,
        "has_meta": bool,
        "has_self_explanation": bool,
        "has_external_fact": bool,
    }
    """
    if not isinstance(response_text, str) or not response_text.strip():
        return {
            "has_intent": False,
            "has_meta": False,
            "has_self_explanation": False,
            "has_external_fact": False,
        }

    # Simple line/sentence split to keep it cheap
    segments = re.split(r"[.\n]", response_text)
    kinds = set(classify_claim_text(seg) for seg in segments if seg.strip())

    return {
        "has_intent": "intent" in kinds,
        "has_meta": "meta" in kinds,
        "has_self_explanation": "self_explanation" in kinds,
        "has_external_fact": "external_fact" in kinds,
    }


# =============================================================================
# WORKLOAD TYPE CLASSIFICATION
# =============================================================================

def infer_workload_type(touched_paths: Iterable[str]) -> WorkloadType:
    """
    Infer if the last turn primarily touched code, docs, or both.

    Intended to be fed by PostToolUse logs of file writes.

    Returns:
        - "code": Only code files were touched
        - "docs": Only documentation files were touched
        - "mixed": Both code and docs were touched
        - "unknown": No files were touched or unrecognized types
    """
    has_code = False
    has_docs = False

    for p in touched_paths or []:
        lower = str(p).lower()
        if lower.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".cs", ".java", ".go", ".rs", ".rb")):
            has_code = True
        elif lower.endswith((".md", ".rst", ".txt", ".adoc")):
            has_docs = True
        # YAML/JSON can be either config or docs - count as docs for softening
        elif lower.endswith((".yml", ".yaml", ".json")):
            has_docs = True

    if has_code and has_docs:
        return "mixed"
    if has_code:
        return "code"
    if has_docs:
        return "docs"
    return "unknown"


# =============================================================================
# BLOCK PAYLOAD BUILDER (Observability)
# =============================================================================

def make_block_payload(
    reason: str,
    data: dict,
    flags: dict,
    hook_name: str = "unknown_hook"
) -> dict:
    """
    Create standardized block payload with observability metadata.

    Includes:
    - Hook name
    - Claim kind that triggered enforcement
    - Workload type
    - Concrete next action hint
    """
    workload_type = data.get("workload_type", "unknown")

    return {
        "decision": "block",
        "reason": reason,
        "hook": hook_name,
        "workload_type": workload_type,
        "claim_kinds": {
            "has_external_fact": bool(flags.get("has_external_fact")),
            "has_meta": bool(flags.get("has_meta")),
            "has_self_explanation": bool(flags.get("has_self_explanation")),
        },
        "next_action_hint": (
            "Provide test output or tool logs for your external correctness claim."
            if flags.get("has_external_fact")
            else "Clarify whether this is a goal/intent or a factual claim about code/system."
        ),
    }


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == "__main__":
    # Test claim classification
    claim_tests = [
        ("I want the LLM to push back when I'm wrong.", "intent"),
        ("I did not use TDD for this change.", "meta"),
        ("The reason I did that was to avoid the import error.", "self_explanation"),
        ("The fix works. All tests passed.", "external_fact"),
        ("Hello world", "other"),
        ("I only ran py_compile, not pytest.", "meta"),
        ("File is at C:\\path\\to\\file.py", "external_fact"),
    ]

    print("Claim Classification Self-Test:")
    print("=" * 60)
    for text, expected in claim_tests:
        result = classify_claim_text(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status}: '{text[:50]}'")
        print(f"  Expected: {expected}, Got: {result}")

    # Test workload classification
    workload_tests = [
        (["file.py"], "code"),
        (["README.md"], "docs"),
        (["file.py", "README.md"], "mixed"),
        ([], "unknown"),
        (["script.ts", "component.tsx"], "code"),
        (["docs.md", "config.json"], "docs"),
    ]

    print("\nWorkload Classification Self-Test:")
    print("=" * 60)
    for paths, expected in workload_tests:
        result = infer_workload_type(paths)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status}: {paths}")
        print(f"  Expected: {expected}, Got: {result}")
