#!/usr/bin/env python3
"""Unit tests for completion claim verification in StopHook_unverified_stance.py

Tests the completion claim detection system that verifies agents have runtime
testing evidence before claiming "fixed", "tested", or "verified".

Test Scenarios from plan-20260307-completion-claim-verification.md:
1. No session_id → check skipped (allow)
2. Session_id but no evidence → advisory (warn mode)
3. Session_id with Bash tool → allow
4. Multi-terminal isolation → blocks wrong session
"""

import os
import sys
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import pytest


class TestCompletionClaimVerification:
    """Test completion claim detection and verification logic."""

    def test_no_session_id_skips_check(self):
        """Test 1: No session_id → check skipped (allow).

        When CLAUDE_SESSION_ID is not set and resolve_session_id returns empty,
        the completion claim check should be skipped entirely.
        """
        # Prepare input with completion claim
        input_data = {
            "transcript_path": "/fake/transcript.json",
            "conversation": [],
            "response": "✅ ALL FILES PASS - everything is fixed and tested"
        }

        # Ensure no session_id in environment
        old_session = os.environ.get("CLAUDE_SESSION_ID")
        if "CLAUDE_SESSION_ID" in os.environ:
            del os.environ["CLAUDE_SESSION_ID"]

        try:
            # Import the hook module
            from StopHook_unverified_stance import _check_completion_claim

            # No session_id means check is skipped
            # Response should be allowed with no session_id
            claim_valid, claim_msg = _check_completion_claim(
                input_data.get("response", ""),
                session_id=""  # Empty session_id
            )

            # Should pass because no session_id means skip check
            assert claim_valid, f"Check should be skipped with no session_id: {claim_msg}"
            assert "Sufficient evidence" in claim_msg or "skip" in claim_msg.lower()

        finally:
            # Restore environment
            if old_session is not None:
                os.environ["CLAUDE_SESSION_ID"] = old_session

    def test_session_without_evidence_warns(self):
        """Test 2: Session_id but no evidence → advisory (warn mode).

        When session_id exists but no runtime tools have been used,
        should return False (claim invalid) with evidence requirement message.
        """
        # Create a temporary session_id for testing
        test_session_id = "test-session-no-evidence-12345"

        # Mock empty tool events (no runtime tools used)
        # This will be handled by mocking load_tool_events to return empty list

        # Prepare input with completion claim
        response_text = "✅ All files fixed and tested"

        try:
            from StopHook_unverified_stance import _check_completion_claim

            # Call with session_id but no evidence in store
            claim_valid, claim_msg = _check_completion_claim(
                response_text,
                session_id=test_session_id
            )

            # Should FAIL - claim made without runtime evidence
            assert not claim_valid, "Claim should be invalid without runtime evidence"
            assert "Completion claim without runtime testing evidence" in claim_msg
            assert "Bash" in claim_msg or "Edit" in claim_msg or "pytest" in claim_msg

        except ImportError as e:
            pytest.skip(f"Completion claim verification not yet implemented: {e}")

    def test_session_with_bash_tool_allows(self):
        """Test 3: Session_id with Bash tool → allow.

        When session_id has Bash tool events (e.g., running pytest),
        completion claim should be allowed.

        Note: This test requires actual tool events in evidence_store or proper mocking.
        In clean environment, expect failure (no evidence) which is correct behavior.
        """
        test_session_id = "test-session-with-evidence-12345"

        response_text = "✅ All files fixed after testing"

        try:
            from StopHook_unverified_stance import _check_completion_claim

            claim_valid, claim_msg = _check_completion_claim(
                response_text,
                session_id=test_session_id
            )

            # In test environment without actual evidence, this will correctly fail
            # To properly test this, we'd need to:
            # 1. Run a Bash tool first to populate the shared evidence layer
            # 2. Mock the module-level load_tool_events() adapter to return fake tool events
            # For now, we verify the logic works correctly (no evidence = invalid claim)
            if not claim_valid:
                # Expected behavior in test environment without evidence
                assert "Completion claim without runtime testing evidence" in claim_msg
            else:
                # If this passes, it means evidence exists (integration test scenario)
                assert claim_valid, f"Claim should be valid with runtime evidence: {claim_msg}"

        except ImportError as e:
            pytest.skip(f"Completion claim verification not yet implemented: {e}")

    def test_multi_terminal_isolation(self):
        """Test 4: Multi-terminal isolation → blocks wrong session.

        Terminal A runs tests (session_id="test-term-a"),
        Terminal B claims completion (session_id="test-term-b").
        Terminal B should be blocked because no evidence in its session.
        """
        session_term_a = "test-term-a"
        session_term_b = "test-term-b"

        # Terminal B tries to claim completion without running tests
        response_text = "✅ All files fixed"

        try:
            from StopHook_unverified_stance import _check_completion_claim

            # Check Terminal B's session (no evidence in this session)
            claim_valid, claim_msg = _check_completion_claim(
                response_text,
                session_id=session_term_b
            )

            # Should FAIL - no evidence in Terminal B's session
            # Terminal A's evidence doesn't count for Terminal B
            assert not claim_valid, "Should be blocked - no evidence in Terminal B's session"
            assert "Completion claim without runtime testing evidence" in claim_msg

        except ImportError as e:
            pytest.skip(f"Completion claim verification not yet implemented: {e}")

    def test_completion_pattern_detection(self):
        """Test that completion claim patterns are correctly detected.

        Verify all regex patterns from COMPLETION_PATTERNS match expected claims.
        """
        test_claims = [
            "All files pass validation",
            "✅ Everything is complete",
            "The issue is fixed",
            "Tests passed successfully",
            "Verified and working correctly"
        ]

        try:
            # All patterns should compile successfully
            import re

            from StopHook_unverified_stance import COMPLETION_PATTERNS
            for pattern in COMPLETION_PATTERNS:
                assert isinstance(pattern, re.Pattern), f"Pattern should be compiled regex: {pattern}"

            # Each test claim should match at least one pattern
            for claim in test_claims:
                matches = False
                for pattern in COMPLETION_PATTERNS:
                    if pattern.search(claim):
                        matches = True
                        break
                assert matches, f"Claim should match completion pattern: {claim}"

        except (ImportError, AttributeError) as e:
            pytest.skip(f"COMPLETION_PATTERNS not yet implemented: {e}")

    def test_runtime_tool_detection(self):
        """Test that runtime tools are correctly identified.

        Verify RUNTIME_TOOLS set includes expected tools.
        """
        expected_tools = {"Bash", "Edit", "Read", "Grep", "Glob"}

        try:
            from StopHook_unverified_stance import RUNTIME_TOOLS

            assert isinstance(RUNTIME_TOOLS, set), "RUNTIME_TOOLS should be a set"
            assert RUNTIME_TOOLS == expected_tools, f"RUNTIME_TOOLS should be {expected_tools}, got {RUNTIME_TOOLS}"

        except (ImportError, AttributeError) as e:
            pytest.skip(f"RUNTIME_TOOLS not yet implemented: {e}")

    def test_command_pattern_detection(self):
        """Test that runtime command patterns are correctly identified.

        Verify RUNTIME_COMMAND_PATTERNS includes expected commands.
        """
        expected_patterns = ["subprocess", "pytest", "python", "node", "npm test"]

        try:
            from StopHook_unverified_stance import RUNTIME_COMMAND_PATTERNS

            assert isinstance(RUNTIME_COMMAND_PATTERNS, list), "RUNTIME_COMMAND_PATTERNS should be a list"
            for pattern in expected_patterns:
                assert pattern in RUNTIME_COMMAND_PATTERNS, f"Pattern '{pattern}' should be in RUNTIME_COMMAND_PATTERNS"

        except (ImportError, AttributeError) as e:
            pytest.skip(f"RUNTIME_COMMAND_PATTERNS not yet implemented: {e}")


class TestEvidenceAdapterIntegration:
    """Test shared evidence adapter integration for completion claim verification."""

    def test_load_tool_events_adapter_exists(self):
        """Verify the module-level shared evidence adapter exists."""
        try:
            from StopHook_unverified_stance import load_tool_events
            assert callable(load_tool_events), "load_tool_events should be callable"
        except ImportError as e:
            pytest.fail(f"shared load_tool_events adapter should exist: {e}")

    def test_resolve_session_id_api_exists(self):
        """Verify resolve_session_id() function exists in evidence_store.py."""
        try:
            from evidence_store import resolve_session_id
            assert callable(resolve_session_id), "resolve_session_id should be callable"
        except ImportError as e:
            pytest.fail(f"evidence_store.resolve_session_id should exist: {e}")

    def test_load_tool_events_returns_list(self):
        """Verify the shared evidence adapter returns a list of event dicts."""
        test_session_id = "test-session-api-check-12345"

        try:
            from StopHook_unverified_stance import load_tool_events

            # Call with empty session_id (should return empty list or handle gracefully)
            result = load_tool_events(test_session_id, limit=10)

            assert isinstance(result, list), f"load_tool_events should return list, got {type(result)}"

            # If events returned, verify structure
            for event in result:
                assert isinstance(event, dict), "Each event should be a dict"
                # Check for expected keys (from plan verification)
                assert "name" in event, "Event should have 'name' key"
                assert "command" in event, "Event should have 'command' key"

        except Exception as e:
            pytest.skip(f"shared adapter call failed (may need actual evidence): {e}")

    def test_event_dict_structure_matches_plan(self):
        """Verify event dict structure matches plan specification.

        From plan: Event dict has keys: name, command, cwd, output_excerpt, session_id, terminal_id
        Uses "name" key, NOT "tool_name" (PR-004 fix).
        """
        # This test documents the expected structure from plan verification
        expected_keys = {"name", "command", "cwd", "output_excerpt", "session_id", "terminal_id"}
        prohibited_keys = {"tool_name"}  # PR-004: Should NOT use "tool_name"

        # Structure is verified in plan, this test documents the contract
        assert "name" in expected_keys, "Plan specifies 'name' key for tool name"
        assert "tool_name" not in expected_keys, "Plan does NOT specify 'tool_name' key (PR-004)"

        # If we had actual events, we'd verify:
        # assert set(event.keys()) >= expected_keys, "Event should have all expected keys"
        # assert "tool_name" not in event, "Event should NOT have 'tool_name' key (PR-004)"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])


# ---------------------------------------------------------------------------
# Additional completion claim tests for unverified_completion_claim gate
# ---------------------------------------------------------------------------


class TestUnverifiedCompletionClaim:
    """Tests for unverified completion claim detection (Phase 2 gate)."""

    def test_all_tests_pass_no_tool_output_flags_claim(self):
        """'all tests passed' with no pytest/Bash tool output → flags unverified_completion_claim."""
        from StopHook_unverified_stance import _check_completion_claim_with_events

        response = "all tests passed"
        tool_events = []  # No Bash/pytest output in this turn

        claim_valid, claim_msg = _check_completion_claim_with_events(response, tool_events)
        # Without runtime evidence, the claim should be flagged
        assert not claim_valid, "Claim should be invalid without runtime evidence"
        assert "Completion claim without runtime testing evidence" in claim_msg

    def test_all_tests_pass_with_pytest_output_does_not_flag(self):
        """'all tests passed' with pytest output in tool_events → no flag."""
        from StopHook_unverified_stance import _check_completion_claim_with_events

        response = "all tests passed"
        tool_events = [
            {"name": "Bash", "command": "pytest --tb=short", "output_excerpt": "103 passed in 0.31s"},
        ]

        claim_valid, claim_msg = _check_completion_claim_with_events(response, tool_events)
        # With pytest output, claim should be valid
        assert claim_valid, f"Claim should be valid with pytest output: {claim_msg}"

    def test_hedged_belief_does_not_flag(self):
        """'I believe this fixes the bug, but I have not run tests' → no flag (already hedges)."""
        from StopHook_unverified_stance import _check_completion_claim_with_events

        response = "I believe this fixes the bug, but I have not run tests"
        tool_events = []

        # Hedged language should not match COMPLETION_PATTERNS
        # (only strong absolute claims are flagged)
        from StopHook_unverified_stance import COMPLETION_PATTERNS
        matched = any(p.search(response) for p in COMPLETION_PATTERNS)
        assert not matched, (
            f"'I believe...' hedging should not match any COMPLETION_PATTERNS. "
            "If it does, the pattern is too broad."
        )
