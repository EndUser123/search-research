from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from research_runtime.evaluate_quality_execution import CASES, decision_changed, signals_for  # noqa: E402
from research_runtime.quality import plan_research_quality  # noqa: E402


def test_execution_corpus_has_fifteen_bounded_cases() -> None:
    assert len(CASES) == 15
    assert all(len(plan_research_quality(question, signals_for(question, kind))["targeted_queries"]) <= 4 for _, question, kind in CASES)


def test_candidate_is_one_supplemental_query_and_not_inverse_automation() -> None:
    question = "Should we adopt a maintained repository for agentic coding workflows?"
    plan = plan_research_quality(question, signals_for(question, "adoption"))
    assert len(plan["targeted_queries"]) >= 2
    assert plan["inverse_search"]["status"] == "planned_not_executed"


def test_decision_change_is_action_change_not_claim_status_detail() -> None:
    assert decision_changed({"stop_reason": "insufficient", "claim_status": []}, {"stop_reason": "insufficient", "claim_status": ["unverified"]}) is False
