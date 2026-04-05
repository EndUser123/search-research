"""Tests for pre-mortem validation utilities.

Tests cover action mapping validation, kill criteria validation, and
operational verification. Target: 80%+ coverage.
"""

from __future__ import annotations

from __lib.validation import (
    _detect_generic_actions,
    _extract_recommended_actions,
    _extract_top_priorities,
    run_all_validations,
    validate_action_mapping,
    validate_kill_criteria_defined,
    validate_operational_verification,
)


class TestExtractTopPriorities:
    """Tests for _extract_top_priorities function."""

    def test_extracts_high_risk_items(self) -> None:
        """Should extract priorities with risk score >= 6."""
        output = """
        🔴 RISK:9 - Database connection failure
        🟡 RISK:6 - Memory leak in loop
        🟢 RISK:3 - Minor UI bug
        """
        priorities = _extract_top_priorities(output)
        assert len(priorities) == 2
        assert priorities[0]["risk_score"] == 9
        assert priorities[0]["description"] == "Database connection failure"
        assert priorities[1]["risk_score"] == 6

    def test_ignores_low_risk_items(self) -> None:
        """Should ignore priorities with risk score < 6."""
        output = """
        🟢 RISK:3 - Minor UI bug
        🟢 RISK:2 - Typo in docs
        """
        priorities = _extract_top_priorities(output)
        assert len(priorities) == 0

    def test_handles_missing_emoji(self) -> None:
        """PM-004 FIX: Should now extract priorities without emoji (flexible regex)."""
        output = "RISK:9 - No emoji here"
        priorities = _extract_top_priorities(output)
        assert len(priorities) == 1
        assert priorities[0]["risk_score"] == 9
        assert priorities[0]["description"] == "No emoji here"

    def test_handles_case_variations(self) -> None:
        """PM-004 FIX: Should handle case-insensitive RISK format."""
        output = "risk: 7 - Lowercase risk format"
        priorities = _extract_top_priorities(output)
        assert len(priorities) == 1
        assert priorities[0]["risk_score"] == 7

    def test_handles_bracket_format(self) -> None:
        """PM-004 FIX: Should handle bracket format [RISK 9]."""
        output = "[RISK 8] Bracket format description"
        priorities = _extract_top_priorities(output)
        assert len(priorities) == 1
        assert priorities[0]["risk_score"] == 8


class TestExtractRecommendedActions:
    """Tests for _extract_recommended_actions function."""

    def test_extracts_numbered_actions(self) -> None:
        """Should extract numbered actions."""
        output = """
        1a: Add test coverage → Use pytest
        1b: Fix memory leak → Use profiler
        2a: Update docs → Readme
        """
        actions = _extract_recommended_actions(output)
        assert len(actions) == 3
        assert "Add test coverage" in actions[0]
        assert "Fix memory leak" in actions[1]
        assert "Update docs" in actions[2]

    def test_handles_empty_output(self) -> None:
        """Should return empty list for no actions."""
        actions = _extract_recommended_actions("No actions here")
        assert len(actions) == 0


class TestDetectGenericActions:
    """Tests for _detect_generic_actions function."""

    def test_detects_add_tests(self) -> None:
        """Should detect 'add tests' as generic."""
        actions = ["add tests", "Add Tests", "ADD TESTS"]
        generic = _detect_generic_actions(actions)
        assert len(generic) == 3

    def test_detects_improve_testing(self) -> None:
        """Should detect 'improve testing' as generic."""
        actions = ["improve testing", "Improve Testing"]
        generic = _detect_generic_actions(actions)
        assert len(generic) == 2

    def test_allows_specific_actions(self) -> None:
        """Should allow specific actions."""
        actions = ["Add ImportError handling", "Fix memory leak in loop"]
        generic = _detect_generic_actions(actions)
        assert len(generic) == 0


class TestValidateActionMapping:
    """Tests for validate_action_mapping function."""

    def test_passes_when_actions_match_priorities(self) -> None:
        """Should pass when action count >= priority count."""
        output = """
        🔴 RISK:9 - Database failure
        1a: Add retry logic → Use circuit breaker
        """
        is_valid, errors = validate_action_mapping(output)
        assert is_valid
        assert len(errors) == 0

    def test_fails_when_fewer_actions_than_priorities(self) -> None:
        """Should fail when action count < priority count."""
        output = """
🔴 RISK:9 - Database failure
🟡 RISK:6 - Memory leak
🟡 RISK:6 - API timeout
1a: Add retry logic → Use circuit breaker
"""
        is_valid, errors = validate_action_mapping(output)
        assert not is_valid
        assert "Action mapping incomplete" in errors[0]

    def test_fails_on_generic_actions(self) -> None:
        """Should fail when actions are generic."""
        output = """
        🔴 RISK:9 - Database failure
        1a: add tests → Use pytest
        """
        is_valid, errors = validate_action_mapping(output)
        assert not is_valid
        assert "Generic actions detected" in errors[0]


class TestValidateKillCriteriaDefined:
    """Tests for validate_kill_criteria_defined function."""

    def test_passes_when_kill_criteria_present(self) -> None:
        """Should pass when kill criteria section exists."""
        output = """
        ## Time-Based Kill Criteria
        - If > 2 hours without prototype, pivot
        """
        is_valid, errors = validate_kill_criteria_defined(output)
        assert is_valid
        assert len(errors) == 0

    def test_fails_when_kill_criteria_missing(self) -> None:
        """Should fail when no kill criteria found."""
        output = "No abandonment criteria defined here"
        is_valid, errors = validate_kill_criteria_defined(output)
        assert not is_valid
        assert "Kill criteria not defined" in errors[0]


class TestValidateOperationalVerification:
    """Tests for validate_operational_verification function."""

    def test_warns_for_planning_pre_mortem(self) -> None:
        """Should warn for planning pre-mortems."""
        output = "REQUIRES OPERATIONAL VERIFICATION AFTER IMPLEMENTATION"
        is_valid, warnings = validate_operational_verification(output)
        assert is_valid  # Always returns True
        assert len(warnings) == 1
        assert "remember to run operational verification" in warnings[0]

    def test_warns_for_missing_evidence(self) -> None:
        """Should warn when no evidence found."""
        output = "## Analysis\nNo implementation details mentioned."
        is_valid, warnings = validate_operational_verification(output)
        assert is_valid
        assert len(warnings) == 1
        assert "No operational evidence detected" in warnings[0]

    def test_passes_with_evidence_present(self) -> None:
        """Should pass when evidence keywords found."""
        output = "Test results passed with 95% coverage. Verified."
        is_valid, warnings = validate_operational_verification(output)
        assert is_valid
        assert len(warnings) == 0


class TestRunAllValidations:
    """Tests for run_all_validations function."""

    def test_aggregates_all_validation_results(self) -> None:
        """Should run all validations and aggregate results."""
        output = """
        🔴 RISK:9 - Database failure
        1a: Add retry logic → Use circuit breaker
        ## Time-Based Kill Criteria
        - If > 2 hours without prototype, pivot
        Test results passed.
        ## Step 2.7: Temporal Failure Modes
        - LLM forgot constraint from turn 47 (requirement stated at turn 44)
        """
        results = run_all_validations(output)
        assert results["is_valid"]
        assert len(results["errors"]) == 0
        assert len(results["warnings"]) == 0

    def test_collects_errors_from_all_validations(self) -> None:
        """Should collect errors from failed validations."""
        output = """
🔴 RISK:9 - Database failure
🟡 RISK:6 - Memory leak
1a: Add retry logic → Use circuit breaker
## Analysis
No kill criteria. No test results.
## Step 2.7: Temporal Failure Modes
- LLM forgot constraint from turn 47 (requirement stated at turn 44)
"""
        results = run_all_validations(output)
        assert not results["is_valid"]
        assert len(results["errors"]) == 1  # Kill criteria only (actions >= priorities)

    def test_collects_warnings_from_non_blocking_validations(self) -> None:
        """Should collect warnings from non-blocking validations."""
        output = """
🔴 RISK:9 - Database failure
1a: Add retry logic → Use circuit breaker
## Time-Based Kill Criteria
- If > 2 hours without prototype, pivot
## Analysis
No implementation details mentioned.
## Step 2.7: Temporal Failure Modes
- LLM forgot constraint from turn 47 (requirement stated at turn 44)
"""
        results = run_all_validations(output)
        assert results["is_valid"]  # Action mapping and kill criteria pass
        assert len(results["warnings"]) == 1  # Operational verification warning
