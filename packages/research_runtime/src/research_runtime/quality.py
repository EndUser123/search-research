"""Deterministic research-quality telemetry for research-run.v1.

This module plans and assesses evidence quality; it does not invoke providers,
change routing, or authorize Phase 2A.  Its outputs are deliberately
conservative because discovery and source opening are not the same as proof.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from .router import TaskSignals

EVIDENCE_CATEGORIES = (
    "conceptual",
    "implementation",
    "authority",
    "compatibility",
    "maintenance",
    "failure",
    "local",
)

_CATEGORY_SUFFIX = {
    "conceptual": "concepts options tradeoffs",
    "implementation": "implementation source code example",
    "authority": "official documentation specification",
    "compatibility": "compatibility support version platform",
    "maintenance": "release activity maintenance status",
    "failure": "limitations failure modes issues risks",
    "local": "workspace repository prior decisions architecture",
}


def _words(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def required_evidence_categories(question: str, signals: TaskSignals) -> tuple[str, ...]:
    words = _words(question)
    categories: set[str] = set()
    if signals.needs_local_context or words & {"workspace", "repository", "our", "local", "prior"}:
        categories.add("local")
    if signals.needs_primary_source_verification or words & {"official", "authoritative", "authority", "identity", "backend", "specification", "standard", "api", "docs"}:
        categories.add("authority")
    if signals.requested_roles & {"IMPLEMENTATION_DISCOVERY", "REPOSITORY_PROJECT_DISCOVERY"} or words & {"implement", "implementation", "code", "build", "library", "repo", "repository"}:
        categories.add("implementation")
    if signals.requested_roles & {"COMPATIBILITY_RESEARCH"} or words & {"windows", "linux", "compatibility", "support", "version", "migration"}:
        categories.add("compatibility")
    if signals.requested_roles & {"MAINTENANCE_STATUS"} or words & {"maintained", "maintenance", "release", "active", "abandoned", "archived"}:
        categories.add("maintenance")
    if signals.requested_roles & {"OMISSION_SENSITIVE_DISCOVERY"} or words & {"failure", "failures", "risk", "risks", "limitation", "limitations", "cleanup", "timeout", "security", "production", "cancel"}:
        categories.add("failure")
    if signals.requested_roles & {"CONCEPTUAL_RECALL", "BROAD_EXTERNAL_DISCOVERY", "EXPLORATORY_RESEARCH"} or words & {"compare", "options", "approach", "adopt", "tradeoff", "choose", "should"}:
        categories.add("conceptual")
    if not categories:
        categories.add("conceptual")
    return tuple(category for category in EVIDENCE_CATEGORIES if category in categories)


def _inverse_eligible(question: str, signals: TaskSignals) -> tuple[bool, str]:
    words = _words(question)
    high_impact = signals.decision_impact in {"medium", "high", "critical"}
    explicit_risk = bool(words & {"security", "production", "authorization", "compatibility", "failure", "risk", "limitations", "cleanup", "timeout"})
    consequential_choice = bool(words & {"adopt", "choose", "should", "replace", "architecture", "policy"})
    if high_impact or explicit_risk or consequential_choice:
        return True, "bounded inverse search could change the decision"
    return False, "low-impact or descriptive lookup; inverse search is not justified by the request"


def plan_research_quality(question: str, signals: TaskSignals) -> dict[str, Any]:
    normalized = " ".join(question.split())
    categories = required_evidence_categories(normalized, signals)
    queries = [normalized]
    for category in categories:
        if len(queries) >= 4:
            break
        suffix = _CATEGORY_SUFFIX[category]
        if not _words(suffix).issubset(_words(normalized)):
            queries.append(f"{normalized} {suffix}")
    inverse, reason = _inverse_eligible(normalized, signals)
    return {
        "required_categories": list(categories),
        "targeted_queries": queries,
        "query_budget": 4,
        "inverse_search": {
            "eligible": inverse,
            "status": "planned_not_executed",
            "query": f"{normalized} limitations failures contradictory evidence" if inverse else None,
            "reason": reason,
        },
    }


def _source_category(source: dict[str, Any]) -> str:
    provider = str(source.get("provider", "")).lower()
    source_type = str(source.get("source_type", "")).lower()
    if provider == "qmd" or str(source.get("url", "")).startswith("qmd://"):
        return "local"
    if source_type == "primary" or "official" in str(source.get("title", "")).lower():
        return "authority"
    if provider in {"brave", "mmx"}:
        return "implementation"
    return "conceptual"


def assess_source_contribution(artifact: dict[str, Any]) -> dict[str, Any]:
    sources = artifact.get("sources", [])
    claims = artifact.get("claims", [])
    assessments = artifact.get("assessments", [])
    useful_ids: set[str] = set()
    for claim in claims:
        if claim.get("status") in {"supported", "partially_supported", "contradicted"}:
            useful_ids.update(claim.get("supporting_source_ids", []))
            useful_ids.update(claim.get("contradicting_source_ids", []))
    for assessment in assessments:
        if assessment.get("relationship") in {"directly_supports", "contradicts"}:
            useful_ids.add(str(assessment.get("source_id")))
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for source in sources:
        identity = str(source.get("url") or source.get("source_id"))
        duplicate = identity in seen
        seen.add(identity)
        status = source.get("discovery_status", "discovery_only")
        useful = str(source.get("source_id")) in useful_ids
        rows.append({
            "source_id": source.get("source_id"),
            "provider": source.get("provider"),
            "category": _source_category(source),
            "status": status,
            "useful": useful,
            "duplicate": duplicate,
            "contribution": "useful" if useful else ("opened_unassessed" if status in {"opened", "anchor_confirmed", "verified"} else "discovery_only"),
        })
    return {
        "sources": rows,
        "unique_useful_sources": sum(row["useful"] and not row["duplicate"] for row in rows),
        "opened_unassessed_sources": sum(row["contribution"] == "opened_unassessed" for row in rows),
        "duplicate_sources": sum(row["duplicate"] for row in rows),
        "category_counts": dict(Counter(row["category"] for row in rows if row["useful"] and not row["duplicate"])),
    }


def assess_stopping(plan: dict[str, Any], contribution: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    required = set(plan.get("required_categories", []))
    covered = set(contribution.get("category_counts", {}))
    missing = [category for category in plan.get("required_categories", []) if category not in covered]
    failures = [failure for lane in artifact.get("retrieval_lanes", []) for failure in lane.get("failures", [])]
    if not contribution.get("unique_useful_sources"):
        status = "insufficient"
        reason = "no opened source is linked to a claim-specific supporting or contradicting assessment"
    elif missing:
        status = "insufficient"
        reason = "required evidence categories remain uncovered"
    elif failures:
        status = "incomplete"
        reason = "useful evidence exists but one or more lane failures remain"
    else:
        status = "candidate_sufficient"
        reason = "all planned categories have claim-linked source contribution"
    return {
        "status": status,
        "reason": reason,
        "required_categories": list(plan.get("required_categories", [])),
        "covered_categories": [category for category in EVIDENCE_CATEGORIES if category in covered],
        "missing_categories": missing,
        "failure_count": len(failures),
        "authorization_effect": "evidence_gathering_only",
    }


def analyze_artifact(question: str, signals: TaskSignals, artifact: dict[str, Any]) -> dict[str, Any]:
    plan = plan_research_quality(question, signals)
    contribution = assess_source_contribution(artifact)
    stopping = assess_stopping(plan, contribution, artifact)
    return {"schema_version": "research-quality.v1", "plan": plan, "source_contribution": contribution, "stopping": stopping}
