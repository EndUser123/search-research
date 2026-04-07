#!/usr/bin/env python3
"""StopHook_premortem_quality_gate — validates pre-mortem output quality before synthesis.

Per ADR-20260329: Phase 3 synthesis should not proceed if findings are missing
critical evidence (file:line citations for HIGH/CRITICAL, non-empty findings array,
valid severity tags).

Exit codes: 0 = allow, 2 = block.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


def run(data: dict) -> dict:
    """Validate pre-mortem Phase 1 findings quality.

    Requires:
    - findings array is non-empty
    - HIGH/CRITICAL findings have file:line citations
    - all severity tags are valid
    """
    findings = data.get("findings", [])

    # QA-001: findings must not be empty
    if not findings:
        return {
            "decision": "block",
            "reason": "findings array is empty — nothing to synthesize",
        }

    # QA-002: severity tags must be valid
    invalid_severities = set()
    for f in findings:
        sev = f.get("severity", "").upper()
        if sev not in VALID_SEVERITIES:
            invalid_severities.add(sev)

    if invalid_severities:
        return {
            "decision": "block",
            "reason": f"Invalid severity tags: {sorted(invalid_severities)}",
        }

    # QA-003: HIGH/CRITICAL findings must have file:line citations
    missing_citations = []
    file_line_pattern = re.compile(r"^.+?:\d+")

    for f in findings:
        sev = f.get("severity", "").upper()
        if sev in ("HIGH", "CRITICAL"):
            location = f.get("location", "")
            if not file_line_pattern.match(location):
                missing_citations.append(f.get("id", "UNKNOWN"))

    if missing_citations:
        return {
            "decision": "block",
            "reason": f"HIGH/CRITICAL findings lack file:line citation: {', '.join(missing_citations)}",
        }

    return {"decision": "allow"}


if __name__ == "__main__":
    input_data = json.load(sys.stdin)
    result = run(input_data)
    print(json.dumps(result))
    sys.exit(0 if result["decision"] == "allow" else 2)
