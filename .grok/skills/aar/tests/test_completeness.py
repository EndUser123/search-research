"""Tests for the completeness classifier.

Evidence class: production unit (pure function over CompletenessInputs).

Covers spec Section 8 acceptance criteria:
* file existence alone does not produce SOURCE_COMPLETE;
* complete active history through cutoff produces SOURCE_COMPLETE;
* complete history with truncated tool output → SOURCE_COMPLETE_WITH_LIMITATIONS;
* compaction-only input → SOURCE_PARTIAL;
* heuristic session binding → SOURCE_UNVERIFIED.
"""

from __future__ import annotations

import pytest

from completeness import (
    COMPLETENESS_HIERARCHY,
    CompletenessClassification,
    CompletenessInputs,
    CompletenessStatus,
    can_downgrade_to,
    classify_completeness,
)


def _base_complete_inputs() -> CompletenessInputs:
    """Inputs that would yield SOURCE_COMPLETE."""
    return CompletenessInputs(
        identity_verified=True,
        chat_history_present=True,
        chat_history_fully_parsed=True,
        chat_history_start_boundary=True,
        expected_message_count=100,
        reconstructed_message_count=100,
        expected_turn_count=10,
        reconstructed_turn_count=10,
        branch_state_resolved=True,
        unexplained_sequence_gaps=0,
        known_missing_evidence=(),
        truncated_tool_outputs=0,
        unsupported_schema=False,
        unsupported_format=False,
    )


# ---------------------------------------------------------------------------
# SOURCE_COMPLETE
# ---------------------------------------------------------------------------


def test_complete_inputs_yield_source_complete():
    r = classify_completeness(_base_complete_inputs(), snapshot_cutoff="2026-07-18T00:00:00Z")
    assert r.status is CompletenessStatus.COMPLETE
    assert r.coverage_through == "2026-07-18T00:00:00Z"
    assert r.limitations == ()


def test_file_existence_alone_is_not_complete():
    """Having chat_history is necessary but not sufficient."""
    inputs = CompletenessInputs(
        identity_verified=False,  # not verified → cannot be complete
        chat_history_present=True,
        chat_history_fully_parsed=True,
        chat_history_start_boundary=True,
        expected_message_count=None,
        reconstructed_message_count=100,
        expected_turn_count=None,
        reconstructed_turn_count=10,
        branch_state_resolved=True,
        unexplained_sequence_gaps=0,
        known_missing_evidence=(),
        truncated_tool_outputs=0,
        unsupported_schema=False,
        unsupported_format=False,
    )
    r = classify_completeness(inputs)
    assert r.status is CompletenessStatus.UNVERIFIED


# ---------------------------------------------------------------------------
# SOURCE_COMPLETE_WITH_LIMITATIONS
# ---------------------------------------------------------------------------


def test_truncated_tool_outputs_yields_with_limitations():
    inputs = _base_complete_inputs().replace_truncated(5)
    r = classify_completeness(inputs)
    assert r.status is CompletenessStatus.COMPLETE_WITH_LIMITATIONS
    assert any("truncated" in lim for lim in r.limitations)


def test_missing_summary_counts_yields_with_limitations():
    """If summary.json supplied no expected counts, we cannot self-check."""
    inputs = CompletenessInputs(
        identity_verified=True,
        chat_history_present=True,
        chat_history_fully_parsed=True,
        chat_history_start_boundary=True,
        expected_message_count=None,  # not provided
        reconstructed_message_count=100,
        expected_turn_count=None,
        reconstructed_turn_count=10,
        branch_state_resolved=True,
        unexplained_sequence_gaps=0,
        known_missing_evidence=(),
        truncated_tool_outputs=0,
        unsupported_schema=False,
        unsupported_format=False,
    )
    r = classify_completeness(inputs)
    assert r.status is CompletenessStatus.COMPLETE_WITH_LIMITATIONS


def test_sequence_gap_yields_with_limitations():
    inputs = _base_complete_inputs().replace_gaps(2)
    r = classify_completeness(inputs)
    assert r.status is CompletenessStatus.COMPLETE_WITH_LIMITATIONS


# ---------------------------------------------------------------------------
# SOURCE_PARTIAL
# ---------------------------------------------------------------------------


def test_count_mismatch_yields_partial():
    inputs = _base_complete_inputs()
    inputs = CompletenessInputs(
        **{**inputs.__dict__, "reconstructed_message_count": 50}  # 100 expected
    )
    r = classify_completeness(inputs)
    assert r.status is CompletenessStatus.PARTIAL
    assert any("message count mismatch" in r_ for r_ in r.reasons)


def test_missing_start_boundary_yields_partial():
    inputs = _base_complete_inputs()
    inputs = CompletenessInputs(
        **{**inputs.__dict__, "chat_history_start_boundary": False}
    )
    r = classify_completeness(inputs)
    assert r.status is CompletenessStatus.PARTIAL


def test_unresolved_branch_yields_partial():
    inputs = _base_complete_inputs()
    inputs = CompletenessInputs(
        **{**inputs.__dict__, "branch_state_resolved": False}
    )
    r = classify_completeness(inputs)
    assert r.status is CompletenessStatus.PARTIAL


def test_compaction_only_input_is_partial():
    """If chat_history was reconstructed from compaction only (no primary),
    the inputs would show it as effectively missing — but even if it parsed,
    unresolved branch + missing start covers this case."""
    inputs = CompletenessInputs(
        identity_verified=True,
        chat_history_present=True,
        chat_history_fully_parsed=True,
        chat_history_start_boundary=False,  # compaction has no real start
        expected_message_count=None,
        reconstructed_message_count=10,
        expected_turn_count=None,
        reconstructed_turn_count=1,
        branch_state_resolved=False,
        unexplained_sequence_gaps=0,
        known_missing_evidence=("chat_history.jsonl is a compaction reconstruction",),
        truncated_tool_outputs=0,
        unsupported_schema=False,
        unsupported_format=False,
    )
    r = classify_completeness(inputs)
    assert r.status is CompletenessStatus.PARTIAL


# ---------------------------------------------------------------------------
# SOURCE_UNVERIFIED
# ---------------------------------------------------------------------------


def test_heuristic_binding_unverified():
    """Identity not verified → UNVERIFIED regardless of other inputs."""
    inputs = _base_complete_inputs()
    inputs = CompletenessInputs(**{**inputs.__dict__, "identity_verified": False})
    r = classify_completeness(inputs)
    assert r.status is CompletenessStatus.UNVERIFIED


def test_malformed_primary_yields_unverified():
    inputs = _base_complete_inputs()
    inputs = CompletenessInputs(
        **{**inputs.__dict__, "chat_history_fully_parsed": False}
    )
    r = classify_completeness(inputs)
    assert r.status is CompletenessStatus.UNVERIFIED


# ---------------------------------------------------------------------------
# SOURCE_UNSUPPORTED
# ---------------------------------------------------------------------------


def test_unsupported_format_is_unsupported():
    inputs = _base_complete_inputs()
    inputs = CompletenessInputs(
        **{**inputs.__dict__, "unsupported_format": True}
    )
    r = classify_completeness(inputs)
    assert r.status is CompletenessStatus.UNSUPPORTED


def test_unsupported_schema_is_unsupported():
    inputs = _base_complete_inputs()
    inputs = CompletenessInputs(
        **{**inputs.__dict__, "unsupported_schema": True}
    )
    r = classify_completeness(inputs)
    assert r.status is CompletenessStatus.UNSUPPORTED


# ---------------------------------------------------------------------------
# Hierarchy helper (used by the output validator)
# ---------------------------------------------------------------------------


def test_hierarchy_ranks_complete_highest():
    assert COMPLETENESS_HIERARCHY[CompletenessStatus.COMPLETE] == 5
    assert COMPLETENESS_HIERARCHY[CompletenessStatus.UNSUPPORTED] == 1


def test_can_downgrade_to():
    # The validator allows the LLM to claim a stricter status than manifest.
    assert can_downgrade_to(CompletenessStatus.COMPLETE, CompletenessStatus.PARTIAL) is True
    # But not a more permissive one.
    assert can_downgrade_to(CompletenessStatus.PARTIAL, CompletenessStatus.COMPLETE) is False


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_classify_is_deterministic():
    inputs = _base_complete_inputs()
    a = classify_completeness(inputs)
    b = classify_completeness(inputs)
    assert a.status == b.status
    assert a.reasons == b.reasons
    assert a.limitations == b.limitations


# ---------------------------------------------------------------------------
# Test-only helpers attached to CompletenessInputs (kept here, not in module)
# ---------------------------------------------------------------------------


def _replace_truncated(self, n: int) -> CompletenessInputs:
    """Return a copy with truncated_tool_outputs replaced."""
    from dataclasses import replace
    return replace(self, truncated_tool_outputs=n)


def _replace_gaps(self, n: int) -> CompletenessInputs:
    from dataclasses import replace
    return replace(self, unexplained_sequence_gaps=n)


CompletenessInputs.replace_truncated = _replace_truncated  # type: ignore[attr-defined]
CompletenessInputs.replace_gaps = _replace_gaps  # type: ignore[attr-defined]
