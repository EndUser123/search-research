#!/usr/bin/env python3
"""Tests for Stop_tdd_refactor_gate.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Stop_tdd_refactor_gate import (
    _has_completion_language,
    _has_refactor_evidence,
    check_tdd_refactor,
)


class TestHasCompletionLanguage:
    """Tests for _has_completion_language helper."""

    def test_refactor_complete_pattern(self):
        """'refactoring complete' triggers completion language."""
        assert _has_completion_language("The refactoring complete.") is True

    def test_tests_all_passing_pattern(self):
        """'tests all passing now' triggers completion language."""
        assert _has_completion_language("All tests passing now.") is True

    def test_all_done_pattern(self):
        """'all done' triggers completion language."""
        assert _has_completion_language("All done! The code is clean.") is True

    def test_code_is_clean_pattern(self):
        """'code is clean' triggers completion language."""
        assert _has_completion_language("The code is clean now.") is True

    def test_green_refactor_pattern(self):
        """'green' near 'refactor' triggers completion language."""
        assert _has_completion_language("Green refactor done.") is True

    def test_emoji_checkmark_pattern(self):
        """Emoji checkmark with refactor triggers completion language."""
        assert _has_completion_language("✅ refactoring complete") is True

    def test_no_completion_language(self):
        """Normal statements without completion language pass through."""
        assert _has_completion_language("Running pytest to check the tests.") is False
        assert _has_completion_language("Need to clean up this function.") is False


class TestHasRefactorEvidence:
    """Tests for _has_refactor_evidence helper."""

    def test_pytest_pass_evidence(self):
        """'pytest...pass' is valid refactor evidence."""
        assert _has_refactor_evidence("pytest ran and all tests pass") is True

    def test_tests_pass_evidence(self):
        """'tests...pass' is valid refactor evidence."""
        assert _has_refactor_evidence("All tests pass now") is True

    def test_run_pytest_evidence(self):
        """'run pytest' is valid refactor evidence."""
        assert _has_refactor_evidence("I will run pytest to verify") is True

    def test_test_suite_evidence(self):
        """'test suite' is valid refactor evidence."""
        assert _has_refactor_evidence("Test suite passes") is True

    def test_no_evidence(self):
        """Without evidence patterns, returns False."""
        assert _has_refactor_evidence("The code looks clean") is False


class TestCheckTddRefactor:
    """Tests for check_tdd_refactor main function."""

    def test_no_tdd_state_allows(self, monkeypatch):
        """When no TDD state file exists, allows through."""
        monkeypatch.setattr(
            "Stop_tdd_refactor_gate._check_active_refactor",
            lambda: (False, None),
        )
        data = {"response_text": "The refactoring is complete."}
        result = check_tdd_refactor(data)
        assert result is None

    def test_no_completion_language_allows(self, monkeypatch):
        """When TDD is refactoring but no completion language, allows."""
        monkeypatch.setattr(
            "Stop_tdd_refactor_gate._check_active_refactor",
            lambda: (True, "test_foo.py"),
        )
        data = {"response_text": "Running the tests now."}
        result = check_tdd_refactor(data)
        assert result is None

    def test_completion_with_evidence_allows(self, monkeypatch):
        """When TDD is refactoring with completion language AND evidence, allows."""
        monkeypatch.setattr(
            "Stop_tdd_refactor_gate._check_active_refactor",
            lambda: (True, "test_foo.py"),
        )
        data = {"response_text": "The refactoring is complete. pytest passed."}
        result = check_tdd_refactor(data)
        assert result is None

    def test_completion_without_evidence_blocks(self, monkeypatch):
        """When TDD is refactoring with completion language but NO evidence, blocks."""
        monkeypatch.setattr(
            "Stop_tdd_refactor_gate._check_active_refactor",
            lambda: (True, "test_foo.py"),
        )
        # Mock both block count functions to isolate test from filesystem state
        monkeypatch.setattr(
            "Stop_tdd_refactor_gate._load_block_count",
            lambda: 0,
        )
        monkeypatch.setattr(
            "Stop_tdd_refactor_gate._save_block_count",
            lambda _count: None,
        )
        # Use string that definitely matches completion pattern: "All done!"
        data = {"response_text": "All done!"}
        result = check_tdd_refactor(data)
        assert result is not None
        assert result.get("decision") == "block"
        assert "refactoring" in result.get("reason", "").lower()

    def test_circuit_breaker_allows_after_max_blocks(self, monkeypatch):
        """Circuit breaker safety valve allows through after MAX blocks."""
        monkeypatch.setattr(
            "Stop_tdd_refactor_gate._check_active_refactor",
            lambda: (True, "test_foo.py"),
        )
        monkeypatch.setattr(
            "Stop_tdd_refactor_gate._load_block_count",
            lambda: 5,  # MAX_CONSECUTIVE_BLOCKS = 5
        )
        data = {"response_text": "The refactoring is complete."}
        result = check_tdd_refactor(data)
        # After MAX blocks, safety valve allows through
        assert result is None
