#!/usr/bin/env python
"""P6 Main Entry Point - Security Phase.

This is the main entry point for P6 security phase.
Can be invoked as: python P:/.claude/skills/p/scripts/p6_main.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from cve_scan import check_cves
from security import main as security_main


def main() -> int:
    """Run P6 security scanning phase."""
    if len(sys.argv) < 2:
        print("Usage: p6 <target>")
        print("\nP6 Security Scanning:")
        print("  1. Bandit static analysis (code security)")
        print("  2. pip-audit CVE scan (dependency vulnerabilities)")
        return 1

    target = sys.argv[1]

    print("## P6: Security Scanning")
    print(f"Target: {target}")
    print()

    # Step 1: Bandit security scan
    print("### Step 1: Bandit Static Analysis")
    bandit_result = security_main()
    print()

    # Step 2: CVE scan
    print("### Step 2: Dependency CVE Scan")
    cve_result = check_cves()
    print()

    # Overall result
    print("## P6 Security Summary")
    if bandit_result == 0 and cve_result == 0:
        print("✅ PASS: All security checks passed")
        return 0
    elif bandit_result == 2 or cve_result == 2:
        print("❌ FAIL: High/Critical security issues found - HALT")
        return 2
    else:
        print("⚠️  WARN: Security issues found - review recommended")
        return 1


if __name__ == "__main__":
    sys.exit(main())
