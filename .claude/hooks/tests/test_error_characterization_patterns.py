"""
Unit tests for ERROR_CHARACTERIZATION_PATTERNS and has_error_characterization().

Tests error-dismissal detection from claim_patterns.py:
- Positive cases: error-dismissal language that SHOULD be flagged
- Tentative cases: hedging language that should NOT be flagged
- False-positive regression: legitimate prose that must NOT be flagged

Test file: P:/.claude/hooks/__lib/claim_patterns.py
"""

import sys
from pathlib import Path

_hooks_dir = Path(__file__).resolve().parent.parent
_str_hooks_dir = str(_hooks_dir)
if _str_hooks_dir not in sys.path:
    sys.path.insert(0, _str_hooks_dir)

import pytest
from __lib.claim_patterns import has_error_characterization


class TestErrorDismissalDetected:
    """Error-dismissal language that should be flagged (requires investigation evidence)."""

    @pytest.mark.parametrize("text", [
        "This was a transient hook warning, not a real failure",
        "The hook error was non-blocking, benign noise",
        "No fix needed. The file is fine.",
        "known benign issue",
        "transient error, can be ignored",
        "not a real problem",
        "This is a transient error that can be ignored",
        "was a transient warning from the hook",
        "The file is fine.",
        "The hook is fine.",
    ])
    def test_error_dismissal_detected(self, text):
        assert has_error_characterization(text) is True


class TestTentativeLanguageAllowed:
    """Hedging/tentative language should NOT be flagged."""

    @pytest.mark.parametrize("text", [
        "This might be transient",
        "This could be benign",
        "appears to be transient",
    ])
    def test_tentative_not_flagged(self, text):
        assert has_error_characterization(text) is False


class TestNeutralStatementsAllowed:
    """Investigation-oriented statements should NOT be flagged."""

    @pytest.mark.parametrize("text", [
        "The traceback shows the root cause is...",
        "I need to investigate this error",
        "Let me read the hook source to understand the traceback",
    ])
    def test_neutral_not_flagged(self, text):
        assert has_error_characterization(text) is False


class TestFalsePositiveRegression:
    """Legitimate technical prose that must NOT trigger the gate.

    These cases come from pre-mortem adversarial testing (2026-04-16).
    They protect against pattern broadening that would cause advisory fatigue.
    """

    @pytest.mark.parametrize("text", [
        # 'transient' in non-error contexts
        "This is a transient API response design pattern",
        "this is a transient field in the dataclass",
        # 'known issue' in bug-tracker contexts
        "This is a known issue tracked in #1234",
        "The known issue with OpenSSL was patched in v3.2",
        "A known issue with Python 3.12 threading",
        # Colloquial 'not a problem'
        "Not a problem at all",
        # 'fine' in non-dismissal contexts
        "The file is fine to commit",
        "The hook is fine-grained enough for our needs",
    ])
    def test_legitimate_prose_not_flagged(self, text):
        assert has_error_characterization(text) is False


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_empty_response(self):
        assert has_error_characterization("") is False

    def test_none_response(self):
        assert has_error_characterization(None) is False

    def test_non_string_response(self):
        assert has_error_characterization(123) is False

    def test_case_insensitive(self):
        assert has_error_characterization("TRANSIENT ERROR, CAN BE IGNORED") is True
        assert has_error_characterization("benign noise in the system") is True

    def test_no_fix_needed_case_insensitive(self):
        assert has_error_characterization("NO FIX NEEDED") is True
        assert has_error_characterization("no Fix Needed") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
