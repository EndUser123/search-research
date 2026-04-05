#!/usr/bin/env python3
"""
Stop hook for /p skill - Halt format validator.

Validates that when /p outputs a HALT status, it follows the required format
AND shows evidence of real tool execution (not fabricated results).
"""

import json
import re
import sys
from pathlib import Path

# Add lib directory to path for imports
LIB_DIR = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

from evidence_patterns import (
    validate_p_response,
)


def main():
    # Read the LLM's response from stdin
    response_text = sys.stdin.read() if not sys.stdin.isatty() else ""

    # Use shared validation function for common checks
    allow, reason = validate_p_response(response_text, check_for_completion=False)

    if not allow:
        print(json.dumps({"allow": False, "reason": reason}))
        sys.exit(1)

    if "Not a /p response" in reason or "No halt detected" in reason:
        print(json.dumps({"allow": True, "reason": reason}))
        sys.exit(0)

    # Halt detected - validate format has required sections
    errors = []

    # Check for "Reason:" section
    if not re.search(r"\*\*Reason:\*\*", response_text, re.IGNORECASE):
        errors.append("Missing **Reason:** section explaining why the pipeline halted")

    # Check for "Next Steps:" section
    if not re.search(r"## Next Steps", response_text, re.IGNORECASE):
        errors.append("Missing ## Next Steps section with actionable items")

    # Check for the required numbered format: "1 - /tdd Fix", etc.
    numbered_format_checks = [
        r"1\s*-\s*/tdd Fix",
        r"2\s*-\s*/tdd Fix CRITICAL",
        r"3\s*-\s*/tdd Fix HIGH",
        r"4\s*-\s*/tdd Fix all findings",
        r"x\s*-\s*Fix all verified findings:",
        r"Then re-run:\s*/p",
    ]

    missing_formats = []
    for pattern in numbered_format_checks:
        if not re.search(pattern, response_text, re.IGNORECASE):
            missing_formats.append(pattern)

    if missing_formats:
        errors.append(
            "Missing required HALT format. Must use numbered format: "
            "'1 - /tdd Fix...', 'x - Fix all verified findings: N', 'Then re-run: /p'"
        )

    # Check for phase results table
    if not re.search(r"Phase\s+\d+", response_text):
        errors.append("Missing phase results (Phase 1, Phase 2, etc.)")

    # Block if format is incomplete
    if errors:
        error_msg = "HALT format validation failed:\n" + "\n".join(f"- {e}" for e in errors)
        print(json.dumps({
            "allow": False,
            "reason": error_msg + "\n\nHALT responses must include: Reason, Next Steps, phase results, and clear continuation path."
        }))
        sys.exit(1)

    # Format looks good - allow the response
    print(json.dumps({"allow": True, "reason": "HALT format validated"}))
    sys.exit(0)


if __name__ == "__main__":
    main()
