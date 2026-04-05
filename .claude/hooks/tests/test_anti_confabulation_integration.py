#!/usr/bin/env python3
"""
Integration tests for anti-confabulation hooks (Option B)

Tests that hooks actually work when invoked with realistic input:
1. investigate_before_explain.py - detects skill questions and injects SKILL.md read instruction
2. assumption_audit_v2.py verify_code_quotes() - correctly matches Read tool output content to quoted code

These tests would have caught the bugs we fixed:
- investigate_before_explain.py being registered but never invoked (dead hook)
- verify_code_quotes() checking if file PATH appears in quoted CODE (wrong) vs checking if Read OUTPUT matches quoted code (right)

Run with: pytest P:/.claude/hooks/tests/test_anti_confabulation_integration.py -v
"""

import sys

# Add hooks directory to path for imports
sys.path.insert(0, "P:/.claude/hooks")

# =============================================================================
# Test 1: investigate_before_explain.py Integration Test
# =============================================================================

def test_investigate_before_explain_skill_question_detection():
    """Test that investigate_before_explain detects skill questions correctly."""
    from investigate_before_explain import detect_skill_question

    # Test skill question pattern: "why didn't /skill do X?"
    test_cases = [
        ("why didn't /p6 do X?", "p6", "why_not"),
        ("how does /p work?", "p", "how_works"),
        ("what does /commit do?", "commit", "what_does"),
        ("is /rca supposed to Y?", "rca", "intended_behavior"),
        ("why didn't /analyze run?", "analyze", "why_not"),
    ]

    for prompt, expected_skill, question_type in test_cases:
        skill_name, detected = detect_skill_question(prompt)
        assert skill_name == expected_skill, (
            f"Failed to detect skill '{expected_skill}' in prompt: '{prompt}'"
        )
        assert detected == question_type, (
            f"Wrong question type for '{expected_skill}': expected {question_type}, got {detected}"
        )

    print("✅ investigate_before_explain skill question detection works correctly")


def test_investigate_before_explain_injection():
    """Test that investigate_before_explain generates correct injection."""
    from investigate_before_explain import process_prompt

    # Test 1: Skill question should generate injection
    data = {"prompt": "why didn't /p6 do X?"}
    result = process_prompt(data)

    assert "additionalContext" in result, (
        f"Missing additionalContext for skill question. Got: {list(result.keys())}"
    )
    assert "SKILL.md" in result["additionalContext"], (
        f"Injection should mention SKILL.md. Got: {result['additionalContext'][:100]}"
    )

    # Test 2: Non-skill question should not generate injection
    data = {"prompt": "how do I write a file?"}
    result = process_prompt(data)

    assert result == {} or "additionalContext" not in result, (
        f"Non-skill question should not generate injection. Got: {result}"
    )

    # Test 3: Injection for non-existent skill should still provide guidance
    data = {"prompt": "why didn't /nonexistent do X?"}
    result = process_prompt(data)

    assert "additionalContext" in result, (
        f"Should inject guidance for non-existent skill. Got: {result['additionalContext'][:100]}"
    )
    assert "search for the skill" in result["additionalContext"].lower(), (
        f"Should suggest searching for skill. Got: {result['additionalContext'][:100]}"
    )

    print("✅ investigate_before_explain injection logic works correctly")


# =============================================================================
# Test 2: assumption_audit_v2.py verify_code_quotes() Integration Test
# =============================================================================

def test_verify_code_quotes_with_real_read_output():
    """Test that verify_code_quotes correctly matches Read tool OUTPUT (not file paths)."""
    from assumption_audit_v2 import verify_code_quotes

    # Scenario 1: Code quote matches Read tool output (should PASS)
    # verify_code_quotes extracts code quotes from response_text internally
    response_with_matching_code = """Here is the code you asked for:

```python
def hello():
    print('world')
```
This function does what you requested."""

    # Simulate tool_sequence with Read tool that outputs this exact content
    tool_sequence = [
        {
            "name": "Read",
            "command": {"file_path": "test.py"},
            "response": {
                "content": "def hello():\n    print('world')\n",
                "error": None
            }
        }
    ]

    has_quotes, fabrications = verify_code_quotes(response_with_matching_code, tool_sequence)

    assert has_quotes, "verify_code_quotes should detect code quotes"
    assert len(fabrications) == 0, (
        f"Quote matching Read output should NOT be flagged as fabrication. Got fabrications: {fabrications}"
    )

    # Scenario 2: Code quote does NOT match Read tool output (should be fabrication)
    response_with_unmatched_code = """Here is a different function:

```python
def different():
    print('different')
```
This is not from the file we read."""

    has_quotes, fabrications = verify_code_quotes(response_with_unmatched_code, tool_sequence)

    assert has_quotes, "verify_code_quotes should detect code quotes"
    assert len(fabrications) == 1, (
        f"Unmatched quote should be flagged as fabrication. Got: {fabrications}"
    )

    # Scenario 3: Quote is very short (< 30 chars) - should be allowed without verification
    response_with_short_code = """Short code: `print('short')`"""

    has_quotes, fabrications = verify_code_quotes(response_with_short_code, tool_sequence)

    assert has_quotes, "Short quotes should be detected"
    assert len(fabrications) == 0, (
        f"Short quotes should be allowed. Got fabrications: {fabrications}"
    )

    # Scenario 4: Code with function definition but matching Read content (should PASS)
    response_with_func_def = """The function is:

```python
def hello():
    print('world')
```

This is from test.py"""

    has_quotes, fabrications = verify_code_quotes(response_with_func_def, tool_sequence)

    assert has_quotes, "Should detect code with function definition"
    assert len(fabrications) == 0, (
        f"Function definition matching Read output should NOT be fabrication. Got: {fabrications}"
    )

    print("✅ assumption_audit_v2 verify_code_quotes works correctly")


# =============================================================================
# Test 3: Verify hooks are properly registered in routers
# =============================================================================

def test_investigate_before_explain_registered_in_router():
    """Verify investigate_before_explain is properly registered."""
    # Import the router to check registration
    from UserPromptSubmit_router import HOOK_PRIORITY, HOOKS

    assert "investigate_before_explain" in HOOK_PRIORITY, (
        "investigate_before_explain not found in HOOK_PRIORITY. "
        "Ensure it was added during Fix #1."
    )

    assert "investigate_before_explain" in HOOKS, (
        "investigate_before_explain not found in HOOKS. "
        "Ensure run_investigate_before_explain function was added."
    )

    print("✅ investigate_before_explain is properly registered in router")


# =============================================================================
# Test Suite
# =============================================================================

def test_all():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("ANTI-CONFABULATION HOOK INTEGRATION TESTS")
    print("=" * 70)

    try:
        # investigate_before_explain.py tests
        print("\n[1] investigate_before_explain.py - Skill Question Detection")
        test_investigate_before_explain_skill_question_detection()
        print()
        print("[2] investigate_before_explain.py - Injection Generation")
        test_investigate_before_explain_injection()
        print()
        print("[3] investigate_before_explain.py - Router Registration")
        test_investigate_before_explain_registered_in_router()
        print()

        # assumption_audit_v2.py tests
        print("\n[4] assumption_audit_v2.py - verify_code_quotes() with Read Output")
        test_verify_code_quotes_with_real_read_output()
        print()

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED")
        print("=" * 70)
        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(test_all())
