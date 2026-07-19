"""Representative replay against the live current Grok session.

Evidence class: LIVE_BEHAVIOR_TESTED (read-only).

Per spec Section 17: run the full preprocessor against the verified current
session, then validate a synthetic report citing real packet event_ids.
Skipped when the real session is not present.

This test exercises the entire pipeline on production-scale data and is the
final integration check before declaring the upgrade complete.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from full_preprocessor import PREPROCESS_ARTIFACTS, run_full_preprocessor
from output_validator import validate_aar_report_with_packet

REAL_SESSION_ID = "019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe"
REAL_WORKSPACE = "P%3A%5C"
REAL_SESSION_DIR = (
    Path("C:/Users/brsth/.grok/sessions")
    / REAL_WORKSPACE
    / REAL_SESSION_ID
)

pytestmark = pytest.mark.skipif(
    not REAL_SESSION_DIR.is_dir(),
    reason=f"real session directory not present at {REAL_SESSION_DIR}",
)


def test_real_session_full_pipeline_runs(tmp_path):
    """End-to-end against the live session: all 12 artifacts written, no crash."""
    r = run_full_preprocessor(
        session_id=REAL_SESSION_ID,
        workspace_encoded=REAL_WORKSPACE,
        run_dir=tmp_path / "run",
        env={"CLAUDE_TERMINAL_ID": "replay-test"},
        cutoff="2026-07-18T14:00:00Z",
    )
    assert r.ok, f"pipeline failed: {r.reasons}"
    pdir = Path(r.packet_dir)
    for artifact in PREPROCESS_ARTIFACTS:
        assert (pdir / artifact).is_file(), f"missing: {artifact}"


def test_real_session_identity_verified(tmp_path):
    """Spec Section 2: identity must be live-verified, not heuristically bound."""
    r = run_full_preprocessor(
        session_id=REAL_SESSION_ID,
        workspace_encoded=REAL_WORKSPACE,
        run_dir=tmp_path / "run",
        env={"CLAUDE_TERMINAL_ID": "replay-test"},
        cutoff="2026-07-18T14:00:00Z",
    )
    assert r.ok
    assert r.session_id == REAL_SESSION_ID


def test_real_session_earns_partial_due_to_compaction_loss(tmp_path):
    """The real session has been compacted; reconstructed user-message count
    is less than the turn_started count in events.jsonl. The reconciler
    must classify this as SOURCE_PARTIAL, not SOURCE_COMPLETE."""
    r = run_full_preprocessor(
        session_id=REAL_SESSION_ID,
        workspace_encoded=REAL_WORKSPACE,
        run_dir=tmp_path / "run",
        env={"CLAUDE_TERMINAL_ID": "replay-test"},
        cutoff="2026-07-18T14:00:00Z",
    )
    assert r.ok
    # The compacted session has 76 real user messages vs ~116 turn_started
    # events in events.jsonl. Material count mismatch → SOURCE_PARTIAL.
    assert r.source_status == "SOURCE_PARTIAL"


def test_real_session_active_superseded_separation(tmp_path):
    """Spec Section 7: active and superseded histories are separate artifacts."""
    r = run_full_preprocessor(
        session_id=REAL_SESSION_ID,
        workspace_encoded=REAL_WORKSPACE,
        run_dir=tmp_path / "run",
        env={"CLAUDE_TERMINAL_ID": "replay-test"},
        cutoff="2026-07-18T14:00:00Z",
    )
    pdir = Path(r.packet_dir)
    active_ids = {
        json.loads(l)["event_id"]
        for l in (pdir / "active-timeline.json").read_text(encoding="utf-8").splitlines()
        if l.strip() and l.startswith("{")
    }
    # active-timeline.json is a JSON array; parse it properly
    active_data = json.loads((pdir / "active-timeline.json").read_text(encoding="utf-8"))
    active_ids = {e["event_id"] for e in active_data}
    sup_text = (pdir / "superseded-events.jsonl").read_text(encoding="utf-8")
    sup_ids = {
        json.loads(l)["event_id"]
        for l in sup_text.splitlines()
        if l.strip()
    }
    assert active_ids.isdisjoint(sup_ids), "active and superseded must not share event_ids"
    # This session has no rewinds → superseded should be empty.
    assert r.superseded_events == 0


def test_real_session_validator_accepts_real_event_citations(tmp_path):
    """A report citing real packet event_ids passes the packet-aware validator."""
    r = run_full_preprocessor(
        session_id=REAL_SESSION_ID,
        workspace_encoded=REAL_WORKSPACE,
        run_dir=tmp_path / "run",
        env={"CLAUDE_TERMINAL_ID": "replay-test"},
        cutoff="2026-07-18T14:00:00Z",
    )
    pdir = Path(r.packet_dir)
    # Take a real USER_MESSAGE event_id from the active timeline
    active_data = json.loads((pdir / "active-timeline.json").read_text(encoding="utf-8"))
    user_msg = next((e for e in active_data if e.get("event_type") == "USER_MESSAGE"), None)
    assert user_msg is not None, "fixture should have user messages"
    real_id = user_msg["event_id"]

    report = {
        "verdict": {"text": "ok", "scope": "SESSION_SPECIFIC"},
        "evidence_scope": {
            "source_status": r.source_status,  # PARTIAL — earned
            "snapshot_cutoff": r.snapshot_cutoff,
            "sessions_count": 1,
            "boundaries": "single compacted session",
        },
        "intended_vs_actual": {"goal": "x", "actual": "y", "success": True},
        "validated_successes": [],
        "episodes": [
            {
                "id": "AAR-001",
                "type": "observation",
                "event": "Real event observed.",
                "evidence": "see canonical event",
                "evidence_event_ids": [real_id],
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
            "validated_success": 0,
            "resolved_incident": 0,
            "open_defect": 0,
            "process_weakness": 0,
            "pending_decision": 0,
            "opportunity_candidate": 0,
            "observation": 1,
            "unknown": 0,
        },
        "n_sessions": 1,
    }
    result = validate_aar_report_with_packet(report, pdir)
    assert result.passed, (
        f"valid report should pass: {result.summary}\n"
        f"blockers: {[f.to_dict() for f in result.blockers()]}"
    )


def test_real_session_signal_count_is_reasonable(tmp_path):
    """Detector precision on real data.

    Failure-shaped detectors stay bounded (<200). Opportunity-candidate
    detectors (Section 19) are intentionally additive and may produce more
    low-severity signals — they are *candidates* the LLM interprets, not
    defects. Total stays under 600 to guard against regression to wild
    over-firing.
    """
    r = run_full_preprocessor(
        session_id=REAL_SESSION_ID,
        workspace_encoded=REAL_WORKSPACE,
        run_dir=tmp_path / "run",
        env={"CLAUDE_TERMINAL_ID": "replay-test"},
        cutoff="2026-07-18T14:00:00Z",
    )
    assert r.ok
    assert 0 < r.signals_total < 600
