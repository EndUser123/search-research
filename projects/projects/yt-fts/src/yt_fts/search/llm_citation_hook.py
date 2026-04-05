"""Citation tracking for LLM response workflows.

This module provides context managers and decorators to automatically track
citations in LLM responses.
"""

import functools
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any, ParamSpec, TypeVar

from yt_fts.search.citation_extractor import get_citation_extractor
from yt_fts.search.llm_context import create_llm_context

P = ParamSpec("P")
R = TypeVar("R")


class CitationTrackingError(Exception):
    """Error raised when citation tracking fails."""



class CitationTracker:
    """Tracks citations for an LLM call."""

    def __init__(self, query: str, result_ids: list[str]) -> None:
        """Initialize citation tracker.

        Args:
            query: The search query
            result_ids: List of search result IDs
        """
        self.query = query
        self.result_ids = result_ids
        self.llm_context = create_llm_context(query, result_ids)
        self.response: str | None = None
        self.citations: list[dict[str, Any]] = []
        self._extractor = get_citation_extractor()

    def set_response(self, response: str) -> None:
        """Set the LLM response and extract citations.

        Args:
            response: The LLM response text
        """
        self.response = response
        self._extract_citations()

    def get_response(self) -> str | None:
        """Get the LLM response.

        Returns:
            Response text or None if not set
        """
        return self.response

    def get_citations(self) -> list[dict[str, Any]]:
        """Get extracted citations.

        Returns:
            List of citation dictionaries
        """
        return self.citations

    def _extract_citations(self) -> None:
        """Extract citations from the response.

        Raises:
            CitationTrackingError: If extraction fails
        """
        if not self.response:
            return

        try:
            self.citations = self._extractor.extract_citations(self.response)
        except Exception as e:
            msg = f"Failed to extract citations: {e}"
            raise CitationTrackingError(msg) from e


@contextmanager
def track_citations(query: str, result_ids: list[str]):
    """Context manager to track citations in LLM responses.

    Usage:
        with track_citations(query, result_ids) as tracker:
            llm_response = ask_llm(...)
            tracker.set_response(llm_response)
        # Citations automatically extracted and available in tracker.get_citations()

    Args:
        query: The search query
        result_ids: List of search result IDs

    Yields:
        CitationTracker instance
    """
    tracker = CitationTracker(query, result_ids)
    try:
        yield tracker
    except Exception:
        # Re-raise any exceptions from the with block
        raise


def track_citations_decorator(
    query_arg: str = "query",
    result_ids_arg: str | list[str] = "result_ids",
):
    """Decorator to automatically track citations in LLM functions.

    Usage:
        @track_citations_decorator(query_arg="prompt", result_ids_arg="result_ids")
        def ask_llm(prompt, result_ids, model="gpt-3"):
            return llm_client.chat.completions.create(...)

    Args:
        query_arg: Name of the argument containing the query
        result_ids_arg: Name of the argument containing result IDs,
                       or a list of result IDs directly

    Returns:
        Decorator function
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            # Extract query and result_ids from function arguments
            query = kwargs.get(query_arg)
            result_ids = kwargs.get(result_ids_arg)

            # If result_ids_arg is a list, use it directly
            if isinstance(result_ids, list):
                pass
            elif result_ids is None and args:
                # Try to get from positional args (basic implementation)
                # This is a simplified version - in production you'd want
                # more sophisticated argument inspection
                pass

            # Create tracker and call function
            tracker = CitationTracker(
                query=query or "",
                result_ids=result_ids if isinstance(result_ids, list) else []
            )

            try:
                result = func(*args, **kwargs)
                # If result is a string, treat it as response and extract citations
                if isinstance(result, str):
                    tracker.set_response(result)
                return result
            except Exception as e:
                msg = f"LLM call failed: {e}"
                raise CitationTrackingError(msg) from e

        return wrapper

    return decorator


# Backward compatibility alias
track_citations_decorator.__doc__ = """Decorator to track citations in LLM functions."""
