from __future__ import annotations

import hashlib
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""Simple Conversation Chunker.

Sentence-level conversation chunking for CSF NIP RAG implementation.
Provides clean, solopreneur-friendly text chunking for conversational data.
"""



# Add CSF NIP paths
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "src" / "lib"))


class ConversationChunker:
    """Simple sentence-level chunker for conversational data.

    Optimized for chat history with intelligent sentence boundary detection,
    context preservation, and metadata enrichment.
    """

    def __init__(
        self,
        max_chunk_size: int = 300,
        overlap_sentences: int = 1,
        min_chunk_size: int = 50,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize conversation chunker.

        Args:
        ----
            max_chunk_size: Maximum characters per chunk
            overlap_sentences: Number of sentences to overlap between chunks
            min_chunk_size: Minimum characters per chunk
            logger: Logger instance

        """
        self.logger = logger or logging.getLogger(__name__)
        self.max_chunk_size = max_chunk_size
        self.overlap_sentences = overlap_sentences
        self.min_chunk_size = min_chunk_size

        # Compile regex patterns for efficiency
        self.sentence_boundary_pattern = re.compile(
            r"(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*$|(?<=\n)\s*",
            re.MULTILINE,
        )
        self.code_block_pattern = re.compile(r"```[\s\S]*?```")
        self.inline_code_pattern = re.compile(r"`[^`]+`")

    def chunk_conversation_entry(self, entry: dict[str, Any]) -> list[dict[str, Any]]:
        """Chunk a single conversation entry into manageable pieces.

        Args:
        ----
            entry: Chat entry with display text and metadata

        Returns:
        -------
            List of chunks with preserved metadata

        """
        text = entry.get("display", "")
        if not text or len(text) < self.min_chunk_size:
            # Skip very short entries or return as single chunk
            return [
                {
                    "text": text,
                    "chunk_id": self._generate_chunk_id(text),
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "metadata": {
                        **entry,
                        "chunk_type": "single",
                        "chunk_size": len(text),
                        "created_at": datetime.now().isoformat(),
                    },
                },
            ]

        # Extract code blocks for special handling
        chunks = self._chunk_with_code_preservation(text, entry)
        self.logger.debug(f"Created {len(chunks)} chunks from entry")

        return chunks

    def _chunk_with_code_preservation(
        self, text: str, entry: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Chunk text while preserving code blocks and inline code.

        Args:
        ----
            text: Text to chunk
            entry: Original entry metadata

        Returns:
        -------
            List of chunks with preserved code

        """
        # Identify and protect code blocks
        code_blocks = []
        protected_text = text

        for i, match in enumerate(self.code_block_pattern.finditer(text)):
            code_placeholder = f"__CODE_BLOCK_{i}__"
            code_blocks.append(
                {
                    "placeholder": code_placeholder,
                    "content": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                },
            )
            protected_text = protected_text.replace(match.group(0), code_placeholder)

        # Chunk the protected text
        sentence_chunks = self._split_into_sentences(protected_text)

        # Group sentences into chunks of appropriate size
        text_chunks = self._group_sentences_into_chunks(sentence_chunks)

        # Restore code blocks and create chunk objects
        final_chunks = []
        for i, chunk_text in enumerate(text_chunks):
            # Restore code blocks
            restored_text = chunk_text
            for code_block in code_blocks:
                restored_text = restored_text.replace(
                    code_block["placeholder"], code_block["content"]
                )

            # Create chunk metadata
            chunk = {
                "text": restored_text.strip(),
                "chunk_id": self._generate_chunk_id(restored_text),
                "chunk_index": i,
                "total_chunks": len(text_chunks),
                "metadata": {
                    **entry,
                    "chunk_type": "conversation",
                    "chunk_size": len(restored_text),
                    "has_code": bool(self.code_block_pattern.search(restored_text)),
                    "created_at": datetime.now().isoformat(),
                },
            }
            final_chunks.append(chunk)

        return final_chunks

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences using boundary detection.

        Args:
        ----
            text: Text to split

        Returns:
        -------
            List of sentences

        """
        # Split on sentence boundaries
        sentences = self.sentence_boundary_pattern.split(text)

        # Clean up and filter sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (
                sentence and len(sentence) >= self.min_chunk_size // 4
            ):  # Allow very short sentences
                cleaned_sentences.append(sentence)

        return cleaned_sentences

    def _group_sentences_into_chunks(self, sentences: list[str]) -> list[str]:
        """Group sentences into chunks of appropriate size.

        Args:
        ----
            sentences: List of sentences to group

        Returns:
        -------
            List of text chunks

        """
        if not sentences:
            return []

        chunks = []
        current_chunk = ""
        overlap_buffer = []

        for _i, sentence in enumerate(sentences):
            # Check if adding this sentence would exceed max size
            potential_chunk = (
                current_chunk + " " + sentence if current_chunk else sentence
            )

            if len(potential_chunk) <= self.max_chunk_size:
                # Add to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

                # Add to overlap buffer
                if self.overlap_sentences > 0:
                    overlap_buffer.append(sentence)
                    if len(overlap_buffer) > self.overlap_sentences:
                        overlap_buffer.pop(0)
            else:
                # Save current chunk if it's large enough
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append(current_chunk)

                # Start new chunk with overlap if available
                current_chunk = (
                    " ".join(overlap_buffer) + " " + sentence
                    if overlap_buffer
                    else sentence
                )

                # Reset overlap buffer with current sentence
                overlap_buffer = [sentence] if self.overlap_sentences > 0 else []

        # Add final chunk if it's large enough
        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(current_chunk)

        # Handle edge case: no chunks created
        if not chunks and sentences:
            # Create single chunk from all sentences
            all_text = " ".join(sentences)
            if len(all_text) >= self.min_chunk_size:
                chunks.append(all_text)

        return chunks

    def _generate_chunk_id(self, text: str) -> str:
        """Generate a unique ID for a chunk.

        Args:
        ----
            text: Chunk text

        Returns:
        -------
            Unique chunk ID

        """
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        timestamp = str(int(datetime.now().timestamp() * 1000))[-6:]
        return f"chunk_{content_hash}_{timestamp}"

    def chunk_conversation_history(
        self,
        entries: list[dict[str, Any]],
        session_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Chunk multiple conversation entries.

        Args:
        ----
            entries: List of conversation entries
            session_filter: Optional session filter

        Returns:
        -------
            List of all chunks from all entries

        """
        all_chunks = []

        for entry in entries:
            # Apply session filter if provided
            if session_filter and not self._passes_session_filter(
                entry, session_filter
            ):
                continue

            chunks = self.chunk_conversation_entry(entry)
            all_chunks.extend(chunks)

        self.logger.info(
            f"Created {len(all_chunks)} chunks from {len(entries)} entries"
        )
        return all_chunks

    def _passes_session_filter(
        self, entry: dict[str, Any], session_filter: str
    ) -> bool:
        """Check if an entry passes session filtering.

        Args:
        ----
            entry: Chat entry
            session_filter: Session filter string

        Returns:
        -------
            True if entry passes filter

        """
        from datetime import timedelta

        timestamp = entry.get("timestamp", 0)
        entry_time = datetime.fromtimestamp(timestamp / 1000)
        now = datetime.now()

        if session_filter == "today":
            return entry_time.date() == now.date()
        if session_filter == "yesterday":
            yesterday = now.date() - timedelta(days=1)
            return entry_time.date() == yesterday
        if session_filter == "week":
            return entry_time >= now - timedelta(days=7)
        if session_filter == "month":
            return entry_time >= now - timedelta(days=30)
        # "all"
        return True

    def get_chunk_statistics(self, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        """Calculate statistics about created chunks.

        Args:
        ----
            chunks: List of chunks

        Returns:
        -------
            Dictionary with chunk statistics

        """
        if not chunks:
            return {
                "total_chunks": 0,
                "total_characters": 0,
                "average_chunk_size": 0,
                "chunks_with_code": 0,
            }

        total_chars = sum(chunk["metadata"]["chunk_size"] for chunk in chunks)
        chunks_with_code = sum(
            1 for chunk in chunks if chunk["metadata"].get("has_code", False)
        )

        return {
            "total_chunks": len(chunks),
            "total_characters": total_chars,
            "average_chunk_size": total_chars // len(chunks),
            "min_chunk_size": min(chunk["metadata"]["chunk_size"] for chunk in chunks),
            "max_chunk_size": max(chunk["metadata"]["chunk_size"] for chunk in chunks),
            "chunks_with_code": chunks_with_code,
            "code_percentage": (chunks_with_code / len(chunks)) * 100,
        }


class ConversationChunkerFactory:
    """Factory for creating conversation chunkers with different configurations."""

    @staticmethod
    def create_default_chunker() -> ConversationChunker:
        """Create a default conversation chunker.

        Returns
        -------
            ConversationChunker with balanced settings

        """
        return ConversationChunker(
            max_chunk_size=300,
            overlap_sentences=1,
            min_chunk_size=50,
        )

    @staticmethod
    def create_small_chunker() -> ConversationChunker:
        """Create a chunker for smaller, more precise chunks.

        Returns
        -------
            ConversationChunker optimized for small chunks

        """
        return ConversationChunker(
            max_chunk_size=200,
            overlap_sentences=0,
            min_chunk_size=30,
        )

    @staticmethod
    def create_large_chunker() -> ConversationChunker:
        """Create a chunker for larger, more contextual chunks.

        Returns
        -------
            ConversationChunker optimized for large chunks

        """
        return ConversationChunker(
            max_chunk_size=500,
            overlap_sentences=2,
            min_chunk_size=100,
        )

    @staticmethod
    def create_code_friendly_chunker() -> ConversationChunker:
        """Create a chunker optimized for technical conversations with code.

        Returns
        -------
            ConversationChunker with code preservation focus

        """
        return ConversationChunker(
            max_chunk_size=400,
            overlap_sentences=1,
            min_chunk_size=50,
        )


# Convenience function for creating chunkers
def create_conversation_chunker(
    max_chunk_size: int = 300,
    overlap_sentences: int = 1,
    min_chunk_size: int = 50,
) -> ConversationChunker:
    """Create a conversation chunker with custom settings.

    Args:
    ----
        max_chunk_size: Maximum characters per chunk
        overlap_sentences: Number of sentences to overlap
        min_chunk_size: Minimum characters per chunk

    Returns:
    -------
        ConversationChunker instance

    """
    return ConversationChunker(
        max_chunk_size=max_chunk_size,
        overlap_sentences=overlap_sentences,
        min_chunk_size=min_chunk_size,
    )
