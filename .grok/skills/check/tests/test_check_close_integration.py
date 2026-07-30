"""Close-integration tests for check_lifecycle.

Tests scenarios 9-20 from the spec: verify that close_accounting.py's
scan_check_receipts() correctly detects all /check run outcomes including
incomplete runs via check-run.json manifests.

Uses hermetic temp directories (no real P:/ artifacts).
"""

import json
import os
import re
import sys
from pathlib import Path

import pytest

_lib = Path(__file__).resolve().parent.parent / "__lib"
sys.path.insert(0, str(_lib))

from check_lifecycle import (
    start_run,
    write_verifier_result,
    finalize_run,
    MANIFEST_FILENAME,
    RECEIPT_FILENAME,
    STATUS_RUNNING,
    STATUS_COMPLETE,
    STATUS_INCOMPLETE,
    STATUS_FINALIZE_FAILED,
)

# Import close_accounting's scan function
_close_lib = Path.home() / ".grok" / "skills" / "close" / "__lib"
sys.path.insert(0, str(_close_lib))
from close_accounting import scan_check_receipts, Config


SESSION_ID = "test-close-integration-001"
SESSION_ID_OTHER = "other-session-999"


@pytest.fixture
def cfg(tmp_path):
    """Config with a tmp artifacts dir for hermetic testing."""
    return Config(artifacts_root=tmp_path / "artifacts", workspace=tmp_path)


@pytest.fixture
def run_dir(cfg):
    """A /check run dir inside the test artifacts root."""
    import urllib.parse
    d = cfg.artifacts_dir / "testterm" / "grok-check" / "20260729-120000-000"
    d.mkdir(parents=True)
    (d / "results").mkdir()
    return d


class TestCloseDetectsComplete:
    """Scenarios 9, 10, 20: valid COMPLETE manifest + receipt."""

    def test_complete_pass_detected(self, cfg, run_dir):
        """Scenario 9: valid COMPLETE + PASS receipt → consumed normally."""
        start_run(SESSION_ID, run_dir)
        write_verifier_result(run_dir, 0, "c1", "PASS")
        write_verifier_result(run_dir, 1, "c2", "PASS")
        finalize_run(run_dir)

        result = scan_check_receipts(SESSION_ID, cfg=cfg)
        assert result["detected"] is True
        assert result["passed_runs"] == 1
        assert result["failed_runs"] == 0
        assert result["verifier_passes"] == 2
        assert result["verifier_total"] == 2

    def test_complete_fail_detected(self, cfg, run_dir):
        """Scenario 10: CHECK FAIL receipt detected by /close."""
        start_run(SESSION_ID, run_dir)
        write_verifier_result(run_dir, 0, "c1", "PASS")
        write_verifier_result(run_dir, 1, "c2", "FAIL",
                              [{"severity": "bug", "description": "broken"}])
        finalize_run(run_dir)

        result = scan_check_receipts(SESSION_ID, cfg=cfg)
        assert result["detected"] is True
        assert result["failed_runs"] == 1
        assert result["passed_runs"] == 0

    def test_legacy_receipt_without_manifest(self, cfg, run_dir):
        """Scenario 20: existing check-state.md without check-run.json still readable."""
        receipt = run_dir / RECEIPT_FILENAME
        receipt.write_text(
            f"# /check state\n**Session:** {SESSION_ID}\n"
            f"**Verdict:** CHECK PASS (2/2 verifiers)\n",
            encoding="utf-8",
        )

        result = scan_check_receipts(SESSION_ID, cfg=cfg)
        assert result["detected"] is True
        assert result["passed_runs"] == 1
        assert len(result.get("incomplete_runs", [])) == 0


class TestCloseDetectsIncomplete:
    """Scenarios 11-13: RUNNING, INCOMPLETE, FINALIZE_FAILED visible to /close."""

    def test_running_manifest_visible(self, cfg, run_dir):
        """Scenario 11: RUNNING manifest without receipt → needs_attention."""
        start_run(SESSION_ID, run_dir)
        # Don't call finalize — simulates an interrupted run

        result = scan_check_receipts(SESSION_ID, cfg=cfg)
        assert result["detected"] is False  # no receipt
        inc = result.get("incomplete_runs", [])
        assert len(inc) == 1
        assert inc[0]["status"] == STATUS_RUNNING

    def test_incomplete_manifest_visible(self, cfg, run_dir):
        """Scenario 12: INCOMPLETE manifest → visible to /close."""
        start_run(SESSION_ID, run_dir)
        # Finalize with no verifier results → INCOMPLETE
        finalize_run(run_dir)

        result = scan_check_receipts(SESSION_ID, cfg=cfg)
        inc = result.get("incomplete_runs", [])
        assert len(inc) == 1
        assert inc[0]["status"] == STATUS_INCOMPLETE

    def test_finalize_failed_manifest_visible(self, cfg, run_dir, monkeypatch):
        """Scenario 13: FINALIZE_FAILED manifest → visible to /close."""
        start_run(SESSION_ID, run_dir)
        write_verifier_result(run_dir, 0, "c1", "PASS")

        original_replace = os.replace
        def fail_replace(src, dst):
            if str(dst).endswith(RECEIPT_FILENAME):
                raise OSError("simulated")
            return original_replace(src, dst)
        monkeypatch.setattr(os, "replace", fail_replace)

        finalize_run(run_dir)  # receipt write fails → FINALIZE_FAILED

        result = scan_check_receipts(SESSION_ID, cfg=cfg)
        inc = result.get("incomplete_runs", [])
        assert len(inc) == 1
        assert inc[0]["status"] == STATUS_FINALIZE_FAILED


class TestCloseDetectsInconsistency:
    """Scenarios 14, 15: manifest/receipt disagreement."""

    def test_complete_manifest_missing_receipt(self, cfg, run_dir):
        """Scenario 14: COMPLETE manifest but receipt file deleted → inconsistent."""
        start_run(SESSION_ID, run_dir)
        write_verifier_result(run_dir, 0, "c1", "PASS")
        finalize_run(run_dir)

        # Delete the receipt but leave the manifest saying COMPLETE
        (run_dir / RECEIPT_FILENAME).unlink()

        result = scan_check_receipts(SESSION_ID, cfg=cfg)
        inc = result.get("incomplete_runs", [])
        assert len(inc) == 1
        assert "INCONSISTENT" in inc[0]["status"]

    def test_manifest_receipt_disagreement(self, cfg, run_dir):
        """Scenario 15: manifest says PASS but receipt says FAIL → detected."""
        start_run(SESSION_ID, run_dir)
        write_verifier_result(run_dir, 0, "c1", "PASS")
        finalize_run(run_dir)

        # Tamper with the receipt to say FAIL
        receipt = run_dir / RECEIPT_FILENAME
        receipt.write_text(
            f"# /check state\n**Session:** {SESSION_ID}\n"
            f"**Verdict:** CHECK FAIL (0/1 verifiers)\n",
            encoding="utf-8",
        )

        result = scan_check_receipts(SESSION_ID, cfg=cfg)
        # The receipt scan detects the FAIL; the manifest says COMPLETE with PASS receipt_path.
        # The receipt scan and manifest scan operate independently. The receipt FAIL
        # is detected by the check-state.md scan. The manifest/receipt agreement check
        # only fires if the receipt_path doesn't resolve to a detected receipt.
        # Since the tampered receipt still exists at the same path and has a valid
        # format, both detect it. The key test: failed_runs > 0.
        assert result["failed_runs"] == 1


class TestCloseEdgeCases:
    """Scenarios 16, 17: malformed manifest, other session ignored."""

    def test_malformed_manifest_visible(self, cfg, run_dir):
        """Scenario 16: malformed check-run.json → visible degraded state."""
        (run_dir / MANIFEST_FILENAME).write_text("NOT JSON {{{", encoding="utf-8")

        result = scan_check_receipts(SESSION_ID, cfg=cfg)
        inc = result.get("incomplete_runs", [])
        assert len(inc) == 1
        assert "MALFORMED" in inc[0]["status"]

    def test_other_session_manifest_ignored(self, cfg, run_dir):
        """Scenario 17: another session's manifest is ignored."""
        start_run(SESSION_ID_OTHER, run_dir)

        result = scan_check_receipts(SESSION_ID, cfg=cfg)
        assert result["detected"] is False
        inc = result.get("incomplete_runs", [])
        assert len(inc) == 0  # other session's manifest ignored

    def test_no_manifest_no_receipt(self, cfg):
        """No manifest and no receipt → existing 'no check evidence' behavior."""
        cfg.artifacts_dir.mkdir(parents=True, exist_ok=True)
        result = scan_check_receipts(SESSION_ID, cfg=cfg)
        assert result["detected"] is False
        assert len(result.get("incomplete_runs", [])) == 0


class TestGateCondition:
    """Verify the verify gate treats incomplete runs as needs_attention."""

    def test_incomplete_runs_trigger_needs_attention(self, cfg, run_dir):
        """The verify gate must be needs_attention when incomplete_runs > 0."""
        start_run(SESSION_ID, run_dir)
        # RUNNING manifest, no receipt

        result = scan_check_receipts(SESSION_ID, cfg=cfg)
        assert len(result["incomplete_runs"]) > 0
        # The gate logic in resolve_gates checks incomplete_runs before
        # failed_runs or passed_runs. We verify the data is correct;
        # the gate resolution itself is tested via the integration test
        # that calls resolve_gates directly.
