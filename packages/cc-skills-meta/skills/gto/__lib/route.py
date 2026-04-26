from __future__ import annotations

from ..models import Finding

# Maps gap_type prefixes to owning skills.
# Findings not matching any route remain unrouted (owner_skill=None).
GAP_TYPE_ROUTES: dict[str, str] = {
    "missingdocs": "/docs",
    "techdebt": "/code",
    "runtime_error": "/diagnose",
    "bug": "/diagnose",
    "security": "/security",
    "perf": "/perf",
    "invalidrepo": "/git",
    "staledeps": "/deps",
}


def route_finding(f: Finding) -> Finding:
    """Route a single finding to an owning skill based on gap_type."""
    owner = GAP_TYPE_ROUTES.get(f.gap_type)
    if owner:
        return Finding(
            id=f.id,
            title=f.title,
            description=f.description,
            source_type=f.source_type,
            source_name=f.source_name,
            domain=f.domain,
            gap_type=f.gap_type,
            severity=f.severity,
            evidence_level=f.evidence_level,
            action=f.action,
            priority=f.priority,
            status=f.status,
            scope=f.scope,
            owner_skill=owner,
            owner_reason=f"routed by gap_type '{f.gap_type}'",
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
    return f


def route_findings(findings: list[Finding]) -> list[Finding]:
    return [route_finding(f) for f in findings]
