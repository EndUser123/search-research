from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from research_runtime.quality import analyze_artifact, plan_research_quality, required_evidence_categories
from research_runtime.router import TaskSignals


def test_categories_cover_local_authority_implementation_maintenance_and_failure() -> None:
    signals = TaskSignals(
        needs_local_context=True,
        needs_primary_source_verification=True,
        decision_impact="high",
        requested_roles=frozenset({"IMPLEMENTATION_DISCOVERY", "MAINTENANCE_STATUS", "COMPATIBILITY_RESEARCH", "OMISSION_SENSITIVE_DISCOVERY"}),
    )
    categories = required_evidence_categories("Should we adopt this Windows repository for production?", signals)
    assert categories == ("conceptual", "implementation", "authority", "compatibility", "maintenance", "failure", "local")


def test_quality_plan_is_bounded_and_inverse_is_plan_only() -> None:
    plan = plan_research_quality("Should we adopt a subprocess supervisor for production?", TaskSignals(decision_impact="high"))
    assert len(plan["targeted_queries"]) <= 4
    assert plan["inverse_search"]["eligible"] is True
    assert plan["inverse_search"]["status"] == "planned_not_executed"


def test_authority_identity_question_requires_authority_evidence() -> None:
    categories = required_evidence_categories(
        "What is the authoritative backend model identity of this worker?",
        TaskSignals(),
    )
    assert "authority" in categories


def test_source_contribution_and_stopping_are_conservative() -> None:
    artifact = {
        "sources": [{"source_id": "s1", "provider": "brave", "url": "https://example.test", "title": "Candidate", "source_type": "discovered-web", "discovery_status": "opened"}],
        "claims": [], "assessments": [], "retrieval_lanes": [{"failures": []}],
    }
    result = analyze_artifact("compare implementation options", TaskSignals(requested_roles=frozenset({"IMPLEMENTATION_DISCOVERY"})), artifact)
    assert result["source_contribution"]["unique_useful_sources"] == 0
    assert result["stopping"]["status"] == "insufficient"
