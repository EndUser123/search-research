#!/usr/bin/env python3
"""
Stop Hook: Verification Gate Enforcement

Purpose: Block responses that make claims without testing, propose solutions without verification,
or skip systematic diagnostic protocols.

Triggers: Pre-response analysis of behavioral patterns

Behavioral Anti-Patterns Detected:
- BEHAV-001: Premature solution jump without verification
- BEHAV-002: Acceptance of first plausible explanation
- BEHAV-003: Insufficient verification before claims
- BEHAV-004: Jumping between diagnostic approaches

Enforced Protocols (from MEMORY.md):
- Verification First Protocol: Claim → Test → Document
- Solution Proposal Gate: 6 checkboxes before any solution proposal
- Structured Diagnostic Protocol: 3+ hypotheses, systematic testing
"""

import json
import re

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

def check_response_violations(response_text: str) -> dict:
    """
    Analyze response for behavioral anti-patterns.

    Returns dict with:
    - violations: list of violation types found
    - confidence: float 0-1
    - suggestions: list of corrective actions
    """
    violations = []
    suggestions = []

    # Check for premature claims without testing
    for pattern in CLAIM_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            # Look for test evidence in surrounding context
            has_test_evidence = bool(
                re.search(r'(Test|Result|Output|Confirmed|Verified)', response_text, re.IGNORECASE)
            )
            if not has_test_evidence:
                violations.append("BEHAV-003: Claim without verification")
                suggestions.append("State hypothesis, design test, show output before claiming")

    # Check for solution jumps
    for pattern in SOLUTION_JUMP_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            # Check if solution proposal gate was passed
            has_gate_check = all([
                "root cause" in response_text.lower(),
                ("test" in response_text.lower() or "verified" in response_text.lower()),
            ])
            if not has_gate_check:
                violations.append("BEHAV-001: Premature solution jump")
                suggestions.append("Complete Solution Proposal Gate checklist first")

    # Check for single-hypothesis acceptance
    hypothesis_count = len(re.findall(r'(?:Hypothesis|H\d+:)', response_text, re.IGNORECASE))
    if hypothesis_count == 1 and "root cause" in response_text.lower():
        violations.append("BEHAV-002: Single hypothesis accepted")
        suggestions.append("Generate 3+ hypotheses upfront, test each systematically")

    # BEHAV-002-A: Zero-hypothesis flat assertion (evasion path)
    # Fires when a definitive implementation status claim is made with no hypothesis
    # framing at all AND no code-level evidence — the pattern MiniMax used in the
    # "lazy again.txt" incident (Status: Proposed → "NOT fully implemented").
    if hypothesis_count == 0:
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
        has_code_evidence = bool(re.search(
            r"(?:\.py|\.ts|\.js|\.go|\.rs)(?::\d+)?"   # file:line citation
            r"|Read\s+\d+\s+file"                        # Read tool usage
            r"|\bSearched\s+for\b"                       # Grep/search tool usage
            r"|\bline\s+\d+\b"                           # line number reference
            r"|(?:grep|glob)\s+\S",                      # direct grep/glob call
            response_text, re.IGNORECASE,
        ))
        if has_impl_claim and not has_code_evidence:
            violations.append("BEHAV-002-A: Zero-hypothesis definitive claim without code evidence")
            suggestions.append(
                "State 3+ hypotheses and verify via code search (Grep/Read) "
                "before asserting implementation status. 'Status: Proposed' in an ADR "
                "is NOT code evidence."
            )

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
        "suggestions": suggestions
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

    result = check_response_violations(response_text)
    if not result["violations"]:
        return None

    lines = [
        "VERIFICATION GATE VIOLATION DETECTED",
        "",
        f"Violations Found: {len(result['violations'])}",
    ]
    for i, violation in enumerate(result["violations"], 1):
        lines.append(f"  {i}. {violation}")
    lines.extend([
        "",
        f"Confidence: {result['confidence']:.0%}",
        "",
        "Required Actions:",
    ])
    for i, suggestion in enumerate(result["suggestions"], 1):
        lines.append(f"  {i}. {suggestion}")
    lines.extend([
        "",
        "See MEMORY.md protocols:",
        "  - Verification First Protocol",
        "  - Solution Proposal Gate",
        "  - Structured Diagnostic Protocol",
    ])
    return {
        "block": True,
        "reason": "\n".join(lines),
        "blocking_hook": "Stop_verification_gate.py",
    }

def main():
    """
    Stop hook entry point.

    Read Stop hook payload from stdin, check the response text, and emit
    structured JSON on stdout so hook_runner can relay the decision.
    """
    import sys

    raw_input = sys.stdin.read()
    response_text = raw_input

    if raw_input:
        try:
            parsed = json.loads(raw_input)
            if isinstance(parsed, dict):
                response_text = str(parsed.get("response", ""))
        except json.JSONDecodeError:
            response_text = raw_input

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
