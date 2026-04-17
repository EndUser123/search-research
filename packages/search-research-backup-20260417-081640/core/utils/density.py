"""Density calculation (simplified - numerics + technical only)."""

from typing import List
from re import findall


class DensityCalculator:
    """Calculate information density of search results.

    Simplified version: focuses on numeric and technical density.
    Readability analysis deferred for future implementation.
    """

    # Technical terms that indicate high-density content
    TECHNICAL_TERMS = {
        "api", "endpoint", "json", "xml", "sql", "database", "query",
        "async", "await", "thread", "process", "protocol", "http",
        "config", "timeout", "connection", "pool", "serial", "format",
        "parse", "serialize", "deserialize", "encode", "decode",
        "authentication", "authorization", "token", "session", "cookie",
        "function", "method", "class", "object", "interface", "type",
        "variable", "parameter", "argument", "return", "exception",
        "error", "warning", "debug", "log", "trace", "profile",
    }

    def compute_numeric_density(self, results: List) -> float:
        """Calculate numeric density (ratio of numbers to total words).

        Returns 0.0 to 1.0 score.
        """
        if not results:
            return 0.0

        total_words = 0
        numeric_count = 0

        for result in results:
            text = f"{result.title} {result.snippet}"
            words = findall(r'\b[a-zA-Z0-9]+\b', text)
            numbers = findall(r'\b\d+(\.\d+)?\b', text)

            total_words += len(words)
            numeric_count += len(numbers)

        if total_words == 0:
            return 0.0

        return min(1.0, numeric_count / total_words * 5)  # Amplify for sensitivity

    def compute_technical_density(self, results: List) -> float:
        """Calculate technical term density.

        Returns 0.0 to 1.0 score.
        """
        if not results:
            return 0.0

        total_words = 0
        technical_count = 0

        for result in results:
            text = f"{result.title} {result.snippet}".lower()
            words = findall(r'\b[a-z]{3,}\b', text)

            total_words += len(words)
            technical_count += sum(1 for w in words if w in self.TECHNICAL_TERMS)

        if total_words == 0:
            return 0.0

        return min(1.0, technical_count / total_words * 3)  # Amplify for sensitivity

    def compute_density(self, results: List) -> float:
        """Calculate combined density score.

        Returns 0.0 to 1.0 score averaging numeric and technical density.
        """
        numeric = self.compute_numeric_density(results)
        technical = self.compute_technical_density(results)

        return (numeric + technical) / 2
