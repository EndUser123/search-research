"""Bounded context-selection policy for the LLM AAR synthesis stage.

Per spec Section 14: "Create a bounded context-selection policy. Initial LLM
input should include source manifest summary, session phase outline,
high-confidence deterministic signals, user-correction ledger,
decision/reversal candidates, open parser warnings, compact event excerpts
for top signals. Then allow targeted retrieval by exact event IDs or source
ranges. Do not include all normalized events by default."

Accounting (recorded, never silently dropped):

    events_total
    events_sent_initially
    events_retrieved_later
    selection_reason

This module is **deterministic**. The selection rules are mechanical: top-N
signals by severity, the events they cite, plus the always-included ledgers.
No LLM in the loop at selection time — the LLM only consumes the result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from canonical_model import BranchStatus, CanonicalEvent, CanonicalEventType
from detectors import Signal, SignalSeverity
from indexes import EventIndex

__all__ = [
    "ContextSelection",
    "select_initial_context",
    "select_by_event_ids",
    "DEFAULT_MAX_SIGNALS",
    "DEFAULT_MAX_EVENTS_PER_SIGNAL",
    "DEFAULT_MAX_TOTAL_EVENTS",
]

#: Defaults — every constant needs a justification.
DEFAULT_MAX_SIGNALS = 30  #: ~top 30 signals by severity; enough to seed synthesis without bloating.
DEFAULT_MAX_EVENTS_PER_SIGNAL = 3  #: each signal cites up to 3 events (most cite 1-2).
DEFAULT_MAX_TOTAL_EVENTS = 120  #: hard cap; initial context stays bounded.
DEFAULT_EXCERPT_CHARS = 600  #: per-event text excerpt sent to the LLM.


@dataclass(frozen=True)
class ContextSelection:
    """The bounded context bundle sent to the LLM.

    Fields are tuples (immutable). The ``accounting`` block records what was
    selected vs what was held back — never silently dropped.
    """

    #: Manifest summary (key fields from SourceManifest).
    manifest_summary: dict[str, Any]
    #: High-confidence signals (top-N by severity), in stable order.
    signals: tuple[dict[str, Any], ...]
    #: Canonical events cited by the selected signals (deduped, bounded).
    events: tuple[dict[str, Any], ...]
    #: User-correction event ids (always included).
    user_correction_event_ids: tuple[str, ...]
    #: Decision/reversal candidate event ids (GIT_OPERATION + REWIND).
    decision_candidate_event_ids: tuple[str, ...]
    #: Open parser warnings from the reconciler.
    parser_warnings: tuple[str, ...]
    #: Snapshot cutoff ISO timestamp.
    snapshot_cutoff: str | None
    #: Accounting block (spec Section 14).
    accounting: dict[str, int | str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_summary": dict(self.manifest_summary),
            "signals": list(self.signals),
            "events": list(self.events),
            "user_correction_event_ids": list(self.user_correction_event_ids),
            "decision_candidate_event_ids": list(self.decision_candidate_event_ids),
            "parser_warnings": list(self.parser_warnings),
            "snapshot_cutoff": self.snapshot_cutoff,
            "accounting": dict(self.accounting),
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def select_initial_context(
    *,
    manifest_summary: dict[str, Any],
    events: Iterable[CanonicalEvent],
    signals: Iterable[Signal],
    indexes: EventIndex,
    parser_warnings: Iterable[str] = (),
    snapshot_cutoff: str | None = None,
    max_signals: int = DEFAULT_MAX_SIGNALS,
    max_events_per_signal: int = DEFAULT_MAX_EVENTS_PER_SIGNAL,
    max_total_events: int = DEFAULT_MAX_TOTAL_EVENTS,
    excerpt_chars: int = DEFAULT_EXCERPT_CHARS,
) -> ContextSelection:
    """Build the bounded initial context for the LLM.

    The selection is deterministic: same inputs → same outputs (no model
    calls, no randomness). Selection order:

    1. Top-N signals ordered by (severity rank, signal kind, first event_id).
    2. For each selected signal, the canonical events it cites — mapped from
       stream ``index`` to ``event_id`` via the events list.
    3. Always-included ledgers: user corrections and decision/reversal
       candidates (GIT_OPERATION on ACTIVE_HISTORY).
    4. Hard cap at ``max_total_events`` (further signals are listed in the
       ``signals`` ledger without their event excerpts).
    """
    materialised: list[CanonicalEvent] = list(events)
    by_stream_index = {ce.index: ce for ce in materialised}
    sig_list = list(signals)

    # 1. Order signals by severity (HIGH > MEDIUM > LOW > INFO) then stable.
    severity_rank = {
        SignalSeverity.HIGH: 0,
        SignalSeverity.MEDIUM: 1,
        SignalSeverity.LOW: 2,
        SignalSeverity.INFO: 3,
    }
    ordered_sigs = sorted(
        enumerate(sig_list),
        key=lambda pair: (
            severity_rank.get(pair[1].severity, 9),
            pair[1].kind.value,
            pair[1].event_indices[0] if pair[1].event_indices else 0,
            pair[0],  # preserve original order for ties
        ),
    )
    top_sigs = [s for _, s in ordered_sigs[:max_signals]]

    # 2-3. Collect event_ids, bounded.
    cited_ids: list[str] = []
    cited_set: set[str] = set()
    events_per_sig: dict[int, list[str]] = {}

    for i, sig in enumerate(top_sigs):
        per_sig: list[str] = []
        for idx in sig.event_indices[:max_events_per_signal]:
            ce = by_stream_index.get(idx)
            if ce is None or ce.event_id in cited_set:
                continue
            # Skip SYSTEM_METADATA events — they are not user-facing evidence.
            if ce.branch_status is BranchStatus.SYSTEM_METADATA:
                continue
            per_sig.append(ce.event_id)
            cited_ids.append(ce.event_id)
            cited_set.add(ce.event_id)
            if len(cited_ids) >= max_total_events:
                break
        events_per_sig[i] = per_sig
        if len(cited_ids) >= max_total_events:
            break

    # Always-included ledgers.
    user_corr_ids = list(indexes.by_canonical_type.get("USER_MESSAGE", ()))
    # Filter USER_MESSAGEs whose text matches correction markers — reuse
    # the detector's signal list as the source of truth.
    user_correction_ids_from_signals = {
        eid
        for sig in sig_list
        for eid in (
            [by_stream_index[idx].event_id for idx in sig.event_indices if idx in by_stream_index]
            if sig.kind.value == "user_correction"
            else []
        )
    }
    decision_candidate_ids = list(
        eid for eid in indexes.by_canonical_type.get("GIT_OPERATION", ())
        if eid in indexes.active_event_ids
    )

    # Merge always-included into cited without exceeding max_total_events.
    for eid in user_correction_ids_from_signals:
        if eid not in cited_set and len(cited_ids) < max_total_events:
            cited_ids.append(eid)
            cited_set.add(eid)
    for eid in decision_candidate_ids[:max_total_events]:
        if eid not in cited_set and len(cited_ids) < max_total_events:
            cited_ids.append(eid)
            cited_set.add(eid)

    # Build event excerpts.
    cited_events = [by_stream_index_by_id(materialised, eid) for eid in cited_ids]
    event_dicts = tuple(_excerpt_dict(ce, excerpt_chars) for ce in cited_events if ce is not None)

    # Signals ledger (kind, severity, event_ids, falsifier) — compact.
    sig_dicts = tuple(
        {
            "kind": sig.kind.value,
            "severity": sig.severity.value,
            "detail": sig.detail,
            "falsifier": sig.falsifier,
            "event_ids": [
                by_stream_index[idx].event_id
                for idx in sig.event_indices
                if idx in by_stream_index
            ],
        }
        for sig in top_sigs
    )

    accounting = {
        "events_total": len(materialised),
        "events_sent_initially": len(event_dicts),
        "events_retrieved_later": 0,  # bumped by select_by_event_ids calls
        "selection_reason": (
            f"top-{min(len(top_sigs), max_signals)} signals by severity + "
            f"user-correction + decision candidates; cap={max_total_events}"
        ),
    }

    return ContextSelection(
        manifest_summary=dict(manifest_summary),
        signals=sig_dicts,
        events=event_dicts,
        user_correction_event_ids=tuple(sorted(user_correction_ids_from_signals)),
        decision_candidate_event_ids=tuple(decision_candidate_ids),
        parser_warnings=tuple(parser_warnings),
        snapshot_cutoff=snapshot_cutoff,
        accounting=accounting,
    )


def select_by_event_ids(
    base: ContextSelection,
    event_ids: Iterable[str],
    events: Iterable[CanonicalEvent],
    *,
    excerpt_chars: int = DEFAULT_EXCERPT_CHARS,
) -> ContextSelection:
    """Targeted retrieval: return a new ContextSelection extended with the
    requested event_ids.

    Used when the LLM asks for "give me events E1, E2, E3 in full". Records
    each retrieved id in ``accounting.events_retrieved_later``.

    Unknown event_ids are silently dropped from the result but counted in
    ``accounting['unknown_event_ids_requested']``.
    """
    by_id = {ce.event_id: ce for ce in events}
    requested = list(event_ids)
    known = [eid for eid in requested if eid in by_id]
    unknown = [eid for eid in requested if eid not in by_id]

    existing_ids = {e["event_id"] for e in base.events}
    new_events: list[dict[str, Any]] = []
    for eid in known:
        if eid in existing_ids:
            continue
        new_events.append(_excerpt_dict(by_id[eid], excerpt_chars))

    merged_events = tuple(list(base.events) + new_events)
    new_accounting = dict(base.accounting)
    new_accounting["events_retrieved_later"] = int(new_accounting.get("events_retrieved_later", 0)) + len(new_events)
    new_accounting["unknown_event_ids_requested"] = len(unknown)

    from dataclasses import replace
    return replace(base, events=merged_events, accounting=new_accounting)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _excerpt_dict(ce: CanonicalEvent, excerpt_chars: int) -> dict[str, Any]:
    """Compact dict for the LLM: identifying fields + bounded text excerpt."""
    text = ce.text or ""
    if len(text) > excerpt_chars:
        text = text[:excerpt_chars] + "...<+%d>" % (len(text) - excerpt_chars)
    return {
        "event_id": ce.event_id,
        "turn_index": ce.turn_index,
        "sequence_index": ce.sequence_index,
        "timestamp": ce.timestamp,
        "actor": ce.actor,
        "event_type": ce.canonical_type.value,
        "tool_name": ce.tool_name,
        "command": ce.command,
        "paths": list(ce.paths),
        "branch_status": ce.branch_status.value,
        "exit_code": ce.exit_code,
        "duration_ms": ce.duration_ms,
        "text_excerpt": text,
    }


def by_stream_index_by_id(
    events: list[CanonicalEvent], eid: str
) -> CanonicalEvent | None:
    for ce in events:
        if ce.event_id == eid:
            return ce
    return None
