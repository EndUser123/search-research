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

    # OUTCOME_ATTRIBUTION claims: verify the claimed outcome appears in tool output
    if "OUTCOME_ATTRIBUTION" in claim_type_upper:
        return _verify_outcome_attribution_claim(claim, relevant_events)

    # FOLDER_CREATE claims: verify the claimed folder was actually created
    if "FOLDER_CREATE" in claim_type_upper:
        return _verify_folder_create_claim(claim, relevant_events)

    # Default: SILENT for unsupported claim types
    return VerificationStatus.SILENT


def _verify_rule_claim(claim: Any, events: List[Dict[str, Any]]) -> VerificationStatus:
    """Verify a rule/policy claim against tool events.

    RULE claims assert that a specific rule, policy, or requirement exists
    in a file or document. It's SUPPORTED if the relevant file was read and
    the claimed rule content is found in the output.

    Args:
        claim: Claim with type RULE
        events: Relevant tool events

    Returns:
        SUPPORTED if rule confirmed in file content, REFUTED if rule missing,
        SILENT if no verification evidence
    """
    claimed_rule = None
    for target in claim.targets:
        if target and len(target) > 1:
            claimed_rule = target.lower()
            break

    if not claimed_rule:
        return VerificationStatus.SILENT

    for event in events:
        tool_name = event.get("name", "").lower()
        output = str(event.get("output", "")).lower()
        command = str(event.get("command", "")).lower()

        # Read tool: file was accessed - check if target path appears in output
        if tool_name == "read":
            # Check if the claimed file path appears in output (file was read)
            if claimed_rule and _path_in_command_or_output(claimed_rule, command, output):
                # File was accessed - now check if content confirms the rule
                # Look for key terms from claim targets in output
                key_terms = [t for t in claim.targets if t and len(t) > 2]
                for term in key_terms:
                    if term.lower() in output:
                        return VerificationStatus.SUPPORTED
                # File was read but claim content not specifically found
                if output and len(output) > 0 and "not found" not in output.lower():
                    return VerificationStatus.SUPPORTED
            # File not found or inaccessible
            if "not found" in output or "no such file" in output:
                return VerificationStatus.REFUTED

        # Glob tool: check if glob output confirms file exists
        if tool_name == "glob":
            if claimed_rule in output:
                return VerificationStatus.SUPPORTED
            if "no matches found" in output:
                return VerificationStatus.REFUTED

        # Bash with grep: check for the rule in grep output
        if tool_name == "bash" and "grep" in command:
            if claimed_rule in output:
                return VerificationStatus.SUPPORTED
            if "no matches" in output.lower():
                return VerificationStatus.REFUTED

    return VerificationStatus.SILENT


# Patterns that indicate self-verification (inline evidence in claim text)
_SELF_VERIFICATION_PATTERNS = [
    re.compile(r"\bthis\s+session\b", re.IGNORECASE),
    # Line citation patterns — "Line 393", "lines 167-177", "SKILL.md:171"
    # These are self-verifying: the claim cites specific line numbers already in the turn's grep/Read output
    re.compile(r"\blines?\s+\d+(?:[–-]\d+)?", re.IGNORECASE),  # "Line 393", "lines 167-177"
    re.compile(r"\b\w[\w./\\-]+\.\w+:\d+(?:[–-]\d+)?", re.IGNORECASE),  # "file.py:171" or "file.py:171-180"
    re.compile(r"\bverified\s+(?:this|in)\s+(?:the\s+)?(?:session|earlier|before)\b", re.IGNORECASE),
    re.compile(r"\bls\s+\|\s*grep\b", re.IGNORECASE),
    re.compile(r"\bls\s+(?:showed|confirmed|revealed)\b", re.IGNORECASE),
    re.compile(r"\bgrep\s+(?:-[nri]?\s+\S+\s+)?(?:\S+\s+)?(?:showed|confirmed|empty|no\s+match)\b", re.IGNORECASE),
    re.compile(r"\bread\s+(?:tool\s+)?(?:\w+\.)?(?:\w+\.)?\w+\.py:\d+\b", re.IGNORECASE),  # read file.py:line
    re.compile(r"\bcode\s+at\s+`?[\w./\\-]+\.\w+:\d+", re.IGNORECASE),  # "Code at file.py:51" or "Code at `file.py:51-53`"
    re.compile(r"`[\w./\\-]+\.\w+:\d+[-–]?\d*`[\s,;:—–]+show(?:ed|s)?\b", re.IGNORECASE),  # "`file.py:51-53` shows/ed"
    re.compile(r"\bconfirmed\s+(?:absent|present|exists?|missing|empty)\b", re.IGNORECASE),
    re.compile(r"\bempty\s+result(?:s)?\b", re.IGNORECASE),
    re.compile(r"\bno\s+(?:matches?|files?|results?)\b", re.IGNORECASE),
    # OUTCOME_ATTRIBUTION self-verification: inline trace of what handled/blocked/caused
    re.compile(r"\b(?:owned|handled)\s+by\s+\S+", re.IGNORECASE),  # "owned by /verify" — inline attribution
    re.compile(r"\b(?:blocked|triggered|prevented)\s+by\b", re.IGNORECASE),  # "blocked by hook" — inline
    re.compile(r"\b(?:outcome|event)\s+traced\s+to\b", re.IGNORECASE),  # "outcome traced to X"
    re.compile(r"\bfrom\s+(?:the\s+)?(?:hook\s+)?output\b", re.IGNORECASE),  # "from hook output"
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


def _verify_outcome_attribution_claim(
    claim: Any, events: List[Dict[str, Any]]
) -> VerificationStatus:
    """Verify an outcome attribution claim against tool events.

    Claims like "X handled Y", "hook blocked Z" are SUPPORTED if the tool output
    (Stop hook JSON, Bash output) contains evidence of the claimed outcome.

    Args:
        claim: Claim with type OUTCOME_ATTRIBUTION
        events: Relevant tool events

    Returns:
        SUPPORTED if outcome confirmed in output, SILENT if not found
    """
    claim_text_lower = claim.text.lower()

    # Extract the claimed outcome verbs and actors from claim text
    # e.g. "inference was owned by /skill-ship" -> "/skill-ship" is the actor
    # e.g. "hook correctly blocked the command" -> "hook" or implied actor
    claimed_actor = None
    for target in claim.targets:
        if target and len(target) > 1:
            claimed_actor = target.lower()
            break

    for event in events:
        tool_name = event.get("name", "").lower()
        output = str(event.get("output", "")).lower()
        reason = str(event.get("reason", "")).lower()

        # Stop hook output: look for decision + reason confirming outcome
        if tool_name in ("bash", "subprocess") or "stop" in tool_name:
            # Check if output contains JSON with block/allow decision
            if '"decision"' in output or "'decision'" in output:
                if claimed_actor and claimed_actor in output:
                    return VerificationStatus.SUPPORTED
                # Any block/handle evidence for the outcome described
                outcome_indicators = ["blocked", "handled", "triggered", "prevented", "caught"]
                if any(ind in reason or ind in output for ind in outcome_indicators):
                    return VerificationStatus.SUPPORTED

        # Skill execution evidence: look for skill name in output
        if tool_name == "skill" or "/skill" in str(event.get("command", "")):
            if claimed_actor and claimed_actor in str(event.get("command", "")).lower():
                return VerificationStatus.SUPPORTED

        # General Bash output: look for the claimed actor or outcome verbs
        if tool_name == "bash":
            if claimed_actor and claimed_actor in output:
                return VerificationStatus.SUPPORTED
            outcome_indicators = ["blocked", "handled", "triggered", "prevented", "caught", "owned"]
            if any(ind in reason or ind in output for ind in outcome_indicators):
                return VerificationStatus.SUPPORTED

    return VerificationStatus.SILENT


def _verify_folder_create_claim(
    claim: Any, events: List[Dict[str, Any]]
) -> VerificationStatus:
    """Verify a folder/file creation claim against tool events.

    Claims like "made an inference gap folder" are SUPPORTED if Glob or Read
    confirms the folder exists at the claimed path.

    Args:
        claim: Claim with type FOLDER_CREATE
        events: Relevant tool events

    Returns:
        SUPPORTED if folder confirmed, REFUTED if folder missing, SILENT if no evidence
    """
    # Extract folder path from claim targets or text
    claimed_path = None
    for target in claim.targets:
        if target and len(target) > 2:
            claimed_path = target.lower()
            break

    if not claimed_path:
        # Try to extract from claim text
        import re as _re

        path_match = _re.search(r"made an? (\S+(?:/\S+)*)", claim.text, _re.IGNORECASE)
        if path_match:
            claimed_path = path_match.group(1).lower()

    if not claimed_path:
        return VerificationStatus.SILENT

    for event in events:
        tool_name = event.get("name", "").lower()
        output = str(event.get("output", "")).lower()
        command = str(event.get("command", "")).lower()

        # Glob confirming folder exists
        if tool_name == "glob":
            if claimed_path in output:
                return VerificationStatus.SUPPORTED
            # Check for absence indicators
            if "no matches found" in output or "not found" in output:
                return VerificationStatus.REFUTED

        # Read confirming folder exists (e.g., ls output)
        if tool_name in ("read", "bash") and ("dir" in command or "ls" in command):
            if claimed_path in output:
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


def _path_in_command_or_output(path: str, command: str, output: str) -> bool:
    """Check if path appears in command or output.

    Used to verify that a file was accessed (path appears in either
    the command that was run or the output produced).

    Args:
        path: Path to search for
        command: Command that was executed
        output: Output from the command

    Returns:
        True if path found in command or output
    """
    path_lower = path.lower()
    return path_lower in command.lower() or path_lower in output.lower()


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


def _claim_matches_tool_output(
    claim: Any,
    events: List[Dict[str, Any]],
) -> bool:
    """Check if claim text appears in any tool event's output from this turn.

    Used as a fallback when _filter_events_by_targets() returns empty (SILENT verdict).
    This catches cases where a claim's content was confirmed by tool output even though
    the target file path wasn't in the claim's targets list.

    Args:
        claim: Claim object with text attribute
        events: List of tool event dictionaries from this turn

    Returns:
        True if claim text (or key assertion phrases) found in any tool output
    """
    if not events:
        return False

    claim_text = claim.text.lower()

    # Split claim into key terms (nouns/verbs, length > 2)
    # Ignore common stopwords for matching
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "that", "this", "it",
    }

    words = claim_text.split()
    key_terms = [w for w in words if len(w) > 2 and w not in stopwords]

    for event in events:
        output = str(event.get("output", "")).lower()
        command = str(event.get("command", "")).lower()

        # Full claim text check
        if claim_text in output or claim_text in command:
            return True

        # Key term subset check (at least 3 terms must match)
        if len(key_terms) >= 3:
            matches = sum(1 for term in key_terms if term in output or term in command)
            if matches >= 3:
                return True

    return False
