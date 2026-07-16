"""Explicit evidence-to-claim assessment with conservative aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


RELATIONSHIPS = {"directly_supports", "partially_supports", "contradicts", "contextual_only", "insufficient"}
AUTHORITIES = {"primary", "secondary", "runtime", "unknown"}
CURRENCIES = {"current", "possibly_stale", "stale", "unknown"}
METHODS = {"caller_supplied", "reference_evaluator", "model_assisted", "deterministic_anchor_only"}


@dataclass(frozen=True)
class ClaimRequirement:
    required_authorities: frozenset[str] = frozenset()
    require_current: bool = False
    require_direct_support: bool = False
    required_methods: frozenset[str] = frozenset()


@dataclass(frozen=True)
class EvidenceAssessment:
    claim_id: str
    source_id: str
    source_location: str
    passage_or_anchor: str
    relationship: str
    authority: str
    currency: str
    assessment_method: str
    assessment_basis: str
    assessed_at: str
    limitations: tuple[str, ...] = ()
    run_id: str | None = None
    source_identity: str | None = None
    source_status: str = "discovery_only"


@dataclass(frozen=True)
class ClaimAssessment:
    claim_id: str
    status: str
    supporting_source_ids: tuple[str, ...]
    contradicting_source_ids: tuple[str, ...]
    rationale: tuple[str, ...]


def _valid_iso(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def validate_assessment(item: EvidenceAssessment) -> tuple[str, ...]:
    errors: list[str] = []
    if item.relationship not in RELATIONSHIPS:
        errors.append("relationship_invalid")
    if item.authority not in AUTHORITIES:
        errors.append("authority_invalid")
    if item.currency not in CURRENCIES:
        errors.append("currency_invalid")
    if item.assessment_method not in METHODS:
        errors.append("assessment_method_invalid")
    if not item.claim_id or not item.source_id or not item.source_location or not item.passage_or_anchor:
        errors.append("source_binding_incomplete")
    if not _valid_iso(item.assessed_at):
        errors.append("assessed_at_invalid")
    return tuple(errors)


def assess_claim(
    claim_id: str,
    assessments: Iterable[EvidenceAssessment],
    requirement: ClaimRequirement = ClaimRequirement(),
    *,
    expected_run_id: str | None = None,
) -> ClaimAssessment:
    """Aggregate explicit assessments without confidence scoring or inference."""

    items = [item for item in assessments if item.claim_id == claim_id]
    invalid = [item for item in items if validate_assessment(item)]
    if expected_run_id is not None:
        invalid.extend(item for item in items if item.run_id != expected_run_id)
    if not items:
        return ClaimAssessment(claim_id, "unverified", (), (), ("no_assessment",))

    # One underlying source contributes once. A duplicate URL cannot multiply support.
    unique: dict[str, EvidenceAssessment] = {}
    for item in items:
        identity = item.source_identity or item.source_id
        existing = unique.get(identity)
        if existing is None or (existing.assessment_method == "model_assisted" and item.assessment_method != "model_assisted"):
            unique[identity] = item
    usable = [item for item in unique.values() if not validate_assessment(item) and (expected_run_id is None or item.run_id == expected_run_id)]
    direct_support = [item for item in usable if item.relationship == "directly_supports" and item.source_status in {"opened", "anchor_confirmed", "verified"}]
    partial_support = [item for item in usable if item.relationship == "partially_supports" and item.source_status in {"opened", "anchor_confirmed", "verified"}]
    contradiction = [item for item in usable if item.relationship == "contradicts" and item.source_status in {"opened", "anchor_confirmed", "verified"} and item.authority != "unknown"]
    acceptable_support = [item for item in direct_support + partial_support if item.authority in requirement.required_authorities or not requirement.required_authorities]
    if contradiction:
        return ClaimAssessment(claim_id, "contradicted", tuple(item.source_id for item in acceptable_support), tuple(item.source_id for item in contradiction), ("credible_opened_contradiction",))
    if not acceptable_support:
        return ClaimAssessment(claim_id, "unverified", (), (), ("no_adequate_opened_support",))
    if any(item.relationship == "partially_supports" for item in acceptable_support):
        return ClaimAssessment(claim_id, "supported", tuple(item.source_id for item in acceptable_support), (), ("support_is_partial",))
    if requirement.require_current and any(item.currency != "current" for item in direct_support):
        return ClaimAssessment(claim_id, "supported", tuple(item.source_id for item in acceptable_support), (), ("currency_requirement_incomplete",))
    if requirement.require_direct_support and not direct_support:
        return ClaimAssessment(claim_id, "supported", tuple(item.source_id for item in acceptable_support), (), ("direct_support_required",))
    if requirement.required_methods and not any(item.assessment_method in requirement.required_methods for item in direct_support):
        return ClaimAssessment(claim_id, "supported", tuple(item.source_id for item in acceptable_support), (), ("verification_method_requirement_incomplete",))
    if any(item.assessment_method in {"deterministic_anchor_only", "model_assisted"} for item in direct_support):
        return ClaimAssessment(claim_id, "supported", tuple(item.source_id for item in acceptable_support), (), ("advisory_or_anchor_only",))
    return ClaimAssessment(claim_id, "verified", tuple(item.source_id for item in direct_support), (), ("authority_directness_currency_and_method_satisfied",))
