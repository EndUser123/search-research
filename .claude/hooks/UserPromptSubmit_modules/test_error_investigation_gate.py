"""Tests for error_investigation_gate.py - Simplified version"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from error_investigation_gate import _is_error_inquiry, ERROR_KEYWORDS


def test_error_inquiry_detection():
    """Test that error investigation keywords are correctly detected."""
    
    # Should trigger (error investigation keywords)
    error_prompts = [
        "What went wrong?",  # "wrong" in ERROR_KEYWORDS
        "Why did the test fail?",  # "fail" in ERROR_KEYWORDS
        "Check the transcript",  # "transcript" in ERROR_KEYWORDS
        "Debug this error",  # "debug" and "error" in ERROR_KEYWORDS
        "Investigate why it crashed",  # "investigate" and "crash" in ERROR_KEYWORDS
        "What is the error?",  # "error" in ERROR_KEYWORDS
        "The build failed",  # "fail" in ERROR_KEYWORDS
        "Can you debug this?",  # "debug" in ERROR_KEYWORDS
        "Look at the transcript",  # "transcript" in ERROR_KEYWORDS
        "Why is this broken?",  # "broken" in ERROR_KEYWORDS
    ]
    
    for prompt in error_prompts:
        assert _is_error_inquiry(prompt), f"Should detect: '{prompt}'"
    
    # Should NOT trigger (no error keywords)
    non_error_prompts = [
        "Implement this feature",
        "Run the tests",
        "Create a new file",
        "How do I write a for loop?",
        "Summarize this document",
        "Refactor this code",
        "Add authentication",
        "The weather is nice",
        "Hello world",
    ]
    
    for prompt in non_error_prompts:
        assert not _is_error_inquiry(prompt), f"Should NOT detect: '{prompt}'"


def test_keyword_coverage():
    """Test that ERROR_KEYWORDS contains essential terms."""
    
    # Essential keywords for error investigation
    essential_keywords = {"error", "fail", "transcript", "debug", "investigate"}
    
    for kw in essential_keywords:
        assert kw in ERROR_KEYWORDS, f"Missing essential keyword: {kw}"


def test_case_insensitive_matching():
    """Test that keyword matching is case-insensitive."""
    
    test_cases = [
        ("ERROR: something failed", True),
        ("Error: test failed", True),
        ("error: system crashed", True),
        ("The Error is", True),
        ("DEBUG this", True),
        ("Debug this", True),
        ("debug this", True),
    ]
    
    for prompt, expected in test_cases:
        result = _is_error_inquiry(prompt)
        assert result == expected, f"Case sensitivity failed for: '{prompt}'"


def test_simple_substring_limitations():
    """Test known limitations of simple substring matching.
    
    NOTE: Simple substring matching has false positives. This is acceptable
    for solo-dev simplicity. The reminder is harmless even when triggered
    inappropriately.
    """
    
    # These WILL trigger (contain "error") but that's acceptable
    false_positive_cases = [
        "No error here",  # Contains "error" but is a negation
        "What files use error codes?",  # Contains "error" but is a different question
    ]
    
    for prompt in false_positive_cases:
        result = _is_error_inquiry(prompt)
        # We accept false positives for simplicity
        assert result is True, f"Accepted false positive: '{prompt}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
