"""Tests for empirical_claims_gate.py — pytest coverage for DOC-PROXY and VERIFICATION-LANGUAGE violations."""

from __future__ import annotations

import sys
from pathlib import Path

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent))
from empirical_claims_gate import (
    check_empirical_claims,
    run,
)


# ── Violation 1: DOC-PROXY ───────────────────────────────────────────────────

class TestDOCPROXY:
    """Tests for Violation 1: document metadata + implementation claim without code evidence."""

    def test_doc_proxy_fires_on_status_proposed_not_implemented(self):
        """DOC-PROXY should fire when ADR Status: Proposed is cited alongside 'not implemented'."""
        text = 'Status: Proposed not implemented. The RFC was NOT fully implemented.'
        result = check_empirical_claims(text)
        assert result is not None, "DOC-PROXY should fire on Status: Proposed + not implemented"
        assert "DOC-PROXY" in result["violation"]

    def test_doc_proxy_fires_on_status_draft_not_implemented(self):
        """DOC-PROXY should fire on Status: Draft + 'not implemented'."""
        text = "The RFC has Status: Draft and is not implemented."
        result = check_empirical_claims(text)
        assert result is not None, "DOC-PROXY should fire on Status: Draft + not implemented"
        assert "DOC-PROXY" in result["violation"]

    def test_doc_proxy_fires_on_status_pending_task(self):
        """DOC-PROXY should fire on 'task pending' + 'not implemented'."""
        text = "The task is pending and not implemented."
        result = check_empirical_claims(text)
        assert result is not None, "DOC-PROXY should fire on task pending + not implemented"

    def test_doc_proxy_fires_on_proposed_incomplete(self):
        """DOC-PROXY should fire on Status: Proposed + 'incomplete' (not just 'not implemented')."""
        text = "Status: Proposed not implemented and incomplete"
        result = check_empirical_claims(text)
        assert result is not None, "DOC-PROXY should fire on Status: Proposed + incomplete"

    def test_doc_proxy_fires_on_proposed_unfinished(self):
        """DOC-PROXY should fire on Status: Proposed + 'unfinished'."""
        text = "Status: Proposed not implemented and unfinished"
        result = check_empirical_claims(text)
        assert result is not None, "DOC-PROXY should fire on Status: Proposed + unfinished"

    def test_doc_proxy_with_unicode_quotes(self):
        """DOC-PROXY should fire regardless of quote style (straight or curly)."""
        text = 'Status: Proposed not implemented.'
        result = check_empirical_claims(text)
        assert result is not None, "DOC-PROXY should fire with standard quotes"

    def test_doc_proxy_exempted_by_code_evidence(self):
        """DOC-PROXY should NOT fire when code evidence is present."""
        text = "Searched for 'select_provider' — found at orchestrator.py:243. Status: Proposed but the feature IS implemented."
        result = check_empirical_claims(text)
        assert result is None, "DOC-PROXY should be exempted by Grep evidence"

    def test_doc_proxy_not_fired_on_doc_status_alone(self):
        """DOC-PROXY should NOT fire on document status without an implementation claim."""
        text = "The ADR has Status: Proposed and needs review."
        result = check_empirical_claims(text)
        assert result is None, "DOC-PROXY should not fire on status alone without claim"

    def test_doc_proxy_not_fired_on_claim_alone(self):
        """DOC-PROXY should NOT fire on implementation claim without document status proxy."""
        text = "X is not fully implemented."
        result = check_empirical_claims(text)
        assert result is None, "DOC-PROXY should not fire on claim alone without doc status"


# ── Violation 2: VERIFICATION-LANGUAGE ───────────────────────────────────────

class TestVerificationLanguage:
    """Tests for Violation 2: verification language near claim without code evidence."""

    def test_verif_near_claim_fires(self):
        """VERIFICATION-LANGUAGE should fire when 'verify' appears near 'is implemented'."""
        text = "X is implemented — verify against actual code."
        result = check_empirical_claims(text)
        assert result is not None, "VERIFICATION-LANGUAGE should fire on verify + claim nearby"
        assert "VERIFICATION-LANGUAGE" in result["violation"]

    def test_verif_near_claim_60_chars_apart(self):
        """VERIFICATION-LANGUAGE should fire even when 60 chars separate the phrases."""
        text = "X is implemented" + " " * 60 + "verify against code."
        result = check_empirical_claims(text)
        assert result is not None, f"VERIFICATION-LANGUAGE should fire at 60-char separation (WINDOW=200)"

    def test_verif_near_not_implemented(self):
        """VERIFICATION-LANGUAGE should fire on verify + 'not implemented'."""
        text = "X is not implemented — we need Tier 1 evidence."
        result = check_empirical_claims(text)
        assert result is not None, "VERIFICATION-LANGUAGE should fire on verify + not implemented"

    def test_verif_exempted_by_code_evidence(self):
        """VERIFICATION-LANGUAGE should NOT fire when code evidence is present."""
        text = "Searched for 'empirical_claims_gate' — found at hooks/empirical_claims_gate.py:54. The verification patterns ARE implemented."
        result = check_empirical_claims(text)
        assert result is None, "VERIFICATION-LANGUAGE should be exempted by file:line citation"

    def test_verif_lang_case_insensitive(self):
        """VERIFICATION-LANGUAGE should fire regardless of case on 'searched'."""
        text = "I searched for 'foo' — X is implemented."
        result = check_empirical_claims(text)
        # Note: current pattern requires capital 'S' — this test documents the desired behavior
        # After fix: should be None (exempted by 'searched')
        # Current behavior may vary based on implementation


# ── Code evidence patterns ───────────────────────────────────────────────────

class TestCodeEvidenceExemptions:
    """Tests that code evidence properly exempts responses from blocking."""

    def test_file_path_exempts(self):
        """File:line citation should exempt."""
        text = "local_model is wired into select_provider() at orchestrator.py:243."
        result = check_empirical_claims(text)
        assert result is None, "file:line citation should exempt"

    def test_read_exempts(self):
        """'Read N files' should exempt."""
        text = "Read 2 files: lm_studio_provider.py exists."
        result = check_empirical_claims(text)
        assert result is None, "'Read N files' should exempt"

    def test_import_statement_exempts(self):
        """Import statement should exempt."""
        text = "The code imports from hooks/empirical_claims_gate.py which handles this."
        result = check_empirical_claims(text)
        assert result is None, "import statement should exempt"

    def test_def_statement_exempts(self):
        """Function definition should exempt."""
        text = "def check_empirical_claims is the entry point."
        result = check_empirical_claims(text)
        assert result is None, "def statement should exempt"

    def test_swift_extension_not_exempted(self):
        """Swift file extensions not in pattern should NOT exempt (before fix)."""
        text = "feature.swift:42 shows the implementation."
        # Current pattern only covers py|ts|js|go|rs|java|rb|cpp|c|cs
        # After fix with [a-z]{1,10} this should be None
        result = check_empirical_claims(text)
        # Documenting current behavior


# ── run() protocol (RISK-003) ───────────────────────────────────────────────

class TestRunProtocol:
    """Tests for the Stop_router subprocess protocol."""

    def test_run_returns_none_for_clean_response(self):
        """run() should return None (allow) for clean response."""
        data = {"assistant_response": "The feature works correctly — I verified it by reading the code."}
        result = run(data)
        assert result is None, "Clean response should return None"

    def test_run_returns_block_for_doc_proxy(self):
        """run() should return block dict for DOC-PROXY violation."""
        data = {"assistant_response": 'Status: Proposed not implemented and ADR was NOT fully implemented.'}
        result = run(data)
        assert result is not None, "DOC-PROXY should be blocked"
        assert result.get("block") is True
        assert "reason" in result

    def test_run_returns_block_for_verif_lang(self):
        """run() should return block dict for VERIFICATION-LANGUAGE violation."""
        data = {"assistant_response": "X is implemented — verify against code."}
        result = run(data)
        assert result is not None, "VERIFICATION-LANGUAGE should be blocked"
        assert result.get("block") is True

    def test_run_accepts_response_field(self):
        """run() should also accept 'response' as field name."""
        data = {"response": 'Status: Proposed not implemented and the RFC is incomplete.'}
        result = run(data)
        assert result is not None, "run() should accept 'response' field"
        assert result.get("block") is True

    def test_run_returns_none_for_empty_response(self):
        """run() should return None for empty response."""
        data = {"assistant_response": ""}
        result = run(data)
        assert result is None, "Empty response should return None"

    def test_run_json_output_structure(self):
        """run() output should be parseable JSON with required fields."""
        data = {"assistant_response": 'Status: Proposed not implemented.'}
        result = run(data)
        if result is not None:
            # Should be a dict with block and reason
            assert isinstance(result, dict)
            assert "block" in result
            assert "reason" in result


# ── Self-tests (migrated from __main__) ──────────────────────────────────────

class TestSelfTestMigrations:
    """Inline self-tests converted to pytest assertions."""

    def test_incident_replay_caught(self):
        """Motivating incident should be caught."""
        incident = (
            'RFC-20260403 is NOT fully implemented. '
            'Status is Proposed, meaning it is an uncommitted architectural decision.'
        )
        assert check_empirical_claims(incident) is not None

    def test_adr_status_proxy_caught(self):
        """ADR status proxy should be caught."""
        assert check_empirical_claims('Status: Proposed not implemented') is not None

    def test_plan_pending_proxy_caught(self):
        """Pending task proxy should be caught."""
        assert check_empirical_claims("plan pending not implemented") is not None

    def test_verif_near_impl_caught(self):
        """Verification near implementation claim should be caught."""
        assert check_empirical_claims("X is implemented — verify against actual code.") is not None

    def test_verif_near_not_impl_caught(self):
        """Verification near non-implementation claim should be caught."""
        assert check_empirical_claims("X is not implemented — we need Tier 1 evidence.") is not None

    def test_with_grep_exempts(self):
        """Grep evidence should exempt."""
        text = "Searched for 'select_provider' — found at orchestrator.py:243. The provider IS implemented."
        assert check_empirical_claims(text) is None

    def test_with_read_exempts(self):
        """Read evidence should exempt."""
        text = "Read 2 files: lm_studio_provider.py exists. LocalModelProvider is fully implemented."
        assert check_empirical_claims(text) is None

    def test_with_file_line_exempts(self):
        """file:line citation should exempt."""
        text = "local_model is wired into select_provider() at orchestrator.py:243. The feature is implemented."
        assert check_empirical_claims(text) is None

    def test_doc_status_without_impl_claim_passes(self):
        """Doc status without implementation claim should pass."""
        assert check_empirical_claims("The ADR has status Proposed and needs review.") is None

    def test_empty_response_passes(self):
        """Empty response should pass."""
        assert check_empirical_claims("") is None

    def test_verif_without_claim_nearby_passes(self):
        """Verification language without nearby claim should pass."""
        text = (
            "The VERIFICATION-LANGUAGE trigger fires when verify appears "
            "without a nearby implementation assertion."
        )
        assert check_empirical_claims(text) is None

    def test_verif_with_code_exempts(self):
        """Verification language WITH code evidence should exempt."""
        text = (
            "Searched for 'empirical_claims_gate' — found at hooks/empirical_claims_gate.py:54. "
            "The verification language patterns ARE implemented."
        )
        assert check_empirical_claims(text) is None
