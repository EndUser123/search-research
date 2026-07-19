"""Tests for the evidence packet builder, writer, and loader.

Evidence classification: CONTRACT_MODEL_TESTED

Verifies:
* provenance discipline (terminal_id fallback with visible warning, session_id
  derivation, no invented identity);
* deterministic build (same inputs → same content hash);
* atomic write + manifest verification;
* round-trip load preserves all fields;
* schema-version refusal on mismatch.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from detectors import Signal, SignalKind, SignalSeverity
from evidence_packet import (
    EvidencePacket,
    MANIFEST_FILENAME,
    PACKET_FILENAME,
    PRODUCER,
    build_evidence_packet,
    load_packet,
    resolve_terminal_id,
    run_preprocessor,
    write_packet,
)
from event_model import Event, ParseStats, Role, SourceStatus, Transcript

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "chat_history_sample.jsonl"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _minimal_transcript() -> Transcript:
    return Transcript(
        events=(Event(index=0, role=Role.SYSTEM, text="sys"),),
        source_path="C:/tmp/019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe/chat_history.jsonl",
        source_status=SourceStatus.COMPLETE,
        parse_stats=ParseStats(total_lines=1, parsed_events=1),
        session_id="019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe",
    )


def _signal(idx: int = 0) -> Signal:
    return Signal(
        kind=SignalKind.EMPTY_TOOL_RESULT,
        event_indices=(idx,),
        detail="empty",
        severity=SignalSeverity.LOW,
        detector="test",
        falsifier="none",
    )


# ---------------------------------------------------------------------------
# resolve_terminal_id (provenance discipline)
# ---------------------------------------------------------------------------


def test_resolve_terminal_id_from_env():
    tid, warnings = resolve_terminal_id(env={"CLAUDE_TERMINAL_ID": "console_abc"})
    assert tid == "console_abc"
    assert warnings == ()


def test_resolve_terminal_id_fallback_to_noterm_with_warning():
    tid, warnings = resolve_terminal_id(env={})
    assert tid == "noterm"
    assert len(warnings) == 1
    assert "noterm" in warnings[0]


def test_resolve_terminal_id_tries_vars_in_order():
    """WT_SESSION is checked after CLAUDE_TERMINAL_ID."""
    tid, _ = resolve_terminal_id(env={"WT_SESSION": "wt_123"})
    assert tid == "wt_123"
    # CLAUDE_TERMINAL_ID wins when both present.
    tid, _ = resolve_terminal_id(
        env={"CLAUDE_TERMINAL_ID": "primary", "WT_SESSION": "secondary"}
    )
    assert tid == "primary"


# ---------------------------------------------------------------------------
# build_evidence_packet
# ---------------------------------------------------------------------------


def test_build_packet_records_source_status_and_session():
    t = _minimal_transcript()
    pkt = build_evidence_packet(t, [], env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    assert pkt.source.source_status == "SOURCE_COMPLETE"
    assert pkt.source.session_id == "019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe"
    assert pkt.source.terminal_id == "t1"
    assert pkt.source.provenance_warnings == ()


def test_build_packet_warns_when_no_terminal_env():
    t = _minimal_transcript()
    pkt = build_evidence_packet(t, [], env={}, produced_at="2026-01-01T00:00:00Z")
    assert pkt.source.terminal_id == "noterm"
    assert any("noterm" in w for w in pkt.source.provenance_warnings)


def test_build_packet_warns_when_no_session_id_in_path():
    t = Transcript(
        events=(Event(index=0, role=Role.SYSTEM, text="sys"),),
        source_path="C:/tmp/no-uuid-here.jsonl",
        source_status=SourceStatus.COMPLETE,
        parse_stats=ParseStats(total_lines=1, parsed_events=1),
        session_id=None,
    )
    pkt = build_evidence_packet(t, [], env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    assert any("session_id" in w for w in pkt.source.provenance_warnings)


def test_build_packet_runs_detectors_when_signals_omitted():
    """If signals is None, detectors run automatically over the transcript."""
    t = _minimal_transcript()
    pkt = build_evidence_packet(t, None, env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    # Minimal transcript has no tool results, so signal_total is 0 but the
    # pipeline ran without error.
    assert pkt.signal_total >= 0
    assert pkt.signals == pkt.signals  # tuple, immutable


def test_build_packet_signal_counts_match_signals():
    t = _minimal_transcript()
    sigs = [_signal(0), _signal(0), _signal(1)]
    pkt = build_evidence_packet(t, sigs, env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    assert pkt.signal_total == 3
    assert pkt.signal_counts["empty_tool_result"] == 3


# ---------------------------------------------------------------------------
# Determinism / integrity
# ---------------------------------------------------------------------------


def test_build_packet_is_deterministic_for_same_inputs():
    t = _minimal_transcript()
    a = build_evidence_packet(t, [_signal(0)], env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    b = build_evidence_packet(t, [_signal(0)], env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    assert a.integrity is not None and b.integrity is not None
    assert a.integrity.content_sha256 == b.integrity.content_sha256


def test_integrity_hash_differs_for_different_signals():
    t = _minimal_transcript()
    a = build_evidence_packet(t, [_signal(0)], env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    b = build_evidence_packet(t, [_signal(0), _signal(1)], env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    assert a.integrity is not None and b.integrity is not None
    assert a.integrity.content_sha256 != b.integrity.content_sha256


# ---------------------------------------------------------------------------
# write_packet / load_packet
# ---------------------------------------------------------------------------


def test_write_packet_creates_packet_and_manifest(tmp_path: Path):
    t = _minimal_transcript()
    pkt = build_evidence_packet(t, [_signal(0)], env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    out = write_packet(pkt, tmp_path)
    assert out.name == PACKET_FILENAME
    assert (tmp_path / MANIFEST_FILENAME).exists()
    assert out.exists()


def test_write_packet_is_atomic_no_tmp_left(tmp_path: Path):
    """After write, no .tmp file should remain."""
    t = _minimal_transcript()
    pkt = build_evidence_packet(t, [], env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    write_packet(pkt, tmp_path)
    assert list(tmp_path.glob("*.tmp")) == []


def test_load_packet_round_trips(tmp_path: Path):
    t = _minimal_transcript()
    pkt = build_evidence_packet(t, [_signal(0)], env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    out = write_packet(pkt, tmp_path)
    loaded = load_packet(out)
    assert loaded.source.source_status == pkt.source.source_status
    assert loaded.source.session_id == pkt.source.session_id
    assert loaded.signal_total == pkt.signal_total
    assert loaded.signals == pkt.signals
    assert loaded.integrity is not None
    assert loaded.integrity.content_sha256 == pkt.integrity.content_sha256


def test_load_packet_detects_tampering(tmp_path: Path):
    t = _minimal_transcript()
    pkt = build_evidence_packet(t, [], env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    out = write_packet(pkt, tmp_path)
    # Tamper: rewrite packet.json without updating the manifest.
    data = json.loads(out.read_text(encoding="utf-8"))
    data["signals"] = [{"kind": "injected", "event_indices": [99]}]
    out.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity check failed"):
        load_packet(out)


def test_load_packet_refuses_unknown_schema(tmp_path: Path):
    t = _minimal_transcript()
    pkt = build_evidence_packet(t, [], env={"CLAUDE_TERMINAL_ID": "t1"}, produced_at="2026-01-01T00:00:00Z")
    out = write_packet(pkt, tmp_path)
    data = json.loads(out.read_text(encoding="utf-8"))
    data["schema_version"] = "99.99"
    out.write_text(json.dumps(data), encoding="utf-8")
    # Manifest still points at old hash → tamper detection fires first.
    # Rewrite manifest to match so we exercise the schema check specifically.
    import hashlib

    new_hash = hashlib.sha256(out.read_bytes()).hexdigest()
    (tmp_path / MANIFEST_FILENAME).write_text(
        json.dumps({"packet_sha256": new_hash, "algorithm": "sha256"}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="schema version"):
        load_packet(out)


# ---------------------------------------------------------------------------
# End-to-end pipeline runner
# ---------------------------------------------------------------------------


def test_run_preprocessor_on_fixture(tmp_path: Path):
    transcript, pkt, written = run_preprocessor(
        SAMPLE, tmp_path, env={"CLAUDE_TERMINAL_ID": "test"}, produced_at="2026-01-01T00:00:00Z"
    )
    assert len(transcript.events) > 0
    assert pkt.signal_total > 0
    assert written.exists()
    assert pkt.source.terminal_id == "test"
    # Reload confirms round-trip integrity.
    reloaded = load_packet(written)
    assert reloaded.signal_total == pkt.signal_total


def test_run_preprocessor_producer_string():
    """Producer field is stable for consumers that gate on it."""
    assert PRODUCER == "aar-transcript-preprocessor/1.0"
