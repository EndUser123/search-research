"""Tests for the full-session preprocessor runner.

Evidence class: integration + artifact validation.

Covers spec Section 12 (packet artifacts), Section 16 (AAR integration,
index/packet tests). Builds a controlled session dir, runs the full
preprocessor, and asserts every artifact is well-formed.

Live behavior against the real Grok session is covered separately in
``test_real_session_full_smoke.py``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from full_preprocessor import PREPROCESS_ARTIFACTS, run_full_preprocessor

SID = "019fabc1-0000-0000-0000-000000000001"


def _build_session(
    root: Path,
    *,
    sid: str = SID,
    chat_lines: list[dict] | None = None,
    num_chat_messages: int | None = None,
    events_lines: list[dict] | None = None,
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
    summary = {
        "info": {"id": sid, "cwd": "P:\\"},
        "num_chat_messages": num_chat_messages if num_chat_messages is not None else len(chat_lines),
        "chat_format_version": 1,
    }
    (sd / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    if events_lines is not None:
        (sd / "events.jsonl").write_text(
            "\n".join(json.dumps(x) for x in events_lines) + "\n", encoding="utf-8"
        )
    return sd


# ---------------------------------------------------------------------------
# Happy path — all artifacts written
# ---------------------------------------------------------------------------


def test_full_preprocessor_writes_all_artifacts(tmp_path: Path):
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"},
        cutoff="2026-07-18T00:00:00Z",
    )
    assert r.ok is True
    assert r.status_label == "OK"
    packet_dir = Path(r.packet_dir)
    for artifact in PREPROCESS_ARTIFACTS:
        assert (packet_dir / artifact).is_file(), f"missing artifact: {artifact}"


def test_full_preprocessor_returns_earned_source_status(tmp_path: Path):
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"},
    )
    # Status must be one of the earned-through-reconciliation values.
    assert r.source_status.startswith("SOURCE_")
    assert r.source_status in {
        "SOURCE_COMPLETE", "SOURCE_COMPLETE_WITH_LIMITATIONS",
        "SOURCE_PARTIAL", "SOURCE_UNVERIFIED", "SOURCE_UNSUPPORTED",
    }


# ---------------------------------------------------------------------------
# Identity verification gate
# ---------------------------------------------------------------------------


def test_unverified_identity_blocks(tmp_path: Path):
    """Spec Section 2: 'if current session identity cannot be verified, stop
    with SESSION_IDENTITY_UNVERIFIED'."""
    # Build a session with mismatched summary.json id
    sd = _build_session(tmp_path)
    summary = json.loads((sd / "summary.json").read_text(encoding="utf-8"))
    summary["info"]["id"] = "some-other-id"
    (sd / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"},
    )
    assert r.ok is False
    assert r.status_label == "SESSION_IDENTITY_UNVERIFIED"
    assert r.source_status == "SOURCE_UNVERIFIED"


def test_foreign_session_directory_ignored(tmp_path: Path):
    """The runner does not consume any directory other than the bound one."""
    # Build two sessions under the same root; only the bound one is opened.
    _build_session(tmp_path, sid=SID)
    _build_session(tmp_path, sid="019fabc9-0000-0000-0000-000000000009")
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"},
    )
    assert r.ok is True
    assert r.session_id == SID


# ---------------------------------------------------------------------------
# Artifact validation
# ---------------------------------------------------------------------------


def test_canonical_events_jsonl_is_one_object_per_line(tmp_path: Path):
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"}, cutoff="2026-07-18T00:00:00Z",
    )
    canonical = Path(r.packet_dir) / "canonical-events.jsonl"
    lines = [l for l in canonical.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == r.events_total
    for line in lines:
        obj = json.loads(line)  # each line must be valid JSON
        assert "event_id" in obj
        assert "branch_status" in obj


def test_active_timeline_excludes_superseded(tmp_path: Path):
    """Spec: active and superseded histories are clearly separated."""
    chat = [
        {"type": "system", "content": "sys"},
        {"type": "user", "content": [{"type": "text", "text": "first"}], "prompt_index": 0},
        {"type": "assistant", "content": "v1"},
        {"type": "user", "content": [{"type": "text", "text": "rewound"}], "prompt_index": 0},
        {"type": "assistant", "content": "v2"},
    ]
    _build_session(tmp_path, chat_lines=chat, num_chat_messages=5)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"}, cutoff="2026-07-18T00:00:00Z",
    )
    active = json.loads((Path(r.packet_dir) / "active-timeline.json").read_text(encoding="utf-8"))
    superseded_lines = (Path(r.packet_dir) / "superseded-events.jsonl").read_text(encoding="utf-8").splitlines()
    superseded = [json.loads(l) for l in superseded_lines if l.strip()]

    active_texts = {e.get("text_excerpt") for e in active}
    superseded_texts = {e.get("raw_excerpt") for e in superseded}

    # v1 was superseded; v2 is active.
    assert any("v1" in (t or "") for t in superseded_texts)
    assert not any("v1" in (t or "") for t in active_texts)
    assert any("v2" in (t or "") for t in active_texts)


def test_signals_json_contains_counts_and_signals(tmp_path: Path):
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"}, cutoff="2026-07-18T00:00:00Z",
    )
    data = json.loads((Path(r.packet_dir) / "signals.json").read_text(encoding="utf-8"))
    assert data["signal_total"] == r.signals_total
    assert "signal_counts" in data
    assert isinstance(data["signals"], list)


def test_event_index_resolves_all_canonical_event_ids(tmp_path: Path):
    """Spec: 'all event references resolve'."""
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"}, cutoff="2026-07-18T00:00:00Z",
    )
    canonical_lines = (Path(r.packet_dir) / "canonical-events.jsonl").read_text(encoding="utf-8").splitlines()
    canonical_ids = {json.loads(l)["event_id"] for l in canonical_lines if l.strip()}
    idx_data = json.loads((Path(r.packet_dir) / "event-index.json").read_text(encoding="utf-8"))
    # Index includes by_event_id_count matching the canonical event count.
    assert idx_data["by_event_id_count"] == len(canonical_ids)


def test_context_selection_accounting_reconciles(tmp_path: Path):
    """Spec: 'context-selection accounting reconciles'."""
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"}, cutoff="2026-07-18T00:00:00Z",
    )
    ctx = json.loads((Path(r.packet_dir) / "context-selection.json").read_text(encoding="utf-8"))
    acc = ctx["accounting"]
    # events_sent_initially should equal len(events)
    assert acc["events_sent_initially"] == len(ctx["events"])
    assert acc["events_total"] == r.events_total
    assert acc["events_retrieved_later"] == 0  # initial selection only


def test_snapshot_cutoff_recorded_in_artifacts(tmp_path: Path):
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"}, cutoff="2026-07-18T12:34:56Z",
    )
    summary = (Path(r.packet_dir) / "preprocess-summary.md").read_text(encoding="utf-8")
    assert "2026-07-18T12:34:56Z" in summary
    assert r.snapshot_cutoff == "2026-07-18T12:34:56Z"


def test_preprocess_summary_distinguishes_active_and_superseded(tmp_path: Path):
    """Spec Section 12: summary must distinguish active/superseded/limitations."""
    _build_session(tmp_path)
    r = run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"}, cutoff="2026-07-18T00:00:00Z",
    )
    summary = (Path(r.packet_dir) / "preprocess-summary.md").read_text(encoding="utf-8")
    assert "active_events" in summary
    assert "superseded_events" in summary
    assert "Source status" in summary or "SOURCE_" in summary


# ---------------------------------------------------------------------------
# Atomic writes — no .tmp files left
# ---------------------------------------------------------------------------


def test_no_tmp_files_in_packet_dir(tmp_path: Path):
    _build_session(tmp_path)
    run_full_preprocessor(
        session_id=SID, workspace_encoded="P%3A%5C", run_dir=tmp_path / "run",
        sessions_root=tmp_path, env={"CLAUDE_TERMINAL_ID": "test"}, cutoff="2026-07-18T00:00:00Z",
    )
    run_dir = tmp_path / "run"
    tmps = list(run_dir.rglob("*.tmp"))
    assert tmps == []
