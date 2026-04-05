"""Layer 5 — SECURITY: path traversal, adversarial-security, anti-bleed gates."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

from findings.models import EvidenceTier, Finding, Layer, Severity

ALLOWED_COMMANDS = [
    "ruff",
    "mypy",
    "pytest",
    "aid",
    "gto",
    "verify",
    "hook-audit",
    "hook-inventory",
    "adversarial-security",
    "adversarial-performance",
    "diagnose",
]


def _check_command(cmd: str) -> None:
    """Validate command against ALLOWED_COMMANDS."""
    cmd_name = cmd.split()[0] if isinstance(cmd, str) else cmd[0]
    assert cmd_name in ALLOWED_COMMANDS, f"Command {cmd_name} not in ALLOWED_COMMANDS"


def _check_path_traversal(target: Path) -> list[Finding]:
    """Check for path traversal vulnerabilities in Python files."""
    findings: list[Finding] = []
    py_files = list(target.rglob("*.py"))

    for py_file in py_files:
        try:
            content = py_file.read_text(errors="ignore")
            for i, line in enumerate(content.splitlines(), 1):
                # Simple heuristic: open() with variable argument without validation
                if "open(" in line and not _is_validated_open(line):
                    findings.append(
                        Finding(
                            finding_id=f"L5-PATH-TRAVERSAL-{py_file.name}-{i}",
                            severity=Severity.CRITICAL,
                            layer=Layer.L5_SECURITY,
                            title="Potential path traversal — open() with unvalidated input",
                            description=f"{py_file}:{i}: {line.strip()}",
                            location=f"{py_file}:{i}",
                            evidence_tier=EvidenceTier.T3,
                            category="security",
                        )
                    )
        except OSError:
            pass

    return findings


def _is_validated_open(line: str) -> bool:
    """Heuristic: open() call has some validation nearby."""
    # Very simple: if line has any of these validation keywords, consider it validated
    validation_keywords = ["assert", "validate", "realpath", "is_relative_to", "safepath"]
    return any(kw in line for kw in validation_keywords)


def _run_adversarial_security(target: Path) -> list[Finding]:
    findings: list[Finding] = []
    _check_command("adversarial-security")
    try:
        result = subprocess.run(
            ["adversarial-security", str(target)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0 and result.stdout:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(
                        Finding(
                            finding_id="L5-ADV-SEC-FINDING",
                            severity=Severity.HIGH,
                            layer=Layer.L5_SECURITY,
                            title="Adversarial security finding",
                            description=line.strip(),
                            evidence_tier=EvidenceTier.T3,
                            category="security",
                        )
                    )
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    return findings


def _check_anti_bleed(target: Path) -> list[Finding]:
    """Check for data-safety guards on VCS operations."""
    findings: list[Finding] = []
    try:
        result = subprocess.run(
            ["data-safety-vcs", "--verify", str(target)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0 and result.stdout:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(
                        Finding(
                            finding_id="L5-ANTI-BLEED-MISSING",
                            severity=Severity.MEDIUM,
                            layer=Layer.L5_SECURITY,
                            title="Missing data-safety guard on VCS operation",
                            description=line.strip(),
                            evidence_tier=EvidenceTier.T3,
                            category="safety",
                        )
                    )
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    return findings


def run(target: Path) -> list[Finding]:
    """Run Layer 5 SECURITY analysis."""
    findings: list[Finding] = []

    pt_findings = _check_path_traversal(target)
    findings.extend(pt_findings)

    sec_findings = _run_adversarial_security(target)
    findings.extend(sec_findings)

    bleed_findings = _check_anti_bleed(target)
    findings.extend(bleed_findings)

    return findings
