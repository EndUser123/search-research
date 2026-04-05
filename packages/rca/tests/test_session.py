"""Tests for rca.session module."""

import pytest

from rca.session import (
    ProblemType,
    classify_problem_type,
    detect_error_type,
    load_active_session,
    manage_active_session,
    search_cks_history,
    run_regression_check,
)


class TestProblemClassification:
    """Tests for classify_problem_type function."""

    def test_classify_test_failure(self):
        """Test classification of test failures."""
        assert classify_problem_type("test failed") == ProblemType.TEST
        assert classify_problem_type("pytest error") == ProblemType.TEST
        assert classify_problem_type("AssertionError") == ProblemType.TEST
        assert classify_problem_type("test_foo") == ProblemType.TEST

    def test_classify_crash(self):
        """Test classification of crashes."""
        assert classify_problem_type("segfault") == ProblemType.CRASH
        assert classify_problem_type("core dump") == ProblemType.CRASH

    def test_classify_performance(self):
        """Test classification of performance issues."""
        assert classify_problem_type("slow response") == ProblemType.PERFORMANCE
        assert classify_problem_type("high latency") == ProblemType.PERFORMANCE
        assert classify_problem_type("timeout") == ProblemType.PERFORMANCE

    def test_classify_error(self):
        """Test classification of general errors."""
        assert classify_problem_type("traceback") == ProblemType.ERROR
        assert classify_problem_type("exception") == ProblemType.ERROR
        assert classify_problem_type("ValueError") == ProblemType.ERROR
        assert classify_problem_type("failed") == ProblemType.ERROR

    def test_classify_behavior(self):
        """Test classification of behavior issues."""
        assert classify_problem_type("acting weird") == ProblemType.BEHAVIOR
        assert classify_problem_type("unexpected output") == ProblemType.BEHAVIOR


class TestErrorDetection:
    """Tests for detect_error_type function."""

    def test_detect_python_exception(self):
        """Test detection of Python exceptions."""
        assert detect_error_type("Traceback (most recent call last)") == "python_exception"
        assert detect_error_type("ValueError: invalid literal") == "python_exception"
        assert detect_error_type("import_error: module not found") == "python_exception"

    def test_detect_timeout(self):
        """Test detection of timeout errors."""
        assert detect_error_type("connection timeout") == "timeout"
        assert detect_error_type("request timeout") == "timeout"
        assert detect_error_type("timeout occurred") == "timeout"

    def test_detect_permission_error(self):
        """Test detection of permission errors."""
        assert detect_error_type("permission denied") == "permission_error"

    def test_detect_network_error(self):
        """Test detection of network errors."""
        assert detect_error_type("connection refused") == "network_error"
        assert detect_error_type("connection reset") == "network_error"

    def test_detect_generic_error(self):
        """Test detection of generic errors."""
        assert detect_error_type("something broke") == "generic_error"
        assert detect_error_type("unknown issue") == "generic_error"


class TestSessionManagement:
    """Tests for session management functions."""

    def test_manage_active_session_returns_tuple(self):
        """Test that manage_active_session returns a tuple."""
        session_id, state = manage_active_session(
            user_input="test problem",
            source="test"
        )
        assert isinstance(session_id, str)
        assert len(session_id) > 0
        assert isinstance(state, dict)
        assert "session_id" in state
        assert state["source"] == "test"

    def test_session_id_starts_with_source(self):
        """Test that session ID starts with the source prefix."""
        session_id, _ = manage_active_session(
            user_input="test problem",
            source="debug"
        )
        assert session_id.startswith("debug_")

    def test_load_active_session_returns_dict(self):
        """Test that load_active_session returns a dict."""
        # Create a session first
        manage_active_session(user_input="test", source="test")
        # Then load it
        state = load_active_session()
        assert isinstance(state, dict)


class TestCKSSearch:
    """Tests for CKS history search."""

    def test_search_cks_history_returns_dict(self):
        """Test that search_cks_history always returns a dict."""
        result = search_cks_history("test error", limit=3)
        assert isinstance(result, dict)
        assert "status" in result
        assert "count" in result
        assert "results" in result


class TestRegressionCheck:
    """Tests for regression check."""

    def test_run_regression_check_returns_none(self):
        """Test that run_regression_check currently returns None (stub)."""
        result = run_regression_check("test error", days=30)
        assert result is None
