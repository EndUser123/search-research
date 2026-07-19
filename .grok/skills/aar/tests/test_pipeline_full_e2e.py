"""End-to-end integration test: full preprocessor + packet-aware validator.

Evidence class: integration + live behavior (against real fixture).

Confirms the entire pipeline works as a chain: resolve identity → snapshot →
reconcile → normalize → detect → index → select context → write packet →
validate a report against the packet.

The report cites real event_ids from the packet and exercises both the
PASS and FAIL paths of the validator.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from full_preprocessor import PREPROCESS_ARTIFACTS, run_full_preprocessor
from output_validator import validate_aar_report_with_packet

SID = "019fabc1-0000-0000-0000-000000000001"


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


def _valid_report(cutoff: str, source_status: str = "SOURCE_COMPLETE_WITH_LIMITATIONS") -> dict:
    """A structurally valid report that cites no event_ids (passes base checks)."""
    return {
        "verdict": {"text": "ok", "scope": "PROBLEM_CLASS"},
        "evidence_scope": {
            "source_status": source_status,
            "snapshot_cutoff": cutoff,
            "sessions_count": 1,
            "boundaries": "single session",
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
                "evidence_event_ids": [],
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


def test_e2e_pipeline_passes_validator_with_packet_citations(tmp_path: Path):
    """Full pipeline → packet → valid report citing real event_ids → PASS."""
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"},
        cutoff="2026-07-18T12:00:00Z",
    )
    assert r.ok

    # Read real event_ids from the packet
    pdir = Path(r.packet_dir)
    canonical_lines = (pdir / "canonical-events.jsonl").read_text(encoding="utf-8").splitlines()
    real_ids = [json.loads(l)["event_id"] for l in canonical_lines if l.strip()]
    assert real_ids

    # Align report source_status with what the manifest earned
    manifest = json.loads((pdir / "source-manifest.json").read_text(encoding="utf-8"))
    earned_status = manifest.get("completeness", {}).get("status", r.source_status)
    report = _valid_report(cutoff=r.snapshot_cutoff, source_status=earned_status)
    report["episodes"][0]["evidence_event_ids"] = [real_ids[0]]

    result = validate_aar_report_with_packet(report, pdir)
    assert result.passed, f"report should pass: {result.summary}\nblockers: {[f.to_dict() for f in result.blockers()]}"


def test_e2e_pipeline_blocks_when_event_id_invented(tmp_path: Path):
    """A report that invents an event_id is caught by the packet-aware validator."""
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"},
        cutoff="2026-07-18T12:00:00Z",
    )
    pdir = Path(r.packet_dir)
    manifest = json.loads((pdir / "source-manifest.json").read_text(encoding="utf-8"))
    earned_status = manifest.get("completeness", {}).get("status", r.source_status)
    report = _valid_report(cutoff=r.snapshot_cutoff, source_status=earned_status)
    report["episodes"][0]["evidence_event_ids"] = ["chat_history-L999999-S999999"]  # invented

    result = validate_aar_report_with_packet(report, pdir)
    assert not result.passed
    blocker_codes = {f.code for f in result.blockers()}
    assert "UNRESOLVED_EVENT_ID" in blocker_codes


def test_e2e_pipeline_blocks_when_status_upgraded(tmp_path: Path):
    """If the packet earned PARTIAL but the report claims COMPLETE, validation fails."""
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"},
        cutoff="2026-07-18T12:00:00Z",
    )
    pdir = Path(r.packet_dir)
    # Force manifest to PARTIAL and claim COMPLETE in the report
    manifest = json.loads((pdir / "source-manifest.json").read_text(encoding="utf-8"))
    manifest["completeness"] = {"status": "SOURCE_PARTIAL"}
    (pdir / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    report = _valid_report(cutoff=r.snapshot_cutoff, source_status="SOURCE_COMPLETE")

    result = validate_aar_report_with_packet(report, pdir)
    assert not result.passed
    assert "SOURCE_STATUS_UPGRADED_BEYOND_MANIFEST" in {f.code for f in result.blockers()}


def test_e2e_unverified_identity_blocks_before_any_artifact(tmp_path: Path):
    """SESSION_IDENTITY_UNVERIFIED stops the pipeline cleanly."""
    _build_session(tmp_path)
    # Corrupt the summary to cause identity mismatch
    sd = tmp_path / "P%3A%5C" / SID
    summary = json.loads((sd / "summary.json").read_text(encoding="utf-8"))
    summary["info"]["id"] = "019fffff-0000-0000-0000-000000000000"
    (sd / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"},
    )
    assert r.ok is False
    assert r.status_label == "SESSION_IDENTITY_UNVERIFIED"
    assert r.source_status == "SOURCE_UNVERIFIED"
    # No canonical events should have been produced.
    assert r.events_total == 0


def test_e2e_no_tmp_files_in_full_run(tmp_path: Path):
    """End-to-end run leaves no .tmp artifacts anywhere in the run dir."""
    _build_session(tmp_path)
    run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"},
        cutoff="2026-07-18T12:00:00Z",
    )
    assert list((tmp_path / "run").rglob("*.tmp")) == []


def test_e2e_artifacts_self_consistent(tmp_path: Path):
    """Cross-check: every event_id in signals is in canonical-events.jsonl;
    every event_id in context-selection is in canonical-events.jsonl."""
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"},
        cutoff="2026-07-18T12:00:00Z",
    )
    pdir = Path(r.packet_dir)
    canonical_ids = {
        json.loads(l)["event_id"]
        for l in (pdir / "canonical-events.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    }
    # context-selection events
    ctx = json.loads((pdir / "context-selection.json").read_text(encoding="utf-8"))
    for ev in ctx["events"]:
        assert ev["event_id"] in canonical_ids, (
            f"context-selection cites {ev['event_id']} not in canonical events"
        )
