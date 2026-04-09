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
sys.path.insert(0, str(_HOOKS_DIR))

try:
    from turn_scoped_evidence import load_turn_scoped_events
    from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
except ImportError:
    load_turn_scoped_events = None  # type: ignore
    SCOPE_SESSION_FRESH = None
    load_scoped_tool_events = None  # type: ignore

# Tools that constitute verification evidence
_VERIFICATION_TOOLS = frozenset({"Read", "Grep", "Glob", "WebSearch", "WebFetch", "Bash"})

# Declarative patterns — checked independently, ALL violations collected (not just first).
# Regex for variable-extraction patterns; fixed phrases use \b word boundaries.

CLAIM_PATTERNS = [
    (r"\blikely caused by\b", None),
    (r"\bprobably a\b", None),
    (r"\bprobably an\b", None),
    (r"\bthis should fix it\b", None),
    (r"\bI think\s+\w+\s+is\s+the\s+(cause|problem|issue)\b", r'(Test|Result|Output|Confirmed|Verified)'),
    (r"\bthe problem is\b", r'(Test|Result|Output|Confirmed|Verified)'),
]

SOLUTION_JUMP_PATTERNS = [
    (r"\blet(?:'s|s)?\s+(?:fix|try|attempt)\b|\blet\s+us\s+(?:fix|try|attempt)\b", None),
    (r"\bhere(?:'?s?|\s+is)\s+the\s+fix\b", None),
    (r"\bproposed\s+solution:|\bquick\s+fix:", None),
]


def _check_claim_patterns(text: str, verified_this_turn: bool = False) -> list[str]:
    """Check for unverified causal claims. Returns list of violations.

    Skips when verification tools (Read/Grep/Glob/Bash/etc.) ran this turn —
    the response is grounded in actual investigation, not speculation."""
    if verified_this_turn:
        return []
    violations = []
    t = text.lower()
    for pattern, exemption in CLAIM_PATTERNS:
        if re.search(pattern, t, re.IGNORECASE):
            if exemption is None or not re.search(exemption, text, re.IGNORECASE):
                violations.append("BEHAV-003: Claim without verification")
    return violations


def _check_solution_jump_patterns(text: str, verified_this_turn: bool = False) -> list[str]:
    """Check for premature solution jumps. Returns list of violations.

    Skips when verification tools (Read/Grep/Glob/Bash/etc.) ran this turn —
    the response is grounded in actual investigation, not speculation."""
    if verified_this_turn:
        return []
    violations = []
    t = text.lower()
    has_root_cause = "root cause" in t
    has_test_or_verified = "test" in t or "verified" in t
    for pattern, _ in SOLUTION_JUMP_PATTERNS:
        if re.search(pattern, t, re.IGNORECASE):
            if not (has_root_cause and has_test_or_verified):
                violations.append("BEHAV-001: Premature solution jump")
    return violations

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


def _has_verification_tools_this_turn(session_id: str, terminal_id: str) -> bool:
    """Return True if Grep/Read/Glob/etc. were called this turn.

    Uses session-scoped evidence (not turn-scoped) because terminal_id is often
    empty in the evidence store, making turn-scoped queries unreliable.
    Fails open: returns False if evidence is unavailable.
    """
    if not session_id or load_scoped_tool_events is None:
        return False
    try:
        events = load_scoped_tool_events(
            session_id=session_id,
            terminal_id=terminal_id,
            scope=SCOPE_SESSION_FRESH,
            limit=200,
        )
        if not events:
            return False
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

    # Exempt BEHAV-001/003 when tools ran this turn — response is grounded in investigation
    _verified_this_turn = _has_verification_tools_this_turn(session_id, terminal_id)

    # Check for premature claims without testing
    violations.extend(_check_claim_patterns(response_text, verified_this_turn=_verified_this_turn))
    if "BEHAV-003" in violations:
        suggestions.append("State hypothesis, design test, show output before claiming")

    # Check for solution jumps
    violations.extend(_check_solution_jump_patterns(response_text, verified_this_turn=_verified_this_turn))
    if "BEHAV-001" in violations:
        suggestions.append("Complete Solution Proposal Gate checklist first")

    # Check for single-hypothesis acceptance
    hypothesis_count = len(hypothesis_details)
    if hypothesis_count == 1 and "root cause" in response_text.lower() and not is_single_rc_escape:
        violations.append("BEHAV-002: Single hypothesis accepted")
        suggestions.append("Generate 3+ hypotheses upfront, test each systematically")

    # BEHAV-002-A: Zero-hypothesis flat assertion
    # Skip if verification tools were used this turn — claim is grounded in tool output
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
            # Exempt pytest test output — "N passed" is unambiguous verification evidence
            if re.search(r"\b\d+\s+passed\b", response_text, re.IGNORECASE):
                pass  # Don't flag — pytest output IS verification evidence
            else:
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
        sys.exit(1)
    print("{}")
    sys.exit(0)

if __name__ == "__main__":
    main()
