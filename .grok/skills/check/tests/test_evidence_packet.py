"""Tests for ``evidence_packet.py``.

Evidence classification: CONTRACT_MODEL_TESTED + fixture-grounded
"""

import json
from pathlib import Path

import pytest

import transcript_parser as tp
import evidence_packet as ep
import detectors as d
import event_model as m

FIXTURE = Path(__file__).parent / "fixture_sample.jsonl"


@pytest.fixture(scope="module")
def packet():
    t = tp.parse_file(FIXTURE)
    return ep.build_packet(t, produced_at="2026-07-18T00:00:00+00:00")


def test_build_packet_runs_all_detectors(packet):
    counts = packet.signal_counts
    for name in d.DETECTOR_NAMES:
        assert name in counts


def test_packet_has_required_top_level_keys(packet):
    dct = packet.to_dict()
    for k in ("schema_version", "producer", "produced_at", "source", "parse_stats", "signal_counts", "signals", "warnings"):
        assert k in dct


def test_packet_schema_version(packet):
    assert packet.schema_version == m.PACKET_SCHEMA_VERSION


def test_packet_source_carries_provenance(packet):
    src = packet.to_dict()["source"]
    assert src["path"].endswith("fixture_sample.jsonl")
    assert src["status"] == "SOURCE_COMPLETE"
    assert src["session_id"] is None  # fixture has no UUID parent
    assert src["has_timestamps"] is False
    assert src["line_count"] > 0


def test_packet_reconciles(packet):
    assert packet.reconciles() is True


def test_signal_counts_match_len_signals(packet):
    dct = packet.to_dict()
    for name, count in dct["signal_counts"].items():
        assert count == len(dct["signals"][name])


def test_json_roundtrip_preserves_counts(packet):
    blob = packet.to_json()
    rt = json.loads(blob)
    assert rt["signal_counts"] == packet.signal_counts
    assert rt["schema_version"] == packet.schema_version


def test_json_serialisable_with_no_unicode_errors(packet):
    blob = packet.to_json()
    assert isinstance(blob, str)
    # Re-decode to confirm valid JSON
    json.loads(blob)


def test_write_atomic_and_readable(packet, tmp_path):
    out = tmp_path / "pkt.json"
    written = packet.write(str(out))
    assert Path(written).exists()
    # No .tmp leftover
    assert not (tmp_path / "pkt.json.tmp").exists()
    # Re-read and validate
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == packet.schema_version


def test_build_packet_with_explicit_synthetic_signals():
    t = m.Transcript(
        events=(m.Event(index=0, role=m.Role.ASSISTANT, text="x"),),
        source_path="inline",
        source_status=m.SourceStatus.COMPLETE,
        parse_stats=m.ParseStats(total_lines=1, parsed_events=1),
    )
    fake_signals = {name: [] for name in d.DETECTOR_NAMES}
    fake_signals["file_edits"] = [
        d.Signal(
            kind="file_edits",
            event_indices=(0,),
            summary="edit a.py",
            detail={"tool": "write", "target_path": "a.py", "op": "edit"},
        )
    ]
    pkt = ep.build_packet(t, signals_by_kind=fake_signals, produced_at="now")
    assert pkt.signal_counts["file_edits"] == 1
    assert pkt.reconciles() is True


def test_build_packet_missing_buckets_filled_with_empty():
    """If caller passes a partial dict, missing detectors default to []."""
    t = m.Transcript(
        events=(),
        source_path="inline",
        source_status=m.SourceStatus.UNVERIFIED,
        parse_stats=m.ParseStats(),
    )
    pkt = ep.build_packet(t, signals_by_kind={"file_edits": []}, produced_at="now")
    for name in d.DETECTOR_NAMES:
        assert pkt.signal_counts[name] == 0
    assert pkt.reconciles() is True
