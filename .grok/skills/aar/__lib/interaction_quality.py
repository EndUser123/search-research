"""Interaction-quality analytical concepts for `/aar`.

Per the spec (Sections 3–14), the AAR must support a class of failure
analysis that goes beyond counting proximate mistakes. This module
provides:

* 7 analytical concept categories the LLM may use during synthesis:
  - Terminal outcome reconstruction (Section 3)
  - Goal-substitution analysis (Section 4)
  - User-as-debugger burden (Section 5)
  - Correction-quality classification (Section 6)
  - Procedure-to-value test (Section 7)
  - Instruction-interaction analysis (Section 8)
  - Evidence-resolution analysis (Section 9–10)
  - Stop-point reconstruction (Section 11)
* Classification enums for each category.
* Lightweight schema-validators for the optional report sections.
* A helper for the layered root-cause hierarchy (Section 12).

Design contract
---------------
* **Conditional, not mandatory.** None of these sections are required.
  They appear in the report only when the evidence supports them. The
  spec explicitly warns: "Do not add a large interaction-failure taxonomy
  to every report."
* **Deterministic signals come from the detectors layer**; this module
  holds only the analytical concepts the LLM applies when reading those
  signals.
* **No factual claim about a session** is encoded here — every value
  produced by this module is either a classification enum, a schema
  validator, or a serialisation helper.

This module deliberately does NOT define the deterministic detectors
that flag candidate evidence; those live in ``detectors.py``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

__all__ = [
    # Section 3
    "TerminalOutcomeField",
    # Section 4 — finding concept
    "FindingConcept",
    # Section 5
    "UserBurdenCategory",
    # Section 6
    "CorrectionQualityClass",
    # Section 7
    "ProcedureClassification",
    # Section 8
    "InstructionStatus",
    # Section 9–10
    "EvidenceResolutionClass",
    "EvidenceCeilingAction",
    # Section 11
    "StopPointAssessment",
    # Section 12
    "RootCauseLayer",
    # Section 14
    "UserCostCategory",
    # Validators
    "validate_terminal_outcome",
    "validate_user_debugging_burden",
    "validate_correction_quality",
    "validate_procedure_to_value",
    "validate_instruction_interaction",
    "validate_evidence_resolution",
    "validate_stop_point",
    "validate_root_cause_structure",
    "validate_value_accounting_extension",
]


# ---------------------------------------------------------------------------
# Section 3 — Terminal outcome reconstruction
# ---------------------------------------------------------------------------


class TerminalOutcomeField(str, Enum):
    """Six required sub-fields when terminal_outcome is reported.

    * ``user_terminal_outcome`` — what the user was actually trying to
      accomplish (NOT the artifact produced).
    * ``success_conditions`` — what would constitute success for the user.
    * ``explicit_constraints`` — constraints the user named.
    * ``implicit_operational_need`` — constraints implied by context.
    * ``actual_outcome`` — what the session actually delivered.
    * ``degree_of_completion`` — "complete" / "partial" / "abandoned" /
      "substitute".
    """

    USER_TERMINAL_OUTCOME = "user_terminal_outcome"
    SUCCESS_CONDITIONS = "success_conditions"
    EXPLICIT_CONSTRAINTS = "explicit_constraints"
    IMPLICIT_OPERATIONAL_NEED = "implicit_operational_need"
    ACTUAL_OUTCOME = "actual_outcome"
    DEGREE_OF_COMPLETION = "degree_of_completion"


_VALID_DEGREES = frozenset({"complete", "partial", "abandoned", "substitute"})


def validate_terminal_outcome(block: dict[str, Any]) -> list[str]:
    """Validate a terminal_outcome section. Returns a list of issue strings
    (empty if valid). The block is OPTIONAL — call this only when present.
    """
    issues: list[str] = []
    if not isinstance(block, dict):
        return [f"terminal_outcome must be a dict, got {type(block).__name__}"]
    missing = [f.value for f in TerminalOutcomeField if f.value not in block]
    if missing:
        issues.append(f"terminal_outcome missing sub-fields: {missing}")
    if block.get("degree_of_completion") not in _VALID_DEGREES and "degree_of_completion" in block:
        issues.append(
            f"terminal_outcome.degree_of_completion must be one of {sorted(_VALID_DEGREES)}, got {block['degree_of_completion']!r}"
        )
    for fld in ("user_terminal_outcome", "success_conditions", "actual_outcome"):
        v = block.get(fld)
        if v is not None and (not isinstance(v, str) or not v.strip()):
            issues.append(f"terminal_outcome.{fld} must be a non-empty string")
    return issues


# ---------------------------------------------------------------------------
# Section 4 — Goal-substitution finding concept
# ---------------------------------------------------------------------------


class FindingConcept(str, Enum):
    """Analytical finding concepts (NOT new mandatory episode types).

    A finding concept is surfaced in the verdict / lessons section when
    the evidence supports it. It is an *observation* about the session,
    not a new bucket in the episode-type taxonomy.

    * ``TERMINAL_OUTCOME_DRIFT`` — substantial work stopped advancing the
      user's real success condition; an intermediate artifact / process /
      investigation became a substitute.
    * ``PROCEDURE_DISPLACED_JUDGMENT`` — a procedure (plan mode, gate,
      artifact requirement) displaced the judgment the user actually
      needed.
    * ``INSTRUCTION_COMBINATION_PATHOLOGY`` — individually reasonable
      instructions combined into pathological behaviour.
    """

    TERMINAL_OUTCOME_DRIFT = "TERMINAL_OUTCOME_DRIFT"
    PROCEDURE_DISPLACED_JUDGMENT = "PROCEDURE_DISPLACED_JUDGMENT"
    INSTRUCTION_COMBINATION_PATHOLOGY = "INSTRUCTION_COMBINATION_PATHOLOGY"


# ---------------------------------------------------------------------------
# Section 5 — User-as-debugger burden
# ---------------------------------------------------------------------------


class UserBurdenCategory(str, Enum):
    """Seven categories of user debugging burden (Section 5).

    * ``NORMAL_CLARIFICATION`` — user provided routine clarification
      that any reasonable agent would have asked for. NOT a defect.
    * ``NEW_USER_REQUIREMENT`` — user added genuinely new requirements;
      not an agent failure.
    * ``USER_PREFERENCE_UPDATE`` — user changed a preference; not an
      agent failure.
    * ``AVOIDABLE_AGENT_CORRECTION`` — user corrected an agent mistake;
      the agent should have got it right.
    * ``USER_RESTORED_GOAL`` — user had to re-state the original objective
      after the agent drifted.
    * ``USER_SUPPLIED_MISSING_REASONING`` — user performed reasoning the
      agent should have done.
    * ``USER_OVERRULED_DEFENSIVE_RESISTANCE`` — user had to push past an
      agent's defensive hold on a wrong conclusion.
    """

    NORMAL_CLARIFICATION = "NORMAL_CLARIFICATION"
    NEW_USER_REQUIREMENT = "NEW_USER_REQUIREMENT"
    USER_PREFERENCE_UPDATE = "USER_PREFERENCE_UPDATE"
    AVOIDABLE_AGENT_CORRECTION = "AVOIDABLE_AGENT_CORRECTION"
    USER_RESTORED_GOAL = "USER_RESTORED_GOAL"
    USER_SUPPLIED_MISSING_REASONING = "USER_SUPPLIED_MISSING_REASONING"
    USER_OVERRULED_DEFENSIVE_RESISTANCE = "USER_OVERRULED_DEFENSIVE_RESISTANCE"


def validate_user_debugging_burden(block: Any) -> list[str]:
    """Validate a user_debugging_burden section."""
    issues: list[str] = []
    if not isinstance(block, dict):
        return [f"user_debugging_burden must be a dict, got {type(block).__name__}"]
    items = block.get("items")
    if items is None:
        return issues  # whole block optional
    if not isinstance(items, list):
        issues.append("user_debugging_burden.items must be a list")
        return issues
    valid_cats = {c.value for c in UserBurdenCategory}
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            issues.append(f"user_debugging_burden.items[{i}] must be a dict")
            continue
        cat = it.get("category")
        if cat not in valid_cats:
            issues.append(
                f"user_debugging_burden.items[{i}].category {cat!r} not in {[c.value for c in UserBurdenCategory]}"
            )
    return issues


# ---------------------------------------------------------------------------
# Section 6 — Correction-quality classification
# ---------------------------------------------------------------------------


class CorrectionQualityClass(str, Enum):
    """Six classifications of a single correction response.

    * ``PROMPT_HEALTHY_CORRECTION`` — agent acknowledged, retracted,
      corrected downstream artefacts, residual damage = none.
    * ``DELAYED_CORRECTION`` — agent eventually corrected but only after
      delay or repeated pressure.
    * ``PARTIAL_CORRECTION`` — agent corrected the immediate claim but
      did not propagate to downstream artefacts or related claims.
    * ``DEFENSIVE_CORRECTION`` — agent defended a disproven claim before
      conceding.
    * ``COSMETIC_CORRECTION`` — agent apologised or rephrased but the
      underlying artefact still embeds the false claim.
    * ``CORRECTION_WITH_RESIDUAL_DAMAGE`` — correction happened but
      downstream artefacts (links, recommendations) remain wrong.
    """

    PROMPT_HEALTHY_CORRECTION = "PROMPT_HEALTHY_CORRECTION"
    DELAYED_CORRECTION = "DELAYED_CORRECTION"
    PARTIAL_CORRECTION = "PARTIAL_CORRECTION"
    DEFENSIVE_CORRECTION = "DEFENSIVE_CORRECTION"
    COSMETIC_CORRECTION = "COSMETIC_CORRECTION"
    CORRECTION_WITH_RESIDUAL_DAMAGE = "CORRECTION_WITH_RESIDUAL_DAMAGE"


def validate_correction_quality(block: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(block, dict):
        return [f"correction_quality must be a dict, got {type(block).__name__}"]
    items = block.get("items")
    if not isinstance(items, list):
        return issues  # whole block optional
    valid_cats = {c.value for c in CorrectionQualityClass}
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            issues.append(f"correction_quality.items[{i}] must be a dict")
            continue
        cls = it.get("classification")
        if cls not in valid_cats:
            issues.append(
                f"correction_quality.items[{i}].classification {cls!r} not in valid set"
            )
        # Required sub-fields per spec Section 6.
        for fld in (
            "correction_trigger",
            "claim_retracted",
            "downstream_artifacts_corrected",
        ):
            if fld not in it:
                issues.append(f"correction_quality.items[{i}].{fld} required")
    return issues


# ---------------------------------------------------------------------------
# Section 7 — Procedure-to-value test
# ---------------------------------------------------------------------------


class ProcedureClassification(str, Enum):
    """Six classifications for procedure-to-value test (Section 7).

    * ``PROCEDURE_ENABLED_VALUE`` — the procedure improved a decision
      and the cost was proportionate.
    * ``PROCEDURE_PROPORTIONATE`` — the procedure was useful but the
      value could have come from less.
    * ``PROCEDURE_OVERUSED`` — the procedure added work without
      proportionate benefit.
    * ``PROCEDURE_DISPLACED_JUDGMENT`` — the procedure replaced the
      judgment the user actually needed.
    * ``PROCEDURE_BECAME_DELIVERABLE`` — the procedure became the
      deliverable instead of supporting it.
    * ``PROCEDURE_NOT_NEEDED`` — the procedure was unnecessary.
    """

    PROCEDURE_ENABLED_VALUE = "PROCEDURE_ENABLED_VALUE"
    PROCEDURE_PROPORTIONATE = "PROCEDURE_PROPORTIONATE"
    PROCEDURE_OVERUSED = "PROCEDURE_OVERUSED"
    PROCEDURE_DISPLACED_JUDGMENT = "PROCEDURE_DISPLACED_JUDGMENT"
    PROCEDURE_BECAME_DELIVERABLE = "PROCEDURE_BECAME_DELIVERABLE"
    PROCEDURE_NOT_NEEDED = "PROCEDURE_NOT_NEEDED"


def validate_procedure_to_value(block: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(block, dict):
        return [f"procedure_to_value must be a dict, got {type(block).__name__}"]
    items = block.get("items")
    if not isinstance(items, list):
        return issues
    valid_cats = {c.value for c in ProcedureClassification}
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            issues.append(f"procedure_to_value.items[{i}] must be a dict")
            continue
        cls = it.get("classification")
        if cls not in valid_cats:
            issues.append(
                f"procedure_to_value.items[{i}].classification {cls!r} not in valid set"
            )
    return issues


# ---------------------------------------------------------------------------
# Section 8 — Instruction-interaction analysis
# ---------------------------------------------------------------------------


class InstructionStatus(str, Enum):
    """Eight classifications for instruction-interaction analysis (Section 8).

    * ``INSTRUCTION_ABSENT`` — no rule covers the situation.
    * ``INSTRUCTION_IGNORED`` — rule exists but agent didn't apply it.
    * ``INSTRUCTION_AMBIGUOUS`` — rule is unclear; agent guessed.
    * ``INSTRUCTION_OVERBROAD`` — rule applied too broadly.
    * ``INSTRUCTION_CONFLICT`` — two rules contradict.
    * ``INSTRUCTION_COMBINATION_PATHOLOGY`` — individually reasonable
      rules combined into pathological behaviour.
    * ``INSTRUCTION_USED_OUT_OF_SCOPE`` — rule applied where it
      doesn't apply.
    * ``INSTRUCTION_EFFECTIVE`` — rule was effective.
    """

    INSTRUCTION_ABSENT = "INSTRUCTION_ABSENT"
    INSTRUCTION_IGNORED = "INSTRUCTION_IGNORED"
    INSTRUCTION_AMBIGUOUS = "INSTRUCTION_AMBIGUOUS"
    INSTRUCTION_OVERBROAD = "INSTRUCTION_OVERBROAD"
    INSTRUCTION_CONFLICT = "INSTRUCTION_CONFLICT"
    INSTRUCTION_COMBINATION_PATHOLOGY = "INSTRUCTION_COMBINATION_PATHOLOGY"
    INSTRUCTION_USED_OUT_OF_SCOPE = "INSTRUCTION_USED_OUT_OF_SCOPE"
    INSTRUCTION_EFFECTIVE = "INSTRUCTION_EFFECTIVE"


def validate_instruction_interaction(block: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(block, dict):
        return [f"instruction_interaction must be a dict, got {type(block).__name__}"]
    items = block.get("items")
    if not isinstance(items, list):
        return issues
    valid_cats = {c.value for c in InstructionStatus}
    for i, it in enumerate(items):
        if not isinstance(it, dict):
            issues.append(f"instruction_interaction.items[{i}] must be a dict")
            continue
        cls = it.get("status")
        if cls not in valid_cats:
            issues.append(
                f"instruction_interaction.items[{i}].status {cls!r} not in valid set"
            )
    return issues


# ---------------------------------------------------------------------------
# Section 9–10 — Evidence-resolution + evidence-ceiling
# ---------------------------------------------------------------------------


class EvidenceResolutionClass(str, Enum):
    """Eight classifications for evidence-resolution analysis (Section 9).

    * ``EVIDENCE_SUFFICIENT`` — answer was supported by adequate
      evidence.
    * ``EVIDENCE_CEILING_REACHED`` — answer could not be verified with
      available tools/evidence; the ceiling was correctly reported.
    * ``SEARCH_STOPPED_TOO_EARLY`` — answer was findable but search
      ended early.
    * ``INVALID_EVIDENCE_USED`` — plausibly related material was
      treated as proof.
    * ``UNSUPPORTED_CERTAINTY`` — "verified" / "direct evidence" /
      "cannot know" used without an operationally valid basis.
    * ``UNHELPFUL_OVERHEDGING`` — epistemic caveats added without
      value.
    * ``EXCESSIVE_VERIFICATION`` — verification continued after the
      answer was sufficiently supported.
    * ``SOURCE_AUTHORITY_MISMATCH`` — relied on the wrong source as
      authority.
    """

    EVIDENCE_SUFFICIENT = "EVIDENCE_SUFFICIENT"
    EVIDENCE_CEILING_REACHED = "EVIDENCE_CEILING_REACHED"
    SEARCH_STOPPED_TOO_EARLY = "SEARCH_STOPPED_TOO_EARLY"
    INVALID_EVIDENCE_USED = "INVALID_EVIDENCE_USED"
    UNSUPPORTED_CERTAINTY = "UNSUPPORTED_CERTAINTY"
    UNHELPFUL_OVERHEDGING = "UNHELPFUL_OVERHEDGING"
    EXCESSIVE_VERIFICATION = "EXCESSIVE_VERIFICATION"
    SOURCE_AUTHORITY_MISMATCH = "SOURCE_AUTHORITY_MISMATCH"


class EvidenceCeilingAction(str, Enum):
    """Five classifications for evidence-ceiling response (Section 10).

    * ``STOP_AND_REPORT`` — agent correctly stopped and reported.
    * ``REFRAME_TO_BEST_AVAILABLE`` — agent correctly reframed.
    * ``REQUEST_MINIMAL_USER_EVIDENCE`` — agent correctly asked the
      user for the smallest evidence needed.
    * ``CONTINUE_TARGETED_RESEARCH`` — agent correctly continued
      targeted research within the ceiling.
    * ``CONTINUED_AFTER_EVIDENCE_CEILING`` — agent continued producing
      work after the ceiling; this is the failure mode.
    """

    STOP_AND_REPORT = "STOP_AND_REPORT"
    REFRAME_TO_BEST_AVAILABLE = "REFRAME_TO_BEST_AVAILABLE"
    REQUEST_MINIMAL_USER_EVIDENCE = "REQUEST_MINIMAL_USER_EVIDENCE"
    CONTINUE_TARGETED_RESEARCH = "CONTINUE_TARGETED_RESEARCH"
    CONTINUED_AFTER_EVIDENCE_CEILING = "CONTINUED_AFTER_EVIDENCE_CEILING"


def validate_evidence_resolution(block: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(block, dict):
        return [f"evidence_resolution must be a dict, got {type(block).__name__}"]
    valid = {c.value for c in EvidenceResolutionClass}
    for fld in ("classification", "question_to_resolve", "minimum_sufficient_evidence"):
        if fld not in block:
            issues.append(f"evidence_resolution.{fld} required when section is present")
    cls = block.get("classification")
    if cls not in valid:
        issues.append(f"evidence_resolution.classification {cls!r} not in valid set")
    return issues


# ---------------------------------------------------------------------------
# Section 11 — Stop-point reconstruction
# ---------------------------------------------------------------------------


@dataclass
class StopPointAssessment:
    """Bounded counterfactual: where should the agent have stopped?"""

    best_stop_point: str
    evidence_available_at_that_point: str
    what_should_have_been_said: str
    what_work_afterward_was_avoidable: str

    def to_dict(self) -> dict[str, str]:
        return {
            "best_stop_point": self.best_stop_point,
            "evidence_available_at_that_point": self.evidence_available_at_that_point,
            "what_should_have_been_said": self.what_should_have_been_said,
            "what_work_afterward_was_avoidable": self.what_work_afterward_was_avoidable,
        }


def validate_stop_point(block: Any) -> list[str]:
    issues: list[str] = []
    if not isinstance(block, dict):
        return [f"stop_point must be a dict, got {type(block).__name__}"]
    for fld in (
        "best_stop_point",
        "evidence_available_at_that_point",
        "what_should_have_been_said",
        "what_work_afterward_was_avoidable",
    ):
        v = block.get(fld)
        if not isinstance(v, str) or not v.strip():
            issues.append(f"stop_point.{fld} required and non-empty")
    return issues


# ---------------------------------------------------------------------------
# Section 12 — Layered root-cause structure
# ---------------------------------------------------------------------------


class RootCauseLayer(str, Enum):
    """Six layers for a layered causal hierarchy (Section 12).

    * ``OBSERVED_FAILURE`` — what actually happened.
    * ``IMMEDIATE_TRIGGER`` — what set the failure in motion.
    * ``PROXIMATE_CAUSE`` — what the agent directly did wrong.
    * ``CONTRIBUTING_CONDITIONS`` — what made the failure likely.
    * ``SYSTEMIC_REUSABLE_CAUSE`` — what systemic or reusable cause
      best explains the pattern across events.
    * ``COMPETING_EXPLANATION`` — alternative hypotheses; do not force
      one cause.
    """

    OBSERVED_FAILURE = "OBSERVED_FAILURE"
    IMMEDIATE_TRIGGER = "IMMEDIATE_TRIGGER"
    PROXIMATE_CAUSE = "PROXIMATE_CAUSE"
    CONTRIBUTING_CONDITIONS = "CONTRIBUTING_CONDITIONS"
    SYSTEMIC_REUSABLE_CAUSE = "SYSTEMIC_REUSABLE_CAUSE"
    COMPETING_EXPLANATION = "COMPETING_EXPLANATION"


def validate_root_cause_structure(block: Any) -> list[str]:
    """Validate a layered root-cause section."""
    issues: list[str] = []
    if not isinstance(block, dict):
        return [f"root_cause must be a dict, got {type(block).__name__}"]
    layers = block.get("layers")
    if not isinstance(layers, list):
        return ["root_cause.layers required when section is present (list)"]
    valid_layers = {l.value for l in RootCauseLayer}
    seen_layers: set[str] = set()
    for i, layer in enumerate(layers):
        if not isinstance(layer, dict):
            issues.append(f"root_cause.layers[{i}] must be a dict")
            continue
        lname = layer.get("layer")
        if lname not in valid_layers:
            issues.append(f"root_cause.layers[{i}].layer {lname!r} not in valid set")
        if lname in seen_layers:
            issues.append(f"root_cause.layers[{i}] duplicate layer {lname!r}")
        seen_layers.add(lname)
        if not layer.get("claim"):
            issues.append(f"root_cause.layers[{i}].claim required and non-empty")
    # Competing explanations are *required* per spec Section 12 ("preserve
    # competing explanations and falsifiers").
    if RootCauseLayer.COMPETING_EXPLANATION.value not in seen_layers:
        issues.append(
            "root_cause.layers must include a COMPETING_EXPLANATION layer "
            "even if the claim is 'none identified'"
        )
    return issues


# ---------------------------------------------------------------------------
# Section 14 — Extended value accounting (new cost sub-categories)
# ---------------------------------------------------------------------------


class UserCostCategory(str, Enum):
    """Seven cost sub-categories for VALUE_DESTROYED_OR_COST.

    Per the spec, these map into the existing VALUE_DESTROYED_OR_COST
    category rather than creating new top-level value categories. The AAR
    report's value_accounting entries can include a ``cost_subcategory``
    field referencing one of these values.
    """

    USER_ATTENTION_COST = "USER_ATTENTION_COST"
    USER_DEBUGGING_COST = "USER_DEBUGGING_COST"
    TRUST_COST = "TRUST_COST"
    DECISION_DELAY = "DECISION_DELAY"
    AVOIDABLE_TOOL_COST = "AVOIDABLE_TOOL_COST"
    ARTIFACT_MAINTENANCE_COST = "ARTIFACT_MAINTENANCE_COST"
    OPPORTUNITY_COST = "OPPORTUNITY_COST"


def validate_value_accounting_extension(block: Any) -> list[str]:
    """Validate value_accounting entries; ensures cost_subcategory values
    are recognised."""
    issues: list[str] = []
    valid = {c.value for c in UserCostCategory}
    # value_accounting is keyed by ValueCategory; entries are lists.
    if not isinstance(block, dict):
        return [f"value_accounting must be a dict, got {type(block).__name__}"]
    for cat_key, entries in block.items():
        if not isinstance(entries, list):
            continue
        for j, e in enumerate(entries):
            if not isinstance(e, dict):
                continue
            sub = e.get("cost_subcategory")
            if sub is not None and sub not in valid:
                issues.append(
                    f"value_accounting.{cat_key}[{j}].cost_subcategory {sub!r} not in recognised cost set"
                )
    return issues


# ---------------------------------------------------------------------------
# Cheap heuristic helpers (used by deterministic detectors)
# ---------------------------------------------------------------------------

#: Phrases indicating the agent has reached an evidence ceiling or a
#: blocking unknown.
_EVIDENCE_CEILING_PHRASES = (
    r"\bcannot verify\b",
    r"\bcannot confirm\b",
    r"\bunable to verify\b",
    r"\bno (?:way to )?(?:confirm|verify)\b",
    r"\bevidence (?:is )?incomplete\b",
    r"\binsufficient evidence\b",
    r"\bneed (?:more|additional) (?:information|evidence)\b",
    r"\bblocked (?:on|by)\b",
    r"\bevidence (?:does not|won't|will not) (?:support|show|confirm)\b",
)

EVIDENCE_CEILING_RE = re.compile("|".join(_EVIDENCE_CEILING_PHRASES), re.IGNORECASE)

#: Phrases the user uses to push past an evidence ceiling.
_USER_PUSHBACK_PHRASES = (
    r"\bno,?\s+(?:i|we)\s+(?:said|meant|want|asked)\b",
    r"\bthat's not what\b",
    r"\bthe (?:evidence|source) (?:does not|doesn't|won't) say\b",
    r"\bplease just\b",
    r"\bstop (?:saying|doing|suggesting)\b",
    r"\bi (?:already|just) (?:said|asked|told|showed)\b",
    r"\byou're (?:wrong|defending|making)\b",
    r"\bwhy (?:do you|are you) (?:keep|insist)\b",
)

USER_PUSHBACK_RE = re.compile("|".join(_USER_PUSHBACK_PHRASES), re.IGNORECASE)

#: Phrases the agent uses to cite rules / modes / procedures.
_PROCEDURE_CITATION_PHRASES = (
    r"\b(?:per|according to) (?:AGENTS\.md|CLAUDE\.md|the (?:skill|rules?)|spec)\b",
    r"\bplan mode\b",
    r"\b(?:/go|/aar|/check|/review|/red-team)\b",
    r"\bthe (?:spec|skill|rule|gate) (?:requires?|says?|calls? for)\b",
    r"\bdisposition\b",
    r"\bmandatory (?:section|field)\b",
)

PROCEDURE_CITATION_RE = re.compile("|".join(_PROCEDURE_CITATION_PHRASES), re.IGNORECASE)


def has_evidence_ceiling_phrase(text: str) -> bool:
    """True if ``text`` contains a phrase acknowledging a blocking unknown."""
    return bool(text) and bool(EVIDENCE_CEILING_RE.search(text))


def has_user_pushback_phrase(text: str) -> bool:
    return bool(text) and bool(USER_PUSHBACK_RE.search(text))


def procedure_citation_count(text: str) -> int:
    """Count distinct procedure-citation phrases in ``text``."""
    if not text:
        return 0
    return sum(1 for _ in PROCEDURE_CITATION_RE.finditer(text))