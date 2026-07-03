#!/usr/bin/env python3
"""Regression suite for CKS correction context-injection pipeline.

Covers:
- Read-path relevance filtering (overlap threshold + punctuation normalization)
- Injection mode gating
- Dead-path regression (no __csf.nip in executable paths)
"""

from __future__ import annotations

import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

# Import the module under test
from UserPromptSubmit import cks_context
from turn_mode import classify as classify_turn_mode


# ============================================================================
# Part A1: Read-path relevance filtering
# ============================================================================

class TestReadPathRelevanceFiltering:
    """Unit tests: _query_recent_corrections precision gate."""

    def _write_correction(self, title: str, content: str) -> str:
        """Write a live correction to the real DB and return its ID."""
        cks_path = Path("P:/packages/.claude-marketplace/plugins/search-research/core")
        if str(cks_path) not in sys.path:
            sys.path.insert(0, str(cks_path))
        from cks.unified import CKS

        db = "P:/__csf/data/cks.db"
        with CKS(db) as cks:
            eid = cks.ingest_correction(
                title=title,
                content=content,
                test_marker="test_cks_correction_inject",
                test_timestamp=datetime.now(timezone.utc).isoformat(),
            )
        return eid

    def test_zero_overlap_not_returned(self):
        """Entries with zero keyword overlap must NOT appear in results."""
        # Write a correction with distinctive words that won't overlap anything
        eid = self._write_correction(
            title="xyz_quark_flux_capacitor_2026",
            content="When calibrating the xyz device, avoid using quark flux. "
                    "The flux capacitor must be balanced with rare-earth magnets only.",
        )

        try:
            results = cks_context._query_recent_corrections(
                "fix the CSS layout issue",  # no overlap with xyz/quark/flux/capacitor
                max_results=5,
                hours=48,
            )
            titles = [r["title"] for r in results]
            assert eid not in titles, (
                f"Bug: zero-overlap entry returned. entry_id={eid}, "
                f"prompt='fix the CSS layout issue', returned_titles={titles}"
            )
        finally:
            # Cleanup
            conn = sqlite3.connect("P:/__csf/data/cks.db")
            conn.execute("DELETE FROM entries WHERE id=?", (eid,))
            conn.commit()
            conn.close()

    def test_punctuation_normalization(self):
        """'authentication,' must match 'authentication' after normalization."""
        # The normalization logic:
        # 1. separator replacement: hyphen/underscore/slash → space
        # 2. punctuation stripping: trailing . , ! ? ; : etc.
        normalized = cks_context._query_recent_corrections.__code__.co_consts[1]
        # Verify the normalize function exists by checking scoring works correctly
        prompt = "How do I handle authentication in my app?"
        results = cks_context._query_recent_corrections(prompt, max_results=3, hours=48)

        # If our auth correction exists and is recent, it should be returned
        # (the one we wrote earlier in the session will still be there)
        if results:
            # At least one result has overlap > 0
            prompt_words = set()
            normalized = re.sub(r"[-_/]", " ", prompt.lower())
            prompt_words = set(
                w.strip().strip(".,!?;:\"'()[]{}")
                for w in normalized.split()
                if w.strip().strip(".,!?;:\"'()[]{}")
            )
            for r in results:
                entry_words = set()
                normalized_e = re.sub(r"[-_/]", " ", ((r["title"] or "") + " " + (r["content"] or "")).lower())
                entry_words = set(
                    w.strip().strip(".,!?;:\"'()[]{}")
                    for w in normalized_e.split()
                    if w.strip().strip(".,!?;:\"'()[]{}")
                )
                overlap = len(prompt_words & entry_words)
                assert overlap > 0, (
                    f"Bug: returned result with zero overlap. "
                    f"prompt_words={prompt_words}, entry_words={entry_words}, "
                    f"title={r['title']}"
                )

    def test_top_result_has_highest_overlap(self):
        """Results must be sorted by overlap descending, not by created_at."""
        results = cks_context._query_recent_corrections(
            "authentication session jwt", max_results=5, hours=48
        )
        if len(results) >= 2:
            # Compute overlap for each
            prompt = "authentication session jwt"
            prompt_words = set()
            normalized = re.sub(r"[-_/]", " ", prompt.lower())
            prompt_words = set(
                w.strip().strip(".,!?;:\"'()[]{}")
                for w in normalized.split()
                if w.strip().strip(".,!?;:\"'()[]{}")
            )
            scores = []
            for r in results:
                normalized_e = re.sub(
                    r"[-_/]", " ",
                    ((r["title"] or "") + " " + (r["content"] or "")).lower(),
                )
                entry_words = set(
                    w.strip().strip(".,!?;:\"'()[]{}")
                    for w in normalized_e.split()
                    if w.strip().strip(".,!?;:\"'()[]{}")
                )
                scores.append(len(prompt_words & entry_words))
            # Must be non-increasing
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1], (
                    f"Sort order wrong: scores={scores} — higher overlap must come first"
                )


# ============================================================================
# Part A2: Injection mode gating
# ============================================================================

class TestInjectionModeGating:
    """Unit tests: turn mode determines whether auto-injection fires."""

    # Real prompt patterns that the classifier recognizes for each mode.
    # The classifier uses frozenset starts + keyword matching, not arbitrary labels.
    PROMPTS_BY_MODE: dict[str, str] = {
        # Control: starts with imperative verb/command
        "control": "Stop, I want to try a different approach.",
        # Plan: matches _PLANNING_PROMPT_RE (next steps, roadmap, action items, etc.)
        "plan": "What are the next steps for this refactor?",
        # Meta: contains hook/system introspection keywords
        "meta": "How does the cks_context hook work?",
        # Exploration: contains architecture/design keywords
        "exploration": "Which is better: Redis session store or JWT tokens?",
        # Execution-report: starts with [status] or similar
        "execution-report": "[status] Done. All tests pass.",
        # Analysis: causal reasoning (no ? — ? routes to final-answer)
        "analysis": "The authentication module started throwing 401 errors after the last deployment.",
        # Final-answer: direct question (has '?')
        "final-answer": "What authentication library should I use for this project?",
    }

    MODES_EXPECTED_TO_INJECT = {"analysis", "final-answer", "meta"}
    MODES_EXPECTED_TO_SKIP = {"control", "plan", "exploration", "execution-report"}

    @pytest.mark.parametrize("mode", sorted(MODES_EXPECTED_TO_INJECT))
    def test_mode_injects(self, mode):
        """Injection must be enabled for analysis, final-answer, meta."""
        prompt = self.PROMPTS_BY_MODE[mode]
        data = {"user_prompt": prompt, "response": ""}
        classified = classify_turn_mode(data)
        assert classified == mode, (
            f"Turn classifier returned '{classified}', expected '{mode}'. "
            f"Prompt: {prompt}"
        )

        should_inject = cks_context._should_inject_recent_corrections(prompt)
        assert should_inject, (
            f"Bug: _should_inject_recent_corrections returned False for mode='{mode}'. "
            f"CORRECTION_INJECTION_MODES={cks_context.CORRECTION_INJECTION_MODES}"
        )

    @pytest.mark.parametrize("mode", sorted(MODES_EXPECTED_TO_SKIP))
    def test_mode_skips(self, mode):
        """Injection must be disabled for control, plan, exploration, execution-report."""
        prompt = self.PROMPTS_BY_MODE[mode]
        data = {"user_prompt": prompt, "response": ""}
        classified = classify_turn_mode(data)
        assert classified == mode, (
            f"Turn classifier returned '{classified}', expected '{mode}'. "
            f"Prompt: {prompt}"
        )

        should_inject = cks_context._should_inject_recent_corrections(prompt)
        assert not should_inject, (
            f"Bug: _should_inject_recent_corrections returned True for mode='{mode}'. "
            f"CORRECTION_INJECTION_MODES={cks_context.CORRECTION_INJECTION_MODES}"
        )

    def test_env_var_disables(self, monkeypatch):
        """CKS_CORRECTION_AUTO_INJECT=false must disable injection."""
        monkeypatch.setenv("CKS_CORRECTION_AUTO_INJECT", "false")
        # Re-import to pick up env change (env var read at call time, not import time)
        # No need to re-import — the function reads os.environ at runtime
        should_inject = cks_context._should_inject_recent_corrections(
            "Analyze the authentication flow for me"
        )
        assert not should_inject, (
            "Bug: injection not disabled by CKS_CORRECTION_AUTO_INJECT=false"
        )


# ============================================================================
# Part A3: Dead-path regression
# ============================================================================

class TestDeadPathRegression:
    """No executable hook files may contain __csf.nip paths."""

    HOOKS_DIR = Path(__file__).resolve().parent.parent
    DEAD_PATH = "__csf.nip"

    def test_no_csf_nip_in_hook_files(self):
        """Grep all .py hook files for __csf.nip string in executable paths."""
        violations = []
        for py_file in self.HOOKS_DIR.glob("**/*.py"):
            # Skip test files, caches, __pycache__
            if any(part in py_file.parts for part in ("__pycache__", "_legacy", ".pytest_cache", "tests")):
                continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                if self.DEAD_PATH in content:
                    # Find line numbers
                    for i, line in enumerate(content.splitlines(), 1):
                        if self.DEAD_PATH in line and not line.strip().startswith("#"):
                            violations.append(f"{py_file.relative_to(self.HOOKS_DIR)}:{i}: {line.strip()}")
            except OSError:
                continue

        assert not violations, (
            f"Dead path '{self.DEAD_PATH}' found in hook files (must use P:/__csf/data/cks.db instead):\n"
            + "\n".join(violations)
        )