from __future__ import annotations

"""
Action Normalizer Agent — spawned via Claude Code Agent tool.

Normalizes findings: ensures valid domains, severities, actions, priorities,
and adds effort estimates for findings that lack them.
"""
from pathlib import Path
import json

from ..models import Finding, EvidenceRef, AgentResult


def write_handoff(path: Path, findings: list[Finding]) -> None:
    """Write findings for the normalizer agent to process."""
    handoff = {
        "role": "action_normalizer",
        "findings": [f.to_dict() for f in findings],
        "output_path": str(path.parent / "action_normalizer_result.json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")


def read_result(path: Path) -> AgentResult:
    """Read the normalizer result from its output file."""
    if not path.exists():
        return AgentResult(agent="action_normalizer", findings=[], success=False)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AgentResult(agent="action_normalizer", findings=[], success=False)

    findings: list[Finding] = []
    for item in data.get("findings", []):
        if not isinstance(item, dict):
            continue
        evidence = [
            EvidenceRef(kind=e.get("kind", ""), value=e.get("value", ""))
            for e in item.get("evidence", [])
            if isinstance(e, dict)
        ]
        findings.append(
            Finding(
                id=item.get("id", "NORM-???"),
                title=item.get("title", "Normalized finding"),
                description=item.get("description", ""),
                source_type=item.get("source_type", "agent"),
                source_name=item.get("source_name", "action_normalizer"),
                domain=item.get("domain", "other"),
                gap_type=item.get("gap_type", "unknown"),
                severity=item.get("severity", "medium"),
                evidence_level=item.get("evidence_level", "unverified"),
                action=item.get("action", "recover"),
                priority=item.get("priority", "medium"),
                file=item.get("file"),
                line=item.get("line"),
                effort=item.get("effort"),
                unverified=item.get("unverified", False),
                evidence=evidence,
            )
        )

    return AgentResult(
        agent="action_normalizer",
        findings=findings,
        raw_notes=data.get("notes", ""),
        success=True,
    )
