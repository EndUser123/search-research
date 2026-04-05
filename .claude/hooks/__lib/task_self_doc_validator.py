#!/usr/bin/env python3
"""
task_self_doc_validator.py - Task self-documentation validation

Validates that tasks explain the problem, situation, and symptoms.
Used by PostToolUse advisory (task_tracker_hook.py) and Stop completion gate.

Self-documentation Schema:
- Subject: 10+ characters
- Description: 50+ characters with at least one indicator from each category:
  - Problem: fix, bug, issue, error, crash, broken, fails
  - Situation: when, during, while, after, in, on
  - Symptom: shows, returns, throws, produces, outputs, error, exception
"""

from __future__ import annotations

import os
import re
from typing import NamedTuple

# Minimum lengths
DEFAULT_MIN_SUBJECT_LEN = 10
DEFAULT_MIN_DESC_LEN = 50

# Indicator patterns by category
PROBLEM_INDICATORS = [
    r"\bfix\b",
    r"\bbug\b",
    r"\bissue\b",
    r"\berror\b",
    r"\bcrash\b",
    r"\bbroken\b",
    r"\bfails\b",
]
SITUATION_INDICATORS = [
    r"\bwhen\b",
    r"\bduring\b",
    r"\bwhile\b",
    r"\bafter\b",
    r"\bin\b",
    r"\bon\b",
]
SYMPTOM_INDICATORS = [
    r"\bshows\b",
    r"\breturns\b",
    r"\bthrows\b",
    r"\bproduces\b",
    r"\boutputs\b",
    r"\berror\b",
    r"\bexception\b",
]


class ValidationResult(NamedTuple):
    """Result of self-documentation validation."""

    is_valid: bool
    missing_categories: list[str]
    warnings: list[str]
    subject_length: int
    desc_length: int


def _check_category(text: str, patterns: list[str]) -> bool:
    """Check if text contains any indicator from a category."""
    lower = text.lower()
    for pattern in patterns:
        if re.search(pattern, lower):
            return True
    return False


def self_documentation_check(
    subject: str,
    description: str,
    min_subject_len: int | None = None,
    min_desc_len: int | None = None,
    require_all: bool = True,
) -> ValidationResult:
    """
    Validate that a task has self-documentation.

    A task is self-documenting if:
    1. Subject is at least min_subject_len characters
    2. Description is at least min_desc_len characters
    3. Description contains at least one indicator from each category
       (Problem, Situation, Symptom) - unless require_all=False

    Args:
        subject: Task subject line
        description: Task description
        min_subject_len: Minimum subject length (default: 10)
        min_desc_len: Minimum description length (default: 50)
        require_all: If True, all three categories required. If False, any one.

    Returns:
        ValidationResult with is_valid, missing_categories, warnings
    """
    # Get thresholds from env or defaults
    if min_subject_len is None:
        min_subject_len = int(os.environ.get("TASK_SELF_DOC_MIN_SUBJECT", DEFAULT_MIN_SUBJECT_LEN))
    if min_desc_len is None:
        min_desc_len = int(os.environ.get("TASK_SELF_DOC_MIN_DESC", DEFAULT_MIN_DESC_LEN))

    missing_categories: list[str] = []
    warnings: list[str] = []

    subject_len = len(subject) if subject else 0
    desc_len = len(description) if description else 0

    # Check subject length
    if subject_len < min_subject_len:
        warnings.append(
            f"Subject too short ({subject_len}/{min_subject_len} chars). "
            f"Add context to make it self-explanatory."
        )

    # Check description length
    if desc_len < min_desc_len:
        warnings.append(
            f"Description too short ({desc_len}/{min_desc_len} chars). "
            f"Add problem, situation, and symptom details."
        )

    # Check category indicators
    has_problem = _check_category(description, PROBLEM_INDICATORS)
    has_situation = _check_category(description, SITUATION_INDICATORS)
    has_symptom = _check_category(description, SYMPTOM_INDICATORS)

    if not has_problem:
        missing_categories.append("Problem (what issue is this fixing?)")
    if not has_situation:
        missing_categories.append("Situation (when/where does it occur?)")
    if not has_symptom:
        missing_categories.append("Symptom (what observable behavior?)")

    # Determine validity
    if require_all:
        is_valid = (
            subject_len >= min_subject_len
            and desc_len >= min_desc_len
            and has_problem
            and has_situation
            and has_symptom
        )
    else:
        # Any one category is enough
        is_valid = (subject_len >= min_subject_len or desc_len >= min_desc_len) and (
            has_problem or has_situation or has_symptom
        )

    return ValidationResult(
        is_valid=is_valid,
        missing_categories=missing_categories,
        warnings=warnings,
        subject_length=subject_len,
        desc_length=desc_len,
    )


def is_task_self_documented(
    subject: str,
    description: str,
) -> bool:
    """
    Simple boolean check if task is self-documenting.

    Args:
        subject: Task subject
        description: Task description

    Returns:
        True if task meets self-documentation requirements
    """
    result = self_documentation_check(subject, description)
    return result.is_valid


if __name__ == "__main__":
    # Self-test
    print("Running self-tests...")

    # Test 1: Well-documented task
    result = self_documentation_check(
        subject="Fix file not found error when running test suite",
        description="When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
    )
    print(f"Test 1 (valid task): {result.is_valid}")
    assert result.is_valid, f"Expected valid, got: {result}"
    assert not result.missing_categories

    # Test 2: Vague task (has Problem indicator "bug" but missing Situation and Symptom)
    # Note: "Bug in tests" has "in" which is a situation indicator, so only Symptom is missing
    result = self_documentation_check(
        subject="Fix bug",
        description="Bug in tests",
    )
    print(f"Test 2 (vague task): {result.is_valid}")
    assert not result.is_valid
    # Check that the categories that ARE found are not in missing_categories
    missing_str = str(result.missing_categories)
    assert "Problem" not in result.missing_categories  # "bug" matches Problem indicator
    assert "Situation" not in result.missing_categories  # "in" matches Situation indicator
    assert any("Symptom" in m for m in result.missing_categories)  # Symptom is missing

    # Test 3: Empty task
    result = self_documentation_check(
        subject="",
        description="",
    )
    print(f"Test 3 (empty task): {result.is_valid}")
    assert not result.is_valid

    print("All self-tests passed.")
