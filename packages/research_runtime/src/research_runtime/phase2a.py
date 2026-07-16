"""Minimal Phase 2A falsifier and reconciliation contract.

This module contains data-shape validation only. It does not generate claims,
choose providers, or decide truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

GENERIC_RISK_PATTERNS = ("there may be", "could be worse", "may have problems", "security concerns")
DECISION_CHANGE_TERMS = ("reject", "remove", "narrow", "reduce", "require", "add", "guardrail", "authorization", "confidence", "scope")


FALSIFIER_OUTCOMES = frozenset({"tested", "not_tested", "no_evidence", "source_open_failed", "noisy"})
RECONCILIATION_OUTCOMES = frozenset({
    "survived", "narrowed_scope", "reduced_confidence", "added_tests_or_guardrails",
    "reduced_authorization", "required_more_evidence", "rejected_conclusion",
})


@dataclass(frozen=True)
class FalsifierSpec:
    falsifier_id: str
    claim_id: str
    statement: str
    query: str
    decision_relevance: str
    evidence_terms: tuple[str, ...]
    contradiction_terms: tuple[str, ...]
    applicable: bool = True


def admit_falsifier(falsifier: dict[str, Any], *, claim_id: str, prior: tuple[dict[str, Any], ...] = ()) -> tuple[bool, tuple[str, ...]]:
    """Conservative deterministic admission before any provider call."""
    reasons: list[str] = []
    if falsifier.get("claim_id") != claim_id:
        reasons.append("claim_binding_mismatch")
    statement = str(falsifier.get("statement", "")).strip().lower()
    query = str(falsifier.get("query", "")).strip()
    relevance = str(falsifier.get("decision_relevance", "")).lower()
    if any(pattern in statement for pattern in GENERIC_RISK_PATTERNS):
        reasons.append("generic_risk")
    if not any(term in relevance for term in DECISION_CHANGE_TERMS):
        reasons.append("not_decision_changing")
    if not query or len(query.split()) < 4:
        reasons.append("not_externally_testable")
    if falsifier.get("already_resolved", False):
        reasons.append("already_answered_by_affirmative_evidence")
    fingerprint = " ".join(statement.split())
    for item in prior:
        if fingerprint and fingerprint == " ".join(str(item.get("statement", "")).lower().split()):
            reasons.append("duplicates_another_falsifier")
            break
    if falsifier.get("admission_status") == "rejected":
        reasons.extend(str(reason) for reason in falsifier.get("rejection_reasons", ()))
    return not reasons, tuple(dict.fromkeys(reasons))


def build_bounded_query(falsifier: dict[str, Any]) -> str:
    """Keep the concrete hypothesis in the provider query; reject keyword-only queries."""
    query = str(falsifier.get("query", "")).strip()
    generic = {"problem", "failure", "issue", "bad"}
    meaningful = {word.lower().strip('"') for word in query.split()} - generic
    if len(meaningful) < 3:
        raise ValueError("query_too_generic")
    anchors = tuple(str(item).strip() for item in falsifier.get("anchor_terms", ()) if str(item).strip())
    if anchors and not any(anchor.lower() in query.lower() for anchor in anchors):
        query = f'{query} "{anchors[0]}"'
    return query


@dataclass(frozen=True)
class Reconciliation:
    claim_id: str
    original_action: str
    revised_action: str
    outcome: str
    changed: bool
    basis_falsifier_ids: tuple[str, ...]
    noisy_falsifier_ids: tuple[str, ...]
    false_contradiction_count: int
    additional_evidence_required: bool
    limitation: str


def validate_phase2a_record(record: dict[str, Any]) -> None:
    """Validate the compact fields required by the Phase 2A evaluator."""
    for field in ("case_id", "claim_id", "affirmative_action", "disconfirmation_action", "falsifiers", "reconciliation"):
        if field not in record:
            raise ValueError(f"missing_{field}")
    falsifiers = record["falsifiers"]
    if not isinstance(falsifiers, list) or not 0 <= len([item for item in falsifiers if item.get("applicable", True)]) <= 5:
        raise ValueError("falsifier_count_out_of_bounds")
    ids: set[str] = set()
    for item in falsifiers:
        for field in ("falsifier_id", "claim_id", "statement", "query", "decision_relevance", "evidence_terms", "anchor_terms", "contradiction_terms", "outcome"):
            if field not in item:
                raise ValueError(f"falsifier_missing_{field}")
        if item["falsifier_id"] in ids:
            raise ValueError("duplicate_falsifier_id")
        ids.add(item["falsifier_id"])
        if item["outcome"] not in FALSIFIER_OUTCOMES:
            raise ValueError("invalid_falsifier_outcome")
        if item.get("admission_status") == "rejected" and not item.get("rejection_reasons"):
            raise ValueError("rejected_falsifier_missing_reasons")
    reconciliation = record["reconciliation"]
    for field in ("claim_id", "original_action", "revised_action", "outcome", "changed", "basis_falsifier_ids", "noisy_falsifier_ids", "false_contradiction_count", "additional_evidence_required", "limitation"):
        if field not in reconciliation:
            raise ValueError(f"reconciliation_missing_{field}")
    if reconciliation["outcome"] not in RECONCILIATION_OUTCOMES:
        raise ValueError("invalid_reconciliation_outcome")
    if any(item not in ids for item in reconciliation["basis_falsifier_ids"] + reconciliation["noisy_falsifier_ids"]):
        raise ValueError("reconciliation_unknown_falsifier")
