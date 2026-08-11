from __future__ import annotations

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from research_runtime.phase2a import admit_falsifier, build_bounded_query, validate_phase2a_record
from research_runtime.evaluate_phase2a_prospective import _trigger


def _record():
    falsifiers = [
        {"falsifier_id": "f1", "claim_id": "c", "statement": "specific contradiction", "query": "specific query", "decision_relevance": "would reject the action", "evidence_terms": ["source"], "anchor_terms": ["specific"], "contradiction_terms": ["unsupported"], "outcome": "tested", "applicable": True},
        {"falsifier_id": "f2", "claim_id": "c", "statement": "second contradiction", "query": "second query", "decision_relevance": "would narrow scope", "evidence_terms": ["issue"], "anchor_terms": ["second"], "contradiction_terms": ["limitation"], "outcome": "noisy", "applicable": True},
    ]
    return {"case_id": "case", "claim_id": "c", "affirmative_action": "usable_evidence", "disconfirmation_action": "narrowed_scope", "falsifiers": falsifiers, "reconciliation": {"claim_id": "c", "original_action": "usable_evidence", "revised_action": "narrowed_scope", "outcome": "narrowed_scope", "changed": True, "basis_falsifier_ids": ["f1"], "noisy_falsifier_ids": ["f2"], "false_contradiction_count": 0, "additional_evidence_required": False, "limitation": "bounded source sample"}}


def test_phase2a_contract_accepts_specific_falsifiers_and_reconciliation():
    validate_phase2a_record(_record())


def test_phase2a_contract_rejects_malformed_falsifiers():
    record = _record()
    record["falsifiers"] = [{"applicable": True}]
    with pytest.raises(ValueError, match="falsifier_missing_falsifier_id"):
        validate_phase2a_record(record)


def test_admission_rejects_generic_and_duplicate_falsifiers():
    generic = {"claim_id": "c", "statement": "There may be security concerns.", "query": "security issue", "decision_relevance": "might matter"}
    admitted, reasons = admit_falsifier(generic, claim_id="c")
    assert not admitted
    assert "generic_risk" in reasons
    first = {"claim_id": "c", "statement": "The source is conceptual only.", "query": "source conceptual implementation", "decision_relevance": "would narrow scope"}
    admitted, reasons = admit_falsifier(first, claim_id="c", prior=(first,))
    assert not admitted
    assert "duplicates_another_falsifier" in reasons


def test_query_builder_rejects_keyword_only_and_preserves_anchor():
    with pytest.raises(ValueError, match="query_too_generic"):
        build_bounded_query({"query": "problem failure issue bad"})
    query = build_bounded_query({"query": "runtime compatibility release", "anchor_terms": ["agentic workflow"]})
    assert '"agentic workflow"' in query


def test_prospective_trigger_skips_low_impact_lookup_and_selects_consequential_case():
    low = {"impact": "low", "reversibility": "high", "omission_sensitivity": "low", "trigger_expected": False}
    high = {"impact": "high", "reversibility": "low", "omission_sensitivity": "high", "trigger_expected": True}
    assert _trigger(low)["produced"] is False
    assert _trigger(high)["produced"] is True
