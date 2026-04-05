"""Evidence Saturation Detection for rca Tier 1.

Detects when sufficient evidence has been gathered to move from
the Gather phase to the Isolate phase using semantic similarity
and diminishing returns detection.
"""

import re
from typing import List, Optional, Any


class EvidenceSaturationDetector:
    """Detects evidence saturation during root cause analysis.

    Uses semantic similarity (via CKS) and Jaccard keyword overlap as
    fallback to determine when new evidence no longer provides novel
    information.

    Attributes:
        threshold: The similarity threshold for considering evidence
                   as redundant (0.0 to 1.0).
        query_type: The type of query for threshold configuration.
        cks_client: Optional CKS client for semantic search.

    Examples:
        >>> detector = EvidenceSaturationDetector(threshold=0.85)
        >>> detector.check_saturation(["error in auth"], ["auth failure"])
        True
        >>> detector.detect_diminishing_returns(["a", "a", "a"])
        True
    """

    def __init__(
        self,
        threshold: float = 0.75,
        query_type: str = "default",
        cks_client: Optional[Any] = None,
    ):
        """Initialize the saturation detector.

        Args:
            threshold: Similarity threshold for saturation (default: 0.75).
            query_type: The type of query (default: "default").
            cks_client: Optional CKS client for semantic search.
        """
        self.threshold = threshold
        self.query_type = query_type
        self.cks_client = cks_client

    def check_saturation(self, existing_evidence: List[str], new_evidence: List[str]) -> bool:
        """Check if saturation is reached based on existing and new evidence.

        Compares new evidence against existing evidence using semantic
        similarity or keyword overlap. Returns True if the average
        similarity exceeds the threshold.

        Args:
            existing_evidence: List of existing evidence strings.
            new_evidence: List of new evidence strings to evaluate.

        Returns:
            True if saturation is detected (high similarity), False otherwise.

        Examples:
            >>> detector = EvidenceSaturationDetector(threshold=0.85)
            >>> detector.check_saturation([], ["test"])
            False
            >>> detector.check_saturation(["database error"], ["database failure"])
            True
        """
        if not existing_evidence or not new_evidence:
            return False

        # Calculate average similarity between all pairs
        similarities = []
        for existing in existing_evidence:
            for new in new_evidence:
                score = self.get_similarity_score(existing, new)
                similarities.append(score)

        if not similarities:
            return False

        avg_similarity = sum(similarities) / len(similarities)
        return avg_similarity >= self.threshold

    def detect_diminishing_returns(self, evidence_history: List[str]) -> bool:
        """Detect diminishing returns using sliding window analysis.

        Checks for 3 consecutive items in the evidence history that
        have similarity above the threshold, indicating that new evidence
        is not providing novel information.

        Args:
            evidence_history: List of evidence strings in chronological order.

        Returns:
            True if diminishing returns detected (3+ consecutive similar),
            False otherwise.

        Examples:
            >>> detector = EvidenceSaturationDetector(threshold=0.8)
            >>> detector.detect_diminishing_returns(["a", "b"])
            False
            >>> detector.detect_diminishing_returns(["a", "similar to a", "almost a"])
            True
        """
        if len(evidence_history) < 3:
            return False

        # Sliding window of size 3
        consecutive_count = 0

        for i in range(len(evidence_history) - 1):
            current = evidence_history[i]
            next_item = evidence_history[i + 1]
            similarity = self.get_similarity_score(current, next_item)

            if similarity >= self.threshold:
                consecutive_count += 1
                if consecutive_count >= 2:  # 2 similarities = 3 consecutive items
                    return True
            else:
                consecutive_count = 0

        return False

    def get_similarity_score(self, text1: str, text2: str) -> float:
        """Get similarity score between two texts.

        Uses CKS semantic search if available, otherwise falls back to
        Jaccard keyword similarity.

        Args:
            text1: First text string.
            text2: Second text string.

        Returns:
            Similarity score between 0.0 and 1.0.

        Examples:
            >>> detector = EvidenceSaturationDetector()
            >>> detector.get_similarity_score("same", "same")
            1.0
            >>> detector.get_similarity_score("cat dog", "bird fish")
            0.0
        """
        # Handle edge cases
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
        if text1 == text2:
            return 1.0

        # Try CKS semantic search if available
        if self.cks_client is not None:
            try:
                results = self.cks_client.search_semantic(text1, limit=1)
                if results and len(results) > 0:
                    # Extract score from results
                    # CKS returns list of dicts with 'score' key
                    for result in results:
                        if "score" in result:
                            return float(result["score"])
            except Exception:
                # Fall back to Jaccard if CKS fails
                pass

        # Fallback to Jaccard similarity
        return self._jaccard_similarity(text1, text2)

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts.

        Jaccard similarity = |intersection| / |union| of word sets.

        Args:
            text1: First text string.
            text2: Second text string.

        Returns:
            Jaccard similarity between 0.0 and 1.0.
        """
        # Tokenize into words (lowercase, alphanumeric only)
        words1 = self._tokenize(text1)
        words2 = self._tokenize(text2)

        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0

        set1 = set(words1)
        set2 = set(words2)

        intersection = set1 & set2
        union = set1 | set2

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase words.

        Args:
            text: Text string to tokenize.

        Returns:
            List of lowercase word tokens.
        """
        # Extract alphanumeric words, convert to lowercase
        words = re.findall(r"\b\w+\b", text.lower())
        return words

    # Legacy methods for backward compatibility
    def is_saturated(self, evidence: List[str]) -> bool:
        """Check if the evidence list has reached saturation (legacy method).

        Args:
            evidence: List of evidence strings to evaluate.

        Returns:
            True if saturation is detected, False otherwise.
        """
        if not evidence:
            return False

        # Check for diminishing returns within the evidence list
        return self.detect_diminishing_returns(evidence)

    def get_saturation_score(self, evidence: List[str]) -> float:
        """Get the current saturation score (legacy method).

        Args:
            evidence: List of evidence strings to evaluate.

        Returns:
            Saturation score between 0.0 and 1.0.
        """
        if not evidence:
            return 0.0

        # Calculate average pairwise similarity
        if len(evidence) < 2:
            return 0.0

        total_similarity = 0.0
        count = 0

        for i in range(len(evidence) - 1):
            for j in range(i + 1, len(evidence)):
                total_similarity += self.get_similarity_score(evidence[i], evidence[j])
                count += 1

        if count == 0:
            return 0.0

        return total_similarity / count

    def add_evidence(self, evidence: str) -> None:
        """Add evidence to the detector (legacy stub).

        Args:
            evidence: New evidence string to add.
        """
        # This method is a stub for backward compatibility
        pass
