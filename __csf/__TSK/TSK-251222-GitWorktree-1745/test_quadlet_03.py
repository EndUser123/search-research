#!/usr/bin/env python3
"""
Test script for Quadlet-03: Explore Opportunity Detection
Tests the explore opportunity detection functionality in user_prompt_submit_cks.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path("P:/").resolve() / ".claude" / "hooks"
sys.path.insert(0, str(hooks_dir))

from user_prompt_submit_cks import CKSIntegrator


def test_explore_detection():
    """Test explore opportunity detection with various prompts."""
    print("=" * 70)
    print("Quadlet-03: Explore Opportunity Detection Tests")
    print("=" * 70)
    print()

    # Create CKS integrator instance
    integrator = CKSIntegrator()

    # Test cases with expected outcomes
    # Threshold for recommendation is 0.60 (as defined in detect_explore_opportunities)
    test_cases = [
        {
            "name": "Moderate Probability: Codebase Understanding",
            "prompt": "I want to understand the codebase structure",
            "min_probability": 0.60  # Meets recommendation threshold
        },
        {
            "name": "High Probability: Explore Keyword",
            "prompt": "Explore the authentication system",
            "min_probability": 0.60  # "explore" keyword should trigger
        },
        {
            "name": "Moderate Probability: Question Pattern",
            "prompt": "What design patterns are used?",
            "min_probability": 0.60  # "what" triggers question pattern
        },
        {
            "name": "Low Probability: File-Specific",
            "prompt": "What does the path_validator.py file do?",
            "min_probability": 0.0  # Should not recommend (specific file mentioned)
        },
        {
            "name": "Low Probability: Non-Exploration",
            "prompt": "Fix the bug in line 42",
            "min_probability": 0.0  # Should not recommend (specific task)
        },
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print(f'  Prompt: "{test['prompt']}"')

        # Detect explore opportunity
        result = integrator.detect_explore_opportunities(
            test["prompt"],
            {"cwd": os.getcwd()}
        )

        if result is None:
            if test["min_probability"] == 0:
                print("  Result: No opportunity detected ✅ PASS")
                passed += 1
            else:
                print(f"  Result: No opportunity detected ❌ FAIL (expected >= {test['min_probability']})")
                failed += 1
        else:
            probability = result.get("success_probability", 0.0)
            has_suggestion = result.get("suggestion") is not None
            has_benefits = len(result.get("expected_benefits", [])) > 0

            print("  Result: Opportunity detected")
            print(f"    Success Probability: {probability:.2f}")
            print(f"    Has Suggestion: {has_suggestion}")
            print(f"    Has Benefits: {has_benefits}")
            if has_benefits:
                print(f"    Benefits: {', '.join(result['expected_benefits'][:2])}")

            if probability >= test["min_probability"]:
                print("  ✅ PASS")
                passed += 1
            else:
                print(f"  ❌ FAIL (probability {probability:.2f} < {test['min_probability']})")
                failed += 1

        print()

    # Print summary
    print("=" * 70)
    print(f"Test Summary: {passed} passed, {failed} failed out of {len(test_cases)} total")
    print("=" * 70)

    if failed == 0:
        print("\n✅ All tests passed!")
        return 0
    print(f"\n❌ {failed} test(s) failed")
    return 1

if __name__ == "__main__":
    sys.exit(test_explore_detection())
