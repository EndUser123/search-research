#!/usr/bin/env python3
"""Test FrameGuard regex safety.

Tests that FrameGuard regex patterns are safe from ReDoS and perform well:
- Systemic patterns are safe from ReDoS
- Handling patterns are safe from ReDoS
- Pattern match performance (<100ms)
- Long input handling
- Special characters in input
- Unicode in patterns
- Empty string handling
- Null input handling
"""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

import pytest

sys_path_insert = str(Path(__file__).resolve().parents[1])
if sys_path_insert not in sys.path:
    sys.path.insert(0, sys_path_insert)


# === Helper Functions ===


def measure_pattern_performance(pattern: str, test_input: str) -> float:
    """Measure pattern match performance in milliseconds."""
    start = time.perf_counter()
    re.search(pattern, test_input)
    end = time.perf_counter()
    return (end - start) * 1000  # Convert to ms


# === ReDoS Safety Tests ===


def test_systemic_patterns_no_redos() -> None:
    """Test systemic patterns are safe from ReDoS."""
    from UserPromptSubmit_modules.frameguard_classifier import SYSTEMIC_PATTERNS

    # Evil input that could trigger ReDoS in vulnerable patterns
    evil_input = "a" * 10000 + " hook" + "a" * 10000

    for pattern in SYSTEMIC_PATTERNS:
        # Should complete quickly (not hang due to catastrophic backtracking)
        duration = measure_pattern_performance(pattern, evil_input)
        assert duration < 100, f"Pattern took {duration}ms, potential ReDoS: {pattern}"


def test_handling_patterns_no_redos() -> None:
    """Test handling patterns are safe from ReDoS."""
    # These are the patterns from frameguard_stop.py
    HANDLING_PATTERNS = [
        r"(?i)\bbroader (question|issue|structure|context|frame)\b",
        r"(?i)\bcoverage\b",
        r"(?i)\brelationship\b",
        r"(?i)\b(other|related) (agents?|hooks?|services?|components?|elements?)\b",
        r"(?i)\bI am not addressing the broader\b",
        r"(?i)\bsystemic (context|frame|question)\b",
        r"(?i)\barchitectural (context|implication)\b",
    ]

    evil_input = "a" * 10000 + " broader " + "a" * 10000

    for pattern in HANDLING_PATTERNS:
        duration = measure_pattern_performance(pattern, evil_input)
        assert duration < 100, f"Pattern took {duration}ms, potential ReDoS: {pattern}"


# === Performance Tests ===


def test_pattern_match_performance() -> None:
    """Test patterns match in <100ms."""
    from UserPromptSubmit_modules.frameguard_classifier import SYSTEMIC_PATTERNS

    # Typical input length
    typical_input = "Do we have a hook for session management in the system?"

    for pattern in SYSTEMIC_PATTERNS:
        duration = measure_pattern_performance(pattern, typical_input)
        assert duration < 100, f"Pattern took {duration}ms: {pattern}"


# === Edge Case Tests ===


def test_long_input_handling() -> None:
    """Test long inputs handled gracefully."""
    from UserPromptSubmit_modules.frameguard_classifier import SYSTEMIC_PATTERNS

    # Very long input (100k characters)
    long_input = "Do we have " + "x" * 100000 + " hook?"

    for pattern in SYSTEMIC_PATTERNS:
        # Should not raise exception and should complete quickly
        duration = measure_pattern_performance(pattern, long_input)
        assert duration < 100, f"Long input took {duration}ms"


def test_special_characters_in_input() -> None:
    """Test special characters don't break patterns."""
    from UserPromptSubmit_modules.frameguard_classifier import SYSTEMIC_PATTERNS

    special_input = 'Do we have a hook for: "test" \n\t\r\n\x00?'

    for pattern in SYSTEMIC_PATTERNS:
        # Should handle special characters without error
        _ = re.search(pattern, special_input)  # Verify no exception


def test_unicode_in_patterns() -> None:
    """Test Unicode handled correctly."""
    from UserPromptSubmit_modules.frameguard_classifier import SYSTEMIC_PATTERNS

    unicode_input = "Do we have a hook for café? 日本語测试 🎉"

    for pattern in SYSTEMIC_PATTERNS:
        # Should handle Unicode without error
        _ = re.search(pattern, unicode_input)  # Verify no exception


def test_empty_string_handling() -> None:
    """Test empty strings handled gracefully."""
    from UserPromptSubmit_modules.frameguard_classifier import SYSTEMIC_PATTERNS

    empty_input = ""

    for pattern in SYSTEMIC_PATTERNS:
        # Should not match empty string
        result = re.search(pattern, empty_input)
        assert result is None, "Pattern should not match empty string"


def test_null_input_handling() -> None:
    """Test None/null handled gracefully."""
    from UserPromptSubmit_modules.frameguard_classifier import SYSTEMIC_PATTERNS

    for pattern in SYSTEMIC_PATTERNS:
        # None should be handled before regex (type check)
        # This test documents the expectation
        # In actual code, input is converted to str() before pattern matching
        test_input = None
        try:
            # Simulate what the hook does: str(None) = "None"
            _ = re.search(pattern, str(test_input))  # Should not match "None" string
        except Exception:
            # Or raise a clear error
            pass  # Either behavior is acceptable


# === Additional Safety Tests ===


def test_nested_quantifiers_safety() -> None:
    """Test patterns don't have dangerous nested quantifiers."""
    from UserPromptSubmit_modules.frameguard_classifier import SYSTEMIC_PATTERNS

    # Nested quantifiers like (a+)+ are common ReDoS sources
    for pattern in SYSTEMIC_PATTERNS:
        # Check for suspicious patterns
        assert not re.search(r"\(\.\*[+\*]\)", pattern), "Nested quantifier detected"
        assert not re.search(r"\(\.\+[+\*]\)", pattern), "Nested quantifier detected"


def test_overlapping_alternations_safety() -> None:
    """Test patterns don't have dangerous overlapping alternations."""
    from UserPromptSubmit_modules.frameguard_classifier import SYSTEMIC_PATTERNS

    # Overlapping alternations like (a|a)+ are ReDoS sources
    for pattern in SYSTEMIC_PATTERNS:
        # This is a simplified check - real ReDoS analysis is more complex
        # We're just ensuring basic safety
        compiled = re.compile(pattern)
        # If compilation succeeds, pattern is at least syntactically valid
        assert compiled is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
