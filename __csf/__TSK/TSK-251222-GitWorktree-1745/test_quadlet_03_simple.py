#!/usr/bin/env python3
"""
Simple diagnostic test for Quadlet-03: Explore Opportunity Detection
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path("P:/").resolve() / ".claude" / "hooks"
sys.path.insert(0, str(hooks_dir))

from user_prompt_submit_cks import CKSIntegrator


def test_basic_functionality():
    """Test basic explore opportunity detection functionality."""
    print("=" * 70)
    print("Quadlet-03: Basic Explore Opportunity Detection Test")
    print("=" * 70)
    print()

    integrator = CKSIntegrator()

    # Test 1: High-confidence explore prompt
    print("Test 1: Explore keyword trigger")
    result = integrator.detect_explore_opportunities(
        "I want to understand the codebase structure",
        {"cwd": os.getcwd()}
    )
    if result and result.get("success_probability", 0) >= 0.6:
        print(f"  ✅ PASS - Opportunity detected with probability {result['success_probability']:.2f}")
        test1_pass = True
    else:
        print(f"  ❌ FAIL - Probability: {result['success_probability'] if result else 0:.2f}")
        test1_pass = False
    print()

    # Test 2: Should NOT recommend (file-specific)
    print("Test 2: File-specific prompt (should NOT recommend)")
    result = integrator.detect_explore_opportunities(
        "What does path_validator.py do?",
        {"cwd": os.getcwd()}
    )
    if result is None:
        print("  ✅ PASS - No opportunity detected (as expected)")
        test2_pass = True
    else:
        print(f"  ❌ FAIL - Unexpectedly detected opportunity with probability {result['success_probability']:.2f}")
        test2_pass = False
    print()

    # Test 3: Should NOT recommend (specific task)
    print("Test 3: Specific task (should NOT recommend)")
    result = integrator.detect_explore_opportunities(
        "Fix the bug in line 42",
        {"cwd": os.getcwd()}
    )
    if result is None:
        print("  ✅ PASS - No opportunity detected (as expected)")
        test3_pass = True
    else:
        print(f"  ❌ FAIL - Unexpectedly detected opportunity with probability {result['success_probability']:.2f}")
        test3_pass = False
    print()

    # Summary
    print("=" * 70)
    all_pass = test1_pass and test2_pass and test3_pass
    if all_pass:
        print("✅ All basic tests passed!")
        return 0
    print("❌ Some tests failed")
    return 1

if __name__ == "__main__":
    sys.exit(test_basic_functionality())
