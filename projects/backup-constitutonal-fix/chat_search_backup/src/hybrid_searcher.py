from __future__ import annotations

import logging
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    # Try absolute import first
    from src.lib.core_utils.embedding_manager import ComponentManager, EmbeddingManager
    from src.lib.core_utils.vector_store import VectorStore
except ImportError:
    try:
        # Fallback to relative import from project root
        from lib.core_utils.embedding_manager import ComponentManager, EmbeddingManager
        from lib.core_utils.vector_store import VectorStore
    except ImportError as e:
        # Final fallback - provide error message
        raise ImportError(
            f"RAG dependencies not available: {e}. "
            "Ensure src/lib/core_utils/ is in Python path or install required packages."
        )

#!/usr/bin/env python3
"""Hybrid Searcher.

TF-IDF + vector search integration for CSF NIP RAG implementation.
Combines traditional keyword search with semantic similarity for optimal results.
"""



# Add CSF NIP paths
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "src" / "lib"))



class HybridSearcher:
    """Hybrid search combining TF-IDF keyword search with vector semantic search.

    Provides optimal search results by leveraging both exact keyword matching
    and semantic understanding for conversational data.
    """

    def __init__(
        self,
        vector_store: VectorStore | None = None,
        embedding_manager: EmbeddingManager | None = None,
        tfidf_weight: float = 0.3,
        vector_weight: float = 0.7,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize hybrid searcher.

        Args:
        ----
            vector_store: Vector store instance (created if None)
            embedding_manager: Embedding manager instance (created if None)
            tfidf_weight: Weight for TF-IDF search results (0-1)
            vector_weight: Weight for vector search results (0-1)
            logger: Logger instance

        """
        self.logger = logger or logging.getLogger(__name__)

        # Validate weights
        if not math.isclose(tfidf_weight + vector_weight, 1.0, rel_tol=0.01):
            self.logger.warning("Weights don't sum to 1.0, normalizing...")
            total = tfidf_weight + vector_weight
            tfidf_weight /= total
            vector_weight /= total

        self.tfidf_weight = tfidf_weight
        self.vector_weight = vector_weight

        # Initialize components using singleton manager
        self.vector_store = vector_store or ComponentManager.get_vector_store()
        self.embedding_manager = (
            embedding_manager or ComponentManager.get_embedding_manager()
        )

        # TF-IDF data structures
        self.vocabulary: dict[str, dict[str, Any]] = {}
        self.document_frequency: dict[str, int] = defaultdict(int)
        self.total_documents = 0

        self.logger.info(
            f"Hybrid searcher initialized with TF-IDF weight: {tfidf_weight:.2f}, vector weight: {vector_weight:.2f}",
        )

    def add_documents(self, documents: list[dict[str, Any]]) -> list[str]:
        """Add documents to both TF-IDF index and vector store.

        Args:
        ----
            documents: List of documents with 'text' and metadata

        Returns:
        -------
            List of document IDs

        """
        if not documents:
            return []

        self.logger.info(f"Adding {len(documents)} documents to hybrid index")

        # Generate IDs and extract texts
        document_ids = []
        texts = []
        payloads = []

        for doc in documents:
            doc_id = doc.get("id") or self._generate_document_id(doc["text"])
            document_ids.append(doc_id)
            texts.append(doc["text"])

            # Prepare payload for vector store
            payload = {
                **doc.get("metadata", {}),
                "document_id": doc_id,
                "text": doc["text"][:500],  # Store text preview for display
                "source": "hybrid_searcher",
            }
            payloads.append(payload)

        # Update TF-IDF index
        self._update_tfidf_index(document_ids, texts)

        # Generate embeddings and add to vector store
        embeddings = self.embedding_manager.encode(texts)
        self.vector_store.add_vectors(embeddings, payloads, document_ids)

        self.total_documents += len(documents)
        self.logger.info(f"Successfully indexed {len(documents)} documents")

        return document_ids

    def _update_tfidf_index(self, document_ids: list[str], texts: list[str]) -> None:
        """Update TF-IDF index with new documents.

        Args:
        ----
            document_ids: List of document IDs
            texts: List of document texts

        """
        for doc_id, text in zip(document_ids, texts, strict=False):
            # Tokenize and count terms
            tokens = self._tokenize_text(text)
            token_counts = Counter(tokens)

            # Update document frequency
            for token in set(tokens):
                self.document_frequency[token] += 1

            # Store term frequencies for this document
            if "documents" not in self.vocabulary:
                self.vocabulary["documents"] = {}

            self.vocabulary["documents"][doc_id] = {
                "term_counts": dict(token_counts),
                "total_terms": len(tokens),
                "text": text[:500],  # Store preview
            }

        # Update IDF scores
        for token in self.document_frequency:
            if token not in self.vocabulary:
                self.vocabulary[token] = {}
            # Prevent math domain error by ensuring valid input for log
            if self.total_documents > 0:
                idf_value = self.total_documents / (1 + self.document_frequency[token])
                if idf_value > 0:
                    self.vocabulary[token]["idf"] = math.log(idf_value)
                else:
                    self.vocabulary[token]["idf"] = 0.0  # Fallback for invalid values
            else:
                self.vocabulary[token]["idf"] = 0.0  # Fallback for zero documents

    def search(
        self,
        query: str,
        limit: int = 10,
        tfidf_limit: int = 50,
        vector_limit: int = 50,
        score_threshold: float = 0.1,
    ) -> list[dict[str, Any]]:
        """Perform hybrid search combining TF-IDF and vector search.

        Args:
        ----
            query: Search query
            limit: Maximum number of results to return
            tfidf_limit: Maximum TF-IDF results to consider
            vector_limit: Maximum vector results to consider
            score_threshold: Minimum combined score threshold

        Returns:
        -------
            List of hybrid search results

        """
        self.logger.info(f"Hybrid search for: '{query}'")

        # Perform TF-IDF search
        tfidf_results = self._tfidf_search(query, tfidf_limit)
        self.logger.debug(f"TF-IDF found {len(tfidf_results)} results")

        # Perform vector search
        vector_results = self._vector_search(query, vector_limit)
        self.logger.debug(f"Vector search found {len(vector_results)} results")

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

    def _tfidf_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Perform TF-IDF keyword search.

        Args:
        ----
            query: Search query
            limit: Maximum results

        Returns:
        -------
            List of TF-IDF search results

        """
        query_tokens = self._tokenize_text(query)
        if not query_tokens:
            return []

        # Calculate TF-IDF scores for each document
        doc_scores = defaultdict(float)

        for token in query_tokens:
            if token in self.vocabulary and "documents" in self.vocabulary:
                idf = self.vocabulary[token].get("idf", 0)

                for doc_id, doc_info in self.vocabulary["documents"].items():
                    # Safety check: ensure doc_info is a dictionary
                    if not isinstance(doc_info, dict) or "term_counts" not in doc_info:
                        continue

                    tf = doc_info["term_counts"].get(token, 0)
                    if tf > 0:
                        # TF-IDF score
                        tfidf_score = tf * idf
                        doc_scores[doc_id] += tfidf_score

        # Create result objects
        results = []
        for doc_id, score in doc_scores.items():
            if (
                "documents" in self.vocabulary
                and doc_id in self.vocabulary["documents"]
            ):
                doc_info = self.vocabulary["documents"][doc_id]

                # Safety check: ensure doc_info is a dictionary
                if not isinstance(doc_info, dict):
                    continue

                result = {
                    "document_id": doc_id,
                    "tfidf_score": score,
                    "vector_score": 0.0,
                    "combined_score": 0.0,
                    "text": doc_info.get("text", ""),
                    "matched_tokens": [
                        token
                        for token in query_tokens
                        if doc_info.get("term_counts", {}).get(token, 0) > 0
                    ],
                    "source": "tfidf",
                }
                results.append(result)

        # Sort by TF-IDF score and limit
        results.sort(key=lambda x: x["tfidf_score"], reverse=True)
        return results[:limit]

    def _vector_search(self, query: str, limit: int) -> list[dict[str, Any]]:
        """Perform vector semantic search.

        Args:
        ----
            query: Search query
            limit: Maximum results

        Returns:
        -------
            List of vector search results

        """
        # Generate query embedding
        query_embedding = self.embedding_manager.encode_single(query)

        # Search vector store
        vector_results = self.vector_store.search(
            collection_name="chat_vectors",
            query_vector=query_embedding,
            limit=limit,
            score_threshold=0.1,
        )

        # Convert to hybrid result format
        results = []
        for hit in vector_results:
            result = {
                "document_id": hit["id"],
                "tfidf_score": 0.0,
                "vector_score": hit["score"],
                "combined_score": 0.0,
                "text": hit["payload"].get("text", ""),
                "matched_tokens": [],  # Not applicable for vector search
                "source": "vector",
                "metadata": hit["payload"],
            }
            results.append(result)

        return results

    def _combine_results(
        self,
        tfidf_results: list[dict[str, Any]],
        vector_results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Combine TF-IDF and vector search results.

        Args:
        ----
            tfidf_results: Results from TF-IDF search
            vector_results: Results from vector search

        Returns:
        -------
            List of combined results

        """
        # Create a map of document_id to results
        combined_map = {}

        # Process TF-IDF results
        for result in tfidf_results:
            doc_id = result["document_id"]
            combined_map[doc_id] = result.copy()
            # Normalize TF-IDF scores (0-1 range)
            if tfidf_results:
                max_tfidf = tfidf_results[0]["tfidf_score"]
                if max_tfidf > 0:
                    combined_map[doc_id]["tfidf_score"] = (
                        result["tfidf_score"] / max_tfidf
                    )

        # Process vector results and merge
        for result in vector_results:
            doc_id = result["document_id"]
            if doc_id in combined_map:
                # Merge with existing result
                combined_map[doc_id]["vector_score"] = result["vector_score"]
                combined_map[doc_id]["source"] = "hybrid"
                # Add metadata from vector result
                if "metadata" in result:
                    combined_map[doc_id]["metadata"] = result["metadata"]
            else:
                # Add new result
                combined_map[doc_id] = result.copy()

        # Calculate combined scores
        for doc_id, result in combined_map.items():
            combined_score = (
                result["tfidf_score"] * self.tfidf_weight
                + result["vector_score"] * self.vector_weight
            )
            result["combined_score"] = combined_score

        return list(combined_map.values())

    def _tokenize_text(self, text: str) -> list[str]:
        """Tokenize text for TF-IDF processing.

        Args:
        ----
            text: Text to tokenize

        Returns:
        -------
            List of tokens

        """
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r"\b\w+\b", text.lower())

        # Filter out common stop words
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
            "were",
            "will",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "but",
            "or",
            "if",
            "they",
            "he",
            "she",
            "it",
            "we",
            "you",
            "i",
            "this",
            "that",
            "these",
            "those",
            "am",
            "been",
            "being",
            "for",
            "with",
            "by",
            "from",
        }

        return [token for token in tokens if token not in stop_words and len(token) > 2]

    def _generate_document_id(self, text: str) -> str:
        """Generate a unique document ID using UUID4 for Qdrant compatibility.

        Args:
        ----
            text: Document text

        Returns:
        -------
            UUID string suitable for Qdrant point IDs

        """
        import hashlib
        import uuid

        # Generate deterministic UUID based on content hash for reproducibility
        content_hash = hashlib.sha256(text.encode()).hexdigest()
        # Use hash to create deterministic UUID (UUID5 with namespace)
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"doc://{content_hash}"))

    def get_statistics(self) -> dict[str, Any]:
        """Get search statistics and index information.

        Returns
        -------
            Dictionary with statistics

        """
        vector_stats = self.vector_store.get_collection_info()
        embedding_stats = self.embedding_manager.get_device_info()

        return {
            "total_documents": self.total_documents,
            "vocabulary_size": len(self.document_frequency),
            "tfidf_weight": self.tfidf_weight,
            "vector_weight": self.vector_weight,
            "vector_store": vector_stats,
            "embedding_manager": embedding_stats,
            "last_updated": datetime.now().isoformat(),
        }

    def rebuild_index(self, documents: list[dict[str, Any]]) -> bool:
        """Rebuild the entire search index.

        Args:
        ----
            documents: List of all documents to reindex

        Returns:
        -------
            True if successful

        """
        try:
            self.logger.info("Rebuilding hybrid search index")

            # Clear existing data
            self.vocabulary.clear()
            self.document_frequency.clear()
            self.total_documents = 0

            # Clear vector store
            self.vector_store.clear_collection()

            # Reindex all documents
            self.add_documents(documents)

            self.logger.info(
                f"Successfully rebuilt index with {len(documents)} documents"
            )
            return True

        except Exception as e:
            self.logger.exception(f"Failed to rebuild index: {e}")
            return False

    def close(self) -> None:
        """Clean up resources."""
        if self.embedding_manager:
            self.embedding_manager.close()
        if self.vector_store:
            self.vector_store.close()
        self.logger.info("Hybrid searcher closed")


class HybridSearcherFactory:
    """Factory for creating hybrid searchers with different configurations."""

    @staticmethod
    def create_default_searcher() -> HybridSearcher:
        """Create a default hybrid searcher.

        Returns
        -------
            HybridSearcher with balanced settings

        """
        return HybridSearcher(
            tfidf_weight=0.3,
            vector_weight=0.7,
        )

    @staticmethod
    def create_keyword_focused_searcher() -> HybridSearcher:
        """Create a searcher focused on keyword matching.

        Returns
        -------
            HybridSearcher with TF-IDF emphasis

        """
        return HybridSearcher(
            tfidf_weight=0.6,
            vector_weight=0.4,
        )

    @staticmethod
    def create_semantic_focused_searcher() -> HybridSearcher:
        """Create a searcher focused on semantic understanding.

        Returns
        -------
            HybridSearcher with vector search emphasis

        """
        return HybridSearcher(
            tfidf_weight=0.2,
            vector_weight=0.8,
        )


# Convenience function for creating searchers
def create_hybrid_searcher(
    tfidf_weight: float = 0.3,
    vector_weight: float = 0.7,
) -> HybridSearcher:
    """Create a hybrid searcher with custom weights.

    Args:
    ----
        tfidf_weight: Weight for TF-IDF search (0-1)
        vector_weight: Weight for vector search (0-1)

    Returns:
    -------
        HybridSearcher instance

    """
    return HybridSearcher(
        tfidf_weight=tfidf_weight,
        vector_weight=vector_weight,
    )
