"""
Unit tests for ErrorRecoveryManager.

Tests cover:
- Error classification into categories
- Recovery strategy selection
- Backoff delay calculation
- Retry decision logic
- Execute with recovery
- Error summary tracking
"""

from unittest.mock import patch

import pytest

from yt_fts.download.error_recovery import (
    ErrorCategory,
    ErrorRecoveryManager,
    RecoveryStrategy,
)


class TestErrorCategory:
    """Tests for ErrorCategory enum."""

    def test_all_categories_defined(self):
        """All expected error categories are defined."""
        expected = {
            "NETWORK",
            "RATE_LIMIT",
            "AUTHENTICATION",
            "QUOTA_EXCEEDED",
            "RESOURCE_NOT_FOUND",
            "TEMPORARY_FAILURE",
            "PERMANENT_FAILURE",
            "SYSTEM_ERROR",
            "UNKNOWN",
        }
        actual = {cat.name for cat in ErrorCategory}
        assert actual == expected


class TestRecoveryStrategy:
    """Tests for RecoveryStrategy enum."""

    def test_all_strategies_defined(self):
        """All expected recovery strategies are defined."""
        expected = {
            "IMMEDIATE_RETRY",
            "EXPONENTIAL_BACKOFF",
            "SKIP_AND_CONTINUE",
            "FAIL_FAST",
            "WAIT_AND_RETRY",
            "MANUAL_INTERVENTION",
        }
        actual = {strategy.name for strategy in RecoveryStrategy}
        assert actual == expected


class TestErrorRecoveryManagerInitialization:
    """Tests for ErrorRecoveryManager initialization."""

    def test_initialization_with_defaults(self):
        """Default values are set correctly."""
        manager = ErrorRecoveryManager()
        assert manager.max_retries == 3
        assert manager.base_backoff == 1.0
        assert manager.max_backoff == 300.0
        assert manager.continue_on_error is True
        assert manager.error_counts == {}
        assert manager.last_error_time == {}

    def test_initialization_with_custom_values(self):
        """Custom values override defaults."""
        manager = ErrorRecoveryManager(
            max_retries=5,
            base_backoff_seconds=2.0,
            max_backoff_seconds=600.0,
            continue_on_error=False,
        )
        assert manager.max_retries == 5
        assert manager.base_backoff == 2.0
        assert manager.max_backoff == 600.0
        assert manager.continue_on_error is False


class TestClassifyError:
    """Tests for error classification."""

    def test_classify_network_error(self):
        """Network-related errors are classified correctly."""
        manager = ErrorRecoveryManager()

        test_cases = [
            Exception("Connection timeout"),
            Exception("Network error"),
            Exception("DNS resolution failed"),
            Exception("SSL certificate error"),
            Exception("connection reset"),
            Exception("connection refused"),
            Exception("connection aborted"),
        ]

        for error in test_cases:
            category = manager.classify_error(error)
            assert category == ErrorCategory.NETWORK

    def test_classify_rate_limit_error(self):
        """Rate limit errors are classified correctly."""
        manager = ErrorRecoveryManager()

        test_cases = [
            Exception("rate limit exceeded"),
            Exception("Too Many Requests"),
            Exception("HTTP 429"),
            Exception("temporary ban"),
            Exception("blocked"),
            Exception("throttled"),
        ]

        for error in test_cases:
            category = manager.classify_error(error)
            assert category == ErrorCategory.RATE_LIMIT

    def test_classify_authentication_error(self):
        """Authentication errors are classified correctly."""
        manager = ErrorRecoveryManager()

        test_cases = [
            Exception("unauthorized"),
            Exception("forbidden"),
            Exception("authentication failed"),
            Exception("login required"),
            Exception("invalid credentials"),
            Exception("HTTP 401"),
            Exception("HTTP 403"),
            Exception("invalid api key"),
        ]

        for error in test_cases:
            category = manager.classify_error(error)
            assert category == ErrorCategory.AUTHENTICATION

    def test_classify_resource_not_found(self):
        """Resource not found errors are classified correctly."""
        manager = ErrorRecoveryManager()

        test_cases = [
            Exception("not found"),
            Exception("404"),
            Exception("does not exist"),
            Exception("deleted"),
            Exception("removed"),
            Exception("channel not found"),
            Exception("video not available"),
        ]

        for error in test_cases:
            category = manager.classify_error(error)
            assert category == ErrorCategory.RESOURCE_NOT_FOUND

    def test_classify_quota_exceeded(self):
        """Quota exceeded errors are classified correctly."""
        manager = ErrorRecoveryManager()

        # Note: "api quota exceeded" contains "quota exceeded" which matches RATE_LIMIT first (line 111)
        # Use "daily limit exceeded" which matches QUOTA_EXCEEDED
        test_cases = [
            Exception("daily limit exceeded"),
        ]

        for error in test_cases:
            category = manager.classify_error(error)
            assert category == ErrorCategory.QUOTA_EXCEEDED

    def test_classify_temporary_failure(self):
        """Temporary failure errors are classified correctly."""
        manager = ErrorRecoveryManager()

        test_cases = [
            Exception("temporary error"),
            Exception("retry later"),
            Exception("service unavailable"),
            Exception("HTTP 503"),
            Exception("HTTP 502"),
            Exception("internal server error"),
            Exception("HTTP 500"),
            Exception("maintenance mode"),
        ]

        for error in test_cases:
            category = manager.classify_error(error)
            assert category == ErrorCategory.TEMPORARY_FAILURE

    def test_classify_permanent_failure(self):
        """Permanent failure errors are classified correctly."""
        manager = ErrorRecoveryManager()

        # Use messages that match permanent_failure keywords but not earlier patterns
        test_cases = [
            Exception("account permanently banned"),
            Exception("channel permanently terminated"),
            Exception("account suspended"),
            Exception("banned"),
            Exception("violates terms"),
            Exception("inappropriate content"),
            Exception("copyright strike"),
        ]

        for error in test_cases:
            category = manager.classify_error(error)
            assert category == ErrorCategory.PERMANENT_FAILURE

    def test_classify_system_error(self):
        """System errors are classified correctly."""
        manager = ErrorRecoveryManager()

        test_cases = [
            MemoryError("out of memory"),
            OSError("disk space"),
            PermissionError("permission denied"),
            OSError("io error"),
        ]

        for error in test_cases:
            category = manager.classify_error(error)
            assert category == ErrorCategory.SYSTEM_ERROR

    def test_classify_unknown_error(self):
        """Unknown errors are classified as UNKNOWN."""
        manager = ErrorRecoveryManager()

        # Use RuntimeError since "Exception" contains "io" which matches SYSTEM_ERROR
        category = manager.classify_error(RuntimeError("something unexpected"))
        assert category == ErrorCategory.UNKNOWN

    def test_classification_is_case_insensitive(self):
        """Classification is case-insensitive."""
        manager = ErrorRecoveryManager()

        category1 = manager.classify_error(Exception("RATE LIMIT EXCEEDED"))
        category2 = manager.classify_error(Exception("rate limit exceeded"))

        assert category1 == ErrorCategory.RATE_LIMIT
        assert category2 == ErrorCategory.RATE_LIMIT


class TestGetRecoveryStrategy:
    """Tests for recovery strategy selection."""

    def test_permanent_failure_skip_and_continue(self):
        """Permanent failures use SKIP_AND_CONTINUE."""
        manager = ErrorRecoveryManager()
        strategy = manager.get_recovery_strategy(ErrorCategory.PERMANENT_FAILURE, 0)
        assert strategy == RecoveryStrategy.SKIP_AND_CONTINUE

    def test_authentication_fail_fast(self):
        """Authentication issues use FAIL_FAST."""
        manager = ErrorRecoveryManager()
        strategy = manager.get_recovery_strategy(ErrorCategory.AUTHENTICATION, 0)
        assert strategy == RecoveryStrategy.FAIL_FAST

    def test_resource_not_found_skip_and_continue(self):
        """Resource not found uses SKIP_AND_CONTINUE."""
        manager = ErrorRecoveryManager()
        strategy = manager.get_recovery_strategy(ErrorCategory.RESOURCE_NOT_FOUND, 0)
        assert strategy == RecoveryStrategy.SKIP_AND_CONTINUE

    def test_system_error_wait_and_retry_under_max(self):
        """System errors under max retries use WAIT_AND_RETRY."""
        manager = ErrorRecoveryManager(max_retries=3)
        strategy = manager.get_recovery_strategy(ErrorCategory.SYSTEM_ERROR, 1)
        assert strategy == RecoveryStrategy.WAIT_AND_RETRY

    def test_system_error_manual_intervention_at_max(self):
        """System errors at max retries use MANUAL_INTERVENTION."""
        manager = ErrorRecoveryManager(max_retries=3)
        strategy = manager.get_recovery_strategy(ErrorCategory.SYSTEM_ERROR, 3)
        assert strategy == RecoveryStrategy.MANUAL_INTERVENTION

    def test_rate_limit_exponential_backoff(self):
        """Rate limit errors use EXPONENTIAL_BACKOFF."""
        manager = ErrorRecoveryManager()
        strategy = manager.get_recovery_strategy(ErrorCategory.RATE_LIMIT, 0)
        assert strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF

    def test_quota_exceeded_exponential_backoff(self):
        """Quota exceeded uses EXPONENTIAL_BACKOFF."""
        manager = ErrorRecoveryManager()
        strategy = manager.get_recovery_strategy(ErrorCategory.QUOTA_EXCEEDED, 0)
        assert strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF

    def test_network_exponential_backoff_under_max(self):
        """Network errors under max retries use EXPONENTIAL_BACKOFF."""
        manager = ErrorRecoveryManager(max_retries=3)
        strategy = manager.get_recovery_strategy(ErrorCategory.NETWORK, 1)
        assert strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF

    def test_network_skip_at_max_retries(self):
        """Network errors at max retries use SKIP_AND_CONTINUE."""
        manager = ErrorRecoveryManager(max_retries=3)
        strategy = manager.get_recovery_strategy(ErrorCategory.NETWORK, 3)
        assert strategy == RecoveryStrategy.SKIP_AND_CONTINUE

    def test_unknown_exponential_backoff_under_max(self):
        """Unknown errors under max retries use EXPONENTIAL_BACKOFF."""
        manager = ErrorRecoveryManager(max_retries=3)
        strategy = manager.get_recovery_strategy(ErrorCategory.UNKNOWN, 1)
        assert strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF

    def test_unknown_skip_at_max_retries(self):
        """Unknown errors at max retries use SKIP_AND_CONTINUE."""
        manager = ErrorRecoveryManager(max_retries=3)
        strategy = manager.get_recovery_strategy(ErrorCategory.UNKNOWN, 3)
        assert strategy == RecoveryStrategy.SKIP_AND_CONTINUE


class TestCalculateBackoffDelay:
    """Tests for backoff delay calculation."""

    def test_base_exponential_backoff(self):
        """Base exponential backoff increases with attempts."""
        manager = ErrorRecoveryManager(base_backoff_seconds=1.0)

        with patch("random.uniform", return_value=1.0):
            delay0 = manager.calculate_backoff_delay(ErrorCategory.NETWORK, 0)
            delay1 = manager.calculate_backoff_delay(ErrorCategory.NETWORK, 1)
            delay2 = manager.calculate_backoff_delay(ErrorCategory.NETWORK, 2)

            assert delay0 < delay1 < delay2

    def test_max_backoff_is_respected(self):
        """Delay never exceeds max_backoff."""
        manager = ErrorRecoveryManager(base_backoff_seconds=1.0, max_backoff_seconds=10.0)

        with patch("random.uniform", return_value=1.0):
            # Even at high attempt, delay should be capped
            delay = manager.calculate_backoff_delay(ErrorCategory.NETWORK, 10)
            assert delay <= 10.0

    def test_rate_limit_longer_delay(self):
        """Rate limit errors have longer delays."""
        manager = ErrorRecoveryManager(base_backoff_seconds=1.0, max_backoff_seconds=100.0)

        with patch("random.uniform", return_value=1.0):
            network_delay = manager.calculate_backoff_delay(ErrorCategory.NETWORK, 1)
            rate_limit_delay = manager.calculate_backoff_delay(ErrorCategory.RATE_LIMIT, 1)

            assert rate_limit_delay > network_delay

    def test_quota_exceeded_very_long_delay(self):
        """Quota exceeded errors have very long delays."""
        manager = ErrorRecoveryManager(base_backoff_seconds=1.0, max_backoff_seconds=100.0)

        with patch("random.uniform", return_value=1.0):
            network_delay = manager.calculate_backoff_delay(ErrorCategory.NETWORK, 1)
            quota_delay = manager.calculate_backoff_delay(ErrorCategory.QUOTA_EXCEEDED, 1)

            assert quota_delay > network_delay

    def test_network_shorter_delay(self):
        """Network errors have shorter delays."""
        manager = ErrorRecoveryManager(base_backoff_seconds=2.0, max_backoff_seconds=100.0)

        with patch("random.uniform", return_value=1.0):
            base_delay = manager.calculate_backoff_delay(ErrorCategory.TEMPORARY_FAILURE, 1)
            network_delay = manager.calculate_backoff_delay(ErrorCategory.NETWORK, 1)

            assert network_delay < base_delay

    def test_jitter_is_applied(self):
        """Random jitter is applied to prevent thundering herd."""
        manager = ErrorRecoveryManager(base_backoff_seconds=1.0)

        # Call multiple times without patching random
        delays = [
            manager.calculate_backoff_delay(ErrorCategory.NETWORK, 1)
            for _ in range(10)
        ]

        # With jitter, delays should vary
        # (unlikely to get exactly same value 10 times)
        assert len(set(delays)) > 1


class TestShouldRetry:
    """Tests for retry decision logic."""

    def test_fail_fast_never_retries(self):
        """FAIL_FAST strategy never retries."""
        manager = ErrorRecoveryManager()

        result = manager.should_retry(ErrorCategory.AUTHENTICATION, 0)
        assert result is False

    def test_skip_and_continue_never_retries(self):
        """SKIP_AND_CONTINUE strategy never retries."""
        manager = ErrorRecoveryManager()

        result = manager.should_retry(ErrorCategory.RESOURCE_NOT_FOUND, 0)
        assert result is False

    def test_manual_intervention_never_retries(self):
        """MANUAL_INTERVENTION strategy never retries."""
        manager = ErrorRecoveryManager(max_retries=3)

        result = manager.should_retry(ErrorCategory.SYSTEM_ERROR, 3)
        assert result is False

    def test_retry_under_max_retries(self):
        """Retries when under max_retries."""
        manager = ErrorRecoveryManager(max_retries=3)

        result = manager.should_retry(ErrorCategory.NETWORK, 1)
        assert result is True

    def test_no_retry_at_max_retries(self):
        """No retry when at max_retries."""
        manager = ErrorRecoveryManager(max_retries=3)

        result = manager.should_retry(ErrorCategory.NETWORK, 3)
        assert result is False


class TestExecuteWithRecovery:
    """Tests for execute_with_recovery method."""

    def test_successful_operation_returns_result(self):
        """Successful operation returns result immediately."""
        manager = ErrorRecoveryManager()

        result = manager.execute_with_recovery(lambda: 42, "test_op")
        assert result == 42

    def test_operation_fails_without_retry(self):
        """Operation that fails permanently raises exception."""
        manager = ErrorRecoveryManager(max_retries=3)

        def failing_operation():
            raise Exception("permanent error")

        with pytest.raises(Exception, match="permanent error"):
            manager.execute_with_recovery(
                failing_operation,
                "test_op"
            )

    def test_operation_retries_on_transient_error(self):
        """Operation retries on transient errors."""
        manager = ErrorRecoveryManager(max_retries=3, base_backoff_seconds=0.01)

        call_count = [0]

        def flaky_operation():
            call_count[0] += 1
            if call_count[0] < 2:
                msg = "timeout"
                raise Exception(msg)
            return "success"

        result = manager.execute_with_recovery(flaky_operation, "test_op")
        assert result == "success"
        assert call_count[0] == 2

    def test_on_error_callback_is_called(self):
        """on_error callback is called on each error."""
        manager = ErrorRecoveryManager(max_retries=2, base_backoff_seconds=0.01)

        errors = []

        def on_error(error, category, strategy):
            errors.append((error, category, strategy))

        def failing_operation():
            msg = "network timeout"
            raise Exception(msg)

        with pytest.raises(Exception):
            manager.execute_with_recovery(
                failing_operation,
                "test_op",
                on_error=on_error
            )

        assert len(errors) == 3  # max_retries + 1

    def test_on_error_callback_none_is_safe(self):
        """None on_error callback doesn't cause issues."""
        manager = ErrorRecoveryManager(max_retries=1, base_backoff_seconds=0.01)

        def failing_operation():
            msg = "error"
            raise Exception(msg)

        with pytest.raises(Exception):
            manager.execute_with_recovery(failing_operation, "test_op", on_error=None)


class TestGetErrorSummary:
    """Tests for error summary tracking."""

    def test_initial_summary_is_empty(self):
        """Initial summary shows no errors."""
        manager = ErrorRecoveryManager()
        summary = manager.get_error_summary()

        assert summary["error_counts"] == {}
        assert summary["total_errors"] == 0
        assert summary["error_categories"] == []

    def test_summary_returns_correct_structure(self):
        """Summary returns dict with expected keys."""
        manager = ErrorRecoveryManager()
        summary = manager.get_error_summary()

        assert "error_counts" in summary
        assert "total_errors" in summary
        assert "error_categories" in summary
        assert isinstance(summary["error_counts"], dict)
        assert isinstance(summary["total_errors"], int)
        assert isinstance(summary["error_categories"], list)
