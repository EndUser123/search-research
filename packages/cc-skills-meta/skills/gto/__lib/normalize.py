from __future__ import annotations

from ..models import Finding

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
VALID_SEVERITIES = set(SEVERITY_ORDER)
VALID_ACTIONS = {"recover", "prevent", "realize"}
VALID_PRIORITIES = {"critical", "high", "medium", "low"}

DOMAIN_ALIASES: dict[str, str] = {
    "code_quality": "quality",
    "testing": "tests",
    "documentation": "docs",
    "dependencies": "deps",
}


def normalize_finding(f: Finding) -> Finding:
    """Normalize a finding's domain, severity, action, and priority."""
    domain = DOMAIN_ALIASES.get(f.domain, f.domain)
    severity = f.severity if f.severity in VALID_SEVERITIES else "medium"
    action = f.action if f.action in VALID_ACTIONS else "recover"
    priority = f.priority if f.priority in VALID_PRIORITIES else "medium"
    return Finding(
        id=f.id,
        title=f.title,
        description=f.description,
        source_type=f.source_type,
        source_name=f.source_name,
        domain=domain,
        gap_type=f.gap_type,
        severity=severity,
        evidence_level=f.evidence_level,
        action=action,
        priority=priority,
        status=f.status,
        scope=f.scope,
        owner_skill=f.owner_skill,
        owner_reason=f.owner_reason,
        file=f.file,
        line=f.line,
        symbol=f.symbol,
        reversibility=f.reversibility,
        effort=f.effort,
        target=f.target,
        depends_on=f.depends_on,
        evidence=f.evidence,
        tags=f.tags,
        terminal_id=f.terminal_id,
        session_id=f.session_id,
        git_sha=f.git_sha,
        freshness=f.freshness,
        unverified=f.unverified,
        metadata=f.metadata,
    )


def normalize_findings(findings: list[Finding]) -> list[Finding]:
    return [normalize_finding(f) for f in findings]
