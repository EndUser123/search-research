"""Phase 3 tests for the aggregation layer.

Verifies:
- aggregates contain all required fields (event_count, episode_count,
  severity, examples, first/last, impact, raw refs, falsifier)
- severity is NOT event count alone — depends on consequence + persistence
- raw signals preserved for traceability
- aggregation reduces synthesis-facing signal count materially
"""
from __future__ import annotations

import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "__lib"))

import pytest

from detectors import Signal, SignalKind, SignalSeverity
from aggregators import (
    AggregateSignal,
    aggregate_recommendation_revisions,
    aggregate_post_failure_continuation,
    aggregate_assistant_self_corrections,
    all_aggregates,
    _estimate_episode_count,
)


def _mk_signal(detector: str, kind: SignalKind, idx: int, detail: str = "x") -> Signal:
    return Signal(
        detector=detector,
        kind=kind,
        event_indices=(idx,),
        detail=detail,
        severity=SignalSeverity.LOW,
        falsifier="test",
    )


# ---------------------------------------------------------------------------
# Required-field contract
# ---------------------------------------------------------------------------


def test_aggregate_has_all_required_fields():
    """Per spec: each aggregate must contain event count, episode count,
    severity derivation, representative examples, first and last occurrence,
    impact on terminal outcome, raw event references, falsifier."""
    raw = [
        _mk_signal("detect_recommendation_revisions", SignalKind.OPPORTUNITY_CANDIDATE_RECOMMENDATION_REVISION, i)
        for i in range(5, 35)  # 30 revisions
    ]
    agg = aggregate_recommendation_revisions(
        raw, all_events_count=200, has_user_correction_after=True,
    )
    assert agg is not None
    assert agg.event_count == 30
    assert agg.episode_count_estimate >= 1
    assert isinstance(agg.severity, SignalSeverity)
    assert len(agg.representative_examples) <= 3
    assert all(isinstance(e, str) for e in agg.representative_examples)
    assert agg.first_event_index == 5
    assert agg.last_event_index == 34
    assert isinstance(agg.impact_on_terminal_outcome, str)
    assert len(agg.impact_on_terminal_outcome) > 0
    assert len(agg.raw_event_indices) == 30
    assert isinstance(agg.falsifier, str)


# ---------------------------------------------------------------------------
# Severity derivation rule (NOT count alone)
# ---------------------------------------------------------------------------


def test_severity_not_count_alone_high_count_low_span_stays_medium():
    """Many revisions in a short span = MEDIUM, not HIGH (no persistence)."""
    # 15 revisions all in events 0-5 (span = 5, below threshold of 30)
    raw = [
        _mk_signal("detect_recommendation_revisions", SignalKind.OPPORTUNITY_CANDIDATE_RECOMMENDATION_REVISION, i)
        for i in range(15)
    ]
    agg = aggregate_recommendation_revisions(
        raw, all_events_count=100, has_user_correction_after=True,
    )
    assert agg is not None
    # Count meets high threshold (10) but span doesn't (5 < 30)
    assert agg.severity is SignalSeverity.MEDIUM


def test_severity_high_requires_count_span_and_user_correction():
    """HIGH requires count AND span AND user correction after."""
    # 15 revisions across events 0-50 (span 50, count 15)
    raw = [
        _mk_signal("detect_recommendation_revisions", SignalKind.OPPORTUNITY_CANDIDATE_RECOMMENDATION_REVISION, i * 4)
        for i in range(15)  # events 0, 4, 8, ..., 56
    ]
    # WITH user correction
    agg_with = aggregate_recommendation_revisions(
        raw, all_events_count=200, has_user_correction_after=True,
    )
    assert agg_with is not None
    assert agg_with.severity is SignalSeverity.HIGH

    # WITHOUT user correction
    agg_without = aggregate_recommendation_revisions(
        raw, all_events_count=200, has_user_correction_after=False,
    )
    assert agg_without is not None
    # Should be MEDIUM because the third condition (user_correction) is missing
    assert agg_without.severity is SignalSeverity.MEDIUM


def test_severity_low_for_small_burst():
    """A small burst of revisions in a short span is LOW."""
    raw = [
        _mk_signal("detect_recommendation_revisions", SignalKind.OPPORTUNITY_CANDIDATE_RECOMMENDATION_REVISION, i)
        for i in range(3)  # 3 revisions, span 2
    ]
    agg = aggregate_recommendation_revisions(
        raw, all_events_count=100, has_user_correction_after=False,
    )
    assert agg is not None
    assert agg.severity is SignalSeverity.LOW


# ---------------------------------------------------------------------------
# Post-failure continuation aggregation
# ---------------------------------------------------------------------------


def test_post_failure_continuation_aggregate():
    """detect_post_failure_continuation aggregates correctly."""
    raw = [
        _mk_signal("detect_post_failure_continuation", SignalKind.OPPORTUNITY_CANDIDATE_POST_FAILURE_CONTINUATION, i * 3)
        for i in range(10)  # events 0, 3, ..., 27 (span 27)
    ]
    agg = aggregate_post_failure_continuation(
        raw, all_events_count=200, has_user_correction_after=True,
    )
    assert agg is not None
    assert agg.event_count == 10
    assert agg.first_event_index == 0
    assert agg.last_event_index == 27


# ---------------------------------------------------------------------------
# Assistant self-correction aggregation (Phase 4 candidate)
# ---------------------------------------------------------------------------


def test_assistant_self_corrections_aggregate():
    raw = [
        _mk_signal("detect_assistant_self_corrections", SignalKind.ASSISTANT_SELF_CORRECTION, i * 2)
        for i in range(40)  # span 78
    ]
    agg = aggregate_assistant_self_corrections(
        raw, all_events_count=200, has_user_correction_after=True,
    )
    assert agg is not None
    assert agg.event_count == 40
    # 40 ≥ 20 threshold; span 78 ≥ 50 threshold; with user correction → HIGH
    assert agg.severity is SignalSeverity.HIGH


# ---------------------------------------------------------------------------
# Episode-count heuristic
# ---------------------------------------------------------------------------


def test_episode_count_clusters_by_gap():
    """Signals separated by ≥window events count as separate episodes."""
    indices = (0, 1, 2, 10, 11, 20, 21, 22)  # 3 clusters if window=5
    episodes = _estimate_episode_count(indices, window=5)
    assert episodes == 3


def test_episode_count_single_burst():
    indices = (5, 6, 7, 8)  # all adjacent → 1 episode
    assert _estimate_episode_count(indices, window=3) == 1


# ---------------------------------------------------------------------------
# Raw-signal preservation
# ---------------------------------------------------------------------------


def test_aggregate_preserves_raw_event_indices():
    """The aggregate carries every raw event index for traceability."""
    raw = [
        _mk_signal("detect_post_failure_continuation", SignalKind.OPPORTUNITY_CANDIDATE_POST_FAILURE_CONTINUATION, idx)
        for idx in [3, 7, 12, 19, 25]
    ]
    agg = aggregate_post_failure_continuation(
        raw, all_events_count=100, has_user_correction_after=False,
    )
    assert agg is not None
    assert set(agg.raw_event_indices) == {3, 7, 12, 19, 25}


# ---------------------------------------------------------------------------
# all_aggregates composition
# ---------------------------------------------------------------------------


def test_all_aggregates_returns_only_non_none():
    """all_aggregates returns only families that actually fired."""
    raw = [
        _mk_signal("detect_recommendation_revisions", SignalKind.OPPORTUNITY_CANDIDATE_RECOMMENDATION_REVISION, 1),
        _mk_signal("detect_recommendation_revisions", SignalKind.OPPORTUNITY_CANDIDATE_RECOMMENDATION_REVISION, 2),
    ]
    aggs = all_aggregates(raw, all_events_count=50, has_user_correction_after=False)
    # Only recommendation_revisions fired (no post_failure, no self_corrections)
    assert len(aggs) == 1
    assert aggs[0].detector == "detect_recommendation_revisions"


def test_all_aggregates_handles_empty_input():
    aggs = all_aggregates([], all_events_count=0, has_user_correction_after=False)
    assert aggs == []


# ---------------------------------------------------------------------------
# Synthesis-facing signal-count reduction (the point of Phase 3)
# ---------------------------------------------------------------------------


def test_aggregate_reduces_synthesis_facing_count():
    """Many raw signals → 1 aggregate. The reduction ratio is the value."""
    raw = [
        _mk_signal("detect_recommendation_revisions", SignalKind.OPPORTUNITY_CANDIDATE_RECOMMENDATION_REVISION, i)
        for i in range(50)
    ]
    agg = aggregate_recommendation_revisions(
        raw, all_events_count=500, has_user_correction_after=True,
    )
    assert agg is not None
    # 50 raw signals → 1 aggregate
    assert agg.event_count == 50
    # The synthesis-facing count is 1 (the aggregate) not 50
