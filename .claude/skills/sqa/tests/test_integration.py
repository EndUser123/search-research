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
    """Tests for save_report() JSON serialization with terminal isolation."""

    def test_save_report_writes_valid_json(self, validated_target, monkeypatch):
        """save_report() writes a valid JSON file to terminal-isolated path."""
        import hashlib
        import shutil
        from pathlib import Path

        # Isolate to a test terminal id
        monkeypatch.setenv("TERMINAL_ID", "test_sqa_terminal")
        report = run_sqa(validated_target)

        # The path argument is ignored — report goes to terminal-isolated dir
        save_report(report, Path("/unused/path/that/is/ignored.json"))

        # Compute expected terminal path
        tid = "test_sqa_terminal"
        target_hash = hashlib.sha256(report.target.encode()).hexdigest()[:16]
        report_dir = Path.home() / ".claude" / "sqa_reports" / f"terminal_{tid}"
        terminal_path = report_dir / f"{target_hash}.json"

        try:
            assert terminal_path.exists(), f"Report not found at {terminal_path}"
            data = json.loads(terminal_path.read_text())
            assert "target" in data
            assert "findings" in data
            assert "health_score" in data
            assert "timestamp" in data  # TASK-007: timestamp field present
            assert data["timestamp"]  # non-empty
            # Verify ISO-8601 format
            from datetime import datetime

            datetime.fromisoformat(data["timestamp"])
        finally:
            # Clean up
            shutil.rmtree(report_dir, ignore_errors=True)

    def test_findings_have_required_fields_and_evidence(self, validated_target, monkeypatch):
        """Each finding in saved report has required fields; evidence field is preserved."""
        import hashlib
        import shutil
        from pathlib import Path

        monkeypatch.setenv("TERMINAL_ID", "test_sqa_terminal2")
        report = run_sqa(validated_target)
        save_report(report, Path("/ignored.json"))

        tid = "test_sqa_terminal2"
        target_hash = hashlib.sha256(report.target.encode()).hexdigest()[:16]
        report_dir = Path.home() / ".claude" / "sqa_reports" / f"terminal_{tid}"
        terminal_path = report_dir / f"{target_hash}.json"

        try:
            data = json.loads(terminal_path.read_text())
            for finding in data["findings"]:
                assert "finding_id" in finding
                assert "severity" in finding
                assert "layer" in finding
                assert "title" in finding
                # evidence field is serialized (TASK-006)
                assert "evidence" in finding
                assert isinstance(finding["evidence"], list)
        finally:
            shutil.rmtree(report_dir, ignore_errors=True)


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
        # 100 - 20*0.5 (1 CRITICAL T3) - 2*0.5 (1 LOW T3) = 89
        assert report.health_score == 89

    def test_empty_findings_produces_healthy_score(self):
        """Empty findings list produces health score of 100."""
        report = SQAReport(findings=[], target="/test")
        report.health_score = report.compute_health_score()
        assert report.health_score == 100
