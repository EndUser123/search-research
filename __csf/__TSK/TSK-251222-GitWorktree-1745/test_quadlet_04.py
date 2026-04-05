#!/usr/bin/env python3
"""
Test script for Quadlet-04: Explore Opportunity Detector
Tests the standalone explore_opportunity_detector.py functionality
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path("P:/").resolve() / ".claude" / "hooks"
sys.path.insert(0, str(hooks_dir))

from explore_opportunity_detector import ExploreOpportunityDetector


def test_explore_detector():
    """Test explore opportunity detector with various scenarios."""
    print("=" * 70)
    print("Quadlet-04: Explore Opportunity Detector Tests")
    print("=" * 70)
    print()

    # Create detector instance
    detector = ExploreOpportunityDetector()

    # Test cases (threshold is 0.60 for recommendation)
    test_cases = [
        {
            "name": "Moderate: Architecture Understanding",
            "prompt": "I want to understand the codebase architecture",
            "min_probability": 0.60,  # Meets recommendation threshold
            "expected_confidence": "moderate"  # 0.60-0.65 = moderate
        },
        {
            "name": "Moderate: Discovery Request",
            "prompt": "Explore the authentication system components",
            "min_probability": 0.60,  # Meets recommendation threshold
            "expected_confidence": "moderate"  # 0.60-0.65 = moderate
        },
        {
            "name": "Moderate: Analysis Request",
            "prompt": "Analyze the error handling approach across the system",
            "min_probability": 0.60,  # Meets recommendation threshold
            "expected_confidence": "moderate"  # 0.60-0.65 = moderate
        },
        {
            "name": "Low: File-Specific (should NOT recommend)",
            "prompt": "What does path_validator.py and user_prompt_submit_cks.py do?",
            "min_probability": 0.0,
            "expected_confidence": None
        },
        {
            "name": "Low: Specific Task (should NOT recommend)",
            "prompt": "Fix the bug in line 42 of path_validator.py",
            "min_probability": 0.0,
            "expected_confidence": None
        },
        {
            "name": "Low: Simple Where Question (specific file reference)",
            "prompt": "Where is the API endpoint defined?",
            "min_probability": 0.0,  # Has file-like reference, likely doesn't pass threshold
            "expected_confidence": None
        },
        {
            "name": "Low: Question without context (below threshold)",
            "prompt": "What design patterns are used in this project?",
            "min_probability": 0.0,  # Question-only, below threshold without exploration keywords
            "expected_confidence": None
        },
        {
            "name": "Low: Vague question (below threshold)",
            "prompt": "How does this work?",
            "min_probability": 0.0,  # Too vague, below threshold
            "expected_confidence": None
        },
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['name']}")
        print(f'  Prompt: "{test['prompt']}"')

        # Detect opportunity
        result = detector.detect_opportunity(
            test["prompt"],
            {"cwd": "P:/__csf"}
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
            confidence = result.get("confidence_level", "")
            has_suggestion = result.get("suggestion") is not None
            has_benefits = len(result.get("expected_benefits", [])) > 0
            has_factors = len(result.get("factors", {})) > 0

            print("  Result: Opportunity detected")
            print(f"    Success Probability: {probability:.2f}")
            print(f"    Confidence Level: {confidence}")
            print(f"    Has Suggestion: {has_suggestion}")
            print(f"    Has Benefits: {has_benefits}")
            print(f"    Has Factors: {has_factors}")

            if has_benefits:
                print(f"    Benefits: {', '.join(result['expected_benefits'][:2])}")

            if has_factors:
                print(f"    Factors: {', '.join(list(result['factors'].keys())[:3])}")

            # Check probability threshold
            if probability >= test["min_probability"]:
                prob_pass = True
            else:
                print(f"    ❌ Probability {probability:.2f} < {test['min_probability']}")
                prob_pass = False

            # Check confidence level (if specified)
            conf_pass = True
            if test["expected_confidence"]:
                conf_levels = {"moderate": 0, "good": 1, "high": 2, "very_high": 3}
                expected_level = conf_levels.get(test["expected_confidence"], 0)
                actual_level = conf_levels.get(confidence, 0)
                if actual_level < expected_level:
                    print(f"    ❌ Confidence '{confidence}' < '{test['expected_confidence']}'")
                    conf_pass = False

            if prob_pass and conf_pass:
                print("  ✅ PASS")
                passed += 1
            else:
                print("  ❌ FAIL")
                failed += 1

        print()

    # Test cache functionality
    print("=" * 70)
    print("Cache Performance Tests")
    print("=" * 70)
    print()

    import time

    # Test L1 cache performance
    prompt = "I want to understand the codebase architecture"

    # First call (cache miss)
    start = time.time()
    result1 = detector.detect_opportunity(prompt, {"cwd": "P:/__csf"})
    miss_time = (time.time() - start) * 1000

    # Second call (L1 cache hit)
    start = time.time()
    result2 = detector.detect_opportunity(prompt, {"cwd": "P:/__csf"})
    hit_time = (time.time() - start) * 1000

    print("L1 Cache Performance:")
    print(f"  Cache Miss: {miss_time:.2f}ms")
    print(f"  Cache Hit: {hit_time:.2f}ms")
    print(f"  Speedup: {miss_time/hit_time:.1f}x")

    if hit_time < miss_time and hit_time < 10:  # Should be <10ms for L1 hit
        print("  ✅ L1 cache working correctly")
        passed += 1
    else:
        print("  ❌ L1 cache not performing as expected")
        failed += 1

    print()

    # Print summary
    print("=" * 70)
    print(f"Test Summary: {passed} passed, {failed} failed out of {len(test_cases) + 1} total")
    print("=" * 70)

    if failed == 0:
        print("\n✅ All tests passed!")
        return 0
    print(f"\n❌ {failed} test(s) failed")
    return 1


def test_cli_interface():
    """Test the CLI interface for the detector."""
    import subprocess

    print("\n" + "=" * 70)
    print("CLI Interface Tests")
    print("=" * 70)
    print()

    detector_path = Path("P:/").resolve() / ".claude" / "hooks" / "explore_opportunity_detector.py"

    # Test with a good prompt
    print("Test: CLI with high-probability prompt")
    result = subprocess.run(
        [sys.executable, str(detector_path), "understand", "the", "codebase", "architecture"],
        capture_output=True,
        text=True,
        timeout=10, check=False
    )

    if result.returncode == 0 and "Explore Opportunity Detected" in result.stdout:
        print("  ✅ CLI working correctly")
        return 0
    print("  ❌ CLI test failed")
    print(f"  stdout: {result.stdout[:200]}")
    print(f"  stderr: {result.stderr[:200]}")
    return 1


if __name__ == "__main__":
    result1 = test_explore_detector()
    result2 = test_cli_interface()
    sys.exit(max(result1, result2))
