"""Layer 4 — REQUIREMENTS: gto, spec-compliance, artifact status.

HARD DEPENDENCY: Layer 4 MUST NOT execute if Layer 2 (SEMANTIC) reported failures.
The orchestrator enforces this; this layer just runs its checks.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

from findings.models import EvidenceTier, Finding, Layer, Severity


def run(target: Path) -> list[Finding]:
    """Run Layer 4 REQUIREMENTS analysis."""
    findings: list[Finding] = []

    # gto gap analysis
    gto_findings = _run_gto(target)
    findings.extend(gto_findings)

    # spec-compliance check
    spec_findings = _run_spec_compliance(target)
    findings.extend(spec_findings)

    # Artifact status (CHANGELOG, README sync)
    artifact_findings = _check_artifact_status(target)
    findings.extend(artifact_findings)

    return findings


def _run_gto(target: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        result = subprocess.run(
            ["gto", "analyze", str(target)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and result.stdout:
            findings.append(
                Finding(
                    finding_id="L4-GTO-RESULTS",
                    severity=Severity.LOW,
                    layer=Layer.L4_REQUIREMENTS,
                    title="GTO gap analysis results",
                    description=result.stdout[:500],
                    evidence_tier=EvidenceTier.T3,
                    category="requirements",
                )
            )
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    return findings


def _run_spec_compliance(target: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        result = subprocess.run(
            ["spec-compliance", str(target)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0 and result.stdout:
            for line in result.stdout.splitlines():
                if line.strip():
                    findings.append(
                        Finding(
                            finding_id="L4-SPEC-NONCOMPLIANCE",
                            severity=Severity.MEDIUM,
                            layer=Layer.L4_REQUIREMENTS,
                            title="Spec compliance violation",
                            description=line.strip(),
                            evidence_tier=EvidenceTier.T3,
                            category="requirements",
                        )
                    )
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    return findings


def _check_artifact_status(target: Path) -> list[Finding]:
    """Check CHANGELOG is in sync with git tags (last 30 days)."""
    findings: list[Finding] = []

    # Check CHANGELOG exists
    changelog = target / "CHANGELOG.md"
    if not changelog.exists():
        findings.append(
            Finding(
                finding_id="L4-MISSING-CHANGELOG",
                severity=Severity.LOW,
                layer=Layer.L4_REQUIREMENTS,
                title="Missing CHANGELOG.md",
                description="No CHANGELOG.md found in target",
                evidence_tier=EvidenceTier.T3,
                category="requirements",
            )
        )
        return findings

    # Check for git tags in last 30 days without CHANGELOG entries
    try:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        result = subprocess.run(
            ["git", "tag", f"--since={cutoff}"],
            capture_output=True,
            text=True,
            cwd=str(target),
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            recent_tags = result.stdout.strip().splitlines()
            changelog_text = changelog.read_text(errors="ignore")
            for tag in recent_tags:
                if tag not in changelog_text:
                    findings.append(
                        Finding(
                            finding_id="L4-CHANGELOG-OUT-OF-SYNC",
                            severity=Severity.MEDIUM,
                            layer=Layer.L4_REQUIREMENTS,
                            title="CHANGELOG missing recent entries",
                            description=f"Git tag '{tag}' created in last 30 days with no CHANGELOG entry",
                            evidence_tier=EvidenceTier.T3,
                            category="requirements",
                        )
                    )
                    break  # One finding per layer is enough
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass

    return findings
