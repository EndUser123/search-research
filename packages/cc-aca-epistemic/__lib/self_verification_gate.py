#!/usr/bin/env python3
"""
Self-Verification Gate - PostToolUse Hook
=========================================

Validates completion claims against session evidence.
Extends StopHook_unverified_stance.py patterns into PostToolUse.
Per ADR-20260325: Self-Correcting Agent Loop.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Import patterns from StopHook_unverified_stance if available
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from StopHook_unverified_stance import (
        COMPLETION_PATTERNS,
        E2E_PATTERNS,
        RUNTIME_COMMAND_PATTERNS,
        RUNTIME_TOOLS,
    )
except ImportError:
    # Fallback patterns if import fails
    COMPLETION_PATTERNS = [
        re.compile(r"\ball\s+tests?\s+pass", re.IGNORECASE),
        re.compile(r"\bfix(?:ed|es)?\s+", re.IGNORECASE),
        re.compile(r"\bverif(?:ied|ies|ication)\s+", re.IGNORECASE),
        re.compile(r"\bcomplete[td]?\s+", re.IGNORECASE),
        re.compile(r"\bdone\s+", re.IGNORECASE),
        re.compile(r"\bsuccess(?:ful|ly)?\s+", re.IGNORECASE),
        re.compile(r"\bimplemented\s+", re.IGNORECASE),
        re.compile(r"\bworking\s+", re.IGNORECASE),
    ]
    E2E_PATTERNS = [
        re.compile(r"\b(?:end-to-end|e2e)\s+(?:test|run|verify)", re.IGNORECASE),
        re.compile(r"\bfull\s+(?:test|run|verify)", re.IGNORECASE),
    ]
    RUNTIME_TOOLS = {"Bash", "Edit", "Read", "Grep", "Glob"}
    RUNTIME_COMMAND_PATTERNS = ["subprocess", "pytest", "python", "node", "npm test"]


# Maximum re-research attempts per claim (from plan)
MAX_RESEARCH_ATTEMPTS = 2


def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data


def _get_response_text(data: dict) -> str:
    """Extract response text from PostToolUse event data."""
    # Try various common field names
    response = data.get("response", "") or data.get("result", "") or ""
    if isinstance(response, dict):
        response = response.get("content", "") or response.get("text", "") or str(response)
    return str(response) if response else ""


def _get_tool_events(data: dict) -> list[dict]:
    """Extract tool events from session data."""
    events = data.get("events", []) or data.get("tool_events", []) or []
    return events if isinstance(events, list) else []


def _get_session_context(data: dict) -> dict:
    """Get session context for attribution tracking."""
    return {
        "terminal_id": data.get("terminal_id", "") or data.get("terminalId", ""),
        "session_id": data.get("session_id", "") or data.get("sessionId", ""),
    }


def _check_completion_claim_with_events(claim: str, events: list[dict]) -> tuple[bool, str]:
    """Check if completion claim is supported by tool events.

    Returns (is_verified, verification_message).
    """
    claim_lower = claim.lower()

    # Check for runtime tool usage that would verify the claim
    for event in events:
        event_type = event.get("type", "") or event.get("tool", "")
        event_name = event.get("name", "") or event.get("command", "") or ""

        # Bash commands that indicate actual execution
        if event_type == "Bash" or event_type == "bash":
            for pattern in RUNTIME_COMMAND_PATTERNS:
                if pattern in event_name.lower():
                    return True, f"Verified via: {event_name}"

        # Edit operations indicate implementation
        if event_type == "Edit" or event_type == "edit":
            if any(word in claim_lower for word in ["implement", "fix", "add", "create"]):
                return True, f"Verified via: {event_type}"

        # Read/Glob operations indicate verification
        if event_type in ("Read", "Glob", "Grep"):
            if any(word in claim_lower for word in ["verify", "check", "test"]):
                return True, f"Verified via: {event_type}"

    return False, "No supporting tool events found"


def _detect_completion_claims(response_text: str) -> list[tuple[str, int]]:
    """Detect completion claims in response text.

    Returns list of (matched_pattern, match_start_position).
    """
    claims = []
    for pattern in COMPLETION_PATTERNS:
        for match in pattern.finditer(response_text):
            claims.append((match.group(), match.start()))
    return claims


def _check_claim_verified(claim: str, events: list[dict]) -> tuple[bool, str]:
    """Check if a claim has been verified.

    Returns (is_verified, evidence_message).
    """
    # Check against tool events
    verified, msg = _check_completion_claim_with_events(claim, events)
    if verified:
        return True, msg

    # Check for explicit verification language
    verification_indicators = [
        "ran ",
        "tested",
        "verified",
        "confirmed",
        "pytest",
        "python -m",
        "node test",
    ]
    for indicator in verification_indicators:
        if indicator in claim.lower():
            return False, f"Claim mentions '{indicator}' but no verification evidence found"

    return False, "Claim not verified by tool events"


def main() -> None:
    """PostToolUse hook entry point."""
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        print("{}")
        sys.exit(0)

    try:
        raw_input = raw_input.lstrip("\ufeff")
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        print("{}")
        sys.exit(0)

    response_text = _get_response_text(data)
    if not response_text:
        print("{}")
        sys.exit(0)

    # Detect completion claims
    claims = _detect_completion_claims(response_text)
    if not claims:
        # No completion claims
        print("{}")
        sys.exit(0)

    # Get tool events for verification
    events = _get_tool_events(data)
    session = _get_session_context(data)

    # Track unverified claims
    unverified: list[str] = []
    for claim, _ in claims:
        verified, msg = _check_claim_verified(claim, events)
        if not verified:
            unverified.append(f"{claim}: {msg}")

    # If any unverified claims, block with evidence requirement
    if unverified:
        context_msg = "; ".join(unverified[:3])  # Limit to first 3
        output = {
            "decision": "block",
            "reason": (
                f"Completion claim(s) require verification: {context_msg}. "
                "Provide runtime evidence (test output, command results) to confirm."
            ),
            "blocking_hook": "self_verification_gate.py",
            "claims": unverified,
            "session": session,
        }
        print(json.dumps(_normalize_stdout(output)))
        sys.exit(2)

    # All claims verified
    print("{}")
    sys.exit(0)


if __name__ == "__main__":
    main()
