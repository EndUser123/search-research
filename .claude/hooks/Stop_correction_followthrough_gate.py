#!/usr/bin/env python3
"""Stop_correction_followthrough_gate.py - Correction Follow-Through Gate

Phase 4 of LLM Behavioral Integrity system.

Detects user corrections AND requires substantive follow-through:
- Re-checking the relevant source (file, test, data) and updating the claim, OR
- Explicitly stating inability to verify with what was attempted

Superficial "Understood / Acknowledged / Got it" responses are blocked.
This gate runs at Stop phase and reads the transcript to detect corrections
that occurred in prior turns of the conversation.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from __lib__.correction_detector import has_correction, has_acknowledgment

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CORRECTION_FOLLOWTHROUGH_ENABLED = (
    os.environ.get("CORRECTION_FOLLOWTHROUGH_ENABLED", "true").lower() == "true"
)
CORRECTION_FOLLOWTHROUGH_MODE = os.environ.get(
    "CORRECTION_FOLLOWTHROUGH_MODE", "block"
).lower()

# ---------------------------------------------------------------------------
# Follow-through detection patterns
# ---------------------------------------------------------------------------

# Evidence of re-checking / re-reading / re-running
RECHECK_PATTERNS = [
    # Explicit re-read/re-check/re-run language
    re.compile(r"\bI\s+(?:re-?)?read\b", re.IGNORECASE),
    re.compile(r"\bI\s+re-?checked\b", re.IGNORECASE),
    re.compile(r"\bI\s+(?:re-?)?ran\b", re.IGNORECASE),
    re.compile(r"\bI\s+re-?verified\b", re.IGNORECASE),
    re.compile(r"\bI\s+(?:re-?)?tested\b", re.IGNORECASE),
    re.compile(r"\bI\s+re-?inspect(?:ed|ing)?\b", re.IGNORECASE),
    re.compile(r"\bI\s+re-?examined?\b", re.IGNORECASE),
    re.compile(r"\bI\s+(?:re-?)?confirmed\b", re.IGNORECASE),
    re.compile(r"\bI\s+re-?ran\b", re.IGNORECASE),
    re.compile(r"\bI\s+(?:re-?)?looked\s+(?:at|into)\b", re.IGNORECASE),
    re.compile(r"\bI\s+(?:re-?)?checked\s+(?:the\s+)?(?:file|code|output|test|path|line)s?\b", re.IGNORECASE),
    re.compile(r"\bI\s+(?:re-?)?ran\s+(?:the\s+)?(?:pytest|tests?|python|node|npm)\b", re.IGNORECASE),
    re.compile(r"\bI\s+(?:just|already)\s+(?:re-?read|re-?checked|re-?ran|re-?tested)\b", re.IGNORECASE),
    re.compile(r"\bafter\s+(?:re-?reading|re-?checking|re-?running|re-?testing)\b", re.IGNORECASE),
    re.compile(r"\bhaving\s+(?:re-?read|re-?checked|re-?ran)\b", re.IGNORECASE),
    # Explicit inability to verify (counts as honest follow-through)
    re.compile(r"\bI\s+could\s+not\s+(?:verify|re-?check|re-?read|re-?test)\b", re.IGNORECASE),
    re.compile(r"\bI\s+was\s+unable\s+to\s+(?:verify|re-?check|re-?read)\b", re.IGNORECASE),
    re.compile(r"\bI\s+(?:have\s+)?not\s+(?:been\s+)?able\s+to\s+(?:verify|re-?check)\b", re.IGNORECASE),
    re.compile(r"\bcould\s+not\s+(?:verify|re-?check)\b.*?\bwhat\s+I\s+tried\b", re.IGNORECASE | re.DOTALL),
    # Specific file/test/section reference (evidence of actual checking)
    re.compile(r"\b(?:file|path|code|test|line)s?\s+\d+\b", re.IGNORECASE),  # line 42, file.py:51
    re.compile(r"\b(?:file|module|hook|test)\s+`[^`]+`", re.IGNORECASE),     # `Stop.py`
    re.compile(r"\b`[^`]+\.py\b", re.IGNORECASE),                           # `foo.py`
    re.compile(r"\bpytest\b.*?-v", re.IGNORECASE),                          # pytest -v
    re.compile(r"\bpython\b.*?\.py\b", re.IGNORECASE),                      # python foo.py
    # Outcome update patterns — explicitly stating the corrected claim
    re.compile(r"\bI\s+(?:was\s+)?wrong\b", re.IGNORECASE),
    re.compile(r"\bI\s+stand\s+corrected\b", re.IGNORECASE),
    re.compile(r"\bafter\s+(?:checking|reading|running|verifying)\b.*?\b(?:I|it|that|this)\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\b(?:checking|reading|running)\b.*?\b(?:confirms|reveals|shows)\b", re.IGNORECASE | re.DOTALL),
    re.compile(r"\bconfirms?\b.*?\b(?:that|what|is|was)\b", re.IGNORECASE),
    re.compile(r"\b(confirmed|verified)\s+(?:to\s+be|that|what|is)\b", re.IGNORECASE),
]

# Pure acknowledgment patterns — no substantive follow-through
# These match at START of response — the acknowledgment phrase must be at the beginning.
# - PURE_ACK_START: blocks pure acknowledgment at start (no follow-through after)
# - ACK_WITH_TRAILING: allows if followed by actual follow-through content
PURE_ACK_START = [
    # Simple single-word acks at start
    re.compile(r"^\s*(?:understood|acknowledged|got\s+it|noted|copy|fair\s+enough|make\s+sense)\s*[.!?]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?:yes|no|okay|ok|sure|alright)\s*[.!]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?:i(?:'ll|'m\s+fine|'ve\s+got\s+it|understand)|roger|indeed)\s*[.!]?\s*$", re.IGNORECASE),
    re.compile(r"^\s*(?:will\s+do|sounds\s+good|noted\s+with\s+thanks?)\s*[.!]?\s*$", re.IGNORECASE),
]

# Ack at start followed by TRAILING content that looks like intent/promise but NOT re-check
# These are weaker acknowledgment forms that still lack substantive follow-through
ACK_WITH_INTENT_BLOCK = [
    # "Understood, thanks for the correction" — blocks (no re-check language)
    re.compile(r"^\s*understood[,.\s]+thanks?\s+for\s+the\s+(?:correction|clarification|feedback)[.!]?\s*$", re.IGNORECASE),
    # "Thanks for the correction!" — blocks (no re-check language)
    re.compile(r"^\s*thanks?\s+for\s+the\s+(?:correction|clarification|feedback)[.!]?\s*$", re.IGNORECASE),
    # "Thank you for the correction." — blocks (no re-check language)
    re.compile(r"^\s*thank\s+you\s+for\s+the\s+(?:correction|clarification|feedback)[.!]?\s*$", re.IGNORECASE),
    # "Understood. I will check..." / "Understood. I'll check..." — blocks (promise, not evidence)
    re.compile(r"^\s*understood[.!]\s+(?:I\s+will|I'll|i'll)\s+(?:check|look|read|verify|examine)", re.IGNORECASE),
    # "Got it. I'll..." / "Got it. I will..." — blocks (promise, not evidence)
    re.compile(r"^\s*got\s+it[.!]\s+(?:i\s+will|i'll|let\s+me)", re.IGNORECASE),
    # "Acknowledged. I will..." / "Acknowledged. I'll..." — blocks (promise, not evidence)
    re.compile(r"^\s*acknowledged[.!]\s+(?:i\s+will|i'll|let\s+me)", re.IGNORECASE),
]

# Apology without substantive change — always blocks
PURE_APOLOGY_DISMISSAL = [
    # Apology + dismissal: "I apologize/I am sorry/I'm sorry" + dismissals
    re.compile(r"(?i)^.*?\bI\s+(?:am|'m|'ve)\s+sorry\b.*?(?:not\s+a\s+bug|was?\s+correct|ruling\s+stands?|no\s+fix\s+needed|working\s+as\s+designed).*$", re.DOTALL),
    re.compile(r"(?i)^.*?\bI\s+apologize\b.*?(?:not\s+a\s+bug|was?\s+correct|ruling\s+stands?|no\s+fix\s+needed|working\s+as\s+designed).*$", re.DOTALL),
    # "not a bug" / dismissal without evidence (apology at end: "working as designed, I'm sorry")
    re.compile(r"(?i)\bworking\s+as\s+designed\b.*\bI\s+(?:am|'m)\s+sorry\b", re.DOTALL),
    re.compile(r"(?i)\bworking\s+as\s+designed\b.*\bI\s+apologize\b", re.DOTALL),
    re.compile(r"(?i)\bnot\s+a?\s+bug\b.*(?:was?\s+correct|ruling\s+stands?|no\s+fix\s+needed|working\s+as\s+design|this\s+is\s+expected)\b", re.DOTALL),
]


def _is_pure_acknowledgment(text: str) -> bool:
    """Check if response is a pure acknowledgment with no substantive follow-through."""
    stripped = text.strip()
    if not stripped:
        return False
    for pattern in PURE_ACK_START:
        if pattern.match(stripped):
            return True
    for pattern in ACK_WITH_INTENT_BLOCK:
        if pattern.match(stripped):
            return True
    for pattern in PURE_APOLOGY_DISMISSAL:
        if pattern.match(stripped):
            return True
    return False


def _has_recheck_evidence(text: str, tool_events: list[dict[str, Any]]) -> bool:
    """Check if response shows evidence of re-checking or explicit inability to verify.

    Looks for:
    1. Re-check language in response text (regex patterns above)
    2. Tool events in this turn that show Read/Bash/Glob activity on relevant targets
    3. Explicit "I could not verify" statements with what was attempted

    NOTE: If the response is a pure acknowledgment (pure_ack=True), tool events
    do NOT count as re-check evidence. The LLM must show actual re-check language
    in its RESPONSE text — having executed tool events for other reasons is not
    sufficient follow-through for a "Understood/Acknowledged" response.
    """
    # Pure acknowledgment: tool events don't save it — must show re-check language
    if _is_pure_acknowledgment(text):
        return False

    # Check for re-check language patterns
    for pattern in RECHECK_PATTERNS:
        if pattern.search(text):
            return True

    # Tool events this turn are evidence of actual verification
    # (only reached if response is not pure acknowledgment)
    if tool_events:
        for event in tool_events:
            tool_name = event.get("name", "")
            if tool_name in ("Read", "Grep", "Glob", "Bash"):
                command = event.get("command", "") or ""
                output = event.get("output", "") or ""
                if command or output:
                    return True

    return False


def _detect_correction_in_conversation(transcript_text: str) -> bool:
    """Scan transcript for user correction patterns.

    Uses the same detection logic as correction_detector but applied to
    the full conversation transcript (which may contain multiple turns).
    """
    if not transcript_text:
        return False
    return has_correction(transcript_text)


def _run_gate(data: dict[str, Any]) -> dict[str, Any] | None:
    """Main gate logic.

    Returns:
        None if no correction is active or response is acceptable.
        dict with "decision": "block" and systemMessage if violation found.
    """
    response = data.get("response", "") or ""
    user_prompt = data.get("user_prompt", "") or ""
    transcript_path = data.get("transcript_path", "") or ""

    if not response:
        return None

    # Step 1: Detect if this turn's user prompt contains a correction
    this_turn_has_correction = has_correction(user_prompt)

    # Step 2: If no correction in this turn, check transcript for prior corrections
    correction_in_conversation = this_turn_has_correction
    if not correction_in_conversation and transcript_path:
        try:
            transcript_content = Path(transcript_path).read_text(encoding="utf-8")
            correction_in_conversation = _detect_correction_in_conversation(transcript_content)
        except Exception:
            # If we can't read the transcript, be conservative and skip
            correction_in_conversation = False

    if not correction_in_conversation:
        # No correction in this conversation — nothing to enforce
        return None

    # Step 3: A correction was detected — check for follow-through
    tool_events = data.get("tool_events", [])
    if isinstance(tool_events, str):
        tool_events = []

    has_recheck = _has_recheck_evidence(response, tool_events)
    is_pure_ack = _is_pure_acknowledgment(response)

    if is_pure_ack and not has_recheck:
        # Pure acknowledgment without any evidence of re-checking
        msg = (
            "CORRECTION WITHOUT FOLLOW-THROUGH DETECTED\n\n"
            "A user correction was detected, but your response is a pure acknowledgment "
            "without any substantive follow-through.\n\n"
            "You must either:\n"
            "  (1) Re-read/check the relevant file/test/data and update your claim, OR\n"
            "  (2) State explicitly: 'I could not verify X. I tried A, B, and what I "
            "found is...' with specific details.\n\n"
            "Do NOT respond with 'Understood / Acknowledged / Got it' without re-checking.\n"
            "Do NOT apologize while repeating the same conclusion.\n\n"
            "Re-check and revise, then regenerate."
        )
        if CORRECTION_FOLLOWTHROUGH_MODE == "warn":
            return {"decision": "allow", "systemMessage": msg}
        return {"decision": "block", "systemMessage": msg}

    if has_recheck:
        # Substantive follow-through detected — allow
        return None

    # Response has some content but unclear if it's substantive
    # Allow with advisory to be safe (don't over-block)
    return None


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Entry point for the correction follow-through gate.

    Args:
        input_data: Stop hook input data with response, user_prompt, tool_events, transcript_path

    Returns:
        {"decision": "allow"|"block", "systemMessage": str|None}
    """
    if not CORRECTION_FOLLOWTHROUGH_ENABLED:
        return {"decision": "allow"}

    try:
        result = _run_gate(input_data)
        return result if result else {"decision": "allow"}
    except Exception as e:
        print(f"[Stop] correction_followthrough error: {e}", file=sys.stderr)
        # Fail open — don't block on internal errors
        return {"decision": "allow"}


if __name__ == "__main__":
    import json as _json

    input_text = sys.stdin.read()
    try:
        input_data = _json.loads(input_text) if input_text else {}
    except _json.JSONDecodeError:
        input_data = {}

    result = run(input_data)
    print(_json.dumps(result))