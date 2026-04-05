"""Citation extraction from LLM responses.

This module provides functionality to extract citation references from LLM responses.
"""

import re
from typing import Any


class CitationExtractor:
    """Extract citations from LLM responses."""

    # Common patterns for YouTube video citations
    YOUTUBE_PATTERNS = [
        r"youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"video[_\s-]?id[:\s]+([a-zA-Z0-9_-]{11})",
        r"([a-zA-Z0-9_-]{11})[\s]*(?:at|@)[\s]*([0-9:]+)",
    ]

    def __init__(self, patterns: list[str] | None = None):
        """Initialize citation extractor.

        Args:
            patterns: Optional list of regex patterns for citation detection
        """
        self.patterns = patterns or self.YOUTUBE_PATTERNS

    def extract_citations(self, text: str) -> list[dict[str, Any]]:
        """Extract citations from LLM response text.

        Args:
            text: LLM response text to parse

        Returns:
            List of citation dictionaries with video_id, timestamp, and context
        """
        if not text:
            return []

        citations = []
        seen = set()  # Avoid duplicate citations

        for pattern in self.patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                groups = match.groups()

                # Extract video_id (first group)
                video_id = groups[0] if groups else None
                if not video_id or len(video_id) != 11:
                    continue

                # Avoid duplicates
                if video_id in seen:
                    continue
                seen.add(video_id)

                # Extract timestamp if available (second group)
                timestamp = groups[1] if len(groups) > 1 else None

                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context_text = text[start:end].strip()

                citation = {
                    "video_id": video_id,
                    "timestamp": timestamp,
                    "text": context_text,
                }
                citations.append(citation)

        return citations


def get_citation_extractor() -> CitationExtractor:
    """Get the global citation extractor instance.

    Returns:
        CitationExtractor instance
    """
    return CitationExtractor()
