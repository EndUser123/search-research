"""Tests for the packet-aware output validator (spec Section 15).

Evidence class: integration.

Builds a real packet dir via the full preprocessor, then validates reports
that cite (or mis-cite) packet evidence. Covers:

* every material episode references known event/signal IDs;
* no claim says SOURCE_COMPLETE when manifest status differs;
* snapshot cutoff appears in the report;
* active vs superseded evidence is labelled.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from full_preprocessor import run_full_preprocessor
from output_validator import validate_aar_report_with_packet

SID = "019fabc1-0000-0000-0000-000000000001"
VALID_REPORT_TEMPLATE = {
    "verdict": {"text": "ok", "scope": "PROBLEM_CLASS"},
    "evidence_scope": {
        "source_status": "SOURCE_COMPLETE_WITH_LIMITATIONS",
        "sessions_count": 1,
        "boundaries": "Single session.",
    },
    "intended_vs_actual": {"goal": "x", "actual": "y", "success": True},
    "validated_successes": [],
    "episodes": [
        {
            "id": "AAR-001",
            "type": "validated_success",
            "event": "Pipeline ran.",
            "evidence": "test",
            "impact": "ok",
            "status": "closed",
        }
    ],
    "decisions": [],
    "recurring_patterns": [],
    "opportunity_candidates": [],
    "open_work": [],
    "routing": [],
    "accounting": {
        "total_episodes": 1,
        "validated_success": 1,
        "resolved_incident": 0,
        "open_defect": 0,
        "process_weakness": 0,
        "pending_decision": 0,
        "opportunity_candidate": 0,
        "observation": 0,
        "unknown": 0,
    },
    "n_sessions": 1,
}


def _build_session(
    root: Path,
    *,
    sid: str = SID,
    chat_lines: list[dict] | None = None,
) -> Path:
    sd = root / "P%3A%5C" / sid
    sd.mkdir(parents=True, exist_ok=True)
    if chat_lines is None:
        chat_lines = [
            {"type": "system", "content": "sys"},
            {"type": "user", "content": [{"type": "text", "text": "hi"}], "prompt_index": 0},
            {"type": "assistant", "content": "hello", "model_id": "grok-4.5"},
        ]
    (sd / "chat_history.jsonl").write_text(
        "\n".join(json.dumps(x) for x in chat_lines) + "\n", encoding="utf-8"
    )
    (sd / "summary.json").write_text(
        json.dumps({"info": {"id": sid, "cwd": "P:\\"}, "num_chat_messages": len(chat_lines), "chat_format_version": 1}),
        encoding="utf-8",
    )
    return sd


@pytest.fixture
def packet_dir(tmp_path: Path) -> Path:
    """Build a real packet via the full preprocessor; return its directory."""
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"},
        cutoff="2026-07-18T12:00:00Z",
    )
    assert r.ok, f"preprocessor failed: {r.reasons}"
    return Path(r.packet_dir)


def _canonical_event_ids(pdir: Path) -> list[str]:
    lines = (pdir / "canonical-events.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(l)["event_id"] for l in lines if l.strip()]


def _report_with_evidence(evidence_event_ids: list[str], *, source_status: str = "SOURCE_COMPLETE_WITH_LIMITATIONS", cutoff: str = "2026-07-18T12:00:00Z") -> dict:
    """Build a report that cites the given event ids."""
    r = json.loads(json.dumps(VALID_REPORT_TEMPLATE))
    r["episodes"][0]["evidence_event_ids"] = evidence_event_ids
    r["episodes"][0]["evidence"] = "see event"
    r["evidence_scope"]["source_status"] = source_status
    r["evidence_scope"]["snapshot_cutoff"] = cutoff
    return r


# ---------------------------------------------------------------------------
# Evidence ID resolution
# ---------------------------------------------------------------------------


def test_known_event_id_passes(packet_dir: Path):
    ids = _canonical_event_ids(packet_dir)
    report = _report_with_evidence([ids[0]])
    result = validate_aar_report_with_packet(report, packet_dir)
    codes = {f.code for f in result.findings}
    assert "UNRESOLVED_EVENT_ID" not in codes


def test_unknown_event_id_is_blocker(packet_dir: Path):
    report = _report_with_evidence(["chat_history-L999999-S999999"])  # not in packet
    result = validate_aar_report_with_packet(report, packet_dir)
    codes = {f.code for f in result.blockers()}
    assert "UNRESOLVED_EVENT_ID" in codes


def test_event_id_in_evidence_text_checked(packet_dir: Path):
    """Free-text evidence containing event-id references is verified too."""
    ids = _canonical_event_ids(packet_dir)
    report = _report_with_evidence([])
    report["episodes"][0]["evidence"] = f"see {ids[0]} and chat_history-L88888888-S000000 (fake)"
    result = validate_aar_report_with_packet(report, packet_dir)
    codes = {f.code for f in result.blockers()}
    assert "UNRESOLVED_EVENT_ID" in codes


# ---------------------------------------------------------------------------
# Source status consistency
# ---------------------------------------------------------------------------


def test_report_upgrading_status_is_blocker(packet_dir: Path):
    """If manifest earned only PARTIAL, report cannot claim COMPLETE."""
    # First inspect the manifest's actual earned status
    manifest = json.loads((packet_dir / "source-manifest.json").read_text(encoding="utf-8"))
    # Force the manifest to record a PARTIAL status for this test
    manifest["completeness"] = {"status": "SOURCE_PARTIAL"}
    (packet_dir / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    report = _report_with_evidence([], source_status="SOURCE_COMPLETE")  # upgrade attempt
    result = validate_aar_report_with_packet(report, packet_dir)
    codes = {f.code for f in result.blockers()}
    assert "SOURCE_STATUS_UPGRADED_BEYOND_MANIFEST" in codes


def test_report_downgrading_status_passes(packet_dir: Path):
    """A stricter claim (PARTIAL when manifest says COMPLETE) is allowed."""
    manifest = json.loads((packet_dir / "source-manifest.json").read_text(encoding="utf-8"))
    manifest["completeness"] = {"status": "SOURCE_COMPLETE"}
    (packet_dir / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    report = _report_with_evidence([], source_status="SOURCE_PARTIAL")
    result = validate_aar_report_with_packet(report, packet_dir)
    codes = {f.code for f in result.blockers()}
    assert "SOURCE_STATUS_UPGRADED_BEYOND_MANIFEST" not in codes


# ---------------------------------------------------------------------------
# Snapshot cutoff
# ---------------------------------------------------------------------------


def test_snapshot_cutoff_must_appear_in_report(packet_dir: Path):
    """Spec Section 15: 'snapshot cutoff appears in the report'."""
    ids = _canonical_event_ids(packet_dir)
    report = _report_with_evidence([ids[0]])
    # Remove cutoff from the report
    del report["evidence_scope"]["snapshot_cutoff"]
    result = validate_aar_report_with_packet(report, packet_dir)
    codes = {f.code for f in result.blockers()}
    assert "SNAPSHOT_CUTOFF_MISSING" in codes


def test_snapshot_cutoff_in_coverage_through_passes(packet_dir: Path):
    """The cutoff may be in evidence_scope.coverage_through as an alternative."""
    ids = _canonical_event_ids(packet_dir)
    report = _report_with_evidence([ids[0]])
    del report["evidence_scope"]["snapshot_cutoff"]
    report["evidence_scope"]["coverage_through"] = "2026-07-18T12:00:00Z"
    result = validate_aar_report_with_packet(report, packet_dir)
    codes = {f.code for f in result.blockers()}
    assert "SNAPSHOT_CUTOFF_MISSING" not in codes


# ---------------------------------------------------------------------------
# Superseded evidence labelling
# ---------------------------------------------------------------------------


def test_superseded_evidence_must_be_labelled(tmp_path: Path):
    """Superseded event ids require from_superseded_history=true."""
    chat = [
        {"type": "system", "content": "sys"},
        {"type": "user", "content": [{"type": "text", "text": "first"}], "prompt_index": 0},
        {"type": "assistant", "content": "v1"},
        {"type": "user", "content": [{"type": "text", "text": "redo"}], "prompt_index": 0},
        {"type": "assistant", "content": "v2"},
    ]
    _build_session(tmp_path, chat_lines=chat)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"}, cutoff="2026-07-18T12:00:00Z",
    )
    pdir = Path(r.packet_dir)
    # Find a superseded event id
    sup_lines = (pdir / "superseded-events.jsonl").read_text(encoding="utf-8").splitlines()
    superseded_ids = [json.loads(l)["event_id"] for l in sup_lines if l.strip()]
    assert superseded_ids, "test fixture should produce superseded events"
    superseded_id = superseded_ids[0]

    report = _report_with_evidence([superseded_id])
    report["episodes"][0]["from_superseded_history"] = False
    result = validate_aar_report_with_packet(report, pdir)
    codes = {f.code for f in result.blockers()}
    assert "SUPERSEDED_EVIDENCE_UNLABELLED" in codes


def test_superseded_evidence_with_flag_passes(tmp_path: Path):
    chat = [
        {"type": "system", "content": "sys"},
        {"type": "user", "content": [{"type": "text", "text": "first"}], "prompt_index": 0},
        {"type": "assistant", "content": "v1"},
        {"type": "user", "content": [{"type": "text", "text": "redo"}], "prompt_index": 0},
        {"type": "assistant", "content": "v2"},
    ]
    _build_session(tmp_path, chat_lines=chat)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"}, cutoff="2026-07-18T12:00:00Z",
    )
    pdir = Path(r.packet_dir)
    sup_lines = (pdir / "superseded-events.jsonl").read_text(encoding="utf-8").splitlines()
    superseded_ids = [json.loads(l)["event_id"] for l in sup_lines if l.strip()]
    report = _report_with_evidence([superseded_ids[0]])
    report["episodes"][0]["from_superseded_history"] = True
    result = validate_aar_report_with_packet(report, pdir)
    codes = {f.code for f in result.blockers()}
    assert "SUPERSEDED_EVIDENCE_UNLABELLED" not in codes


# ---------------------------------------------------------------------------
# Missing manifest
# ---------------------------------------------------------------------------


def test_missing_packet_manifest_is_blocker(tmp_path: Path):
    pdir = tmp_path / "no_packet"
    pdir.mkdir()
    report = _report_with_evidence([])
    result = validate_aar_report_with_packet(report, pdir)
    codes = {f.code for f in result.blockers()}
    assert "PACKET_MISSING_MANIFEST" in codes
