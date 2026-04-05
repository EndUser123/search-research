#!/usr/bin/env python3
"""
Stop_advisory.py - Non-Blocking Suggestions & Heuristics
========================================================

Appends suggestions to the response without blocking execution.
Focuses on soft improvements: sycophancy detection, hyperbole, and reminders.
"""

from __future__ import annotations

import re

# Absolutist language patterns (for confidence label check)
ABSOLUTIST_PATTERNS = [
    r"\bdefinitel(?:y|y)\b",
    r"\bcertainl(?:y|y)\b",
    r"\bundoubtedl(?:y|y)\b",
    r"\bwithout\s+(?:a\s+)?doubt\b",
    r"\b100%\b",
    r"\bthere'?s\s+no\s+(?:way|chance|question)\b",
]

# Confidence labels (if present, absolutist check passes)
CONFIDENCE_LABELS = re.compile(
    r"\b(?:HIGH|MEDIUM|LOW)\s+confidence\b"
    r"|\bconfidence:\s*(?:HIGH|MEDIUM|LOW)\b",
    re.IGNORECASE,
)

import json
import re
import sys
from pathlib import Path

# Patterns indicating sycophancy (overly agreeable)
SYCOPHANCY_PATTERNS = [
    r"exactly\s+right",
    r"absolutely\s+correct",
    r"perfect\s+point",
    r"brilliant\s+observation",
]

# Patterns indicating hyperbole (over-claiming success)
HYPERBOLE_PATTERNS = [
    r"massive\s+success",
    r"complete\s+victory",
    r"perfectly\s+working",
]

# Patterns indicating lazy shortcuts (diagnostic backstop for root-cause principle)
# These are telemetry, not the primary enforcement mechanism.
# If these fire frequently, the constitutional principle needs strengthening.
SHORTCUT_PATTERNS = [
    (r"(?:this is |it'?s )?(?:just |only )?(?:a )?cosmetic(?:\s+(?:error|issue|warning))?", "Cosmetic dismissal detected. Fix the root cause or provide evidence it's unfixable."),
    (r"(?:as a |for a )?workaround|work around this by", "Workaround offered without root cause. Identify and fix the source, or explain what blocks the fix."),
    (r"(?:you can |just )?(?:safely )?ignore (?:this|that|it|the)", "Dismissing an issue. Either fix it or document why it's genuinely harmless with evidence."),
]

import os

HOOKS_DIR = Path(__file__).resolve().parent
COACH_NOTE_DIR = HOOKS_DIR / "session_data"

def _safe_id(value: str) -> str:
    """Sanitize ID for filesystem safety (matches Stop_behavior_audit.py pattern)."""
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)

def _coach_note_path() -> Path:
    """Return session-scoped coach note path using env vars set by Stop.py._pin_scope_env()."""
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "")
    scoped_name = f"coach_note_{_safe_id(session_id)}_{_safe_id(terminal_id)}.json"
    return COACH_NOTE_DIR / scoped_name

def _write_coach_note(note: str) -> None:
    """Write a single coach note for next turn. Session-scoped via env vars."""
    try:
        COACH_NOTE_DIR.mkdir(parents=True, exist_ok=True)
        _coach_note_path().write_text(note, encoding="utf-8")
    except OSError:
        pass

def _clear_coach_note() -> None:
    """Clear coach note for this session scope."""
    try:
        path = _coach_note_path()
        if path.exists():
            path.unlink(missing_ok=True)
    except OSError:
        pass

def read_and_clear_coach_note() -> str | None:
    """Read and delete the coach note. Returns note text or None."""
    try:
        path = _coach_note_path()
        if not path.exists():
            return None
        note = path.read_text(encoding="utf-8").strip()
        path.unlink(missing_ok=True)
        return note if note else None
    except OSError:
        return None




def check_advisories(response: str) -> list[str]:
    suggestions = []
    response_lower = response.lower()

    # 1. Sycophancy Check
    if any(re.search(p, response_lower) for p in SYCOPHANCY_PATTERNS):
        suggestions.append("Response shows agreement bias. State positions with evidence, not praise.")

    # 2. Hyperbole Check
    if any(re.search(p, response_lower) for p in HYPERBOLE_PATTERNS):
        suggestions.append("Success claim may be hyperbolic. Itemize specific verified components.")

    # 3. Test Reminder
    if "fixed" in response_lower and "test" not in response_lower:
        suggestions.append("You claimed a fix but haven't run tests. Verify with `pytest` or `Bash`.")

    # 4. Shortcut Detection (diagnostic backstop for root-cause obligation)
    for pattern, advisory in SHORTCUT_PATTERNS:
        if re.search(pattern, response_lower):
            suggestions.append(advisory)
            break  # One shortcut advisory per response is enough
    # 5. Absolutist language without confidence labels
    if any(re.search(p, response_lower) for p in ABSOLUTIST_PATTERNS):
        if not CONFIDENCE_LABELS.search(response):
            suggestions.append(
                "Absolutist language detected without confidence labels. "
                "Label key claims as HIGH/MEDIUM/LOW confidence."
            )


    # Coach notes for next turn
    coach_notes = []

    # Coach 1: Claimed "fixed" without running tests
    if "fixed" in response_lower and "test" not in response_lower:
        coach_notes.append(
            "You claimed a fix but did not run tests. "
            "Next turn: run tests before claiming success."
        )

    # Coach 2: Made a plan without defining completion criteria
    plan_indicators = ["plan:", "steps:", "approach:", "strategy:"]
    done_indicators = ["done when", "complete when", "success criteria",
                       "acceptance criteria", "definition of done"]
    if any(ind in response_lower for ind in plan_indicators):
        if not any(ind in response_lower for ind in done_indicators):
            coach_notes.append(
                "You described a plan but gave no completion criteria. "
                "Next turn: define what 'done' looks like before starting work."
            )

    if coach_notes:
        _write_coach_note(coach_notes[0])  # Only persist the first/most important
    else:
        _clear_coach_note()

    return suggestions

def main():
    try:
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            sys.exit(0)

        data = json.loads(raw_input)
        response = data.get("response", "")

        if not response:
            sys.exit(0)

        suggestions = check_advisories(response)

        if suggestions:
            print(json.dumps({"systemMessage": "\n\n💡 **ADVISORY**: " + " | ".join(suggestions)}))
        else:
            print("{}")

    except Exception:
        print("{}")

if __name__ == "__main__":
    main()
