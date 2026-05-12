#!/usr/bin/env python3
"""Regression corpus for response intent classifier.

Tests the exact failure mode:
- Quoted/meta discussion should NOT trigger blocking
- Direct first-person commitment SHOULD trigger blocking
- Mixed quoted trigger + real commitment SHOULD trigger blocking
"""
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from __lib.response_intent import classify_response_intent, IntentClass, is_meta_or_quoted_context
from Stop_approval_gate import run as approval_run
from Stop_commit_gate import run as commit_run


def check(classifier_fn, text, gate_name, expected_intent, should_block, description):
    """Check a single test case."""
    result = classifier_fn(text, gate_name)
    result_intent = classify_response_intent(text, gate_name)
    passed = result_intent == expected_intent

    return {
        "description": description,
        "text": text[:80],
        "expected": expected_intent,
        "actual": result_intent,
        "passed": passed,
    }


def run_corpus():
    """Run all test cases and report."""
    results = []
    all_passed = True

    # === GROUP A: Should NOT block (GATE_DEBUG_META or NEUTRAL_ANALYSIS) ===

    a_cases = [
        # Quoted trigger phrases
        ('The phrase "Proceeding to implement now" triggered the gate.',
         IntentClass.GATE_DEBUG_META, "Quoted trigger phrase"),

        ('The phrase \'Proceeding to implement\' was detected.',
         IntentClass.GATE_DEBUG_META, "Single-quoted trigger"),

        ('Can you show me what text triggered the approval gate?',
         IntentClass.GATE_DEBUG_META, "Question about trigger"),

        ('I was blocked by IMPLEMENTATION WITHOUT APPROVAL.',
         IntentClass.GATE_DEBUG_META, "Block message discussion"),

        ('Stop hook feedback:\nIMPLEMENTATION WITHOUT APPROVAL',
         IntentClass.GATE_DEBUG_META, "Stop hook feedback text"),

        # Code blocks with triggers
        ('```\nProceeding to implement the fix\n```',
         IntentClass.GATE_DEBUG_META, "Code block with trigger"),

        # Markdown bullets with triggers
        ('- proceeding to implement\n- want me to implement',
         IntentClass.GATE_DEBUG_META, "Bullet list with triggers"),

        # Markdown quoted examples
        ('> proceeding to implement\n> want me to implement',
         IntentClass.GATE_DEBUG_META, "Blockquote with triggers"),

        # Discussion about command patterns
        ("The command 'git commit -m test' should be gated.",
         IntentClass.GATE_DEBUG_META, "Command pattern discussion"),

        # Long debugging responses
        ('I was blocked by IMPLEMENTATION WITHOUT APPROVAL when trying to respond. '
         'The trigger appears to be the phrase "Proceeding to implement". '
         'Here is what I see in the response: proceeding to implement. '
         'Can you show me what text triggered the gate?',
         IntentClass.GATE_DEBUG_META, "Long debugging response"),

        # Neutral analysis should pass through
        ('The architecture consists of three layers: auth, API, and data.',
         IntentClass.NEUTRAL_ANALYSIS, "Neutral architecture discussion"),

        ('This implements the specification correctly.',
         IntentClass.NEUTRAL_ANALYSIS, "Neutral implement usage"),
    ]

    for text, expected, desc in a_cases:
        result_intent = classify_response_intent(text, "approval")
        passed = result_intent == expected
        if not passed:
            all_passed = False
        results.append((passed, desc, expected, result_intent))

    # === GROUP B: Should block (IMPLEMENTATION_COMMITMENT or COMMIT_COMMITMENT) ===

    b_cases = [
        ('I will implement the fix now.',
         IntentClass.IMPLEMENTATION_COMMITMENT, "I will implement"),

        ('I will implement the changes.',
         IntentClass.IMPLEMENTATION_COMMITMENT, "I will implement (plural)"),

        ('Proceeding to implement the changes.',
         IntentClass.IMPLEMENTATION_COMMITMENT, "Proceeding to implement"),

        ('I am going to implement the solution now.',
         IntentClass.IMPLEMENTATION_COMMITMENT, "I am going to implement"),

        ('Let me implement the fix.',
         IntentClass.IMPLEMENTATION_COMMITMENT, "Let me implement"),

        ('I am implementing the changes now.',
         IntentClass.IMPLEMENTATION_COMMITMENT, "I am implementing"),

        ('I will commit these changes.',
         IntentClass.COMMIT_COMMITMENT, "I will commit"),

        ('I will push the branch now.',
         IntentClass.COMMIT_COMMITMENT, "I will push"),

        ('I am going to commit these changes.',
         IntentClass.COMMIT_COMMITMENT, "I am going to commit"),
    ]

    for text, expected, desc in b_cases:
        gate_name = "commit" if expected == IntentClass.COMMIT_COMMITMENT else "approval"
        result_intent = classify_response_intent(text, gate_name)
        passed = result_intent == expected
        if not passed:
            all_passed = False
        results.append((passed, desc, expected, result_intent))

    # === GROUP C: Mixed contexts ===

    c_cases = [
        # Quoted trigger PLUS real commitment outside quote
        ('The phrase "proceeding to implement" was in the text. Now I will implement the fix.',
         IntentClass.IMPLEMENTATION_COMMITMENT, "Quoted trigger + real commitment"),

        ('I was blocked on "proceeding to implement", but I will now implement the solution.',
         IntentClass.IMPLEMENTATION_COMMITMENT, "Block discussion + commitment"),

        ('The command "git commit" was gated, and I am now committing these changes.',
         IntentClass.COMMIT_COMMITMENT, "Quoted git commit + real commitment"),
    ]

    for text, expected, desc in c_cases:
        gate_name = "commit" if expected == IntentClass.COMMIT_COMMITMENT else "approval"
        result_intent = classify_response_intent(text, gate_name)
        passed = result_intent == expected
        if not passed:
            all_passed = False
        results.append((passed, desc, expected, result_intent))

    # === GROUP D: Completion reports (should NOT block) ===

    d_cases = [
        ('All tests passed. Implementation complete.',
         IntentClass.COMPLETION_REPORT, "Tests passed + complete"),

        ('Verification complete - all checks pass.',
         IntentClass.COMPLETION_REPORT, "Verification complete"),

        ('pytest output shows 42 passed.',
         IntentClass.COMPLETION_REPORT, "Pytest output report"),
    ]

    for text, expected, desc in d_cases:
        result_intent = classify_response_intent(text, "approval")
        passed = result_intent == expected
        if not passed:
            all_passed = False
        results.append((passed, desc, expected, result_intent))

    return results, all_passed


def main():
    results, all_passed = run_corpus()

    print("=" * 70)
    print("REGRESSION CORPUS RESULTS")
    print("=" * 70)

    passed_count = sum(1 for p, *_ in results if p)
    failed_count = len(results) - passed_count

    for passed, desc, expected, actual in results:
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {desc}")
        if not passed:
            print(f"       Expected: {expected}")
            print(f"       Actual:   {actual}")

    print()
    print(f"Results: {passed_count} passed, {failed_count} failed, {len(results)} total")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
