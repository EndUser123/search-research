"""Adapter layer between hooks and verification engine.

Provides utilities for hooks to use the verification engine while
preserving hook-specific patterns and turn scoping.

Usage in hooks:
    from verification.hook_adapter import (
        create_claim_from_match,
        verify_claim_with_engine,
        load_turn_scoped_events,
    )
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from verification.claims import Claim

# Import from verification engine
from verification.engine import VerificationStatus, match_claim_to_events

# Setup paths
HOOKS_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = HOOKS_DIR / "state" / "turn_markers"

_logger = logging.getLogger("verification.adapter")


@dataclass
class ClaimMatch:
    """Represents a detected claim match from hook pattern detection."""

    matched_text: str
    claim_type: str
    targets: list[str]
    confidence: float = 0.9


def create_claim_from_match(match: ClaimMatch, claim_id: str = "") -> Claim:
    """Create a Claim object from a hook-detected match.

    Args:
        match: ClaimMatch from hook pattern detection
        claim_id: Optional ID (generated if empty)

    Returns:
        Claim object suitable for engine verification
    """
    import uuid

    return Claim(
        id=claim_id or str(uuid.uuid4())[:8],
        text=match.matched_text,
        targets=match.targets,
        type=match.claim_type,
        confidence=match.confidence,
        risk_domain="verification",
        has_hedge=False,
    )


def verify_claim_with_engine(
    claim: Claim,
    tool_events: list[dict[str, Any]],
) -> VerificationStatus:
    """Verify a claim against tool events using the engine.

    Args:
        claim: Claim to verify
        tool_events: List of tool event dictionaries

    Returns:
        VerificationStatus (SUPPORTED, REFUTED, or SILENT)
    """
    return match_claim_to_events(claim, tool_events)


def verify_claims_batch(
    claims: list[Claim],
    tool_events: list[dict[str, Any]],
) -> dict[str, VerificationStatus]:
    """Verify multiple claims against tool events.

    Args:
        claims: List of claims to verify
        tool_events: List of tool event dictionaries

    Returns:
        Dict mapping claim.id to VerificationStatus
    """
    results = {}
    for claim in claims:
        results[claim.id] = match_claim_to_events(claim, tool_events)
    return results


# --- Turn Scoping Utilities ---


def _safe_scope_key(session_id: str, terminal_id: str) -> str:
    """Create safe filename key from session and terminal IDs."""

    def _safe(s: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_.-]", "_", (s or "unknown").strip())

    return f"{_safe(session_id)}__{_safe(terminal_id)}"


def read_turn_marker(session_id: str, terminal_id: str) -> int | None:
    """Read turn_start_event_id from marker file.

    Args:
        session_id: Session ID
        terminal_id: Terminal ID for multi-terminal isolation

    Returns:
        Turn start event ID, or None if marker not found
    """
    path = STATE_DIR / f"turn_start_{_safe_scope_key(session_id, terminal_id)}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        val = data.get("turn_start_event_id")
        if val is not None:
            return int(val)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        _logger.warning("turn marker read failed: %s: %s", path, exc)
    return None


def load_turn_scoped_events(
    session_id: str,
    terminal_id: str,
    all_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Filter events to only those from the current turn.

    Args:
        session_id: Session ID
        terminal_id: Terminal ID for multi-terminal isolation
        all_events: All tool events from the session

    Returns:
        Filtered list of events from current turn only
    """
    min_id = read_turn_marker(session_id, terminal_id)
    if min_id is None:
        return all_events  # Fallback: no marker, return all

    return [e for e in all_events if int(e.get("id", 0)) > min_id]


# --- Convenience Functions for Hook Migration ---


def check_verification_status(
    claim_type: str,
    matched_text: str,
    targets: list[str],
    tool_events: list[dict[str, Any]],
    confidence: float = 0.9,
) -> VerificationStatus:
    """One-shot verification check for hooks.

    Combines claim creation and verification in a single call.

    Args:
        claim_type: Type of claim (string like "NEGATIVE_EXISTENCE" or ClaimType enum)
        matched_text: The matched text from pattern detection
        targets: List of target entities (files, URLs, etc.)
        tool_events: Tool events to verify against
        confidence: Confidence level for the claim

    Returns:
        VerificationStatus (SUPPORTED = verified, REFUTED = contradicted, SILENT = no evidence)
    """
    # Accept both string and ClaimType enum for type safety
    from verification.engine import ClaimType

    if isinstance(claim_type, ClaimType):
        claim_type_str = claim_type.value
    else:
        claim_type_str = claim_type

    match = ClaimMatch(
        matched_text=matched_text,
        claim_type=claim_type_str,
        targets=targets,
        confidence=confidence,
    )
    claim = create_claim_from_match(match)
    return verify_claim_with_engine(claim, tool_events)


def is_verified(
    claim_type: str,
    matched_text: str,
    targets: list[str],
    tool_events: list[dict[str, Any]],
) -> bool:
    """Check if a claim is verified by tool events.

    Convenience function that returns True if SUPPORTED.

    Args:
        claim_type: Type of claim (string like "NEGATIVE_EXISTENCE" or ClaimType enum)
        matched_text: The matched text from pattern detection
        targets: List of target entities
        tool_events: Tool events to verify against

    Returns:
        True if claim is SUPPORTED by tool events
    """
    status = check_verification_status(claim_type, matched_text, targets, tool_events)
    return status == VerificationStatus.SUPPORTED
