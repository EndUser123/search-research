"""Integration tests for the SQA orchestrator end-to-end pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from orchestrator import run_sqa, save_report

from findings.models import EvidenceTier, Finding, Layer, Severity, SQAReport


class TestEndToEndPipeline:
    """Tests for the full orchestrator.run_sqa() pipeline."""

    def test_run_sqa_returns_sqa_report(self, validated_target):
        """run_sqa() returns an SQAReport with findings and health score."""
        report = run_sqa(validated_target)
        assert isinstance(report, SQAReport)
        assert hasattr(report, "findings")
        assert hasattr(report, "health_score")
        assert isinstance(report.findings, list)

    def test_health_score_is_computed(self, validated_target):
        """Health score is computed when report is generated."""
        report = run_sqa(validated_target)
        assert isinstance(report.health_score, int)
        assert report.health_score <= 100

    def test_report_has_all_required_fields(self, validated_target):
        """Report includes target, findings, health_score, and audit entries."""
        report = run_sqa(validated_target)
        assert report.target == str(validated_target)
        assert isinstance(report.findings, list)
        assert isinstance(report.health_score, int)
        assert hasattr(report, "audit_trail")


class TestSaveReport:
    """Tests for save_report() JSON serialization."""

    def test_save_report_writes_valid_json(self, validated_target, tmp_path):
        """save_report() writes a valid JSON file."""
        report = run_sqa(validated_target)
        output_path = tmp_path / "sqa_report.json"
        save_report(report, output_path)
        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "target" in data
        assert "findings" in data
        assert "health_score" in data

    def test_findings_have_required_fields(self, validated_target, tmp_path):
        """Each finding in saved report has required fields."""
        report = run_sqa(validated_target)
        output_path = tmp_path / "sqa_report.json"
        save_report(report, output_path)
        data = json.loads(output_path.read_text())
        for finding in data["findings"]:
            assert "finding_id" in finding
            assert "severity" in finding
            assert "layer" in finding
            assert "title" in finding


class TestHealthScoreComputation:
    """Integration tests for health score with mixed findings."""

    def test_critical_and_low_mixed_score(self):
        """Report with 1 critical and 1 low produces correct health score."""
        findings = [
            Finding(
                finding_id="C1",
                severity=Severity.CRITICAL,
                layer=Layer.L5_SECURITY,
                title="SQL injection",
                description="Vulnerable",
                evidence_tier=EvidenceTier.T3,
                category="security",
            ),
            Finding(
                finding_id="L1",
                severity=Severity.LOW,
                layer=Layer.L7_OPERATIONAL,
                title="Dead hook",
                description="Hook unused",
                evidence_tier=EvidenceTier.T3,
                category="operational",
            ),
        ]
        report = SQAReport(findings=findings, target="/test")
        report.health_score = report.compute_health_score()
        # 100 - 20 (1 CRITICAL) - 2 (1 LOW) = 78
        assert report.health_score == 78

    def test_empty_findings_produces_healthy_score(self):
        """Empty findings list produces health score of 100."""
        report = SQAReport(findings=[], target="/test")
        report.health_score = report.compute_health_score()
        assert report.health_score == 100
