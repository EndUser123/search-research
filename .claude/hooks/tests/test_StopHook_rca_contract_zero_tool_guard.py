#!/usr/bin/env python3
"""Tests for StopHook_rca_contract zero-tool-call guard (TASK-001).

Covers:
  - Confirmed root cause + empty tool_events → block
  - UNVERIFIED in root cause → exempt, pass
  - Non-confirmed root cause (missing/empty) + empty tool_events → no zero-tool block
  - tool_events present → no block regardless of root cause
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from StopHook_rca_contract import (
    _contains_unverified_token,
    _validate_rca_contract,
)


class TestContainsUnverifiedToken:
    """Tests for _contains_unverified_token helper."""

    def test_standalone_unverified_blocks(self):
        """UNVERIFIED as standalone word token should return True."""
        assert _contains_unverified_token("Root Cause: UNVERIFIED") is True
        # [UNVERIFIED] in brackets — word boundary after ] means UNVERIFIED is standalone
        assert _contains_unverified_token("Root Cause is [UNVERIFIED] tentative") is True
        assert _contains_unverified_token("UNVERIFIED") is True
        assert _contains_unverified_token("the word UNVERIFIED appears here") is True

    def test_unverified_not_flagged_in_substring(self):
        """UNVERIFIED as part of another word should return False."""
        assert _contains_unverified_token("NOTUNVERIFIED") is False
        assert _contains_unverified_token("fooUNVERIFIEDbar") is False

    def test_case_insensitive(self):
        """Matching should be case-insensitive."""
        assert _contains_unverified_token("root cause: unverified") is True
        assert _contains_unverified_token("Root Cause: UNVERIFIED") is True
        assert _contains_unverified_token("root cause: Unverified") is True


class TestZeroToolCallGuard:
    """Tests for zero-tool-call guard inside _validate_rca_contract."""

    def _make_response(
        self,
        symptom: str = "Symptom: test error",
        evidence: str = "Evidence: Read on file.py",
        executed_path: str = "Executed Path: file.py",
        alternative: str = "Alternative Hypothesis: A",
        falsifier: str = "Falsifier: Not A",
        root_cause: str = "Root Cause: bug in file.py",
        fix: str = "Fix: update file.py",
        verification: str = "Verification: run tests",
    ) -> str:
        return "\n".join(
            [
                f"## Symptom\n{symptom}",
                f"## Evidence\n{evidence}",
                f"## Executed Path\n{executed_path}",
                f"## Alternative Hypothesis\n{alternative}",
                f"## Falsifier\n{falsifier}",
                f"## Root Cause\n{root_cause}",
                f"## Fix\n{fix}",
                f"## Verification\n{verification}",
            ]
        )

    def test_confirmed_root_cause_empty_events_blocks(self):
        """Confirmed root cause + empty tool_events → block with zero-tool-calls reason."""
        response = self._make_response()
        is_valid, reasons = _validate_rca_contract(response, [], True, "sess", "term")
        assert is_valid is False
        # Implementation appends the full BLOCK_REASONS text, not the key
        assert any("zero tool calls" in r for r in reasons)

    def test_unverified_exempts(self):
        """Root cause containing UNVERIFIED → exempt, no zero-tool block."""
        response = self._make_response(root_cause="Root Cause: UNVERIFIED — not yet confirmed")
        is_valid, reasons = _validate_rca_contract(response, [], True, "sess", "term")
        assert "zero-tool-calls-for-confirmed-root-cause" not in reasons

    def test_missing_root_cause_no_zero_tool_block(self):
        """No root cause field → zero-tool guard does not fire (field guard handles it)."""
        response = self._make_response(root_cause="")
        is_valid, reasons = _validate_rca_contract(response, [], True, "sess", "term")
        assert "zero-tool-calls-for-confirmed-root-cause" not in reasons
        # Implementation returns full text from BLOCK_REASONS, not the key
        assert any("Root Cause not reachable" in r for r in reasons)

    def test_tool_events_present_no_block(self):
        """tool_events present → no zero-tool-call block even with confirmed root cause."""
        response = self._make_response()
        fake_events = [{"name": "Read", "command": "Read file.py"}]
        is_valid, reasons = _validate_rca_contract(response, fake_events, True, "sess", "term")
        assert "zero-tool-calls-for-confirmed-root-cause" not in reasons

    def test_non_rca_turn_skips(self):
        """rca_turn=False → validation skipped entirely, no zero-tool block."""
        response = self._make_response()
        is_valid, reasons = _validate_rca_contract(response, [], False, "sess", "term")
        assert is_valid is True
        assert reasons == []
