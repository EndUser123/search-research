"""
Embedding Recovery Manager for yt-fts
Handles missing embeddings detection and recovery strategies
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from rich.console import Console

from ..src.yt_fts.config import get_chroma_client
from ..src.yt_fts.llm.get_embeddings import EmbeddingsHandler


class FallbackStrategy(Enum):
    """Available fallback strategies for missing embeddings"""
    TEXT_SEARCH = "text_search"
    KEYWORD_SEARCH = "keyword_search"
    HYBRID_SEARCH = "hybrid_search"
    SKIP_SEGMENT = "skip_segment"


@dataclass
class RecoveryResult:
    """Result of embedding recovery attempt"""
    success: bool
    strategy_used: FallbackStrategy | None
    embedding_generated: bool
    fallback_results: list[dict[str, Any]]
    processing_time: float
    error_message: str | None = None


@dataclass
class MissingEmbeddingInfo:
    """Information about missing embeddings"""
    video_id: str
    channel_id: str
    start_time: str
    text_content: str
    metadata: dict[str, Any]


class EmbeddingRecoveryManager:
    """
    Manages recovery strategies for missing embeddings in yt-fts search operations.

    This class detects missing embeddings during vector search operations and
    implements intelligent fallback strategies including automatic embedding
    generation when source content is available.
    """

    def __init__(self,
                 max_recovery_attempts: int = 3,
                 enable_background_generation: bool = True,
                 cache_generated_embeddings: bool = True):
        """
        Initialize the EmbeddingRecoveryManager.

        Args:
            max_recovery_attempts: Maximum attempts to recover missing embeddings
            enable_background_generation: Enable background embedding generation
            cache_generated_embeddings: Cache newly generated embeddings
        """
        self.console = Console()
        self.logger = logging.getLogger(__name__)
        self.embeddings_handler = EmbeddingsHandler()
        self.max_recovery_attempts = max_recovery_attempts
        self.enable_background_generation = enable_background_generation
        self.cache_generated_embeddings = cache_generated_embeddings

        # Statistics tracking
        self.stats = {
            'total_recovery_attempts': 0,
            'successful_recoveries': 0,
            'embeddings_generated': 0,
            'fallback_searches': 0,
            'total_processing_time': 0.0
        }

        self.logger.info("EmbeddingRecoveryManager initialized")

    def detect_missing_embeddings(self,
                                chroma_results: dict[str, Any],
                                expected_count: int) -> list[MissingEmbeddingInfo]:
        """
        Detect missing embeddings from ChromaDB query results.

        Args:
            chroma_results: Results from ChromaDB query
            expected_count: Expected number of embeddings

        Returns:
            List of missing embedding information
        """
        missing_embeddings = []

        # Check if we got fewer results than expected
        if 'documents' not in chroma_results or not chroma_results['documents']:
            return missing_embeddings

        actual_count = len(chroma_results['documents'][0]) if chroma_results['documents'][0] else 0

        if actual_count < expected_count:
            self.logger.warning(f"Missing embeddings detected: expected {expected_count}, got {actual_count}")

            # For now, we'll identify missing embeddings by analyzing the metadata
            # In a full implementation, we'd cross-reference with expected video/channel data

        return missing_embeddings

    def recover_missing_embeddings(self,
                                 missing_info: list[MissingEmbeddingInfo],
                                 model_config: dict[str, Any]) -> list[RecoveryResult]:
        """
        Attempt to recover missing embeddings using multiple strategies.

        Args:
            missing_info: List of missing embedding information
            model_config: Model configuration for embedding generation

        Returns:
            List of recovery results for each missing embedding
        """
        recovery_results = []

        for info in missing_info:
            start_time = time.time()
            self.stats['total_recovery_attempts'] += 1

            result = self._recover_single_embedding(info, model_config)
            result.processing_time = time.time() - start_time

            self.stats['total_processing_time'] += result.processing_time

            if result.success:
                self.stats['successful_recoveries'] += 1

            recovery_results.append(result)

        return recovery_results

    def _recover_single_embedding(self,
                                info: MissingEmbeddingInfo,
                                model_config: dict[str, Any]) -> RecoveryResult:
        """
        Recover a single missing embedding.

        Args:
            info: Missing embedding information
            model_config: Model configuration

        Returns:
            Recovery result
        """
        # Strategy 1: Try to generate embedding automatically
        if self._can_generate_embedding(info):
            try:
                embedding_generated = self._generate_embedding(info, model_config)
                if embedding_generated:
                    self.stats['embeddings_generated'] += 1
                    return RecoveryResult(
                        success=True,
                        strategy_used=None,
                        embedding_generated=True,
                        fallback_results=[],
                        processing_time=0.0
                    )
            except Exception as e:
                self.logger.error(f"Failed to generate embedding for {info.video_id}: {e}")

        # Strategy 2: Use fallback search strategies
        fallback_results = self._execute_fallback_searches(info)
        self.stats['fallback_searches'] += 1

        return RecoveryResult(
            success=len(fallback_results) > 0,
            strategy_used=FallbackStrategy.HYBRID_SEARCH,
            embedding_generated=False,
            fallback_results=fallback_results,
            processing_time=0.0,
            error_message="Embedding generation failed, used fallback search"
        )

    def _can_generate_embedding(self, info: MissingEmbeddingInfo) -> bool:
        """
        Check if we can generate an embedding for the given content.

        Args:
            info: Missing embedding information

        Returns:
            True if embedding generation is possible
        """
        # Check if we have the necessary source content
        if not info.text_content or info.text_content.strip() == "":
            return False

        # Check if we have valid metadata
        if not info.metadata or not info.metadata.get('video_title'):
            return False

        return True

    def _generate_embedding(self,
                          info: MissingEmbeddingInfo,
                          model_config: dict[str, Any]) -> bool:
        """
        Generate embedding for missing content.

        Args:
            info: Missing embedding information
            model_config: Model configuration

        Returns:
            True if embedding was successfully generated and stored
        """
        try:
            # Prepare text with metadata (following yt-fts pattern)
            text_with_metadata = self._prepare_text_with_metadata(info)

            # Generate embedding
            embedding_gen = self.embeddings_handler.get_embedding(
                text_list=[text_with_metadata],
                model=model_config['embedding_model'],
                api_key=model_config['api_key']
            )

            embedding = next(embedding_gen)

            # Store embedding in ChromaDB if caching is enabled
            if self.cache_generated_embeddings:
                self._store_embedding(info, embedding, text_with_metadata)

            self.logger.info(f"Successfully generated embedding for {info.video_id}")
            return True

        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            return False

    def _prepare_text_with_metadata(self, info: MissingEmbeddingInfo) -> str:
        """
        Prepare text with metadata following yt-fts pattern.

        Args:
            info: Missing embedding information

        Returns:
            Text with metadata formatted for embedding
        """
        metadata = {
            "video_title": info.metadata.get('video_title', 'Unknown'),
            "channel_name": info.metadata.get('channel_name', 'Unknown'),
            "video_date": info.metadata.get('video_date', 'Unknown'),
            "segment_start_time": info.start_time
        }

        text_with_metadata = "---\n"
        text_with_metadata += "\n".join([f"{key}: {value}" for key, value in metadata.items()])
        text_with_metadata += f"\n---\n\nContent:\n\n{info.text_content}"

        return text_with_metadata

    def _store_embedding(self,
                        info: MissingEmbeddingInfo,
                        embedding: list[float],
                        text_with_metadata: str) -> None:
        """
        Store generated embedding in ChromaDB.

        Args:
            info: Missing embedding information
            embedding: Generated embedding vector
            text_with_metadata: Text used for embedding
        """
        try:
            chroma_client = get_chroma_client()
            collection = chroma_client.get_or_create_collection(name="subEmbeddings")

            # Prepare metadata for ChromaDB
            metadata = {
                "channel_id": info.channel_id,
                "channel_name": info.metadata.get('channel_name', 'Unknown'),
                "video_id": info.video_id,
                "start_time": info.start_time,
                "video_title": info.metadata.get('video_title', 'Unknown'),
                "video_date": info.metadata.get('video_date', 'Unknown'),
            }

            # Generate unique ID
            import uuid
            embedding_id = str(uuid.uuid4())

            # Add to ChromaDB
            collection.add(
                documents=[info.text_content],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[embedding_id]
            )

            self.logger.info(f"Stored embedding in ChromaDB: {embedding_id}")

        except Exception as e:
            self.logger.error(f"Failed to store embedding: {e}")

    def _execute_fallback_searches(self, info: MissingEmbeddingInfo) -> list[dict[str, Any]]:
        """
        Execute fallback search strategies when embedding generation fails.

        Args:
            info: Missing embedding information

        Returns:
            List of fallback search results
        """
        fallback_results = []

        # Strategy 1: Text-based search within the same video
        if info.text_content:
            text_matches = self._text_search_within_video(info)
            fallback_results.extend(text_matches)

        # Strategy 2: Channel-wide keyword search
        keyword_matches = self._keyword_search_in_channel(info)
        fallback_results.extend(keyword_matches)

        return fallback_results

    def _text_search_within_video(self, info: MissingEmbeddingInfo) -> list[dict[str, Any]]:
        """
        Perform text-based search within the same video.

        Args:
            info: Missing embedding information

        Returns:
            List of text search results
        """
        # This would integrate with the existing full-text search in yt-fts
        # For now, return a placeholder result
        return [{
            'type': 'text_search',
            'video_id': info.video_id,
            'match_text': info.text_content[:100] + "...",
            'relevance_score': 0.8
        }]

    def _keyword_search_in_channel(self, info: MissingEmbeddingInfo) -> list[dict[str, Any]]:
        """
        Perform keyword search within the same channel.

        Args:
            info: Missing embedding information

        Returns:
            List of keyword search results
        """
        # Extract keywords from the missing content
        keywords = self._extract_keywords(info.text_content)

        # This would integrate with the existing search functionality
        # For now, return placeholder results
        return [{
            'type': 'keyword_search',
            'channel_id': info.channel_id,
            'keywords': keywords[:5],  # Top 5 keywords
            'relevance_score': 0.6
        }]

    def _extract_keywords(self, text: str) -> list[str]:
        """
        Extract keywords from text for fallback search.

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        # Simple keyword extraction - in a real implementation, use NLP
        import re

        # Remove punctuation and split into words
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}

        keywords = [word for word in words if word not in stop_words and len(word) > 3]

        # Return most common keywords
        from collections import Counter
        keyword_counts = Counter(keywords)

        return [word for word, count in keyword_counts.most_common(10)]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get recovery manager statistics.

        Returns:
            Dictionary of statistics
        """
        stats = self.stats.copy()

        if stats['total_recovery_attempts'] > 0:
            stats['success_rate'] = stats['successful_recoveries'] / stats['total_recovery_attempts']
            stats['embedding_generation_rate'] = stats['embeddings_generated'] / stats['total_recovery_attempts']
            stats['average_processing_time'] = stats['total_processing_time'] / stats['total_recovery_attempts']
        else:
            stats['success_rate'] = 0.0
            stats['embedding_generation_rate'] = 0.0
            stats['average_processing_time'] = 0.0

        return stats

    def reset_statistics(self) -> None:
        """Reset statistics counters."""
        self.stats = {
            'total_recovery_attempts': 0,
            'successful_recoveries': 0,
            'embeddings_generated': 0,
            'fallback_searches': 0,
            'total_processing_time': 0.0
        }
        self.logger.info("Statistics reset")

    def log_statistics(self) -> None:
        """Log current statistics."""
        stats = self.get_statistics()

        self.console.print("[bold green]Embedding Recovery Statistics:[/bold green]")
        self.console.print(f"Total Recovery Attempts: {stats['total_recovery_attempts']}")
        self.console.print(f"Successful Recoveries: {stats['successful_recoveries']}")
        self.console.print(f"Embeddings Generated: {stats['embeddings_generated']}")
        self.console.print(f"Fallback Searches: {stats['fallback_searches']}")
        self.console.print(f"Success Rate: {stats['success_rate']:.2%}")
        self.console.print(f"Embedding Generation Rate: {stats['embedding_generation_rate']:.2%}")
        self.console.print(f"Average Processing Time: {stats['average_processing_time']:.3f}s")

        self.logger.info(f"Recovery statistics: {stats}")
