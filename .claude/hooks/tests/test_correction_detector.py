from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from __lib__.correction_detector import (
    has_correction,
    has_acknowledgment,
    check_correction_acknowledge,
)


# --- has_correction tests ---

def test_has_correction_standalone_no() -> None:
    assert has_correction("No, that's not right.")


def test_has_correction_youre_wrong() -> None:
    assert has_correction("You're wrong about this.")


def test_has_correction_i_didnt_say() -> None:
    assert has_correction("I didn't say to use that approach.")


def test_has_correction_thats_not_what() -> None:
    assert has_correction("That's not what I asked for.")


def test_has_correction_not_correct() -> None:
    assert has_correction("That assessment is not correct.")


def test_has_correction_thats_inaccurate() -> None:
    assert has_correction("That's inaccurate.")


def test_has_correction_wrong() -> None:
    assert has_correction("The answer is wrong.")


def test_has_correction_case_insensitive() -> None:
    assert has_correction("NO, that's wrong.")


def test_has_correction_no_false_positive_knowledge() -> None:
    """'not knowing' contains 'not' but not a correction."""
    assert not has_correction("Not knowing the answer, I asked.")


def test_has_correction_no_false_positive_not_today() -> None:
    """'not today' should not trigger correction."""
    assert not has_correction("Not today, maybe tomorrow.")


# --- has_acknowledgment tests ---

def test_has_acknowledgment_i_was_wrong() -> None:
    assert has_acknowledgment("I was wrong. Let me fix that.")


def test_has_acknowledgment_let_me_correct() -> None:
    assert has_acknowledgment("Let me correct my earlier statement.")


def test_has_acknowledgment_youre_right() -> None:
    assert has_acknowledgment("You're right, I missed that.")


def test_has_acknowledgment_i_am_mistaken() -> None:
    assert has_acknowledgment("I am mistaken about that.")


def test_has_acknowledgment_i_stand_corrected() -> None:
    assert has_acknowledgment("I stand corrected.")


def test_has_acknowledgment_case_insensitive() -> None:
    assert has_acknowledgment("YOU'RE RIGHT about this.")


def test_has_acknowledgment_no_false_positive() -> None:
    """Generic agreement without acknowledgment should not trigger."""
    assert not has_acknowledgment("That seems reasonable.")
    assert not has_acknowledgment("Okay, I can do that.")


# --- check_correction_acknowledge integration tests ---

def test_check_correction_acknowledge_no_correction() -> None:
    """No correction pattern → acknowledged."""
    result = check_correction_acknowledge("Please summarize this.", "Here is a summary.")
    assert result["acknowledged"] is True
    assert result["reason"] is None


def test_check_correction_acknowledge_correction_no_acknowledgment() -> None:
    """Correction without acknowledgment → blocked."""
    result = check_correction_acknowledge(
        "No, that's wrong.",
        "Let me explain why it is correct.",
    )
    assert result["acknowledged"] is False
    assert "acknowledgment" in result["reason"].lower()


def test_check_correction_acknowledge_correction_with_acknowledgment() -> None:
    """Correction with acknowledgment → allowed."""
    result = check_correction_acknowledge(
        "No, you're wrong.",
        "I was wrong. Let me correct that.",
    )
    assert result["acknowledged"] is True


def test_check_correction_acknowledge_acknowledgment_proximity() -> None:
    """Acknowledgment within 200 chars → allowed."""
    result = check_correction_acknowledge(
        "I didn't say that.",
        "I stand corrected. " + "x" * 100,
    )
    assert result["acknowledged"] is True


def test_check_correction_acknowledge_acknowledgment_too_late() -> None:
    """Acknowledgment after 200 chars → blocked.

    Must use a space before 'I' to create a word boundary,
    since 'x500' leaves no boundary between x and I.
    """
    result = check_correction_acknowledge(
        "I didn't say that.",
        "x" * 300 + " I was wrong.",
    )
    assert result["acknowledged"] is False
    assert "position" in result["reason"].lower()
