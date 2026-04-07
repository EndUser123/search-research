#!/usr/bin/env python3
"""
Stop hook for /sqa skill - Completion validator.

Validates that when /sqa completes, it follows the required format
AND shows evidence of real tool execution (not fabricated results).

Adapted from /p StopHook_p_completion_validator.py.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Add lib directory to path for imports
LIB_DIR = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

from sqa_evidence_patterns import validate_sqa_response


def main() -> None:
    # Read the LLM's response from stdin
    response_text = sys.stdin.read() if not sys.stdin.isatty() else ""

    # Use shared validation function for common checks
    allow, reason = validate_sqa_response(response_text, check_for_completion=True)

    if not allow:
        print(json.dumps({"allow": False, "reason": reason}))
        sys.exit(1)

    if "Not a /sqa response" in reason or "Not a completion message" in reason:
        print(json.dumps({"allow": True, "reason": reason}))
        sys.exit(0)

    # Completion detected - validate format has required sections
    errors: list[str] = []

    # Check for health score section
    if not re.search(r"health.?score", response_text, re.IGNORECASE):
        errors.append("Missing health score in output")

    # Check for layers completed section or table
    if not re.search(r"L\d+", response_text):
        errors.append("Missing layer references (L0-L7, META)")

    # Check for findings summary
    if not re.search(r"finding", response_text, re.IGNORECASE):
        errors.append("Missing findings summary")

    # Check for target being certified
    if not re.search(r"certif|targe|analy", response_text, re.IGNORECASE):
        errors.append("Missing target or certification context")

    # Block if format is incomplete
    if errors:
        error_msg = "Completion format validation failed:\n" + "\n".join(
            f"- {e}" for e in errors
        )
        print(
            json.dumps(
                {
                    "allow": False,
                    "reason": error_msg
                    + "\n\nCompletion responses must include: health score, layer references, findings summary.",
                }
            )
        )
        sys.exit(1)

    # Format looks good - allow the response
    print(json.dumps({"allow": True, "reason": "Completion format validated"}))
    sys.exit(0)


if __name__ == "__main__":
    main()
