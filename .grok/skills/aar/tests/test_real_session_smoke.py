"""Read-only smoke test against a real Grok session transcript.

Evidence classification: LIVE_BEHAVIOR_TESTED (read-only)

This test does NOT run on a fixture — it runs the preprocessor against the
real 1197-line session transcript referenced in the task. It confirms the
parser handles production-scale Grok JSONL without crashing and that the
detectors produce a sane signal distribution.

Skipped automatically when the real session is not present (e.g. on a
different machine or after the session is archived), so the suite remains
portable.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from detectors import run_all_detectors
from evidence_packet import build_evidence_packet
from transcript_parser import parse_transcript

# Real session transcript path (the one the task asked us to replay against).
# Encoded path component ``P%3A%5C`` is the URL-encoded form of ``P:\``.
REAL_TRANSCRIPT = Path(
    r"C:\Users\brsth\.grok\sessions\P%3A%5C"
    r"\019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe\chat_history.jsonl"
)


pytestmark = pytest.mark.skipif(
    not REAL_TRANSCRIPT.exists(),
    reason=f"real session transcript not present at {REAL_TRANSCRIPT}",
)


def test_real_session_parses_without_error():
    t = parse_transcript(REAL_TRANSCRIPT)
    assert len(t.events) > 100  # real session is ~1197 events
    assert t.parse_stats.reconciles() is True
    assert t.parse_stats.has_timestamps is False  # Grok JSONL has no timestamps


def test_real_session_source_status_is_partial():
    """The real session has a compaction/ dir → SOURCE_PARTIAL."""
    t = parse_transcript(REAL_TRANSCRIPT)
    assert t.source_status.value == "SOURCE_PARTIAL"


def test_real_session_session_id_derived_from_path():
    """Session id is derived from the transcript path, not invented."""
    t = parse_transcript(REAL_TRANSCRIPT)
    assert t.session_id == "019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe"


def test_real_session_detectors_produce_sane_signal_count():
    """Detector precision on real data.

    Failure-shaped detectors stay bounded (<200). Opportunity-candidate
    detectors (Section 19) are additive low-severity candidates the LLM
    interprets; the total may exceed the failure-only threshold but stays
    well below wild over-firing.
    """
    t = parse_transcript(REAL_TRANSCRIPT)
    sigs = run_all_detectors(t.events)
    assert len(sigs) < 600, f"detector over-firing: {len(sigs)} signals (expected <600)"
    assert len(sigs) > 0


def test_real_session_packet_builds_with_provenance():
    t = parse_transcript(REAL_TRANSCRIPT)
    sigs = run_all_detectors(t.events)
    pkt = build_evidence_packet(
        t, sigs, env={"CLAUDE_TERMINAL_ID": "smoketest"}, produced_at="2026-01-01T00:00:00Z"
    )
    assert pkt.source.session_id == "019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe"
    assert pkt.source.terminal_id == "smoketest"
    assert pkt.source.source_status == "SOURCE_PARTIAL"
    assert pkt.signal_total == len(sigs)
    assert pkt.integrity is not None
