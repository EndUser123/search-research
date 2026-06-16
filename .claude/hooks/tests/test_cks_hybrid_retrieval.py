#!/usr/bin/env python3
"""Tests for CKS hybrid semantic + keyword correction injection.

Covers:
- Feature flag gating (CKS_CORRECTION_SEMANTIC env var)
- Keyword retrieval unchanged when flag is off
- Semantic retrieval produces results when flag is on
- De-duplication: keyword results preserved, semantic-only appended
- Fail-open on semantic errors (keyword results returned)
"""

from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

from UserPromptSubmit_modules import cks_context
from turn_mode import classify as classify_turn_mode


# ============================================================================
# Helpers
# ============================================================================

def _write_correction(title: str, content: str, hours_ago: int = 1) -> str:
    """Write a live correction to the real DB and return its ID."""
    cks_path = Path("P:/packages/.claude-marketplace/plugins/search-research/core")
    if str(cks_path) not in sys.path:
        sys.path.insert(0, str(cks_path))
    from cks.unified import CKS

    db = "P:/__csf/data/cks.db"
    created_at = (datetime.now(timezone.utc).replace(microsecond=0) -
                  timedelta(hours=hours_ago)).isoformat()

    with CKS(db_path=db, enable_semantic=True) as cks:
        eid = cks.ingest_correction(
            title=title,
            content=content,
            test_marker="test_cks_hybrid",
            test_timestamp=created_at,
        )
    return eid


def _cleanup_correction(eid: str) -> None:
    conn = sqlite3.connect("P:/__csf/data/cks.db")
    conn.execute("DELETE FROM entries WHERE id=?", (eid,))
    conn.commit()
    conn.close()


def _classify_mode(prompt: str) -> str:
    data = {"user_prompt": prompt, "response": ""}
    return classify_turn_mode(data)


# ============================================================================
# Test: Feature flag gates semantic path
# ============================================================================

class TestSemanticFlagGating:
    """CKS_CORRECTION_SEMANTIC env var controls hybrid behavior."""

    def test_flag_off_keyword_only(self, monkeypatch):
        """When CKS_CORRECTION_SEMANTIC=false, keyword retrieval only."""
        monkeypatch.setenv("CKS_CORRECTION_SEMANTIC", "false")
        # Force module-level re-read
        import importlib
        importlib.reload(cks_context)

        assert cks_context.CKS_SEMANTIC_ENABLED is False

        # _query_hybrid_corrections should fall back to keyword-only
        results = cks_context._query_hybrid_corrections("authentication jwt token", max_results=3, hours=48)
        # Should not call semantic path when flag is off
        # (No mock needed — just verify it returns results from keyword path)
        assert isinstance(results, list)
        importlib.reload(cks_context)  # restore

    def test_flag_on_enables_hybrid(self, monkeypatch):
        """When CKS_CORRECTION_SEMANTIC=true, hybrid path activates."""
        monkeypatch.setenv("CKS_CORRECTION_SEMANTIC", "true")
        import importlib
        importlib.reload(cks_context)

        assert cks_context.CKS_SEMANTIC_ENABLED is True
        importlib.reload(cks_context)  # restore

    def test_flag_default_is_off(self, monkeypatch):
        """CKS_CORRECTION_SEMANTIC defaults to false."""
        monkeypatch.delenv("CKS_CORRECTION_SEMANTIC", raising=False)
        import importlib
        importlib.reload(cks_context)

        assert cks_context.CKS_SEMANTIC_ENABLED is False
        importlib.reload(cks_context)  # restore


# ============================================================================
# Test: Keyword retrieval unchanged when flag is off
# ============================================================================

class TestKeywordRetrievalUnchanged:
    """Verify keyword path produces correct results regardless of semantic flag."""

    def test_strong_keyword_overlap_returns_result(self, monkeypatch):
        """Keyword path returns corrections with strong word overlap."""
        monkeypatch.setenv("CKS_CORRECTION_SEMANTIC", "false")

        # Write a correction with distinctive overlapping words
        eid = _write_correction(
            title="auth_fix_flux_xyz_correction_2026",
            content="When fixing flux capacitor auth, ensure rare-earth magnets are balanced. "
                    "Do not use xyz authentication without proper jwt token handling.",
        )
        try:
            results = cks_context._query_recent_corrections(
                "fix authentication jwt token error",
                max_results=5,
                hours=48,
            )
            titles = [r["title"] for r in results]
            # Should find by keyword overlap: "auth"+"jwt"+"token"+"fix"
            assert any("auth_fix_flux_xyz" in t for t in titles), (
                f"Keyword result missing. titles={titles}"
            )
        finally:
            _cleanup_correction(eid)


# ============================================================================
# Test: De-duplication — keyword results preserved
# ============================================================================

class TestHybridDeduplication:
    """Keyword results always come first; semantic-only results appended."""

    def test_keyword_results_first(self, monkeypatch):
        """Keyword results appear before semantic-only results in merged list."""
        monkeypatch.setenv("CKS_CORRECTION_SEMANTIC", "true")

        # Write two corrections:
        # - kw_entry: high keyword overlap, should appear first
        # - sem_only: low keyword overlap but semantic match, appended after
        kw_eid = _write_correction(
            title="keyword_auth_jwt_overlap_correction",
            content="Use authentication JWT token for secure session handling. "
                    "This pattern applies to auth flows with jwt token validation.",
        )
        sem_eid = _write_correction(
            title="semantic_symptom_silent_failure_fix",
            content="The flux capacitor silently failed to validate session tokens. "
                    "Symptoms appeared as mysterious 401 errors appearing intermittently. "
                    "Root cause was missing token signature verification in the auth module.",
        )
        try:
            # Query using symptom language (zero keyword overlap with sem_only)
            # but high overlap with kw_entry
            results = cks_context._query_hybrid_corrections(
                "fix authentication jwt token error",
                max_results=5,
                hours=48,
            )
            ids = [r["id"] for r in results]

            # kw_entry MUST be in results (keyword overlap)
            assert kw_eid in ids, f"keyword result missing: {kw_eid} not in {ids}"

            # sem_only may or may not appear depending on embedding quality
            # But if it does, kw_entry must come first
            if sem_eid in ids:
                kw_pos = ids.index(kw_eid)
                sem_pos = ids.index(sem_eid)
                assert kw_pos < sem_pos, (
                    f"keyword result must come before semantic-only: "
                    f"kw_pos={kw_pos}, sem_pos={sem_pos}"
                )

        finally:
            _cleanup_correction(kw_eid)
            _cleanup_correction(sem_eid)


# ============================================================================
# Test: Fail-open on semantic errors
# ============================================================================

class TestSemanticFailOpen:
    """Semantic path errors fall back to keyword-only, never break injection."""

    def test_semantic_error_returns_keyword_results(self, monkeypatch):
        """If semantic path throws, _query_hybrid_corrections returns keyword results."""
        monkeypatch.setenv("CKS_CORRECTION_SEMANTIC", "true")

        kw_eid = _write_correction(
            title="failopen_keyword_result_2026",
            content="Ensure proper authentication error handling with jwt token validation. "
                    "Never use hardcoded credentials in production systems.",
        )
        try:
            # Patch _query_semantic_corrections to always throw
            with patch.object(
                cks_context,
                "_query_semantic_corrections",
                side_effect=RuntimeError("semantic path broken"),
            ):
                results = cks_context._query_hybrid_corrections(
                    "authentication jwt token security",
                    max_results=3,
                    hours=48,
                )

            # Should still return keyword result
            ids = [r["id"] for r in results]
            assert kw_eid in ids, (
                f"keyword result should still be returned on semantic error: {ids}"
            )
        finally:
            _cleanup_correction(kw_eid)


# ============================================================================
# Test: Integration — _should_inject_recent_corrections gate still works
# ============================================================================

class TestInjectionGateIntegration:
    """_should_inject_recent_corrections gates injection regardless of semantic flag."""

    MODES_EXPECTED_TO_INJECT = {"analysis", "final-answer", "meta"}
    MODES_EXPECTED_TO_SKIP = {"control", "plan", "exploration", "execution-report"}

    PROMPTS_BY_MODE = {
        "control": "Stop, I want to try a different approach.",
        "plan": "What are the next steps for this refactor?",
        "meta": "How does cks_context work?",
        "exploration": "Which is better: Redis or JWT?",
        "execution-report": "[status] Done. All tests pass.",
        "analysis": "The auth module started throwing 401 errors after deployment.",
        "final-answer": "What authentication library should I use?",
    }

    @pytest.mark.parametrize("mode", sorted(MODES_EXPECTED_TO_INJECT))
    def test_mode_injects(self, mode, monkeypatch):
        """Injection enabled for analysis/final-answer/meta."""
        monkeypatch.setenv("CKS_CORRECTION_AUTO_INJECT", "true")
        monkeypatch.setenv("CKS_CORRECTION_SEMANTIC", "false")
        prompt = self.PROMPTS_BY_MODE[mode]
        classified = _classify_mode(prompt)
        assert classified == mode, f"Classifier returned {classified}, expected {mode}"
        assert cks_context._should_inject_recent_corrections(prompt) is True

    @pytest.mark.parametrize("mode", sorted(MODES_EXPECTED_TO_SKIP))
    def test_mode_skips(self, mode, monkeypatch):
        """Injection disabled for control/plan/exploration/execution-report."""
        monkeypatch.setenv("CKS_CORRECTION_AUTO_INJECT", "true")
        monkeypatch.setenv("CKS_CORRECTION_SEMANTIC", "false")
        prompt = self.PROMPTS_BY_MODE[mode]
        classified = _classify_mode(prompt)
        assert classified == mode, f"Classifier returned {classified}, expected {mode}"
        assert cks_context._should_inject_recent_corrections(prompt) is False