from __future__ import annotations

import logging
import math
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from modules.analysis.chat_search.pattern_recognizer import PatternRecognizer

#!/usr/bin/env python3
"""Enhanced Chat History Search Processor.

Intelligent conversation segmentation, hybrid search enhancement, and performance
optimization for the CSF NIP Chat History Search system.

CSF NIP Constitution §3.6: Evidence-based development with real conversation data
CSF NIP Constitution §3.8: Modular design with clear interfaces
CSF NIP Constitution §3.9: Architectural thinking with performance considerations
"""



# Add CSF NIP paths
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "src" / "lib"))

# Import existing components


class EnhancedConversationSegmenter:
    """Advanced conversation segmentation with intelligent topic detection.

    Identifies high-value conversation segments using pattern recognition,
    temporal analysis, and semantic understanding.
    """

    def __init__(
        self,
        pattern_recognizer: PatternRecognizer | None = None,
        min_segment_length: int = 3,
        topic_similarity_threshold: float = 0.3,
        time_gap_threshold: timedelta = timedelta(hours=1),
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize enhanced conversation segmenter.

        Args:
        ----
            pattern_recognizer: Pattern recognizer instance
            min_segment_length: Minimum entries for a valid segment
            topic_similarity_threshold: Similarity threshold for topic grouping
            time_gap_threshold: Time gap for segment separation
            logger: Logger instance

        """
        self.logger = logger or logging.getLogger(__name__)
        self.pattern_recognizer = pattern_recognizer or PatternRecognizer()
        self.min_segment_length = min_segment_length
        self.topic_similarity_threshold = topic_similarity_threshold
        self.time_gap_threshold = time_gap_threshold

        # Technical vocabulary for topic analysis
        self.technical_vocab = {
            "programming": {
                "python",
                "javascript",
                "java",
                "typescript",
                "go",
                "rust",
                "c++",
                "function",
                "class",
                "method",
            },
            "frameworks": {
                "fastapi",
                "django",
                "flask",
                "react",
                "vue",
                "angular",
                "spring",
                "express",
                "laravel",
            },
            "database": {
                "sql",
                "nosql",
                "postgresql",
                "mysql",
                "mongodb",
                "redis",
                "database",
                "query",
                "table",
                "index",
            },
            "api": {
                "rest",
                "graphql",
                "endpoint",
                "api",
                "http",
                "request",
                "response",
                "json",
                "xml",
            },
            "devops": {
                "docker",
                "kubernetes",
                "ci",
                "cd",
                "deployment",
                "pipeline",
                "jenkins",
                "github",
                "git",
            },
            "testing": {
                "test",
                "testing",
                "pytest",
                "unittest",
                "mock",
                "assert",
                "coverage",
                "tdd",
                "bdd",
            },
        }

    def segment_by_topic(
        self, conversation_history: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Segment conversations by topic changes using semantic analysis.

        Algorithm Approach: Topic modeling with TF-IDF similarity and temporal coherence.
        Uses sliding window analysis to detect topic boundaries based on vocabulary shifts.

        Time Complexity: O(n*m) where n is number of entries, m is vocabulary size
        Space Complexity: O(n) for storing topic vectors and segments

        Args:
        ----
            conversation_history: List of conversation entries with timestamps

        Returns:
        -------
            List of topic segments with metadata

        Example:
        -------
        >>> segmenter = EnhancedConversationSegmenter()
        >>> history = [
        ...     {"display": "Let's discuss database design", "timestamp": 1000},
        ...     {"display": "Now switching to API design", "timestamp": 2000}
        ... ]
        >>> segments = segmenter.segment_by_topic(history)
        >>> len(segments)
        2

        """
        if len(conversation_history) < 2:
            return self._create_single_segment(
                conversation_history, "short_conversation"
            )

        self.logger.info(f"Segmenting {len(conversation_history)} entries by topic")

        # Extract topic vectors for each entry
        topic_vectors = []
        for entry in conversation_history:
            vector = self._extract_topic_vector(entry.get("display", ""))
            topic_vectors.append(
                {
                    "entry": entry,
                    "vector": vector,
                    "dominant_topic": self._identify_dominant_topic(vector),
                },
            )

        # Detect topic boundaries using similarity analysis
        segments = []
        current_segment_start = 0
        current_topic = topic_vectors[0]["dominant_topic"]

        for i in range(1, len(topic_vectors)):
            current_vector = topic_vectors[i]["vector"]
            current_entry_topic = topic_vectors[i]["dominant_topic"]

            # Calculate topic similarity with previous entries
            if current_segment_start < i:
                segment_vector = self._aggregate_segment_vector(
                    topic_vectors[current_segment_start:i]
                )
                similarity = self._calculate_topic_similarity(
                    current_vector, segment_vector
                )
            else:
                similarity = 0.0

            # Check for topic boundary - more lenient conditions
            has_topic_change = current_entry_topic not in (current_topic, "general")
            has_low_similarity = similarity < self.topic_similarity_threshold
            has_time_gap = self._has_significant_time_gap(
                topic_vectors[i - 1]["entry"],
                topic_vectors[i]["entry"],
            )

            # Create segment if any boundary condition is met
            if has_topic_change or has_low_similarity or has_time_gap:
                # Create segment before boundary
                segment_entries = [
                    tv["entry"] for tv in topic_vectors[current_segment_start:i]
                ]
                if len(segment_entries) >= 1:  # Allow shorter segments
                    segment = self._create_topic_segment(
                        segment_entries,
                        topic_vectors[current_segment_start:i],
                        current_topic,
                    )
                    segments.append(segment)

                # Start new segment
                current_segment_start = i
                current_topic = current_entry_topic

        # Add final segment
        final_entries = [tv["entry"] for tv in topic_vectors[current_segment_start:]]
        if len(final_entries) >= 1:  # Allow shorter segments
            segment = self._create_topic_segment(
                final_entries,
                topic_vectors[current_segment_start:],
                current_topic,
            )
            segments.append(segment)

        self.logger.info(f"Created {len(segments)} topic segments")
        return segments

    def _extract_topic_vector(self, text: str) -> dict[str, float]:
        """Extract topic vector from text using TF-IDF weighting.

        Args:
        ----
            text: Text to analyze

        Returns:
        -------
            Dictionary mapping topics to relevance scores

        """
        text_lower = text.lower()
        words = set(re.findall(r"\b\w+\b", text_lower))
        topic_vector = {}

        for topic, vocab in self.technical_vocab.items():
            # Count vocabulary matches
            matches = len(words.intersection(vocab))
            if matches > 0:
                # Simple TF-IDF inspired scoring
                tf = matches / len(words)
                # Approximate IDF (inverse document frequency) based on topic specificity
                idf = math.log(1 + len(vocab))
                topic_vector[topic] = tf * idf

        return topic_vector

    def _identify_dominant_topic(self, topic_vector: dict[str, float]) -> str:
        """Identify the dominant topic from a topic vector.

        Args:
        ----
            topic_vector: Topic relevance scores

        Returns:
        -------
            Dominant topic name or "general"

        """
        if not topic_vector:
            return "general"

        return max(topic_vector.items(), key=lambda x: x[1])[0]

    def _calculate_topic_similarity(
        self, vector1: dict[str, float], vector2: dict[str, float]
    ) -> float:
        """Calculate cosine similarity between two topic vectors.

        Args:
        ----
            vector1: First topic vector
            vector2: Second topic vector

        Returns:
        -------
            Cosine similarity score (0.0 to 1.0)

        """
        if not vector1 or not vector2:
            return 0.0

        # Get all topics
        all_topics = set(vector1.keys()).union(set(vector2.keys()))

        # Calculate dot product and magnitudes
        dot_product = sum(
            vector1.get(topic, 0) * vector2.get(topic, 0) for topic in all_topics
        )
        mag1 = math.sqrt(sum(score**2 for score in vector1.values()))
        mag2 = math.sqrt(sum(score**2 for score in vector2.values()))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def _aggregate_segment_vector(
        self, topic_vectors: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Aggregate multiple topic vectors into a segment vector.

        Args:
        ----
            topic_vectors: List of topic vectors with metadata

        Returns:
        -------
            Aggregated topic vector

        """
        if not topic_vectors:
            return {}

        # Average all vectors
        aggregated = {}
        for topic_data in topic_vectors:
            vector = topic_data["vector"]
            for topic, score in vector.items():
                aggregated[topic] = aggregated.get(topic, 0) + score

        # Normalize by number of vectors
        for topic in aggregated:
            aggregated[topic] /= len(topic_vectors)

        return aggregated

    def _has_significant_time_gap(
        self, entry1: dict[str, Any], entry2: dict[str, Any]
    ) -> bool:
        """Check if there's a significant time gap between entries.

        Args:
        ----
            entry1: First entry
            entry2: Second entry

        Returns:
        -------
            True if time gap exceeds threshold

        """
        ts1 = entry1.get("timestamp", 0) / 1000
        ts2 = entry2.get("timestamp", 0) / 1000

        time_diff = datetime.fromtimestamp(ts2) - datetime.fromtimestamp(ts1)
        return time_diff > self.time_gap_threshold

    def _create_topic_segment(
        self,
        entries: list[dict[str, Any]],
        topic_vectors: list[dict[str, Any]],
        dominant_topic: str,
    ) -> dict[str, Any]:
        """Create a topic segment with metadata.

        Args:
        ----
            entries: Conversation entries in the segment
            topic_vectors: Topic vectors for entries
            dominant_topic: Dominant topic for the segment

        Returns:
        -------
            Segment dictionary with metadata

        """
        # Calculate segment statistics
        segment_vector = self._aggregate_segment_vector(topic_vectors)
        confidence = max(segment_vector.values()) if segment_vector else 0.5

        # Analyze patterns in segment
        segment_text = " ".join(entry.get("display", "") for entry in entries)
        patterns = self.pattern_recognizer.identify_patterns(segment_text)

        return {
            "entries": entries,
            "start_time": entries[0].get("timestamp", 0),
            "end_time": entries[-1].get("timestamp", 0),
            "entry_count": len(entries),
            "topic": dominant_topic,
            "topic_vector": segment_vector,
            "confidence": min(
                confidence + 0.2, 1.0
            ),  # Boost confidence for coherent segments
            "patterns": patterns,
            "metadata": {
                "has_code": len(patterns.get("code_blocks", [])) > 0,
                "question_count": len(patterns.get("questions", [])),
                "solution_count": len(patterns.get("solutions", [])),
                "technical_keywords": patterns.get("technical_keywords", []),
                "segment_type": self._classify_segment_type(patterns),
                "value_score": self._calculate_segment_value_score(patterns),
            },
        }

    def _classify_segment_type(self, patterns: dict[str, Any]) -> str:
        """Classify the type of segment based on patterns.

        Args:
        ----
            patterns: Identified patterns

        Returns:
        -------
            Segment type classification

        """
        code_count = len(patterns.get("code_blocks", []))
        question_count = len(patterns.get("questions", []))
        solution_count = len(patterns.get("solutions", []))
        error_count = len(patterns.get("error_patterns", []))

        if error_count > 0:
            return "debugging"
        if code_count > 0 and solution_count > 0:
            return "implementation"
        if question_count > 0 and solution_count > 0:
            return "q_and_a"
        if code_count > 0:
            return "code_discussion"
        if question_count > 0:
            return "question"
        return "general"

    def _calculate_segment_value_score(self, patterns: dict[str, Any]) -> float:
        """Calculate value score for a segment based on patterns.

        Args:
        ----
            patterns: Identified patterns

        Returns:
        -------
            Value score between 0.0 and 1.0

        """
        score = 0.0

        # Code blocks are valuable
        code_blocks = patterns.get("code_blocks", [])
        for code_block in code_blocks:
            score += 0.3 * code_block.get("confidence", 0.5)

        # Solutions are very valuable
        solutions = patterns.get("solutions", [])
        score += len(solutions) * 0.4

        # Questions and answers are valuable
        questions = patterns.get("questions", [])
        score += len(questions) * 0.2

        # Technical keywords indicate valuable content
        tech_keywords = patterns.get("technical_keywords", [])
        score += min(len(tech_keywords) * 0.05, 0.3)

        # Error analysis is valuable for troubleshooting
        error_patterns = patterns.get("error_patterns", [])
        score += len(error_patterns) * 0.3

        return min(score, 1.0)

    def _create_single_segment(
        self, entries: list[dict[str, Any]], segment_type: str
    ) -> list[dict[str, Any]]:
        """Create a single segment for short conversations.

        Args:
        ----
            entries: Conversation entries
            segment_type: Type of single segment

        Returns:
        -------
            List with single segment

        """
        segment_text = " ".join(entry.get("display", "") for entry in entries)
        patterns = self.pattern_recognizer.identify_patterns(segment_text)

        segment = {
            "entries": entries,
            "start_time": entries[0].get("timestamp", 0) if entries else 0,
            "end_time": entries[-1].get("timestamp", 0) if entries else 0,
            "entry_count": len(entries),
            "topic": "general",
            "topic_vector": {},
            "confidence": 0.5,
            "patterns": patterns,
            "metadata": {
                "has_code": len(patterns.get("code_blocks", [])) > 0,
                "question_count": len(patterns.get("questions", [])),
                "solution_count": len(patterns.get("solutions", [])),
                "technical_keywords": patterns.get("technical_keywords", []),
                "segment_type": segment_type,
                "value_score": self._calculate_segment_value_score(patterns),
            },
        }

        return [segment]

    def identify_high_value_segments(
        self,
        conversation: list[dict[str, Any]],
        value_threshold: float = 0.3,  # Lower threshold for testing
    ) -> list[dict[str, Any]]:
        """Identify high-value conversation segments.

        Args:
        ----
            conversation: Conversation entries
            value_threshold: Minimum value score for high-value segments

        Returns:
        -------
            List of high-value segments

        """
        segments = self.segment_by_topic(conversation)
        high_value_segments = []

        for segment in segments:
            value_score = segment["metadata"]["value_score"]
            # Also consider segments with code or solutions as high-value
            has_code_or_solutions = (
                segment["metadata"]["has_code"]
                or segment["metadata"]["solution_count"] > 0
            )

            if value_score >= value_threshold or has_code_or_solutions:
                segment["value_ranking"] = value_score
                high_value_segments.append(segment)

        # Sort by value score
        high_value_segments.sort(key=lambda x: x["value_ranking"], reverse=True)

        self.logger.info(f"Identified {len(high_value_segments)} high-value segments")
        return high_value_segments

    def extract_code_solutions(
        self, conversation: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Extract complete code solutions from conversation.

        Args:
        ----
            conversation: Conversation entries

        Returns:
        -------
            List of code solutions with context

        """
        code_solutions = []

        for entry in conversation:
            text = entry.get("display", "")
            patterns = self.pattern_recognizer.identify_patterns(text)

            code_blocks = patterns.get("code_blocks", [])
            solutions = patterns.get("solutions", [])

            # Look for code with solution indicators or implementation patterns
            solution_indicators = [
                "solution",
                "implement",
                "here's",
                "try this",
                "the way to",
                "you need to",
                "this creates",
                "use this",
                "function",
                "class",
            ]

            has_solution_indicator = any(
                indicator in text.lower() for indicator in solution_indicators
            )

            if code_blocks and (solutions or has_solution_indicator):
                # This looks like a code solution
                code_solution = {
                    "code": code_blocks[0]["text"],
                    "language": code_blocks[0]["language"],
                    "explanation": text,
                    "context": [entry],
                    "confidence": code_blocks[0]["confidence"],
                    "timestamp": entry.get("timestamp", 0),
                    "indicators": [
                        ind for ind in solution_indicators if ind in text.lower()
                    ],
                }
                code_solutions.append(code_solution)

        return code_solutions

    def segment_by_time(
        self, coherent_entries: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Segment conversations by temporal coherence.

        Args:
        ----
            coherent_entries: List of conversation entries

        Returns:
        -------
            List of time-based segments

        """
        if not coherent_entries:
            return []

        segments = []
        current_segment = [coherent_entries[0]]

        for i in range(1, len(coherent_entries)):
            current_entry = coherent_entries[i]
            previous_entry = coherent_entries[i - 1]

            if self._has_significant_time_gap(previous_entry, current_entry):
                # Create segment before gap
                if (
                    len(current_segment) >= 1
                ):  # Allow shorter segments for time-based segmentation
                    segment = self._create_time_segment(current_segment)
                    segments.append(segment)

                # Start new segment
                current_segment = [current_entry]
            else:
                current_segment.append(current_entry)

        # Add final segment
        if (
            len(current_segment) >= 1
        ):  # Allow shorter segments for time-based segmentation
            segment = self._create_time_segment(current_segment)
            segments.append(segment)

        return segments

    def _create_time_segment(self, entries: list[dict[str, Any]]) -> dict[str, Any]:
        """Create a time-based segment with metadata.

        Args:
        ----
            entries: Entries in the time segment

        Returns:
        -------
            Time segment dictionary

        """
        segment_text = " ".join(entry.get("display", "") for entry in entries)
        patterns = self.pattern_recognizer.identify_patterns(segment_text)

        return {
            "entries": entries,
            "start_time": entries[0].get("timestamp", 0),
            "end_time": entries[-1].get("timestamp", 0),
            "entry_count": len(entries),
            "duration": (
                entries[-1].get("timestamp", 0) - entries[0].get("timestamp", 0)
            )
            / 1000,
            "patterns": patterns,
            "metadata": {
                "has_code": len(patterns.get("code_blocks", [])) > 0,
                "question_count": len(patterns.get("questions", [])),
                "solution_count": len(patterns.get("solutions", [])),
                "segment_type": "time_based",
                "value_score": self._calculate_segment_value_score(patterns),
            },
        }


class EnhancedHybridSearcher:
    """Enhanced hybrid search with context-aware weighting and semantic understanding."""

    def __init__(
        self,
        tfidf_weight: float = 0.3,
        vector_weight: float = 0.7,
        enable_temporal_decay: bool = True,
        semantic_threshold: float = 0.3,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize enhanced hybrid searcher.

        Args:
        ----
            tfidf_weight: Weight for TF-IDF search results
            vector_weight: Weight for vector search results
            enable_temporal_decay: Enable temporal decay for recent content
            semantic_threshold: Minimum semantic similarity threshold
            logger: Logger instance

        """
        self.logger = logger or logging.getLogger(__name__)
        self.tfidf_weight = tfidf_weight
        self.vector_weight = vector_weight
        self.enable_temporal_decay = enable_temporal_decay
        self.semantic_threshold = semantic_threshold

        # For now, create a placeholder for the hybrid searcher
        # In a real implementation, this would integrate with the existing HybridSearcher
        self.documents = []
        self.index_built = False

    def add_documents(self, documents: list[dict[str, Any]]) -> list[str]:
        """Add documents to the search index.

        Args:
        ----
            documents: List of documents with 'text' and metadata

        Returns:
        -------
            List of document IDs

        """
        document_ids = []
        for i, doc in enumerate(documents):
            doc_id = f"doc_{i}_{hash(doc['text']) % 10000}"
            document_ids.append(doc_id)
            doc["id"] = doc_id
            self.documents.append(doc)

        self.index_built = True
        self.logger.info(f"Added {len(documents)} documents to hybrid search index")
        return document_ids

    def search(
        self,
        query: str,
        limit: int = 10,
        tfidf_limit: int = 50,
        vector_limit: int = 50,
        score_threshold: float = 0.1,
        semantic_threshold: float | None = None,
    ) -> list[dict[str, Any]]:
        """Perform enhanced hybrid search.

        Args:
        ----
            query: Search query
            limit: Maximum number of results
            tfidf_limit: Maximum TF-IDF results to consider
            vector_limit: Maximum vector results to consider
            score_threshold: Minimum combined score threshold
            semantic_threshold: Semantic similarity threshold override

        Returns:
        -------
            List of hybrid search results

        """
        if not self.index_built:
            self.logger.warning("Search index not built, returning empty results")
            return []

        semantic_threshold = semantic_threshold or self.semantic_threshold
        self.logger.info(f"Hybrid search for: '{query}'")

        # Perform TF-IDF search (simplified implementation)
        tfidf_results = self._simple_tfidf_search(query, tfidf_limit)

        # Perform semantic search (simplified implementation)
        vector_results = self._simple_vector_search(query, vector_limit)

        # Combine results
        combined_results = self._combine_results(tfidf_results, vector_results)

        # Filter by threshold and sort
        filtered_results = [
            result
            for result in combined_results
            if result["combined_score"] >= score_threshold
        ]

        filtered_results.sort(key=lambda x: x["combined_score"], reverse=True)

        self.logger.info(f"Returning {len(filtered_results[:limit])} hybrid results")
        return filtered_results[:limit]

    def _simple_tfidf_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Simple TF-IDF implementation for demonstration."""
        query_words = set(query.lower().split())
        results = []

        for doc in self.documents:
            doc_words = set(doc["text"].lower().split())
            common_words = query_words.intersection(doc_words)

            if common_words:
                score = len(common_words) / len(query_words)
                if self.enable_temporal_decay:
                    score *= self._apply_temporal_decay(doc)

                result = {
                    "document_id": doc["id"],
                    "tfidf_score": score,
                    "vector_score": 0.0,
                    "combined_score": 0.0,
                    "text": doc["text"][:200],
                    "matched_tokens": list(common_words),
                    "source": "tfidf",
                    "metadata": doc.get("metadata", {}),
                    "temporal_boost": 1.0,
                }
                results.append(result)

        return sorted(results, key=lambda x: x["tfidf_score"], reverse=True)[:limit]

    def _simple_vector_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Simple vector search implementation for demonstration."""
        # This is a simplified implementation - in reality would use embeddings
        query_words = set(query.lower().split())
        results = []

        for doc in self.documents:
            doc_words = set(doc["text"].lower().split())
            overlap = len(query_words.intersection(doc_words))
            total_unique = len(query_words.union(doc_words))

            if total_unique > 0:
                # Jaccard similarity as a proxy for semantic similarity
                score = overlap / total_unique
                if score >= self.semantic_threshold:
                    if self.enable_temporal_decay:
                        score *= self._apply_temporal_decay(doc)

                    result = {
                        "document_id": doc["id"],
                        "tfidf_score": 0.0,
                        "vector_score": score,
                        "combined_score": 0.0,
                        "text": doc["text"][:200],
                        "matched_tokens": list(query_words.intersection(doc_words)),
                        "source": "vector",
                        "metadata": doc.get("metadata", {}),
                        "temporal_boost": 1.0,
                    }
                    results.append(result)

        return sorted(results, key=lambda x: x["vector_score"], reverse=True)[:limit]

    def _apply_temporal_decay(self, doc: dict[str, Any]) -> float:
        """Apply temporal decay to boost recent content."""
        if not self.enable_temporal_decay:
            return 1.0

        # Get document timestamp
        timestamp = doc.get("metadata", {}).get("timestamp", 0)
        if timestamp == 0:
            return 1.0

        # Calculate age in days
        doc_time = datetime.fromtimestamp(timestamp / 1000)
        age_days = (datetime.now() - doc_time).days

        # Apply decay: recent content gets higher scores
        decay_factor = math.exp(-age_days / 30)  # 30-day half-life
        return 1.0 + (1.0 - decay_factor)  # Boost between 1.0 and 2.0

    def _combine_results(
        self,
        tfidf_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Combine TF-IDF and vector search results."""
        combined_map = {}

        # Process TF-IDF results
        for result in tfidf_results:
            doc_id = result["document_id"]
            combined_map[doc_id] = result.copy()
            # Store temporal boost separately
            combined_map[doc_id]["temporal_boost"] = result.get("temporal_boost", 1.0)

        # Process and merge vector results
        for result in vector_results:
            doc_id = result["document_id"]
            if doc_id in combined_map:
                # Merge with existing result
                combined_map[doc_id]["vector_score"] = result["vector_score"]
                combined_map[doc_id]["source"] = "hybrid"
                # Merge metadata
                if "metadata" in result:
                    combined_map[doc_id]["metadata"].update(result["metadata"])
            else:
                # Add new result
                combined_map[doc_id] = result.copy()
                combined_map[doc_id]["temporal_boost"] = result.get(
                    "temporal_boost", 1.0
                )

        # Calculate combined scores
        for doc_id, result in combined_map.items():
            # Normalize scores
            tfidf_norm = result["tfidf_score"]
            vector_norm = result["vector_score"]

            # Apply context-aware weighting
            if result.get("metadata", {}).get("has_code", False):
                # Boost code-heavy results for vector search
                vector_weight = self.vector_weight * 1.2
                tfidf_weight = self.tfidf_weight * 0.8
            elif result.get("metadata", {}).get("is_exact_match", False):
                # Boost exact matches for TF-IDF search
                tfidf_weight = self.tfidf_weight * 1.3
                vector_weight = self.vector_weight * 0.7
            else:
                tfidf_weight = self.tfidf_weight
                vector_weight = self.vector_weight

            # Normalize weights
            total_weight = tfidf_weight + vector_weight
            tfidf_weight /= total_weight
            vector_weight /= total_weight

            combined_score = tfidf_norm * tfidf_weight + vector_norm * vector_weight

            # Apply temporal boost
            temporal_boost = result.get("temporal_boost", 1.0)
            result["combined_score"] = combined_score * temporal_boost
            result["temporal_boost"] = temporal_boost

        return list(combined_map.values())


class PerformanceOptimizer:
    """Performance optimization for large conversation histories."""

    def __init__(
        self,
        enable_cache: bool = True,
        cache_size: int = 1000,
        diversity_threshold: float = 0.8,
        memory_limit_mb: int = 500,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize performance optimizer.

        Args:
        ----
            enable_cache: Enable result caching
            cache_size: Maximum cache size
            diversity_threshold: Similarity threshold for diversity filtering
            memory_limit_mb: Memory limit for indexing
            logger: Logger instance

        """
        self.logger = logger or logging.getLogger(__name__)
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        self.diversity_threshold = diversity_threshold
        self.memory_limit_mb = memory_limit_mb

        # Simple LRU cache implementation
        self.search_cache = {} if enable_cache else None

    def optimize_search(
        self,
        conversation_history: list[dict[str, Any]],
        query: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Optimize search for large conversation histories.

        Args:
        ----
            conversation_history: Large conversation dataset
            query: Search query
            limit: Maximum results

        Returns:
        -------
            Optimized search results

        """
        self.logger.info(f"Optimizing search for {len(conversation_history)} entries")

        # Check cache first
        cache_key = f"{query}_{limit}" if self.enable_cache else None
        if cache_key and cache_key in self.search_cache:
            self.logger.debug("Returning cached results")
            return self.search_cache[cache_key]

        # For large datasets, use sampling or indexing strategies
        if len(conversation_history) > 10000:
            results = self._search_large_dataset(conversation_history, query, limit)
        else:
            results = self._search_standard_dataset(conversation_history, query, limit)

        # Cache results if enabled
        if cache_key and self.enable_cache:
            self._cache_result(cache_key, results)

        return results

    def _search_large_dataset(
        self,
        conversation_history: list[dict[str, Any]],
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search strategy for very large datasets."""
        # Use a combination of strategies for large datasets

        # 1. Quick keyword filtering
        query_words = set(query.lower().split())
        filtered = []

        for entry in conversation_history:
            text = entry.get("display", "").lower()
            words = set(text.split())
            if query_words.intersection(words):
                filtered.append(entry)

        # 2. If still too many results, use time-based sampling
        if len(filtered) > 5000:
            filtered = self._time_based_sample(filtered, 2000)

        # 3. Apply diversity filtering
        diverse_results = self.apply_diversity_filtering(
            filtered, self.diversity_threshold
        )

        # 4. Limit results
        return diverse_results[:limit]

    def _search_standard_dataset(
        self,
        conversation_history: list[dict[str, Any]],
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Standard search for moderate datasets."""
        query_words = set(query.lower().split())
        results = []

        for entry in conversation_history:
            text = entry.get("display", "").lower()
            words = set(text.split())
            common_words = query_words.intersection(words)

            if common_words:
                score = len(common_words) / len(query_words)
                result = entry.copy()
                result["relevance_score"] = score
                result["matched_words"] = list(common_words)
                results.append(result)

        # Sort by relevance and limit
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:limit]

    def _time_based_sample(
        self, entries: list[dict[str, Any]], target_size: int
    ) -> list[dict[str, Any]]:
        """Sample entries by time to get recent and diverse content."""
        if len(entries) <= target_size:
            return entries

        # Sort by timestamp
        sorted_entries = sorted(
            entries, key=lambda x: x.get("timestamp", 0), reverse=True
        )

        # Take recent entries (70%) and sample older entries (30%)
        recent_count = int(target_size * 0.7)
        older_count = target_size - recent_count

        recent_entries = sorted_entries[:recent_count]

        # Sample from older entries
        older_entries = sorted_entries[recent_count:]
        if len(older_entries) > older_count:
            import random

            older_entries = random.sample(older_entries, older_count)

        return recent_entries + older_entries

    def apply_diversity_filtering(
        self,
        results: list[dict[str, Any]],
        similarity_threshold: float,
    ) -> list[dict[str, Any]]:
        """Apply diversity filtering to avoid redundant results.

        Args:
        ----
            results: Search results
            similarity_threshold: Similarity threshold for filtering

        Returns:
        -------
            Diverse results

        """
        if not results:
            return []

        diverse_results = [
            results[0]
        ]  # Always include the first (highest scoring) result

        for result in results[1:]:
            is_similar = False
            result_text = set(result.get("display", "").lower().split())

            for diverse_result in diverse_results:
                diverse_text = set(diverse_result.get("display", "").lower().split())

                # Calculate Jaccard similarity
                intersection = result_text.intersection(diverse_text)
                union = result_text.union(diverse_text)

                if union and len(intersection) / len(union) > similarity_threshold:
                    is_similar = True
                    break

            if not is_similar:
                diverse_results.append(result)

        return diverse_results

    def cached_search(
        self,
        query: str,
        documents: list[dict[str, Any]],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Perform cached search with intelligent caching."""
        if not self.enable_cache:
            return self._search_standard_dataset(documents, query, limit)

        cache_key = f"{hash(query)}_{len(documents)}_{limit}"

        if cache_key in self.search_cache:
            self.logger.debug(f"Cache hit for query: {query}")
            return self.search_cache[cache_key]

        # Perform search
        results = self._search_standard_dataset(documents, query, limit)

        # Cache result
        self._cache_result(cache_key, results)

        return results

    def _cache_result(self, cache_key: str, results: list[dict[str, Any]]) -> None:
        """Cache search results with LRU eviction."""
        if not self.enable_cache or not self.search_cache:
            return

        # Simple LRU: if cache is full, remove oldest entry
        if len(self.search_cache) >= self.cache_size:
            # Remove the first item (simple FIFO for demonstration)
            first_key = next(iter(self.search_cache))
            del self.search_cache[first_key]

        self.search_cache[cache_key] = results

    def create_memory_efficient_index(
        self,
        large_dataset: list[dict[str, Any]],
        memory_limit_mb: int,
    ) -> dict[str, Any]:
        """Create memory-efficient index for large datasets.

        Args:
        ----
            large_dataset: Large dataset to index
            memory_limit_mb: Memory limit in MB

        Returns:
        -------
            Memory-efficient index structure

        """
        # Estimate memory usage
        estimated_usage = self.estimate_memory_usage(large_dataset)
        self.logger.info(f"Estimated memory usage: {estimated_usage:.1f}MB")

        if estimated_usage <= memory_limit_mb:
            # Can use standard indexing
            return {
                "documents": large_dataset,
                "compressed_index": False,
                "memory_usage_mb": estimated_usage,
                "index_type": "standard",
            }

        # Use compressed indexing for large datasets
        compressed_index = self._create_compressed_index(large_dataset)
        return {
            "documents": large_dataset[:1000],  # Keep recent documents in memory
            "compressed_index": compressed_index,
            "compressed_size_mb": memory_limit_mb,
            "memory_usage_mb": memory_limit_mb,
            "index_type": "compressed",
        }

    def _create_compressed_index(self, dataset: list[dict[str, Any]]) -> dict[str, Any]:
        """Create compressed index structure."""
        # This is a simplified implementation
        # In reality, would use more sophisticated compression techniques

        # Create word frequency index
        word_index = {}
        for i, doc in enumerate(dataset):
            words = set(doc.get("display", "").lower().split())
            for word in words:
                if word not in word_index:
                    word_index[word] = []
                word_index[word].append(i)

        return {
            "word_index": word_index,
            "document_count": len(dataset),
            "compression_ratio": len(dataset) / 1000,  # Simplified metric
        }

    def estimate_memory_usage(self, dataset: list[dict[str, Any]]) -> float:
        """Estimate memory usage for dataset in MB."""
        import sys

        total_size = 0
        sample_size = min(100, len(dataset))
        sample = dataset[:sample_size]

        for item in sample:
            total_size += sys.getsizeof(item)

        # Extrapolate to full dataset
        avg_size = total_size / sample_size if sample_size > 0 else 0
        estimated_total = avg_size * len(dataset)

        return estimated_total / (1024 * 1024)  # Convert to MB

    def optimize_query(self, query: str) -> dict[str, Any]:
        """Optimize query for better search performance.

        Args:
        ----
            query: Original search query

        Returns:
        -------
            Optimized query information

        """
        # Extract key terms
        words = query.lower().split()
        key_terms = []

        # Filter stop words and extract meaningful terms
        stop_words = {
            "the",
            "is",
            "at",
            "which",
            "on",
            "and",
            "a",
            "to",
            "are",
            "as",
            "was",
            "with",
            "for",
            "of",
            "in",
            "it",
            "i",
            "you",
            "that",
        }

        for word in words:
            if len(word) > 2 and word not in stop_words:
                key_terms.append(word)

        # Simplified query
        simplified_query = " ".join(key_terms)

        return {
            "original_query": query,
            "simplified_query": simplified_query,
            "key_terms": key_terms,
            "term_count": len(key_terms),
            "optimization_applied": len(key_terms) < len(words),
        }


class EnhancedCHSProcessor:
    """Main Enhanced CHS Processor integrating all components."""

    def __init__(
        self,
        chat_history_path: Path | None = None,
        enable_pattern_recognition: bool = True,
        enable_segmentation: bool = True,
        enable_hybrid_search: bool = True,
        enable_performance_optimization: bool = True,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize Enhanced CHS Processor.

        Args:
        ----
            chat_history_path: Path to chat history file
            enable_pattern_recognition: Enable pattern recognition features
            enable_segmentation: Enable conversation segmentation
            enable_hybrid_search: Enable enhanced hybrid search
            enable_performance_optimization: Enable performance optimization
            logger: Logger instance

        """
        self.logger = logger or logging.getLogger(__name__)
        self.chat_history_path = chat_history_path

        # Initialize components
        self.pattern_recognizer = (
            PatternRecognizer() if enable_pattern_recognition else None
        )
        self.segmenter = (
            EnhancedConversationSegmenter(
                pattern_recognizer=self.pattern_recognizer,
            )
            if enable_segmentation
            else None
        )
        self.hybrid_searcher = (
            EnhancedHybridSearcher() if enable_hybrid_search else None
        )
        self.performance_optimizer = (
            PerformanceOptimizer() if enable_performance_optimization else None
        )

        # Index storage
        self.conversations_indexed = False
        self.indexed_conversations = []

    def index_conversations(self, conversations: list[dict[str, Any]]) -> bool:
        """Index conversations for enhanced search.

        Args:
        ----
            conversations: List of conversation entries

        Returns:
        -------
            True if indexing successful

        """
        try:
            self.logger.info(f"Indexing {len(conversations)} conversations")

            self.indexed_conversations = conversations

            # Index in hybrid searcher if available
            if self.hybrid_searcher:
                documents = []
                for conv in conversations:
                    doc = {
                        "text": conv.get("display", ""),
                        "metadata": {
                            "timestamp": conv.get("timestamp", 0),
                            "project": conv.get("project", ""),
                        },
                    }
                    documents.append(doc)

                self.hybrid_searcher.add_documents(documents)

            self.conversations_indexed = True
            self.logger.info("Successfully indexed conversations")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to index conversations: {e}")
            return False

    def search(
        self,
        query: str,
        limit: int = 20,
        enable_patterns: bool = True,
        enable_segmentation: bool = False,
        use_hybrid_search: bool = False,
    ) -> list[dict[str, Any]]:
        """Enhanced search with multiple search modes.

        Args:
        ----
            query: Search query
            limit: Maximum results
            enable_patterns: Enable pattern recognition in results
            enable_segmentation: Enable conversation segmentation
            use_hybrid_search: Use enhanced hybrid search

        Returns:
        -------
            Search results with enhanced metadata

        """
        try:
            if not self.conversations_indexed:
                self.logger.warning(
                    "Conversations not indexed, returning empty results"
                )
                return []

            self.logger.info(f"Enhanced search for: '{query}'")

            # Choose search method
            if use_hybrid_search and self.hybrid_searcher:
                # Use enhanced hybrid search
                documents = [
                    {"text": conv.get("display", ""), "metadata": conv}
                    for conv in self.indexed_conversations
                ]
                self.hybrid_searcher.add_documents(documents)
                results = self.hybrid_searcher.search(query, limit=limit)
            # Use performance-optimized search
            elif self.performance_optimizer:
                results = self.performance_optimizer.optimize_search(
                    self.indexed_conversations,
                    query,
                    limit,
                )
            else:
                # Fallback to simple search
                results = self._simple_search(query, limit)

            # Enhance results with patterns if requested
            if enable_patterns and self.pattern_recognizer:
                results = self._enhance_with_patterns(results)

            # Apply segmentation if requested
            if enable_segmentation and self.segmenter:
                results = self._apply_segmentation(results, query)

            return results

        except Exception as e:
            self.logger.exception(f"Search failed: {e}")
            return []

    def _simple_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Simple fallback search implementation."""
        query_words = set(query.lower().split())
        results = []

        for conv in self.indexed_conversations:
            text = conv.get("display", "").lower()
            words = set(text.split())
            common_words = query_words.intersection(words)

            if common_words:
                score = len(common_words) / len(query_words)
                result = conv.copy()
                result["relevance_score"] = score
                result["matched_words"] = list(common_words)
                results.append(result)

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:limit]

    def _enhance_with_patterns(
        self, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Enhance search results with pattern recognition."""
        for result in results:
            text = result.get("display", "")
            patterns = self.pattern_recognizer.identify_patterns(text)
            result["patterns"] = patterns
            result["pattern_summary"] = self.pattern_recognizer.get_pattern_summary(
                patterns
            )

        return results

    def _apply_segmentation(
        self, results: list[dict[str, Any]], query: str
    ) -> list[dict[str, Any]]:
        """Apply conversation segmentation to results."""
        if len(results) < 3:
            return results

        # Extract conversations from results
        conversations = [result for result in results if "display" in result]
        if not conversations:
            return results

        # Segment and find relevant segments
        segments = self.segmenter.segment_by_topic(conversations)
        high_value_segments = self.segmenter.identify_high_value_segments(conversations)

        # Add segmentation information to results
        for result in results:
            result["segment_info"] = {
                "segments_found": len(segments),
                "high_value_segments": len(high_value_segments),
                "segmentation_applied": True,
            }

        return results

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status."""
        status = {
            "conversations_indexed": self.conversations_indexed,
            "indexed_conversation_count": len(self.indexed_conversations),
            "components": {
                "pattern_recognizer": self.pattern_recognizer is not None,
                "segmenter": self.segmenter is not None,
                "hybrid_searcher": self.hybrid_searcher is not None,
                "performance_optimizer": self.performance_optimizer is not None,
            },
            "chat_history_path": (
                str(self.chat_history_path) if self.chat_history_path else None
            ),
        }

        # Add component-specific status
        if self.hybrid_searcher:
            status["hybrid_search_status"] = {
                "documents_indexed": len(self.hybrid_searcher.documents),
                "index_built": self.hybrid_searcher.index_built,
            }

        if self.performance_optimizer:
            status["performance_status"] = {
                "cache_enabled": self.performance_optimizer.enable_cache,
                "cache_size": (
                    len(self.performance_optimizer.search_cache)
                    if self.performance_optimizer.search_cache
                    else 0
                ),
            }

        return status
