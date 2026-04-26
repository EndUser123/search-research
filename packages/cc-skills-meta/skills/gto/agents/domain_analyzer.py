from __future__ import annotations

"""
Domain Analyzer Agent — spawned via Claude Code Agent tool.

This module provides the agent specification and handoff contract
for the domain analyzer subagent. The actual execution happens via
Agent(subagent_type="general-purpose", prompt=...) in Claude Code.

The agent reads a handoff JSON file, performs analysis, and writes
results back to a designated output file.
"""
from pathlib import Path
import json

from ..models import Finding, EvidenceRef, AgentResult


def write_handoff(path: Path, target: str, root: str, domains: list[str] | None = None) -> None:
    """Write the handoff JSON for the domain analyzer agent."""
    handoff = {
        "role": "domain_analyzer",
        "target": target,
        "root": root,
        "domains": domains or ["quality", "tests", "docs", "security", "performance"],
        "output_path": str(path.parent / "domain_analyzer_result.json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")


def read_result(path: Path) -> AgentResult:
    """Read the domain analyzer result from its output file."""
    if not path.exists():
        return AgentResult(agent="domain_analyzer", findings=[], success=False)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AgentResult(agent="domain_analyzer", findings=[], success=False)

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
                id=item.get("id", "AGENT-???"),
                title=item.get("title", "Agent finding"),
                description=item.get("description", ""),
                source_type="agent",
                source_name="domain_analyzer",
                domain=item.get("domain", "other"),
                gap_type=item.get("gap_type", "unknown"),
                severity=item.get("severity", "medium"),
                evidence_level="unverified",
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
        agent="domain_analyzer",
        findings=findings,
        raw_notes=data.get("notes", ""),
        success=True,
    )
