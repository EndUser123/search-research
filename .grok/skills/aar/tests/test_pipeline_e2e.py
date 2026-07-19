"""End-to-end pipeline test: parse → detect → packet → validate.

Evidence classification: CONTRACT_MODEL_TESTED

Confirms the deterministic preprocessor produces a packet the validator
accepts, and that an LLM-style report citing the packet's signals passes the
output gate. This is the integration test that ties the four modules
together.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from detectors import run_all_detectors
from evidence_packet import build_evidence_packet, load_packet, write_packet
from output_validator import validate_aar_report
from transcript_parser import parse_transcript

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "chat_history_sample.jsonl"
VALID_REPORT = FIXTURES / "aar_report_valid.json"


def test_full_pipeline_parse_detect_packet_validate(tmp_path: Path):
    """Parse fixture → run detectors → build packet → write → load → validate a report."""
    # 1. Parse
    transcript = parse_transcript(SAMPLE)
    assert len(transcript.events) > 0
    assert transcript.source_status.value == "SOURCE_COMPLETE"

    # 2. Detect
    signals = run_all_detectors(transcript.events)
    assert len(signals) > 0, "fixture should produce at least one signal"

    # 3. Build packet (inject env + timestamp for determinism)
    packet = build_evidence_packet(
        transcript,
        signals,
        env={"CLAUDE_TERMINAL_ID": "e2e"},
        produced_at="2026-01-01T00:00:00Z",
    )
    assert packet.signal_total == len(signals)
    assert packet.source.terminal_id == "e2e"
    assert packet.integrity is not None

    # 4. Write + reload
    out = write_packet(packet, tmp_path / "packet_dir")
    reloaded = load_packet(out)
    assert reloaded.signal_total == packet.signal_total
    assert reloaded.integrity.content_sha256 == packet.integrity.content_sha256

    # 5. A structurally valid report (the canonical fixture) passes the gate.
    result = validate_aar_report(VALID_REPORT)
    assert result.passed, f"valid report should pass: {result.summary}"


def test_packet_signals_cite_real_event_indices():
    """Every signal's event_indices must reference actual events in the transcript."""
    transcript = parse_transcript(SAMPLE)
    signals = run_all_detectors(transcript.events)
    valid_indices = {e.index for e in transcript.events}
    for sig in signals:
        assert sig.event_indices, f"signal {sig.kind.value} has empty event_indices"
        for idx in sig.event_indices:
            assert idx in valid_indices, (
                f"signal {sig.kind.value} cites unknown event index {idx}"
            )


def test_packet_accounting_honest_about_data_quality():
    """ParseStats data-quality flags surface in the packet."""
    transcript = parse_transcript(SAMPLE)
    packet = build_evidence_packet(
        transcript,
        env={"CLAUDE_TERMINAL_ID": "e2e"},
        produced_at="2026-01-01T00:00:00Z",
    )
    # The fixture has one orphaned tool_result and one arg parse error.
    assert packet.parse_stats["tool_results_orphaned"] == 1
    assert packet.parse_stats["tool_calls_with_parse_error"] == 1
    assert packet.parse_stats["has_timestamps"] is False


def test_invalid_report_fails_pipeline_gate():
    """A report with an invalid episode type must fail validation."""
    bad = json.loads(VALID_REPORT.read_text(encoding="utf-8"))
    bad["episodes"][0]["type"] = "totally_made_up"
    result = validate_aar_report(bad)
    assert not result.passed
    assert any(f.code == "EPISODE_TYPE_INVALID" for f in result.blockers())
