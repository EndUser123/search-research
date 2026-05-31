"""
Tests for FIX 1 (has_bash_evidence parameter) and FIX 2 (inline backtick exemption).
"""

import re
from lazy_closure_detector import detect_lazy_closure


def test_capitulation_with_bash_evidence_flag_true():
    """
    FIX 1: Capitulation phrase + has_bash_evidence=True should return None (no block).

    When explicit Bash evidence flag is provided as True, the prose-based check is overridden.
    """
    response = "I see now. So the command simply shows documentation, not options."

    # Without the flag (default behavior): should detect capitulation
    result_default = detect_lazy_closure(response)
    assert result_default is not None, "Should detect capitulation without flag (default)"
    assert result_default.pattern_type == "sycophancy_capitulation"

    # With has_bash_evidence=True: should NOT detect (override prose check)
    result_with_flag = detect_lazy_closure(response, has_bash_evidence=True)
    assert result_with_flag is None, "Should NOT detect capitulation when has_bash_evidence=True"


def test_capitulation_with_bash_evidence_flag_false():
    """
    FIX 1: Capitulation phrase + has_bash_evidence=False should return a block (no override).

    When explicit Bash evidence flag is False, it confirms no bash run occurred.
    """
    response = "I see now. So the command simply shows documentation, not options."

    # With has_bash_evidence=False: should detect capitulation
    result = detect_lazy_closure(response, has_bash_evidence=False)
    assert result is not None, "Should detect capitulation when has_bash_evidence=False"
    assert result.pattern_type == "sycophancy_capitulation"


def test_capitulation_with_bash_evidence_none():
    """
    FIX 1: Capitulation phrase + has_bash_evidence=None should use default prose check.

    None value preserves backward compatibility (falls back to _has_bash_evidence).
    """
    response = "I see now. So the command simply shows documentation, not options."

    # With has_bash_evidence=None: should use default prose check (detect because no bash markers)
    result = detect_lazy_closure(response, has_bash_evidence=None)
    assert result is not None, "Should detect capitulation with has_bash_evidence=None"
    assert result.pattern_type == "sycophancy_capitulation"

    # With no parameter (default): should also detect
    result_default = detect_lazy_closure(response)
    assert result_default is not None, "Should detect capitulation without parameter"


def test_capitulation_phrase_inside_backticks():
    """
    FIX 2: Capitulation phrase inside inline backticks should return None (no block).

    Inline code spans like `you're right` should be exempted.
    """
    # Case 1: Quote of model saying "you're right" inside backticks
    response = "Here's what the user said: `you're right that this is broken`."
    result = detect_lazy_closure(response)
    assert result is None, "Should NOT detect when phrase is inside inline backticks"

    # Case 2: Longer response with capitulation outside backticks (should still block)
    response2 = "You're right. The code has `some backticks` but still shows agreement."
    result2 = detect_lazy_closure(response2)
    assert result2 is not None, "Should detect capitulation outside backticks"


def test_capitulation_phrase_outside_backticks():
    """
    FIX 2: Same capitulation phrase outside backticks should be detected.

    Ensures fix doesn't create false negatives for actual capitulation.
    """
    response = "You're right. The implementation is already working as intended."
    result = detect_lazy_closure(response)
    assert result is not None, "Should detect capitulation outside backticks"
    assert result.pattern_type == "sycophancy_capitulation"


def test_capitulation_with_odd_backticks_before_match():
    """
    FIX 2: Odd number of backticks before match = inside code span.

    Tests the backtick counting logic: if odd count before match, match is inside backticks.
    """
    # One backtick before match = inside code span
    response = "The user wrote: `I see now and this is correct`."
    result = detect_lazy_closure(response)
    assert result is None, "Should NOT detect when odd backticks before phrase"


def test_capitulation_with_even_backticks_before_match():
    """
    FIX 2: Even number of backticks before match = outside code span.

    Tests that even number of backticks (closed spans) don't block detection.
    """
    # Two backticks before match (one complete code span) = outside code span
    response = "The `code` is fine. I see now why this is better."
    result = detect_lazy_closure(response)
    assert result is not None, "Should detect capitulation after complete backtick pair"


def test_true_positive_preserved():
    """
    FIX 1+2 combined: Ensure true positives still fire.

    Capitulation without bash evidence and not in backticks = block.
    """
    response = "Now I understand. The API returns the data directly."
    result = detect_lazy_closure(response)
    assert result is not None, "Should still detect true positive capitulation"
    assert result.pattern_type == "sycophancy_capitulation"

    # With explicit bash_evidence=True, same response should NOT block
    result_with_bash = detect_lazy_closure(response, has_bash_evidence=True)
    assert result_with_bash is None, "Should NOT block when bash_evidence=True"


def test_both_fixes_combined():
    """
    FIX 1+2 combined: Backticks + explicit bash evidence.

    Double-protected false positive should return None.
    """
    response = "`You're right` about the behavior. $ echo test"

    # Inside backticks AND (no bash flag OR explicit bash_evidence=True)
    _result1 = detect_lazy_closure(response)  # Backticks protect, no bash in prose
    # May detect because "$ echo test" is bash marker

    # Inside backticks with explicit bash_evidence=True
    result2 = detect_lazy_closure(response, has_bash_evidence=True)
    assert result2 is None, "Should NOT detect: backticks + bash_evidence=True"




# -- FIX 3: table/blockquote newline exemption ------------------------------------

def test_capitulation_inside_markdown_table_not_blocked():
    """FIX 3 (live repro): capitulation phrase inside a table cell is NOT blocked.

    Root cause: whitespace normalization stripped newlines, so _is_inside_quoted_content
    could not detect the table via rfind('\\n'). Fix: preserve newlines in normalization.
    """
    table_resp = (
        "Here is my analysis:\n\n"
        "| Block | Label | Why |\n"
        "|---|---|---|\n"
        '| Capitulation on "You\'re right to challenge it" | TRUE positive | the gate worked |\n\n'
        "That is the finding."
    )
    result = detect_lazy_closure(table_resp, has_bash_evidence=False)
    assert result is None, (
        f"Should NOT block capitulation inside table cell, got: {result}"
    )


def test_capitulation_inside_blockquote_not_blocked():
    """FIX 3: capitulation phrase on a blockquote line is NOT blocked.

    Blockquote lines start with '> ', which _is_inside_quoted_content detects via
    line-prefix check after rfind('\\n'). This only works when newlines are preserved.
    """
    blockquote_resp = (
        "Here is the transcript:\n\n"
        "> You're right, I was wrong about that.\n\n"
        "That was the prior model output being quoted."
    )
    result = detect_lazy_closure(blockquote_resp, has_bash_evidence=False)
    assert result is None, (
        f"Should NOT block capitulation inside blockquote, got: {result}"
    )


def test_bare_capitulation_still_blocked():
    """FIX 3 (preserved TRUE POSITIVE): bare capitulation as model assertion is blocked.

    The fix must not weaken bare (unquoted) capitulation detection.
    This is the catch that found a real error this session.
    """
    response = "You're right, I was wrong about that."
    result = detect_lazy_closure(response, has_bash_evidence=False)
    assert result is not None, "Should BLOCK bare capitulation in model assertion"
    assert result.pattern_type == "sycophancy_capitulation"


def test_capitulation_with_bash_evidence_true_still_exempt():
    """Preserved: has_bash_evidence=True exempts bare capitulation (existing exemption)."""
    response = "You're right, I was wrong about that."
    result = detect_lazy_closure(response, has_bash_evidence=True)
    assert result is None, (
        f"Should NOT block when has_bash_evidence=True, got: {result}"
    )


if __name__ == "__main__":
    test_capitulation_with_bash_evidence_flag_true()
    print("✅ test_capitulation_with_bash_evidence_flag_true")

    test_capitulation_with_bash_evidence_flag_false()
    print("✅ test_capitulation_with_bash_evidence_flag_false")

    test_capitulation_with_bash_evidence_none()
    print("✅ test_capitulation_with_bash_evidence_none")

    test_capitulation_phrase_inside_backticks()
    print("✅ test_capitulation_phrase_inside_backticks")

    test_capitulation_phrase_outside_backticks()
    print("✅ test_capitulation_phrase_outside_backticks")

    test_capitulation_with_odd_backticks_before_match()
    print("✅ test_capitulation_with_odd_backticks_before_match")

    test_capitulation_with_even_backticks_before_match()
    print("✅ test_capitulation_with_even_backticks_before_match")

    test_true_positive_preserved()
    print("✅ test_true_positive_preserved")

    test_both_fixes_combined()
    print("✅ test_both_fixes_combined")

    print("\n✅✅✅ All tests passed!")
