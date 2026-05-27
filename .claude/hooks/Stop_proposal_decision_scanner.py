#!/usr/bin/env python3
"""
Stop_proposal_decision_scanner.py - Proposal-Decision Conflation Guard
=====================================================================

Detects when plans claim that rejected options are "correct" — a cognitive
pattern where initial proposals persist as decisions even after user rejection.

FAILURE MODE CAUGHT:
  User rejected Option B, confirmed removal, but plan says "Option B is correct"
  -> Guard warns and surfaces the contradiction

DETECTION LOGIC:
  1. Scan response for decision claims: "Option X is correct", "go with Option X"
  2. Cross-reference with conversation history for prior rejections
  3. If contradiction found between claimed decision and prior rejection -> warn

LIFECYCLE: Stop (advisory — warn only, does not block)

v1.0 - 2026-04-07: Initial implementation
"""

from __future__ import annotations

import json
import logging as _li
import os
import re
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

try:
    from __lib.hook_base import hook_main
except ImportError:
    from hook_base import hook_main

try:
    from __lib.transcript_reader import get_user_messages as _get_user_messages_from_transcript
except ImportError:
    _get_user_messages_from_transcript = None

# --- Configuration -------------------------------------------------------

ENABLED = os.environ.get("PROPOSAL_DECISION_SCANNER_ENABLED", "true").lower() == "true"
DEBUG = os.environ.get("PROPOSAL_DECISION_SCANNER_DEBUG", "false").lower() == "true"


# --- Detection Patterns ---------------------------------------------------

# Patterns that claim an option is correct/valid/selected
DECISION_CLAIM_PATTERNS = [
    re.compile(r"(Option\s+[A-Z])\s+is\s+correct", re.IGNORECASE),
    re.compile(r"(Option\s+[A-Z])\s+is\s+(?:also\s+)?correct", re.IGNORECASE),
    re.compile(r"(Option\s+[A-Z])\s+is\s+right", re.IGNORECASE),
    re.compile(r"(Option\s+[A-Z])\s+should\s+be\s+used", re.IGNORECASE),
    re.compile(r"go\s+with\s+(Option\s+[A-Z])", re.IGNORECASE),
    re.compile(r"(Option\s+[A-Z])\s+is\s+the\s+(?:right|correct)\s+approach", re.IGNORECASE),
    re.compile(r"select(?:ing)?\s+(Option\s+[A-Z])", re.IGNORECASE),
]

# Patterns that indicate user rejection of an option
REJECTION_PATTERNS = [
    re.compile(r"(Option\s+[A-Z])\s+(?:doesn['\u2019]?t\s+make\s+sense|doesnt\s+make\s+sense)", re.IGNORECASE),
    re.compile(r"(Option\s+[A-Z])\s+(?:is|was|were)?\s*rejected?", re.IGNORECASE),
    re.compile(r"(Option\s+[A-Z])\s+shouldn?['\s]t\s+be\s+used", re.IGNORECASE),
    re.compile(r"don['\s]t\s+rebuild", re.IGNORECASE),
    re.compile(r"remove[d]?\s+(?:the\s+)?(?:session'?s?\s+)?index", re.IGNORECASE),
    re.compile(r"(Option\s+[A-Z])\s+is?\s+wrong", re.IGNORECASE),
]


# --- Core Detection Logic -----------------------------------------------


def _extract_decision_claims(text: str) -> list[str]:
    """Extract all claimed options (e.g., 'Option B') from decision claim patterns."""
    found = []
    for pattern in DECISION_CLAIM_PATTERNS:
        for match in pattern.finditer(text):
            option = match.group(1) if match.groups() else None
            if option:
                found.append(option)
    # Deduplicate while preserving order (patterns may overlap)
    return list(dict.fromkeys(found))


def _extract_rejections(text: str) -> list[str]:
    """Extract all rejected options from rejection patterns."""
    found = []
    for pattern in REJECTION_PATTERNS:
        for match in pattern.finditer(text):
            option = match.group(1) if match.groups() else None
            if option:
                found.append(option)
    return found


def _normalize_option(option: str) -> str:
    """Normalize option string for comparison (e.g., 'option b' -> 'OPTION B')."""
    return option.upper()


def _check_response_for_conflation(response: str, transcript_texts: list[str]) -> dict | None:
    """Check if response claims a rejected option is correct.

    Returns warning dict if contradiction detected, None otherwise.
    """
    # Extract decision claims from current response
    claimed_options = _extract_decision_claims(response)
    if not claimed_options:
        return None

    # Extract rejections from conversation history
    all_rejected: set[str] = set()
    for entry_text in transcript_texts:
        rejected = _extract_rejections(entry_text)
        for opt in rejected:
            all_rejected.add(_normalize_option(opt))

    # Check for contradiction
    contradicted_options = []
    for claimed in claimed_options:
        normalized = _normalize_option(claimed)
        if normalized in all_rejected:
            contradicted_options.append(claimed)

    if not contradicted_options:
        return None

    # Build warning message
    option_list = ", ".join(f"**{opt}**" for opt in set(contradicted_options))
    warning_lines = [
        "",
        "=" * 60,
        "⚠️  PROPOSAL-DECISION CONFLATION DETECTED",
        "=" * 60,
        "",
        f"You claimed in your response that {option_list} is correct,",
        "but your conversation history shows these options were rejected.",
        "",
        "This is a cognitive pattern (belief perseverance) where initial",
        "proposals persist as decisions even after user correction.",
        "",
        "BEFORE FINALIZING THIS RESPONSE:",
        "  1. Re-read your conversation history to confirm what was actually decided",
        "  2. Update the plan/response to reflect the confirmed decision",
        "  3. Do NOT claim rejected options are correct",
        "",
        "Evidence: User rejection > Confirmation > Plan should reflect decision",
        "=" * 60,
        "",
    ]

    warning = "\n".join(warning_lines)

    if DEBUG:
        _logger.debug(f"Contradiction detected: {contradicted_options}")

    return {
        "decision": "warn",
        "reason": warning,
        "blocking_hook": "Stop_proposal_decision_scanner",
    }


# --- Main Entry Point ---------------------------------------------------


def check(data: dict) -> dict | None:
    """Core guard logic. Returns warning dict or None (allow)."""
    if not ENABLED:
        return None

    response = data.get("assistant_response", "") or data.get("response", "") or ""
    if not response:
        return None

    # transcript_entries is never populated in Stop hooks; use transcript_path
    transcript_texts: list[str] = []
    if _get_user_messages_from_transcript is not None:
        transcript_texts = _get_user_messages_from_transcript(data)

    return _check_response_for_conflation(response, transcript_texts)


def run(data: dict) -> dict | None:
    """In-process validator protocol for Stop_router."""
    result = check(data)
    if result and result.get("decision") == "warn":
        return {
            "decision": "warn",
            "reason": result.get("reason", ""),
            "blocking_hook": "Stop_proposal_decision_scanner",
        }
    return result


def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            sys.exit(0)
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    result = check(data)
    if result:
        print(json.dumps(result))


if __name__ == "__main__":
    main()
