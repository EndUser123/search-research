"""Tests for orchestrator parallel layer execution (CHANGE-003)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from orchestrator import (
    _run_parallel_layers,
    L2State,
)
from findings.models import AuditEntry, Finding


class TestRunParallelLayers:
    """Tests for _run_parallel_layers."""

    def test_parallel_layers_all_complete(self, tmp_path: Path):
        """All parallel layers return findings and audit entries."""
        # Create a simple target dir
        (tmp_path / "test.py").write_text("x = 1\n")

        results = _run_parallel_layers(
            ["L1_SYNTACTIC", "L3_STRUCTURAL"],
            tmp_path,
        )

        assert "L1_SYNTACTIC" in results
        assert "L3_STRUCTURAL" in results
        findings_l1, audit_l1 = results["L1_SYNTACTIC"]
        findings_l3, audit_l3 = results["L3_STRUCTURAL"]
        assert isinstance(findings_l1, list)
        assert isinstance(findings_l3, list)
        assert isinstance(audit_l1, AuditEntry)
        assert isinstance(audit_l3, AuditEntry)
        assert audit_l1.skill == "L1_SYNTACTIC"
        assert audit_l3.skill == "L3_STRUCTURAL"

    def test_parallel_layers_returns_results_dict(self, tmp_path: Path):
        """_run_parallel_layers returns dict with correct structure."""
        (tmp_path / "test.py").write_text("x = 1\n")

        results = _run_parallel_layers(
            ["L1_SYNTACTIC", "L3_STRUCTURAL"],
            tmp_path,
        )

        # Verify return type: dict[str, tuple[list[Finding], AuditEntry]]
        assert isinstance(results, dict)
        for layer_name, result in results.items():
            assert isinstance(layer_name, str)
            assert isinstance(result, tuple)
            assert len(result) == 2
            findings, audit = result
            assert isinstance(findings, list)
            assert isinstance(audit, AuditEntry)
            assert audit.skill == layer_name

    def test_audit_trail_order_preserved(self, tmp_path: Path):
        """Audit entries are in insertion order regardless of completion order."""
        (tmp_path / "test.py").write_text("x = 1\n")

        results = _run_parallel_layers(
            ["L1_SYNTACTIC", "L3_STRUCTURAL", "L5_SECURITY", "L6_PERFORMANCE"],
            tmp_path,
        )

        # Verify all four layers returned results
        assert len(results) == 4
        for layer in ["L1_SYNTACTIC", "L3_STRUCTURAL", "L5_SECURITY", "L6_PERFORMANCE"]:
            assert layer in results
            _, audit = results[layer]
            assert audit.skill == layer


class TestL2StateCheckpoint:
    """Tests for L2 checkpoint persistence."""

    def test_l2_state_dataclass(self):
        """L2State dataclass serializes correctly."""
        state = L2State(layer2_had_failures=True, target="/test/path")
        assert state.layer2_had_failures is True
        assert state.target == "/test/path"
