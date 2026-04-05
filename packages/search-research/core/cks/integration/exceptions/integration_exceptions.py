from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

"""CSF CKS Integration Exceptions

This module defines standardized exception classes for the CKS cross-system
integration layer, providing comprehensive error classification and handling.

Algorithm Approach: Exception hierarchy with contextual information
and CSF constitutional compliance reporting.

Design Principles:
- Typed exceptions for different error categories
- Rich context information for debugging
- CSF constitutional violation tracking
- Solo developer-friendly error messages
- Evidence-based error reporting
"""


class ErrorSeverity(Enum):
    """Enumeration of error severity levels.

    Provides standardized classification for integration errors
    to enable proper handling and escalation procedures.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Enumeration of error categories for integration operations.

    Enables systematic error analysis and prevention strategies
    across all integration systems.
    """

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NETWORK = "network"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    DEPENDENCY = "dependency"
    SECURITY = "security"
    CONSTITUTIONAL = "constitutional"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for integration errors.

    Provides comprehensive context for error debugging and
    CSF constitutional compliance reporting.

    Attributes:
        integration_source (str): Name of the integration system
        operation_name (str): Name of the operation that failed
        error_timestamp (datetime): When the error occurred
        attempt_count (int): Number of retry attempts
        execution_time_seconds (float): Time before error occurred
        metadata (Dict[str, Any]): Additional error context
        constitutional_violations (List[str]): CSF constitutional violations
        suggestion (Optional[str]): Suggested resolution

    """

    integration_source: str
    operation_name: str
    error_timestamp: datetime = field(default_factory=datetime.utcnow)
    attempt_count: int = 1
    execution_time_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    constitutional_violations: list[str] = field(default_factory=list)
    suggestion: str | None = None


class IntegrationException(Exception):
    """Base exception for all integration operations.

    Provides standardized error handling with rich context
    and CSF constitutional compliance tracking.

    Algorithm Approach: Exception chaining with contextual
    information preservation and systematic error classification.

    CSF Compliance:
    - Constitutional violation tracking
    - Evidence-based error reporting
    - Solo developer-friendly diagnostics
    - Force multiplier impact assessment
    """

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        original_exception: Exception | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize integration exception with comprehensive context.

        Parameters
        ----------
        message (str): Human-readable error message
        context (ErrorContext): Error context information
        severity (ErrorSeverity): Error severity level
        category (ErrorCategory): Error category classification
        original_exception (Optional[Exception]): Original exception that caused this
        error_code (Optional[str]): Machine-readable error code

        """
        super().__init__(message)
        self.message = message
        self.context = context
        self.severity = severity
        self.category = category
        self.original_exception = original_exception
        self.error_code = error_code

        # Add constitutional violation if applicable
        self._assess_constitutional_compliance()

    def _assess_constitutional_compliance(self) -> None:
        """Assess if the error represents a constitutional violation.

        Identifies CSF constitutional violations based on error
        category and context for compliance tracking.
        """
        if self.category == ErrorCategory.SECURITY:
            self.context.constitutional_violations.append(
                "CSF §4.2: Security requirements violation",
            )
        elif self.category == ErrorCategory.RATE_LIMIT:
            self.context.constitutional_violations.append(
                "CSF §3.3: Rate limiting and resource management violation",
            )
        elif self.category == ErrorCategory.AUTHENTICATION:
            self.context.constitutional_violations.append(
                "CSF §4.1: Authentication requirements violation",
            )

        if self.severity == ErrorSeverity.CRITICAL:
            self.context.constitutional_violations.append(
                "CSF §2.1: System stability and reliability requirement violation",
            )

    def __str__(self) -> str:
        """String representation with context information."""
        base_msg = f"{self.message} (Source: {self.context.integration_source})"
        if self.error_code:
            base_msg = f"[{self.error_code}] {base_msg}"
        return base_msg

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for serialization.

        Returns
        -------
        Dict[str, Any]: Exception data as dictionary

        """
        return {
            "exception_type": self.__class__.__name__,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "error_code": self.error_code,
            "context": {
                "integration_source": self.context.integration_source,
                "operation_name": self.context.operation_name,
                "error_timestamp": self.context.error_timestamp.isoformat(),
                "attempt_count": self.context.attempt_count,
                "execution_time_seconds": self.context.execution_time_seconds,
                "metadata": self.context.metadata,
                "constitutional_violations": self.context.constitutional_violations,
                "suggestion": self.context.suggestion,
            },
            "original_exception": (
                str(self.original_exception) if self.original_exception else None
            ),
        }


class AuthenticationException(IntegrationException):
    """Exception raised for authentication failures.

    Used when credentials are invalid, expired, or missing
    for integration system access.
    """

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        original_exception: Exception | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize authentication exception.

        Parameters
        ----------
        message (str): Error message
        context (ErrorContext): Error context
        original_exception (Optional[Exception]): Original exception
        error_code (Optional[str]): Error code

        """
        super().__init__(
            message=message,
            context=context,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.AUTHENTICATION,
            original_exception=original_exception,
            error_code=error_code or "AUTH_001",
        )

        if not context.suggestion:
            context.suggestion = (
                "Verify credentials are valid and properly configured. "
                "Check API key expiration and permissions."
            )


class AuthorizationException(IntegrationException):
    """Exception raised for authorization failures.

    Used when authenticated user lacks sufficient permissions
    for the requested operation.
    """

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        required_permission: str | None = None,
        original_exception: Exception | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize authorization exception.

        Parameters
        ----------
        message (str): Error message
        context (ErrorContext): Error context
        required_permission (Optional[str]): Permission that was required
        original_exception (Optional[Exception]): Original exception
        error_code (Optional[str]): Error code

        """
        super().__init__(
            message=message,
            context=context,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.AUTHORIZATION,
            original_exception=original_exception,
            error_code=error_code or "AUTHZ_001",
        )

        self.required_permission = required_permission

        if not context.suggestion:
            context.suggestion = (
                f"Grant required permission: {required_permission or 'unknown'}. "
                "Check user roles and access control configuration."
            )


class NetworkException(IntegrationException):
    """Exception raised for network connectivity issues.

    Used for connection failures, DNS resolution problems,
    and other network-related issues.
    """

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        endpoint: str | None = None,
        original_exception: Exception | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize network exception.

        Parameters
        ----------
        message (str): Error message
        context (ErrorContext): Error context
        endpoint (Optional[str]): Network endpoint that failed
        original_exception (Optional[Exception]): Original exception
        error_code (Optional[str]): Error code

        """
        super().__init__(
            message=message,
            context=context,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.NETWORK,
            original_exception=original_exception,
            error_code=error_code or "NET_001",
        )

        self.endpoint = endpoint

        if not context.suggestion:
            context.suggestion = (
                "Check network connectivity and firewall settings. "
                f"Verify endpoint accessibility: {endpoint or 'unknown endpoint'}"
            )


class TimeoutException(IntegrationException):
    """Exception raised for operation timeouts.

    Used when integration operations exceed configured
    timeout thresholds.
    """

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        timeout_seconds: float | None = None,
        original_exception: Exception | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize timeout exception.

        Parameters
        ----------
        message (str): Error message
        context (ErrorContext): Error context
        timeout_seconds (Optional[float]): Timeout threshold in seconds
        original_exception (Optional[Exception]): Original exception
        error_code (Optional[str]): Error code

        """
        super().__init__(
            message=message,
            context=context,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.TIMEOUT,
            original_exception=original_exception,
            error_code=error_code or "TIMEOUT_001",
        )

        self.timeout_seconds = timeout_seconds

        if not context.suggestion:
            context.suggestion = (
                f"Increase timeout threshold beyond {timeout_seconds} seconds "
                "or optimize the operation for better performance."
            )


class RateLimitException(IntegrationException):
    """Exception raised when rate limits are exceeded.

    Used when integration systems reject requests due to
        rate limiting policies.
    """

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        limit: int | None = None,
        window_seconds: int | None = None,
        retry_after_seconds: int | None = None,
        original_exception: Exception | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize rate limit exception.

        Parameters
        ----------
        message (str): Error message
        context (ErrorContext): Error context
        limit (Optional[int]): Rate limit that was exceeded
        window_seconds (Optional[int]): Time window for rate limit
        retry_after_seconds (Optional[int]): Seconds to wait before retry
        original_exception (Optional[Exception]): Original exception
        error_code (Optional[str]): Error code

        """
        super().__init__(
            message=message,
            context=context,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.RATE_LIMIT,
            original_exception=original_exception,
            error_code=error_code or "RATE_LIMIT_001",
        )

        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after_seconds = retry_after_seconds

        if not context.suggestion:
            retry_time = retry_after_seconds or 60
            context.suggestion = (
                f"Wait {retry_time} seconds before retrying. "
                f"Current limit: {limit or 'unknown'} requests per {window_seconds or 'unknown'} seconds."
            )


class ValidationException(IntegrationException):
    """Exception raised for data validation failures.

    Used when input data fails validation rules
    or schema requirements.
    """

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        validation_errors: list[str] | None = None,
        original_exception: Exception | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize validation exception.

        Parameters
        ----------
        message (str): Error message
        context (ErrorContext): Error context
        validation_errors (Optional[List[str]]): Specific validation errors
        original_exception (Optional[Exception]): Original exception
        error_code (Optional[str]): Error code

        """
        super().__init__(
            message=message,
            context=context,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
            original_exception=original_exception,
            error_code=error_code or "VALIDATION_001",
        )

        self.validation_errors = validation_errors or []

        if not context.suggestion:
            context.suggestion = (
                "Fix validation errors: " + "; ".join(self.validation_errors)
                if self.validation_errors
                else "Review input data format and requirements."
            )


class ConfigurationException(IntegrationException):
    """Exception raised for configuration errors.

    Used when integration client configuration is invalid
    or incomplete.
    """

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        configuration_errors: list[str] | None = None,
        original_exception: Exception | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize configuration exception.

        Parameters
        ----------
        message (str): Error message
        context (ErrorContext): Error context
        configuration_errors (Optional[List[str]]): Specific configuration errors
        original_exception (Optional[Exception]): Original exception
        error_code (Optional[str]): Error code

        """
        super().__init__(
            message=message,
            context=context,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.CONFIGURATION,
            original_exception=original_exception,
            error_code=error_code or "CONFIG_001",
        )

        self.configuration_errors = configuration_errors or []

        if not context.suggestion:
            context.suggestion = (
                "Fix configuration errors: " + "; ".join(self.configuration_errors)
                if self.configuration_errors
                else "Review client configuration and required parameters."
            )


class SecurityException(IntegrationException):
    """Exception raised for security-related violations.

    Used for security policy violations, malicious content,
    and other security issues.
    """

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        security_policy: str | None = None,
        threat_level: str | None = None,
        original_exception: Exception | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize security exception.

        Parameters
        ----------
        message (str): Error message
        context (ErrorContext): Error context
        security_policy (Optional[str]): Security policy that was violated
        threat_level (Optional[str]): Threat level assessment
        original_exception (Optional[Exception]): Original exception
        error_code (Optional[str]): Error code

        """
        super().__init__(
            message=message,
            context=context,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SECURITY,
            original_exception=original_exception,
            error_code=error_code or "SECURITY_001",
        )

        self.security_policy = security_policy
        self.threat_level = threat_level

        if not context.suggestion:
            context.suggestion = (
                f"Security violation: {security_policy or 'unknown policy'}. "
                f"Threat level: {threat_level or 'unknown'}. "
                "Review security policies and content validation."
            )

        # Add constitutional violation for security issues
        context.constitutional_violations.append(
            "CSF §4.0: Security requirements violation",
        )


class ConstitutionalException(IntegrationException):
    """Exception raised for CSF constitutional violations.

    Used when operations violate CSF constitutional requirements
    or solo developer optimization principles.
    """

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        violated_articles: list[str] | None = None,
        constitutional_score: float | None = None,
        original_exception: Exception | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize constitutional exception.

        Parameters
        ----------
        message (str): Error message
        context (ErrorContext): Error context
        violated_articles (Optional[List[str]]): Specific constitutional articles violated
        constitutional_score (Optional[float]): Compliance score (0-1)
        original_exception (Optional[Exception]): Original exception
        error_code (Optional[str]): Error code

        """
        super().__init__(
            message=message,
            context=context,
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.CONSTITUTIONAL,
            original_exception=original_exception,
            error_code=error_code or "CONST_001",
        )

        self.violated_articles = violated_articles or []
        self.constitutional_score = constitutional_score

        if not context.suggestion:
            context.suggestion = (
                "CSF constitutional violation detected. "
                "Review solo developer optimization principles and "
                "constitutional requirements compliance."
            )

        # Add all violated articles to context
        for article in self.violated_articles:
            if article not in context.constitutional_violations:
                context.constitutional_violations.append(article)


class DependencyException(IntegrationException):
    """Exception raised for dependency resolution failures.

    Used when required dependencies are missing, incompatible,
    or fail to initialize.
    """

    def __init__(
        self,
        message: str,
        context: ErrorContext,
        dependency_name: str | None = None,
        required_version: str | None = None,
        current_version: str | None = None,
        original_exception: Exception | None = None,
        error_code: str | None = None,
    ) -> None:
        """Initialize dependency exception.

        Parameters
        ----------
        message (str): Error message
        context (ErrorContext): Error context
        dependency_name (Optional[str]): Name of the problematic dependency
        required_version (Optional[str]): Required version
        current_version (Optional[str]): Currently installed version
        original_exception (Optional[Exception]): Original exception
        error_code (Optional[str]): Error code

        """
        super().__init__(
            message=message,
            context=context,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DEPENDENCY,
            original_exception=original_exception,
            error_code=error_code or "DEP_001",
        )

        self.dependency_name = dependency_name
        self.required_version = required_version
        self.current_version = current_version

        if not context.suggestion:
            context.suggestion = (
                f"Install or upgrade dependency: {dependency_name or 'unknown'}. "
                f"Required version: {required_version or 'any'}, "
                f"Current version: {current_version or 'not installed'}."
            )


# Exception factory functions for creating standardized exceptions
def create_authentication_error(
    message: str,
    integration_source: str,
    operation_name: str,
    original_exception: Exception | None = None,
) -> AuthenticationException:
    """Create an authentication exception with standard context.

    Parameters
    ----------
    message (str): Error message
    integration_source (str): Name of the integration system
    operation_name (str): Name of the operation that failed
    original_exception (Optional[Exception]): Original exception

    Returns
    -------
    AuthenticationException: Configured authentication exception

    """
    context = ErrorContext(
        integration_source=integration_source,
        operation_name=operation_name,
    )
    return AuthenticationException(message, context, original_exception)


def create_rate_limit_error(
    message: str,
    integration_source: str,
    operation_name: str,
    limit: int,
    retry_after_seconds: int,
) -> RateLimitException:
    """Create a rate limit exception with standard context.

    Parameters
    ----------
    message (str): Error message
    integration_source (str): Name of the integration system
    operation_name (str): Name of the operation that failed
    limit (int): Rate limit that was exceeded
    retry_after_seconds (int): Seconds to wait before retry

    Returns
    -------
    RateLimitException: Configured rate limit exception

    """
    context = ErrorContext(
        integration_source=integration_source,
        operation_name=operation_name,
    )
    return RateLimitException(
        message,
        context,
        limit=limit,
        retry_after_seconds=retry_after_seconds,
    )


def create_constitutional_violation(
    message: str,
    integration_source: str,
    operation_name: str,
    violated_articles: list[str],
    constitutional_score: float,
) -> ConstitutionalException:
    """Create a constitutional violation exception with standard context.

    Parameters
    ----------
    message (str): Error message
    integration_source (str): Name of the integration system
    operation_name (str): Name of the operation that failed
    violated_articles (List[str]): Specific constitutional articles violated
    constitutional_score (float): Compliance score (0-1)

    Returns
    -------
    ConstitutionalException: Configured constitutional violation exception

    """
    context = ErrorContext(
        integration_source=integration_source,
        operation_name=operation_name,
    )
    return ConstitutionalException(
        message,
        context,
        violated_articles=violated_articles,
        constitutional_score=constitutional_score,
    )
