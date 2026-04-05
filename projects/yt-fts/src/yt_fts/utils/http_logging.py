"""
HTTP Request Logging Wrapper for NFR-15 Comprehensive Logging.

Provides structured logging for all HTTP requests including:
- URL (sanitized)
- HTTP status code
- Response time in milliseconds
- Request method
- Error details

Integrates with dual_sink_logger for clean separation of technical
debug logs and user console output.
"""
from __future__ import annotations

import logging
import time
import urllib.parse
from collections.abc import Callable, Iterator
from typing import Any
from contextlib import contextmanager

import requests

from .dual_sink_logger import get_logger, log_operation

logger = get_logger(__name__)


def sanitize_url(url: str) -> str:
    """
    Sanitize URL for logging by removing sensitive query parameters.

    Removes: api_key, key, token, auth, password, secret

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL with sensitive parameters redacted
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if not parsed.params:
            return url

        # Parse query parameters
        params = urllib.parse.parse_qsl(parsed.query)
        sensitive_keys = {
            "api_key", "key", "token", "auth", "password",
            "secret", "access_token", "refresh_token", "apikey",
            "authorization", "bearer"
        }

        # Filter out sensitive parameters
        clean_params = [
            (k, "***REDACTED***" if k.lower() in sensitive_keys else v)
            for k, v in params
        ]

        # Rebuild URL
        clean_query = urllib.parse.urlencode(clean_params)
        return urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            clean_query,
            ""  # Remove fragment
        ))
    except (ValueError, TypeError):
        # If sanitization fails, return a safe placeholder
        return "[URL_SANITIZATION_FAILED]"


@contextmanager
def log_http_request(
    operation: str,
    url: str,
    method: str = "GET",
    **context: Any
) -> None:
    """
    Context manager for logging HTTP requests with timing and status.

    Logs:
    - Request start with sanitized URL
    - Request completion with status code and response time
    - Request failure with error details

    Args:
        operation: Operation name (e.g., "rss_fetch", "yt_api_call")
        url: Request URL (will be sanitized)
        method: HTTP method (default: GET)
        **context: Additional context for logging

    Yields:
        None

    Example:
        with log_http_request("rss_fetch", "https://youtube.com/feeds/...", channel_id="UC..."):
            response = requests.get(url)
    """
    sanitized_url = sanitize_url(url)
    start_time = time.time()

    log_operation(
        f"http.{operation}",
        f"HTTP {method} {operation} starting",
        level=logging.DEBUG,
        http_method=method,
        url=sanitized_url,
        **context
    )

    try:
        yield
        duration_ms = (time.time() - start_time) * 1000

        # Note: Status code will be added by the caller after response
        log_operation(
            f"http.{operation}",
            f"HTTP {method} {operation} completed",
            level=logging.DEBUG,
            http_method=method,
            url=sanitized_url,
            duration_ms=round(duration_ms, 2),
            **context
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        log_operation(
            f"http.{operation}",
            f"HTTP {method} {operation} failed",
            level=logging.ERROR,
            http_method=method,
            url=sanitized_url,
            duration_ms=round(duration_ms, 2),
            error_type=type(e).__name__,
            error_message=str(e)[:200],  # Truncate long error messages
            **context
        )
        raise


class LoggedSession(requests.Session):
    """
    Requests.Session subclass that automatically logs all HTTP requests.

    Provides automatic logging for all requests made through this session:
    - URL, method, status code
    - Response time
    - Error details

    Example:
        session = LoggedSession(operation="youtube_api")
        response = session.get("https://www.googleapis.com/youtube/v3/videos", ...)
    """

    def __init__(self, operation: str = "http", **context: Any) -> None:
        """
        Initialize logged session.

        Args:
            operation: Operation name for logging (e.g., "rss_fetch", "yt_api")
            **context: Additional context to include in all logs
        """
        super().__init__()
        self.operation = operation
        self.context = context

    def request(
        self,
        method: str,
        url: str,
        params: Any | None = None,
        data: Any | None = None,
        headers: dict[str, str] | None = None,
        cookies: Any | None = None,
        files: Any | None = None,
        auth: Any | None = None,
        timeout: Any | None = None,
        allow_redirects: bool = True,
        proxies: dict[str, str] | None = None,
        verify: Any | None = None,
        stream: bool | None = None,
        cert: Any | None = None,
        json: Any | None = None,
        **kwargs: Any
    ) -> requests.Response:
        """
        Send HTTP request with automatic logging.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional requests arguments

        Returns:
            requests.Response object
        """
        sanitized_url = sanitize_url(url)
        start_time = time.time()

        log_operation(
            f"http.{self.operation}",
            f"HTTP {method} {self.operation} starting",
            level=logging.DEBUG,
            http_method=method,
            url=sanitized_url,
            **self.context
        )

        try:
            response = super().request(method, url, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            log_operation(
                f"http.{self.operation}",
                f"HTTP {method} {self.operation} completed",
                level=logging.DEBUG,
                http_method=method,
                url=sanitized_url,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                **self.context
            )

            return response

        except requests.RequestException as e:
            duration_ms = (time.time() - start_time) * 1000

            # Extract status code if available from response
            status_code = None
            if hasattr(e, "response") and e.response is not None:
                status_code = e.response.status_code

            log_operation(
                f"http.{self.operation}",
                f"HTTP {method} {self.operation} failed",
                level=logging.WARNING,
                http_method=method,
                url=sanitized_url,
                status_code=status_code,
                duration_ms=round(duration_ms, 2),
                error_type=type(e).__name__,
                error_message=str(e)[:200],
                **self.context
            )

            raise


def log_retry_with_backoff(
        operation: str,
        attempt: int,
        max_attempts: int,
        delay: float,
        reason: str,
        **context: Any
) -> None:
    """
    Log retry attempt with backoff details (NFR-15 AC.15.2).

    Args:
        operation: Operation being retried
        attempt: Current attempt number (1-indexed)
        max_attempts: Maximum number of attempts
        delay: Delay before next retry in seconds
        reason: Reason for retry
        **context: Additional context
    """
    log_operation(
        f"retry.{operation}",
        f"Retry attempt {attempt}/{max_attempts} after {delay:.1f}s delay",
        level=logging.INFO,
        operation_name=operation,
        attempt=attempt,
        max_attempts=max_attempts,
        delay_seconds=round(delay, 2),
        reason=reason[:200],  # Truncate long reasons
        **context
    )


def log_fallback_activated(
        operation: str,
        primary_method: str,
        fallback_method: str,
        reason: str,
        **context: Any
) -> None:
    """
    Log fallback mechanism activation (NFR-15 AC.15.3).

    Args:
        operation: Operation that triggered fallback
        primary_method: Primary method that failed
        fallback_method: Fallback method being activated
        reason: Reason primary method failed
        **context: Additional context
    """
    log_operation(
        f"fallback.{operation}",
        f"Fallback activated: {primary_method} -> {fallback_method}",
        level=logging.WARNING,
        operation_name=operation,
        primary_method=primary_method,
        fallback_method=fallback_method,
        reason=reason[:200],
        **context
    )


def wrap_request_function(
        func: Callable[..., Any],
        operation: str,
        **context: Any
) -> Callable[..., Any]:
    """
    Wrap a request-making function to add automatic logging.

    Args:
        func: Function that makes HTTP requests
        operation: Operation name for logging
        **context: Additional context for logging

    Returns:
        Wrapped function with logging
    """
    def wrapper(*args, **kwargs):
        """
        Wrapper function that logs HTTP request execution.

        Args:
            *args: Positional arguments passed to wrapped function
            **kwargs: Keyword arguments passed to wrapped function

        Returns:
            Result from the wrapped function

        Raises:
            Exception: Re-raises any exception from wrapped function
        """
        # Extract URL from args if possible
        url = "unknown"
        if args and isinstance(args[0], str):
            url = args[0]
        elif "url" in kwargs:
            url = kwargs["url"]

        sanitized_url = sanitize_url(url)
        start_time = time.time()

        log_operation(
            f"http.{operation}",
            f"HTTP request {operation} starting",
            level=logging.DEBUG,
            url=sanitized_url,
            **context
        )

        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            # Check if result is a response object
            status_code = None
            if hasattr(result, "status_code"):
                status_code = result.status_code

            log_operation(
                f"http.{operation}",
                f"HTTP request {operation} completed",
                level=logging.DEBUG,
                url=sanitized_url,
                status_code=status_code,
                duration_ms=round(duration_ms, 2),
                **context
            )

            return result

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            log_operation(
                f"http.{operation}",
                f"HTTP request {operation} failed",
                level=logging.WARNING,
                url=sanitized_url,
                duration_ms=round(duration_ms, 2),
                error_type=type(e).__name__,
                error_message=str(e)[:200],
                **context
            )

            raise

    return wrapper
