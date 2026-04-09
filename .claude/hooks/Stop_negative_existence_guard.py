#!/usr/bin/env python3
"""
Stop_negative_existence_guard.py - File/Resource Negative Existence Claim Guard
==============================================================================

Blocks responses claiming files, documentation, or resources don't exist
WITHOUT verification tools used THIS TURN.

WHY THIS EXISTS:
  AI agents claim "no X file", "X doesn't exist", "missing X" without checking
  with Read, Glob, Grep, or other verification tools. This creates hallucinated
  gap analysis that blocks legitimate work.

FAILURE MODE CAUGHT:
  "There's no documentation for feature X"
  -> No Read/Grep for documentation files THIS TURN.
  -> Guard blocks and demands verification.

TURN SCOPING (stale-data-immune):
  Uses the shared turn-scoped evidence helper to check only tool events from
  THIS turn (id > turn_start_event_id). Prevents "I verified 3 hours ago"
  stale evidence bypass and keeps spool fallback behavior consistent.

ALLOWLIST (obvious claims that don't need verification):
  - "no internet access", "no network", "offline" (capability statements)
  - "no configuration needed", "no config required" (domain knowledge)

COORDINATION (PreToolUse state sharing):
  Checks for file_existence_decision_{session_id}.json state file written by
  PreToolUse hooks to coordinate overwrite justification.

LIFECYCLE: Stop (blocking guard -- exits with code 2 to block)
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOKS_DIR / "state"
LOG_DIR = HOOKS_DIR / "state" / "logs"
sys.path.insert(0, str(HOOKS_DIR))

# --- Logging ----------------------------------------------------------------

LOG_DIR.mkdir(parents=True, exist_ok=True)

_logger = logging.getLogger("negative_existence_guard")
_handler = logging.FileHandler(LOG_DIR / "negative_existence_guard.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)


try:
    from turn_scoped_evidence import load_turn_scoped_events
    EVIDENCE_AVAILABLE = True
except ImportError as exc:
    EVIDENCE_AVAILABLE = False
    _logger.warning("evidence_store import failed: %s", exc)


# --- Patterns: Negative Existence Claims ------------------------------------

# Core negative existence patterns
NEGATIVE_EXISTENCE_PATTERNS = re.compile(
    r"\bdoesn't\s+exist\b"
    r"|\bdoes\s+not\s+exist\b"
    r"|\bno\s+such\b"
    r"|\bwasn't\s+created\b"
    r"|\bnot\s+documented\b"
    r"|\bno\s+documentation\b"
    r"|\bno\s+\w+\s+file\b",  # "no config file", "no setup file", etc.
    re.IGNORECASE,
)

# File/resource-specific patterns (more precise)
FILE_CLAIM_PATTERNS = re.compile(
    r"\bno\s+(\w+\.?\w*)\s+file\b"  # "no config file", "no .env file"
    r"|\b(\w+\.?\w*)\s+file\s+(?:doesn't|does\s+not)\s+exist\b"
    r"|\b(\w+\.?\w*)\s+(?:is|was)\s+missing\b"
    r"|\bthere's\s+no\s+(\w+\.?\w*)\b"
    r"|\bno\s+(\w+)\s+documentation\b"
    r"|\bmissing\s+(?:file|folder|directory|resource|module|package|documentation|config(?:uration)?)\b"
    r"|\b(?:file|folder|directory|resource|module|package|documentation|config(?:uration)?)\s+(?:is|was)\s+missing\b"
    # Known stale archive references (established missing in session)
    r"|\b(?:src_)?archived[_-]20260325\b"
    r"|\bP:\\?__csf\\?\.archive\b",
    re.IGNORECASE,
)

# Obvious allowlist (domain knowledge, capability statements, conversational denials, verification discussion)
_OBVIOUS_ALLOWLIST_PARTS = (
    # Capability/network statements
    r"\bno\s+(?:internet\s+access|network\s+access|network)\b",
    r"\b(?:offline|no\s+connection)\b",
    # Domain knowledge
    r"\bno\s+configuration\s+needed\b",
    r"\bno\s+config\s+required\b",
    r"\bno\s+setup\s+needed\b",
    # Conversational denials of actions (ADR-20260323: reduce false positives)
    r"\bI\s+didn(?:'?t)?\s+(?:change|modify|delete|remove|create|make|do)\b",
    r"\bI\s+haven(?:'?t)?\s+(?:changed|modified|deleted|removed|created|made|done)\b",
    r"\bI\s+never\s+(?:changed|modified|deleted|removed|created|made|done)\b",
    # Additional conversational forms (ADR-20260323: expand coverage)
    r"\bI\s+don(?:'?t)?\s+(?:think\s+)?I\s+(?:change|modify|delete|deleted|remove|create|make|do)\b",
    r"\bI\s+wasn(?:'?t)?\s+(?:the\s+one\s+who\s+)?(?:changed|modified|deleted|removed|created|made|done)\b",
    r"\bI\s+couldn(?:'?t)?\s+(?:have\s+)?(?:changed|modified|deleted|removed|created|made|done)\b",
    r"\bI\s+didn(?:'?t)?\s+(?:even\s+)?(?:get\s+to\s+)?(?:change|modify|delete|remove|create|make|do)\b",
    r"\bI\s+wasn(?:'?t)?\s+involved\s+(?:in\s+)?(?:changing|modifying|deleting|removing|creating|making)\b",
    r"\bI\s+haven(?:'?t)?\s+(?:been\s+)?(?:able\s+to\s+)?(?:changed|modified|deleted|removed|created|make|made)\b",
    # Handles: "that's not", "that isn't", "that is not", "that was not" (past participle forms)
    r"\b(?:that's\s+not|that\s+isn't|that\s+is\s+not|that\s+wasn't|that\s+was\s+not)\s+(?:something\s+)?I\s+(?:changed|modified|deleted|removed|created|made|done)\b",
    r"\b(?:this\s+isn't|this\s+is\s+not|this\s+wasn't|this\s+was\s+not)\s+(?:something\s+)?I\s+(?:changed|modified|deleted|removed|created|made|done)\b",
    # Conversational verification phrases (discussing verification, not claiming existence)
    r"\b(?:was|were)\s+(?:also\s+)?(?:verified|confirmed)\b",
    r"\b(?:file|resource)\s+(?:was\s+)?verified\b",
    r"\bverification\s+(?:has\s+)?failed\b",
    r"\bverifying\b",
    r"\bconfirm(?:s|ed)?\s+(?:the\s+)?(?:deletion|removal|existence|absence)\b",
    # Conversational denials of statements/references (ADR-20260331: reduce false positives on quoted phrases)
    r"\bI\s+didn(?:'?t)?\s+(?:even\s+)?(?:say|claim|state|mention)\b",
    r"\bI\s+never\s+(?:said|claimed|stated|mentioned)\b",
    r"\bI\s+haven(?:'?t)?\s+(?:said|claimed|stated|mentioned)\b",
    r"\bdidn(?:'?t)?\s+(?:actually\s+)?(?:say|claim|state|mean)\b",
    # Reporting speech/references (the message says X, contains Y, includes Z)
    r"\b(?:the\s+(?:error|message|output|response|hook)\s+)?(?:says?|contains?|includes?|states?)\s+(?:'[^']+'|\"[^\"]+\"|\w+\s+\w+)",
    r"\b(?:'[^']+'\s+(?:in|within|appears?\s+in)|\"[^\"]+\"\s+(?:in|within|appears?\s+in))\b",
    # Known stale archive references (established missing earlier in session)
    r"\b(?:src_)?archived[_-]20260325\b",
    r"\bP:\\?__csf\\?\.archive\b",
)
OBVIOUS_ALLOWLIST = re.compile("|".join(_OBVIOUS_ALLOWLIST_PARTS), re.IGNORECASE)

# Verification tools that count as evidence
VERIFICATION_TOOLS = {
    "Read",
    "Glob",
    "Grep",
    "Bash",  # Only if using ls, find, git ls-files, etc.
    "WebSearch",
    "WebFetch",
    "mcp__web_reader__webReader",
    "mcp__web-reader__webReader",
}

# Bash commands that indicate file system verification
# Includes Windows commands (dir, Get-ChildItem) for PowerShell取证
BASH_VERIFICATION_COMMANDS = re.compile(
    r"\bls\b"
    r"|\bfind\b"
    r"|\bgit\s+ls-files\b"
    r"|\btest\b.*-f\b"
    r"|\b\[\b.*-f\b"
    r"|\bhead\b"
    r"|\btail\b"
    r"|\bcat\b"
    r"|\bfile\b"
    r"|\bwc\b"
    r"|\bdir\b"  # Windows dir command
    r"|\bGet-ChildItem\b",  # PowerShell
    re.IGNORECASE,
)

# Pattern to detect "there's no N" where N is a pure number/count (not a file/code entity)
PURE_NUMBER_PATTERN = re.compile(r"\bthere's\s+no\s+(\d+)\b", re.IGNORECASE)


# --- Tool history verification ---------------------------------------------

def _load_turn_events(session_id: str, terminal_id: str) -> list[dict] | None:
    """Load tool events for the current turn only (id > turn_start_event_id).

    Returns None when evidence system is unavailable.
    Returns [] when evidence is available but no matching events exist this turn.
    """
    if not EVIDENCE_AVAILABLE:
        _logger.warning("FAIL-WARN: evidence_store not importable")
        return None

    if not session_id:
        _logger.warning("FAIL-WARN: session_id empty/missing")
        return None

    all_events = load_turn_scoped_events(
        session_id=session_id,
        terminal_id=terminal_id,
        limit=200,
    )
    if all_events is None:
        _logger.warning("FAIL-WARN: load_turn_scoped_events returned unavailable")
        return None

    _logger.debug("loaded %d events for session=%s", len(all_events), session_id[:16])
    return all_events


def _has_verification_this_turn(tool_events: list[dict]) -> bool:
    """Check if verification tools were used THIS TURN."""
    for event in tool_events:
        # Support both "name" (from evidence store) and "tool_name" (from spool files)
        tool_name = event.get("name") or event.get("tool_name", "")
        if tool_name in VERIFICATION_TOOLS:
            # Bash needs special handling - must use verification commands
            if tool_name == "Bash":
                command = event.get("command", "")
                if BASH_VERIFICATION_COMMANDS.search(command):
                    return True
            else:
                return True
    return False


def _extract_read_targets(tool_events: list[dict]) -> dict[str, set[str]]:
    """Extract what files/patterns were examined this turn.

    Returns dict with keys: 'files' (paths seen), 'globs' (glob patterns),
    'greps' (grep patterns), 'all_text' (all lowercase text for substring matching).
    When code files were Read, code-element claims about them are empirically grounded.
    """
    result: dict[str, set[str]] = {
        "files": set(),
        "globs": set(),
        "greps": set(),
        "all_text": set(),
    }
    for event in tool_events:
        tool_name = event.get("name") or event.get("tool_name", "")
        command = event.get("command", "") or ""

        if tool_name == "Read":
            file_path = event.get("file_path") or (event.get("tool_input", {}) or {}).get(
                "file_path", ""
            )
            if file_path:
                result["files"].add(file_path.lower())
                result["all_text"].add(file_path.lower())
        elif tool_name == "Glob":
            pattern = event.get("pattern") or command
            if pattern:
                result["globs"].add(pattern.lower())
                result["all_text"].add(pattern.lower())
        elif tool_name == "Grep":
            pattern = event.get("pattern") or command
            if pattern:
                result["greps"].add(pattern.lower())
                result["all_text"].add(pattern.lower())

    return result


# --- PreToolUse coordination check -----------------------------------------


def _check_pretooluse_coordination(session_id: str) -> bool:
    """Check if PreToolUse file existence decision state exists.

    If PreToolUse hooks have already evaluated file existence and allowed
    an overwrite (e.g., for user justification), we should not block here.
    """
    if not session_id:
        return False

    state_file = STATE_DIR / f"file_existence_decision_{session_id}.json"
    if not state_file.exists():
        return False

    try:
        data = json.loads(state_file.read_text())
        # Check if PreToolUse explicitly allowed this
        decision = data.get("decision", "")
        if decision == "allow":
            _logger.info("PreToolUse coordination: file existence decision allowed")
            return True
    except (OSError, json.JSONDecodeError) as exc:
        _logger.warning("PreToolUse state file read failed: %s: %s", state_file, exc)

    return False


# --- Pattern detection -------------------------------------------------------


def _is_exempt_pure_number_claim(claim: str) -> bool:
    """Return True if claim is 'there's no N' where N is a pure number.

    These are count claims (e.g. "there's no 10 failures") not file existence claims.
    """
    return bool(PURE_NUMBER_PATTERN.search(claim))


def _should_exempt_claim(claim: str, read_targets: dict[str, set[str]] | None) -> bool:
    """Return True if claim should be exempt because the relevant code was read this turn.

    Exempts:
    - Pure number counts: "there's no 10" (count claim, not file existence) - always exempt
    - Code-element claims where the element name appears in Grep patterns used - requires read_targets
    """
    claim_lower = claim.lower()

    # Pure number exemption - always applies, independent of tool usage
    # "there's no 10 failures" is a count claim, not a file/entity existence claim
    if _is_exempt_pure_number_claim(claim):
        _logger.debug("exempting pure number claim: %s", claim)
        return True

    # Code-element exemption requires read_targets to be available
    if read_targets is None:
        return False

    greps = read_targets.get("greps", set())

    # If the claim mentions something that was grepped (word-boundary match), it's exempt.
    # Require word boundaries to avoid substring false positives (e.g., "xyz_missing"
    # should NOT exempt "no config" via unrelated substring).
    for grep_pattern in greps:
        grep_base = grep_pattern.replace("*", "").replace("?", "")
        if grep_base and len(grep_base) >= 4:
            # Use word boundaries to avoid substring false positives
            if re.search(r"(?<!\w)" + re.escape(grep_base) + r"(?!\w)", claim_lower):
                _logger.debug(
                    "exempting code-element claim (grep basis): %s (grep=%s)", claim, grep_pattern
                )
                return True

    return False


def _detect_negative_existence_claims(
    response: str, read_targets: dict[str, set[str]] | None = None
) -> list[tuple[str, str]]:
    """Detect negative existence claims about files/resources.

    Returns list of (matched_text, pattern_type) tuples.
    Claims are filtered to remove exemptions (pure numbers, code-element claims
    where relevant code was read this turn).
    """
    if not response:
        return []

    claims = []

    # Strip quoted strings — content within quotes is "data being reported", not "claims being made".
    # This handles GTO artifact messages like '"No test file found for basic_usage.py"' which would
    # otherwise trigger the negative-existence patterns even though the response is just quoting data.
    response_for_check = re.sub(r"'[^']*'|\"[^\"]*\"", "", response)

    # Check obvious allowlist first (domain knowledge)
    if OBVIOUS_ALLOWLIST.search(response_for_check):
        _logger.debug("matched obvious allowlist pattern - skipping")
        return []

    # Check core negative existence patterns (on stripped response)
    for match in NEGATIVE_EXISTENCE_PATTERNS.finditer(response_for_check):
        claims.append((match.group(0), "core_negative", match.start(), match.end()))

    # Check file/resource-specific patterns (on stripped response)
    for match in FILE_CLAIM_PATTERNS.finditer(response_for_check):
        claims.append((match.group(0), "file_claim", match.start(), match.end()))

    # Deduplicate: keep first-encountered (text, type) for each unique claim text.
    # This prevents the same claim from appearing multiple times in the block message
    # when multiple regex patterns match the same text (e.g., "no config file" matched
    # by both core_negative and file_claim patterns, or appearing at multiple positions).
    seen_text: dict[str, tuple[str, str]] = {}
    for text, ptype, *_ in claims:
        if text not in seen_text:
            seen_text[text] = (text, ptype)
    claims = list(seen_text.values())

    # Apply exemptions when read_targets available
    if read_targets:
        original_count = len(claims)
        claims = [(c, t) for c, t in claims if not _should_exempt_claim(c, read_targets)]
        if original_count != len(claims):
            _logger.info(
                "exempted %d claim(s) based on read targets",
                original_count - len(claims),
            )

    return claims


# --- Decision logic ---------------------------------------------------------


def check(data: dict) -> dict | None:
    """Core guard logic. Returns block dict or None (allow)."""
    response = data.get("assistant_response", "") or data.get("response", "")
    if not response:
        return None

    # Load tool events for THIS TURN
    terminal_id = (
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
        or ""
    ).strip()

    session_id = (
        data.get("session_id")
        or data.get("sessionId")
        or (data.get("session") or {}).get("id", "")
        or ""
    ).strip()

    supplied_events = data.get("tool_events")
    if isinstance(supplied_events, list) and supplied_events:
        # Non-empty list provided - use it
        tool_events = supplied_events
    elif isinstance(supplied_events, list) and not supplied_events:
        # Empty list provided - may be stale snapshot. Query evidence_store directly.
        _logger.info("supplied tool_events is empty - querying evidence_store for fresh data")
        tool_events = _load_turn_events(session_id, terminal_id)
        # If evidence_store also returns empty or None, use the supplied empty list
        if not tool_events:
            tool_events = supplied_events
    else:
        tool_events = _load_turn_events(session_id, terminal_id)

    # Extract read targets for exemption analysis
    read_targets = _extract_read_targets(tool_events) if tool_events is not None else None

    # Detect negative existence claims (with exemption logic)
    claims = _detect_negative_existence_claims(response, read_targets)
    if not claims:
        return None  # No negative patterns (or all exempted) - allow

    _logger.info(
        "found %d negative existence claim(s): %s",
        len(claims),
        [claim for claim, _ in claims],
    )

    # Check PreToolUse coordination (already evaluated?)
    if _check_pretooluse_coordination(session_id):
        return None  # PreToolUse already allowed - don't double-block

    # Evidence system unavailable - warn and allow (fail-warn)
    # This allows work to continue during transient evidence system failures
    if tool_events is None:
        _logger.warning(
            "WARN: Evidence store unavailable - cannot verify %d negative existence claim(s)",
            len(claims),
        )
        lines = ["**⚠️ Unverified Negative Existence Claim (evidence system unavailable)**\n"]
        lines.append(
            "The response claims file(s)/resource(s) don't exist, "
            "but the evidence system is unavailable and cannot verify whether "
            "verification tools were used this turn.\n"
        )
        lines.append(
            "This prevents false claims like 'file doesn't exist' when the file "
            "actually exists. If this error persists, check the evidence store logs.\n"
        )
        for claim, claim_type in claims:
            lines.append(f'- Claimed: "{claim}" ({claim_type})')
        lines.append("")
        lines.append(
            "Before claiming something doesn't exist, verify it: "
            "use Read, Glob, Grep, or Bash (ls/find/git ls-files) first."
        )
        return {
            "decision": "warn",
            "reason": "\n".join(lines),
            "blocking_hook": "Stop_negative_existence_guard",
        }

    # No verification tools found (empty list) - block
    if not tool_events:
        _logger.warning(
            "BLOCK: %d unverified negative existence claim(s) (no tools used this turn)",
            len(claims),
        )
        lines = ["**Unverified Negative Existence Claim Detected**\n"]
        lines.append(
            "The response claims file(s)/resource(s) don't exist "
            "without evidence of verification tools used this turn.\n"
        )
        for claim, claim_type in claims:
            lines.append(f'- Claimed: "{claim}" ({claim_type})')
        lines.append("")
        lines.append(
            "Before claiming something doesn't exist, verify it: "
            "use Read, Glob, Grep, or Bash (ls/find/git ls-files) first."
        )

        return {
            "decision": "block",
            "reason": "\n".join(lines),
            "blocking_hook": "Stop_negative_existence_guard",
        }

    # Check if verification tools were used THIS TURN
    if _has_verification_this_turn(tool_events):
        _logger.info("verification tools used this turn - allowing claims")
        return None  # Verified - allow

    # Verification tools used but none were verification type - block
    _logger.warning(
        "BLOCK: %d unverified negative existence claim(s) (no verification tools)", len(claims)
    )
    lines = ["**Unverified Negative Existence Claim Detected**\n"]
    lines.append(
        "The response claims file(s)/resource(s) don't exist "
        "without evidence of verification tools used this turn.\n"
    )
    for claim, claim_type in claims:
        lines.append(f'- Claimed: "{claim}" ({claim_type})')
    lines.append("")
    lines.append(
        "Before claiming something doesn't exist, verify it: "
        "use Read, Glob, Grep, or Bash (ls/find/git ls-files) first."
    )

    return {
        "decision": "block",
        "reason": "\n".join(lines),
        "blocking_hook": "Stop_negative_existence_guard",
    }


def run(data: dict) -> dict | None:
    """In-process validator protocol for Stop_router."""
    result = check(data)
    if result and result.get("decision") == "block":
        return {
            "block": True,
            "reason": result.get("reason", ""),
            "blocking_hook": result.get("blocking_hook", "Stop_negative_existence_guard"),
        }
    return result


# --- Main ------------------------------------------------------------------


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
        if result.get("decision") == "block":
            sys.exit(2)
        # warn -> exit 0 (non-blocking, but message is injected)


if __name__ == "__main__":
    main()
