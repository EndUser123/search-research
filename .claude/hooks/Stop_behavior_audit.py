#!/usr/bin/env python3
"""
Stop_behavior_audit.py - Unified Behavioral Verifier
====================================================

The single source of truth for Stop-time behavioral proof.
Cross-references assistant claims against tool-call history.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

# Force hooks directory into path
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from unified_claim_verifier import evaluate_claims

# --- User-Dismissal Detector ---
# Catches responses that dismiss user-reported problems after CORRECTION intent.
# Requires conjunction: (a) user expressed correction/assertion AND (b) response
# contains dismissal AND (c) response lacks reconciliation of the user's failure path.

_CORRECTION_MARKERS = re.compile(
    r"\b("
    r"i\s+(?:just\s+)?told\s+you|"
    r"it'?s\s+a\s+(?:bug|error|problem|issue|failure)|"
    r"you'?re\s+(?:wrong|missing|not\s+listening)|"
    r"i\s+(?:already|just)\s+(?:said|told|explained)|"
    r"(?:that'?s|it'?s|this\s+is)\s+(?:a\s+)?(?:bug|broken|error)|"
    r"stop\s+(?:saying|claiming|telling\s+me)"
    r")\b",
    re.IGNORECASE,
)

_DISMISSAL_PATTERNS = re.compile(
    r"\b("
    r"not\s+a\s+bug|"
    r"no\s+fix\s+needed|"
    r"not\s+broken|"
    r"currently\s+functioning|"
    r"working\s+correctly|"
    r"working\s+as\s+expected|"
    r"no\s+(?:action|changes?)\s+needed|"
    r"appears?\s+to\s+be\s+working|"
    r"is\s+functioning\s+normally|"
    r"testing\s+artifact|"
    r"diagnostic\s+artifact"
    r")\b",
    re.IGNORECASE,
)

# Reconciliation: response explains WHY the user's specific failure path is invalid
_RECONCILIATION_PATTERNS = re.compile(
    r"(?:"
    r"here\s+is\s+why\s+(?:this|that|your)\s+(?:cannot|can'?t|isn'?t|is\s+not)|"
    r"(?:your|the)\s+(?:error|failure|issue)\s+(?:occurs?|happens?|is\s+caused)\s+because|"
    r"the\s+reason\s+(?:this|your|that)\s+(?:fails?|errors?|breaks?)|"
    r"reproducing\s+your\s+(?:exact\s+)?(?:steps|scenario|error)|"
    r"i\s+re-?ran\s+your\s+(?:exact\s+)?steps|"
    r"using\s+your\s+(?:exact\s+)?(?:reproduction|repro|command|invocation)|"
    # Broader reconciliation: explanations that address the specific failure path
    r"i\s+traced\s+(?:the|your)|"
    r"the\s+(?:actual|specific)\s+(?:cause|reason|failure|error)\s+is|"
    r"(?:however|but)\s+(?:the|this)\s+(?:only|specifically)\s+(?:occurs?|happens?|fails?)\s+when|"
    r"(?:your|the)\s+(?:specific|exact)\s+(?:case|scenario|situation)\s+(?:is|differs|works)\b"
    r")",
    re.IGNORECASE,
)


def check_user_dismissal(response: str, data: dict) -> dict | None:
    """Check if response dismisses a user-reported problem.

    Returns block payload if all three conditions met:
    1. User's prompt contains CORRECTION intent (they're asserting something)
    2. Response contains dismissal language
    3. Response lacks reconciliation of the user's specific failure path

    Returns None if no dismissal detected or reconciliation present.
    """
    # Extract user's last message
    transcript = data.get("transcript", [])
    user_msg = ""
    for entry in reversed(transcript):
        if isinstance(entry, dict) and entry.get("role") == "user":
            content = entry.get("content", "")
            if isinstance(content, list):
                user_msg = " ".join(
                    b.get("text", "") for b in content if isinstance(b, dict)
                )
            else:
                user_msg = str(content)
            if user_msg:
                break

    if not user_msg:
        return None

    # Condition (a): User expressed CORRECTION intent
    if not _CORRECTION_MARKERS.search(user_msg):
        return None

    # Condition (b): Response contains dismissal
    dismissal_match = _DISMISSAL_PATTERNS.search(response)
    if not dismissal_match:
        return None

    # Condition (c): Response lacks reconciliation of user's failure path
    if _RECONCILIATION_PATTERNS.search(response):
        return None  # Has reconciliation — allow through

    return {
        "decision": "block",
        "reason": (
            f"USER REPORT DISMISSAL: Response contains '{dismissal_match.group()}' "
            f"after user asserted a problem exists. To dismiss a user-reported issue, "
            f"you must reproduce their exact failure path and explain why it's invalid."
        ),
        "blocking_hook": "Stop_behavior_audit.py:user_dismissal",
    }


def _safe_id(value: str | None) -> str:
    """Convert session/terminal id to filesystem-safe fragment."""
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _marker_path(data: dict) -> Path:
    """Return scoped marker path."""
    session_id = (
        data.get("session_id")
        or data.get("sessionId")
        or os.environ.get("CLAUDE_SESSION_ID")
        or ""
    )
    terminal_id = (
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID")
        or ""
    )
    scoped_name = (
        f"last_blocked_claim_{_safe_id(str(session_id))}_{_safe_id(str(terminal_id))}.json"
    )
    scoped_marker = HOOKS_DIR / "session_data" / scoped_name
    return scoped_marker

def main():
    try:
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            sys.exit(0)

        data = json.loads(raw_input)
        response = data.get("response", "")

        if not response:
            sys.exit(0)

        # Run behavioral evaluation
        result = evaluate_claims(response, session_id=data.get("session_id", ""))

        if result["decision"] == "block":
            # Set marker for UserPromptSubmit pushback protocol.
            scoped_marker = _marker_path(data)
            scoped_marker.parent.mkdir(parents=True, exist_ok=True)
            marker_data = {
                "timestamp": time.monotonic(),
                "reason": result["reason"],
                "missing_claims": result.get("missing_claims", []),
                "session_id": (
                    data.get("session_id")
                    or data.get("sessionId")
                    or os.environ.get("CLAUDE_SESSION_ID")
                    or ""
                ),
                "terminal_id": (
                    data.get("terminal_id")
                    or data.get("terminalId")
                    or os.environ.get("CLAUDE_TERMINAL_ID")
                    or ""
                ),
            }
            # Marker is terminal/session scoped to avoid cross-terminal bleed.
            scoped_marker.write_text(json.dumps(marker_data), encoding="utf-8")

            # Emit block payload
            print(json.dumps({
                "decision": "block",
                "reason": (
                    f"UNVERIFIED CLAIMS: {result['reason']}\n\n"
                    f"Evidence missing for: {result.get('missing_claims', [])}"
                ),
                "blocking_hook": "Stop_behavior_audit.py",
            }))
            sys.exit(2) # Block exit code

        print(json.dumps({"decision": "allow"}))

    except Exception as e:
        # Fail OPEN on audit error to avoid deadlock
        print(json.dumps({"decision": "allow", "note": f"Audit error: {e}"}))
        sys.exit(0)

if __name__ == "__main__":
    main()
