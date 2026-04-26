from __future__ import annotations

"""
Findings Reviewer Agent — spawned via Claude Code Agent tool.

Reviews and validates findings from deterministic detectors and domain analyzers.
Removes duplicates, adjusts severities, and ensures evidence quality.
"""
from pathlib import Path
import json

from ..models import Finding, EvidenceRef, AgentResult


def write_handoff(path: Path, findings: list[Finding]) -> None:
    """Write findings for the reviewer agent to evaluate."""
    handoff = {
        "role": "findings_reviewer",
        "findings": [f.to_dict() for f in findings],
        "output_path": str(path.parent / "findings_reviewer_result.json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")


def read_result(path: Path) -> AgentResult:
    """Read the reviewer result from its output file."""
    if not path.exists():
        return AgentResult(agent="findings_reviewer", findings=[], success=False)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AgentResult(agent="findings_reviewer", findings=[], success=False)

    findings: list[Finding] = []
    for item in data.get("findings", []):
        if not isinstance(item, dict):
            continue
        if item.get("status") == "rejected":
            continue
        evidence = [
            EvidenceRef(kind=e.get("kind", ""), value=e.get("value", ""))
            for e in item.get("evidence", [])
            if isinstance(e, dict)
        ]
        findings.append(
            Finding(
                id=item.get("id", "REV-???"),
                title=item.get("title", "Reviewed finding"),
                description=item.get("description", ""),
                source_type="agent",
                source_name="findings_reviewer",
                domain=item.get("domain", "other"),
                gap_type=item.get("gap_type", "unknown"),
                severity=item.get("severity", "medium"),
                evidence_level=item.get("evidence_level", "unverified"),
                action=item.get("action", "recover"),
                priority=item.get("priority", "medium"),
                file=item.get("file"),
                line=item.get("line"),
                effort=item.get("effort"),
                unverified=item.get("unverified", True),
                evidence=evidence,
            )
        )

    return AgentResult(
        agent="findings_reviewer",
        findings=findings,
        raw_notes=data.get("notes", ""),
        success=True,
    )
