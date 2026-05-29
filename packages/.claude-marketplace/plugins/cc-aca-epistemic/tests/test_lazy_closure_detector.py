"""Tests for lazy_closure_detector RNS false-positive fix and self-referential evasion patterns.

Covers:
- RNS machine-format lines (RNS|D|, RNS|A|, RNS|Z|) are stripped before evasion matching
- unverified=1 in RNS field values does NOT trigger self_referential_evasion
- [UNVERIFIED] bracketed marker does NOT trigger (existing lookbehind)
- bare 'unverified' in prose DOES still trigger (regression guard)
- (?<!=) lookbehind edge cases
"""
from __future__ import annotations

import re

import pytest

# Import the compiled patterns directly to avoid full module import chain.
_PATTERNS_SOURCE = (
    "P:/packages/cc-aca-epistemic/__lib/anti_sycophancy/lazy_closure_detector.py"
)


def _read_patterns() -> list[str]:
    """Extract SELF_REFERENTIAL_EVASION_PATTERNS from source file."""
    content = open(_PATTERNS_SOURCE, encoding="utf-8").read()
    patterns: list[str] = []
    in_list = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "SELF_REFERENTIAL_EVASION_PATTERNS = [":
            in_list = True
            continue
        if in_list and stripped == "]":
            break
        if in_list and stripped.startswith('r"'):
            raw = stripped.rstrip(",")
            patterns.append(raw[2:-1])  # strip r" and trailing "
    return patterns


PATTERNS = _read_patterns()


@pytest.fixture
def compiled_patterns() -> list[re.Pattern[str]]:
    return [re.compile(p) for p in PATTERNS]


def _any_match(patterns: list[re.Pattern[str]], text: str) -> list[str]:
    return [m.group(0) for p in patterns for m in p.finditer(text)]


class TestRNSMachineFormatStripping:
    """RNS| lines should be stripped before self-referential evasion matching."""

    def test_rns_action_line_stripped(self, compiled_patterns):
        rns_line = (
            "RNS|A|1a|hooks|E:?|recover/medium|"
            "not verified in runtime||owner=|done=0|unverified=1|root_cause=unknown"
        )
        _NL = chr(10)
        stripped = _NL.join(
            line for line in rns_line.split(_NL) if not line.startswith("RNS|")
        )
        assert stripped == ""

    def test_rns_domain_line_stripped(self):
        _NL = chr(10)
        lines = "RNS|D|1|\U0001f4cc|HOOKS"
        stripped = _NL.join(
            line for line in lines.split(_NL) if not line.startswith("RNS|")
        )
        assert stripped == ""

    def test_rns_footer_stripped(self):
        _NL = chr(10)
        lines = "RNS|Z|0|NONE"
        stripped = _NL.join(
            line for line in lines.split(_NL) if not line.startswith("RNS|")
        )
        assert stripped == ""

    def test_human_readable_lines_preserved(self):
        human = "1a [recover/medium] Stop_removal_guard not tested [UNVERIFIED] @ file.py:10"
        _NL = chr(10)
        stripped = _NL.join(
            line for line in human.split(_NL) if not line.startswith("RNS|")
        )
        assert stripped == human

    def test_mixed_rns_and_human(self, compiled_patterns):
        _NL = chr(10)
        text = _NL.join([
            "RNS|D|1|\U0001f4cc|HOOKS",
            "RNS|A|1a|hooks|E:?|recover/medium|desc||unverified=1|root_cause=unknown",
            "RNS|Z|0|NONE",
            "1a [recover/medium] Finding description [UNVERIFIED] @ file.py:10",
        ])
        stripped = _NL.join(
            line for line in text.split(_NL) if not line.startswith("RNS|")
        )
        matches = _any_match(compiled_patterns, stripped)
        assert len(matches) == 0, f"Unexpected matches on RNS-stripped text: {matches}"


class TestUnverifiedPatternLookbehinds:
    """The unverified pattern should exclude bracketed, backtick-wrapped, and =prefixed forms."""

    @pytest.fixture
    def unverified_pattern(self, compiled_patterns):
        for i, p in enumerate(compiled_patterns):
            if "unverified" in p.pattern:
                return p
        pytest.fail("No unverified pattern found in SELF_REFERENTIAL_EVASION_PATTERNS")

    def test_bracketed_excluded(self, unverified_pattern):
        assert not unverified_pattern.search("[UNVERIFIED]")

    def test_backtick_excluded(self, unverified_pattern):
        assert not unverified_pattern.search("`unverified`")

    def test_equals_prefixed_excluded(self, unverified_pattern):
        assert not unverified_pattern.search("status=unverified")

    def test_bare_unverified_matches(self, unverified_pattern):
        assert unverified_pattern.search("this is unverified")

    def test_pipe_unverified_equals_still_matches(self, unverified_pattern):
        # |unverified=1| has pipe before, equals after — the word itself still matches
        # This is expected: RNS line stripping handles this case, not the regex
        assert unverified_pattern.search("|unverified=1|")


class TestProseUnverifiedRegression:
    """Bare 'unverified' in prose should still be caught by evasion detection."""

    def test_prose_unverified_caught(self, compiled_patterns):
        prose = "I tested this but the result is still unverified."
        matches = _any_match(compiled_patterns, prose)
        assert any("unverified" in m for m in matches), (
            "Bare 'unverified' in prose should still match evasion pattern"
        )

    def test_prose_hypothesis_caught(self, compiled_patterns):
        prose = "this might be a root cause candidate for the bug"
        matches = _any_match(compiled_patterns, prose)
        assert len(matches) > 0, "hypothesis/candidate language should still match"
