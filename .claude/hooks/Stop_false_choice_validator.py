#!/usr/bin/env python3
"""
Stop_false_choice_validator.py

Detects when the LLM presents independent, complementary actions as competing
resource-allocation decisions requiring the operator to pick a subset.

This is the structural backstop for the false-choices pattern documented in
~/.grok/AGENTS.md section "No false choices" and the wiki concept
[[false-choices-parallel-branch-framing]].

SEVERITY: advisory (systemMessage) - not block. This is intentional to measure
false-positive rate before promoting to block. Reference: MINIMAL_BIAS_GATE
noise problem (keyword-matching fired on descriptive context).

DIFFERENTIATION from Stop_recommendation_gate.py:
  recommendation_gate detects: options WITHOUT any recommendation.
  false_choice_validator detects: independent actions framed as competing choices.
    The "or both" telltale is the key signal - genuine alternatives do not have
    "or both" because only one can be chosen.
"""

from __future__ import annotations
import re

# -- Trigger patterns --
# These surface patterns indicate independent actions being framed as competing options.

# Pattern 1: "or both" / "or all" telltale - only appears when options are
# independent (genuine alternatives do not have "or both")
OR_BOTH_PATTERNS = [
    r"\bor\s+(?:both|all(?:\s+of\s+(?:them|these|the\s+above))?)\b",
]

# Pattern 2: "which subset" / "which of these" - operator asked to choose
# among independent items rather than told all will be done
SUBSET_DELEGATION_PATTERNS = [
    r"which\s+(?:subset|ones?|set)\s+(?:would|should|do|can)\s+you",
    r"which\s+of\s+these\s+(?:would|do|should)\s+you\s+(?:like|want|prefer)",
    r"which\s+(?:ones?|items?|tasks?)\s+(?:would|do)\s+you\s+(?:like|want)\s+me\s+to",
]

# Pattern 3: "Should I do X, or Y, or Z?" where items are independent actions
MENU_DELEGATION_PATTERNS = [
    r"(?:would|shall)\s+you\s+like\s+me\s+to\s+(?:do|implement|proceed|start|work)",
    r"want\s+me\s+to\s+(?:do|implement|proceed|start)\s+(?:option|item|task|all)",
    r"should\s+i\s+(?:do|implement|proceed|start|prioritize)\s+(?:option|item|task|all|these)",
]

# -- Escape patterns --
# These signal the response is NOT a false choice.

DO_ALL_PATTERNS = [
    r"\bdo\s+(?:all|both|every\s+one)\s+(?:of\s+)?(?:them|these|the\s+above)\b",
    r"\bi\s+(?:recommend|suggest|propose)\s+do(?:ing)?\s+(?:all|both|everything)\b",
    r"\bwe\s+should\s+(?:do|implement|proceed\s+with)\s+(?:all|both)\b",
    r"\bgo\s+ahead\s+and\s+(?:do|implement)\s+(?:all|both|everything)\b",
]

GENUINE_COMPETITION_PATTERNS = [
    r"\b(?:vs\.?|versus)\b",
    r"\btrade-?off\b",
    r"\beither\s+(?:option|approach|way)\b",
    r"\bonly\s+one\s+(?:can|should)\b",
    r"\bmutually\s+exclusive\b",
]

MIN_RESPONSE_LENGTH = 100


def _has_or_both(response: str) -> bool:
    return any(re.search(p, response, re.IGNORECASE) for p in OR_BOTH_PATTERNS)


def _has_subset_delegation(response: str) -> bool:
    return any(re.search(p, response, re.IGNORECASE) for p in SUBSET_DELEGATION_PATTERNS)


def _has_menu_delegation(response: str) -> bool:
    return any(re.search(p, response, re.IGNORECASE) for p in MENU_DELEGATION_PATTERNS)


def _has_do_all(response: str) -> bool:
    return any(re.search(p, response, re.IGNORECASE) for p in DO_ALL_PATTERNS)


def _has_genuine_competition(response: str) -> bool:
    return any(re.search(p, response, re.IGNORECASE) for p in GENUINE_COMPETITION_PATTERNS)


def _has_action_list(response: str) -> bool:
    numbered = re.findall(r"^\s*\d+\.\s+\S", response, re.MULTILINE)
    if len(numbered) >= 2:
        return True
    bulleted = re.findall(r"^\s*[-*]\s+\S", response, re.MULTILINE)
    return len(bulleted) >= 2


ADVISORY_MESSAGE = (
    "[FALSE CHOICE CHECK] You may be presenting independent actions as competing choices.\n\n"
    "If these actions are independent and each has positive ROI, do ALL of them - "
    "do not ask the operator which subset to pick. Present as a parallel list, "
    "not a resource-allocation menu.\n\n"
    "Reference: AGENTS.md 'No false choices' section and "
    "[[false-choices-parallel-branch-framing]]"
)


def check_false_choice(response: str, data: dict | None = None) -> dict | None:
    """
    Check for false-choice patterns in the response.

    Returns:
        dict with 'systemMessage' if potential false choice detected, else None.
        Advisory only - never blocks.
    """
    if not response or len(response) < MIN_RESPONSE_LENGTH:
        return None

    if _has_do_all(response):
        return None

    if _has_genuine_competition(response):
        return None

    has_trigger = (
        _has_or_both(response)
        or _has_subset_delegation(response)
        or _has_menu_delegation(response)
    )

    if _has_or_both(response) and not _has_genuine_competition(response):
        return {"systemMessage": ADVISORY_MESSAGE}

    if has_trigger and _has_action_list(response):
        return {"systemMessage": ADVISORY_MESSAGE}

    return None
