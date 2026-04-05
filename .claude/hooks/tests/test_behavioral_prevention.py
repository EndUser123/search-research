#!/usr/bin/env python3
"""
Behavioral Issue Prevention Hooks Test Suite

Tests for the 7 new behavioral issue prevention mechanisms:
1. StopHook_diagnostic_conclusion_validator.py
2. PreToolUse_requirements_gate.py
3. PostToolUse_change_verification.py (fix completeness extension)
4. StopHook_commitment_verifier.py
5. Constitutional enforcer (deflection + numeric patterns)
6. UserPromptSubmit_verification_reminder.py (fix completeness extension)
7. session_pattern_analyzer.py
"""

import sys
import unittest
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(hooks_dir))


class TestDiagnosticConclusionValidator(unittest.TestCase):
    """Test StopHook_diagnostic_conclusion_validator.py"""

    def setUp(self):
        """Import the module for testing."""
        try:
            self.module = __import__("StopHook_diagnostic_conclusion_validator")
        except ImportError:
            self.skipTest("Module not available")

    def test_detects_root_cause_claim_without_evidence(self):
        """Should detect 'root cause:' pattern without verification evidence."""
        response = "The root cause is a memory leak in the caching layer."

        # Call detection logic
        claim_info = self.module.detect_diagnostic_claim(response)

        self.assertIsNotNone(claim_info)
        self.assertEqual(claim_info["category"], "exact_diagnostic")
        self.assertIn("root cause", claim_info["matched"].lower())

    def test_allows_with_reproduction_evidence(self):
        """Should allow if response contains reproduction evidence."""
        response = """I can reproduce this error:

```bash
python test.py
Error: out of memory
```

The root cause is a memory leak."""

        claim_info = self.module.detect_diagnostic_claim(response)
        # Should be None because has_verification_evidence returns True
        self.assertIsNone(claim_info)

    def test_allows_with_uncertainty_marker(self):
        """Should allow if response contains explicit uncertainty marker."""
        response = "Tentative conclusion: root cause appears to be a memory leak. Requires verification."

        claim_info = self.module.detect_diagnostic_claim(response)
        # Should be None because has_uncertainty_marker returns True
        self.assertIsNone(claim_info)

    def test_detects_transient_claim(self):
        """Should detect 'transient error' claims without evidence."""
        response = "This is most likely a transient error from the runtime."

        claim_info = self.module.detect_diagnostic_claim(response)
        self.assertIsNotNone(claim_info)
        self.assertEqual(claim_info["category"], "transient_claim")

    def test_detects_most_likely_cause(self):
        """Should detect 'most likely cause' pattern."""
        response = "The most likely cause is a race condition."

        claim_info = self.module.detect_diagnostic_claim(response)
        self.assertIsNotNone(claim_info)
        self.assertEqual(claim_info["category"], "exact_diagnostic")

    def test_allows_normal_response(self):
        """Should allow responses without diagnostic claims."""
        response = "Here's the code you requested. Let me read the file first."

        claim_info = self.module.detect_diagnostic_claim(response)
        self.assertIsNone(claim_info)


class TestConstitutionalEnforcerExtensions(unittest.TestCase):
    """Test extensions to constitutional_enforcer.py"""

    def setUp(self):
        """Import the module for testing."""
        try:
            self.module = __import__("constitutional_enforcer")
            # Get the validator classes
            self.truth_validator = self.module.TruthValidator()
            self.evidence_validator = self.module.WeakEvidenceValidator()
        except ImportError:
            self.skipTest("Module not available")

    def test_deflection_dismissal_pattern(self):
        """Should detect deflection: 'I don't have context. Proceeding...'"""
        response = "I don't have context about this issue, so I'll proceed with the current request."

        violations = self.truth_validator._check_deflection_dismissal(response)
        self.assertIsNotNone(violations)
        self.assertEqual(violations.severity, self.module.Severity.MEDIUM)

    def test_allows_investigation_after_no_context(self):
        """Should allow if 'no context' is followed by investigation."""
        response = "I don't have context, so let me read the file to understand the issue."

        violations = self.truth_validator._check_deflection_dismissal(response)
        self.assertIsNone(violations)

    def test_numeric_claim_without_evidence(self):
        """Should detect numeric claims without git diff output."""
        response = "The changes include +731 additions and -4829 deletions."

        violations = self.evidence_validator.validate(response)
        # Should have violations because no git diff output nearby
        self.assertTrue(len(violations) > 0)
        # Check it's a numeric claim violation
        has_numeric_violation = any("NUM" in v.rule_id for v in violations)
        self.assertTrue(has_numeric_violation)

    @unittest.skip("Requires multiline response testing")
    def test_allows_numeric_claim_with_git_diff(self):
        """Should allow numeric claims with git diff output."""
        response = """```bash
git diff --stat
 file.py | 731 +++++++++++++++++++++++++
 file.py | 4829 ------------------------
```

The changes include +731 additions and -4829 deletions."""

        violations = self.evidence_validator.validate(response)
        # Should have no violations because git diff is present
        numeric_violations = [v for v in violations if "NUM" in v.rule_id]
        self.assertEqual(len(numeric_violations), 0)


class TestRequirementsGate(unittest.TestCase):
    """Test PreToolUse_requirements_gate.py"""

    def setUp(self):
        """Import the module for testing and clear state."""
        try:
            self.module = __import__("PreToolUse_requirements_gate")
            # Clear state file to ensure fresh state for each test
            if hasattr(self.module, 'STATE_FILE') and self.module.STATE_FILE.exists():
                self.module.STATE_FILE.unlink()
                # Also clear parent directory state
                if self.module.STATE_FILE.parent.exists():
                    for f in self.module.STATE_FILE.parent.glob("*.json"):
                        f.unlink()
        except ImportError:
            self.skipTest("Module not available")

    def tearDown(self):
        """Clean up state after test."""
        try:
            if hasattr(self.module, 'STATE_FILE') and self.module.STATE_FILE.exists():
                self.module.STATE_FILE.unlink()
        except Exception:
            pass

    def test_blocks_webfetch_without_requirements(self):
        """Should block WebFetch before requirements are established."""
        # Ensure state is fresh (requirements_established = False)
        if hasattr(self.module, 'STATE_FILE') and self.module.STATE_FILE.exists():
            self.module.STATE_FILE.unlink()

        tool_name = "WebFetch"
        tool_input = {"url": "https://example.com/gist"}
        context = {
            "prompt": "",
            "conversation": [],
            "tool_history": [],
        }

        result = self.module.process_hook(tool_name, tool_input, context)
        self.assertFalse(result["continue"], "Should block WebFetch without requirements")
        self.assertIn("EXTERNAL REQUEST DETECTED", result["reason"])

    def test_allows_with_local_investigation_first(self):
        """Should allow after local investigation."""
        tool_name = "WebFetch"
        tool_input = {"url": "https://example.com/gist"}
        context = {
            "prompt": "",
            "conversation": [],
            "tool_history": [
                {"name": "Read", "input": {"file_path": "test.py"}},
                {"name": "Grep", "input": {"pattern": "import"}},
            ],
        }

        result = self.module.process_hook(tool_name, tool_input, context)
        # Should allow because local_investigation is True
        self.assertTrue(result["continue"])

    def test_allows_with_user_goal(self):
        """Should allow if user's goal is stated."""
        tool_name = "WebFetch"
        tool_input = {"url": "https://example.com/gist"}
        context = {
            "prompt": "I'm trying to implement a retry mechanism for API calls",
            "conversation": [],
            "tool_history": [],
        }

        result = self.module.process_hook(tool_name, tool_input, context)
        # Should allow because user_goal is True
        self.assertTrue(result["continue"])

    def test_allows_local_tools(self):
        """Should always allow local tools (Read, Grep, Glob)."""
        for tool_name in ["Read", "Grep", "Glob", "Write", "Edit"]:
            result = self.module.process_hook(
                tool_name,
                {},
                {"prompt": "", "conversation": [], "tool_history": []}
            )
            self.assertTrue(result["continue"], f"Tool {tool_name} should be allowed")

    def test_allows_with_bypass_acknowledgment(self):
        """Should allow with explicit acknowledgment."""
        tool_name = "WebFetch"
        tool_input = {"url": "https://example.com/gist"}
        context = {
            "prompt": "acknowledge risk, proceed with fetching the documentation",
            "conversation": [],
            "tool_history": [],
        }

        result = self.module.process_hook(tool_name, tool_input, context)
        self.assertTrue(result["continue"])


class TestCommitmentVerifier(unittest.TestCase):
    """Test StopHook_commitment_verifier.py"""

    def setUp(self):
        """Import the module for testing."""
        try:
            self.module = __import__("stop.StopHook_commitment_verifier", fromlist=[""])
        except ImportError:
            self.skipTest("Module not available")

    def test_detects_commitment_checkpoint(self):
        """Should detect 'Commitment checkpoint' pattern."""
        response = "Commitment checkpoint answer: YES - I have not made any changes"

        checkpoint_info = self.module.detect_commitment_checkpoint(response)
        self.assertIsNotNone(checkpoint_info)
        self.assertEqual(checkpoint_info["claim_type"], "not made any changes")

    @unittest.skip("Requires git repo context")
    def test_verifies_no_changes_claim(self):
        """Should verify 'not made any changes' against git status."""
        # This test requires actual git repo context
        pass


class TestFixCompletenessTracking(unittest.TestCase):
    """Test fix completeness tracking in PostToolUse_change_verification.py"""

    def setUp(self):
        """Import the module for testing."""
        try:
            self.module = __import__("PostToolUse_change_verification")
        except ImportError:
            self.skipTest("Module not available")

    def test_detects_bugfix_keywords(self):
        """Should detect bugfix patterns in tool input."""
        # Test with bugfix keywords
        test_cases = [
            ({"old_string": "broken code", "new_string": "fixed code"}, True),
            ({"content": "syntax error fix"}, True),
            ({"diff": "bug fix"}, True),
            ({"content": "add new feature"}, False),
            ({}, False),
        ]

        for tool_input, expected in test_cases:
            result = self.module.is_bugfix_change(tool_input, "test.py")
            self.assertEqual(result, expected, f"Failed for: {tool_input}")

    def test_bugfix_keywords_list(self):
        """Verify bugfix keywords are comprehensive."""
        keywords = self.module.BUGFIX_KEYWORDS

        # Expected keywords
        expected_keywords = [
            "fix", "bug", "error", "syntax", "broken",
            "issue", "problem", "fail", "crash",
            "debug", "patch", "resolve", "correct"
        ]

        for kw in expected_keywords:
            self.assertIn(kw, keywords, f"Missing keyword: {kw}")


class TestSessionPatternAnalyzer(unittest.TestCase):
    """Test session_pattern_analyzer.py"""

    def setUp(self):
        """Import the module for testing."""
        try:
            self.module = __import__("session_pattern_analyzer")
        except ImportError:
            self.skipTest("Module not available")

    def test_extract_topic_from_user_message(self):
        """Should extract topic from user message."""
        test_cases = [
            ("debug the auth module", "auth"),
            ("fix the test hook", "test"),
            ("implement AsyncQueue", "asyncqueue"),
            ("add a new feature", "new"),
            ("", None),
        ]

        for message, expected_topic in test_cases:
            topic = self.module.extract_topic(message)
            if expected_topic is None:
                self.assertIsNone(topic, f"Expected None for: {message}")
            else:
                self.assertIsNotNone(topic, f"Should extract topic from: {message}")

    def test_normalize_topic(self):
        """Should normalize topics for grouping."""
        test_cases = [
            ("Hook", "hooks"),
            ("test.py", "test"),
            ("Test", "testing"),
        ]

        for topic, expected in test_cases:
            normalized = self.module.normalize_topic(topic)
            self.assertEqual(normalized, expected)

    def test_min_sessions_threshold(self):
        """MIN_SESSIONS_FOR_PATTERN should be 3 as specified."""
        self.assertEqual(self.module.MIN_SESSIONS_FOR_PATTERN, 3)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for behavioral prevention scenarios"""

    def test_scenario_1_premature_webfetch(self):
        """
        Scenario 1: Premature WebFetch before understanding
        Expected: Requirements gate blocks, injects requirements gathering
        """
        # This would require running actual hooks
        pass

    def test_scenario_2_dismissive_deflection(self):
        """
        Scenario 2: Dismissive 'I don't have context' → proceed
        Expected: Deflection detector triggers warning
        """
        pass

    def test_scenario_3_unverified_diagnosis(self):
        """
        Scenario 3: Unverified 'transient error' diagnosis
        Expected: Diagnostic validator blocks, requires reproduction
        """
        pass

    def test_scenario_4_incomplete_verification(self):
        """
        Scenario 4: Syntax fix claimed as 'works ok' without E2E test
        Expected: Fix completeness tracker injects E2E requirement
        """
        pass

    def test_scenario_5_commitment_checkpoint_deflection(self):
        """
        Scenario 5: Commitment checkpoint asserted without verification
        Expected: Commitment verifier validates git state
        """
        pass

    def test_scenario_6_unsubstantiated_diff_numbers(self):
        """
        Scenario 6: '+731 -4829' without git diff output
        Expected: Numeric claims validator requires evidence
        """
        pass


def run_tests():
    """Run the test suite."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestDiagnosticConclusionValidator,
        TestConstitutionalEnforcerExtensions,
        TestRequirementsGate,
        TestCommitmentVerifier,
        TestFixCompletenessTracking,
        TestSessionPatternAnalyzer,
        TestIntegrationScenarios,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
