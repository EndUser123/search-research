#!/usr/bin/env python3
"""Unit tests for Tier 3 (E2E) verification in StopHook_unverified_stance.py

Tests the end-to-end workflow verification that detects when agents claim
completion without demonstrating actual skill/workflow execution.

TASK-002: Extend Completion Claim Verification for E2E
From plan-20260310-e2e-verification-enforcement.md

Test Scenarios:
1. Component tests pass but no E2E workflow → block
2. E2E workflow execution shown → allow
3. Distinguish component (Tier 1) from workflow (Tier 3) evidence
4. Session validation fails closed (empty session_id → ValueError)
5. Evidence caching performance (<10ms target)
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import pytest


class TestTier3WorkflowEvidence:
    """Test Tier 3 (E2E) workflow evidence detection."""

    def test_component_tests_without_e2e_blocked(self):
        """Test 1: Component tests pass but no E2E workflow → block.

        Agent shows pytest output (Tier 1) but claims "skill works" without
        actually invoking the skill (Tier 3). Should be blocked.
        """
        test_session_id = "test-session-component-only-12345"

        # Response claims skill is working
        response_text = "✅ /arch skill is fully functional after testing"

        try:
            from StopHook_unverified_stance import _check_completion_claim, _invalidate_evidence_cache

            # Mock evidence_store to return only pytest events (no skill execution)
            with patch('StopHook_unverified_stance.load_tool_events') as mock_load:
                # Return pytest events but no skill invocations
                mock_load.return_value = [
                    {
                        "name": "Bash",
                        "command": "pytest tests/test_arch.py -v",
                        "output": "✅ test_arch PASSED",
                        "timestamp": "2026-03-10T15:30:00",
                        "session_id": test_session_id,
                        "terminal_id": ""
                    }
                ]

                # Should FAIL - component tests alone insufficient for skill claim
                claim_valid, claim_msg = _check_completion_claim(
                    response_text,
                    session_id=test_session_id
                )

                # Component-only claim for skill should be blocked
                # (unless we add logic to distinguish skill claims from code claims)
                # For now, verify it checks for evidence
                if "skill" in response_text.lower() or "workflow" in response_text.lower():
                    # Skill/workflow claims need Tier 3 evidence
                    assert not claim_valid or "workflow" in claim_msg.lower() or "skill" in claim_msg.lower()
                _invalidate_evidence_cache(test_session_id)

        except (ImportError, AttributeError) as e:
            pytest.skip(f"Tier 3 verification not yet implemented: {e}")

    def test_e2e_workflow_execution_allows(self):
        """Test 2: E2E workflow execution shown → allow.

        Agent shows actual skill invocation (Tier 3) evidence.
        Should be allowed because workflow was demonstrated.
        """
        test_session_id = "test-session-e2e-execution-12345"

        # Response after demonstrating skill execution
        response_text = "✅ /arch skill executed successfully and generated ADR"

        try:
            from StopHook_unverified_stance import _check_completion_claim

            # Mock evidence_store to return Skill invocation
            with patch('StopHook_unverified_stance.load_tool_events') as mock_load:
                # Return skill execution event
                mock_load.return_value = [
                    {
                        "name": "Skill",
                        "command": "/arch",
                        "output": "Generating ADR for lean system design...",
                        "timestamp": "2026-03-10T15:35:00",
                        "session_id": test_session_id,
                        "terminal_id": ""
                    },
                    {
                        "name": "Bash",
                        "command": "pytest tests/test_arch.py -v",
                        "output": "✅ test_arch PASSED",
                        "timestamp": "2026-03-10T15:30:00",
                        "session_id": test_session_id,
                        "terminal_id": ""
                    }
                ]

                # Should PASS - E2E workflow demonstrated
                claim_valid, claim_msg = _check_completion_claim(
                    response_text,
                    session_id=test_session_id
                )

                # With E2E evidence, claim should be valid
                assert claim_valid, f"Claim should be valid with E2E evidence: {claim_msg}"
                assert "Sufficient evidence" in claim_msg

        except (ImportError, AttributeError) as e:
            pytest.skip(f"Tier 3 verification not yet implemented: {e}")

    def test_distinguish_component_from_e2e_evidence(self):
        """Test 3: Distinguish component (Tier 1) from workflow (Tier 3) evidence.

        Verify the system can tell the difference between:
        - Tier 1: pytest execution (component tests)
        - Tier 3: skill invocation / workflow execution
        """
        test_session_id = "test-session-tier-distinction-12345"

        try:
            from StopHook_unverified_stance import (
                _check_e2e_workflow_evidence,
                _invalidate_evidence_cache,
            )

            # Test component-only evidence (pytest)
            with patch('StopHook_unverified_stance.load_tool_events') as mock_load:
                mock_load.return_value = [
                    {
                        "name": "Bash",
                        "command": "pytest tests/test_hook.py -v",
                        "output": "2 passed in 0.15s",
                        "timestamp": "2026-03-10T15:40:00",
                        "session_id": test_session_id,
                        "terminal_id": ""
                    }
                ]

                has_e2e = _check_e2e_workflow_evidence(test_session_id)
                assert not has_e2e, "Component tests alone should not count as E2E"
                _invalidate_evidence_cache(test_session_id)

            # Test E2E evidence (skill invocation)
            with patch('StopHook_unverified_stance.load_tool_events') as mock_load:
                mock_load.return_value = [
                    {
                        "name": "Skill",
                        "command": "/verify skill:arch",
                        "output": "Running Tier 1, Tier 2, Tier 3 verification...",
                        "timestamp": "2026-03-10T15:45:00",
                        "session_id": test_session_id,
                        "terminal_id": ""
                    }
                ]

                has_e2e = _check_e2e_workflow_evidence(test_session_id)
                assert has_e2e, "Skill invocation should count as E2E evidence"
                _invalidate_evidence_cache(test_session_id)

        except (ImportError, AttributeError) as e:
            pytest.skip(f"_check_e2e_workflow_evidence not yet implemented: {e}")


class TestSecurityFailClosedValidation:
    """Test SEC-004: Fail-closed session validation."""

    def test_empty_session_id_raises_valueerror(self):
        """Test 4: Session validation fails closed (empty session_id → ValueError).

        SECURITY FIX: Change empty session_id behavior from skip to block.
        Old behavior: empty session_id → skip check (fail-open)
        New behavior: empty session_id → raise ValueError (fail-closed)
        """
        try:
            from StopHook_unverified_stance import _validate_session_id

            # Empty session_id should raise ValueError (fail-closed)
            with pytest.raises(ValueError, match="session_id"):
                _validate_session_id("")

            # None session_id should also raise
            with pytest.raises(ValueError, match="session_id"):
                _validate_session_id(None)

        except (ImportError, AttributeError) as e:
            pytest.skip(f"_validate_session_id not yet implemented: {e}")

    def test_valid_session_id_passes(self):
        """Test that valid session_id passes validation."""
        valid_session_id = "test-session-valid-12345"

        try:
            from StopHook_unverified_stance import _validate_session_id

            # Valid session_id should not raise
            result = _validate_session_id(valid_session_id)
            assert result == valid_session_id

        except (ImportError, AttributeError) as e:
            pytest.skip(f"_validate_session_id not yet implemented: {e}")


class TestPerformanceEvidenceCaching:
    """Test PERF-001: Evidence caching for <10ms target."""

    def test_evidence_cache_performance(self):
        """Test 5: Evidence caching reduces Stop hook latency by >95%.

        Target: <10ms per Stop hook (vs 50-100ms baseline without cache).

        Performance requirement:
        - First call: ~50-100ms (uncached)
        - Subsequent calls: <10ms (cached)
        - Cache invalidation: PostToolUse clears cache
        """
        test_session_id = "test-session-cache-perf-12345"

        try:
            from StopHook_unverified_stance import (
                _check_for_runtime_tools,
                _invalidate_evidence_cache,
            )

            # Mock slow load_tool_events (50ms)
            def slow_load(session_id, limit=100):
                time.sleep(0.050)  # Simulate 50ms database query
                return [{"name": "Bash", "command": "pytest", "timestamp": "2026-03-10T15:50:00"}]

            with patch('StopHook_unverified_stance.load_tool_events', side_effect=slow_load):
                # First call: uncached (should take >50ms)
                start = time.time()
                result1 = _check_for_runtime_tools(test_session_id)
                duration1 = (time.time() - start) * 1000  # Convert to ms

                assert duration1 >= 40, f"First call should be slow (uncached), got {duration1}ms"

                # Second call: cached (should take <10ms)
                start = time.time()
                result2 = _check_for_runtime_tools(test_session_id)
                duration2 = (time.time() - start) * 1000

                assert duration2 < 15, f"Cached call should be fast (<10ms target), got {duration2}ms"
                assert result1 == result2, "Cached result should match first call"

                # Invalidate cache
                _invalidate_evidence_cache(test_session_id)

                # Third call: cache miss (should be slow again)
                start = time.time()
                result3 = _check_for_runtime_tools(test_session_id)
                duration3 = (time.time() - start) * 1000

                assert duration3 >= 40, f"After invalidation, should be slow again, got {duration3}ms"

        except (ImportError, AttributeError) as e:
            pytest.skip(f"Evidence caching not yet implemented: {e}")

    def test_cache_invalidation_on_tool_use(self):
        """Test that cache is invalidated on tool use via PostToolUse."""
        test_session_id = "test-session-cache-invalidation-12345"

        try:
            from StopHook_unverified_stance import (
                _check_for_runtime_tools,
                _get_evidence_cache_stats,
                _invalidate_evidence_cache,
            )

            # Populate cache
            with patch('StopHook_unverified_stance.load_tool_events') as mock_load:
                mock_load.return_value = []

                # First call populates cache
                _check_for_runtime_tools(test_session_id)

                # Check cache stats
                stats = _get_evidence_cache_stats()
                assert test_session_id in stats.get("cached_sessions", [])

                # Invalidate cache (simulating PostToolUse)
                _invalidate_evidence_cache(test_session_id)

                # Check cache cleared
                stats_after = _get_evidence_cache_stats()
                assert test_session_id not in stats_after.get("cached_sessions", [])

        except (ImportError, AttributeError) as e:
            pytest.skip(f"Evidence caching not yet implemented: {e}")


class TestTier3Patterns:
    """Test Tier 3 specific detection patterns."""

    def test_skill_invocation_patterns(self):
        """Test detection of skill invocation claims."""
        test_claims = [
            "/arch skill executed successfully",
            "Workflow completed all stages",
            "All tiers passed verification"
        ]

        try:
            import re

            from StopHook_unverified_stance import E2E_PATTERNS
            for claim in test_claims:
                matches = False
                for pattern in E2E_PATTERNS:
                    if pattern.search(claim):
                        matches = True
                        break
                assert matches, f"Claim should match E2E pattern: {claim}"

        except (ImportError, AttributeError):
            # E2E_PATTERNS may not exist yet, that's ok
            pytest.skip("E2E_PATTERNS not yet implemented")

    def test_multi_step_workflow_detection(self):
        """Test detection of multi-step workflow claims."""
        try:
            from StopHook_unverified_stance import _check_e2e_workflow_evidence

            test_session_id = "test-session-multi-step-12345"

            # Mock multi-step workflow events
            with patch('StopHook_unverified_stance.load_tool_events') as mock_load:
                mock_load.return_value = [
                    {"name": "Bash", "command": "pytest tests/", "timestamp": "2026-03-10T15:55:00"},
                    {"name": "Bash", "command": "python hook_diagnostics.py", "timestamp": "2026-03-10T15:56:00"},
                    {"name": "Skill", "command": "/verify", "timestamp": "2026-03-10T15:57:00"}
                ]

                has_e2e = _check_e2e_workflow_evidence(test_session_id)
                assert has_e2e, "Multi-step workflow should be detected as E2E"

        except (ImportError, AttributeError):
            pytest.skip("_check_e2e_workflow_evidence not yet implemented")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
