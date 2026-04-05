"""
Custom exceptions for FastAPI authentication API.

Test Case ID: TC-EXCEPTIONS-001
Priority: High
Test Type: Exception Handling

Purpose:
Define custom exceptions for authentication and authorization scenarios,
with proper error codes, messages, and security considerations.

Algorithm Approach: Custom exception hierarchy with error categorization
Time Complexity: O(1) - Exception instantiation
Space Complexity: O(1) - Exception object creation

Security Considerations:
- Error messages don't leak sensitive information
- Consistent error responses
- Rate limiting integration
- Audit trail support
"""

import logging
from typing import Any

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """
    Base authentication error.

    Design Pattern: Exception hierarchy with security-focused messaging
    Used for failed authentication attempts without revealing specific reasons.

    Security Considerations:
    - Generic error message prevents user enumeration
    - Logged for security monitoring
    - Can trigger rate limiting
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize authentication error.

        Args:
        message: Error message (generic for security)
        details: Additional error details (not exposed to client)
        """
        self.message = message
        self.details = details or {}
        logger.warning(f"Authentication error: {message} - Details: {self.details}")
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """
        Convert to HTTP exception for FastAPI response.

        Returns:
        HTTPException: Formatted HTTP exception
        """
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=self.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenError(AuthenticationError):
    """
    JWT token-related errors.

    Design Pattern: Specialized authentication error for token issues
    Handles expired tokens, invalid signatures, malformed tokens.

    Security Considerations:
    - Distinguishes token issues from credential issues
    - Supports token revocation checking
    - Maintains audit trail for token usage
    """

    def __init__(
        self, message: str = "Invalid token", token_type: str | None = None
    ):
        """
        Initialize token error.

        Args:
        message: Error message
        token_type: Type of token (access, refresh, etc.)
        """
        self.token_type = token_type
        super().__init__(message, {"token_type": token_type})

    def to_http_exception(self) -> HTTPException:
        """
        Convert to HTTP exception for token errors.

        Returns:
        HTTPException: Token-specific HTTP exception
        """
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=self.message,
            headers={"WWW-Authenticate": "Bearer", "error": "invalid_token"},
        )


class AuthorizationError(Exception):
    """
    Authorization errors for permission issues.

    Design Pattern: Separate from authentication for proper security layering
    Used when user is authenticated but lacks required permissions.

    Security Considerations:
    - Clearly distinguishes authorization from authentication failures
    - Supports role-based and resource-based permissions
    - Provides audit trail for access attempts
    """

    def __init__(
        self,
        message: str = "Access denied",
        resource: str | None = None,
        action: str | None = None,
    ):
        """
        Initialize authorization error.

        Args:
        message: Error message
        resource: Resource being accessed
        action: Action being attempted
        """
        self.message = message
        self.resource = resource
        self.action = action

        logger.warning(
            f"Authorization error: {message} - Resource: {resource}, Action: {action}"
        )
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """
        Convert to HTTP exception for authorization errors.

        Returns:
        HTTPException: Authorization-specific HTTP exception
        """
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=self.message)


class RateLimitError(Exception):
    """
    Rate limiting exceeded error.

    Design Pattern: Security-focused rate limiting exception
    Triggers when request rate exceeds configured limits.

    Algorithm Approach: Rate limit tracking with sliding window
    Time Complexity: O(1) - Rate limit check
    Space Complexity: O(1) - Rate limit storage

    Security Considerations:
    - Prevents brute force attacks
    - Provides retry-after information
    - Supports multiple rate limit tiers
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        limit: int | None = None,
    ):
        """
        Initialize rate limit error.

        Args:
        message: Error message
        retry_after: Seconds until retry is allowed
        limit: Current rate limit
        """
        self.message = message
        self.retry_after = retry_after
        self.limit = limit

        logger.info(
            f"Rate limit exceeded: {message} - Retry after: {retry_after}s, Limit: {limit}"
        )
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """
        Convert to HTTP exception with rate limit headers.

        Returns:
        HTTPException: Rate limit HTTP exception with headers
        """
        headers = {}
        if self.retry_after:
            headers["Retry-After"] = str(self.retry_after)
        if self.limit:
            headers["X-RateLimit-Limit"] = str(self.limit)

        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=self.message,
            headers=headers,
        )


class UserExistsError(Exception):
    """
    User already exists error.

    Design Pattern: Business logic exception for user management
    Used when attempting to create a user that already exists.

    Security Considerations:
    - Prevents user enumeration through timing attacks
    - Consistent error messaging
    - Supports audit logging
    """

    def __init__(
        self, message: str = "User already exists", field: str | None = None
    ):
        """
        Initialize user exists error.

        Args:
        message: Error message
        field: Field that caused the conflict (email, username, etc.)
        """
        self.message = message
        self.field = field

        logger.warning(f"User exists error: {message} - Field: {field}")
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """
        Convert to HTTP exception for user conflicts.

        Returns:
        HTTPException: Conflict HTTP exception
        """
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=self.message)


class UserNotFoundError(Exception):
    """
    User not found error.

    Design Pattern: Business logic exception for user operations
    Used when attempting to access a non-existent user.

    Security Considerations:
    - Consistent error messaging prevents enumeration
    - No distinction between deleted vs non-existent users
    - Audit trail for access attempts
    """

    def __init__(self, message: str = "User not found", user_id: str | None = None):
        """
        Initialize user not found error.

        Args:
        message: Error message
        user_id: User identifier (logged, not exposed)
        """
        self.message = message
        self.user_id = user_id

        logger.info(f"User not found: {message} - User ID: {user_id}")
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """
        Convert to HTTP exception for user not found.

        Returns:
        HTTPException: Not found HTTP exception
        """
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=self.message)


class ValidationError(Exception):
    """
    Input validation error.

    Design Pattern: Validation error for custom business logic
    Used for complex validation beyond Pydantic's capabilities.

    Security Considerations:
    - Detailed validation errors for legitimate users
    - Sanitized error messages
    - Prevents injection through error messages
    """

    def __init__(
        self,
        message: str = "Validation failed",
        field: str | None = None,
        value: str | None = None,
    ):
        """
        Initialize validation error.

        Args:
        message: Error message
        field: Field that failed validation
        value: Value that failed validation (sanitized)
        """
        self.message = message
        self.field = field
        self.value = value

        {
            "field": field,
            "value": "***REDACTED***"
            if value and "password" in str(field).lower()
            else value,
        }

        logger.warning(f"Validation error: {message} - Field: {field}")
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """
        Convert to HTTP exception for validation errors.

        Returns:
        HTTPException: Validation HTTP exception
        """
        error_detail = {"message": self.message, "field": self.field}

        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error_detail
        )


class DatabaseError(Exception):
    """
    Database operation error.

    Design Pattern: Infrastructure exception for database issues
    Used for database connection, query, and transaction errors.

    Security Considerations:
    - Generic error messages prevent database schema disclosure
    - Detailed logging for debugging
    - Connection pool error handling
    """

    def __init__(
        self, message: str = "Database error", operation: str | None = None
    ):
        """
        Initialize database error.

        Args:
        message: Error message
        operation: Database operation that failed
        """
        self.message = message
        self.operation = operation

        logger.error(f"Database error: {message} - Operation: {operation}")
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """
        Convert to HTTP exception for database errors.

        Returns:
        HTTPException: Internal server error HTTP exception
        """
        # Generic message to avoid exposing database details
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


class ConfigurationError(Exception):
    """
    Configuration error.

    Design Pattern: Infrastructure exception for configuration issues
    Used when required configuration is missing or invalid.

    Security Considerations:
    - Prevents application startup with insecure configuration
    - Detailed logging for troubleshooting
    - No exposure of sensitive configuration
    """

    def __init__(
        self, message: str = "Configuration error", setting: str | None = None
    ):
        """
        Initialize configuration error.

        Args:
        message: Error message
        setting: Configuration setting that caused the error
        """
        self.message = message
        self.setting = setting

        logger.error(f"Configuration error: {message} - Setting: {setting}")
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """
        Convert to HTTP exception for configuration errors.

        Returns:
        HTTPException: Internal server error HTTP exception
        """
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Service configuration error",
        )


class SecurityError(Exception):
    """
    General security error.

    Design Pattern: Catch-all for security-related issues
    Used for security violations, suspicious activity, etc.

    Security Considerations:
    - Immediate logging for security monitoring
    - Supports security incident response
    - Can trigger automated security responses
    """

    def __init__(
        self,
        message: str = "Security violation",
        severity: str = "medium",
        details: dict[str, Any] | None = None,
    ):
        """
        Initialize security error.

        Args:
        message: Error message
        severity: Error severity (low, medium, high, critical)
        details: Additional security details
        """
        self.message = message
        self.severity = severity
        self.details = details or {}

        logger.error(
            f"Security error: {message} - Severity: {severity} - Details: {self.details}"
        )
        super().__init__(message)

    def to_http_exception(self) -> HTTPException:
        """
        Convert to HTTP exception for security errors.

        Returns:
        HTTPException: Security violation HTTP exception
        """
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
