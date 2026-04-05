#!/usr/bin/env python3
"""
Test CWO12 + Ralph Loop integration.

Verifies that CWO12 workflows automatically trigger Ralph Loop with TDD.
"""

import sys
import importlib.util
from pathlib import Path

# Load setup-ralph-loop.py (hyphens in filename require importlib)
script_path = Path(__file__).parent.parent / "scripts" / "setup-ralph-loop.py"
spec = importlib.util.spec_from_file_location("setup_ralph_loop", script_path)
setup_module = importlib.util.module_from_spec(spec)
sys.modules['setup_ralph_loop'] = setup_module
spec.loader.exec_module(setup_module)

assess_task = setup_module.assess_task
ALWAYS_TEST_PATTERNS = setup_module.ALWAYS_TEST_PATTERNS


def test_cwo12_pattern_exists():
    """Verify CWO12 pattern is defined in ALWAYS_TEST_PATTERNS."""
    assert "cwo12" in ALWAYS_TEST_PATTERNS, "CWO12 pattern missing from ALWAYS_TEST_PATTERNS"
    print("✅ CWO12 pattern exists in ALWAYS_TEST_PATTERNS")


def test_cwo12_keywords():
    """Verify CWO12 keywords cover common invocations."""
    cwo12 = ALWAYS_TEST_PATTERNS["cwo12"]
    keywords = cwo12["keywords"]

    expected_keywords = ["cwo12", "/cwo12", "/cwo", "cwo", "16-step", "16 step", "cwo12 workflow"]
    for kw in expected_keywords:
        assert kw in keywords, f"Expected keyword '{kw}' not found"

    print(f"✅ CWO12 keywords correct: {keywords}")


def test_cwo12_settings():
    """Verify CWO12 has appropriate settings."""
    cwo12 = ALWAYS_TEST_PATTERNS["cwo12"]

    assert cwo12["suggested_iterations"] == 20, f"Expected 20 iterations, got {cwo12['suggested_iterations']}"
    assert cwo12["auto_promise"] == "CWO12_ALL_16_STEPS_COMPLETED", f"Wrong promise: {cwo12['auto_promise']}"

    print(f"✅ CWO12 settings: iterations={cwo12['suggested_iterations']}, promise={cwo12['auto_promise']}")


def test_cwo12_assessment():
    """Test that various CWO12 prompts are detected correctly."""
    test_prompts = [
        "/cwo12 Build REST API",
        "/cwo Implement feature",
        "cwo12 workflow for authentication",
        "Use 16-step CWO12 process",
        "Run cwo12 for this project",
    ]

    for prompt in test_prompts:
        result = assess_task(prompt)
        assert result["test_required"] is True, f"Expected test_required=True for '{prompt}'"
        assert result["suggested_iterations"] == 20, f"Expected 20 iterations for '{prompt}'"
        assert result["completion_promise"] == "CWO12_ALL_16_STEPS_COMPLETED", f"Wrong promise for '{prompt}'"
        assert result["warning"] is None, f"Unexpected warning for '{prompt}'"
        print(f"  ✅ '{prompt[:40]}...' → TDD=ON, iter=20, promise=CWO12_ALL_16_STEPS_COMPLETED")


def test_cwo12_has_tdd_priority():
    """Verify CWO12 is checked before generic patterns."""
    # CWO12 should be detected even if it also matches "feature" pattern
    result = assess_task("/cwo12 Implement feature")
    assert result["completion_promise"] == "CWO12_ALL_16_STEPS_COMPLETED", \
        "CWO12 promise should override generic feature promise"
    print("✅ CWO12 pattern takes priority over generic patterns")


def test_non_cwo12_still_works():
    """Verify non-CWO12 prompts still use default TDD behavior."""
    result = assess_task("Fix the auth bug")
    assert result["test_required"] is True, "Bug fix should still require tests"
    assert result["completion_promise"] == "BUG_FIXED", "Bug fix should use BUG_FIXED promise"
    print("✅ Non-CWO12 prompts still work correctly")


def main():
    """Run all tests."""
    print("Testing CWO12 + Ralph Loop Integration\n")
    print("=" * 60)

    tests = [
        test_cwo12_pattern_exists,
        test_cwo12_keywords,
        test_cwo12_settings,
        test_cwo12_assessment,
        test_cwo12_has_tdd_priority,
        test_non_cwo12_still_works,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: Unexpected error: {e}")
            failed += 1

    print("=" * 60)
    print(f"\nResults: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
