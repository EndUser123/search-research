"""Tests for write_check_state.py — the mechanized /check receipt writer.

Validates:
1. PASS and FAIL verdicts produce check-state.md
2. Output matches the close_accounting.py consumer regexes
3. Verifier counts are computed correctly
4. Atomic write (os.replace) works
5. Contract violations (missing session_id/verdict) fail loud
6. close_accounting.scan_check_receipts can actually parse the output
"""

import json
import os
import re
import sys
from pathlib import Path

# Add __lib to path for import
_lib = Path(__file__).resolve().parent.parent / "__lib"
sys.path.insert(0, str(_lib))

import pytest
from write_check_state import render_check_state, write_check_state

# The EXACT regexes from close_accounting.py:557-560 — if these match,
# the consumer can detect the receipt.
SESSION_RE = re.compile(r"^\*\*Session:\*\*\s*([^\s]+)", re.I | re.M)
VERDICT_RE = re.compile(
    r"^\*\*Verdict:\*\*\s*CHECK\s+(PASS|FAIL)\b(?:\s*\((\d+)\s*/\s*(\d+)[^)]*\))?",
    re.I | re.M,
)


@pytest.fixture
def sample_verifiers_pass():
    return [
        {"concern": "harvest store", "verdict": "PASS", "finding": "all events fold correctly"},
        {"concern": "close scanner", "verdict": "PASS", "finding": "14 gates resolved"},
    ]


@pytest.fixture
def sample_verifiers_mixed():
    return [
        {"concern": "harvest store", "verdict": "PASS", "finding": "clean"},
        {"concern": "close scanner", "verdict": "FAIL", "finding": "gate regression failed"},
        {"concern": "wiki lifecycle", "verdict": "PASS", "finding": "index rebuilt"},
    ]


@pytest.fixture
def sample_issues():
    return [
        {"severity": "bug", "description": "race condition in claim file (store.py:120)"},
        {"severity": "gap", "description": "no test for concurrent ADD events"},
    ]


class TestRenderFormat:
    """Verify the rendered output matches the consumer contract."""

    def test_pass_renders_session_line(self, sample_verifiers_pass):
        output = render_check_state(
            "019f9aff-a619-70c2-8836-0bb6ae462827",
            "PASS",
            sample_verifiers_pass,
        )
        m = SESSION_RE.search(output)
        assert m is not None
        assert m.group(1) == "019f9aff-a619-70c2-8836-0bb6ae462827"

    def test_pass_renders_verdict_line(self, sample_verifiers_pass):
        output = render_check_state(
            "test-session", "PASS", sample_verifiers_pass
        )
        m = VERDICT_RE.search(output)
        assert m is not None
        assert m.group(1) == "PASS"
        assert int(m.group(2)) == 2  # passed
        assert int(m.group(3)) == 2  # total

    def test_fail_renders_correct_counts(self, sample_verifiers_mixed):
        output = render_check_state(
            "test-session", "FAIL", sample_verifiers_mixed
        )
        m = VERDICT_RE.search(output)
        assert m is not None
        assert m.group(1) == "FAIL"
        assert int(m.group(2)) == 2  # 2 of 3 passed
        assert int(m.group(3)) == 3  # 3 total

    def test_verdict_case_insensitive_input(self, sample_verifiers_pass):
        """Input verdict 'pass' should render as 'PASS' in output."""
        output = render_check_state("s1", "pass", sample_verifiers_pass)
        m = VERDICT_RE.search(output)
        assert m is not None
        assert m.group(1) == "PASS"

    def test_empty_verifiers_renders_zero_counts(self):
        output = render_check_state("s1", "PASS", [])
        m = VERDICT_RE.search(output)
        assert m is not None
        assert int(m.group(2)) == 0
        assert int(m.group(3)) == 0

    def test_issues_section_populated(self, sample_verifiers_pass, sample_issues):
        output = render_check_state(
            "s1", "FAIL", sample_verifiers_pass, issues=sample_issues
        )
        assert "[bug]" in output
        assert "[gap]" in output
        assert "race condition" in output

    def test_no_issues_renders_none(self, sample_verifiers_pass):
        output = render_check_state("s1", "PASS", sample_verifiers_pass)
        assert "## Issues found during check" in output
        assert "none" in output


class TestWriteCheckState:
    """Verify the file write + contract enforcement."""

    def test_writes_file_to_run_dir(self, tmp_path):
        data = {
            "session_id": "test-sid-123",
            "run_dir": str(tmp_path),
            "verdict": "PASS",
            "verifiers": [{"concern": "c1", "verdict": "PASS", "finding": "ok"}],
        }
        target = write_check_state(data)
        assert target == tmp_path / "check-state.md"
        assert target.exists()
        content = target.read_text(encoding="utf-8")
        assert "**Session:** test-sid-123" in content
        assert "CHECK PASS" in content

    def test_fail_verdict_writes_receipt(self, tmp_path, sample_verifiers_mixed):
        """Critical: FAIL verdicts must also produce a receipt."""
        data = {
            "session_id": "fail-session",
            "run_dir": str(tmp_path),
            "verdict": "FAIL",
            "verifiers": sample_verifiers_mixed,
            "issues": [{"severity": "bug", "description": "gate failed"}],
        }
        target = write_check_state(data)
        content = target.read_text(encoding="utf-8")
        m = VERDICT_RE.search(content)
        assert m is not None
        assert m.group(1) == "FAIL"

    def test_missing_session_id_raises(self, tmp_path):
        data = {"run_dir": str(tmp_path), "verdict": "PASS", "verifiers": []}
        with pytest.raises(ValueError, match="session_id"):
            write_check_state(data)

    def test_invalid_verdict_raises(self, tmp_path):
        data = {
            "session_id": "s1",
            "run_dir": str(tmp_path),
            "verdict": "MAYBE",
            "verifiers": [],
        }
        with pytest.raises(ValueError, match="PASS or FAIL"):
            write_check_state(data)

    def test_nonexistent_run_dir_raises(self):
        data = {
            "session_id": "s1",
            "run_dir": "/nonexistent/path/that/does/not/exist",
            "verdict": "PASS",
            "verifiers": [],
        }
        with pytest.raises(ValueError, match="run_dir"):
            write_check_state(data)

    def test_atomic_write_no_tmp_leftover(self, tmp_path):
        data = {
            "session_id": "s1",
            "run_dir": str(tmp_path),
            "verdict": "PASS",
            "verifiers": [],
        }
        write_check_state(data)
        # No .tmp files should remain after os.replace
        leftovers = list(tmp_path.glob("check-state.tmp.*"))
        assert len(leftovers) == 0

    def test_overwrite_existing(self, tmp_path):
        """Re-running /check on the same run_dir should replace, not error."""
        data = {
            "session_id": "s1",
            "run_dir": str(tmp_path),
            "verdict": "FAIL",
            "verifiers": [{"concern": "c1", "verdict": "FAIL", "finding": "broke"}],
        }
        # First write
        write_check_state(data)
        # Second write (different verdict)
        data["verdict"] = "PASS"
        data["verifiers"][0]["verdict"] = "PASS"
        target = write_check_state(data)
        content = target.read_text(encoding="utf-8")
        assert "CHECK PASS" in content


class TestCloseAccountingCompat:
    """Verify the output is parseable by the actual close_accounting logic.

    This simulates scan_check_receipts: rglob for check-state.md, parse
    with the real regexes, filter by session_id, extract verdict + counts.
    """

    def test_full_scan_simulation_pass(self, tmp_path):
        """Simulate close scanning for a PASS receipt."""
        data = {
            "session_id": "019fa276-abcd-1234-5678-000000000001",
            "run_dir": str(tmp_path / "grok-check" / "20260729-120000-000"),
            "verdict": "PASS",
            "verifiers": [
                {"concern": "harvest", "verdict": "PASS", "finding": "clean"},
                {"concern": "close", "verdict": "PASS", "finding": "gates ok"},
            ],
        }
        Path(data["run_dir"]).mkdir(parents=True)
        target = write_check_state(data)

        # Simulate close_accounting.scan_check_receipts
        text = target.read_text(encoding="utf-8")
        session_match = SESSION_RE.search(text)
        verdict_match = VERDICT_RE.search(text)

        assert session_match is not None
        assert session_match.group(1) == data["session_id"]
        assert verdict_match is not None
        assert verdict_match.group(1) == "PASS"
        assert int(verdict_match.group(2)) == 2  # passed
        assert int(verdict_match.group(3)) == 2  # total

    def test_full_scan_simulation_fail(self, tmp_path):
        """Simulate close scanning for a FAIL receipt — the critical gap case."""
        data = {
            "session_id": "019fa276-abcd-1234-5678-000000000002",
            "run_dir": str(tmp_path / "grok-check" / "20260729-130000-000"),
            "verdict": "FAIL",
            "verifiers": [
                {"concern": "harvest", "verdict": "PASS", "finding": "clean"},
                {"concern": "close", "verdict": "FAIL", "finding": "gate regression"},
                {"concern": "wiki", "verdict": "FAIL", "finding": "index stale"},
            ],
            "issues": [
                {"severity": "bug", "description": "retrospective gate bypassed"},
            ],
        }
        Path(data["run_dir"]).mkdir(parents=True)
        target = write_check_state(data)

        text = target.read_text(encoding="utf-8")
        session_match = SESSION_RE.search(text)
        verdict_match = VERDICT_RE.search(text)

        assert session_match is not None
        assert session_match.group(1) == data["session_id"]
        assert verdict_match is not None
        assert verdict_match.group(1) == "FAIL"
        assert int(verdict_match.group(2)) == 1  # only 1 of 3 passed
        assert int(verdict_match.group(3)) == 3  # 3 total
