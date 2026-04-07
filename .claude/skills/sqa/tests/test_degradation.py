"""Tests for graceful degradation behavior in the SQA orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))


class TestHardDependency:
    """Tests for Layer 2 → Layer 4 hard dependency enforcement."""

    def test_layer4_skipped_when_layer2_has_high_findings(self, tmp_path, monkeypatch):
        """When Layer 2 (SEMANTIC) produces HIGH/CRITICAL findings, Layer 4 (REQUIREMENTS) is skipped."""
        from findings.models import Finding, Severity, EvidenceTier

        # Mock L2 runner to return HIGH findings
        def mock_run_l2(target):
            return [
                Finding(
                    finding_id="L2-001",
                    severity=Severity.HIGH,
                    layer="L2",
                    title="Test failure",
                    description="Test failed",
                    location="test_foo.py:10",
                    evidence_tier=EvidenceTier.T1,
                    consensus=1,
                    category="testing",
                )
            ]

        # Mock L4 runner
        def mock_run_l4(target):
            return [Finding(
                finding_id="L4-001",
                severity=Severity.LOW,
                layer="L4",
                title="Gap found",
                description="Gap",
                location=None,
                evidence_tier=EvidenceTier.T1,
                consensus=1,
                category="requirements",
            )]

        import orchestrator
        monkeypatch.setattr(orchestrator.layer2_semantic, "run", mock_run_l2)
        monkeypatch.setattr(orchestrator.layer4_requirements, "run", mock_run_l4)

        report = orchestrator.run_sqa(str(tmp_path))

        # L4 should be SKIPPED, not run
        layer_names = [e.layer for e in report.audit_trail]
        assert "L4_REQUIREMENTS" not in layer_names, f"L4 should be skipped when L2 has failures, got audit: {layer_names}"

    def test_layer4_runs_when_layer2_has_no_critical_findings(self, tmp_path, monkeypatch):
        """When Layer 2 (SEMANTIC) has no HIGH/CRITICAL findings, Layer 4 (REQUIREMENTS) runs normally."""
        from findings.models import Finding, Severity, EvidenceTier

        # Mock L2 runner to return only LOW findings
        def mock_run_l2(target):
            return [
                Finding(
                    finding_id="L2-001",
                    severity=Severity.LOW,
                    layer="L2",
                    title="Minor issue",
                    description="Minor",
                    location="test_foo.py:10",
                    evidence_tier=EvidenceTier.T1,
                    consensus=1,
                    category="testing",
                )
            ]

        # Mock L4 runner
        def mock_run_l4(target):
            return [Finding(
                finding_id="L4-001",
                severity=Severity.LOW,
                layer="L4",
                title="Gap found",
                description="Gap",
                location=None,
                evidence_tier=EvidenceTier.T1,
                consensus=1,
                category="requirements",
            )]

        import orchestrator
        monkeypatch.setattr(orchestrator.layer2_semantic, "run", mock_run_l2)
        monkeypatch.setattr(orchestrator.layer4_requirements, "run", mock_run_l4)

        report = orchestrator.run_sqa(str(tmp_path))

        # L4 should run
        layer_names = [e.layer for e in report.audit_trail]
        assert "L4_REQUIREMENTS" in layer_names, f"L4 should run when L2 has no critical failures, got: {layer_names}"


class TestAllowedCommands:
    """Tests for ALLOWED_COMMANDS allowlist enforcement."""

    def test_orchestrator_has_allowed_commands_list(self):
        from orchestrator import ALLOWED_COMMANDS

        assert "ruff" in ALLOWED_COMMANDS
        assert "mypy" in ALLOWED_COMMANDS
        assert "pytest" in ALLOWED_COMMANDS
        assert "aid" in ALLOWED_COMMANDS
        assert "gto" in ALLOWED_COMMANDS
        assert "verify" in ALLOWED_COMMANDS
        assert "hook-audit" in ALLOWED_COMMANDS
        assert "hook-inventory" in ALLOWED_COMMANDS
        assert "adversarial-security" in ALLOWED_COMMANDS
        assert "adversarial-performance" in ALLOWED_COMMANDS
        assert "diagnose" in ALLOWED_COMMANDS

    def test_allowed_commands_blocks_shell_injection(self):
        """Ensure arbitrary commands cannot be injected via the allowlist."""
        from orchestrator import ALLOWED_COMMANDS

        assert "rm" not in ALLOWED_COMMANDS
        assert "curl" not in ALLOWED_COMMANDS
        assert "wget" not in ALLOWED_COMMANDS
        assert "python" not in ALLOWED_COMMANDS


class TestTargetValidation:
    """Tests for target path validation."""

    def test_validate_rejects_nonexistent_path(self):
        from orchestrator import _validate_target

        with pytest.raises(AssertionError):
            _validate_target("/nonexistent/path/xyz")

    def test_validate_rejects_symlink(self, tmp_path):
        import os

        from orchestrator import _validate_target

        real_dir = tmp_path / "real"
        real_dir.mkdir()
        link_dir = tmp_path / "link"
        try:
            os.symlink(str(real_dir), str(link_dir))
            with pytest.raises(AssertionError):
                _validate_target(str(link_dir))
        except (OSError, NotImplementedError):
            # Symlinks may not be supported on Windows in some configs
            pass
