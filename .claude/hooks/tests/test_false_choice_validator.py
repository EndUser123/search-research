#!/usr/bin/env python3
"""
Tests for Stop_false_choice_validator.py

Covers acceptance criteria from the handoff:
  1. Detects "or both" telltale
  2. Detects "which subset" delegation + action list
  3. Does NOT fire on genuine either/or (vs, trade-off)
  4. Does NOT fire when agent recommends "do all"
  5. Does NOT fire on short responses
"""

import sys
from pathlib import Path

_hooks_dir = Path(__file__).resolve().parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from Stop_false_choice_validator import check_false_choice


class TestTruePositiveOrBoth:
    """Pattern 1: 'or both' telltale signals independent actions."""

    def test_or_both_simple(self):
        response = (
            "I can implement the hook now, or both. Let me know which approach works for you and I will proceed accordingly."
        )
        result = check_false_choice(response)
        assert result is not None
        assert "systemMessage" in result

    def test_or_all_of_them(self):
        response = (
            "Here are the three items I identified. Should I do the first one, "
            "or all of them? The choice is yours on how to proceed with this work."
        )
        result = check_false_choice(response)
        assert result is not None
        assert "systemMessage" in result


class TestTruePositiveSubsetDelegation:
    """Pattern 2: 'which subset' / 'which of these' + action list."""

    def test_which_subset_with_list(self):
        response = (
            "Here are the items I found:\n"
            "1. Push both repos\n"
            "2. Update the wiki\n"
            "3. Build the hook\n\n"
            "Which subset would you like me to proceed with?"
        )
        result = check_false_choice(response)
        assert result is not None
        assert "systemMessage" in result

    def test_which_of_these_would_you_like(self):
        response = (
            "I found several improvements:\n"
            "- Fix the regex pattern\n"
            "- Add error handling\n"
            "- Update the documentation\n\n"
            "Which of these would you like me to do?"
        )
        result = check_false_choice(response)
        assert result is not None


class TestTruePositiveMenuDelegation:
    """Pattern 3: 'Should I do X, or Y, or Z?' with action list."""

    def test_should_i_do_option_with_list(self):
        response = (
            "I have identified three potential fixes for this issue:\n"
            "1. Option A: update the configuration\n"
            "2. Option B: refactor the handler\n"
            "3. Option C: add a new module\n\n"
            "Should I do option A, B, or C first?"
        )
        result = check_false_choice(response)
        assert result is not None


class TestTrueNegativeGenuineCompetition:
    """Does NOT fire when options genuinely compete."""

    def test_vs_pattern(self):
        response = (
            "Should we use PostgreSQL vs SQLite for this project? "
            "There is a real trade-off between them. PostgreSQL offers better "
            "concurrency but SQLite is simpler to deploy for single-user scenarios."
        )
        result = check_false_choice(response)
        assert result is None

    def test_mutually_exclusive(self):
        response = (
            "These two approaches are mutually exclusive. You can only pick one. "
            "Either option has its own set of advantages and disadvantages to consider."
        )
        result = check_false_choice(response)
        assert result is None


class TestTrueNegativeDoAll:
    """Does NOT fire when agent recommends doing everything."""

    def test_do_all_of_them(self):
        response = (
            "I found three issues to fix:\n"
            "1. Update the regex\n"
            "2. Add error handling\n"
            "3. Fix the documentation\n\n"
            "I recommend doing all of them since each has positive ROI."
        )
        result = check_false_choice(response)
        assert result is None

    def test_i_recommend_doing_all(self):
        response = (
            "These are independent improvements. I recommend doing all of them "
            "in parallel since none blocks the others."
        )
        result = check_false_choice(response)
        assert result is None


class TestTrueNegativeShortResponse:
    """Does NOT fire on short responses."""

    def test_short_response(self):
        response = "I can do both if you want."
        result = check_false_choice(response)
        assert result is None

    def test_empty_response(self):
        result = check_false_choice("")
        assert result is None


class TestEdgeCaseOrBothWithVs:
    """'or both' present but context is genuine competition."""

    def test_vs_overrides_or_both(self):
        response = (
            "Should we go with approach A vs approach B? There is a clear trade-off. "
            "Or both could be used in different contexts."
        )
        result = check_false_choice(response)
        assert result is None
