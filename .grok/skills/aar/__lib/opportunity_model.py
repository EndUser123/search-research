"""Typed opportunity model for the continual-improvement AAR.

Per spec Sections 2-10, 13-17: ``/aar`` must support a *first-class*
opportunity landscape, not just failure-derived defect tickets. An
opportunity is any evidence-grounded possibility to improve future value,
effectiveness, efficiency, reliability, usability, learning, or optionality
— including opportunities revealed by success, friction, capability
discovery, reuse, combination, simplification, user experience, or continual
learning.

This module provides the typed primitives every opportunity must use:

* 12 source classes (``OpportunitySourceClass``)
* 6 horizons (``OpportunityHorizon``)
* 16 mechanisms (``OpportunityMechanism``)
* 7 value-accounting categories (``ValueCategory`` / ``ValueAccounting``)
* 10 dispositions including continual-improvement lifecycle states
  (``OpportunityDisposition``)
* 12 expected-value dimensions with bounded ordinal ratings
  (``ExpectedValueDimension`` / ``ExpectedValueRating``)
* 5 revision classifications (``RevisionClassification``)
* the ``Opportunity`` dataclass with full evidence-to-opportunity
  traceability fields (spec Section 8)
* a ``RejectedOpportunityLedger`` that prevents re-proposal of already-ruled-
  out ideas (spec Section 15)

Design invariants
-----------------
* **Opportunity ≠ gap.** A gap is observed; an opportunity is the
  hypothesised improvement. The dataclass requires both an
  ``observed_evidence`` field and an ``interpretation`` field so the
  LLM cannot jump from symptom to solution.
* **No generic opportunities.** The validator rejects opportunities whose
  title or mechanism is on the generic-phrase blocklist (spec Section 8).
* **Every opportunity carries a falsifier and next_evidence_needed.** An
  opportunity without a falsifier is overclaiming.
* **Dispositions support continual improvement.** ``BOUNDED_EXPERIMENT``,
  ``MONITOR``, ``REUSE_EXISTING``, ``SIMPLIFY_OR_REMOVE``, ``PRESERVE``,
  ``DEFER``, ``REJECT``, ``NOT_WORTH_DOING`` are all first-class — a
  no-change conclusion is a valid outcome.
* **Cross-session candidates are emission-only.** This module produces
  ``ImprovementCandidate`` records that may be aggregated *only by explicit
  authorized external mechanism* (spec Section 17). It never reads other
  sessions.

This module performs **no causal interpretation**. It defines the structure
the LLM must fill and the validator enforces.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "OpportunitySourceClass",
    "OpportunityHorizon",
    "OpportunityMechanism",
    "ValueCategory",
    "OpportunityDisposition",
    "ExpectedValueDimension",
    "ExpectedValueRating",
    "RevisionClassification",
    "ExpectedValueRating",
    "Opportunity",
    "ValueAccounting",
    "ValueEntry",
    "ImprovementCandidate",
    "RejectedOpportunity",
    "RejectedOpportunityLedger",
    "GENERIC_OPPORTUNITY_PHRASES",
    "OPPORTUNITY_SCHEMA_VERSION",
    "is_generic_opportunity_title",
]


OPPORTUNITY_SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Enums (all values are the literal strings used in reports/packets)
# ---------------------------------------------------------------------------


class OpportunitySourceClass(str, Enum):
    """Spec Section 3: 12 source classes.

    An opportunity may cite one or more. The source class drives which
    discovery pass (A-H) surfaced it and what evidence is expected.
    """

    FAILURE_DERIVED = "FAILURE_DERIVED"
    FRICTION_DERIVED = "FRICTION_DERIVED"
    SUCCESS_DERIVED = "SUCCESS_DERIVED"
    CAPABILITY_DERIVED = "CAPABILITY_DERIVED"
    REUSE_DERIVED = "REUSE_DERIVED"
    COMBINATION_DERIVED = "COMBINATION_DERIVED"
    SIMPLIFICATION_DERIVED = "SIMPLIFICATION_DERIVED"
    RISK_DERIVED = "RISK_DERIVED"
    USER_EXPERIENCE_DERIVED = "USER_EXPERIENCE_DERIVED"
    LEARNING_DERIVED = "LEARNING_DERIVED"
    STRATEGIC_OPTION_DERIVED = "STRATEGIC_OPTION_DERIVED"
    EXTERNAL_EVIDENCE_DERIVED = "EXTERNAL_EVIDENCE_DERIVED"


class OpportunityHorizon(str, Enum):
    """Spec Section 6: 6 horizons for expected realisation window."""

    IMMEDIATE_LOCAL = "IMMEDIATE_LOCAL"
    NEAR_TERM_WORKFLOW = "NEAR_TERM_WORKFLOW"
    CROSS_SKILL_REUSE = "CROSS_SKILL_REUSE"
    SYSTEM_CAPABILITY = "SYSTEM_CAPABILITY"
    STRATEGIC_OPTION = "STRATEGIC_OPTION"
    CONTINUAL_LEARNING = "CONTINUAL_LEARNING"


class OpportunityMechanism(str, Enum):
    """Spec Section 7: 16 mechanisms. ``NO_CHANGE_PRESERVE`` is first-class."""

    REMOVE = "REMOVE"
    SIMPLIFY = "SIMPLIFY"
    MERGE = "MERGE"
    RESEQUENCE = "RESEQUENCE"
    AUTOMATE = "AUTOMATE"
    VALIDATE = "VALIDATE"
    INSTRUMENT = "INSTRUMENT"
    REUSE = "REUSE"
    GENERALIZE = "GENERALIZE"
    SPECIALIZE = "SPECIALIZE"
    INTEGRATE = "INTEGRATE"
    EXPERIMENT = "EXPERIMENT"
    DOCUMENT = "DOCUMENT"
    TRAIN_OR_PROMPT = "TRAIN_OR_PROMPT"
    CHANGE_DECISION_RULE = "CHANGE_DECISION_RULE"
    NO_CHANGE_PRESERVE = "NO_CHANGE_PRESERVE"


class ValueCategory(str, Enum):
    """Spec Section 5: 7 value-accounting categories.

    A category may be empty — the spec says "Do not force every category to
    contain an item". The ValueAccounting container records which were
    populated and which were explicitly empty.
    """

    VALUE_CREATED = "VALUE_CREATED"
    VALUE_PRESERVED = "VALUE_PRESERVED"
    VALUE_RECOVERED = "VALUE_RECOVERED"
    VALUE_UNREALIZED = "VALUE_UNREALIZED"
    VALUE_DEFERRED = "VALUE_DEFERRED"
    VALUE_DESTROYED_OR_COST = "VALUE_DESTROYED_OR_COST"
    VALUE_COMPOUNDED = "VALUE_COMPOUNDED"


class OpportunityDisposition(str, Enum):
    """Spec Section 14: 10 dispositions.

    The first three trigger implementation / experiment / investigation.
    The remainder govern the continual-improvement lifecycle without
    requiring action this session.
    """

    ACT_NOW = "ACT_NOW"
    BOUNDED_EXPERIMENT = "BOUNDED_EXPERIMENT"
    INVESTIGATE = "INVESTIGATE"
    MONITOR = "MONITOR"
    REUSE_EXISTING = "REUSE_EXISTING"
    SIMPLIFY_OR_REMOVE = "SIMPLIFY_OR_REMOVE"
    PRESERVE = "PRESERVE"
    DEFER = "DEFER"
    REJECT = "REJECT"
    NOT_WORTH_DOING = "NOT_WORTH_DOING"


class ExpectedValueDimension(str, Enum):
    """Spec Section 9: 12 expected-value dimensions.

    Each material opportunity is rated on each applicable dimension using
    a bounded ordinal (``ExpectedValueRating``) plus a one-line rationale.
    No fabricated numeric precision.
    """

    OUTCOME_IMPACT = "outcome_impact"
    FREQUENCY_OR_REACH = "frequency_or_reach"
    RELIABILITY_GAIN = "reliability_gain"
    EFFICIENCY_GAIN = "efficiency_gain"
    USER_EXPERIENCE_GAIN = "user_experience_gain"
    LEARNING_OR_REUSE_GAIN = "learning_or_reuse_gain"
    IMPLEMENTATION_COST = "implementation_cost"
    MAINTENANCE_COST = "maintenance_cost"
    COGNITIVE_BURDEN = "cognitive_burden"
    RISK_OF_HARM = "risk_of_harm"
    REVERSIBILITY = "reversibility"
    EVIDENCE_STRENGTH = "evidence_strength"


class ExpectedValueRating(str, Enum):
    """Bounded ordinal ratings for expected-value dimensions.

    * ``VERY_HIGH`` / ``HIGH`` / ``MEDIUM`` / ``LOW`` / ``NEGLIGIBLE``
    * ``UNKNOWN`` — explicit when the rater cannot responsibly estimate.

    Costs/burdens use the same scale: ``HIGH`` cost is bad, ``HIGH`` impact
    is good. The interpretation is dimension-specific; the rating is
    direction-agnostic and the rationale clarifies.
    """

    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NEGLIGIBLE = "NEGLIGIBLE"
    UNKNOWN = "UNKNOWN"


class RevisionClassification(str, Enum):
    """Spec Section 12: 5 classifications for a changed conclusion.

    The classification is the difference between healthy updating (new
    information or user preference) and avoidable rework (evidence was
    available but unexamined, or an assumption was unchecked).
    """

    HEALTHY_UPDATE_NEW_INFORMATION = "HEALTHY_UPDATE_NEW_INFORMATION"
    HEALTHY_UPDATE_USER_PREFERENCE = "HEALTHY_UPDATE_USER_PREFERENCE"
    AVOIDABLE_UPDATE_MISSED_AVAILABLE_EVIDENCE = "AVOIDABLE_UPDATE_MISSED_AVAILABLE_EVIDENCE"
    AVOIDABLE_UPDATE_UNVERIFIED_ASSUMPTION = "AVOIDABLE_UPDATE_UNVERIFIED_ASSUMPTION"
    AMBIGUOUS_REVISION = "AMBIGUOUS_REVISION"


class ExistingCapabilityStatus(str, Enum):
    """6-value classification of whether a proposed intervention's target
    capability/rule/workflow already exists.

    * ``ABSENT`` — no existing capability addresses this opportunity.
    * ``EXISTS_AND_EFFECTIVE`` — exists and is doing the job.
    * ``EXISTS_BUT_NOT_INVOKED`` — exists but isn't being applied; the
      opportunity is to fix invocation, not to build.
    * ``EXISTS_BUT_INEFFECTIVE`` — exists but the existing form doesn't work;
      the opportunity is to improve effectiveness, not to build.
    * ``PARTIAL_OVERLAP`` — partial overlap with something else; "no change"
      or "remove duplication" may be the right disposition.
    * ``UNKNOWN`` — cannot responsibly classify without more evidence.

    Required per HYBRID refinement: distinguishes "create new" from "reuse
    existing", "improve invocation", "improve compliance", "improve
    effectiveness", "remove duplication", and "no change".
    """

    ABSENT = "ABSENT"
    EXISTS_AND_EFFECTIVE = "EXISTS_AND_EFFECTIVE"
    EXISTS_BUT_NOT_INVOKED = "EXISTS_BUT_NOT_INVOKED"
    EXISTS_BUT_INEFFECTIVE = "EXISTS_BUT_INEFFECTIVE"
    PARTIAL_OVERLAP = "PARTIAL_OVERLAP"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Generic-opportunity blocklist (spec Section 8)
# ---------------------------------------------------------------------------

#: Phrases that signal a non-concrete, generic opportunity. The validator
#: rejects any opportunity whose title or interpretation contains one.
#: Case-insensitive substring match.
GENERIC_OPPORTUNITY_PHRASES: tuple[str, ...] = (
    "improve communication",
    "do more research",
    "automate this",  # bare "automate this" without target — "automate the X preflight" passes
    "add validation",  # bare — "add validation for X credential" passes
    "use better prompts",
    "be more careful",
    "improve quality",
    "do better",
    "fix the process",
)


_GENERIC_RE = re.compile(
    r"(?:^|\W)(" + "|".join(re.escape(p) for p in GENERIC_OPPORTUNITY_PHRASES) + r")(?:\W|$)",
    re.IGNORECASE,
)


def is_generic_opportunity_title(text: str) -> bool:
    """Return True if ``text`` matches a generic-opportunity phrase.

    Used by the validator to reject speculative/vague opportunities. Matches
    a generic phrase only when it appears as the *whole* title or its tail
    (e.g. "add validation" alone or "we should add validation" both fail;
    "add validation for the credential preflight" passes because a concrete
    target follows the phrase).

    The heuristic: if text after the generic phrase (trimmed) is empty, the
    opportunity is generic. If a concrete noun phrase follows, it is not.
    """
    if not text or not text.strip():
        return True  # empty title is trivially generic
    stripped = text.strip()
    for phrase in GENERIC_OPPORTUNITY_PHRASES:
        m = re.search(re.escape(phrase), stripped, re.IGNORECASE)
        if not m:
            continue
        tail = stripped[m.end():].strip()
        # Allow common separators (",", ":", "for", "to", "by", "via", "in",
        # "on", "at", "before", "after") before the concrete target — but
        # require SOMETHING concrete after them.
        tail_cleaned = re.sub(r"^(?:for|to|by|via|in|on|at|before|after|of|the|a|an|that|would|should|could|we|i)\b[\s,,:]*", "", tail, flags=re.IGNORECASE).strip()
        if not tail_cleaned:
            return True
        # Heuristic: if the tail is shorter than 4 chars or has no letter, generic.
        if len(tail_cleaned) < 4 or not re.search(r"[A-Za-z]", tail_cleaned):
            return True
    return False


# ---------------------------------------------------------------------------
# Core dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValueEntry:
    """One value-accounting entry. Spec Section 5.

    ``category`` plus a concrete description plus the evidence event ids
    that substantiate it. ``kind`` distinguishes "the session produced X"
    from "X was available but not captured".
    """

    category: ValueCategory
    description: str
    supporting_event_ids: tuple[str, ...] = ()
    beneficiary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "description": self.description,
            "supporting_event_ids": list(self.supporting_event_ids),
            "beneficiary": self.beneficiary,
        }


@dataclass(frozen=True)
class ValueAccounting:
    """The full value ledger for one session. Spec Section 5.

    Categories not populated are simply absent from ``entries``. The
    ``to_dict`` always emits all 7 keys with the entries listed so consumers
    can distinguish "explicitly empty" from "not considered".
    """

    entries: tuple[ValueEntry, ...] = ()

    def by_category(self, category: ValueCategory) -> tuple[ValueEntry, ...]:
        return tuple(e for e in self.entries if e.category is category)

    def categories_populated(self) -> frozenset[ValueCategory]:
        return frozenset(e.category for e in self.entries)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for cat in ValueCategory:
            out[cat.value] = [e.to_dict() for e in self.by_category(cat)]
        return {"entries_total": len(self.entries), "by_category": out}


@dataclass(frozen=True)
class Opportunity:
    """One evidence-grounded improvement opportunity.

    Spec Section 8 mandatory field set. The validator enforces all of these
    are present and non-generic. Construct via the keyword-only fields; do
    not invent values — fields that cannot be grounded should be left empty
    and the opportunity downgraded to ``REJECT`` or ``DEFER`` with a reason.
    """

    opportunity_id: str
    title: str
    source_classes: tuple[OpportunitySourceClass, ...]
    horizon: OpportunityHorizon
    mechanism: OpportunityMechanism
    supporting_event_ids: tuple[str, ...]
    observed_evidence: str
    interpretation: str
    value_expected: str
    beneficiary: str
    frequency_or_reach: str
    disposition: OpportunityDisposition
    falsifier: str
    next_evidence_needed: str
    expected_value: dict[ExpectedValueDimension, tuple[ExpectedValueRating, str]] = field(default_factory=dict)
    confidence: str = "UNKNOWN"  # OBSERVED / INFERRED / SPECULATIVE
    key_assumptions: tuple[str, ...] = ()
    cost_or_burden: str | None = None
    from_superseded_history: bool = False
    #: HYBRID refinement (prior comparative eval): explicit per-opportunity
    #: existing-capability classification. ``None`` means the LLM declined to
    #: classify (acceptable for low-stakes opportunities).
    existing_capability_status: ExistingCapabilityStatus | None = None
    #: Free-text rationale for the classification (1 sentence).
    existing_capability_evidence: str | None = None
    # Continual-improvement lifecycle (spec Section 14) — required when
    # disposition is MONITOR, BOUNDED_EXPERIMENT, INVESTIGATE, or DEFER.
    lifecycle: "OpportunityLifecycle | None" = None

    def to_dict(self) -> dict[str, Any]:
        out = {
            "opportunity_id": self.opportunity_id,
            "title": self.title,
            "source_classes": [s.value for s in self.source_classes],
            "horizon": self.horizon.value,
            "mechanism": self.mechanism.value,
            "supporting_event_ids": list(self.supporting_event_ids),
            "observed_evidence": self.observed_evidence,
            "interpretation": self.interpretation,
            "value_expected": self.value_expected,
            "beneficiary": self.beneficiary,
            "frequency_or_reach": self.frequency_or_reach,
            "disposition": self.disposition.value,
            "falsifier": self.falsifier,
            "next_evidence_needed": self.next_evidence_needed,
            "expected_value": {
                dim.value: {"rating": rating.value, "rationale": rationale}
                for dim, (rating, rationale) in self.expected_value.items()
            },
            "confidence": self.confidence,
            "key_assumptions": list(self.key_assumptions),
            "cost_or_burden": self.cost_or_burden,
            "from_superseded_history": self.from_superseded_history,
            "existing_capability_status": (
                self.existing_capability_status.value
                if self.existing_capability_status is not None
                else None
            ),
            "existing_capability_evidence": self.existing_capability_evidence,
        }
        if self.lifecycle is not None:
            out["lifecycle"] = self.lifecycle.to_dict()
        else:
            out["lifecycle"] = None
        return out


@dataclass(frozen=True)
class OpportunityLifecycle:
    """Spec Section 14: lifecycle record for non-ACT_NOW dispositions.

    Required when disposition is MONITOR, BOUNDED_EXPERIMENT, INVESTIGATE,
    or DEFER. The validator flags opportunities with those dispositions and
    no lifecycle as incomplete.
    """

    hypothesis: str
    evidence_needed: str
    success_signal: str
    failure_signal: str
    review_trigger: str
    retirement_condition: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis,
            "evidence_needed": self.evidence_needed,
            "success_signal": self.success_signal,
            "failure_signal": self.failure_signal,
            "review_trigger": self.review_trigger,
            "retirement_condition": self.retirement_condition,
        }


@dataclass(frozen=True)
class ImprovementCandidate:
    """Spec Section 17: structured candidate for authorised cross-session aggregation.

    Emission-only: this record may be *written* to a terminal-scoped
    artifact. It must NOT be automatically consumed across sessions. Any
    aggregation requires an explicit user-authorized mechanism using
    supplied artifact paths.
    """

    candidate_id: str
    hypothesis: str
    local_evidence: str
    scope: str  # SESSION_SPECIFIC / PROBLEM_CLASS / GENERAL
    confidence: str  # OBSERVED / INFERRED / SPECULATIVE
    expected_value: str
    future_signal: str
    promotion_condition: str
    retirement_condition: str
    source_opportunity_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "hypothesis": self.hypothesis,
            "local_evidence": self.local_evidence,
            "scope": self.scope,
            "confidence": self.confidence,
            "expected_value": self.expected_value,
            "future_signal": self.future_signal,
            "promotion_condition": self.promotion_condition,
            "retirement_condition": self.retirement_condition,
            "source_opportunity_id": self.source_opportunity_id,
        }


# ---------------------------------------------------------------------------
# Rejection ledger (spec Section 15: prevent re-proposal)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RejectedOpportunity:
    """One rejected opportunity, kept to prevent re-proposal.

    Includes a normalised ``fingerprint`` (lowercased title + mechanism) so
    future LLM runs can check "have we already ruled this out?" before
    emitting a duplicate.
    """

    opportunity_id: str
    title: str
    mechanism: OpportunityMechanism
    rejection_reason: str
    rejected_at: str  # ISO-8601
    fingerprint: str
    original_disposition: OpportunityDisposition

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "title": self.title,
            "mechanism": self.mechanism.value,
            "rejection_reason": self.rejection_reason,
            "rejected_at": self.rejected_at,
            "fingerprint": self.fingerprint,
            "original_disposition": self.original_disposition.value,
        }


class RejectedOpportunityLedger:
    """Append-only ledger of rejected opportunities.

    Loaded from and saved to a terminal-scoped JSON file. The AAR checks
    this before emitting new opportunities: if a candidate's fingerprint
    matches a prior rejection, the LLM must cite new evidence to re-open it.

    Per spec Section 17: this is terminal-scoped, never auto-aggregated
    across sessions.
    """

    def __init__(self, entries: tuple[RejectedOpportunity, ...] = ()) -> None:
        self._entries: list[RejectedOpportunity] = list(entries)

    def add(self, entry: RejectedOpportunity) -> None:
        self._entries.append(entry)

    def __iter__(self):
        return iter(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    def fingerprints(self) -> frozenset[str]:
        return frozenset(e.fingerprint for e in self._entries)

    def contains_fingerprint(self, fingerprint: str) -> bool:
        return fingerprint in self.fingerprints()

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries_total": len(self._entries),
            "entries": [e.to_dict() for e in self._entries],
        }


# ---------------------------------------------------------------------------
# Fingerprinting
# ---------------------------------------------------------------------------

_FP_NORMALISER_RE = re.compile(r"[^a-z0-9 ]+")


def opportunity_fingerprint(title: str, mechanism: OpportunityMechanism | str) -> str:
    """Normalised fingerprint for dedup against the rejection ledger.

    Lowercases, strips non-alphanumeric, collapses whitespace, appends the
    mechanism. Two opportunities with the same fingerprint are considered
    duplicates for re-proposal purposes.
    """
    mech = mechanism.value if isinstance(mechanism, OpportunityMechanism) else str(mechanism)
    title_norm = _FP_NORMALISER_RE.sub(" ", (title or "").lower()).strip()
    title_norm = re.sub(r"\s+", " ", title_norm)
    return f"{title_norm}::{mech.lower()}"
