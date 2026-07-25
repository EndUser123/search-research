"""Tests for wiki_save_gate.py — verifies the gate catches bypasses and passes legitimate saves.

Test scenarios (the same shape as the /close test pattern):
  1. Systemic finding + concept written → pass
  2. Systemic finding + no concept → FAIL (the bypass catch)
  3. Systemic finding + explicit no_findings marker → pass
  4. No systemic findings → n/a (no gate needed)
  5. No artifact → n/a
  6. Systemic finding + sidecar claims "saved" but no concept → FAIL (discrepancy catch)
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent))
import wiki_save_gate as gate


def make_artifact(tmp_dir: Path, content: str, filename: str = "findings.json") -> Path:
    p = tmp_dir / filename
    p.write_text(content, encoding="utf-8")
    return p


def make_sidecar(tmp_dir: Path, status: str, reason: str, skill: str = "test-skill") -> Path:
    p = tmp_dir / gate.SIDECAR_NAME
    p.write_text(
        json.dumps({"status": status, "reason": reason, "skill": skill}),
        encoding="utf-8",
    )
    return p


def run_gate(artifact: Path, skill: str, verbose: bool = True) -> int:
    """Run the gate with patched argv, return exit code."""
    argv = ["gate", "--artifact", str(artifact), "--skill", skill]
    if verbose:
        argv.append("--verbose")
    with patch.object(sys, "argv", argv):
        return gate.main()


def test_no_artifact_returns_na():
    with tempfile.TemporaryDirectory() as tmp:
        code = run_gate(Path(tmp) / "nonexistent.json", "test")
        assert code == 2, f"expected 2 (n/a), got {code}"


def test_no_systemic_findings_returns_na():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        artifact = make_artifact(tmp_path, json.dumps({"findings": [{"severity": "nit"}]}))
        with patch.object(gate, "WIKI_CONCEPTS", tmp_path / "fake"):
            (tmp_path / "fake").mkdir()
            code = run_gate(artifact, "test")
        assert code == 2, f"expected 2 (n/a), got {code}"


def test_systemic_findings_no_concept_no_marker_fails():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        artifact = make_artifact(
            tmp_path,
            json.dumps({"findings": [{"severity": "BLOCK", "class": "architectural"}]}),
        )
        with patch.object(gate, "WIKI_CONCEPTS", tmp_path / "fake"):
            (tmp_path / "fake").mkdir()
            code = run_gate(artifact, "test")
        assert code == 1, f"expected 1 (FAIL — bypass caught), got {code}"


def test_systemic_findings_with_no_findings_marker_passes():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        artifact = make_artifact(
            tmp_path,
            json.dumps({"findings": [{"severity": "BLOCK", "class": "architectural"}]}),
        )
        make_sidecar(tmp_path, "no_findings", "reviewed; finding was session-specific")
        with patch.object(gate, "WIKI_CONCEPTS", tmp_path / "fake"):
            (tmp_path / "fake").mkdir()
            code = run_gate(artifact, "test")
        assert code == 0, f"expected 0 (pass — explicit marker), got {code}"


def test_systemic_findings_with_concept_passes():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        artifact = make_artifact(
            tmp_path,
            json.dumps({"findings": [{"severity": "BLOCK", "class": "architectural"}]}),
        )
        fake_concepts = tmp_path / "fake"
        fake_concepts.mkdir()
        (fake_concepts / "test-finding.md").write_text(
            "# Test Finding\n\nThis was found by test-skill.", encoding="utf-8"
        )
        with patch.object(gate, "WIKI_CONCEPTS", fake_concepts):
            with patch.object(gate, "WIKI_LOG", tmp_path / "fake_log.md"):
                (tmp_path / "fake_log.md").write_text("", encoding="utf-8")
                code = run_gate(artifact, "test-skill")
        assert code == 0, f"expected 0 (pass — concept written), got {code}"


def test_sidecar_claims_saved_but_no_concept_fails():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        artifact = make_artifact(
            tmp_path,
            json.dumps({"findings": [{"severity": "BLOCK", "class": "architectural"}]}),
        )
        make_sidecar(tmp_path, "saved", "claimed but no actual concept")
        with patch.object(gate, "WIKI_CONCEPTS", tmp_path / "fake"):
            (tmp_path / "fake").mkdir()
            code = run_gate(artifact, "test")
        assert code == 1, f"expected 1 (FAIL — discrepancy), got {code}"


def test_has_systemic_findings_detection():
    assert gate.has_systemic_findings("class: architectural")
    assert gate.has_systemic_findings("SYSTEMIC root cause")
    assert gate.has_systemic_findings("PROBLEM_CLASS finding")
    assert gate.has_systemic_findings("severity: BLOCK")
    assert gate.has_systemic_findings("structural fix needed")
    assert not gate.has_systemic_findings("just a nit")
    assert not gate.has_systemic_findings("")
    assert not gate.has_systemic_findings("minor typo")


if __name__ == "__main__":
    import traceback

    tests = [
        test_no_artifact_returns_na,
        test_no_systemic_findings_returns_na,
        test_systemic_findings_no_concept_no_marker_fails,
        test_systemic_findings_with_no_findings_marker_passes,
        test_systemic_findings_with_concept_passes,
        test_sidecar_claims_saved_but_no_concept_fails,
        test_has_systemic_findings_detection,
    ]

    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
