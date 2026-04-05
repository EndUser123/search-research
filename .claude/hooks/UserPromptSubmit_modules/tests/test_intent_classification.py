#!/usr/bin/env python3
"""Tests for intent classification in unified_injector.py."""

import sys
from pathlib import Path

# Add hooks directory to path for imports
hooks_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(hooks_dir))

from UserPromptSubmit.unified_injector import (
    build_intent_injection,
    classify_intent,
)


def test_question_classification():
    """Simple questions should be classified as QUESTION."""
    questions = [
        "What does this function do?",
        "How do I fix this error?",
        "Why is the sky blue?",
        "Can you explain this code?",
        "What's the difference between X and Y?",
    ]
    for prompt in questions:
        result = classify_intent(prompt)
        assert result == "QUESTION", f"Expected QUESTION for '{prompt}', got {result}"
    print("✅ Question classification tests passed")


def test_correction_classification():
    """User pushback should be classified as CORRECTION."""
    corrections = [
        "I asked you to check the logs first",
        "You didn't do what I said",
        "That's not what I wanted",
        "I told you to use the other approach",
        "Did you check X like I told you?",
        "No, that's wrong - fix it properly",
    ]
    for prompt in corrections:
        result = classify_intent(prompt)
        assert result == "CORRECTION", f"Expected CORRECTION for '{prompt}', got {result}"
    print("✅ Correction classification tests passed")


def test_research_classification():
    """Investigation requests should be classified as RESEARCH."""
    research = [
        "Investigate why the API is slow",
        "Look into the memory leak issue",
        "Check how authentication works",
        "Explore the architecture of this module",
        "Research the best approach for X",
    ]
    for prompt in research:
        result = classify_intent(prompt)
        assert result == "RESEARCH", f"Expected RESEARCH for '{prompt}', got {result}"
    print("✅ Research classification tests passed")


def test_debug_classification():
    """Fix/debug requests should be classified as DEBUG."""
    debug = [
        "Fix the authentication bug",
        "Debug this failing test",
        "Troubleshoot the connection issue",
        "The build is broken - help",
        "This isn't working properly",
    ]
    for prompt in debug:
        result = classify_intent(prompt)
        assert result == "DEBUG", f"Expected DEBUG for '{prompt}', got {result}"
    print("✅ Debug classification tests passed")


def test_action_classification():
    """Direct commands should return None (ACTION, no injection)."""
    actions = [
        "Refactor this function",
        "Add error handling here",
        "Create a new test file",
        "/commit",
        "plan the implementation",
        "build the API endpoint",
    ]
    for prompt in actions:
        result = classify_intent(prompt)
        assert result is None, f"Expected None (ACTION) for '{prompt}', got {result}"
    print("✅ Action classification tests passed")


def test_intent_injection_building():
    """Test that intent injections have proper guidance."""
    question_injection = build_intent_injection("QUESTION")
    assert "Answer directly" in question_injection
    assert "Do not execute commands" in question_injection

    correction_injection = build_intent_injection("CORRECTION")
    assert "Follow their instruction" in correction_injection

    research_injection = build_intent_injection("RESEARCH")
    assert "gather information" in research_injection

    debug_injection = build_intent_injection("DEBUG")
    assert "identify the failure" in debug_injection

    none_injection = build_intent_injection(None)
    assert none_injection == ""

    print("✅ Intent injection building tests passed")


def test_question_vs_command_distinction():
    """Questions ending in '?' should not be classified as commands."""
    # Even if it contains command words, a real question is a question
    question_with_command = "How do I refactor this function?"
    result = classify_intent(question_with_command)
    assert result == "QUESTION", f"Expected QUESTION for '{question_with_command}', got {result}"

    # But a command with "?" (like "fix this?") might be action - check
    command_with_question = "Refactor this?"  # Imperative with trailing ?
    result = classify_intent(command_with_question)
    # This could be QUESTION or ACTION depending on pattern - main thing is no crash
    assert result in (None, "QUESTION"), f"Unexpected result for '{command_with_question}': {result}"

    print("✅ Question vs command distinction tests passed")


def test_correction_priority():
    """CORRECTION should take priority over other classifications."""
    # Has DEBUG words but is clearly a CORRECTION
    correction_with_debug = "I told you to fix the bug properly"
    result = classify_intent(correction_with_debug)
    assert result == "CORRECTION", f"Expected CORRECTION for '{correction_with_debug}', got {result}"

    print("✅ Correction priority tests passed")


def test_edge_cases():
    """Test edge cases and potential false positives."""
    # Empty string
    assert classify_intent("") is None

    # Just a slash command
    assert classify_intent("/help") is None
    assert classify_intent("/commit message") is None

    # Question about a command (still a question)
    result = classify_intent("What does the /commit command do?")
    assert result == "QUESTION", f"Expected QUESTION, got {result}"

    print("✅ Edge case tests passed")


if __name__ == "__main__":
    test_question_classification()
    test_correction_classification()
    test_research_classification()
    test_debug_classification()
    test_action_classification()
    test_intent_injection_building()
    test_question_vs_command_distinction()
    test_correction_priority()
    test_edge_cases()
    print("\n✅ All intent classification tests passed!")
