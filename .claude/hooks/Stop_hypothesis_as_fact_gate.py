#!/usr/bin/env python3
"""Stop hook for hypothesis-as-fact claim validation.

This hook implements Phase 2 of the verification claim grounding system.
It uses the unified verification engine to detect confident claims about entities
without verifying those entities were actually examined in tool output this turn.

Core requirements from TASK-009:
1. Refactor Phase 1 gate to use verification engine from TASK-008
2. Use extract_claims() from verification/claims.py
3. Use build_verdicts() from verification/engine.py
4. Entity matching (Phase 2: ABSENCE, RULE, PRESENCE, SYSTEM claims)
5. Warn or block per HYPOTHESIS_AS_FACT_GATE_MODE
6. Log every decision with claim text and tool events considered

CRITICAL: Path normalization MUST normalize separators (convert \\ to /) and
resolve relative paths to absolute before comparison. This prevents Windows vs
Unix path false-negatives.

Example: C:\foo\bar should match C:/foo/bar in tool events.

SCOPING NOTE: Phase 2 gate is terminal-scoped, not turn-scoped.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

# Import verification engine from TASK-008
try:
    from verification import Claim, build_verdicts, extract_claims
    from verification.engine import VerificationStatus
except ImportError:
    # Fallback if module not available
    extract_claims = None  # type: ignore
    build_verdicts = None  # type: ignore
    Claim = None  # type: ignore
    VerificationStatus = None  # type: ignore

# Import evidence store from TASK-001
try:
    from evidence_store import load_tool_events_for_context
except ImportError:
    load_tool_events_for_context = None  # type: ignore


def _get_gate_enabled() -> bool:
    """Get gate enabled flag from environment."""
    return os.environ.get("HYPOTHESIS_AS_FACT_GATE_ENABLED", "true").lower() == "true"


def _get_gate_mode() -> str:
    """Get gate mode from environment."""
    return os.environ.get("HYPOTHESIS_AS_FACT_GATE_MODE", "warn").lower()


# Logging configuration
LOG_DIR = Path(__file__).resolve().parent / "state" / "logs"
LOG_FILE = LOG_DIR / "hypothesis_as_fact_gate.jsonl"


def _should_block_claim(claim: Claim, verdict: Any) -> bool:
    """Determine if a claim should be blocked based on verification verdict.

    Args:
        claim: The Claim object to evaluate
        verdict: VerificationVerdict from build_verdicts

    Returns:
        True if claim should be blocked (ungrounded confident claim)
    """
    # CONVENTION claims are never hedged-exempt.
    # Fabricated organizational norms deliberately use hedge-sounding words
    # ("typically", "usually", "often") to invent policies that don't exist.
    # Example: "hooks often go undocumented" — "often" sounds like a hedge,
    # but the underlying claim (there is a norm of not documenting hooks) is invented.
    #
    # NOTE: claims.py uppercases claim types on conversion (RawClaim → Claim),
    # so the live path yields claim.type == "CONVENTION" while tests using Mock
    # may set "convention" (lowercase). Compare case-insensitively.
    claim_type_str = (getattr(claim, "type", None) or "").upper()
    is_convention = claim_type_str == "CONVENTION"

    # Hedged claims pass without evidence (except CONVENTION type)
    if claim.has_hedge and not is_convention:
        return False

    # Low confidence claims pass (except CONVENTION type).
    # For CONVENTION claims, low confidence is an artifact of hedge word detection
    # reducing the score in _calculate_confidence — the same hedge words that are
    # part of the fabrication pattern ("typically go undocumented") are not genuine
    # epistemic modifiers signalling uncertainty.
    if claim.confidence < 0.7 and not is_convention:
        return False

    # Check verification status
    # SUPPORTED: Evidence found → pass
    # REFUTED: Evidence contradicts → may still pass (not blocked here)
    # SILENT: No relevant evidence → block if confident
    if verdict.status == VerificationStatus.SUPPORTED:
        return False  # Grounded in tool events

    if verdict.status == VerificationStatus.REFUTED:
        return False  # Has some evidence, even if contradictory

    # SILENT status + confident claim = ungrounded
    return True


def _log_decision(
    session_id: str,
    terminal_id: str,
    claim: Claim,
    verdict: Any,
    tool_event_ids: list[int],
    outcome: str,
    reason: str = "",
) -> None:
    """Log gate decision for observability and tuning.

    Args:
        session_id: Session identifier
        terminal_id: Terminal identifier
        claim: The Claim that was evaluated
        verdict: VerificationVerdict from build_verdicts
        tool_event_ids: IDs of tool events considered
        outcome: Decision outcome (block/warn/pass)
        reason: Human-readable reason for decision
    """
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Sanitize claim text for logging (PII protection)
        claim_text_sanitized = claim.text[:200]
        # Redact email-like patterns
        claim_text_sanitized = re.sub(
            r"[\w.+-]+@[\w-]+\.[\w.]+", "[REDACTED]", claim_text_sanitized
        )
        # Redact home directory paths
        claim_text_sanitized = re.sub(
            r"/\b(?:home|Users)\b/[\w-]+", "/[REDACTED]", claim_text_sanitized
        )

        log_entry = {
            "session_id": session_id,
            "terminal_id": terminal_id,
            "claim_id": claim.id,
            "claim_text": claim_text_sanitized,
            "claim_type": claim.type,
            "targets": claim.targets,
            "confidence": claim.confidence,
            "has_hedge": claim.has_hedge,
            "risk_domain": claim.risk_domain,
            "verification_status": str(verdict.status),
            "supporting_evidence": verdict.supporting_evidence,
            "refuting_evidence": verdict.refuting_evidence,
            "tool_event_ids": tool_event_ids,
            "outcome": outcome,
            "reason": reason,
        }

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, separators=(",", ":")) + "\n")
    except (OSError, ValueError):
        # Fail silently - logging should never break the gate
        pass


def _strip_non_assertion_contexts(text: str) -> str:
    """Strip markdown contexts that contain examples/quotes, not first-person assertions.

    Removes fenced code blocks, inline code, table rows, and blockquotes before
    claim detection to prevent false positives when the response documents or
    quotes bad behavior patterns rather than asserting them.
    """
    # Strip fenced code blocks (``` ... ```)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Strip inline code spans (`...`)
    text = re.sub(r"`[^`]+`", "", text)
    # Strip markdown table rows (lines starting with |)
    text = re.sub(r"^\|.*\|.*$", "", text, flags=re.MULTILINE)
    # Strip blockquotes (lines starting with >)
    text = re.sub(r"^>.*$", "", text, flags=re.MULTILINE)
    return text


def run(data: dict[str, Any]) -> dict[str, Any]:
    """Stop hook entrypoint for hypothesis-as-fact validation.

    Args:
        data: Hook data dictionary containing:
            - session_id: Session UUID
            - terminal_id: Terminal identifier
            - response_text: Response text to analyze

    Returns:
        Dictionary with:
            - allow: bool (True to allow stop, False to block)
            - reason: str (explanation for decision)
    """
    # Check if gate is enabled (read dynamically)
    if not _get_gate_enabled():
        return {"allow": True, "reason": "Gate disabled"}

    # Extract required fields
    session_id = data.get("session_id", "")
    terminal_id = data.get("terminal_id", "")
    response_text = data.get("response_text", "")

    # Validate inputs
    if not session_id:
        return {"allow": True, "reason": "No session_id provided"}

    if not terminal_id:
        return {"allow": True, "reason": "No terminal_id provided"}

    if not response_text or len(response_text.strip()) < 20:
        return {"allow": True, "reason": "Response too short to analyze"}

    # Import verification engine if available
    if (
        extract_claims is None
        or build_verdicts is None
        or Claim is None
        or VerificationStatus is None
    ):
        return {"allow": True, "reason": "Verification engine not available"}

    # Import evidence store if available
    if load_tool_events_for_context is None:
        return {"allow": True, "reason": "Evidence store not available"}

    try:
        # Strip non-assertion contexts before claim detection.
        # Quoted examples, code blocks, and table rows contain patterns
        # that look like mechanism claims but are documenting bad behavior,
        # not asserting it. Stripping prevents false positives on responses
        # that explain or quote the very patterns being guarded against.
        analysis_text = _strip_non_assertion_contexts(response_text)

        # Extract claims using verification engine (TASK-007)
        claims = extract_claims(analysis_text)

        if not claims:
            return {"allow": True, "reason": "No claims detected"}

        # Load tool events for context (terminal-scoped from TASK-001)
        tool_events = load_tool_events_for_context(
            session_id=session_id,
            terminal_id=terminal_id,
            limit=500,
        )

        # Extract tool event IDs for logging
        tool_event_ids = [event.get("id", 0) for event in tool_events]

        # Build verification verdicts using engine (TASK-008)
        verdicts = build_verdicts(claims, tool_events)

        # Evaluate each claim against its verdict
        ungrounded_claims = []
        claim_verdict_pairs = []

        for claim, verdict in zip(claims, verdicts):
            claim_verdict_pairs.append((claim, verdict))
            if _should_block_claim(claim, verdict):
                ungrounded_claims.append(claim)

        # If no ungrounded claims, allow
        if not ungrounded_claims:
            # Log all claims as passed
            for claim, verdict in claim_verdict_pairs:
                _log_decision(
                    session_id=session_id,
                    terminal_id=terminal_id,
                    claim=claim,
                    verdict=verdict,
                    tool_event_ids=tool_event_ids,
                    outcome="pass",
                    reason=f"Claim {verdict.status.value}: grounded in tool events or hedged",
                )
            return {"allow": True, "reason": "All claims grounded or hedged"}

        # Build block/warn message
        claim_summary = "\n".join(
            [
                f"  - {claim.targets[0] if claim.targets else 'Unknown'}: {claim.text[:100]}..."
                for claim in ungrounded_claims[:3]  # Show first 3
            ]
        )

        if len(ungrounded_claims) > 3:
            claim_summary += f"\n  ... and {len(ungrounded_claims) - 3} more"

        reason = f"""UNGROUNDED CONFIDENT CLAIMS DETECTED

The following claims lack verification evidence in tool output:
{claim_summary}

Before claiming as fact, verify using:
  - Read tool for documentation claims
  - Glob or ls for filesystem claims
  - Grep for code behavior claims

To bypass for this turn: Add --allow-ungrounded-claims to your message
To disable enforcement: Set HYPOTHESIS_AS_FACT_GATE_ENABLED=false
"""

        # Log all blocked claims
        for claim, verdict in claim_verdict_pairs:
            if claim in ungrounded_claims:
                _log_decision(
                    session_id=session_id,
                    terminal_id=terminal_id,
                    claim=claim,
                    verdict=verdict,
                    tool_event_ids=tool_event_ids,
                    outcome="block" if _get_gate_mode() == "block" else "warn",
                    reason=f"Confident claim without grounding evidence ({verdict.status.value})",
                )

        # Apply mode (warn vs block) - read dynamically
        gate_mode = _get_gate_mode()
        if gate_mode == "block":
            return {"allow": False, "reason": reason}
        else:  # warn mode
            print(f"⚠️ {reason}", file=os.fdopen(1, "w", encoding="utf-8"))
            return {"allow": True, "reason": "Warning issued (warn mode)"}

    except Exception:
        # Fail open on errors to prevent blocking due to system failures
        return {"allow": True, "reason": "Gate error (fail-open)"}
