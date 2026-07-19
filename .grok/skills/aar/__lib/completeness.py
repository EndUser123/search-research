"""Honest source-completeness model.

Per spec Section 8: "Do not declare ``SOURCE_COMPLETE`` merely because
``chat_history.jsonl`` exists."

Five statuses, each with explicit entry criteria. The function
:func:`classify_completeness` consumes a ``ReconciliationReport`` (from
``reconciler.py``) and returns the highest status the evidence supports —
never higher. This is the contract the spec calls "earned through
reconciliation".

Status hierarchy (most → least complete):

    SOURCE_COMPLETE
    SOURCE_COMPLETE_WITH_LIMITATIONS
    SOURCE_PARTIAL
    SOURCE_UNVERIFIED
    SOURCE_UNSUPPORTED

The classifier is pure: same ``ReconciliationReport`` in → same status out.
It performs no I/O. All inputs come from the reconciler's mechanical
accounting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

__all__ = [
    "CompletenessStatus",
    "CompletenessClassification",
    "CompletenessInputs",
    "classify_completeness",
    "COMPLETENESS_HIERARCHY",
]


class CompletenessStatus(str, Enum):
    """The five earned-through-reconciliation statuses.

    Values are the literal strings used in the evidence packet and the AAR
    report's ``evidence_scope`` block. The :func:`classify_completeness`
    function never returns a value not in this enum.
    """

    COMPLETE = "SOURCE_COMPLETE"
    COMPLETE_WITH_LIMITATIONS = "SOURCE_COMPLETE_WITH_LIMITATIONS"
    PARTIAL = "SOURCE_PARTIAL"
    UNVERIFIED = "SOURCE_UNVERIFIED"
    UNSUPPORTED = "SOURCE_UNSUPPORTED"


#: Rank order for "highest status the evidence supports" comparisons.
#: Lower number = more complete. Used by tests and by the validator when
#: checking that the LLM does not upgrade completeness beyond the manifest.
COMPLETENESS_HIERARCHY: dict[CompletenessStatus, int] = {
    CompletenessStatus.COMPLETE: 5,
    CompletenessStatus.COMPLETE_WITH_LIMITATIONS: 4,
    CompletenessStatus.PARTIAL: 3,
    CompletenessStatus.UNVERIFIED: 2,
    CompletenessStatus.UNSUPPORTED: 1,
}


@dataclass(frozen=True)
class CompletenessInputs:
    """Mechanical inputs the classifier needs.

    Every field must be supplied by the reconciler's accounting — never
    inferred, never defaulted to a "good-looking" value. ``not_applicable``
    fields are explicit ``None`` so the classifier can distinguish "metadata
    said 100, we reconstructed 100" from "metadata didn't say".

    See :func:`from_reconciliation_report` in ``reconciler.py`` for how a
    ``ReconciliationReport`` is converted into these inputs.
    """

    identity_verified: bool
    chat_history_present: bool
    chat_history_fully_parsed: bool  #: no malformed records beyond a small ratio
    chat_history_start_boundary: bool  #: begins with system or real user message
    expected_message_count: int | None  #: from summary.json; None if absent
    reconstructed_message_count: int  #: actual events parsed
    expected_turn_count: int | None  #: from summary.json or events.jsonl
    reconstructed_turn_count: int  #: actual turns observed
    branch_state_resolved: bool  #: no SUPERSEDED_HISTORY of unknown extent
    unexplained_sequence_gaps: int  #: gaps in prompt_index sequence
    known_missing_evidence: tuple[str, ...]  #: e.g. ('events.jsonl absent',)
    truncated_tool_outputs: int  #: tool_result records truncated/empty
    unsupported_schema: bool  #: chat_format_version we cannot parse
    unsupported_format: bool  #: source files not parseable at all


@dataclass(frozen=True)
class CompletenessClassification:
    """The classifier's verdict + the reasons that produced it."""

    status: CompletenessStatus
    reasons: tuple[str, ...]
    coverage_through: str | None  #: snapshot cutoff ISO timestamp
    known_missing_evidence: tuple[str, ...]
    limitations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "reasons": list(self.reasons),
            "coverage_through": self.coverage_through,
            "known_missing_evidence": list(self.known_missing_evidence),
            "limitations": list(self.limitations),
        }


def classify_completeness(
    inputs: CompletenessInputs,
    *,
    snapshot_cutoff: str | None = None,
    material_gap_threshold: int = 0,
) -> CompletenessClassification:
    """Return the highest completeness status the inputs support.

    The classifier walks the criteria from least to most demanding. The first
    status whose blocking criteria are met is returned; later (more complete)
    statuses are only considered if all earlier blockers are absent.

    Parameters
    ----------
    inputs
        Mechanical accounting from the reconciler.
    snapshot_cutoff
        ISO timestamp; copied into ``coverage_through`` on the result.
    material_gap_threshold
        Maximum number of unexplained sequence gaps tolerable for COMPLETE.
        Default 0 (any unexplained gap downgrades to WITH_LIMITATIONS).
    """
    reasons: list[str] = []
    limitations: list[str] = []
    missing = list(inputs.known_missing_evidence)

    # --- SOURCE_UNSUPPORTED: cannot parse the format at all ---
    if inputs.unsupported_format or inputs.unsupported_schema:
        reasons.append("source format/schema cannot be parsed safely")
        return CompletenessClassification(
            status=CompletenessStatus.UNSUPPORTED,
            reasons=tuple(reasons),
            coverage_through=snapshot_cutoff,
            known_missing_evidence=tuple(missing),
            limitations=("cannot produce canonical event stream",),
        )

    # --- SOURCE_UNVERIFIED: identity or counts cannot be reconciled ---
    if not inputs.identity_verified:
        reasons.append("session identity not verified (binding unverified)")
        return CompletenessClassification(
            status=CompletenessStatus.UNVERIFIED,
            reasons=tuple(reasons),
            coverage_through=snapshot_cutoff,
            known_missing_evidence=tuple(missing),
            limitations=("identity binding could not be cross-validated",),
        )
    if not inputs.chat_history_present:
        reasons.append("chat_history.jsonl absent — primary source missing")
        missing.append("chat_history.jsonl")
        return CompletenessClassification(
            status=CompletenessStatus.UNVERIFIED,
            reasons=tuple(reasons),
            coverage_through=snapshot_cutoff,
            known_missing_evidence=tuple(missing),
            limitations=("no primary conversation record",),
        )
    if not inputs.chat_history_fully_parsed:
        reasons.append("chat_history.jsonl has materially many malformed records")
        return CompletenessClassification(
            status=CompletenessStatus.UNVERIFIED,
            reasons=tuple(reasons),
            coverage_through=snapshot_cutoff,
            known_missing_evidence=tuple(missing),
            limitations=("primary source failed to parse cleanly",),
        )

    # --- Material count reconciliation ---
    # If summary.json supplied expected counts, they must match (or be
    # explained). If counts were never supplied, we cannot claim exhaustive
    # completeness — that becomes a limitation, not a blocker.
    count_mismatch = False
    if inputs.expected_message_count is not None:
        if inputs.expected_message_count != inputs.reconstructed_message_count:
            count_mismatch = True
            reasons.append(
                f"message count mismatch: summary={inputs.expected_message_count} "
                f"reconstructed={inputs.reconstructed_message_count}"
            )
    if inputs.expected_turn_count is not None:
        if inputs.expected_turn_count != inputs.reconstructed_turn_count:
            count_mismatch = True
            reasons.append(
                f"turn count mismatch: summary={inputs.expected_turn_count} "
                f"reconstructed={inputs.reconstructed_turn_count}"
            )

    # --- SOURCE_PARTIAL: material raw records missing or branch unresolvable ---
    if not inputs.chat_history_start_boundary:
        reasons.append("session start boundary absent (no system/first-user record)")
        return CompletenessClassification(
            status=CompletenessStatus.PARTIAL,
            reasons=tuple(reasons),
            coverage_through=snapshot_cutoff,
            known_missing_evidence=tuple(missing),
            limitations=("session start cannot be established",),
        )
    if not inputs.branch_state_resolved:
        reasons.append("branch/rewind state cannot be resolved (active vs superseded unclear)")
        return CompletenessClassification(
            status=CompletenessStatus.PARTIAL,
            reasons=tuple(reasons),
            coverage_through=snapshot_cutoff,
            known_missing_evidence=tuple(missing),
            limitations=("active vs superseded history cannot be separated",),
        )
    if count_mismatch:
        # A material mismatch is PARTIAL, not just a limitation.
        return CompletenessClassification(
            status=CompletenessStatus.PARTIAL,
            reasons=tuple(reasons),
            coverage_through=snapshot_cutoff,
            known_missing_evidence=tuple(missing),
            limitations=("expected counts from metadata do not reconcile",),
        )

    # --- WITH_LIMITATIONS: complete active history, but with caveats ---
    if inputs.unexplained_sequence_gaps > material_gap_threshold:
        limitations.append(
            f"{inputs.unexplained_sequence_gaps} unexplained sequence gap(s) in prompt_index"
        )
    if inputs.truncated_tool_outputs > 0:
        limitations.append(
            f"{inputs.truncated_tool_outputs} tool_result record(s) truncated/empty"
        )
    if inputs.expected_message_count is None:
        limitations.append(
            "summary.json did not provide expected message count — "
            "completeness self-check could not be performed"
        )

    if limitations:
        return CompletenessClassification(
            status=CompletenessStatus.COMPLETE_WITH_LIMITATIONS,
            reasons=tuple(reasons),
            coverage_through=snapshot_cutoff,
            known_missing_evidence=tuple(missing),
            limitations=tuple(limitations),
        )

    # --- SOURCE_COMPLETE: all criteria satisfied ---
    return CompletenessClassification(
        status=CompletenessStatus.COMPLETE,
        reasons=tuple(reasons),
        coverage_through=snapshot_cutoff,
        known_missing_evidence=tuple(missing),
        limitations=(),
    )


def can_downgrade_to(current: CompletenessStatus, target: CompletenessStatus) -> bool:
    """Helper for the validator: is ``target`` a stricter (lower) status?

    Used to enforce "the LLM may not upgrade completeness beyond the
    manifest". ``can_downgrade_to(manifest, llm_claim)`` must be True; if
    False the LLM is overclaiming.
    """
    return COMPLETENESS_HIERARCHY[target] <= COMPLETENESS_HIERARCHY[current]
