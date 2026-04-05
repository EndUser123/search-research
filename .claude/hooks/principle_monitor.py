#!/usr/bin/env python3
"""
Principle-Based Behavior Monitoring System

Observes model behavior against defined behavioral principles:
- context_reuse: Reuse existing context instead of asking again
- grounded_changes: Cite evidence when making changes
- minimal_redundancy: Avoid redundant broad questions
- transparent_uncertainty: Be explicit about uncertainty

Logs events to JSONL and emits soft suggestions when thresholds exceeded.
Never blocks responses.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# === CONSTANTS ===

STATE_PATH = Path("P:/.claude/state/behavior-counters.json")
LOG_PATH = Path("P:/.claude/logs/principle-events.jsonl")

THRESHOLD = 5  # Emit suggestion after this many violations per session

# Event type to principle mapping
EVENT_TO_PRINCIPLE = {
    "context_grounding_violation": "context_reuse",
    "change_without_evidence": "grounded_changes",
    "redundant_broad_question": "minimal_redundancy",
    "opaque_uncertainty": "transparent_uncertainty",
}

# Agreement patterns (for change_without_evidence detection)
AGREE_PATTERNS = frozenset([
    "you're right",
    "you are right",
    "good point",
    "i agree",
    "exactly",
    "fair point"
])

# Evidence citation markers (exemptions from violation)
EVIDENCE_MARKERS = [
    "see the", "in file", "in the file", "line ",
    "log shows", "logs show", "output shows",
    "stack trace", "traceback", "test shows",
    "as shown in", "according to", "based on",
    "the error above", "the error message",
    "config mentions", "in config", "in the snippet",
    "in the code above", "diff shows", "git diff",
    "pytest", "unittest", "assertion failed",
    "confirms", "config."  # Add missing markers
]

# Uncertainty patterns (for opaque_uncertainty detection)
UNCERTAINTY_PATTERNS = [
    (r"probably|likely|maybe|possibly|might be|seems", "probabilistic_without_check"),
    (r"looks (correct|right|good|fine)|seems (correct|right|good|fine)|appears (correct|right|good|fine)", "visual_inspection_without_verification"),
    (r"should work|should be fine", "optimism_without_verification"),
]

# === DETECTION FUNCTIONS ===

def has_evidence_citation(text: str) -> bool:
    """Check if message cites concrete evidence (logs, files, tests, etc.)."""
    text_lower = text.lower()
    return any(marker in text_lower for marker in EVIDENCE_MARKERS)


def detect_change_without_evidence(text: str) -> bool:
    """
    Detect agreement without evidence citation.
    Violates: grounded_changes principle
    """
    text_lower = text.lower()
    if not any(pattern in text_lower for pattern in AGREE_PATTERNS):
        return False
    if has_evidence_citation(text):
        return False
    return True


def detect_context_grounding_violation(text: str) -> bool:
    """
    Detect questions about info likely present in recent context.
    Violates: context_reuse principle
    """
    # Simple heuristic: question longer than 30 chars
    t = text.strip()
    return len(t) > 30 and t.endswith("?") and "?" in t


def detect_redundant_broad_question(text: str) -> bool:
    """
    Detect broad questions without context reference.
    Violates: minimal_redundancy principle
    """
    # Broad question patterns
    broad_patterns = [
        r"what should (we|i) do",
        r"how do (we|i)",
        r"what('s| is the)? next step",
        r"where do (we|i) start",
        r"how do (we|i) fix",
    ]
    text_lower = text.lower()
    for pattern in broad_patterns:
        if re.search(pattern, text_lower):
            # Check if references context
            if not any(ref in text_lower for ref in ["earlier", "above", "said", "file", "log"]):
                return True
    return False


def detect_opaque_uncertainty(text: str) -> bool:
    """
    Detect uncertain statements without explicit acknowledgment.
    Violates: transparent_uncertainty principle
    """
    for pattern, label in UNCERTAINTY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            # Check if follows with explicit check suggestion
            check_indicators = ["let me check", "I'll verify", "should test", "need to verify", "check", "verify", "testing"]
            text_lower = text.lower()
            if not any(indicator in text_lower for indicator in check_indicators):
                return True
    return False


# === STATE MANAGEMENT ===

def load_state() -> dict:
    """Load per-session violation counters from state file."""
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def save_state(state: dict) -> None:
    """Save per-session violation counters to state file."""
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError:
        # Log error but don't fail
        log_hook_event(
            "principle_monitor",
            "warn",
            f"Failed to write state file: {STATE_PATH}"
        )


# === LOGGING ===

def log_event(event_type: str, session_id: str, message_preview: str, extra: dict | None = None) -> None:
    """Log a principle violation event to JSONL file."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        principle = EVENT_TO_PRINCIPLE.get(event_type, "unknown")

        record: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "event_type": event_type,
            "principle": principle,
            "assistant_preview": message_preview[:200],  # Truncate
        }
        if extra:
            record["extra"] = extra

        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        # Log error but don't fail
        log_hook_event(
            "principle_monitor",
            "warn",
            f"Failed to write log: {LOG_PATH}"
        )


def run(data: dict[str, Any]) -> dict[str, Any] | None:
    """In-process validator protocol for Stop_router."""
    scope_id = str(
        data.get("terminal_id")
        or data.get("session_id")
        or ""
    ).strip()
    message = str(
        data.get("assistant_response")
        or data.get("last_assistant_message")
        or data.get("response")
        or ""
    ).strip()

    if not scope_id or not message:
        return None

    detections = []
    if detect_change_without_evidence(message):
        detections.append("change_without_evidence")
    if detect_context_grounding_violation(message):
        detections.append("context_grounding_violation")
    if detect_redundant_broad_question(message):
        detections.append("redundant_broad_question")
    if detect_opaque_uncertainty(message):
        detections.append("opaque_uncertainty")

    if not detections:
        return None

    state = load_state()
    sess = state.get(scope_id, {
        "context_grounding_violation": 0,
        "change_without_evidence": 0,
        "redundant_broad_question": 0,
        "opaque_uncertainty": 0,
        "suggestions_shown": [],
    })

    for event_type in detections:
        sess[event_type] = sess.get(event_type, 0) + 1
        log_event(event_type, scope_id, message, extra={"scope": "terminal"})

    state[scope_id] = sess
    save_state(state)

    for event_type in detections:
        principle = EVENT_TO_PRINCIPLE[event_type]
        suggestion_key = f"{principle}_suggested"
        if sess.get(event_type, 0) >= THRESHOLD and suggestion_key not in sess.get("suggestions_shown", []):
            sess["suggestions_shown"] = sess.get("suggestions_shown", [])
            sess["suggestions_shown"].append(suggestion_key)
            state[scope_id] = sess
            save_state(state)
            return {
                "allow": True,
                "note": (
                    f"Note: I've seen several {principle} violations in this terminal. "
                    f"If this feels noisy, we could strengthen the session card "
                    f"to emphasize the {principle} principle."
                ),
            }

    return None


# === MAIN HOOK ===

def main() -> None:
    """Main entry point for Stop hook."""
    try:
        data = json.load(sys.stdin)
    except (OSError, json.JSONDecodeError):
        print("{}")
        sys.exit(0)

    # Validate event type
    if data.get("hook_event_name") != "Stop":
        print("{}")
        sys.exit(0)

    out = run(data) or {}

    print(json.dumps(out))
    sys.exit(0)


if __name__ == "__main__":
    main()
