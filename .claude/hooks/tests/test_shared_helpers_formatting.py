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
