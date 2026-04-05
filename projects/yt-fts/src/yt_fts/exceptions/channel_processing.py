"""
Channel Processing Exceptions

Custom exceptions for channel processing operations.
Provides structured error handling with categorization and suggestions.

Author: CSF NIP Implementation Team
Version: 1.0.0
"""
from __future__ import annotations

from typing import Any


class ChannelProcessingError(Exception):
    """
    Custom exception for channel processing errors.

    Provides structured error information including categorization,
    severity, and user-friendly suggestions for resolution.
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        category: str = "processing",
        severity: str = "medium",
        recoverable: bool = True,
        suggestions: list[str] | None = None,
        context: dict[str, Any] | None = None
    ) -> None:
        """
        Initialize channel processing error.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            category: Error category (network, validation, processing, etc.)
            severity: Error severity (low, medium, high, critical)
            recoverable: Whether the error is recoverable
            suggestions: List of suggestions for resolving the error
            context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.category = category
        self.severity = severity
        self.recoverable = recoverable
        self.suggestions = suggestions or []
        self.context = context or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging and serialization."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "category": self.category,
            "severity": self.severity,
            "recoverable": self.recoverable,
            "suggestions": self.suggestions,
            "context": self.context
        }

    def __str__(self) -> str:
        """String representation with suggestions."""
        base_str = self.message
        if self.suggestions:
            suggestions_str = "\nSuggestions:\n" + "\n".join(f"  - {s}" for s in self.suggestions)
            base_str += suggestions_str
        return base_str


class ChannelResolutionError(ChannelProcessingError):
    """Exception for channel resolution failures."""

    def __init__(
        self,
        message: str,
        input_value: str | None = None,
        resolution_type: str | None = None,
        **kwargs: Any
        ) -> None:
        """
        Initialize channel resolution error.

        Args:
            message: Human-readable error message
            input_value: The input value that failed resolution
            resolution_type: Type of resolution attempted
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(
            message=message,
            category="resolution",
            **kwargs
            )
        self.input_value = input_value
        self.resolution_type = resolution_type


class ChannelValidationError(ChannelProcessingError):
    """Exception for channel validation failures."""

    def __init__(
        self,
        message: str,
        validation_rule: str | None = None,
        invalid_value: str | None = None,
        **kwargs: Any
        ) -> None:
        """
        Initialize channel validation error.

        Args:
            message: Human-readable error message
            validation_rule: The validation rule that was violated
            invalid_value: The value that failed validation
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(
            message=message,
            category="validation",
            severity="medium",
            **kwargs
            )
        self.validation_rule = validation_rule
        self.invalid_value = invalid_value


class NetworkError(ChannelProcessingError):
    """Exception for network-related errors."""

    def __init__(
        self,
        message: str,
        url: str | None = None,
        status_code: int | None = None,
        **kwargs: Any
        ) -> None:
        """
        Initialize network error.

        Args:
            message: Human-readable error message
            url: The URL that caused the network error
            status_code: HTTP status code if applicable
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(
            message=message,
            category="network",
            severity="high",
            recoverable=True,
            **kwargs
            )
        self.url = url
        self.status_code = status_code


class AuthenticationError(ChannelProcessingError):
    """Exception for authentication failures."""

    def __init__(
        self,
        message: str,
        auth_type: str | None = None,
        **kwargs: Any
        ) -> None:
        """
        Initialize authentication error.

        Args:
            message: Human-readable error message
            auth_type: Type of authentication that failed
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(
            message=message,
            category="authentication",
            severity="high",
            recoverable=False,
            **kwargs
            )
        self.auth_type = auth_type


class RateLimitError(ChannelProcessingError):
    """Exception for rate limiting errors."""

    def __init__(
        self,
        message: str,
        retry_after: int | None = None,
        **kwargs: Any
        ) -> None:
        """
        Initialize rate limit error.

        Args:
            message: Human-readable error message
            retry_after: Seconds to wait before retrying
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(
            message=message,
            category="rate_limit",
            severity="medium",
            recoverable=True,
            **kwargs
            )
        self.retry_after = retry_after


class ConfigurationError(ChannelProcessingError):
    """Exception for configuration errors."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        **kwargs: Any
        ) -> None:
        """
        Initialize configuration error.

        Args:
            message: Human-readable error message
            config_key: The configuration key that is invalid
            **kwargs: Additional arguments passed to parent class
        """
        super().__init__(
            message=message,
            category="configuration",
            severity="high",
            recoverable=False,
            **kwargs
            )
        self.config_key = config_key


# Error factory functions for common scenarios
def create_resolution_error(input_value: str, reason: str) -> ChannelResolutionError:
    """Create a channel resolution error for common scenarios."""
    suggestions = [
        "Check if the channel exists and is public",
        "Try using the channel's @handle instead",
        "Verify the channel URL is correct",
        "Try searching for the channel on YouTube first"
    ]

    if input_value.startswith("@"):
        suggestions.insert(0, "Verify the @handle is spelled correctly")
    elif input_value.startswith("http"):
        suggestions.insert(0, "Ensure the URL is a valid YouTube channel URL")

    return ChannelResolutionError(
        message=f"Unable to resolve channel '{input_value}': {reason}",
        input_value=input_value,
        suggestions=suggestions
    )


def create_network_error(url: str, reason: str) -> NetworkError:
    """Create a network error for common scenarios."""
    suggestions = [
        "Check your internet connection",
        "Try again in a few moments",
        "Verify the URL is accessible",
        "Check if YouTube is experiencing issues"
    ]

    return NetworkError(
        message=f"Network error accessing '{url}': {reason}",
        url=url,
        suggestions=suggestions
    )


def create_validation_error(field_name: str, value: str, rule: str) -> ChannelValidationError:
    """Create a validation error for common scenarios."""
    return ChannelValidationError(
        message=f"Invalid value for '{field_name}': {value}",
        validation_rule=rule,
        invalid_value=value,
        suggestions=[
            f"Ensure '{field_name}' follows the format: {rule}",
            "Check for typos or missing information",
            "Refer to the documentation for valid formats"
        ]
    )
