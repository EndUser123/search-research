#!/usr/bin/env python3
"""
Tests for Lazy Workaround Detection Gate
"""

import sys
import unittest
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from Stop_lazy_workaround_gate import check_lazy_workarounds


class TestLazyWorkaroundDetection(unittest.TestCase):
    """Test that lazy workaround suggestions are blocked"""

    def test_accept_duplicate_as_visible_logging_blocked(self):
        """The exact pattern from your issue should be blocked"""
        response = "Let's keep current changes and accept the duplicate bars as visible logging"
        result = check_lazy_workarounds(response)

        self.assertEqual(result["decision"], "block")
        self.assertIn("lazy workaround", result["message"].lower())
        self.assertIn("accepting bug as feature", result["message"].lower())

    def test_live_with_bug_blocked(self):
        """'Live with it' suggestions should be blocked"""
        response = "We can just live with this race condition, it's rare"
        result = check_lazy_workarounds(response)

        self.assertEqual(result["decision"], "block")
        self.assertIn("technical debt", result["message"].lower())

    def test_duplicate_is_fine_blocked(self):
        """'Duplicate is fine' should be blocked"""
        response = "The duplicate bars are fine, that's expected behavior"
        result = check_lazy_workarounds(response)

        self.assertEqual(result["decision"], "block")
        self.assertIn("ignoring duplication", result["message"].lower())

    def test_cosmetic_bug_dismissal_blocked(self):
        """Calling functional bugs 'cosmetic' should be blocked"""
        response = "This is just a cosmetic issue, we can ignore it"
        result = check_lazy_workarounds(response)

        self.assertEqual(result["decision"], "block")
        self.assertIn("dismissing", result["message"].lower())

    def test_proper_investigation_allowed(self):
        """Root cause investigation should be allowed"""
        response = "Let me trace where the duplicate tasks are created and fix the source"
        result = check_lazy_workarounds(response)

        self.assertEqual(result["decision"], "allow")

    def test_investigation_then_fix_allowed(self):
        """Proper debugging flow should be allowed"""
        response = "I'll investigate why duplicates appear and prevent the double-call"
        result = check_lazy_workarounds(response)

        self.assertEqual(result["decision"], "allow")

    def test_describing_problem_allowed(self):
        """Describing the problem is fine (without suggesting to live with it)"""
        response = "There are duplicate task bars appearing due to a race condition"
        result = check_lazy_workarounds(response)

        self.assertEqual(result["decision"], "allow")

    def test_workaround_fine_blocked(self):
        """'Workaround is fine' should be blocked"""
        response = "The workaround is fine, we don't need to fix the actual issue"
        result = check_lazy_workarounds(response)

        self.assertEqual(result["decision"], "block")

    def test_not_worth_fixing_blocked(self):
        """'Not worth fixing' should be blocked"""
        response = "This bug isn't worth fixing, let's just document it"
        result = check_lazy_workarounds(response)

        self.assertEqual(result["decision"], "block")


class TestLazyPatternCoverage(unittest.TestCase):
    """Test that all lazy patterns are covered"""

    def test_accept_as_feature_pattern(self):
        """Test accept-as-feature pattern detection"""
        test_cases = [
            "Accept this as a feature",
            "Let's accept the duplication as visible logging",
            "We can accept this bug as intentional behavior",
        ]
        for response in test_cases:
            result = check_lazy_workarounds(response)
            self.assertEqual(result["decision"], "block",
                           f"Should block: {response}")

    def test_live_with_pattern(self):
        """Test live-with pattern detection"""
        test_cases = [
            "Just live with the bug",
            "We can live with this issue",
            "Live with the problem",
        ]
        for response in test_cases:
            result = check_lazy_workarounds(response)
            self.assertEqual(result["decision"], "block",
                           f"Should block: {response}")

    def test_duplicate_fine_pattern(self):
        """Test duplication acceptance pattern"""
        test_cases = [
            "Duplicates are fine",
            "The redundant bars are acceptable",
            "Extra tasks are expected",
        ]
        for response in test_cases:
            result = check_lazy_workarounds(response)
            self.assertEqual(result["decision"], "block",
                           f"Should block: {response}")


if __name__ == "__main__":
    unittest.main()
