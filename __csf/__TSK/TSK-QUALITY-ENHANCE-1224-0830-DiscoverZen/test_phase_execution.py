#!/usr/bin/env python3
"""
Test enhanced quality phase execution on actual code.

This demonstrates the enhanced execution with discover and zen adapters.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def test_foundation_phase():
    """Test foundation phase with discover health check."""
    print("=" * 70)
    print("Testing Foundation Phase with Discover Health Check")
    print("=" * 70)

    from quality.enhanced_execution import EnhancedQualityExecutor

    executor = EnhancedQualityExecutor("P:/projects/yt-fts")
    results = executor.execute_foundation_phase()

    print(f"\nPhase: {results['phase']}")
    print(f"Discover Health: {'✓' if results.get('discover_health') else '✗'}")

    if results.get("discover_health"):
        health = results["discover_health"]
        summary = health.get("summary", {})
        print(f"  Available Tools: {summary.get('available', 0)}/{summary.get('total', 0)}")

        tools = health.get("tools", {})
        for tool_id, status in tools.items():
            available = "✓" if status.get("available") else "✗"
            print(f"  [{available}] {tool_id}")

    print(f"\nTool Status: {results.get('tool_status', {})}")
    return True


def test_architecture_phase():
    """Test architecture phase with discover pattern matching."""
    print("\n" + "=" * 70)
    print("Testing Architecture Phase with Discover Pattern Analysis")
    print("=" * 70)

    from quality.enhanced_execution import EnhancedQualityExecutor

    executor = EnhancedQualityExecutor("P:/projects/yt-fts")
    results = executor.execute_architecture_phase()

    print(f"\nPhase: {results['phase']}")
    print(f"Pattern Analysis: {'✓' if results.get('pattern_analysis') else '✗'}")

    if results.get("pattern_analysis"):
        patterns = results["pattern_analysis"]
        total_matches = patterns.get("total_matches", 0)
        total_patterns = patterns.get("total_patterns", 0)
        print(f"  Total Patterns: {total_patterns}")
        print(f"  Total Matches: {total_matches}")

        for pattern, count in patterns.items():
            if pattern not in ["total_matches", "total_patterns"]:
                if isinstance(count, int):
                    if count > 0:
                        print(f"  • {pattern}: {count} occurrences")
                elif isinstance(count, dict) and "error" in count:
                    print(f"  • {pattern}: ERROR")

    print(f"\nTool Status: {results.get('tool_status', {})}")
    return True


def test_security_phase():
    """Test security phase with discover + zen review."""
    print("\n" + "=" * 70)
    print("Testing Security Phase with Discover + Zen Review")
    print("=" * 70)

    from quality.enhanced_execution import EnhancedQualityExecutor

    executor = EnhancedQualityExecutor("P:/projects/yt-fts")
    results = executor.execute_security_phase()

    print(f"\nPhase: {results['phase']}")

    # Discover patterns
    if results.get("pattern_analysis"):
        patterns = results["pattern_analysis"]
        total_matches = patterns.get("total_matches", 0)
        print(f"Security Patterns: {total_matches} issues found")

        for pattern, count in patterns.items():
            if pattern not in ["total_matches", "total_patterns"]:
                if isinstance(count, int) and count > 0:
                    print(f"  • {pattern}: {count} occurrences")

    # Zen review
    if results.get("zen_review"):
        review = results["zen_review"]
        if review.get("success"):
            findings = review.get("findings", [])
            print("\nLLM Security Review: ✓ Completed")
            print(f"  Security Findings: {len(findings)} issues")
        else:
            print(f"\nLLM Security Review: ✗ {review.get('error', 'Unknown')}")

    print(f"\nTool Status: {results.get('tool_status', {})}")
    return True


def main():
    """Run all phase tests."""
    print("\n" + "=" * 70)
    print("Enhanced Quality Phase Execution Test")
    print("Target: P:/projects/yt-fts")
    print("=" * 70)

    tests = [
        ("Foundation Phase", test_foundation_phase),
        ("Architecture Phase", test_architecture_phase),
        ("Security Phase", test_security_phase),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} failed: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False

    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    passed_count = sum(1 for v in results.values() if v)
    print(f"\nTotal: {passed_count}/{len(results)} tests passed")

    if passed_count == len(results):
        print("\n✅ Enhanced quality execution is working!")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
