"""Full-session preprocessing runner.

Per spec Section 12: produce the complete evidence-packet artifact set:

    source-manifest.json
    canonical-events.jsonl
    active-timeline.json
    superseded-events.jsonl
    event-index.json
    signals.json
    claim-evidence.json
    parser-warnings.json
    timeline.md
    preprocess-summary.md

This module is the orchestrator. It chains: resolve → snapshot → parse →
reconcile → normalize → detect → index → select-context → write everything
to ``P:/.artifacts/<terminal>/grok-aar/<run>/preprocess/``.

The existing :func:`evidence_packet.run_preprocessor` stays for the simple
single-file path; this is the full-session path.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from canonical_model import BranchStatus, CanonicalEvent, CanonicalEventType
from completeness import CompletenessClassification, classify_completeness
from context_selector import ContextSelection, select_initial_context
from detectors import Signal, run_all_detectors
from event_model import Event, Role, Transcript
from evidence_packet import resolve_terminal_id
from indexes import EventIndex, build_indexes
from normalizer import CanonicalStream, normalize_session
from reconciler import (
    BRANCH_RECONCILIATION_PARTIAL,
    ReconciliationReport,
    USEFUL_EVENT_TYPES,
    reconcile_sources,
)
from session_resolver import IdentityStatus, SessionBinding, resolve_session_dir
from source_snapshot import SnapshotResult, snapshot_session_sources
from transcript_parser import parse_transcript

__all__ = [
    "PreprocessResult",
    "FullPreprocessError",
    "run_full_preprocessor",
    "PREPROCESS_ARTIFACTS",
]

#: All artifact files written by run_full_preprocessor (spec Section 12).
PREPROCESS_ARTIFACTS: tuple[str, ...] = (
    "source-manifest.json",
    "canonical-events.jsonl",
    "active-timeline.json",
    "superseded-events.jsonl",
    "event-index.json",
    "signals.json",
    "claim-evidence.json",
    "parser-warnings.json",
    "timeline.md",
    "preprocess-summary.md",
    # Supporting artifacts (not in the spec list but required for the AAR
    # skill to consume the packet):
    "context-selection.json",
    "snapshot-manifest.json",  # mirrored from source-snapshot/
)


class FullPreprocessError(Exception):
    """Raised when full preprocessing cannot proceed (e.g. UNVERIFIED identity)."""


@dataclass(frozen=True)
class PreprocessResult:
    """Outcome of the full preprocessing run.

    ``packet_dir`` is the directory the LLM-facing artifacts live in.
    ``source_status`` is the earned completeness classification.
    """

    ok: bool
    status_label: str  #: 'OK' | 'SESSION_IDENTITY_UNVERIFIED' | 'ERROR'
    packet_dir: str | None
    source_status: str  #: one of CompletenessStatus values
    completeness: CompletenessClassification | None
    session_id: str | None
    snapshot_cutoff: str | None
    events_total: int
    active_events: int
    superseded_events: int
    signals_total: int
    warnings: tuple[str, ...]
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status_label": self.status_label,
            "packet_dir": self.packet_dir,
            "source_status": self.source_status,
            "completeness": self.completeness.to_dict() if self.completeness else None,
            "session_id": self.session_id,
            "snapshot_cutoff": self.snapshot_cutoff,
            "events_total": self.events_total,
            "active_events": self.active_events,
            "superseded_events": self.superseded_events,
            "signals_total": self.signals_total,
            "warnings": list(self.warnings),
            "reasons": list(self.reasons),
        }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_full_preprocessor(
    *,
    session_id: str,
    workspace_encoded: str,
    run_dir: str | Path,
    sessions_root: str | Path = "C:/Users/brsth/.grok/sessions",
    env: dict[str, str] | None = None,
    cutoff: str | None = None,
    max_signals: int = 30,
    max_total_events: int = 120,
) -> PreprocessResult:
    """Run the complete full-session preprocessing pipeline.

    Steps:
    1. Resolve + verify session identity (block on UNVERIFIED).
    2. Snapshot all sources atomically under ``<run_dir>/preprocess/source-snapshot/``.
    3. Parse chat_history.jsonl (snapshot copy).
    4. Reconcile against summary.json / events.jsonl / rewind_points.jsonl.
    5. Normalize into canonical stream with branch labels.
    6. Run deterministic detectors.
    7. Build retrieval indexes.
    8. Select bounded LLM context.
    9. Write all 10+ packet artifacts atomically.

    Returns a :class:`PreprocessResult`. Raises :class:`FullPreprocessError`
    only on unrecoverable failure (e.g. session dir missing entirely).
    """
    run_path = Path(run_dir)
    packet_dir = run_path / "preprocess"
    snapshot_root = packet_dir / "source-snapshot"
    packet_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. Resolve identity ---
    binding: SessionBinding = resolve_session_dir(
        session_id=session_id,
        workspace_encoded=workspace_encoded,
        sessions_root=sessions_root,
        env=env,
    )
    if binding.status is not IdentityStatus.VERIFIED:
        return PreprocessResult(
            ok=False,
            status_label="SESSION_IDENTITY_UNVERIFIED",
            packet_dir=str(packet_dir).replace("\\", "/"),
            source_status="SOURCE_UNVERIFIED",
            completeness=None,
            session_id=session_id,
            snapshot_cutoff=cutoff,
            events_total=0,
            active_events=0,
            superseded_events=0,
            signals_total=0,
            warnings=tuple(binding.reasons),
            reasons=tuple(binding.cross_checks) + tuple(binding.reasons),
        )

    # --- 2. Snapshot ---
    snapshot: SnapshotResult = snapshot_session_sources(
        binding.session_dir, snapshot_root, session_id=session_id, cutoff=cutoff
    )

    # --- 3. Parse primary ---
    chat_path = snapshot_root / "chat_history.jsonl"
    if not chat_path.is_file():
        return PreprocessResult(
            ok=False,
            status_label="ERROR",
            packet_dir=str(packet_dir).replace("\\", "/"),
            source_status="SOURCE_UNVERIFIED",
            completeness=None,
            session_id=session_id,
            snapshot_cutoff=snapshot.snapshot_cutoff,
            events_total=0,
            active_events=0,
            superseded_events=0,
            signals_total=0,
            warnings=("chat_history.jsonl missing from snapshot",),
            reasons=("primary source absent",),
        )
    transcript: Transcript = parse_transcript(chat_path)

    # --- 4. Load + filter secondary sources ---
    summary_path = snapshot_root / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else None

    events: list[dict[str, Any]] = []
    events_path = snapshot_root / "events.jsonl"
    if events_path.is_file():
        with events_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    o = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if o.get("type") in USEFUL_EVENT_TYPES:
                    events.append(o)

    rewind: list[dict[str, Any]] = []
    rewind_path = snapshot_root / "rewind_points.jsonl"
    if rewind_path.is_file():
        for line in rewind_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rewind.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # --- 5. Reconcile ---
    reconciliation: ReconciliationReport = reconcile_sources(
        snapshot, transcript, summary=summary, events=events, rewind_points=rewind
    )

    # --- 6. Classify completeness (earned through reconciliation) ---
    completeness: CompletenessClassification = classify_completeness(
        reconciliation.completeness_inputs, snapshot_cutoff=snapshot.snapshot_cutoff
    )

    # --- 7. Normalize ---
    terminal_id, term_warnings = resolve_terminal_id(env=env)
    stream: CanonicalStream = normalize_session(
        transcript,
        reconciliation=reconciliation,
        events=events,
        session_id=session_id,
        terminal_id=terminal_id,
    )

    # --- 8. Detect (over the ACTIVE history per spec Section 7 default) ---
    active_events_for_detection = [
        ce for ce in stream.events if ce.branch_status in (BranchStatus.ACTIVE_HISTORY,)
    ]
    # Detectors accept Iterable[Event]; CanonicalEvent subclasses Event.
    signals: list[Signal] = run_all_detectors(active_events_for_detection)

    # --- 9. Index ---
    indexes: EventIndex = build_indexes(stream.events, signals=signals)

    # --- 10. Select bounded context ---
    manifest_summary = _manifest_summary(reconciliation, completeness)
    context: ContextSelection = select_initial_context(
        manifest_summary=manifest_summary,
        events=stream.events,
        signals=signals,
        indexes=indexes,
        parser_warnings=reconciliation.manifest.warnings + stream.warnings + term_warnings,
        snapshot_cutoff=snapshot.snapshot_cutoff,
        max_signals=max_signals,
        max_total_events=max_total_events,
    )

    # --- 11. Write artifacts ---
    _write_all_artifacts(
        packet_dir=packet_dir,
        snapshot=snapshot,
        reconciliation=reconciliation,
        completeness=completeness,
        stream=stream,
        signals=signals,
        indexes=indexes,
        context=context,
        session_id=session_id,
        terminal_id=terminal_id,
    )

    return PreprocessResult(
        ok=True,
        status_label="OK",
        packet_dir=str(packet_dir).replace("\\", "/"),
        source_status=completeness.status.value,
        completeness=completeness,
        session_id=session_id,
        snapshot_cutoff=snapshot.snapshot_cutoff,
        events_total=len(stream.events),
        active_events=len(stream.active_events),
        superseded_events=len(stream.superseded_events),
        signals_total=len(signals),
        warnings=tuple(snapshot.warnings) + tuple(stream.warnings) + tuple(term_warnings),
        reasons=(),
    )


# ---------------------------------------------------------------------------
# Artifact writers
# ---------------------------------------------------------------------------


def _write_all_artifacts(
    *,
    packet_dir: Path,
    snapshot: SnapshotResult,
    reconciliation: ReconciliationReport,
    completeness: CompletenessClassification,
    stream: CanonicalStream,
    signals: list[Signal],
    indexes: EventIndex,
    context: ContextSelection,
    session_id: str,
    terminal_id: str,
) -> None:
    """Write every spec-required artifact atomically."""

    # source-manifest.json
    _write_atomic_json(packet_dir / "source-manifest.json", reconciliation.manifest.to_dict())

    # canonical-events.jsonl — every event, one JSON object per line
    canonical_lines = [
        json.dumps(
            {**ce.to_canonical_dict(), "session_id": session_id, "terminal_id": terminal_id},
            ensure_ascii=False,
        )
        for ce in stream.events
    ]
    _write_atomic_text(packet_dir / "canonical-events.jsonl", "\n".join(canonical_lines) + ("\n" if canonical_lines else ""))

    # active-timeline.json — the LLM-facing timeline (ACTIVE only)
    active_timeline = [
        _timeline_entry(ce, session_id, terminal_id) for ce in stream.active_events
    ]
    _write_atomic_json(packet_dir / "active-timeline.json", active_timeline)

    # superseded-events.jsonl — separate, per spec
    superseded_lines = [
        json.dumps(
            {**ce.to_canonical_dict(), "session_id": session_id, "terminal_id": terminal_id},
            ensure_ascii=False,
        )
        for ce in stream.superseded_events
    ]
    _write_atomic_text(packet_dir / "superseded-events.jsonl", "\n".join(superseded_lines) + ("\n" if superseded_lines else ""))

    # event-index.json
    _write_atomic_json(packet_dir / "event-index.json", indexes.to_dict())

    # signals.json
    _write_atomic_json(
        packet_dir / "signals.json",
        {
            "signal_total": len(signals),
            "signal_counts": _count_by_kind(signals),
            "signals": [s.to_dict() for s in signals],
        },
    )

    # claim-evidence.json — initial placeholder; LLM populates during synthesis.
    # Schema: list of {claim_id, episode_id, evidence_event_ids, source_status, snapshot_cutoff}
    _write_atomic_json(
        packet_dir / "claim-evidence.json",
        {
            "schema_version": "1.0",
            "snapshot_cutoff": snapshot.snapshot_cutoff,
            "source_status": completeness.status.value,
            "claims": [],
            "note": "Populated by LLM synthesis; validated by output_validator.",
        },
    )

    # parser-warnings.json
    _write_atomic_json(
        packet_dir / "parser-warnings.json",
        {
            "snapshot_warnings": list(snapshot.warnings),
            "manifest_warnings": list(reconciliation.manifest.warnings),
            "stream_warnings": list(stream.warnings),
            "completeness_reasons": list(completeness.reasons),
            "completeness_limitations": list(completeness.limitations),
        },
    )

    # timeline.md — human-readable nav (compaction-style summary, NOT primary evidence)
    _write_atomic_text(packet_dir / "timeline.md", _render_timeline_md(stream, completeness, snapshot))

    # preprocess-summary.md — the orchestration summary
    _write_atomic_text(
        packet_dir / "preprocess-summary.md",
        _render_summary_md(
            snapshot=snapshot,
            reconciliation=reconciliation,
            completeness=completeness,
            stream=stream,
            signals=signals,
            context=context,
        ),
    )

    # Supporting: context-selection.json (LLM input bundle)
    _write_atomic_json(packet_dir / "context-selection.json", context.to_dict())

    # Supporting: mirror snapshot-manifest.json into packet dir for convenience
    _write_atomic_json(packet_dir / "snapshot-manifest.json", snapshot.to_dict())


def _timeline_entry(ce: CanonicalEvent, session_id: str, terminal_id: str) -> dict[str, Any]:
    """Compact timeline entry — fewer fields than canonical-events.jsonl."""
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
        "text_excerpt": (ce.text or "")[:200],
    }


def _render_timeline_md(
    stream: CanonicalStream, completeness: CompletenessClassification, snapshot: SnapshotResult
) -> str:
    """Render a markdown timeline as a *navigation aid* (spec: compaction files
    are navigation only, not primary evidence)."""
    lines = [
        "# AAR Active Timeline (navigation aid)",
        "",
        f"- Snapshot cutoff: {snapshot.snapshot_cutoff}",
        f"- Source status: {completeness.status.value}",
        f"- Active events: {len(stream.active_events)}",
        f"- Superseded events: {len(stream.superseded_events)}",
        "",
        "## Active timeline by turn",
        "",
    ]
    last_turn = None
    shown = 0
    for ce in stream.active_events[:500]:  # cap for readability
        if ce.turn_index != last_turn:
            lines.append(f"\n### Turn {ce.turn_index}")
            last_turn = ce.turn_index
        text = (ce.text or "").replace("\n", " ")[:120]
        lines.append(
            f"- `{ce.event_id}` **{ce.canonical_type.value}** ({ce.actor}) — {text}"
        )
        shown += 1
    if len(stream.active_events) > 500:
        lines.append(f"\n... ({len(stream.active_events) - 500} more active events; see active-timeline.json)")
    return "\n".join(lines) + "\n"


def _render_summary_md(
    *,
    snapshot: SnapshotResult,
    reconciliation: ReconciliationReport,
    completeness: CompletenessClassification,
    stream: CanonicalStream,
    signals: list[Signal],
    context: ContextSelection,
) -> str:
    """Render the orchestrator's summary markdown."""
    r = reconciliation.manifest.reconciliation
    lines = [
        "# AAR Preprocess Summary",
        "",
        "## Source identity",
        f"- session_id: `{snapshot.session_id}`",
        f"- session_dir: `{snapshot.session_dir}`",
        f"- snapshot_cutoff: `{snapshot.snapshot_cutoff}`",
        f"- snapshot_root: `{snapshot.snapshot_root}`",
        f"- drift_detected: `{snapshot.drift_detected}`",
        "",
        "## Completeness (earned through reconciliation)",
        f"- status: **{completeness.status.value}**",
        f"- coverage_through: `{completeness.coverage_through}`",
    ]
    if completeness.reasons:
        lines.append("")
        lines.append("### Reasons")
        for reason in completeness.reasons:
            lines.append(f"- {reason}")
    if completeness.limitations:
        lines.append("")
        lines.append("### Limitations")
        for lim in completeness.limitations:
            lines.append(f"- {lim}")
    if completeness.known_missing_evidence:
        lines.append("")
        lines.append("### Known missing evidence")
        for m in completeness.known_missing_evidence:
            lines.append(f"- {m}")

    lines.extend(
        [
            "",
            "## Reconciliation accounting",
            f"- expected_message_count: `{r.expected_message_count}`",
            f"- reconstructed_message_count: `{r.reconstructed_message_count}`",
            f"- expected_turn_count: `{r.expected_turn_count}`",
            f"- reconstructed_turn_count: `{r.reconstructed_turn_count}`",
            f"- tool_calls_seen: `{r.tool_calls_seen}`",
            f"- tool_results_seen: `{r.tool_results_seen}`",
            f"- unpaired_tool_calls: `{r.unpaired_tool_calls}`",
            f"- unpaired_tool_results: `{r.unpaired_tool_results}`",
            f"- sequence_gaps: `{r.sequence_gaps}`",
            f"- malformed_records: `{r.malformed_records}`",
            f"- rewind_events: `{r.rewind_events}`",
            f"- superseded_records: `{r.superseded_records}`",
            f"- branch_status_label: `{reconciliation.branch_status_label}`",
            "",
            "## Canonical stream",
            f"- events_total: `{len(stream.events)}`",
            f"- active_events: `{len(stream.active_events)}`",
            f"- superseded_events: `{len(stream.superseded_events)}`",
            f"- system_metadata_events: `{len(stream.system_metadata_events)}`",
            f"- cross_link_count: `{stream.cross_link_count}`",
            "",
            "## Deterministic signals",
            f"- signal_total: `{len(signals)}`",
        ]
    )
    counts = _count_by_kind(signals)
    if counts:
        lines.append("")
        lines.append("### By kind")
        for k, v in sorted(counts.items()):
            lines.append(f"- {k}: `{v}`")

    lines.extend(
        [
            "",
            "## Context selection (bounded LLM input)",
            f"- events_total: `{context.accounting['events_total']}`",
            f"- events_sent_initially: `{context.accounting['events_sent_initially']}`",
            f"- selection_reason: {context.accounting['selection_reason']}",
            "",
            "## Parser warnings",
        ]
    )
    all_warnings = list(snapshot.warnings) + list(stream.warnings)
    if all_warnings:
        for w in all_warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append(
        "_This summary contains mechanically derived facts only. Causal "
        "interpretation is the responsibility of the LLM synthesis stage._"
    )
    return "\n".join(lines) + "\n"


def _manifest_summary(
    reconciliation: ReconciliationReport, completeness: CompletenessClassification
) -> dict[str, Any]:
    """Compact manifest summary for the LLM context bundle."""
    m = reconciliation.manifest
    return {
        "snapshot_cutoff": m.snapshot_cutoff,
        "session_id": m.session_id,
        "source_status": completeness.status.value,
        "branch_status_label": reconciliation.branch_status_label,
        "files": [
            {"name": f.path.split("/")[-1], "role": f.source_role, "records": f.parseable_record_count}
            for f in m.files
        ],
        "reconciliation": m.reconciliation.to_dict(),
        "completeness_limitations": list(completeness.limitations),
    }


def _count_by_kind(signals: list[Signal]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for s in signals:
        counts[s.kind.value] = counts.get(s.kind.value, 0) + 1
    return counts


def _write_atomic_json(path: Path, payload: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    os.replace(tmp, p)


def _write_atomic_text(path: Path, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, p)
