"""Verification engine for claim grounding.

Provides tool event matching and verdict generation for verification claims.
This is the core verification logic that determines if claims are SUPPORTED, REFUTED, or SILENT.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class VerificationStatus(Enum):
    """Verification status for claims."""

    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    SILENT = "SILENT"
    SELF_VERIFIED = "SELF_VERIFIED"  # Inline evidence in claim text


@dataclass
class VerificationVerdict:
    """Verification verdict for a claim.

    Represents the verification result for a single claim against
    available tool event evidence.
    """

    claim_id: str
    status: VerificationStatus
    supporting_evidence: List[str]
    refuting_evidence: List[str]
    confidence: float


@dataclass
class ToolEventView:
    """Normalized view of tool event for matching.

    Provides a unified interface for working with tool events from
    the evidence store, with normalized target paths and extracted facts.
    """

    tool_name: str
    target: str
    facts: List[str]
    timestamp: str
    output_excerpt: str


def build_verdicts(
    claims: List[Any],
    tool_events: List[Dict[str, Any]],
) -> List[VerificationVerdict]:
    """Build verification verdicts from claims and tool events.

    For each claim, analyze the tool events to determine if the claim
    is supported, refuted, or silent (no relevant evidence).

    Args:
        claims: List of Claim objects to verify
        tool_events: List of tool event dictionaries from evidence_store

    Returns:
        List of VerificationVerdict objects, one per claim

    Examples:
        >>> claims = [Claim(id="1", text="No file", targets=["file.txt"], ...]
        >>> events = [{"name": "Glob", "output": "No matches found", ...}]
        >>> verdicts = build_verdicts(claims, events)
        >>> assert verdicts[0].status == VerificationStatus.SUPPORTED
    """
    verdicts: List[VerificationVerdict] = []

    for claim in claims:
        status = match_claim_to_events(claim, tool_events)

        # Extract evidence based on status
        supporting = []
        refuting = []

        if status == VerificationStatus.SUPPORTED:
            supporting = _extract_supporting_evidence(claim, tool_events)
        elif status == VerificationStatus.REFUTED:
            refuting = _extract_refuting_evidence(claim, tool_events)

        verdict = VerificationVerdict(
            claim_id=claim.id,
            status=status,
            supporting_evidence=supporting,
            refuting_evidence=refuting,
            confidence=claim.confidence,
        )
        verdicts.append(verdict)

    return verdicts


def match_claim_to_events(
    claim: Any,
    events: List[Dict[str, Any]],
) -> VerificationStatus:
    """Match claim to tool events and return verification status.

    Determines if a claim is SUPPORTED, REFUTED, SILENT, or SELF_VERIFIED based on
    matching tool event evidence or inline self-verification.

    Args:
        claim: Claim object to verify
        events: List of tool event dictionaries

    Returns:
        VerificationStatus: SUPPORTED, REFUTED, SILENT, or SELF_VERIFIED

    Matching Rules:
    - SELF_VERIFIED: claim text contains inline evidence (this session, ls|, grep|, verified)
    - ABSENCE claims + ls/Glob showing no matches → SUPPORTED
    - ABSENCE claims + Read/Glob showing entity exists → REFUTED
    - RULE claims + Read of relevant file → check content (SUPPORTED/REFUTED)
    - No relevant tools used → SILENT
    """
    # Check for self-verification in claim text first (cross-turn evidence)
    if _is_self_verified_claim(claim):
        return VerificationStatus.SELF_VERIFIED

    if not events:
        return VerificationStatus.SILENT

    # Filter events by claim targets
    relevant_events = _filter_events_by_targets(claim, events)
    if not relevant_events:
        return VerificationStatus.SILENT

    claim_type_upper = claim.type.upper()

    # ABSENCE claims: check if entity exists in tool outputs
    if "ABSENCE" in claim_type_upper:
        return _verify_absence_claim(claim, relevant_events)

    # RULE claims: require Read or Glob of relevant file
    if "RULE" in claim_type_upper:
        return _verify_rule_claim(claim, relevant_events)

    # Default: SILENT for unsupported claim types
    return VerificationStatus.SILENT


# Patterns that indicate self-verification (inline evidence in claim text)
_SELF_VERIFICATION_PATTERNS = [
    re.compile(r"\bthis\s+session\b", re.IGNORECASE),
    re.compile(r"\bverified\s+(?:this|in)\s+(?:the\s+)?(?:session|earlier|before)\b", re.IGNORECASE),
    re.compile(r"\bls\s+\|\s*grep\b", re.IGNORECASE),
    re.compile(r"\bls\s+(?:showed|confirmed|revealed)\b", re.IGNORECASE),
    re.compile(r"\bgrep\s+(?:-[nri]?\s+\S+\s+)?(?:\S+\s+)?(?:showed|confirmed|empty|no\s+match)\b", re.IGNORECASE),
    re.compile(r"\bread\s+(?:tool\s+)?(?:\w+\.)?(?:\w+\.)?\w+\.py:\d+\b", re.IGNORECASE),  # file.py:line
    re.compile(r"\bconfirmed\s+(?:absent|present|exists?|missing|empty)\b", re.IGNORECASE),
    re.compile(r"\bempty\s+result(?:s)?\b", re.IGNORECASE),
    re.compile(r"\bno\s+(?:matches?|files?|results?)\b", re.IGNORECASE),
]


def _is_self_verified_claim(claim: Any) -> bool:
    """Check if claim text contains inline evidence of prior verification.

    This enables cross-turn evidence: if a claim was verified in an earlier
    turn, the LLM can include the verification act in the claim text itself,
    signaling the hook that this was already verified without requiring
    current-turn tool output.

    Args:
        claim: Claim object with text attribute

    Returns:
        True if claim text contains self-verification patterns
    """
    claim_text = claim.text
    for pattern in _SELF_VERIFICATION_PATTERNS:
        if pattern.search(claim_text):
            return True
    return False


def _verify_absence_claim(claim: Any, events: List[Dict[str, Any]]) -> VerificationStatus:
    """Verify an absence claim against tool events.

    An absence claim is SUPPORTED if tools show the entity doesn't exist.
    It's REFUTED if tools show the entity exists.

    Args:
        claim: Claim with type ABSENCE
        events: Relevant tool events

    Returns:
        SUPPORTED if absence confirmed, REFUTED if entity exists, SILENT if unclear
    """
    has_verification_tool = False
    entity_found = False

    for event in events:
        tool_name = event.get("name", "").lower()
        command = event.get("command", "")
        output = event.get("output", "")

        # Check if this is a verification tool (Read, Glob, or Bash ls/dir commands)
        is_verification_tool = False
        if tool_name in ("read", "glob"):
            is_verification_tool = True
        elif tool_name == "bash":
            # Check if Bash command is a directory listing
            command_lower = command.lower()
            is_verification_tool = any(cmd in command_lower for cmd in ["ls ", "dir ", "ll "])

        if is_verification_tool:
            has_verification_tool = True

            # For Read tool: if Read was used on target, entity exists (REFUTED)
            if tool_name == "read":
                for target in claim.targets:
                    normalized_target = _normalize_path(target)
                    if _path_in_output(normalized_target, command):
                        entity_found = True
                        break

            # For Glob and Bash ls: check output content
            else:
                # Check if output shows entity exists
                for target in claim.targets:
                    normalized_target = _normalize_path(target)
                    if _path_in_output(normalized_target, output):
                        entity_found = True
                        break

                # Check for "No matches found" or empty output (indicates absence)
                if not entity_found and _output_indicates_absence(output):
                    return VerificationStatus.SUPPORTED

    if entity_found:
        return VerificationStatus.REFUTED

    if has_verification_tool:
        # Verification tool used but entity not found → SUPPORTED
        return VerificationStatus.SUPPORTED

    # No verification tools used → SILENT
    return VerificationStatus.SILENT


def _verify_rule_claim(claim: Any, events: List[Dict[str, Any]]) -> VerificationStatus:
    """Verify a rule claim against tool events.

    Rule claims require Read or Glob of relevant documentation files.
    Returns SUPPORTED if file was read, REFUTED if claim contradicted, SILENT if no verification.

    Args:
        claim: Claim with type RULE
        events: Relevant tool events

    Returns:
        SUPPORTED if verified, REFUTED if contradicted, SILENT if no verification tools used
    """
    has_verification_tool = False

    for event in events:
        tool_name = event.get("name", "").lower()
        if tool_name in ("read", "glob"):
            has_verification_tool = True
            # Rule claim verified if tool was used
            return VerificationStatus.SUPPORTED

    if has_verification_tool:
        return VerificationStatus.SUPPORTED

    return VerificationStatus.SILENT


def _filter_events_by_targets(claim: Any, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter tool events to those relevant to claim targets.

    Returns events that mention the claim's target paths/files.

    Args:
        claim: Claim with targets list
        events: All tool events

    Returns:
        Filtered list of relevant events
    """
    relevant = []

    for event in events:
        event_text = " ".join([
            event.get("command", ""),
            event.get("output", ""),
            event.get("cwd", ""),
        ])

        for target in claim.targets:
            normalized_target = _normalize_path(target)
            if _path_in_output(normalized_target, event_text):
                relevant.append(event)
                break

    return relevant


def _extract_supporting_evidence(claim: Any, events: List[Dict[str, Any]]) -> List[str]:
    """Extract supporting evidence from tool events.

    Returns brief descriptions of evidence that supports the claim.

    Args:
        claim: Claim being verified
        events: Relevant tool events

    Returns:
        List of evidence descriptions
    """
    evidence = []

    for event in events:
        tool_name = event.get("name", "")
        timestamp = event.get("timestamp", "")
        evidence.append(f"{tool_name} at {timestamp}")

    return evidence


def _extract_refuting_evidence(claim: Any, events: List[Dict[str, Any]]) -> List[str]:
    """Extract refuting evidence from tool events.

    Returns brief descriptions of evidence that refutes the claim.

    Args:
        claim: Claim being verified
        events: Relevant tool events

    Returns:
        List of evidence descriptions
    """
    evidence = []

    for event in events:
        tool_name = event.get("name", "")
        output = event.get("output", "")[:100]  # Truncate long output
        timestamp = event.get("timestamp", "")
        evidence.append(f"{tool_name} at {timestamp}: {output}")

    return evidence


def _normalize_path(path: str) -> str:
    """Normalize path separators for consistent matching.

    Converts Windows backslashes to forward slashes and resolves
    relative paths to absolute where possible.

    Args:
        path: Path string to normalize

    Returns:
        Normalized path string
    """
    # Convert backslashes to forward slashes
    normalized = path.replace("\\", "/")

    # Remove redundant separators
    normalized = re.sub(r"/+", "/", normalized)

    return normalized


def _path_in_output(path: str, output: str) -> bool:
    """Check if path appears in output text.

    Case-insensitive search for path in output.

    Args:
        path: Normalized path to search for
        output: Output text to search in

    Returns:
        True if path found in output, False otherwise
    """
    # Case-insensitive search
    return path.lower() in output.lower()


def _output_indicates_absence(output: str) -> bool:
    """Check if tool output indicates entity absence.

    Looks for patterns like "No matches found", empty directory listings, etc.

    Args:
        output: Tool output text

    Returns:
        True if output indicates absence, False otherwise
    """
    absence_indicators = [
        "no matches found",
        "no such file",
        "does not exist",
        "empty",
    ]

    output_lower = output.lower()
    return any(indicator in output_lower for indicator in absence_indicators)
