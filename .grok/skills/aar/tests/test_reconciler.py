"""Tests for the multi-source reconciler.

Evidence class: production unit + integration (against real fixture files).

Covers spec Section 5 (source manifest), Section 7 (branch resolution),
and Section 16 (parser/reconciliation + rewind/branch tests).

Builds a synthetic session dir, snapshots it, parses, and reconciles —
exercising the full multi-source accounting path with controlled inputs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from completeness import CompletenessStatus, classify_completeness
from event_model import Role
from reconciler import (
    BRANCH_RECONCILIATION_PARTIAL,
    ReconciliationReport,
    SessionReconciliation,
    SourceManifest,
    reconcile_sources,
    USEFUL_EVENT_TYPES,
)
from session_resolver import IdentityStatus, resolve_session_dir
from source_snapshot import snapshot_session_sources
from transcript_parser import parse_transcript

SID = "019fabc1-0000-0000-0000-000000000001"
SID_OTHER = "019fabc2-0000-0000-0000-000000000002"


def _build_session(
    root: Path,
    *,
    sid: str = SID,
    chat_lines: list[dict] | None = None,
    num_chat_messages: int | None = None,
    summary_id: str | None = None,
    events_lines: list[dict] | None = None,
    rewind_lines: list[dict] | None = None,
) -> Path:
    """Build a controlled session directory for reconciliation tests."""
    sd = root / "P%3A%5C" / sid
    sd.mkdir(parents=True, exist_ok=True)
    if chat_lines is None:
        chat_lines = [
            {"type": "system", "content": "sys"},
            {"type": "user", "content": [{"type": "text", "text": "hi"}], "prompt_index": 0},
            {"type": "assistant", "content": "hello", "model_id": "grok-4.5",
             "tool_calls": [{"id": "c1", "name": "read_file", "arguments": '{"target_file":"a.py"}'}]},
            {"type": "tool_result", "tool_call_id": "c1", "content": "file contents"},
        ]
    (sd / "chat_history.jsonl").write_text(
        "\n".join(json.dumps(x) for x in chat_lines) + "\n", encoding="utf-8"
    )
    summary = {
        "info": {"id": summary_id or sid, "cwd": "P:\\"},
        "num_chat_messages": num_chat_messages if num_chat_messages is not None else len(chat_lines),
        "chat_format_version": 1,
    }
    (sd / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    if events_lines is not None:
        (sd / "events.jsonl").write_text(
            "\n".join(json.dumps(x) for x in events_lines) + "\n", encoding="utf-8"
        )
    if rewind_lines is not None:
        (sd / "rewind_points.jsonl").write_text(
            "\n".join(json.dumps(x) for x in rewind_lines) + "\n", encoding="utf-8"
        )
    return sd


def _snapshot_and_reconcile(session_dir: Path, tmp_path: Path) -> ReconciliationReport:
    snap_root = tmp_path / "snap"
    snap = snapshot_session_sources(session_dir, snap_root, session_id=SID, cutoff="2026-07-18T00:00:00Z")
    t = parse_transcript(snap_root / "chat_history.jsonl")
    summary_path = snap_root / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else None
    events: list[dict] = []
    events_path = snap_root / "events.jsonl"
    if events_path.is_file():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if o.get("type") in USEFUL_EVENT_TYPES:
                events.append(o)
    rewind: list[dict] = []
    rewind_path = snap_root / "rewind_points.jsonl"
    if rewind_path.is_file():
        for line in rewind_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rewind.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return reconcile_sources(snap, t, summary=summary, events=events, rewind_points=rewind)


# ---------------------------------------------------------------------------
# Source manifest structure
# ---------------------------------------------------------------------------


def test_manifest_has_entry_for_each_present_source(tmp_path: Path):
    sd = _build_session(tmp_path, events_lines=[{"ts":"2026-07-18T00:00:00Z","type":"turn_started","session_id":SID,"turn_number":0}])
    rep = _snapshot_and_reconcile(sd, tmp_path)
    names = {f.source_role for f in rep.manifest.files}
    assert "primary" in names
    assert "metadata" in names
    assert "operational" in names


def test_manifest_records_sha_and_counts(tmp_path: Path):
    sd = _build_session(tmp_path)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    chat_entry = next(f for f in rep.manifest.files if f.source_role == "primary")
    assert chat_entry.sha256 is not None
    assert chat_entry.record_count == 4
    assert chat_entry.parseable_record_count == 4


def test_events_jsonl_first_and_last_timestamps_recorded(tmp_path: Path):
    events = [
        {"ts": "2026-07-18T00:00:00Z", "type": "turn_started", "session_id": SID, "turn_number": 0},
        {"ts": "2026-07-18T00:05:00Z", "type": "turn_ended", "outcome": "completed"},
    ]
    sd = _build_session(tmp_path, events_lines=events)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    op_entry = next(f for f in rep.manifest.files if f.source_role == "operational")
    assert op_entry.first_timestamp == "2026-07-18T00:00:00Z"
    assert op_entry.last_timestamp == "2026-07-18T00:05:00Z"


# ---------------------------------------------------------------------------
# Reconciliation accounting
# ---------------------------------------------------------------------------


def test_expected_message_count_comes_from_summary(tmp_path: Path):
    sd = _build_session(tmp_path, num_chat_messages=999)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    assert rep.manifest.reconciliation.expected_message_count == 999


def test_reconstructed_message_count_matches_parsed_events(tmp_path: Path):
    sd = _build_session(tmp_path)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    # 4 records in the default chat_lines fixture
    assert rep.manifest.reconciliation.reconstructed_message_count == 4


def test_tool_call_and_result_pairing_accounted(tmp_path: Path):
    sd = _build_session(tmp_path)  # default has c1 call + c1 result
    rep = _snapshot_and_reconcile(sd, tmp_path)
    r = rep.manifest.reconciliation
    assert r.tool_calls_seen == 1
    assert r.tool_results_seen == 1
    assert r.unpaired_tool_calls == 0
    assert r.unpaired_tool_results == 0


def test_unpaired_tool_result_detected(tmp_path: Path):
    chat = [
        {"type": "system", "content": "sys"},
        {"type": "user", "content": [{"type": "text", "text": "hi"}], "prompt_index": 0},
        {"type": "tool_result", "tool_call_id": "orphan", "content": "x"},
    ]
    sd = _build_session(tmp_path, chat_lines=chat)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    assert rep.manifest.reconciliation.unpaired_tool_results == 1


def test_malformed_records_counted(tmp_path: Path):
    bad_session = tmp_path / "P%3A%5C" / SID
    bad_session.mkdir(parents=True)
    (bad_session / "chat_history.jsonl").write_text(
        json.dumps({"type": "system", "content": "ok"}) + "\nthis is not json\n",
        encoding="utf-8",
    )
    (bad_session / "summary.json").write_text(json.dumps({"info": {"id": SID}, "num_chat_messages": 2}), encoding="utf-8")
    rep = _snapshot_and_reconcile(bad_session, tmp_path)
    assert rep.manifest.reconciliation.malformed_records == 1


# ---------------------------------------------------------------------------
# Branch resolution (Section 7)
# ---------------------------------------------------------------------------


def test_no_duplicates_yields_active_history(tmp_path: Path):
    """Session with no duplicate prompt_indices → ACTIVE_HISTORY, resolved."""
    sd = _build_session(tmp_path)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    assert rep.branch_state_resolved is True
    assert rep.branch_status_label == "ACTIVE_HISTORY"
    assert rep.duplicated_prompt_indices == ()


def test_duplicate_prompt_index_flags_partial_branch(tmp_path: Path):
    """Rewind+replay produces a duplicate prompt_index → BRANCH_RECONCILIATION_PARTIAL."""
    chat = [
        {"type": "system", "content": "sys"},
        {"type": "user", "content": [{"type": "text", "text": "first"}], "prompt_index": 0},
        {"type": "assistant", "content": "v1"},
        {"type": "user", "content": [{"type": "text", "text": "rewound"}], "prompt_index": 0},  # DUPLICATE
        {"type": "assistant", "content": "v2"},
    ]
    sd = _build_session(tmp_path, chat_lines=chat, num_chat_messages=5)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    assert rep.branch_state_resolved is False
    assert rep.branch_status_label == BRANCH_RECONCILIATION_PARTIAL
    assert 0 in rep.duplicated_prompt_indices


def test_synthetic_user_messages_excluded_from_branch_scan(tmp_path: Path):
    """Harness-injected user messages (compaction_meta) are not user turns."""
    chat = [
        {"type": "system", "content": "sys"},
        {"type": "user", "content": [{"type": "text", "text": "real"}], "prompt_index": 0},
        {"type": "user", "content": [{"type": "text", "text": "synthetic"}], "synthetic_reason": "compaction_meta"},
    ]
    sd = _build_session(tmp_path, chat_lines=chat, num_chat_messages=3)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    assert rep.branch_state_resolved is True


# ---------------------------------------------------------------------------
# Completeness integration
# ---------------------------------------------------------------------------


def test_clean_session_classifies_complete_or_with_limitations(tmp_path: Path):
    """A clean session with matching counts → COMPLETE (or WITH_LIMITATIONS if
    events.jsonl is absent, which is a soft gap)."""
    sd = _build_session(
        tmp_path,
        num_chat_messages=4,
        events_lines=[{"ts":"2026-07-18T00:00:00Z","type":"turn_started","session_id":SID,"turn_number":0}],
    )
    rep = _snapshot_and_reconcile(sd, tmp_path)
    inputs = rep.completeness_inputs
    cc = classify_completeness(inputs, snapshot_cutoff="2026-07-18T00:00:00Z")
    # 4 messages match; 1 user msg = 1 turn; events present → should be COMPLETE
    # OR WITH_LIMITATIONS if rewind missing is treated as a limitation (it isn't
    # by default — missing rewind is just no branch evidence).
    assert cc.status in (CompletenessStatus.COMPLETE, CompletenessStatus.COMPLETE_WITH_LIMITATIONS)


def test_count_mismatch_classifies_partial(tmp_path: Path):
    sd = _build_session(tmp_path, num_chat_messages=999)  # claimed 999, actually 4
    rep = _snapshot_and_reconcile(sd, tmp_path)
    cc = classify_completeness(rep.completeness_inputs)
    assert cc.status is CompletenessStatus.PARTIAL


def test_unresolved_branch_classifies_partial(tmp_path: Path):
    chat = [
        {"type": "system", "content": "sys"},
        {"type": "user", "content": [{"type": "text", "text": "x"}], "prompt_index": 0},
        {"type": "user", "content": [{"type": "text", "text": "x"}], "prompt_index": 0},  # dup
    ]
    sd = _build_session(tmp_path, chat_lines=chat, num_chat_messages=3)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    cc = classify_completeness(rep.completeness_inputs)
    assert cc.status is CompletenessStatus.PARTIAL


# ---------------------------------------------------------------------------
# Sequence gaps
# ---------------------------------------------------------------------------


def test_sequence_gaps_detected(tmp_path: Path):
    """prompt_index jumps 0 → 5 → 10 should report gaps."""
    chat = [
        {"type": "system", "content": "sys"},
        {"type": "user", "content": [{"type": "text", "text": "a"}], "prompt_index": 0},
        {"type": "user", "content": [{"type": "text", "text": "b"}], "prompt_index": 5},
        {"type": "user", "content": [{"type": "text", "text": "c"}], "prompt_index": 10},
    ]
    sd = _build_session(tmp_path, chat_lines=chat, num_chat_messages=4)
    rep = _snapshot_and_reconcile(sd, tmp_path)
    # Range 0..10 = 11 slots, 3 present = 8 missing
    assert rep.manifest.reconciliation.sequence_gaps == 8


# ---------------------------------------------------------------------------
# Unsupported schema
# ---------------------------------------------------------------------------


def test_unsupported_chat_format_version_flagged(tmp_path: Path):
    sd = _build_session(tmp_path)
    # Rewrite summary.json with a future chat_format_version
    summary = json.loads((sd / "summary.json").read_text(encoding="utf-8"))
    summary["chat_format_version"] = 99
    (sd / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    rep = _snapshot_and_reconcile(sd, tmp_path)
    assert rep.chat_format_version == 99
    assert rep.completeness_inputs.unsupported_schema is True
    cc = classify_completeness(rep.completeness_inputs)
    assert cc.status is CompletenessStatus.UNSUPPORTED
