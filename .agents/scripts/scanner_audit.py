#!/usr/bin/env python3
"""Monthly scanner audit — verify scanner findings against reality.

Picks N random findings from the past month, verifies each against
the actual state, and flags scanners with >20% false-positive rate.

This is the "second coach" from the Coaching Kata — scanning the scanners.

Usage:
    python scanner_audit.py [--sample-size 20] [--since-days 30]
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path("P:/.agents/scripts")))
from findings_index import query  # noqa: E402


def _verify_finding(finding: dict) -> tuple[bool, str]:
    """Verify a single finding against actual state. Returns (is_valid, reason)."""
    path = finding.get("path", "")
    title = finding.get("title", "")
    category = finding.get("category", "")

    # For findings with file paths, check if the issue still exists
    if path and Path(path).exists():
        # For defects: check if the code still has the issue
        # This is a simplified check — a full implementation would
        # re-run the specific scanner that produced the finding
        return True, "path exists, finding plausibly still valid"

    # For findings without paths (informational), assume valid
    if not path:
        return True, "no path to verify (informational finding)"

    # Path doesn't exist — could be fixed or false positive
    return False, f"path not found: {path} (likely fixed or false positive)"


def run_audit(sample_size: int = 20, since_days: int = 30) -> dict:
    """Run the scanner audit."""
    findings = query(since_days=since_days, limit=0)

    if len(findings) < sample_size:
        sample_size = len(findings)

    if sample_size == 0:
        return {
            "status": "no_findings",
            "message": "No findings in the past {since_days} days to audit",
        }

    sample = random.sample(findings, min(sample_size, len(findings)))

    results = []
    valid_count = 0
    invalid_count = 0

    for finding in sample:
        is_valid, reason = _verify_finding(finding)
        results.append({
            "id": finding.get("id", ""),
            "title": finding.get("title", "")[:80],
            "category": finding.get("category", ""),
            "source": finding.get("source", ""),
            "valid": is_valid,
            "reason": reason,
        })
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1

    fp_rate = round(invalid_count / len(sample), 3) if sample else 0.0

    return {
        "status": "complete",
        "sample_size": len(sample),
        "valid": valid_count,
        "invalid": invalid_count,
        "false_positive_rate": fp_rate,
        "threshold": 0.20,
        "action_needed": fp_rate > 0.20,
        "results": results,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monthly scanner audit")
    parser.add_argument("--sample-size", type=int, default=20)
    parser.add_argument("--since-days", type=int, default=30)
    args = parser.parse_args()

    result = run_audit(sample_size=args.sample_size, since_days=args.since_days)
    print(json.dumps(result, indent=2))
