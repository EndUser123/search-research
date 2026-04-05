#!/usr/bin/env python3
"""
Analyze assumption audit compliance rates.

Usage:
    python analyze_audit_compliance.py [--days N]
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

LOG_FILE = Path("P:/.claude/hooks/logs/test_assumption_audit.jsonl")


def analyze(days: int = 7):
    if not LOG_FILE.exists():
        print("No audit log found.")
        return

    cutoff = datetime.now() - timedelta(days=days)

    triggers = []
    compliance_checks = []

    with open(LOG_FILE) as f:
        for line in f:
            try:
                entry = json.loads(line)
                ts = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                if ts.replace(tzinfo=None) < cutoff:
                    continue

                if entry["event"] == "trigger":
                    triggers.append(entry)
                elif entry["event"] == "compliance_check":
                    compliance_checks.append(entry)
            except (json.JSONDecodeError, KeyError):
                continue

    print(f"=== Assumption Audit Compliance Report (last {days} days) ===\n")
    print(f"Audit triggers: {len(triggers)}")
    print(f"Compliance checks: {len(compliance_checks)}")

    if compliance_checks:
        complied = sum(1 for c in compliance_checks if c.get("complied"))
        ignored = len(compliance_checks) - complied
        rate = (complied / len(compliance_checks)) * 100 if compliance_checks else 0

        print(f"\nCompliance rate: {rate:.1f}%")
        print(f"  - Complied (used tools or marked [UNVERIFIED]): {complied}")
        print(f"  - Ignored (no tools, no marker): {ignored}")

        # Show recent non-compliant cases
        if ignored > 0:
            print("\n--- Recent Non-Compliant Cases ---")
            non_compliant = [c for c in compliance_checks if not c.get("complied")][-5:]
            for c in non_compliant:
                print(f"  {c.get('pending_timestamp', '?')[:19]}: {c.get('pending_snippet', '')[:60]}...")
    else:
        print("\nNo compliance checks yet (need at least one followup after audit).")

    print()


if __name__ == "__main__":
    days = 7
    if len(sys.argv) > 2 and sys.argv[1] == "--days":
        days = int(sys.argv[2])
    analyze(days)
