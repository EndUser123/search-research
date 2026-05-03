"""Tests for verification/coverage.py — deterministic coverage checks."""

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from verification.coverage import CoverageReport, assess_coverage


@dataclass
class _FakeClaim:
    id: str
    text: str
    targets: list[str]
    type: str = "ABSENCE"
    confidence: float = 0.9
    risk_domain: str = "SYSTEM"
    has_hedge: bool = False
    decomposition_eligible: bool = False


@dataclass
class _FakeVerdict:
    claim_id: str
    status: object
    supporting_evidence: list[str]
    refuting_evidence: list[str]
    confidence: float = 0.9


class _VS:
    SILENT = "SILENT"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"


class TestPeerCoverage:
    def test_no_peer_claims(self):
        verdict = _FakeVerdict("1", _VS.SILENT, [], [])
        claim = _FakeClaim("1", "X works", ["X"])
        report = assess_coverage(verdict, claim, [verdict], [])
        peer_dim = [d for d in report.dimensions if d.name == "peer_coverage"][0]
        assert peer_dim.score == 0.0

    def test_all_peers_supported(self):
        v1 = _FakeVerdict("1", _VS.SILENT, [], [])
        v2 = _FakeVerdict("2", _VS.SUPPORTED, ["ev"], [])
        v3 = _FakeVerdict("3", _VS.SUPPORTED, ["ev"], [])
        claim = _FakeClaim("1", "X works", ["X"])
        report = assess_coverage(v1, claim, [v1, v2, v3], [])
        peer_dim = [d for d in report.dimensions if d.name == "peer_coverage"][0]
        assert peer_dim.score == 1.0

    def test_half_peers_supported(self):
        v1 = _FakeVerdict("1", _VS.SILENT, [], [])
        v2 = _FakeVerdict("2", _VS.SUPPORTED, ["ev"], [])
        v3 = _FakeVerdict("3", _VS.SILENT, [], [])
        claim = _FakeClaim("1", "X works", ["X"])
        report = assess_coverage(v1, claim, [v1, v2, v3], [])
        peer_dim = [d for d in report.dimensions if d.name == "peer_coverage"][0]
        assert peer_dim.score == 0.5


class TestDirectVsIndirect:
    def test_direct_match(self):
        verdict = _FakeVerdict("1", _VS.SILENT, [], [])
        claim = _FakeClaim("1", "file.py works", ["file.py"])
        events = [{"name": "Read", "output": "file.py contents here", "command": ""}]
        report = assess_coverage(verdict, claim, [verdict], events)
        direct_dim = [d for d in report.dimensions if d.name == "direct_vs_indirect"][0]
        assert direct_dim.score == 0.8

    def test_no_events(self):
        verdict = _FakeVerdict("1", _VS.SILENT, [], [])
        claim = _FakeClaim("1", "X works", ["X"])
        report = assess_coverage(verdict, claim, [verdict], [])
        direct_dim = [d for d in report.dimensions if d.name == "direct_vs_indirect"][0]
        assert direct_dim.score == 0.0


class TestContradiction:
    def test_refuted_sibling(self):
        v1 = _FakeVerdict("1", _VS.SILENT, [], [])
        v2 = _FakeVerdict("2", _VS.REFUTED, [], ["refute"])
        claim = _FakeClaim("1", "X works", ["X"])
        report = assess_coverage(v1, claim, [v1, v2], [])
        assert report.recommendation == "contradicted"

    def test_no_contradiction(self):
        v1 = _FakeVerdict("1", _VS.SILENT, [], [])
        v2 = _FakeVerdict("2", _VS.SUPPORTED, ["ev"], [])
        claim = _FakeClaim("1", "X works", ["X"])
        report = assess_coverage(v1, claim, [v1, v2], [])
        assert report.recommendation != "contradicted"


class TestRecommendationThresholds:
    def test_sufficient(self):
        # All peers supported + direct evidence = high score
        v1 = _FakeVerdict("1", _VS.SILENT, [], [])
        v2 = _FakeVerdict("2", _VS.SUPPORTED, ["ev"], [])
        claim = _FakeClaim("1", "file.py works", ["file.py"])
        events = [{"name": "Read", "output": "file.py contents", "command": ""}]
        report = assess_coverage(v1, claim, [v1, v2], events)
        assert report.recommendation == "sufficient"

    def test_insufficient(self):
        v1 = _FakeVerdict("1", _VS.SILENT, [], [])
        claim = _FakeClaim("1", "X works", ["X"])
        report = assess_coverage(v1, claim, [v1], [])
        assert report.recommendation == "insufficient"


class TestCoverageReportImmutable:
    def test_frozen(self):
        report = CoverageReport(
            verdict_id="1",
            overall_score=0.5,
            dimensions=(),
            recommendation="weak",
        )
        try:
            report.overall_score = 0.9
            assert False, "Should raise"
        except AttributeError:
            pass
