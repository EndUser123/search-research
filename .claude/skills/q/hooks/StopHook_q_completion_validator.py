#!/usr/bin/env python3
"""
Stop hook for /q skill - completion format validator.

Validates that /q completion output includes required sections.
Recognizes both clean and degraded completions.
"""

import json
import re
import sys


def main() -> None:
    response_text = sys.stdin.read() if not sys.stdin.isatty() else ""

    if "/q" not in response_text.lower() and "q pipeline" not in response_text.lower():
        print(json.dumps({"allow": True, "reason": "Not a /q response"}))
        sys.exit(0)

    complete_indicators = [
        r"Q Pipeline Status: COMPLETE",
        r"Q PIPELINE COMPLETE",
        r"\*\*Status:\*\*\s*✅\s*(ALL PHASES PASSED|COMPLETE)",
        r"\*\*Status:\*\*\s*⚠️\s*COMPLETE with warnings",
        r"ALL Q PHASES PASSED",
        r"Status:\s*READY",
    ]
    is_complete = any(re.search(p, response_text, re.IGNORECASE) for p in complete_indicators)
    if not is_complete:
        print(json.dumps({"allow": True, "reason": "Not a completion message"}))
        sys.exit(0)

    errors = []
    if not re.search(r"\*\*Summary:\*\*", response_text, re.IGNORECASE):
        errors.append("Missing **Summary:** section")
    if not re.search(r"## Next Steps", response_text, re.IGNORECASE):
        errors.append("Missing ## Next Steps section")
    if not re.search(r"[✅⚠️]\s*Q[1-6]", response_text):
        errors.append("Missing q-phase results (e.g., ✅ Q1 ... or ⚠️ Q2 ...)")

    if errors:
        msg = "Completion format validation failed:\n" + "\n".join(f"- {e}" for e in errors)
        print(
            json.dumps(
                {
                    "allow": False,
                    "reason": msg + "\n\n/q completion responses must include Summary, Next Steps, and q-phase results.",
                }
            )
        )
        sys.exit(1)

    print(json.dumps({"allow": True, "reason": "Completion format validated"}))
    sys.exit(0)


if __name__ == "__main__":
    main()
