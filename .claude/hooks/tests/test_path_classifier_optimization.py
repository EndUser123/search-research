#!/usr/bin/env python3
"""
Test Path Classifier Optimization

Verifies that the unified path classifier works correctly and provides the
expected performance and security improvements over the previous multi-hook
pattern matching approach.

Tests:
1. Path classification cache works correctly
2. Hook files require planning (security check)
3. Skill internal files are exempt
4. Test files are exempt
5. File existence is cached
"""

import sys
from pathlib import Path

# Add hooks __lib to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

from path_classifier import (
    classify_path,
    clear_cache,
    is_claude_internal,
    is_exempt_path,
    is_new_file,
    is_test_file,
    requires_planning,
)


def test_hook_files_require_planning():
    """Security test: Hook files should ALWAYS require planning."""
    print("Testing: Hook files require planning (security)")

    data = {}
    hook_files = [
        ".claude/hooks/PreToolUse_test.py",
        ".claude/hooks/TEST_CRITICAL_HOOK.py",
        ".claude/hooks/UserPromptSubmit.py",
    ]

    for hook_path in hook_files:
        result = requires_planning(hook_path, data)
        assert result is True, f"FAIL: {hook_path} should require planning"

        # Verify it's NOT exempt
        exempt = is_exempt_path(hook_path, data)
        assert exempt is False, f"FAIL: {hook_path} should NOT be exempt"

    print("  ✅ PASS: All hook files require planning")


def test_skill_internal_files_exempt():
    """Test: Skill internal files should be exempt from planning."""
    print("Testing: Skill internal files are exempt")

    data = {}
    skill_files = [
        ".claude/skills/plan-workflow/lib/validator.py",
        ".claude/skills/ask-cli/templates/prompt.txt",
        ".claude/skills/ask-cli/utils/helper.py",
    ]

    for skill_path in skill_files:
        result = requires_planning(skill_path, data)
        assert result is False, f"FAIL: {skill_path} should NOT require planning"

        # Verify it's marked as claude internal (not necessarily exempt)
        internal = is_claude_internal(skill_path, data)
        assert internal is True, f"FAIL: {skill_path} should be claude internal"

    print("  ✅ PASS: Skill internal files are exempt")


def test_test_files_exempt():
    """Test: Test files should be exempt from planning."""
    print("Testing: Test files are exempt")

    data = {}
    test_files = [
        "tests/test_validator.py",
        "test/helper_test.py",
        "tests/integration/test_api.py",
    ]

    for test_path in test_files:
        result = requires_planning(test_path, data)
        assert result is False, f"FAIL: {test_path} should NOT require planning"

        # Verify it's detected as test file
        is_test = is_test_file(test_path, data)
        assert is_test is True, f"FAIL: {test_path} should be detected as test"

    print("  ✅ PASS: Test files are exempt")


def test_config_files_exempt():
    """Test: Config files should be exempt from planning."""
    print("Testing: Config files are exempt")

    data = {}
    config_files = [
        "README.md",
        "config.json",
        ".env.example",
        "pyproject.toml",
    ]

    for config_path in config_files:
        result = requires_planning(config_path, data)
        assert result is False, f"FAIL: {config_path} should NOT require planning"

        exempt = is_exempt_path(config_path, data)
        assert exempt is True, f"FAIL: {config_path} should be exempt"

    print("  ✅ PASS: Config files are exempt")


def test_new_features_require_planning():
    """Test: New feature files should require planning."""
    print("Testing: New features require planning")

    data = {}
    feature_files = [
        "packages/new_feature/main.py",
        "src/module.py",
        "lib/new_library.py",
    ]

    for feature_path in feature_files:
        result = requires_planning(feature_path, data)
        assert result is True, f"FAIL: {feature_path} should require planning"

        # Verify it's NOT exempt
        exempt = is_exempt_path(feature_path, data)
        assert exempt is False, f"FAIL: {feature_path} should NOT be exempt"

    print("  ✅ PASS: New features require planning")


def test_cache_works():
    """Test: Classification cache should work correctly."""
    print("Testing: Classification cache")

    data = {}
    test_path = "packages/feature.py"

    # First classification
    cls1 = classify_path(test_path, data)
    assert cls1 is not None, "FAIL: First classification failed"

    # Verify cache hit
    cls2 = classify_path(test_path, data)
    assert cls1 is cls2, "FAIL: Cache not working, got different objects"

    # Clear cache
    clear_cache(data)

    # New classification after cache clear
    cls3 = classify_path(test_path, data)
    assert cls3 is not cls1, "FAIL: Cache not cleared"

    print("  ✅ PASS: Cache works correctly")


def test_file_not_exist_detection():
    """Test: File existence detection."""
    print("Testing: File existence detection")

    data = {}

    # Test with a file that definitely doesn't exist
    nonexistent = "test_file_that_does_not_exist_12345.txt"
    is_new = is_new_file(nonexistent, data)
    assert is_new is True, f"FAIL: {nonexistent} should be detected as new"

    print("  ✅ PASS: File existence detection works")


def run_all_tests():
    """Run all optimization tests."""
    print("=" * 60)
    print("Path Classifier Optimization Tests")
    print("=" * 60)
    print()

    tests = [
        test_hook_files_require_planning,
        test_skill_internal_files_exempt,
        test_test_files_exempt,
        test_config_files_exempt,
        test_new_features_require_planning,
        test_cache_works,
        test_file_not_exist_detection,
    ]

    failed = []
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"  ❌ FAILED: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"  ❌ ERROR: {test.__name__}: {e}")
            failed.append(test.__name__)

    print()
    print("=" * 60)
    if failed:
        print(f"FAILED: {len(failed)} test(s)")
        for name in failed:
            print(f"  - {name}")
        return 1
    else:
        print("SUCCESS: All tests passed! ✅")
        return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
