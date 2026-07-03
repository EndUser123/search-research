#!/usr/bin/env python3
"""Test CKS context injection hook functionality."""

import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

from UserPromptSubmit import registry
from UserPromptSubmit.base import HookContext


def test_trigger_detection():
    """Test that trigger phrases are detected."""
    test_cases = [
        ("we discussed this before", True),
        ("check cks for context", True),
        ("you keep making the same mistake", True),
        ("what's the weather today", False),
        ("create a new file", False),
    ]

    from UserPromptSubmit import cks_context

    for prompt, should_trigger in test_cases:
        result = cks_context._should_trigger_cks(prompt)
        assert result == should_trigger, f"Failed for: {prompt} (expected {should_trigger}, got {result})"
        print(f"✓ Trigger detection: '{prompt}' -> {result}")

    print("\n✓ All trigger detection tests passed")


def test_hook_execution():
    """Test that the hook executes without errors."""
    # Create a test context
    context = HookContext(
        prompt="we discussed this before",
        data={},
        session_id="test-session",
        terminal_id="test-terminal"
    )

    # Run the hook
    try:
        result = registry.HOOKS["cks_context"](context)
        print("✓ Hook executed successfully")
        print(f"✓ Result type: {type(result)}")
        print(f"✓ Is empty: {result.is_empty()}")
    except Exception as e:
        print(f"✗ Hook execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_cks_query():
    """Test CKS database query."""
    from UserPromptSubmit import cks_context

    try:
        results = cks_context._query_cks("memory", max_results=3)
        print("✓ CKS query executed successfully")
        print(f"✓ Found {len(results)} results")

        if results:
            print(f"✓ Sample result: {results[0].get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"✗ CKS query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_context_formatting():
    """Test CKS context formatting."""
    from UserPromptSubmit import cks_context

    mock_results = [
        {
            "id": 1,
            "type": "memory",
            "title": "Test Memory",
            "content": "This is a test memory entry with enough content to pass the filter.",
            "metadata": "{}"
        }
    ]

    try:
        formatted = cks_context._format_cks_context(mock_results, "test prompt")
        print("✓ Context formatted successfully")
        print(f"✓ Formatted length: {len(formatted)} characters")
        print(f"✓ Contains header: {'📚 Related Context' in formatted}")
    except Exception as e:
        print(f"✗ Context formatting failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    print("Testing CKS Context Injection Hook\n")
    print("=" * 60)

    print("\n1. Testing trigger phrase detection...")
    test_trigger_detection()

    print("\n2. Testing CKS database query...")
    test_cks_query()

    print("\n3. Testing context formatting...")
    test_context_formatting()

    print("\n4. Testing hook execution...")
    test_hook_execution()

    print("\n" + "=" * 60)
    print("✓ All tests completed")
