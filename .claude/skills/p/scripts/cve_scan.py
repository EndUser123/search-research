#!/usr/bin/env python3
"""
P6 CVE Scanning - pip-audit dependency vulnerability checking

Migrated from /v Stage 7.5: CVE Scan using pip-audit.
Checks for known CVEs in dependencies.

Usage:
    python cve_scan.py

Exit codes:
- 0 = No vulnerabilities (PASS)
- 1 = Low/Medium CVEs found (WARN)
- 2 = High/Critical CVEs found (FAIL/HALT)
- 3 = Error occurred (tool not installed)
"""

import subprocess
import sys


def check_cves() -> int:
    """
    Check for dependency vulnerabilities using pip-audit.

    Returns:
        0 = PASS (no vulnerabilities)
        1 = WARN (low/medium severity CVEs)
        2 = FAIL (high/critical severity CVEs - HALT)
        3 = ERROR (pip-audit not installed)
    """
    # Prevent blue console flash on Windows
    creation_flags = 0x08000000 if sys.platform == 'win32' else 0

    # Check if pip-audit is installed
    check_result = subprocess.run(
        ['pip-audit', '--version'],
        capture_output=True,
        text=True,
        creationflags=creation_flags
    )

    if check_result.returncode != 0:
        print("❌ PIP-AUDIT NOT INSTALLED")
        print("   Install: pip install pip-audit")
        return 3

    # Run pip-audit with strict mode (exit on vulnerabilities)
    result = subprocess.run(
        ['pip-audit', '--strict', '--progress-spinner=off'],
        capture_output=True,
        text=True,
        creationflags=creation_flags
    )

    # pip-audit returns:
    # 0 = no vulnerabilities
    # 1 = vulnerabilities found

    if result.returncode == 0:
        print("✅ CVE SCAN: No known vulnerabilities found")
        return 0

    # Parse output for severity
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    # Combine stdout and stderr for parsing
    output = f"{stdout}\n{stderr}" if stderr else stdout

    # Check for high/critical severity indicators
    high_critical_indicators = ['CRITICAL', 'HIGH', 'CVSS:7.0', 'CVSS:8.0', 'CVSS:9.0', 'CVSS:10.0']
    has_high_critical = any(indicator in output for indicator in high_critical_indicators)

    if has_high_critical:
        print("❌ CVE SCAN: High/Critical vulnerabilities found")
        print("   Update dependencies before deployment")

        # Show first few vulnerabilities
        lines = output.split('\n')
        vuln_lines = [l for l in lines if 'CVE' in l or 'vulnerable' in l.lower()]

        for line in vuln_lines[:5]:
            print(f"  {line}")

        if len(vuln_lines) > 5:
            print(f"  ... and {len(vuln_lines) - 5} more")
            print("  Run: pip-audit -v for full details")

        return 2

    else:
        print("⚠️  CVE SCAN: Low/Medium vulnerabilities found")
        print("   Recommend updating dependencies when convenient")

        # Show summary
        for line in output.split('\n')[:10]:
            if line.strip():
                print(f"  {line}")

        return 1


if __name__ == '__main__':
    sys.exit(check_cves())
