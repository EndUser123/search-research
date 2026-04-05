"""Layer 1 — SYNTACTIC: ruff, mypy, AI Distiller structure analysis."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from findings.models import EvidenceTier, Finding, Layer, Severity


def _run_ruff(target: Path) -> list[Finding]:
    """Run ruff check on Python files."""
    findings: list[Finding] = []
    py_files = list(target.rglob("*.py"))
    if not py_files:
        return findings

    try:
        result = subprocess.run(
            ["ruff", "check", str(target), "--output-format=json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        # ruff returns 0 (no issues), 1 (issues found), >=2 (error)
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                for item in data:
                    loc = item.get("location", {})
                    findings.append(
                        Finding(
                            finding_id=f"L1-RUFF-{item.get('code', 'UNK')}",
                            severity=Severity.MEDIUM,  # ruff violations default MEDIUM
                            layer=Layer.L1_SYNTACTIC,
                            title=item.get("message", "Ruff violation"),
                            description=item.get("description", ""),
                            location=f"{item.get('filename')}:{loc.get('row', 0)}",
                            evidence_tier=EvidenceTier.T1,
                            category="syntax",
                        )
                    )
            except json.JSONDecodeError:
                pass
    except subprocess.TimeoutExpired:
        findings.append(
            Finding(
                finding_id="L1-RUFF-TIMEOUT",
                severity=Severity.MEDIUM,
                layer=Layer.L1_SYNTACTIC,
                title="Ruff check timed out after 60s",
                description="Ruff subprocess exceeded 60s timeout",
                evidence_tier=EvidenceTier.T3,
                category="timeout",
            )
        )
    except FileNotFoundError:
        pass  # ruff not available, skip
    return findings


def _run_mypy(target: Path) -> list[Finding]:
    """Run mypy type check on Python files."""
    findings: list[Finding] = []
    py_files = list(target.rglob("*.py"))
    if not py_files:
        return findings

    try:
        result = subprocess.run(
            ["mypy", str(target), "--output-format=json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.stdout:
            try:
                data = json.loads(result.stdout)
                for item in data:
                    findings.append(
                        Finding(
                            finding_id=f"L1-MYPY-{item.get('code', 'UNK')}",
                            severity=Severity.HIGH,
                            layer=Layer.L1_SYNTACTIC,
                            title=item.get("message", "Type error"),
                            description=f"{item.get('file', '')}:{item.get('line', 0)}",
                            location=f"{item.get('file')}:{item.get('line', 0)}",
                            evidence_tier=EvidenceTier.T2,
                            category="type",
                        )
                    )
            except json.JSONDecodeError:
                pass
    except subprocess.TimeoutExpired:
        findings.append(
            Finding(
                finding_id="L1-MYPY-TIMEOUT",
                severity=Severity.MEDIUM,
                layer=Layer.L1_SYNTACTIC,
                title="Mypy timed out after 60s",
                description="Mypy subprocess exceeded 60s timeout",
                evidence_tier=EvidenceTier.T3,
                category="timeout",
            )
        )
    except FileNotFoundError:
        pass  # mypy not available, skip
    return findings


def _run_aid(target: Path) -> list[Finding]:
    """Run AI Distiller structure analysis."""
    findings: list[Finding] = []
    try:
        result = subprocess.run(
            ["aid", "distill", "--path", str(target), "--format=json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout:
            try:
                data = json.loads(result.stdout)
                for item in data.get("structures", []):
                    findings.append(
                        Finding(
                            finding_id=f"L1-AID-{item.get('id', 'UNK')}",
                            severity=Severity.LOW,
                            layer=Layer.L1_SYNTACTIC,
                            title=item.get("name", "Structure issue"),
                            description=item.get("description", ""),
                            evidence_tier=EvidenceTier.T3,
                            category="structure",
                        )
                    )
            except json.JSONDecodeError:
                pass
    except subprocess.TimeoutExpired:
        pass  # aid timeout, skip gracefully
    except FileNotFoundError:
        pass  # aid not available
    return findings


def run(target: Path) -> list[Finding]:
    """Run Layer 1 SYNTACTIC analysis."""
    findings: list[Finding] = []

    # ruff on Python files
    ruff_findings = _run_ruff(target)
    findings.extend(ruff_findings)

    # mypy on Python files
    mypy_findings = _run_mypy(target)
    findings.extend(mypy_findings)

    # AI Distiller structure analysis
    aid_findings = _run_aid(target)
    findings.extend(aid_findings)

    return findings
