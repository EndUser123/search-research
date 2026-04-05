"""
Retry decorator for transient network errors.

Provides exponential backoff retry logic for operations that may fail
due to temporary network issues, rate limits, etc.
"""

import functools
import logging
import time
from collections.abc import Callable
from typing import Any

from yt_fts.exceptions import NetworkError, RateLimitError


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator for retrying operations with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated function that will retry on failure

    Example:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        def fetch_data(url):
            return requests.get(url)
    """

    def decorator(func: Callable) -> Callable:
        """
        Decorator factory for the retry logic.

        Args:
            func: Function to wrap with retry logic.

        Returns:
            Wrapped function with retry capability.
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """
            Wrapper function that implements retry logic.

            Returns:
                Result from the function call or raises last exception.
            """
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    # Don't retry on the last attempt
                    if attempt == max_retries - 1:
                        break

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2**attempt), max_delay)

                    # Log retry attempt
                    logging.getLogger(__name__).warning(
                        "Retry %s/%s after %.1fs: %s",
                        attempt + 1,
                        max_retries,
                        delay,
                        str(e),
                    )

                    time.sleep(delay)

            # All retries exhausted - raise the last exception
            raise last_exception  # type: ignore

        return wrapper

    return decorator


def retry_network_errors(
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> Callable:
    """
    Convenience decorator for retrying network-related errors.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds

    Returns:
        Decorated function that will retry on network errors

    Example:
        @retry_network_errors(max_retries=3)
        def download_video(url):
            return yt_dlp.YoutubeDL().extract_info(url)
    """
    import requests

    return retry_with_backoff(
        max_retries=max_retries,
        base_delay=base_delay,
        exceptions=(
            requests.RequestException,
            requests.ConnectionError,
            requests.Timeout,
            NetworkError,
            RateLimitError,
        ),
    )
