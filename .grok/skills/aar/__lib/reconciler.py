"""Multi-source reconciliation.

Per spec Section 5: build a source manifest with per-file hashes/counts and
session-level reconciliation accounting. Per spec Section 7: resolve rewind
and branch semantics.

Inputs
------
* A :class:`source_snapshot.SnapshotResult` (immutable snapshot of the
  session dir).
* Parsed artifacts from each snapshot file:
    - chat_history.jsonl → :class:`event_model.Transcript`
    - summary.json → dict
    - events.jsonl → filtered dict records (turn_started/ended, tool_*,
      loop_started)
    - rewind_points.jsonl → list of dicts

Outputs
-------
* :class:`SourceManifest` — per-file accounting + session-level accounting.
* :class:`ReconciliationReport` — the synthetic summary used to drive
  :func:`completeness.classify_completeness` and downstream normalisation.

Branch resolution
-----------------
``rewind_points.jsonl`` records file-state snapshots per prompt but has no
explicit "this branch was abandoned" marker. We resolve branch status
structurally by scanning chat_history for duplicate ``prompt_index`` values
on user messages:

* First occurrence of a given prompt_index → ``ACTIVE_HISTORY``.
* Subsequent occurrences (rewind + replay) → ``SUPERSEDED_HISTORY`` for the
  earlier branch from that prompt_index forward, until the next rewind.

When the structure is ambiguous (e.g. malformed prompt_index, gaps), the
default is ``BRANCH_UNKNOWN`` and ``branch_state_resolved=False`` — which
downgrades completeness to PARTIAL.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from completeness import CompletenessInputs
from event_model import ParseStats, Role, Transcript
from source_snapshot import SnapshotResult

__all__ = [
    "SourceFileManifestEntry",
    "SourceManifest",
    "ReconciliationReport",
    "reconcile_sources",
    "summarise_snapshot_for_manifest",
    "USEFUL_EVENT_TYPES",
    "BRANCH_RECONCILIATION_PARTIAL",
]

#: Status string emitted when branch semantics cannot be fully resolved.
BRANCH_RECONCILIATION_PARTIAL = "BRANCH_RECONCILIATION_PARTIAL"

#: events.jsonl is 97% phase_changed noise. Filter to the useful types so
#: reconciliation and cross-linking stay tractable. This is a deterministic
#: filter on the ``type`` field, not LLM-driven grep.
USEFUL_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "turn_started",
        "turn_ended",
        "tool_started",
        "tool_completed",
        "permission_requested",
        "permission_resolved",
        "loop_started",
        "first_token",
        "yolo_toggled",
        "goal_classifier_fail_open",
    }
)


@dataclass(frozen=True)
class SourceFileManifestEntry:
    """Per-file manifest entry (spec Section 5 first block)."""

    path: str
    source_role: str
    size_bytes: int
    sha256: str | None
    record_count: int
    parseable_record_count: int
    skipped_record_count: int
    first_timestamp: str | None
    last_timestamp: str | None
    session_id: str | None
    schema_version: str | None
    snapshot_cutoff: str
    changed_during_snapshot: bool
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "source_role": self.source_role,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "record_count": self.record_count,
            "parseable_record_count": self.parseable_record_count,
            "skipped_record_count": self.skipped_record_count,
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
            "session_id": self.session_id,
            "schema_version": self.schema_version,
            "snapshot_cutoff": self.snapshot_cutoff,
            "changed_during_snapshot": self.changed_during_snapshot,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class SourceManifest:
    """Full source manifest (spec Section 5)."""

    snapshot_root: str
    snapshot_cutoff: str
    session_id: str
    files: tuple[SourceFileManifestEntry, ...]
    directories: tuple[dict[str, Any], ...]
    reconciliation: "SessionReconciliation"
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_root": self.snapshot_root,
            "snapshot_cutoff": self.snapshot_cutoff,
            "session_id": self.session_id,
            "files": [f.to_dict() for f in self.files],
            "directories": [dict(d) for d in self.directories],
            "reconciliation": self.reconciliation.to_dict(),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class SessionReconciliation:
    """Session-level accounting (spec Section 5 second block)."""

    expected_message_count: int | None
    reconstructed_message_count: int
    expected_turn_count: int | None
    reconstructed_turn_count: int
    tool_calls_seen: int
    tool_results_seen: int
    unpaired_tool_calls: int
    unpaired_tool_results: int
    duplicate_record_ids: int
    sequence_gaps: int
    malformed_records: int
    rewind_events: int
    superseded_records: int
    active_records: int
    unknown_branch_records: int
    expected_count_source: str  #: 'summary.json' | 'events.jsonl' | 'none'

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_message_count": self.expected_message_count,
            "reconstructed_message_count": self.reconstructed_message_count,
            "expected_turn_count": self.expected_turn_count,
            "reconstructed_turn_count": self.reconstructed_turn_count,
            "tool_calls_seen": self.tool_calls_seen,
            "tool_results_seen": self.tool_results_seen,
            "unpaired_tool_calls": self.unpaired_tool_calls,
            "unpaired_tool_results": self.unpaired_tool_results,
            "duplicate_record_ids": self.duplicate_record_ids,
            "sequence_gaps": self.sequence_gaps,
            "malformed_records": self.malformed_records,
            "rewind_events": self.rewind_events,
            "superseded_records": self.superseded_records,
            "active_records": self.active_records,
            "unknown_branch_records": self.unknown_branch_records,
            "expected_count_source": self.expected_count_source,
        }


@dataclass(frozen=True)
class ReconciliationReport:
    """Synthesised view driving completeness classification + normalisation."""

    manifest: SourceManifest
    #: prompt_index values that appeared more than once in user messages
    #: (i.e. were rewound and replayed). Each later occurrence supersedes
    #: the prior branch from that index forward.
    duplicated_prompt_indices: tuple[int, ...]
    #: True iff branch semantics could be fully resolved.
    branch_state_resolved: bool
    branch_status_label: str  #: ACTIVE_HISTORY or BRANCH_RECONCILIATION_PARTIAL
    #: Pre-computed inputs for completeness.classify_completeness.
    completeness_inputs: CompletenessInputs
    #: chat_format_version from summary.json (for unsupported_schema check).
    chat_format_version: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest.to_dict(),
            "duplicated_prompt_indices": list(self.duplicated_prompt_indices),
            "branch_state_resolved": self.branch_state_resolved,
            "branch_status_label": self.branch_status_label,
            "completeness_inputs": _completeness_inputs_to_dict(self.completeness_inputs),
            "chat_format_version": self.chat_format_version,
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def reconcile_sources(
    snapshot: SnapshotResult,
    transcript: Transcript,
    *,
    summary: dict[str, Any] | None = None,
    events: list[dict[str, Any]] | None = None,
    rewind_points: list[dict[str, Any]] | None = None,
) -> ReconciliationReport:
    """Build a SourceManifest and ReconciliationReport from parsed sources.

    All sources are the **parsed snapshot copies** (the orchestrator is
    responsible for snapshot-then-parse). ``transcript`` is the parsed
    chat_history.jsonl; the others are parsed JSON objects/lists.
    """
    warnings: list[str] = []

    # --- Per-file manifest entries ---
    file_entries: list[SourceFileManifestEntry] = []
    for sf in snapshot.files:
        if not sf.present:
            file_entries.append(_absent_entry(sf, snapshot.snapshot_cutoff))
            continue

        # Parse the snapshot copy for counts/timestamps.
        snap_path = Path(sf.snapshot_path)
        if sf.name == "chat_history.jsonl":
            entry = _entry_from_transcript(sf, transcript, snapshot.snapshot_cutoff)
        elif sf.name == "summary.json":
            entry = _entry_from_summary_json(sf, snap_path, snapshot.snapshot_cutoff, summary)
        elif sf.name == "events.jsonl":
            entry = _entry_from_events_jsonl(sf, snap_path, snapshot.snapshot_cutoff)
        elif sf.name == "rewind_points.jsonl":
            entry = _entry_from_rewind_jsonl(sf, snap_path, snapshot.snapshot_cutoff)
        else:
            entry = _generic_entry(sf, snap_path, snapshot.snapshot_cutoff)
        file_entries.append(entry)

    # --- Session-level reconciliation ---
    expected_msg = None
    expected_turn = None
    expected_source = "none"
    schema_version = None
    if summary and isinstance(summary, dict):
        info = summary.get("info") if isinstance(summary.get("info"), dict) else {}
        expected_msg = summary.get("num_chat_messages")
        schema_version = (
            str(summary.get("chat_format_version"))
            if summary.get("chat_format_version") is not None
            else None
        )
        expected_source = "summary.json"
        # num_messages is the *full* message count (includes compacted);
        # num_chat_messages is the live chat count and is the right comparison
        # for reconstructed_message_count.

    # Turn count: prefer turn_started count from events.jsonl when available.
    turn_started_count = None
    if events:
        turn_started_count = sum(1 for e in events if e.get("type") == "turn_started")
        if turn_started_count:
            expected_turn = turn_started_count
            expected_source = "events.jsonl" if expected_source == "none" else expected_source + "+events.jsonl"

    # Reconstructed counts from the parsed transcript.
    stats: ParseStats = transcript.parse_stats
    reconstructed_msg = stats.parsed_events
    # Turns ≈ real user messages (each real user prompt starts a turn).
    reconstructed_turn = stats.real_user_messages

    # Tool call/result pairing.
    produced_ids = {
        tc.id for ev in transcript.events for tc in ev.tool_calls if ev.role is Role.ASSISTANT
    }
    result_ids = {ev.tool_call_id for ev in transcript.events if ev.role is Role.TOOL_RESULT}
    unpaired_results = sum(
        1 for ev in transcript.events if ev.role is Role.TOOL_RESULT and ev.tool_call_id not in produced_ids
    )
    unpaired_calls = sum(
        1 for ev in transcript.events for tc in ev.tool_calls
        if ev.role is Role.ASSISTANT and tc.id not in result_ids
    )

    # Branch resolution: scan for duplicate prompt_index values in real user msgs.
    seen_indices: dict[int, int] = {}
    duplicates: list[int] = []
    for ev in transcript.events:
        if ev.role is not Role.USER or ev.synthetic_reason:
            continue
        pi = ev.prompt_index
        if pi is None:
            continue
        if pi in seen_indices:
            duplicates.append(pi)
        else:
            seen_indices[pi] = 1

    # Sequence gaps in prompt_index (e.g. prompts 0,1,2,5 → gap at 3,4).
    real_indices = sorted(seen_indices.keys())
    seq_gaps = 0
    if real_indices:
        seq_gaps = max(0, (real_indices[-1] - real_indices[0] + 1) - len(real_indices))

    # Branch accounting: if duplicates exist, the earlier branch from each
    # duplicated prompt_index is superseded. We can't count exact superseded
    # records without the normalizer running, so we approximate: each
    # duplicate represents one prior branch that was abandoned.
    superseded_estimate = 0
    branch_resolved = True
    if duplicates:
        # Without explicit schema markers, we mark branch state as PARTIAL.
        # The normalizer will still attempt structural resolution and label
        # records SUPERSEDED_HISTORY; completeness drops to PARTIAL.
        branch_resolved = False
        superseded_estimate = len(duplicates)

    rewind_count = len(rewind_points) if rewind_points else 0

    recon = SessionReconciliation(
        expected_message_count=expected_msg if isinstance(expected_msg, int) else None,
        reconstructed_message_count=reconstructed_msg,
        expected_turn_count=expected_turn,
        reconstructed_turn_count=reconstructed_turn,
        tool_calls_seen=stats.tool_calls_total,
        tool_results_seen=stats.by_role.get(Role.TOOL_RESULT.value, 0),
        unpaired_tool_calls=unpaired_calls,
        unpaired_tool_results=unpaired_results,
        duplicate_record_ids=stats.unknown_role_lines,  # structural dup proxy
        sequence_gaps=seq_gaps,
        malformed_records=stats.skipped_malformed,
        rewind_events=rewind_count,
        superseded_records=superseded_estimate,
        active_records=reconstructed_msg - superseded_estimate,
        unknown_branch_records=0 if branch_resolved else reconstructed_msg,
        expected_count_source=expected_source,
    )

    manifest = SourceManifest(
        snapshot_root=snapshot.snapshot_root,
        snapshot_cutoff=snapshot.snapshot_cutoff,
        session_id=snapshot.session_id,
        files=tuple(file_entries),
        directories=snapshot.directories,
        reconciliation=recon,
        warnings=tuple(warnings + list(snapshot.warnings)),
    )

    # --- Completeness inputs ---
    # chat_format_version=1 is the only schema the existing parser handles.
    unsupported_schema = schema_version is not None and schema_version != "1"

    # Start boundary: first event must be system OR a real user message.
    has_start = bool(transcript.events) and transcript.events[0].role in (
        Role.SYSTEM,
        Role.USER,
    )

    missing: list[str] = []
    if not any(f.name == "events.jsonl" and f.present for f in snapshot.files):
        missing.append("events.jsonl absent (no operational cross-check)")
    if not any(f.name == "rewind_points.jsonl" and f.present for f in snapshot.files):
        missing.append("rewind_points.jsonl absent (no branch evidence)")

    inputs = CompletenessInputs(
        identity_verified=True,  # set by orchestrator from SessionBinding
        chat_history_present=any(
            f.name == "chat_history.jsonl" and f.present for f in snapshot.files
        ),
        chat_history_fully_parsed=stats.skipped_malformed == 0,
        chat_history_start_boundary=has_start,
        expected_message_count=recon.expected_message_count,
        reconstructed_message_count=recon.reconstructed_message_count,
        expected_turn_count=recon.expected_turn_count,
        reconstructed_turn_count=recon.reconstructed_turn_count,
        branch_state_resolved=branch_resolved,
        unexplained_sequence_gaps=seq_gaps,
        known_missing_evidence=tuple(missing),
        truncated_tool_outputs=sum(
            1 for ev in transcript.events
            if ev.role is Role.TOOL_RESULT and (ev.text is None or not ev.text.strip())
        ),
        unsupported_schema=unsupported_schema,
        unsupported_format=False,
    )

    return ReconciliationReport(
        manifest=manifest,
        duplicated_prompt_indices=tuple(dict.fromkeys(duplicates)),
        branch_state_resolved=branch_resolved,
        branch_status_label=(
            "ACTIVE_HISTORY" if branch_resolved else BRANCH_RECONCILIATION_PARTIAL
        ),
        completeness_inputs=inputs,
        chat_format_version=int(schema_version) if schema_version and schema_version.isdigit() else None,
    )


def summarise_snapshot_for_manifest(snapshot: SnapshotResult) -> dict[str, Any]:
    """Convenience: snapshot-only manifest (before parsing). Used when the
    orchestrator wants a manifest written even if downstream parsing fails."""
    return {
        "snapshot_root": snapshot.snapshot_root,
        "snapshot_cutoff": snapshot.snapshot_cutoff,
        "session_id": snapshot.session_id,
        "files": [f.to_dict() for f in snapshot.files],
        "directories": [dict(d) for d in snapshot.directories],
        "drift_detected": snapshot.drift_detected,
        "warnings": list(snapshot.warnings),
    }


# ---------------------------------------------------------------------------
# Per-file entry builders
# ---------------------------------------------------------------------------


def _absent_entry(sf, cutoff: str) -> SourceFileManifestEntry:
    return SourceFileManifestEntry(
        path=sf.snapshot_path,
        source_role=sf.source_role,
        size_bytes=0,
        sha256=None,
        record_count=0,
        parseable_record_count=0,
        skipped_record_count=0,
        first_timestamp=None,
        last_timestamp=None,
        session_id=None,
        schema_version=None,
        snapshot_cutoff=cutoff,
        changed_during_snapshot=False,
        warnings=("source absent",),
    )


def _entry_from_transcript(sf, transcript: Transcript, cutoff: str) -> SourceFileManifestEntry:
    stats = transcript.parse_stats
    return SourceFileManifestEntry(
        path=sf.snapshot_path,
        source_role="primary",
        size_bytes=sf.size_bytes,
        sha256=sf.sha256_snapshot,
        record_count=stats.total_lines,
        parseable_record_count=stats.parsed_events,
        skipped_record_count=stats.skipped_malformed,
        first_timestamp=None,  # chat_history has no timestamps
        last_timestamp=None,
        session_id=transcript.session_id,
        schema_version="chat_history_v1",
        snapshot_cutoff=cutoff,
        changed_during_snapshot=sf.changed_during_snapshot,
        warnings=tuple(stats.warnings),
    )


def _entry_from_summary_json(sf, snap_path: Path, cutoff: str, parsed: dict | None) -> SourceFileManifestEntry:
    sid = None
    schema = None
    if parsed and isinstance(parsed, dict):
        info = parsed.get("info") if isinstance(parsed.get("info"), dict) else {}
        sid = info.get("id")
        schema = str(parsed.get("chat_format_version")) if parsed.get("chat_format_version") is not None else None
    return SourceFileManifestEntry(
        path=sf.snapshot_path,
        source_role="metadata",
        size_bytes=sf.size_bytes,
        sha256=sf.sha256_snapshot,
        record_count=1,
        parseable_record_count=1 if parsed else 0,
        skipped_record_count=0 if parsed else 1,
        first_timestamp=None,
        last_timestamp=None,
        session_id=sid,
        schema_version=schema,
        snapshot_cutoff=cutoff,
        changed_during_snapshot=sf.changed_during_snapshot,
    )


def _entry_from_events_jsonl(sf, snap_path: Path, cutoff: str) -> SourceFileManifestEntry:
    total = 0
    parseable = 0
    skipped = 0
    first_ts = None
    last_ts = None
    sid_seen = None
    with snap_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            total += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            parseable += 1
            ts = obj.get("ts")
            if isinstance(ts, str):
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
            if obj.get("type") == "turn_started" and isinstance(obj.get("session_id"), str):
                sid_seen = obj["session_id"]
    return SourceFileManifestEntry(
        path=sf.snapshot_path,
        source_role="operational",
        size_bytes=sf.size_bytes,
        sha256=sf.sha256_snapshot,
        record_count=total,
        parseable_record_count=parseable,
        skipped_record_count=skipped,
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        session_id=sid_seen,
        schema_version="events_v1",
        snapshot_cutoff=cutoff,
        changed_during_snapshot=sf.changed_during_snapshot,
    )


def _entry_from_rewind_jsonl(sf, snap_path: Path, cutoff: str) -> SourceFileManifestEntry:
    total = 0
    parseable = 0
    skipped = 0
    first_ts = None
    last_ts = None
    with snap_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            total += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            parseable += 1
            ts = obj.get("created_at")
            if isinstance(ts, str):
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
    return SourceFileManifestEntry(
        path=sf.snapshot_path,
        source_role="branch",
        size_bytes=sf.size_bytes,
        sha256=sf.sha256_snapshot,
        record_count=total,
        parseable_record_count=parseable,
        skipped_record_count=skipped,
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        session_id=None,
        schema_version="rewind_v1",
        snapshot_cutoff=cutoff,
        changed_during_snapshot=sf.changed_during_snapshot,
    )


def _generic_entry(sf, snap_path: Path, cutoff: str) -> SourceFileManifestEntry:
    return SourceFileManifestEntry(
        path=sf.snapshot_path,
        source_role=sf.source_role,
        size_bytes=sf.size_bytes,
        sha256=sf.sha256_snapshot,
        record_count=0,
        parseable_record_count=0,
        skipped_record_count=0,
        first_timestamp=None,
        last_timestamp=None,
        session_id=None,
        schema_version=None,
        snapshot_cutoff=cutoff,
        changed_during_snapshot=sf.changed_during_snapshot,
    )


def _completeness_inputs_to_dict(inputs: CompletenessInputs) -> dict[str, Any]:
    """Minimal dict for the report (CompletenessInputs has no to_dict)."""
    return {
        "identity_verified": inputs.identity_verified,
        "chat_history_present": inputs.chat_history_present,
        "chat_history_fully_parsed": inputs.chat_history_fully_parsed,
        "chat_history_start_boundary": inputs.chat_history_start_boundary,
        "expected_message_count": inputs.expected_message_count,
        "reconstructed_message_count": inputs.reconstructed_message_count,
        "expected_turn_count": inputs.expected_turn_count,
        "reconstructed_turn_count": inputs.reconstructed_turn_count,
        "branch_state_resolved": inputs.branch_state_resolved,
        "unexplained_sequence_gaps": inputs.unexplained_sequence_gaps,
        "known_missing_evidence": list(inputs.known_missing_evidence),
        "truncated_tool_outputs": inputs.truncated_tool_outputs,
        "unsupported_schema": inputs.unsupported_schema,
        "unsupported_format": inputs.unsupported_format,
    }
