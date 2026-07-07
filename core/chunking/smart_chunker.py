"""Smart Chunking - Semantic boundary detection for document splitting.

This module implements Phase 1 of ADR-002: Smart Chunking Implementation.
Splits documents at semantic boundaries rather than arbitrary token limits
using distance-weighted scoring to find optimal break points within
a target window.

Chunk identity is content-addressed: chunk IDs derive from
sha256(doc_id | char_start | char_end | text_sha256), so a rebuild over
unchanged text yields identical IDs. Golden eval sets and cross-store
references remain valid across re-index and re-embed runs.

Target: ~900 tokens per chunk with 15% overlap
"""

from __future__ import annotations

import hashlib
import re
from enum import IntEnum
from typing import List, Tuple, TypedDict

CHUNKER_NAME = "smart_chunker"
# Bump when chunk boundaries or ID derivation change. A version change means
# chunk IDs from prior runs are NOT comparable to new runs.
CHUNKER_VERSION = "1.1.0"


class ChunkRecord(TypedDict):
    """Content-addressed chunk with provenance metadata (kb.chunk.v1 style)."""

    chunk_id: str
    doc_id: str
    char_start: int
    char_end: int
    text: str
    text_sha256: str
    chunker_name: str
    chunker_version: str
    chunker_params: dict


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


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class SmartChunker:
    """Split documents at semantic boundaries rather than arbitrary token limits.

    Uses distance-weighted scoring to find optimal break points within
    a search window, preserving semantic units (sections, code blocks).

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

    @property
    def params(self) -> dict:
        """Chunking parameters, recorded per chunk for reproducibility."""
        return {
            "target_tokens": self.TARGET_TOKENS,
            "overlap_ratio": self.OVERLAP_RATIO,
            "search_window": self.SEARCH_WINDOW,
            "overlap": self.overlap,
        }

    def chunk(self, text: str) -> List[str]:
        """Split text into semantically coherent chunks.

        Args:
            text: Input markdown or code

        Returns:
            List of text chunks with semantic boundaries preserved
        """
        return [text[start:end] for start, end in self._chunk_spans(text)]

    def chunk_with_metadata(self, text: str, doc_id: str = "") -> List[ChunkRecord]:
        """Split text into chunks with stable, content-addressed identity.

        The chunk_id is sha256(doc_id | char_start | char_end | text_sha256):
        independent of embedding model, vector store, and run order. Rebuilding
        from identical source text yields identical IDs; any change to the
        text or boundaries produces new IDs.

        Args:
            text: Input markdown or code
            doc_id: Stable logical document identifier (e.g. canonical path
                or source hash). Empty string is allowed but IDs are then
                only unique within this document.

        Returns:
            List of ChunkRecord dicts with identity and provenance metadata
        """
        records: List[ChunkRecord] = []
        for start, end in self._chunk_spans(text):
            chunk_text = text[start:end]
            text_sha = _sha256_text(chunk_text)
            chunk_id = hashlib.sha256(
                f"{doc_id}|{start}|{end}|{text_sha}".encode("utf-8")
            ).hexdigest()
            records.append(
                ChunkRecord(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    char_start=start,
                    char_end=end,
                    text=chunk_text,
                    text_sha256=text_sha,
                    chunker_name=CHUNKER_NAME,
                    chunker_version=CHUNKER_VERSION,
                    chunker_params=self.params,
                )
            )
        return records

    def _chunk_spans(self, text: str) -> List[Tuple[int, int]]:
        """Compute (char_start, char_end) spans for all chunks.

        Single source of truth for boundary selection; chunk() and
        chunk_with_metadata() both derive from these spans.
        """
        if not text:
            return []

        break_points = self._find_break_points(text)

        spans: List[Tuple[int, int]] = []
        position = 0

        while position < len(text):
            # Target end position for this chunk
            target_end = position + self.TARGET_TOKENS

            if target_end >= len(text):
                # Final chunk - take remaining text
                spans.append((position, len(text)))
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
            spans.append((position, chunk_end))

            # Calculate overlap for next chunk
            overlap_tokens = int(self.TARGET_TOKENS * self.OVERLAP_RATIO)
            position = chunk_end - overlap_tokens if self.overlap else chunk_end

        return spans

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


__all__ = [
    "SmartChunker",
    "BreakPointScore",
    "ChunkRecord",
    "CHUNKER_NAME",
    "CHUNKER_VERSION",
]
