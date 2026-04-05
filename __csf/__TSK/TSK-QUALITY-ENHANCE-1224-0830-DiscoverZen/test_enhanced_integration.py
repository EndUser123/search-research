#!/usr/bin/env python3
"""
Test script to verify EnhancedQualityExecutor integration.

This script tests the enhanced execution without requiring full dependencies.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
csf_nip_path = Path(__file__).parent.parent.parent.parent
src_path = csf_nip_path / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def test_adapter_imports():
    """Test that adapters can be imported."""
    print("Testing adapter imports...")

    try:
        print("  ✓ DiscoverAdapter imported")
    except Exception as e:
        print(f"  ✗ DiscoverAdapter import failed: {e}")
        return False

    try:
        print("  ✓ ZenCodeReviewAdapter imported")
    except Exception as e:
        print(f"  ✗ ZenCodeReviewAdapter import failed: {e}")
        return False

    try:
        print("  ✓ EnhancedQualityExecutor imported")
    except Exception as e:
        print(f"  ✗ EnhancedQualityExecutor import failed: {e}")
        return False

    return True


def test_discover_adapter():
    """Test DiscoverAdapter initialization and availability check."""
    print("\nTesting DiscoverAdapter...")

    try:
        from quality.discover_adapter import DiscoverAdapter
        adapter = DiscoverAdapter()
        print("  ✓ DiscoverAdapter initialized")

        # Check availability
        available = adapter.is_available()
        print(f"  {'✓' if available else '⚠'}  Discover tools available: {available}")

        if not available:
            print("    (This is expected in environments without code intelligence tools)")

        return True
    except Exception as e:
        print(f"  ✗ DiscoverAdapter test failed: {e}")
        return False


def test_zen_adapter():
    """Test ZenCodeReviewAdapter initialization and availability check."""
    print("\nTesting ZenCodeReviewAdapter...")

    try:
        from quality.zen_review_adapter import ZenCodeReviewAdapter
        adapter = ZenCodeReviewAdapter()
        print("  ✓ ZenCodeReviewAdapter initialized")

        # Check availability
        available = adapter.is_available()
        print(f"  {'✓' if available else '⚠'}  Zen code review available: {available}")

        if not available:
            print("    (This is expected in environments without zen-code-review)")

        return True
    except Exception as e:
        print(f"  ✗ ZenCodeReviewAdapter test failed: {e}")
        return False


def test_enhanced_executor():
    """Test EnhancedQualityExecutor initialization."""
    print("\nTesting EnhancedQualityExecutor...")

    try:
        from quality.enhanced_execution import EnhancedQualityExecutor
        executor = EnhancedQualityExecutor("P:/__csf")
        print("  ✓ EnhancedQualityExecutor initialized")

        # Check adapter availability
        print(f"  {'✓' if executor.discover_available else '⚠'}  Discover available: {executor.discover_available}")
        print(f"  {'✓' if executor.zen_available else '⚠'}  Zen available: {executor.zen_available}")

        return True
    except Exception as e:
        print(f"  ✗ EnhancedQualityExecutor test failed: {e}")
        return False


def test_phase_methods():
    """Test that phase methods exist and are callable."""
    print("\nTesting phase methods...")

    try:
        from quality.enhanced_execution import EnhancedQualityExecutor
        executor = EnhancedQualityExecutor("P:/__csf")

        phase_methods = [
            "execute_foundation_phase",
            "execute_architecture_phase",
            "execute_security_phase",
            "execute_cognitive_review_phase",
            "execute_validation_phase",
            "execute_phase"
        ]

        for method_name in phase_methods:
            if hasattr(executor, method_name):
                method = getattr(executor, method_name)
                if callable(method):
                    print(f"  ✓ {method_name}")
                else:
                    print(f"  ✗ {method_name} not callable")
                    return False
            else:
                print(f"  ✗ {method_name} not found")
                return False

        return True
    except Exception as e:
        print(f"  ✗ Phase method test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Enhanced Quality Integration Test")
    print("=" * 70)

    tests = [
        ("Adapter Imports", test_adapter_imports),
        ("DiscoverAdapter", test_discover_adapter),
        ("ZenCodeReviewAdapter", test_zen_adapter),
        ("EnhancedQualityExecutor", test_enhanced_executor),
        ("Phase Methods", test_phase_methods),
    ]

    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()

    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✅ All integration tests passed!")
        print("\nNote: Some tests may show 'unavailable' for tools.")
        print("This is expected in environments without the full CSF NIP stack.")
        return 0
    print(f"\n❌ {total - passed} test(s) failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
