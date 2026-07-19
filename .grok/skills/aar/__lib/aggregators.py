"""Aggregation layer for noisy event-level detector families (Phase 3).

Per spec: "Keep raw detector events for traceability, but emit
synthesis-facing session aggregates for:
- recommendation revisions
- post-failure continuation"

Each aggregate contains:
- event count
- episode count (estimated — number of distinct clusters)
- severity derivation (NOT event count alone)
- representative examples (≤3)
- first and last occurrence
- impact on terminal outcome
- raw event references
- falsifier

Severity must depend on consequence, persistence, and outcome impact —
NOT on event count alone.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from detectors import Signal, SignalSeverity, SignalKind


@dataclass(frozen=True)
class AggregateSignal:
    """Synthesis-facing aggregate for one detector family in one session."""

    detector: str                # the underlying detector name
    kind: SignalKind             # underlying signal kind
    severity: SignalSeverity     # DERIVED severity (not raw count)
    event_count: int             # total raw signals in this family
    episode_count_estimate: int  # distinct clusters (heuristic)
    first_event_index: int       # first occurrence
    last_event_index: int        # last occurrence
    representative_examples: tuple[str, ...]  # ≤3 detail strings from raw signals
    raw_event_indices: tuple[int, ...]        # every raw event index
    impact_on_terminal_outcome: str           # narrative assessment
    falsifier: str


def _derive_severity(
    raw_signals: list[Signal],
    *,
    high_count_threshold: int,
    high_span_threshold: int,
    has_user_correction_after: bool,
) -> SignalSeverity:
    """Derive aggregate severity from consequence + persistence, not count alone.

    High severity requires:
    - raw count >= high_count_threshold (persistence), AND
    - span (last_index - first_index) >= high_span_threshold (persistence over time), AND
    - (heuristic) evidence the churn affected a user-facing decision
      (has_user_correction_after=True is a proxy for this)

    MEDIUM: count >= high_count_threshold / 2 OR span >= high_span_threshold / 2
    LOW: otherwise
    """
    if not raw_signals:
        return SignalSeverity.INFO
    count = len(raw_signals)
    first = min(s.event_indices[0] for s in raw_signals if s.event_indices)
    last = max(s.event_indices[-1] for s in raw_signals if s.event_indices)
    span = last - first
    count_meets = count >= high_count_threshold
    span_meets = span >= high_span_threshold
    count_half = count >= max(1, high_count_threshold // 2)
    span_half = span >= max(1, high_span_threshold // 2)

    if count_meets and span_meets and has_user_correction_after:
        return SignalSeverity.HIGH
    if count_half or span_half:
        return SignalSeverity.MEDIUM
    return SignalSeverity.LOW


def aggregate_recommendation_revisions(
    signals: Iterable[Signal],
    *,
    all_events_count: int,
    has_user_correction_after: bool,
) -> AggregateSignal | None:
    """Aggregate detect_recommendation_revisions signals into one session signal.

    High threshold: ≥10 revisions AND span ≥30 events (persistence).
    """
    raw = [s for s in signals if s.detector == "detect_recommendation_revisions"]
    if not raw:
        return None
    severity = _derive_severity(
        raw,
        high_count_threshold=10,
        high_span_threshold=30,
        has_user_correction_after=has_user_correction_after,
    )
    event_indices = tuple(sorted({i for s in raw for i in s.event_indices}))
    examples = tuple(s.detail[:120] for s in raw[:3])
    first = event_indices[0] if event_indices else 0
    last = event_indices[-1] if event_indices else 0
    # Episode estimate: cluster by 5-event windows
    episode_count = _estimate_episode_count(event_indices, window=5)

    # Impact narrative — derived from severity + ratio
    ratio = len(raw) / max(1, all_events_count)
    if severity is SignalSeverity.HIGH:
        impact = (
            f"{len(raw)} recommendation revisions across {last - first} events "
            f"({ratio:.1%} of session) — high churn likely displaced direct evidence work"
        )
    elif severity is SignalSeverity.MEDIUM:
        impact = (
            f"{len(raw)} revisions across {last - first} events — moderate churn; "
            f"may indicate the agent re-deciding without new evidence"
        )
    else:
        impact = (
            f"{len(raw)} revisions in a short span — normal iteration"
        )

    return AggregateSignal(
        detector="detect_recommendation_revisions",
        kind=SignalKind.OPPORTUNITY_CANDIDATE_RECOMMENDATION_REVISION,
        severity=severity,
        event_count=len(raw),
        episode_count_estimate=episode_count,
        first_event_index=first,
        last_event_index=last,
        representative_examples=examples,
        raw_event_indices=event_indices,
        impact_on_terminal_outcome=impact,
        falsifier=(
            "revision count may reflect healthy updating on genuinely new "
            "evidence rather than churn; check whether new user input or "
            "tool output arrived between revisions"
        ),
    )


def aggregate_post_failure_continuation(
    signals: Iterable[Signal],
    *,
    all_events_count: int,
    has_user_correction_after: bool,
) -> AggregateSignal | None:
    """Aggregate detect_post_failure_continuation signals into one session signal.

    High threshold: ≥5 continuations AND span ≥20 events (persistence).
    """
    raw = [s for s in signals if s.detector == "detect_post_failure_continuation"]
    if not raw:
        return None
    severity = _derive_severity(
        raw,
        high_count_threshold=5,
        high_span_threshold=20,
        has_user_correction_after=has_user_correction_after,
    )
    event_indices = tuple(sorted({i for s in raw for i in s.event_indices}))
    examples = tuple(s.detail[:120] for s in raw[:3])
    first = event_indices[0] if event_indices else 0
    last = event_indices[-1] if event_indices else 0
    episode_count = _estimate_episode_count(event_indices, window=3)

    ratio = len(raw) / max(1, all_events_count)
    if severity is SignalSeverity.HIGH:
        impact = (
            f"{len(raw)} post-failure continuations across {last - first} events "
            f"({ratio:.1%} of session) — suggests the agent kept producing work "
            f"after errors without resolving root cause"
        )
    elif severity is SignalSeverity.MEDIUM:
        impact = (
            f"{len(raw)} post-failure continuations — moderate; some failures "
            f"may be expected retry-and-recover patterns"
        )
    else:
        impact = (
            f"{len(raw)} continuations in a short span — normal error recovery"
        )

    return AggregateSignal(
        detector="detect_post_failure_continuation",
        kind=SignalKind.OPPORTUNITY_CANDIDATE_POST_FAILURE_CONTINUATION,
        severity=severity,
        event_count=len(raw),
        episode_count_estimate=episode_count,
        first_event_index=first,
        last_event_index=last,
        representative_examples=examples,
        raw_event_indices=event_indices,
        impact_on_terminal_outcome=impact,
        falsifier=(
            "post-failure continuation may be legitimate retry logic if the "
            "failure was transient (network, race, lock); check whether the "
            "same call succeeded on retry"
        ),
    )


def aggregate_assistant_self_corrections(
    signals: Iterable[Signal],
    *,
    all_events_count: int,
    has_user_correction_after: bool,
) -> AggregateSignal | None:
    """Aggregate detect_assistant_self_corrections signals.

    High threshold: ≥20 corrections AND span ≥50 events.
    Per spec Phase 4: evaluate whether this family should be aggregated
    or suppressed from default synthesis. This function implements the
    aggregation; disposition (suppress/retain) is decided in Phase 4.
    """
    raw = [s for s in signals if s.detector == "detect_assistant_self_corrections"]
    if not raw:
        return None
    severity = _derive_severity(
        raw,
        high_count_threshold=20,
        high_span_threshold=50,
        has_user_correction_after=has_user_correction_after,
    )
    event_indices = tuple(sorted({i for s in raw for i in s.event_indices}))
    examples = tuple(s.detail[:120] for s in raw[:3])
    first = event_indices[0] if event_indices else 0
    last = event_indices[-1] if event_indices else 0
    episode_count = _estimate_episode_count(event_indices, window=5)

    if severity is SignalSeverity.HIGH:
        impact = (
            f"{len(raw)} assistant self-corrections across {last - first} events — "
            f"high oscillation; the agent kept reversing its own thinking"
        )
    elif severity is SignalSeverity.MEDIUM:
        impact = (
            f"{len(raw)} self-corrections — moderate; some back-and-forth "
            f"is normal in complex reasoning"
        )
    else:
        impact = f"{len(raw)} self-corrections in a short span — normal"

    return AggregateSignal(
        detector="detect_assistant_self_corrections",
        kind=SignalKind.ASSISTANT_SELF_CORRECTION,
        severity=severity,
        event_count=len(raw),
        episode_count_estimate=episode_count,
        first_event_index=first,
        last_event_index=last,
        representative_examples=examples,
        raw_event_indices=event_indices,
        impact_on_terminal_outcome=impact,
        falsifier=(
            "self-corrections are often healthy reasoning signals (the agent "
            "catching its own mistakes before output); count alone overstates harm"
        ),
    )


def _estimate_episode_count(event_indices: tuple[int, ...], *, window: int) -> int:
    """Heuristic: count clusters separated by ≥`window` events.

    A new "episode" starts when there's a gap of ≥window events since the
    last signal in the same family.
    """
    if not event_indices:
        return 0
    sorted_idx = sorted(set(event_indices))
    episodes = 1
    prev = sorted_idx[0]
    for idx in sorted_idx[1:]:
        if idx - prev >= window:
            episodes += 1
        prev = idx
    return episodes


def all_aggregates(
    signals: Iterable[Signal],
    *,
    all_events_count: int,
    has_user_correction_after: bool,
) -> list[AggregateSignal]:
    """Compute every supported aggregate. Returns only non-None entries."""
    sig_list = list(signals)
    out: list[AggregateSignal] = []
    for fn in (
        aggregate_recommendation_revisions,
        aggregate_post_failure_continuation,
        aggregate_assistant_self_corrections,
    ):
        agg = fn(
            sig_list,
            all_events_count=all_events_count,
            has_user_correction_after=has_user_correction_after,
        )
        if agg is not None:
            out.append(agg)
    return out
