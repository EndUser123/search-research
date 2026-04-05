#!/usr/bin/env python3
"""
Stop_recommendation_gate.py

Detects when the LLM presents options/choices WITHOUT a recommendation.
Returns a systemMessage advisory so the next response includes one.

Trigger condition: 2+ numbered options + decision-delegation phrase + no recommendation language.
Severity: warn (systemMessage) — not block. Advisory, not enforcement.
"""

from __future__ import annotations

import re

# Any of these signals a recommendation is already present → PASS
RECOMMENDATION_PATTERNS = [
    r"\brecommend\b",
    r"\bmy recommendation\b",
    r"\bgo with\b",
    r"\bbest option\b",
    r"\bbest approach\b",
    r"\boptimal\b",
    r"\bi['\u2019]d (?:choose|pick|suggest|go with)\b",
    r"\bi would (?:choose|pick|suggest|recommend)\b",
    r"\bstart with option\b",
]

# These phrases signal "user must choose" — delegation without guidance
DELEGATION_PATTERNS = [
    r"which (?:would you like|do you prefer|option|approach)",
    r"would you like (?:me to implement|to proceed with|to use|to start|any of)",
    r"want me to (?:implement|proceed|start|use|apply)",
    r"should i (?:proceed|implement|start|use|apply)",
    r"let me know which",
    r"which of these",
    r"do you want (?:me to|to proceed)",
    r"your (?:choice|preference|call|decision)",
    r"choose (?:between|from|which|one)",
    r"pick (?:one|which|the|an option)",
]


def _has_option_list(text: str) -> bool:
    """True if 2+ list items found (numbered or bulleted)."""
    numbered = re.findall(r"^\s*\d+\.\s+\S", text, re.MULTILINE)
    if len(numbered) >= 2:
        return True
    bulleted = re.findall(r"^\s*[-*]\s+\S", text, re.MULTILINE)
    return len(bulleted) >= 2


def _has_delegation(text: str) -> bool:
    """True if response delegates the decision to the user."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in DELEGATION_PATTERNS)


def _has_recommendation(text: str) -> bool:
    """True if response already contains recommendation language."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in RECOMMENDATION_PATTERNS)


def check_recommendation(response: str) -> dict | None:
    """
    Check for options-without-recommendation pattern.

    Returns:
        dict with 'systemMessage' if violation detected, else None.
    """
    if not response or len(response) < 80:
        return None

    if not _has_option_list(response):
        return None

    if not _has_delegation(response):
        return None

    if _has_recommendation(response):
        return None

    return {
        "systemMessage": (
            "[RECOMMENDATION GATE] You presented multiple options and delegated the decision "
            "without stating a recommendation.\n\n"
            "Rule: When presenting options, ALWAYS include your recommendation with reasoning. "
            "Never make the user ask 'what's your recommendation?'.\n\n"
            "On the next response: either add a clear recommendation, or re-answer decisively."
        )
    }
