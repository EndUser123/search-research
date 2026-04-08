#!/usr/bin/env python3
"""
Stop Hook: Verification Gate Enforcement

Purpose: Block responses that make claims without testing, propose solutions without verification,
or skip systematic diagnostic protocols.
"""

import json
import os
import re
import sys
from pathlib import Path

# Advisory mode: when true, log warnings but don't block
_ADVISORY_MODE = os.environ.get("VERIFICATION_GATE_ADVISORY", "false").lower() == "true"

# Turn-scoped tool event awareness
_HOOKS_DIR = Path(__file__).resolve().parent.parent  # stop/ -> hooks/
_STATE_DIR = _HOOKS_DIR / "state" / "turn_markers"

# Tools that constitute verification evidence
_VERIFICATION_TOOLS = frozenset({"Read", "Grep", "Glob", "WebSearch", "WebFetch", "Bash"})

# Patterns indicating behavioral violations
CLAIM_PATTERNS = [
    r"I think\s+\w+\s+is\s+the\s+(cause|problem|issue)",
    r"The\s+problem\s+is\s+\w+",
    r"This\s+should\s+fix\s+it",
    r"Likely\s+caused\s+by",
    r"Probably\s+(a|an)\s+",
]

SOLUTION_JUMP_PATTERNS = [
    r"Let('?s+|us\s+)(fix|try|attempt)",
    r"Here'?s?\s+the\s+fix",
    r"Proposed\s+solution:",
    r"Quick\s+fix:",
]

INSUFFICIENT_VERIFICATION_PATTERNS = [
    r"(?<!Tested|Verified|Confirmed)(?!.{0,50}test)(?!.{0,30}pytest)(?!.{0,30}verify)(The\s+problem|Issue\s+is|Root\s+cause)",
]

# Urgency detection patterns — switch to "fast mode" when incident response
URGENCY_PATTERNS = [
    r"\b(urgent|urgency|emergency)\b",
    r"\b(incident|outage|down)\b",
    r"\b(prod(uction)?|live|customer)\s+(issue|problem|outage|down|broken)\b",
    r"\b(time\s*(critical|sensitive)|ASAP|right now|immediately)\b",
]

# Single root cause escape hatch pattern
SINGLE_RC_ESCAPE = re.compile(
    r"\[SINGLE\s+ROOT\s+CAUSE\s+CONFIRMED\]",
    re.IGNORECASE,
)


def _parse_hypotheses_from_text(text: str) -> list[dict[str, str]]:
    """Extract hypotheses and their status from response text.
    
    Supports:
    | [Icon] | H[n]: [Name] | [Evidence] |
    - [Icon] H[n]: [Name] ([Evidence])
    """
    hypotheses = []

    # Icons: ✓=\u2713, ✗=\u2717, ⧧=\u29E7, ⏳=\u23F3
    # Table format: | Icon | H1: Name | Evidence |
    table_pattern = re.compile(r'\|\s*([\u2713\u2717\u29E7\u23F3])\s*\|\s*([^|]+)\|\s*([^|]+)\|', re.UNICODE)
    for match in table_pattern.finditer(text):
        icon, name, evidence = match.groups()
        status = "CONFIRMED" if icon == "\u2713" else ("FALSIFIED" if icon == "\u2717" else ("INCONCLUSIVE" if icon == "\u29E7" else "UNTESTED"))
        hypotheses.append({
            "name": name.strip(),
            "status": status,
            "evidence": evidence.strip(),
            "icon": icon
        })

    # List format: - Icon H1: Name (Evidence)
    list_pattern = re.compile(r'^[*-]\s*([\u2713\u2717\u29E7\u23F3])\s*(H\d+:[^(\n]+)(?:\(([^)]+)\))?', re.MULTILINE | re.UNICODE)
    for match in list_pattern.finditer(text):
        icon, name, evidence = match.groups()
        status = "CONFIRMED" if icon == "\u2713" else ("FALSIFIED" if icon == "\u2717" else ("INCONCLUSIVE" if icon == "\u29E7" else "UNTESTED"))
        hypotheses.append({
            "name": name.strip(),
            "status": status,
            "evidence": (evidence or "").strip(),
            "icon": icon
        })

    return hypotheses


def _detect_urgency(text: str) -> bool:
    """Check if response indicates an urgent/incident scenario."""
    for pattern in URGENCY_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _format_structured_feedback(violations: list, suggestions: list, hypothesis_details: list) -> str:
    """Format violations as structured, actionable feedback."""
    lines = [
        "**Verification Gate: Behavioral Investigation Failed**",
        "",
        f"⚠️  Violations Found: {len(violations)}",
    ]

    for i, violation in enumerate(violations, 1):
        lines.append(f"   {i}. {violation}")

    # Add hypothesis status details if available
    if hypothesis_details:
        tested_count = sum(
            1 for h in hypothesis_details
            if h.get("status") in ("CONFIRMED", "FALSIFIED", "INCONCLUSIVE")
        )
        total = len(hypothesis_details)
        lines.extend([
            "",
            f"Hypothesis Testing Progress: {tested_count}/{total} tested",
            "",
            "Hypothesis Status:",
            "",
        ])
        for h in hypothesis_details:
            status = h.get("status", "UNTESTED").upper()
            icon = "\u2713" if status == "CONFIRMED" else ("\u2717" if status == "FALSIFIED"
                    else "\u29E7" if status == "INCONCLUSIVE" else "\u23F3")
            name = h.get("name") or h.get("claim", "Unknown")
            lines.append(f"   {icon} {name} \u2192 {status}")
            # Add actionable guidance for untested hypotheses
            if status == "UNTESTED" and h.get("test_suggestion"):
                lines.append(f"      Suggested test: {h['test_suggestion']}")

    if suggestions:
        lines.extend([
            "",
            "Required Actions:",
        ])
        for i, suggestion in enumerate(suggestions, 1):
            lines.append(f"   {i}. {suggestion}")

    lines.extend([
        "",
        "See MEMORY.md protocols:",
        "  - Verification First Protocol",
        "  - Solution Proposal Gate",
        "  - Structured Diagnostic Protocol",
    ])

    return "\n".join(lines)


def _safe_scope_key(session_id: str, terminal_id: str) -> str:
    """Generate a safe scope key from session_id and terminal_id."""
    def _safe(v: str) -> str:
        return "".join(c if c.isalnum() or c in "._-" else "_" for c in v)[:48]
    return f"{_safe(session_id)}__{_safe(terminal_id)}"


def _has_verification_tools_this_turn(session_id: str, terminal_id: str) -> bool:
    """Return True if Grep/Read/Glob/etc. were called this turn.

    Uses the turn marker (written by UserPromptSubmit turn_marker.py) to
    scope tool events to the current turn only. Fails open: returns False
    (don't suppress the check) if evidence system is unavailable.
    """
    if not session_id:
        return False
    try:
        # Read turn marker to get the sentinel event id
        marker_path = _STATE_DIR / f"turn_start_{_safe_scope_key(session_id, terminal_id)}.json"
        min_id: int | None = None
        if marker_path.exists():
            import json as _json
            data = _json.loads(marker_path.read_text())
            val = data.get("turn_start_event_id")
            if val is not None:
                min_id = int(val)

        # Load tool events from evidence store
        sys.path.insert(0, str(_HOOKS_DIR))
        from evidence_store import load_tool_events  # type: ignore
        events = load_tool_events(session_id=session_id, limit=200)

        # Filter to this turn only
        if min_id is not None:
            events = [e for e in events if int(e.get("id", 0)) > min_id]

        return any(e.get("name") in _VERIFICATION_TOOLS for e in events)
    except Exception:
        return False  # fail open — don't suppress the check


def check_response_violations(response_text: str, hypothesis_details: list | None = None,
                              single_root_cause: bool = False,
                              session_id: str = "", terminal_id: str = "") -> dict:
    """Analyze response for behavioral anti-patterns."""
    violations = []
    suggestions = []
    is_urgent = _detect_urgency(response_text)
    is_single_rc_escape = single_root_cause

    # Auto-parse hypotheses if not provided
    if not hypothesis_details:
        hypothesis_details = _parse_hypotheses_from_text(response_text)

    # Check for premature claims without testing
    for pattern in CLAIM_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            has_test_evidence = bool(
                re.search(r'(Test|Result|Output|Confirmed|Verified)', response_text, re.IGNORECASE)
            )
            if not has_test_evidence:
                violations.append("BEHAV-003: Claim without verification")
                suggestions.append("State hypothesis, design test, show output before claiming")

    # Check for solution jumps
    for pattern in SOLUTION_JUMP_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            has_gate_check = all([
                "root cause" in response_text.lower(),
                ("test" in response_text.lower() or "verified" in response_text.lower()),
            ])
            if not has_gate_check:
                violations.append("BEHAV-001: Premature solution jump")
                suggestions.append("Complete Solution Proposal Gate checklist first")

    # Check for single-hypothesis acceptance
    hypothesis_count = len(hypothesis_details)
    if hypothesis_count == 1 and "root cause" in response_text.lower() and not is_single_rc_escape:
        violations.append("BEHAV-002: Single hypothesis accepted")
        suggestions.append("Generate 3+ hypotheses upfront, test each systematically")

    # BEHAV-002-A: Zero-hypothesis flat assertion
    # Skip if verification tools were used this turn — claim is grounded in tool output
    _verified_this_turn = _has_verification_tools_this_turn(session_id, terminal_id)
    if hypothesis_count == 0 and not is_single_rc_escape and not _verified_this_turn:
        has_impl_claim = bool(re.search(
            r"\b(?:NOT\s+(?:fully\s+)?implemented"
            r"|not\s+yet\s+implemented"
            r"|fully\s+implemented"
            r"|completely\s+implemented"
            r"|already\s+implemented"
            r"|is\s+not\s+implemented"
            r"|has\s+not\s+been\s+implemented)\b",
            response_text, re.IGNORECASE,
        ))
        if has_impl_claim:
            violations.append("BEHAV-002-A: Zero-hypothesis definitive claim")
            suggestions.append("State 3+ hypotheses and verify via code search before asserting status.")

    # Check for diagnostic jumping
    diagnostic_approaches = len(re.findall(
        r"(?:Let'?s?\s+(?:try|check|test|verify)|Investigating|Checking)",
        response_text,
        re.IGNORECASE
    ))
    if diagnostic_approaches > 3:
        violations.append("BEHAV-004: Jumping between diagnostic approaches")
        suggestions.append("Use Structured Diagnostic Protocol - list all hypotheses first")

    return {
        "violations": violations,
        "confidence": min(len(violations) / 4.0, 1.0),
        "suggestions": suggestions,
        "hypothesis_details": hypothesis_details or [],
        "is_urgent": is_urgent,
        "is_single_rc_escape": is_single_rc_escape,
    }


def run(data: dict) -> dict | None:
    """In-process validator protocol for Stop_router."""
    response_text = str(
        data.get("assistant_response")
        or data.get("response")
        or ""
    )

    if not response_text or response_text.strip().startswith("#"):
        return None

    session_id = str(
        data.get("session_id") or data.get("sessionId")
        or os.environ.get("CLAUDE_SESSION_ID", "")
    )
    terminal_id = str(
        data.get("terminal_id") or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
    )

    hypothesis_details = data.get("hypothesis_details")
    single_root_cause = data.get("single_root_cause", False)

    result = check_response_violations(
        response_text,
        hypothesis_details=hypothesis_details,
        single_root_cause=single_root_cause,
        session_id=session_id,
        terminal_id=terminal_id,
    )

    if not result["violations"]:
        return None

    if _ADVISORY_MODE:
        import logging
        logger = logging.getLogger("verification_gate")
        logger.warning("ADVISORY: Verification gate violations: %s", result["violations"])
        return None

    if result.get("is_urgent"):
        lines = [
            "⚠️  [URGENT MODE] Verification concerns detected (non-blocking)",
            "",
            f"Violations: {len(result['violations'])}",
        ]
        for i, violation in enumerate(result["violations"], 1):
            lines.append(f"   {i}. {violation}")
        return {
            "block": False,
            "reason": "\n".join(lines),
            "blocking_hook": "Stop_verification_gate.py",
        }

    feedback = _format_structured_feedback(
        result["violations"],
        result["suggestions"],
        result.get("hypothesis_details", []),
    )

    return {
        "block": True,
        "reason": feedback,
        "blocking_hook": "Stop_verification_gate.py",
    }

def main():
    raw_input = sys.stdin.read()
    response_text = raw_input
    if raw_input:
        try:
            parsed = json.loads(raw_input)
            if isinstance(parsed, dict):
                response_text = str(parsed.get("response", ""))
        except json.JSONDecodeError:
            pass
    result = run({"response": response_text})
    if result and result.get("block"):
        print(json.dumps({
            "decision": "block",
            "reason": result["reason"],
            "blocking_hook": result.get("blocking_hook", "Stop_verification_gate.py"),
        }))
        sys.exit(0)
    print("{}")
    sys.exit(0)

if __name__ == "__main__":
    main()
