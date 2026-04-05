#!/usr/bin/env python
"""
Manual test script for proactive search injection.
Run this to verify the implementation works correctly.
"""

import sys
from unittest.mock import Mock, patch

# Add src to path
sys.path.insert(0, "P:/projects/yt-fts/src")

from yt_fts.lib.search.proactive_injection import (
    QueryIntentDetector,
    ProactiveSearchInjection,
)


def test_query_intent_detector():
    """Test QueryIntentDetector functionality."""
    print("Testing QueryIntentDetector...")
    detector = QueryIntentDetector()

    # Test search intent with question words
    tests = [
        ("What is machine learning?", "search"),
        ("How does neural network work?", "search"),
        ("Why do we use transformers?", "search"),
        ("hello", "chat"),
        ("thanks", "chat"),
        ("ok", "unknown"),
        ("maybe", "unknown"),
        ("", "unknown"),
    ]

    passed = 0
    failed = 0

    for query, expected_intent in tests:
        actual_intent = detector.detect(query)
        if actual_intent == expected_intent:
            passed += 1
            print(f"  ✓ '{query}' -> {actual_intent}")
        else:
            failed += 1
            print(f"  ✗ '{query}' -> expected {expected_intent}, got {actual_intent}")

    print(f"  Passed: {passed}/{passed + failed}")
    return failed == 0


def test_proactive_search_injection():
    """Test ProactiveSearchInjection functionality."""
    print("\nTesting ProactiveSearchInjection...")
    injector = ProactiveSearchInjection()

    # Test should_inject
    tests = [
        ("What is machine learning?", True),
        ("hello", False),
        ("ok", False),
        ("", False),
    ]

    passed = 0
    failed = 0

    for query, should_inject in tests:
        actual = injector.should_inject(query)
        if actual == should_inject:
            passed += 1
            print(f"  ✓ '{query}' should_inject={actual}")
        else:
            failed += 1
            print(f"  ✗ '{query}' expected should_inject={should_inject}, got {actual}")

    # Test format_for_llm
    print("\n  Testing format_for_llm...")
    mock_results = [
        {
            "video_id": "test123",
            "start_time": "00:01:23",
            "text": "Machine learning is a subset of artificial intelligence.",
            "channel_name": "TestChannel",
            "video_title": "Introduction to ML",
            "link": "https://youtu.be/test123?t=83",
        }
    ]

    formatted = injector.format_for_llm(mock_results)
    if "machine learning" in formatted.lower() and "TestChannel" in formatted:
        passed += 1
        print(f"  ✓ format_for_llm works correctly")
    else:
        failed += 1
        print(f"  ✗ format_for_llm failed")

    # Test format_for_llm with empty results
    formatted_empty = injector.format_for_llm([])
    if len(formatted_empty) > 0:
        passed += 1
        print(f"  ✓ format_for_llm handles empty results")
    else:
        failed += 1
        print(f"  ✗ format_for_llm doesn't handle empty results")

    print(f"  Passed: {passed}/{passed + failed}")
    return failed == 0


def test_search_execution():
    """Test search execution with mocking."""
    print("\nTesting search execution with mocks...")

    injector = ProactiveSearchInjection()

    # Create mock search handler
    mock_handler = Mock()
    mock_handler.res = [
        {
            "video_id": "test123",
            "start_time": "00:01:23",
            "text": "Machine learning is a subset of artificial intelligence.",
            "channel_name": "TestChannel",
            "video_title": "Introduction to ML",
            "link": "https://youtu.be/test123?t=83",
        }
    ]

    # Test with mocked SearchHandler
    with patch("yt_fts.core.search.SearchHandler", return_value=mock_handler):
        result = injector.execute_search("machine learning", scope="all", limit=5)

        if result["success"] and len(result["results"]) == 1:
            print(f"  ✓ execute_search works correctly")
            return True
        else:
            print(f"  ✗ execute_search failed")
            return False


def test_get_injection_context():
    """Test get_injection_context method."""
    print("\nTesting get_injection_context...")

    injector = ProactiveSearchInjection()

    # Test with search intent
    mock_handler = Mock()
    mock_handler.res = [
        {
            "video_id": "test123",
            "start_time": "00:01:23",
            "text": "Machine learning is a subset of artificial intelligence.",
            "channel_name": "TestChannel",
            "video_title": "Introduction to ML",
            "link": "https://youtu.be/test123?t=83",
        }
    ]

    with patch("yt_fts.core.search.SearchHandler", return_value=mock_handler):
        context = injector.get_injection_context("machine learning", scope="all")

        if (
            context["should_inject"]
            and context["intent"] == "search"
            and len(context["results"]) > 0
            and context["formatted_for_llm"] is not None
        ):
            print(f"  ✓ get_injection_context works correctly for search intent")
            success = True
        else:
            print(f"  ✗ get_injection_context failed for search intent")
            success = False

    # Test with chat intent (no search should be executed)
    context = injector.get_injection_context("hello", scope="all")

    if not context["should_inject"] and context["intent"] == "chat":
        print(f"  ✓ get_injection_context works correctly for chat intent")
    else:
        print(f"  ✗ get_injection_context failed for chat intent")
        success = False

    return success


def main():
    """Run all tests."""
    print("=" * 60)
    print("Proactive Search Injection - Manual Test Suite")
    print("=" * 60)

    all_passed = True

    all_passed &= test_query_intent_detector()
    all_passed &= test_proactive_search_injection()
    all_passed &= test_search_execution()
    all_passed &= test_get_injection_context()

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
