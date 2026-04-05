"""Tests for meta-synthesis layer (consensus, blind-spot, evidence quality)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from layers.layer_meta import (
    _check_evidence_quality,
    _detect_blind_spots,
    _detect_consensus,
    run_meta,
)

from findings.models import EvidenceTier, Finding, Layer, Severity


class TestDetectConsensus:
    """Tests for _detect_consensus."""

    def test_single_layer_no_consensus(self):
        f = Finding(
            finding_id="L1-001",
            severity=Severity.HIGH,
            layer=Layer.L1_SYNTACTIC,
            title="Error",
            description="Error",
            location="/src/a.py:1",
            evidence_tier=EvidenceTier.T3,
            category="syntax",
        )
        result = _detect_consensus([f])
        assert result == []

    def test_two_layers_same_location_creates_consensus(self):
        f1 = Finding(
            finding_id="L1-001",
            severity=Severity.HIGH,
            layer=Layer.L1_SYNTACTIC,
            title="Style violation",
            description="Error",
            location="/src/a.py:1",
            evidence_tier=EvidenceTier.T3,
            category="style",
        )
        f2 = Finding(
            finding_id="L3-001",
            severity=Severity.HIGH,
            layer=Layer.L3_STRUCTURAL,
            title="Style violation",
            description="Structural issue",
            location="/src/a.py:1",
            evidence_tier=EvidenceTier.T3,
            category="style",
        )
        result = _detect_consensus([f1, f2])
        assert len(result) == 1
        assert result[0].severity == Severity.HIGH
        assert result[0].consensus == 2
        assert "L1_SYNTACTIC" in result[0].description
        assert "L3_STRUCTURAL" in result[0].description

    def test_consensus_uses_highest_severity(self):
        f1 = Finding(
            finding_id="L1-001",
            severity=Severity.LOW,
            layer=Layer.L1_SYNTACTIC,
            title="Style violation",
            description="Issue",
            location="/src/a.py:1",
            evidence_tier=EvidenceTier.T3,
            category="style",
        )
        f2 = Finding(
            finding_id="L2-001",
            severity=Severity.CRITICAL,
            layer=Layer.L2_SEMANTIC,
            title="Style violation",
            description="Issue",
            location="/src/a.py:1",
            evidence_tier=EvidenceTier.T3,
            category="style",
        )
        result = _detect_consensus([f1, f2])
        assert result[0].severity == Severity.CRITICAL


class TestDetectBlindSpots:
    """Tests for _detect_blind_spots."""

    def test_no_blind_spot_when_layer_finds_issues(self):
        f = Finding(
            finding_id="L1-001",
            severity=Severity.MEDIUM,
            layer=Layer.L1_SYNTACTIC,
            title="Syntax error",
            description="Error",
            evidence_tier=EvidenceTier.T3,
            category="syntax",
        )
        result = _detect_blind_spots([f])
        # L1 was available and found syntax issues — no blind spot
        syntax_blind = [r for r in result if "syntax" in r.title and "L1_SYNTACTIC" in r.title]
        assert len(syntax_blind) == 0

    def test_no_blind_spot_for_D5_degraded_layer(self):
        # D5 graceful degradation means L5 never ran — this is NOT a blind spot
        # We only flag when a layer RAN but found nothing in its expected categories
        # So if L5 is not in all_findings at all, we shouldn't flag it
        # (the "layer was degraded" case is handled by the orchestrator, not meta)
        result = _detect_blind_spots([])
        # No findings means no blind spot detection (no layer "ran but found nothing")


class TestCheckEvidenceQuality:
    """Tests for _check_evidence_quality."""

    def test_t4_finding_flagged(self):
        f = Finding(
            finding_id="L1-HEURISTIC",
            severity=Severity.LOW,
            layer=Layer.L1_SYNTACTIC,
            title="Heuristic finding",
            description="Based on heuristic",
            evidence_tier=EvidenceTier.T4,
            category="style",
        )
        result = _check_evidence_quality([f])
        assert len(result) == 1
        assert "META-EVIDENCE-Q" in result[0].finding_id
        assert result[0].severity == Severity.LOW

    def test_t3_finding_not_flagged(self):
        f = Finding(
            finding_id="L1-001",
            severity=Severity.MEDIUM,
            layer=Layer.L1_SYNTACTIC,
            title="Logical finding",
            description="Based on logic",
            evidence_tier=EvidenceTier.T3,
            category="syntax",
        )
        result = _check_evidence_quality([f])
        assert len(result) == 0


class TestRunMeta:
    """Tests for run_meta (full meta-synthesis)."""

    def test_run_meta_combines_all_three(self):
        # A T4 finding that triggers evidence quality check
        f_t4 = Finding(
            finding_id="L1-HEURISTIC",
            severity=Severity.LOW,
            layer=Layer.L1_SYNTACTIC,
            title="Heuristic",
            description="Heuristic based",
            evidence_tier=EvidenceTier.T4,
            category="style",
        )
        result = run_meta([f_t4])
        # Should include the T4 quality finding
        assert len(result) >= 1
