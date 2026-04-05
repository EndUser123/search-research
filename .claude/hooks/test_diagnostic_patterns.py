#!/usr/bin/env python3
"""Test diagnostic question patterns against real user queries."""

from __future__ import annotations

import re

# Current pattern (too broad - catches meta-questions)
CURRENT_PATTERN = r"\b(?:why\s+(?:is|does|did|are|was|were|do|doesn't|isn't|aren't|won't|can't))"

# Proposed positive pattern (more specific - targets system state questions)
# Refined v2: include "your" when followed by system-state words
POSITIVE_PATTERN = r"\bwhy\s+(?:is|did|does)\s+(?:the|this|that|my|your)\s+(?:file|code|hook|test|function|class|system|config|daemon|service|api)"

# Two-tier approach: broad pattern + meta-question exclusion
TWO_TIER_BROAD = r"\bwhy\s+(?:is|did|does|are)"
TWO_TIER_META_EXCLUDE = r"\b(?:you|your|said|say|claim|output|response|trigger)"

# Test corpus: real user questions with expected classification
TEST_CASES = [
    # (question, should_trigger, description)
    ("why is the file broken", True, "legitimate diagnostic - system state"),
    ("why did the hook fail", True, "legitimate diagnostic - hook behavior"),
    ("why does this test fail", True, "legitimate diagnostic - test failure"),
    ("why did you say that", False, "meta-question - about my output"),
    ("why is your code broken", True, "legitimate diagnostic - system state (contains 'your')"),
    ("why is this happening", False, "ambiguous - could be meta or system"),
    ("why did this happen", False, "ambiguous - could be meta or system"),
    ("why does the daemon crash", True, "legitimate diagnostic - daemon behavior"),
    ("why is my config wrong", True, "legitimate diagnostic - config issue"),
    ("why are you triggering this", False, "meta-question - about hook behavior"),
    ("why does my function return None", True, "legitimate diagnostic - code behavior"),
    ("why is the test failing on line 42", True, "legitimate diagnostic - specific test"),
    ("why did you recommend X", False, "meta-question - about recommendation"),
]


def test_pattern(pattern: str, name: str) -> dict:
    """Test a pattern against all cases and return results."""
    regex = re.compile(pattern, re.IGNORECASE)
    results = {
        "name": name,
        "pattern": pattern,
        "true_positives": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "errors": [],
    }

    for question, should_trigger, description in TEST_CASES:
        matches = bool(regex.search(question))
        is_correct = matches == should_trigger

        if matches and should_trigger:
            results["true_positives"] += 1
        elif matches and not should_trigger:
            results["false_positives"] += 1
            results["errors"].append(f"FP: '{question}' - {description}")
        elif not matches and should_trigger:
            results["false_negatives"] += 1
            results["errors"].append(f"FN: '{question}' - {description}")

    return results


def test_two_tier() -> dict:
    """Test two-tier approach: broad pattern + meta-question exclusion."""
    broad_regex = re.compile(TWO_TIER_BROAD, re.IGNORECASE)
    meta_regex = re.compile(TWO_TIER_META_EXCLUDE, re.IGNORECASE)

    results = {
        "name": "Two-tier (broad + meta-exclude)",
        "pattern": f"{TWO_TIER_BROAD} + !({TWO_TIER_META_EXCLUDE})",
        "true_positives": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "errors": [],
    }

    for question, should_trigger, description in TEST_CASES:
        # Two-tier: matches broad AND doesn't match meta-exclude
        matches = broad_regex.search(question) and not meta_regex.search(question)
        matches = bool(matches)
        is_correct = matches == should_trigger

        if matches and should_trigger:
            results["true_positives"] += 1
        elif matches and not should_trigger:
            results["false_positives"] += 1
            results["errors"].append(f"FP: '{question}' - {description}")
        elif not matches and should_trigger:
            results["false_negatives"] += 1
            results["errors"].append(f"FN: '{question}' - {description}")

    return results


def main():
    print("=" * 80)
    print("Diagnostic Question Pattern Test Results")
    print("=" * 80)

    patterns = [
        (CURRENT_PATTERN, "Current (broad 'why')"),
        (POSITIVE_PATTERN, "Proposed positive"),
    ]

    all_results = []
    for pattern, name in patterns:
        result = test_pattern(pattern, name)
        all_results.append(result)

    # Add two-tier
    all_results.append(test_two_tier())

    # Print results
    for result in all_results:
        print(f"\n{result['name']}")
        print(f"Pattern: {result['pattern'][:60]}...")
        print(f"  True positives:  {result['true_positives']:2}")
        print(f"  False positives: {result['false_positives']:2}")
        print(f"  False negatives: {result['false_negatives']:2}")

        if result["errors"]:
            print("  Errors:")
            for error in result["errors"][:5]:  # Show first 5
                print(f"    - {error}")

    # Best pattern by accuracy
    best = min(all_results, key=lambda x: x["false_positives"] + x["false_negatives"])
    total_errors = best["false_positives"] + best["false_negatives"]

    print("\n" + "=" * 80)
    print(f"RECOMMENDATION: {best['name']}")
    print(f"Total errors: {total_errors}/{len(TEST_CASES)}")
    print("=" * 80)


if __name__ == "__main__":
    main()
