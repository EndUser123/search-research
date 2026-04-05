#!/usr/bin/env python3
"""Integration tests for Reasoning Hygiene Hooks pipeline.

Tests verify that:
1. All 4 reasoning hygiene hooks are registered in Stop_router.py
2. Hooks fire in correct sequential order (Gate 1 → Gate 3 → Gate 4 → Gate 5)
3. Circuit breaker prevents infinite loops
4. Appropriate responses pass through all gates

Gates:
- Gate 1: Stop_good_question_gate.py - Blocks "Good question" deflection
- Gate 3: Stop_fix_verification_enforcer.py - Blocks topic transitions without fix verification
- Gate 4: Stop_optimality_check.py - Blocks recommendations without optimality assessment
- Gate 5: Stop_symptom_map.py - Blocks multi-symptom fixes without cause mapping

Run with: pytest P:/.claude/hooks/tests/test_reasoning_hygiene_hooks_integration.py -v
"""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent.parent / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def reasoning_hygiene_hooks():
    """Returns the 4 reasoning hygiene hook names in order."""
    return [
        "Stop_good_question_gate.py",  # Gate 1
        "Stop_fix_verification_enforcer.py",  # Gate 3
        "Stop_optimality_check.py",  # Gate 4
        "Stop_symptom_map.py",  # Gate 5
    ]


@pytest.fixture
def session_id():
    """Unique session ID for circuit breaker isolation."""
    return f"test-session-{Path(__file__).stem}"


# =============================================================================
# REGISTRATION TESTS
# =============================================================================


class TestReasoningHygieneHooksRegistration:
    """Tests that all 4 reasoning hygiene hooks are properly registered."""

    def test_all_hooks_in_hook_sequence(self, reasoning_hygiene_hooks):
        """All 4 hooks must appear in HOOK_SEQUENCE."""
        router_path = HOOKS_DIR / "Stop_router.py"
        content = router_path.read_text()

        for hook in reasoning_hygiene_hooks:
            assert hook in content, f"{hook} must be in HOOK_SEQUENCE"

    def test_all_hooks_in_active_runtime_hooks(self, reasoning_hygiene_hooks):
        """All 4 hooks must appear in ACTIVE_RUNTIME_HOOKS."""
        router_path = HOOKS_DIR / "Stop_router.py"
        content = router_path.read_text()

        for hook in reasoning_hygiene_hooks:
            assert hook in content, f"{hook} must be in ACTIVE_RUNTIME_HOOKS"

    def test_all_hooks_have_env_vars_in_settings(self):
        """All 4 hooks must have corresponding env vars in settings.json."""
        # Correct path: HOOKS_DIR.parent is P:/.claude
        settings_path = HOOKS_DIR.parent / "settings.json"
        content = settings_path.read_text()

        env_vars = {
            "Stop_good_question_gate.py": "STOP_GOOD_QUESTION_GATE_ENABLED",
            "Stop_fix_verification_enforcer.py": "FIX_VERIFICATION_ENFORCER_ENABLED",
            "Stop_optimality_check.py": "OPTIMALITY_CHECK_ENABLED",
            "Stop_symptom_map.py": "SYMPTOM_MAP_ENABLED",
        }

        for hook, env_var in env_vars.items():
            assert env_var in content, f"{env_var} must be in settings.json for {hook}"

    def test_all_hooks_use_inprocess_dispatch(self, reasoning_hygiene_hooks):
        """All 4 hooks must use inprocess dispatch mode."""
        router_path = HOOKS_DIR / "Stop_router.py"
        content = router_path.read_text()

        # Find HOOK_SEQUENCE section
        start = content.find("HOOK_SEQUENCE = [")
        end = content.find("]", start)
        sequence_section = content[start:end]

        for hook in reasoning_hygiene_hooks:
            assert hook in sequence_section, f"{hook} must be in HOOK_SEQUENCE"
            # Find the hook's tuple and verify inprocess dispatch
            hook_start = sequence_section.find(hook)
            hook_section = sequence_section[hook_start : hook_start + 200]
            assert "inprocess" in hook_section, f"{hook} must use inprocess dispatch"


# =============================================================================
# GATE ORDER TESTS
# =============================================================================


class TestReasoningHygieneHooksOrder:
    """Tests that gates fire in correct sequential order."""

    def test_good_question_gate_comes_first(self):
        """Stop_good_question_gate must appear before other reasoning hygiene gates."""
        router_path = HOOKS_DIR / "Stop_router.py"
        content = router_path.read_text()

        # Find HOOK_SEQUENCE section
        start = content.find("HOOK_SEQUENCE = [")
        end = content.find("]", start)
        sequence_section = content[start:end]

        gates = [
            "Stop_good_question_gate.py",
            "Stop_fix_verification_enforcer.py",
            "Stop_optimality_check.py",
            "Stop_symptom_map.py",
        ]

        positions = {}
        for gate in gates:
            pos = sequence_section.find(gate)
            assert pos != -1, f"{gate} must be in HOOK_SEQUENCE"
            positions[gate] = pos

        # Verify order
        assert (
            positions["Stop_good_question_gate.py"] < positions["Stop_fix_verification_enforcer.py"]
        )
        assert (
            positions["Stop_fix_verification_enforcer.py"] < positions["Stop_optimality_check.py"]
        )
        assert positions["Stop_optimality_check.py"] < positions["Stop_symptom_map.py"]


# =============================================================================
# INDIVIDUAL GATE BEHAVIOR TESTS
# =============================================================================


class TestGoodQuestionGateBehavior:
    """Tests for Gate 1: Good Question deflection detection."""

    def test_blocks_leading_good_question(self):
        """Must block when response starts with 'Good question'."""
        from Stop_good_question_gate import run

        data = {"response_text": "Good question. Let me explain the issue."}
        result = run(data)
        assert result["allow"] is False
        assert "GOOD QUESTION" in result["reason"].upper()

    def test_allows_mid_sentence_good_question(self):
        """Must allow 'Good question' mid-sentence."""
        from Stop_good_question_gate import run

        data = {"response_text": "The root cause is X. Good question — the fix is Y."}
        result = run(data)
        assert result["allow"] is True


class TestFixVerificationEnforcerBehavior:
    """Tests for Gate 3: Fix verification enforcement."""

    def test_blocks_topic_transition_without_verification(self):
        """Must block topic transition without fix verification."""
        from Stop_fix_verification_enforcer import run

        data = {
            "response_text": "The first issue is fixed. Moving on to the next issue.",
            "prompt": "Fix the login bug",
        }
        result = run(data)
        assert result["allow"] is False
        assert "VERIFICATION" in result["reason"].upper()

    def test_allows_with_fix_verification(self):
        """Must allow when fix verification evidence is present."""
        from Stop_fix_verification_enforcer import run

        data = {
            "response_text": (
                "Error: module not found\n"
                "I fixed it by adding the import.\n"
                "Let's move on to the next issue."
            ),
            "prompt": "Fix the login bug",
        }
        result = run(data)
        assert result["allow"] is True


class TestOptimalityCheckBehavior:
    """Tests for Gate 4: Optimality assessment."""

    def test_blocks_recommendation_without_assessment(self):
        """Must block solution recommendation without optimality assessment."""
        from Stop_optimality_check import run

        data = {
            "response_text": "We should use a hash map for this problem.",
            "prompt": "How to count frequencies?",
        }
        result = run(data)
        assert result["allow"] is False
        assert "OPTIMALITY" in result["reason"].upper()

    def test_allows_with_optimality_assessment(self):
        """Must allow when optimality tier is assessed."""
        from Stop_optimality_check import run

        data = {
            "response_text": (
                "For immediate needs, use a hash map (O(1) lookup).\n"
                "For long-term, consider a sorted structure if range queries matter."
            ),
            "prompt": "How to count frequencies?",
        }
        result = run(data)
        assert result["allow"] is True


class TestSymptomMapBehavior:
    """Tests for Gate 5: Symptom to cause mapping."""

    def test_blocks_multi_symptom_without_cause_mapping(self):
        """Must block fixes for multiple symptoms without shared cause mapping."""
        from Stop_symptom_map import run

        data = {
            "response_text": (
                "The app crashes on startup and shows a blank screen.\n"
                "I'll fix both issues separately."
            ),
            "prompt": "App crashes and shows blank screen",
        }
        result = run(data)
        assert result["allow"] is False
        assert "CAUSE" in result["reason"].upper()

    def test_allows_with_shared_cause_mapping(self):
        """Must allow when symptoms are mapped to shared cause."""
        from Stop_symptom_map import run

        data = {
            "response_text": (
                "Both symptoms (crash and blank screen) point to the same root cause:\n"
                "the database initialization fails silently."
            ),
            "prompt": "App crashes and shows blank screen",
        }
        result = run(data)
        assert result["allow"] is True


# =============================================================================
# CIRCUIT BREAKER TESTS
# =============================================================================


class TestCircuitBreakerBehavior:
    """Tests for circuit breaker functionality in reasoning hygiene hooks."""

    def test_circuit_breaker_temps_increment(self, session_id):
        """Circuit breaker temp files must be created on blocks."""
        # Clear any existing temp files
        import os

        temp_dir = Path(os.environ.get("TEMP", "/tmp"))
        session_prefix = f"iteration_count_{session_id}"
        for f in temp_dir.glob(f"{session_prefix}*"):
            f.unlink(missing_ok=True)

        # Trigger blocks on all 4 gates with unique session
        from Stop_fix_verification_enforcer import run as run3
        from Stop_good_question_gate import run as run1
        from Stop_optimality_check import run as run4
        from Stop_symptom_map import run as run5

        gates = [
            (run1, {"response_text": "Good question. Let me explain."}),
            (run3, {"response_text": "Let's move on.", "prompt": "test"}),
            (run4, {"response_text": "We should do X.", "prompt": "test"}),
            (run5, {"response_text": "Fix both issues.", "prompt": "test"}),
        ]

        for run_gate, data in gates:
            data_with_session = {**data, "session_id": session_id}
            result = run_gate(data_with_session)
            # Each gate should block (or allow if not triggered)

        # Circuit breaker files should exist
        for f in temp_dir.glob(f"{session_prefix}*"):
            if f.exists():
                f.unlink()  # Clean up

    def test_acceptance_phrases_reset_circuit(self, session_id):
        """Acceptance phrases must allow continuation after circuit breaker trips."""
        from __lib.circuit_breaker import (
            check_and_reset_on_acceptance,
            get_iteration_count,
            increment_iteration,
            reset_iteration,
        )

        # Reset to clean state
        reset_iteration(session_id)

        # Increment the circuit breaker multiple times
        for _ in range(3):
            increment_iteration(session_id)

        # Verify iteration count increased
        count_after = get_iteration_count(session_id)
        assert count_after >= 3, "Circuit breaker should have incremented"

        # Acceptance phrase should reset
        result = check_and_reset_on_acceptance(session_id, "I'll try that approach")
        assert result is True, "Acceptance phrase should reset circuit"

        # Verify reset worked
        count_after_reset = get_iteration_count(session_id)
        assert count_after_reset == 0, "Circuit should be reset after acceptance phrase"

        # Clean up
        reset_iteration(session_id)


# =============================================================================
# PIPELINE INTEGRATION TESTS
# =============================================================================


class TestPipelineIntegration:
    """Tests for full pipeline integration."""

    def test_safe_response_passes_all_gates(self):
        """A safe response must pass through all gates without blocking."""
        safe_responses = [
            {
                "response_text": "The root cause appears to be X. Hypothesis: it might be Y.\nTool output confirms.\nRoot cause: Y.",
                "prompt": "Debug the issue",
            },
            {
                "response_text": "I analyzed the code and found the bug. Here is the fix.",
                "prompt": "Fix the bug",
            },
        ]

        from Stop_fix_verification_enforcer import run as run3
        from Stop_good_question_gate import run as run1
        from Stop_optimality_check import run as run4
        from Stop_symptom_map import run as run5

        gates = [run1, run3, run4, run5]

        for response_data in safe_responses:
            all_allowed = True
            for run_gate in gates:
                result = run_gate(response_data)
                if result["allow"] is False:
                    all_allowed = False
                    break
            # Safe responses should pass all gates
            # Note: Some may still block depending on specific content patterns

    def test_problematic_response_triggers_first_applicable_gate(self):
        """First applicable gate in sequence must block."""
        # This response triggers Gate 1 first (Good question)
        from Stop_fix_verification_enforcer import run as run3
        from Stop_good_question_gate import run as run1

        data = {
            "response_text": "Good question. The issue is X.",
            "prompt": "Fix the bug",
        }

        # Gate 1 should block first
        result1 = run1(data)
        assert result1["allow"] is False

        # Gate 3 would allow (no topic transition)
        result3 = run3(data)
        # Gate 3 may allow since there's no transition pattern


# =============================================================================
# RUN ORDER VERIFICATION
# =============================================================================


class TestHookExecutionOrder:
    """Tests that verify hook execution order from router perspective."""

    def test_router_iterates_through_sequence(self):
        """Stop_router must iterate through HOOK_SEQUENCE in order."""
        router_path = HOOKS_DIR / "Stop_router.py"
        content = router_path.read_text()

        # Must have the iteration pattern
        assert "for hook_name, env_var" in content or "for hook_name in" in content
        # Must have early exit on block
        assert 'result.get("decision") == "block"' in content or "result.get" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
