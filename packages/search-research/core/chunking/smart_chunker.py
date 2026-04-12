"""Smart Chunking - Semantic boundary detection for document splitting.

This module implements Phase 1 of ADR-002: Smart Chunking Implementation.
Splits documents at semantic boundaries rather than arbitrary token limits
using distance-weighted scoring to find optimal break points within
a target window.

Target: ~900 tokens per chunk with 15% overlap
"""

from __future__ import annotations

import re
from enum import IntEnum
from typing import List, Tuple


class BreakPointScore(IntEnum):
    """Semantic boundary scores for smart chunking."""
    H1 = 100          # Major section
    H2 = 90           # Subsection
    H3 = 80           # Sub-subsection
    CODE_FENCE = 80   # Code block boundary
    HORIZONTAL_RULE = 60
    BLANK_LINE = 20   # Paragraph boundary
    LIST_ITEM = 5
    LINE_BREAK = 1


class SmartChunker:
    """Split documents at semantic boundaries rather than arbitrary token limits.

    Uses distance-weighted scoring to find optimal break points within
    a target window, preserving semantic units (sections, code blocks).

    Target: ~900 tokens per chunk with 15% overlap
    """

    TARGET_TOKENS: int = 900
    OVERLAP_RATIO: float = 0.15
    SEARCH_WINDOW: int = 200  # Tokens before target to search for breaks

    def __init__(self, overlap: bool = True):
        """Initialize smart chunker.

        Args:
            overlap: Whether to create overlapping chunks (default: True)
        """
        self.overlap = overlap

    def chunk(self, text: str) -> List[str]:
        """Split text into semantically coherent chunks.

        Args:
            text: Input markdown or code

        Returns:
            List of text chunks with semantic boundaries preserved
        """
        # Find all break points with scores
        break_points = self._find_break_points(text)

        # Select optimal break points
        chunks = []
        position = 0
        chunk_id = 0

        while position < len(text):
            # Target end position for this chunk
            target_end = position + self.TARGET_TOKENS

            if target_end >= len(text):
                # Final chunk - take remaining text
                chunks.append(text[position:])
                break

            # Search window for optimal break point
            window_start = max(position, target_end - self.SEARCH_WINDOW)
            window_end = min(len(text), target_end + self.SEARCH_WINDOW)

            # Find highest-scoring break point in window
            best_break = self._find_best_break(
                break_points, window_start, window_end, target_end
            )

            # Extract chunk
            chunk_end = best_break if best_break > position else target_end
            chunks.append(text[position:chunk_end])

            # Calculate overlap for next chunk
            overlap_tokens = int(self.TARGET_TOKENS * self.OVERLAP_RATIO)
            position = chunk_end - overlap_tokens if self.overlap else chunk_end
            chunk_id += 1

        return chunks

    def _find_break_points(self, text: str) -> List[Tuple[int, int]]:
        """Find all semantic break points with scores.

        Returns:
            List of (position, score) tuples sorted by position
        """
        break_points = []

        # Markdown patterns
        patterns = [
            (r'^#\s+', BreakPointScore.H1),
            (r'^##\s+', BreakPointScore.H2),
            (r'^###\s+', BreakPointScore.H3),
            (r'^```\s*$', BreakPointScore.CODE_FENCE),
            (r'^---\s*$', BreakPointScore.HORIZONTAL_RULE),
            (r'^\s*$', BreakPointScore.BLANK_LINE),
            (r'^\s*[-*+]\s+', BreakPointScore.LIST_ITEM),
        ]

        for match, score in patterns:
            for m in re.finditer(match, text, re.MULTILINE):
                break_points.append((m.start(), score))

        # Sort by position
        break_points.sort(key=lambda x: x[0])
        return break_points

    def _find_best_break(
        self,
        break_points: List[Tuple[int, int]],
        window_start: int,
        window_end: int,
        target: int
    ) -> int:
        """Find best break point using distance-weighted scoring.

        Formula: finalScore = baseScore × (1 - (distance/window)² × 0.7)

        This gives preference to closer break points while still allowing
        a strong boundary (e.g., H1) 200 tokens back to beat a weak boundary
        at the target.

        Args:
            break_points: All break points with scores
            window_start: Start of search window
            window_end: End of search window
            target: Ideal target position

        Returns:
            Position of best break point
        """
        candidates = [
            (pos, score) for pos, score in break_points
            if window_start <= pos <= window_end
        ]

        if not candidates:
            return target

        best_pos = target
        best_score = 1  # Default: simple line break at target

        for pos, base_score in candidates:
            distance = abs(pos - target)
            window_size = window_end - window_start

            # Distance decay: squared distance penalty
            distance_penalty = (distance / window_size) ** 2
            decay_factor = 1 - (distance_penalty * 0.7)

            final_score = base_score * decay_factor

            if final_score > best_score:
                best_score = final_score
                best_pos = pos

        return best_pos


__all__ = ["SmartChunker", "BreakPointScore"]