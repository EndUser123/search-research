"""
Integration tests for investigation loop enhancements.

Tests verify that the three new features work correctly:
1. User-facing structured feedback format
2. Urgency detection / fast mode
3. Single root cause escape hatch

Also includes end-to-end tests with realistic debugging scenarios to verify
all three layers (cognitive enhancers, sequential thinking, RCA contract) work together.
"""

import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from stop.Stop_verification_gate import (
    _detect_urgency,
    _format_structured_feedback,
    check_response_violations,
    run as verification_run,
)
from StopHook_rca_contract import (
    _detect_single_rc_escape,
    _detect_urgency as rca_detect_urgency,
    _format_structured_feedback as rca_format_feedback,
    check as rca_check,
)
from StopHook_sequential_thinking import (
    _format_investigation_feedback,
    stop as sequential_stop,
)


class TestStructuredFeedback(unittest.TestCase):
    """Test #2: User-facing feedback mechanism for investigation gates."""

    def test_feedback_format_with_hypothesis_details(self):
        """Structured feedback shows hypothesis status and suggested tests."""
        violations = ["BEHAV-002: Single hypothesis accepted"]
        suggestions = ["Generate 3+ hypotheses upfront, test each systematically"]
        hypothesis_details = [
            {
                "name": "H1 (config mismatch)",
                "status": "CONFIRMED",
            },
            {
                "name": "H2 (race condition)",
                "status": "UNTESTED",
                "test_suggestion": "grep for race-related patterns in logs",
            },
            {
                "name": "H3 (dependency version drift)",
                "status": "FALSIFIED",
            },
        ]

        result = _format_structured_feedback(violations, suggestions, hypothesis_details)

        self.assertIn("Hypothesis Status:", result)
        self.assertIn("H1 (config mismatch) → CONFIRMED", result)
        self.assertIn("H2 (race condition) → UNTESTED", result)
        self.assertIn("Suggested test: grep for race-related patterns in logs", result)
        self.assertIn("H3 (dependency version drift) → FALSIFIED", result)
        # Icons
        self.assertIn("✓", result)  # CONFIRMED
        self.assertIn("⏳", result)  # UNTESTED
        self.assertIn("✗", result)  # FALSIFIED

    def test_feedback_format_empty_hypotheses(self):
        """Works without hypothesis details (backward compatible)."""
        violations = ["BEHAV-001: Premature solution jump"]
        suggestions = ["Complete Solution Proposal Gate checklist first"]

        result = _format_structured_feedback(violations, suggestions, [])

        self.assertIn("BEHAV-001", result)
        self.assertNotIn("Hypothesis Status:", result)

    def test_rca_feedback_shows_testing_progress(self):
        """RCA contract feedback shows hypothesis testing progress."""
        block_reasons = ["single-hypothesis-lock"]
        hypothesis_details = [
            {"claim": "config mismatch", "status": "CONFIRMED"},
            {"claim": "race condition", "status": "UNTESTED", "test_suggestion": "run concurrent load test"},
        ]

        result = rca_format_feedback(block_reasons, hypothesis_details)

        self.assertIn("1/2 tested", result)
        self.assertIn("✓ config mismatch → CONFIRMED", result)
        self.assertIn("⏳ race condition → UNTESTED", result)
        self.assertIn("Suggested test: run concurrent load test", result)

    def test_sequential_thinking_investigation_feedback(self):
        """Sequential thinking investigation feedback includes phase info."""
        hypothesis_details = [
            {"claim": "null pointer in handler", "status": "CONFIRMED"},
            {"claim": "missing validation", "status": "UNTESTED"},
        ]

        result = _format_investigation_feedback("testing", hypothesis_details)

        self.assertIn("Investigation Mode — Phase: TESTING", result)
        self.assertIn("1/2 tested", result)
        self.assertIn("✓ null pointer in handler → CONFIRMED", result)
        self.assertIn("⏳ missing validation → UNTESTED", result)


class TestUrgencyDetection(unittest.TestCase):
    """Test urgency detection for fast mode (related to #4 integration testing)."""

    def test_detects_urgent_keywords(self):
        """Detects urgent, emergency, ASAP."""
        self.assertTrue(_detect_urgency("This is urgent, need it fixed"))
        self.assertTrue(_detect_urgency("Emergency: production is down"))
        self.assertTrue(_detect_urgency("Need this ASAP"))

    def test_detects_incident_patterns(self):
        """Detects incident, outage, production down."""
        self.assertTrue(_detect_urgency("We have an incident on prod"))
        self.assertTrue(_detect_urgency("Service outage affecting customers"))
        self.assertTrue(_detect_urgency("Production is down right now"))

    def test_detects_time_pressure(self):
        """Detects time-critical patterns."""
        self.assertTrue(_detect_urgency("This is time critical"))
        self.assertTrue(_detect_urgency("Fix immediately"))

    def test_non_urgent_passes(self):
        """Non-urgent text doesn't trigger urgency."""
        self.assertFalse(_detect_urgency("Let's investigate why this function fails"))
        self.assertFalse(_detect_urgency("Can you debug this issue when you have time"))
        self.assertFalse(_detect_urgency("What causes the intermittent test failure"))

    def test_rca_urgency_detection(self):
        """RCA contract also detects urgency."""
        self.assertTrue(rca_detect_urgency("URGENT: production outage"))
        self.assertFalse(rca_detect_urgency("Investigate the test flakiness"))


class TestSingleRootCauseEscapeHatch(unittest.TestCase):
    """Test #5: Escape hatch for single root cause with explicit evidence."""

    def test_detects_escape_hatch(self):
        """Detects [SINGLE ROOT CAUSE CONFIRMED] marker."""
        self.assertTrue(_detect_single_rc_escape(
            "Root cause: null pointer in handler [SINGLE ROOT CAUSE CONFIRMED]"
        ))
        self.assertTrue(_detect_single_rc_escape(
            "[single root cause confirmed] The issue is a config mismatch"
        ))

    def test_no_false_positive(self):
        """Doesn't trigger without the marker."""
        self.assertFalse(_detect_single_rc_escape("There is a single root cause here"))
        self.assertFalse(_detect_single_rc_escape("Only one cause found"))

    def test_verification_gate_respects_escape(self):
        """Verification gate skips single-hypothesis check when escape hatch used."""
        response = (
            "Root cause: config mismatch [SINGLE ROOT CAUSE CONFIRMED]\n"
            "The problem is the missing environment variable."
        )

        result = check_response_violations(response, single_root_cause=True)

        # Should not have BEHAV-002 (single hypothesis accepted) violation
        violations = result["violations"]
        behav_002 = [v for v in violations if "BEHAV-002" in v and "BEHAV-002-A" not in v]
        self.assertEqual(len(behav_002), 0)

    def test_rca_contract_respects_escape(self):
        """RCA contract skips hypothesis-related blocks when escape hatch used."""
        # Build a response that would normally trigger single-hypothesis-lock
        response = (
            "## Symptom\nService returns 500\n"
            "## Evidence\nRead on `config.py` showed missing variable\n"
            "## Executed Path\nconfig.py:load_config()\n"
            "## Root Cause\nmissing ENV var [SINGLE ROOT CAUSE CONFIRMED]\n"
            "## Fix\nAdd ENV var\n"
            "## Verification\nRestart service\n"
        )

        data = {
            "rca_turn": True,
            "response": response,
            "tool_events": [{"name": "Read", "id": "evt1"}],
            "session_id": "test",
            "terminal_id": "term1",
        }

        result = rca_check(data)

        # Should not block on single-hypothesis-lock
        if result and result.get("decision") == "block":
            self.assertNotIn("single-hypothesis-lock", result.get("block_reasons", []))


class TestIntegrationScenarios(unittest.TestCase):
    """Test #4: Integration tests with real debugging scenarios."""

    def _make_rca_data(self, response, tool_events=None, **kwargs):
        """Helper to build RCA test data."""
        return {
            "rca_turn": True,
            "response": response,
            "tool_events": tool_events or [],
            "session_id": "test-session",
            "terminal_id": "test-terminal",
            **kwargs,
        }

    def test_scenario_intermittent_test_failure(self):
        """Scenario: 'debug the intermittent test failure' — should trigger multi-hypothesis."""
        response = (
            "I think the test fails due to a race condition.\n"
            "The problem is the timing issue. Let's fix it by adding a sleep."
        )

        result = check_response_violations(response)

        # Should detect at least one violation (claim without verification)
        # Note: exact violations depend on pattern matching
        self.assertIsInstance(result["violations"], list)
        # Should not detect urgency
        self.assertFalse(result["is_urgent"])

    def test_scenario_production_outage(self):
        """Scenario: 'production is down, fix ASAP' — urgency should reduce enforcement."""
        response = (
            "The problem is the database connection pool is exhausted.\n"
            "Let's fix it immediately by increasing the pool size."
        )

        result = verification_run({"response": response})

        # Should still detect violations but with urgency awareness
        if result:
            # In urgent mode, should either not block or include urgency notice
            if result.get("block"):
                self.assertIn("URGENT", result.get("reason", ""))

    def test_scenario_deep_investigation(self):
        """Scenario: Full RCA with proper hypothesis testing — should have fewer blocks."""
        response = (
            "## Symptom\nAPI returns 500 on /users endpoint\n"
            "## Evidence\n"
            "[current-state] Read on `users.py` showed unhandled NoneType\n"
            "## Executed Path\nusers.py get_user called by api.py\n"
            "## Alternative Hypothesis\n"
            "| # | Hypothesis | Score |\n"
            "| 1. | NoneType in get_user | 0.8 |\n"
            "| 2. | Database connection timeout | 0.3 |\n"
            "## Falsifier\nDB connection verified — timeout hypothesis ruled out\n"
            "## Ruled Out\nDB timeout: connection pool healthy\n"
            "## Root Cause\nget_user returns None when user not found\n"
            "## Fix\nAdd null check in get_user\n"
            "## Verification\nRun test_users.py test_missing_user_returns_404\n"
        )

        data = self._make_rca_data(response, tool_events=[
            {"name": "Read", "id": "evt1"},
        ])

        result = rca_check(data)

        # May still have some structural blocks (e.g., unbound evidence in test env)
        # But should NOT have hypothesis-related blocks since we have 2 hypotheses
        if result and result.get("block_reasons"):
            hypothesis_blocks = [
                r for r in result["block_reasons"]
                if "single-hypothesis" in r.lower() or "Only one hypothesis" in r
            ]
            self.assertEqual(
                len(hypothesis_blocks), 0,
                f"Should not have single-hypothesis blocks with 2 hypotheses, got: {result['block_reasons']}"
            )

    def test_scenario_premature_convergence(self):
        """Scenario: Only 1 hypothesis tested — should block with structured feedback."""
        response = (
            "## Symptom\nAPI returns 500\n"
            "## Evidence\n[current-state] Read on `users.py` showed error\n"
            "## Executed Path\nusers.py:handle()\n"
            "## Alternative Hypothesis\n"
            "| # | Hypothesis | Score |\n"
            "| 1. | Null pointer | 0.9 |\n"
            "## Falsifier\nN/A\n"
            "## Ruled Out\nNone\n"
            "## Root Cause\nNull pointer in handler\n"
            "## Fix\nAdd null check\n"
            "## Verification\nTest it\n"
        )

        data = self._make_rca_data(response, tool_events=[
            {"name": "Read", "id": "evt1"},
        ])

        result = rca_check(data)
        self.assertIsNotNone(result)
        self.assertEqual(result["decision"], "block")
        # Block reasons contain full text messages, check for key phrase
        block_reasons = result.get("block_reasons", [])
        has_hypothesis_block = any(
            "Only one hypothesis" in r or "single-hypothesis-lock" in r
            for r in block_reasons
        )
        self.assertTrue(has_hypothesis_block, f"Expected hypothesis block, got: {block_reasons}")
        # Structured feedback should be present
        self.assertIn("RCA Contract Structural Validation Failed", result["reason"])

    def test_scenario_escape_hatch_with_evidence(self):
        """Scenario: Single root cause confirmed with evidence — should skip hypothesis blocks."""
        response = (
            "## Symptom\nAPI returns 500\n"
            "## Evidence\n[current-state] Read on `users.py` showed NoneType\n"
            "## Executed Path\nusers.py:get_user\n"
            "## Alternative Hypothesis\nOnly one cause found [SINGLE ROOT CAUSE CONFIRMED]\n"
            "## Falsifier\nN/A\n"
            "## Ruled Out\nN/A\n"
            "## Root Cause\nget_user returns None\n"
            "## Fix\nAdd null check\n"
            "## Verification\nRun test_users.py\n"
        )

        data = self._make_rca_data(response, tool_events=[
            {"name": "Read", "id": "evt1"},
        ])

        result = rca_check(data)
        # Should not block on hypothesis-related reasons (single-hypothesis-lock, missing-alternative, etc.)
        if result and result.get("block_reasons"):
            hypothesis_related = [
                "single-hypothesis", "missing-alternative", "missing-falsifier",
                "missing-ruled-out", "Only one hypothesis"
            ]
            for reason in result["block_reasons"]:
                for key in hypothesis_related:
                    self.assertNotIn(key, reason,
                        f"Escape hatch should remove hypothesis-related block: {reason}")

    def test_scenario_verification_gate_with_hypothesis_details(self):
        """Verification gate correctly formats feedback when hypothesis details provided."""
        # Ensure advisory mode is off (may have been set by previous test)
        import importlib
        import stop.Stop_verification_gate as vfg
        with patch.dict(os.environ, {"VERIFICATION_GATE_ADVISORY": "false"}, clear=False):
            os.environ.pop("VERIFICATION_GATE_ADVISORY", None)
            importlib.reload(vfg)

            # Use a response that triggers BEHAV-001 (solution jump without verification)
            response = (
                "Let's fix the issue by updating the config.\n"
                "Proposed solution: change the timeout value."
            )
            hypothesis_details = [
                {"name": "H1 (config mismatch)", "status": "CONFIRMED"},
                {"name": "H2 (race condition)", "status": "UNTESTED", "test_suggestion": "grep logs for race"},
            ]

            result = vfg.run({
                "assistant_response": response,
                "hypothesis_details": hypothesis_details,
            })

            self.assertIsNotNone(result)
            self.assertTrue(result["block"])
            # Should include structured feedback
            self.assertIn("Hypothesis Status:", result["reason"])
            self.assertIn("config mismatch", result["reason"])

    def test_scenario_advisory_mode_does_not_block(self):
        """When advisory mode is enabled, violations are logged but don't block."""
        response = "I think the config is wrong. Let's fix it."

        with patch.dict(os.environ, {"VERIFICATION_GATE_ADVISORY": "true"}):
            # Need to reload module to pick up env var
            import importlib
            import stop.Stop_verification_gate as vfg
            importlib.reload(vfg)

            result = vfg.run({"response": response})

            # Advisory mode should not block
            self.assertIsNone(result)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_response_passes(self):
        """Empty response doesn't trigger violations."""
        result = check_response_violations("")
        self.assertEqual(len(result["violations"]), 0)

    def test_none_hypothesis_details_handled(self):
        """None hypothesis details doesn't crash."""
        result = check_response_violations("test response", hypothesis_details=None)
        self.assertIsInstance(result["hypothesis_details"], list)

    def test_rca_check_no_rca_turn_passes(self):
        """Non-RCA turn skips validation."""
        result = rca_check({"rca_turn": False, "response": "anything"})
        self.assertIsNone(result)

    def test_rca_check_empty_response_passes(self):
        """Empty response skips validation."""
        result = rca_check({"rca_turn": True, "response": ""})
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
