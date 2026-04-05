#!/usr/bin/env python3
"""
Stop hook for /p skill - Completion validator.

Validates that when /p completes successfully, it follows the required format
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
    allow, reason = validate_p_response(response_text, check_for_completion=True)

    if not allow:
        print(json.dumps({"allow": False, "reason": reason}))
        sys.exit(1)

    if "Not a /p response" in reason or "Not a completion message" in reason:
        print(json.dumps({"allow": True, "reason": reason}))
        sys.exit(0)

    # Completion detected - validate format has required sections
    errors = []

    # Check for "Summary:" section
    if not re.search(r"\*\*Summary:\*\*", response_text, re.IGNORECASE):
        errors.append("Missing **Summary:** section with brief overview")

    # Check for "Next Steps:" section
    if not re.search(r"## Next Steps", response_text, re.IGNORECASE):
        errors.append("Missing ## Next Steps section with actionable items")

    # Check for phase results table showing all phases passed
    phase_results_pattern = r"✅\s*Phase\s+\d+.*PASS"
    if not re.search(phase_results_pattern, response_text):
        errors.append("Missing phase results table showing each phase as PASS")

    # Block if format is incomplete
    if errors:
        error_msg = "Completion format validation failed:\n" + "\n".join(f"- {e}" for e in errors)
        print(json.dumps({
            "allow": False,
            "reason": error_msg + "\n\nCompletion responses must include: Summary, Next Steps, and phase results table."
        }))
        sys.exit(1)

    # Format looks good - allow the response
    print(json.dumps({"allow": True, "reason": "Completion format validated"}))
    sys.exit(0)


if __name__ == "__main__":
    main()
