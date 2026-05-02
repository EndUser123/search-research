"""Tests for shared_helpers.strip_non_claim_lines and is_question.

Regression tests for the false positive bug where markdown headers
like '## What's Missing (Minor)' and questions like 'Or is there a
different practical improvement?' were detected as factual claims.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from __lib.shared_helpers import is_question, strip_non_claim_lines

# === strip_non_claim_lines ===

def test_strips_markdown_headers():
    text = "## What's Missing (Minor)\n\nBody text here."
    result = strip_non_claim_lines(text)
    assert "## What's Missing" not in result
    assert "Body text here." in result


def test_strips_blockquotes():
    text = "> The file was deleted\n\nActual content."
    result = strip_non_claim_lines(text)
    assert "> The file was deleted" not in result
    assert "Actual content." in result


def test_strips_horizontal_rules():
    text = "Before\n---\nAfter"
    result = strip_non_claim_lines(text)
    assert "---" not in result
    assert "Before" in result
    assert "After" in result


def test_strips_table_rows():
    text = "| Component | Status |\n|---|---|\n| Missing | Incomplete |"
    result = strip_non_claim_lines(text)
    assert "| Missing" not in result
    assert "| Component" not in result


def test_strips_table_separator():
    text = "|---|---|---|\nContent"
    result = strip_non_claim_lines(text)
    assert "|---|" not in result
    assert "Content" in result


def test_preserves_body_text():
    text = "## Header\n\nThe file is missing from the project.\n\n> quoted"
    result = strip_non_claim_lines(text)
    assert "The file is missing from the project." in result


def test_empty_input():
    assert strip_non_claim_lines("") == ""
    assert strip_non_claim_lines(None) == ""


def test_all_structural_returns_empty():
    text = "## Header\n> Quote\n---\n| A | B |"
    result = strip_non_claim_lines(text)
    assert result.strip() == ""


# === is_question ===

def test_question_ending_with_mark():
    assert is_question("Or is there a different practical improvement you had in mind?")


def test_question_starting_with_would():
    assert is_question("Would you like me to add the missing test scenarios?")


def test_question_starting_with_what():
    assert is_question("What files handle routing?")


def test_question_starting_with_should():
    assert is_question("Should I create the optional goal guard hook?")


def test_question_starting_with_can_you():
    assert is_question("Can you help me understand the error?")


def test_question_starting_with_is_there():
    assert is_question("Is there a different approach we should take?")


def test_not_question_statement():
    assert not is_question("The file is missing from the project.")


def test_not_question_empty():
    assert not is_question("")
    assert not is_question(None)


def test_not_question_claim_with_question_word():
    # "What" appears but this is not a question — no question mark, not starting with it
    assert not is_question("I found what was missing in the config.")


# === strip_non_claim_lines: Stop-hook diagnostic stripping ===

def test_strips_status_label():
    """Stop hook block message with STATUS: prefix should be stripped."""
    text = "STATUS: blocked\n\nThe file exists at line 42."
    result = strip_non_claim_lines(text)
    assert "STATUS:" not in result
    assert "The file exists at line 42." in result


def test_strips_unverified_claims_header():
    """UNVERIFIED CLAIMS: header from Stop block should be stripped."""
    text = "UNVERIFIED CLAIMS: some reason\n\nActual answer content."
    result = strip_non_claim_lines(text)
    assert "UNVERIFIED CLAIMS:" not in result
    assert "Actual answer content." in result


def test_strips_evidence_missing_line():
    """'Evidence missing for:' line from Stop block should be stripped."""
    text = "Evidence missing for: ['claim text']\n\nThe function returns True."
    result = strip_non_claim_lines(text)
    assert "Evidence missing for:" not in result
    assert "The function returns True." in result


def test_strips_stop_hook_error_prefix():
    """'Stop hook error:' prefix should be stripped."""
    text = "Stop hook error: something\n\nReal content here."
    result = strip_non_claim_lines(text)
    assert "Stop hook error:" not in result
    assert "Real content here." in result


def test_strips_ran_stop_hooks_line():
    """'Ran N stop hooks' summary line should be stripped."""
    text = "Ran 3 stop hooks\n\nThe patch is applied correctly."
    result = strip_non_claim_lines(text)
    assert "Ran 3 stop hooks" not in result
    assert "The patch is applied correctly." in result


def test_strips_tool_ui_markers():
    """Tool/UI markers like ⎿ and ● should be stripped."""
    text = "⎿ Stop.py output\n● Another marker\n\nActual response body."
    result = strip_non_claim_lines(text)
    assert "⎿" not in result
    assert "●" not in result
    assert "Actual response body." in result


def test_regression_verification_loop():
    """Full regression: a resubmitted response with Stop diagnostics
    should have only the actual answer content remain after stripping.

    This reproduces the exact loop where Stop blocks with 'UNVERIFIED
    CLAIMS', Claude resubmits with block message + STATUS + original
    content, and the verifier re-flags the diagnostic lines as claims.
    """
    contaminated = (
        "Stop hook feedback:\n"
        "UNVERIFIED CLAIMS: UNVERIFIED_CLAIMS\n\n"
        "Evidence missing for: ['claims = extracted_claims if ...']\n\n"
        "STATUS: blocked\n\n"
        "The file at shared_helpers.py:147 defines strip_non_claim_lines().\n"
        "It strips headers, blockquotes, and table rows.\n"
    )
    result = strip_non_claim_lines(contaminated)
    assert "UNVERIFIED CLAIMS:" not in result
    assert "Evidence missing for:" not in result
    assert "STATUS:" not in result
    assert "Stop hook feedback:" not in result
    assert "strip_non_claim_lines" in result
    assert "headers, blockquotes" in result
