"""Findings data models for SQA Orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class Layer(Enum):
    """SQA quality layers."""

    L1_SYNTACTIC = "L1_SYNTACTIC"
    L2_SEMANTIC = "L2_SEMANTIC"
    L3_STRUCTURAL = "L3_STRUCTURAL"
    L4_REQUIREMENTS = "L4_REQUIREMENTS"
    L5_SECURITY = "L5_SECURITY"
    L6_PERFORMANCE = "L6_PERFORMANCE"
    L7_OPERATIONAL = "L7_OPERATIONAL"
    META = "META"


class Severity(Enum):
    """Finding severity levels."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class EvidenceTier(Enum):
    """Evidence quality tiers."""

    T1 = "T1"  # Direct execution/observation
    T2 = "T2"  # Instrumented test
    T3 = "T3"  # Logical inference
    T4 = "T4"  # Heuristic/assumption


@dataclass
class Evidence:
    """Evidence supporting a finding."""

    tier: EvidenceTier
    description: str
    location: str | None = None  # file:line when applicable


@dataclass
class Finding:
    """A quality finding from one layer."""

    finding_id: str  # e.g. "L1-001"
    severity: Severity
    layer: Layer
    title: str
    description: str
    location: str | None = None  # file:line when applicable
    evidence_tier: EvidenceTier = EvidenceTier.T3
    consensus: int = 1  # Number of layers that found this issue
    category: str = "general"
    evidence: list[Evidence] = field(default_factory=list)

    def key(self) -> tuple[str, str, str, str]:
        """Deduplication key: (file, line, category, issue_type)."""
        loc = self.location or ""
        parts = loc.rsplit(":", 1)
        file = parts[0] if parts else ""
        line = parts[1] if len(parts) > 1 else ""
        return (file, line, self.category, self.title)


@dataclass
class AuditEntry:
    """Record of a skill/tool invocation."""

    timestamp: str  # ISO format
    skill: str
    exit_code: int | None
    finding_count: int
    notes: str | None = None


@dataclass
class SQAReport:
    """Complete SQA analysis report."""

    findings: list[Finding] = field(default_factory=list)
    health_score: int = 100
    layers_completed: list[str] = field(default_factory=list)
    audit_trail: list[AuditEntry] = field(default_factory=list)
    target: str = ""

    def add_finding(self, finding: Finding) -> None:
        """Add a finding (append-only)."""
        self.findings.append(finding)

    def add_audit(self, entry: AuditEntry) -> None:
        """Add an audit entry (append-only)."""
        self.audit_trail.append(entry)

    def compute_health_score(self) -> int:
        """Compute health score from deduplicated severity counts.

        Uses deduplicated severity counts (D4 deduplication removes
        consensus duplicates before scoring). Negative scores preserved.
        """
        # Deduplicate findings by key, keeping highest severity per key
        seen: dict[tuple[str, str, str, str], Finding] = {}
        for f in self.findings:
            k = f.key()
            if k not in seen or _severity_order(seen[k].severity) < _severity_order(f.severity):
                seen[k] = f

        unique = list(seen.values())
        crit = sum(1 for f in unique if f.severity == Severity.CRITICAL)
        high = sum(1 for f in unique if f.severity == Severity.HIGH)
        med = sum(1 for f in unique if f.severity == Severity.MEDIUM)
        low = sum(1 for f in unique if f.severity == Severity.LOW)

        score = 100 - crit * 20 - high * 10 - med * 5 - low * 2
        return max(-100, score)

    def deduplicated_findings(self) -> list[Finding]:
        """Return findings deduplicated by (file, line, category, title).

        For duplicate keys, keeps the finding with highest severity.
        """
        seen: dict[tuple[str, str, str, str], Finding] = {}
        for f in self.findings:
            k = f.key()
            if k not in seen or _severity_order(seen[k].severity) < _severity_order(f.severity):
                seen[k] = f
        return list(seen.values())


def _severity_order(sev: Severity) -> int:
    """Return sort order for severity (higher = more severe)."""
    return {Severity.CRITICAL: 4, Severity.HIGH: 3, Severity.MEDIUM: 2, Severity.LOW: 1}[sev]
