import os
import sys
import unittest
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from Stop_lazy_workaround_gate import check_lazy_workarounds
from __lib.stop_gate_telemetry import clear_test_telemetry, read_telemetry


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
        """Test duplication acceptance pattern via proximity detection"""
        test_cases = [
            ("Duplicates are fine", True),
            ("The redundant bars are acceptable", True),
            ("Extra tasks are expected", True),
            # These should NOT trigger (no acceptance word near problem word)
            ("ignoring duplication in the report", False),
            ("duplicate is documented in the changelog", False),
            ("duplicates are mentioned in the README", False),
        ]
        for response, should_block in test_cases:
            result = check_lazy_workarounds(response)
            self.assertEqual(result["decision"], "block" if should_block else "allow",
                           f"{'Should block' if should_block else 'Should allow'}: {response}")


class TestProximityBoundary(unittest.TestCase):
    """Test the 8-token proximity boundary.

    Window behavior (with end = i + PROXIMITY_TOKENS + 1):
    - Forward: tokens[i+1:i+9] — 8 tokens (index i+1 through i+8), distance 1-8 BLOCK
    - Backward: tokens[i-8:i] — 8 tokens (index i-8 through i-1), distance 1-8 BLOCK
    - Distance 9+ (9+ tokens between): ALLOW

    Both directions are symmetric at PROXIMITY_TOKENS=8.
    """

    def _tokens_forward(self, n: int) -> str:
        """n filler tokens between 'duplicate' and 'fine'."""
        return "duplicate " + " ".join(f"tok{i}" for i in range(1, n + 1)) + " fine"

    def _tokens_backward(self, n: int) -> str:
        """n filler tokens between 'fine' and 'duplicate'."""
        return "fine " + " ".join(f"tok{i}" for i in range(1, n + 1)) + " duplicate"

    def test_7_tokens_forward_blocks(self):
        """7 filler tokens (distance 8) — within 8-token window."""
        text = self._tokens_forward(7)
        result = check_lazy_workarounds(text)
        self.assertEqual(result["decision"], "block", f"Should block: {text!r}")

    def test_8_tokens_forward_allows(self):
        """8 filler tokens (distance 9) — outside 8-token window."""
        text = self._tokens_forward(8)
        result = check_lazy_workarounds(text)
        self.assertEqual(result["decision"], "allow", f"Should allow: {text!r}")

    def test_9_tokens_forward_allows(self):
        """9 filler tokens (distance 10) — outside 8-token window."""
        text = self._tokens_forward(9)
        result = check_lazy_workarounds(text)
        self.assertEqual(result["decision"], "allow", f"Should allow: {text!r}")

    def test_7_tokens_backward_blocks(self):
        """7 filler tokens (distance 8) — within 8-token window."""
        text = self._tokens_backward(7)
        result = check_lazy_workarounds(text)
        self.assertEqual(result["decision"], "block", f"Should block: {text!r}")

    def test_8_tokens_backward_allows(self):
        """8 filler tokens (distance 9) — outside 8-token window."""
        text = self._tokens_backward(8)
        result = check_lazy_workarounds(text)
        self.assertEqual(result["decision"], "allow", f"Should allow: {text!r}")

    def test_9_tokens_backward_allows(self):
        """9 filler tokens (distance 10) — outside 8-token window."""
        text = self._tokens_backward(9)
        result = check_lazy_workarounds(text)
        self.assertEqual(result["decision"], "allow", f"Should allow: {text!r}")


class TestReportContextAllowPatterns(unittest.TestCase):
    """Report/implementation context: behavior descriptions should not be blocked."""

    def test_two_signals_intentional_allowed(self):
        """Describing dual-signal suppression as intentional behavior is not lazy."""
        response = (
            "The OR combination means two independent signals suppress the advisory. "
            "This is intentional — both user framing and response style point toward "
            "non-exhaustive coverage."
        )
        result = check_lazy_workarounds(response)
        self.assertEqual(result["decision"], "allow")

    def test_advisory_suppression_intentional_allowed(self):
        """Explaining that suppression is correct behavior is not lazy."""
        response = "The advisory correctly suppresses in both cases — there is no bug to fix."
        result = check_lazy_workarounds(response)
        self.assertEqual(result["decision"], "allow")

    def test_edge_case_to_monitor_allowed(self):
        """Describing an edge case to monitor is not lazy workaround."""
        response = "The edge case to monitor is whether phrase sets drift out of sync over time."
        result = check_lazy_workarounds(response)
        self.assertEqual(result["decision"], "allow")

    def test_not_a_workaround_allowed(self):
        """Describing something as not a workaround is not lazy."""
        response = "There is no redundant execution path — this is not a workaround."
        result = check_lazy_workarounds(response)
        self.assertEqual(result["decision"], "allow")

    def test_suppression_is_correct_allowed(self):
        """Describing suppression as correct is not lazy."""
        response = "Suppression is correct when either signal fires — this is expected behavior."
        result = check_lazy_workarounds(response)
        self.assertEqual(result["decision"], "allow")

    def test_real_duplicate_workaround_still_blocked(self):
        """Real duplicate-workaround language is still blocked in report context."""
        response = (
            "just accept the duplicate advisory — the duplicate bars are fine, "
            "that's expected behavior."
        )
        result = check_lazy_workarounds(response)
        self.assertEqual(result["decision"], "block")

    def test_accept_bug_as_feature_still_blocked(self):
        """Accept-bug-as-feature language still blocked even in report context."""
        response = "We should accept this bug as expected behavior."
        result = check_lazy_workarounds(response)
        self.assertEqual(result["decision"], "block")


class TestTelemetryFields(unittest.TestCase):
    """Verify telemetry fields are written correctly on block decisions."""

    def setUp(self):
        clear_test_telemetry()
        os.environ["STOP_TELEMETRY"] = "1"

    def tearDown(self):
        clear_test_telemetry()
        os.environ.pop("STOP_TELEMETRY", None)

    def test_telemetry_matched_pattern_logs_correctly(self):
        """matched_pattern should log the actual regex that matched."""
        import json

        response = "The workaround is fine, we don't need to fix the actual issue"
        result = check_lazy_workarounds(response)
        self.assertEqual(result["decision"], "block")

        entries = read_telemetry()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["decision"], "block")
        self.assertEqual(entry["gate"], "lazy_workaround_gate")
        self.assertIn("extra", entry)
        self.assertIn("matched_pattern", entry["extra"])
        # Should be the accepting_workaround_over_fix pattern
        self.assertIn("workaround", entry["extra"]["matched_pattern"])

    def test_telemetry_investigation_bypass_true(self):
        """investigation_bypass should be True when investigation intent is present."""
        import json

        # Response has bypass phrase but still triggers proximity detection
        # The "duplicate" is near "fine" so it would block, but investigation intent suppresses
        response = (
            "Let me trace where the duplicate is created. "
            "The duplicate bars are fine in this case, that's expected."
        )
        result = check_lazy_workarounds(response)
        # The investigation intent bypasses the block
        self.assertEqual(result["decision"], "allow")
        # Allow path does NOT write telemetry
        self.assertEqual(len(read_telemetry()), 0)

    def test_telemetry_investigation_bypass_false(self):
        """investigation_bypass should be False on genuine blocks."""
        import json

        response = "We can live with this race condition, it's rare"
        result = check_lazy_workarounds(response)
        self.assertEqual(result["decision"], "block")

        entries = read_telemetry()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["decision"], "block")
        self.assertIn("extra", entry)
        self.assertIn("investigation_bypass", entry["extra"])
        self.assertFalse(entry["extra"]["investigation_bypass"])

    def test_telemetry_response_snippet_captures_context(self):
        """response_snippet should be the last 200 chars of the response."""
        import json

        long_response = (
            "We should accept the duplicate bars as visible logging. "
            "The workaround is fine, we don't need to fix the actual issue. "
            "This is a long response that exceeds 200 characters to verify truncation."
        )
        result = check_lazy_workarounds(long_response)
        self.assertEqual(result["decision"], "block")

        entries = read_telemetry()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry["decision"], "block")
        self.assertIn("extra", entry)
        self.assertIn("response_snippet", entry["extra"])
        # Snippet should be last 200 chars
        self.assertEqual(entry["extra"]["response_snippet"], long_response[-200:])
        # Snippet should be a string
        self.assertIsInstance(entry["extra"]["response_snippet"], str)

    def test_telemetry_no_match_allow_path_no_write(self):
        """Allow path should NOT write telemetry (fields only on block path)."""
        response = "Let me trace where the problem originates and fix it properly."
        result = check_lazy_workarounds(response)
        self.assertEqual(result["decision"], "allow")
        self.assertEqual(len(read_telemetry()), 0)

    def test_telemetry_proximity_match_pattern_format(self):
        """Proximity-based matches should log a synthetic pattern identifier."""
        import json

        response = "The duplicate bars are fine, that's expected behavior"
        result = check_lazy_workarounds(response)
        self.assertEqual(result["decision"], "block")

        entries = read_telemetry()
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertIn("extra", entry)
        self.assertIn("matched_pattern", entry["extra"])
        # Proximity pattern format: "proximity:'duplicate'+'fine'"
        self.assertTrue(entry["extra"]["matched_pattern"].startswith("proximity:"))


if __name__ == "__main__":
    unittest.main()
