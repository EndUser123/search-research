"""Batch URL fetching with concurrent limiting."""

import asyncio
from dataclasses import dataclass

# Default maximum content size in bytes (10MB)
_DEFAULT_MAX_SIZE = 10_000_000


@dataclass
class FetchedContent:
    """Content fetched from a URL.

    Attributes:
        content: The fetched content (None if fetch failed).
        url: The URL that was fetched.
        fetch_time: Time taken to fetch in seconds.
        status_code: HTTP status code (if available).
        content_type: Content-Type header (if available).
        size: Size of content in bytes (if available).
        error: Error message if fetch failed.
    """

    content: str | None
    url: str
    fetch_time: float
    status_code: int | None = None
    content_type: str | None = None
    size: int | None = None
    error: str | None = None


class BatchURLFetcher:
    """Fetch multiple URLs concurrently with limits.

    Attributes:
        max_concurrent: Maximum number of concurrent requests.
        timeout: Request timeout in seconds.
        max_size: Maximum content size in bytes. (defaults to 10MB).
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        timeout: int = 10,
        max_size: int | None = None,
    ):
        """Initialize BatchURLFetcher.

        Args:
            max_concurrent: Maximum concurrent requests.
            timeout: Request timeout in seconds.
            max_size: Maximum content size in bytes. (defaults to 10MB).
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_size = max_size if max_size is not None else _DEFAULT_MAX_SIZE

        # Statistics tracking
        self._total_requests = 0
        self._successful_fetches = 0
        self._failed_fetches = 0
        self._total_bytes_fetched = 0

    async def fetch_urls(
        self, urls: list[str]
    ) -> dict[str, tuple[str | None, float]]:
        """Fetch multiple URLs concurrently.

        Args:
            urls: List of URLs to fetch.

        Returns:
            Dict mapping URL to (content, fetch_time) tuple.
        """
        if not urls:
            return {}

        # Semaphore to enforce concurrent limit
        sem = asyncio.Semaphore(self.max_concurrent)

        async def fetch_with_semaphore(url: str) -> tuple[str, tuple[str | None, float]]:
            """Fetch a single URL with semaphore and timeout."""
            async with sem:
                try:
                    # Apply timeout to the fetch operation
                    result = await asyncio.wait_for(
                        self._fetch_single_url(url, self.timeout, self.max_size),
                        timeout=self.timeout,
                    )

                    content, fetch_time = result

                    # Enforce max_size on returned content
                    if content is not None and len(content) > self.max_size:
                        content = content[: self.max_size] + "...[CONTENT TRUNCATED]"

                    return url, (content, fetch_time)

                except asyncio.TimeoutError:
                    return url, (None, float(self.timeout))
                except Exception:
                    return url, (None, 0.0)

        # Create tasks that will be limited by the semaphore
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        result_dict: dict[str, tuple[str | None, float]] = {}
        for result in results:
            if isinstance(result, Exception):
                self._failed_fetches += 1
            else:
                url, (content, fetch_time) = result
                result_dict[url] = (content, fetch_time)
                self._total_requests += 1
                if content is not None:
                    self._successful_fetches += 1
                    self._total_bytes_fetched += len(content) if content else 0
                else:
                    self._failed_fetches += 1

        return result_dict

    async def _fetch_single_url(
        self, url: str, timeout: int, max_size: int
    ) -> tuple[str | None, float]:
        """Fetch a single URL.

        Args:
            url: URL to fetch.
            timeout: Timeout in seconds.
            max_size: Maximum content size.

        Returns:
            Tuple of (content, fetch_time). Content is None on error/timeout.
        """
        start_time = asyncio.get_event_loop().time()

        # Simulate async fetch - in real implementation use httpx/aiohttp
        await asyncio.sleep(0.01)

        fetch_time = asyncio.get_event_loop().time() - start_time

        # For testing, return mock content
        content = f"Content from {url}"

        return content, fetch_time

    def get_statistics(self) -> dict[str, int]:
        """Get fetcher statistics.

        Returns:
            Dict with total_requests, successful_fetches, failed_fetches,
            total_bytes_fetched.
        """
        return {
            "total_requests": self._total_requests,
            "successful_fetches": self._successful_fetches,
            "failed_fetches": self._failed_fetches,
            "total_bytes_fetched": self._total_bytes_fetched,
        }

    def reset_statistics(self) -> None:
        """Reset all statistics to zero."""
        self._total_requests = 0
        self._successful_fetches = 0
        self._failed_fetches = 0
        self._total_bytes_fetched = 0
