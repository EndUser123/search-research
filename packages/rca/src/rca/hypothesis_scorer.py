"""Hypothesis Scorer for rca Tier 1.

Ranks hypotheses based on reproducibility, recency, and impact.
Uses Bayesian updates for confidence tracking.
Integrates evidence tiering for confidence ceilings.

Formula: Likelihood = P(evidence|H) * prior
Prune hypotheses with score < 0.6
Confidence ceiling: min(confidence, evidence_tier_ceiling)
"""

from typing import Any, Dict, List, Optional

# Lazy import for evidence tiering to avoid circular dependencies
_evidence_tier_imported = False


def _ensure_evidence_tier():
    """Import evidence tiering modules on demand."""
    global _evidence_tier_imported
    if not _evidence_tier_imported:
        from . import evidence_tier
        _evidence_tier_imported = True
        return evidence_tier
    return None


def _load_settings():
    """Lazy load settings to avoid import issues."""
    from .config import _load_settings as _load
    return _load()


class HypothesisScorer:
    """Scores and ranks root cause hypotheses.

    Uses configurable weight factors to score hypotheses based on
    reproducibility, recency, and impact.

    Bayesian Formula: Likelihood = P(evidence|H) * prior
    Pruning threshold: hypotheses with score < 0.6 are filtered.

    Attributes:
        weights: Dictionary of weight factors for scoring.
        hypotheses: List of scored hypotheses.
        pruning_threshold: Minimum score to keep a hypothesis (default 0.6).

    Examples:
        >>> scorer = HypothesisScorer()
        >>> scorer.add_hypothesis("Database timeout", reproducibility=0.9)
        >>> scorer.get_top_hypotheses(1)
        [{"text": "Database timeout", "score": 0.85}]
    """

    # Default pruning threshold per specification
    DEFAULT_PRUNING_THRESHOLD = 0.6

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        pruning_threshold: float = DEFAULT_PRUNING_THRESHOLD,
    ):
        """Initialize the hypothesis scorer.

        Args:
            weights: Custom weight factors. Defaults to spec weights:
                     Reproducibility(0.3) * Recency(0.2) * Impact(0.5)
            pruning_threshold: Minimum score to keep a hypothesis (default 0.6).
        """
        from .confidence_tracker import ConfidenceTracker

        # Default weight mapping per specification:
        # Reproducibility(0.3) * Recency(0.2) * Impact(0.5)
        weight_keys = {
            "reproducibility": ("reproducibility", "reproducibility_weight", 0.3),
            "recency": ("recency", "recency_weight", 0.2),
            "impact": ("impact", "impact_weight", 0.5),
        }

        self.weights = {}
        if weights:
            # Use custom weights if provided
            for key, (user_key, _config_key, default) in weight_keys.items():
                self.weights[key] = weights.get(user_key, default)
        else:
            # Try to load from config, but fall back to spec defaults
            settings = _load_settings()
            scoring_config = settings.get("hypothesis_scoring", {})

            for key, (user_key, config_key, default) in weight_keys.items():
                # Only use config value if explicitly set (exists in config)
                # Otherwise use spec defaults
                self.weights[key] = scoring_config.get(config_key, default)

        self.pruning_threshold = pruning_threshold
        self.hypotheses: List[Dict[str, Any]] = []
        self._confidence_tracker = ConfidenceTracker()

    def add_hypothesis(
        self,
        text: str,
        reproducibility: float = 0.5,
        recency: float = 0.5,
        impact: float = 0.5,
        prior: float = 0.5,
        evidence_likelihood: float = 0.5,
    ) -> str:
        """Add a hypothesis with its scoring factors.

        Args:
            text: Hypothesis description.
            reproducibility: How reproducible the issue is (0.0 to 1.0).
            recency: How recently the issue occurred (0.0 to 1.0).
            impact: Business impact severity (0.0 to 1.0).
            prior: Prior probability P(H) (0.0 to 1.0).
            evidence_likelihood: P(evidence|H), likelihood of evidence given H (0.0 to 1.0).

        Returns:
            The hypothesis ID.

        Examples:
            >>> scorer = HypothesisScorer()
            >>> hypothesis_id = scorer.add_hypothesis(
            ...     "API timeout",
            ...     reproducibility=0.9,
            ...     prior=0.7,
            ...     evidence_likelihood=0.8
            ... )
        """
        # Per research spec:
        # Rank by: Reproducibility (0.3) * Recency (0.2) * Impact (0.5)
        # Formula: Likelihood = P(evidence|H) * prior

        # Weighted factor score (product of factors raised to weight power)
        # This gives: reproducibility^0.3 * recency^0.2 * impact^0.5
        factor_score = (
            reproducibility ** self.weights["reproducibility"]
            * recency ** self.weights["recency"]
            * impact ** self.weights["impact"]
        )

        # Bayesian formula: Likelihood = P(evidence|H) * prior
        bayesian_likelihood = evidence_likelihood * prior

        # Final score: blend factor score with Bayesian likelihood
        # The Bayesian likelihood dominates when we have strong evidence
        score = (factor_score + bayesian_likelihood) / 2

        hypothesis = {
            "id": f"hyp_{len(self.hypotheses)}",
            "text": text,
            "score": score,
            "factor_score": factor_score,
            "bayesian_likelihood": bayesian_likelihood,
            "reproducibility": reproducibility,
            "recency": recency,
            "impact": impact,
            "prior": prior,
            "evidence_likelihood": evidence_likelihood,
            "pruned": score < self.pruning_threshold,
        }

        self.hypotheses.append(hypothesis)
        return hypothesis["id"]

    def get_top_hypotheses(self, limit: int = 5, include_pruned: bool = False) -> List[Dict[str, Any]]:
        """Get the top-scoring hypotheses.

        Args:
            limit: Maximum number of hypotheses to return.
            include_pruned: If False, exclude pruned hypotheses (score < threshold).

        Returns:
            List of hypotheses sorted by score (descending).

        Examples:
            >>> scorer = HypothesisScorer()
            >>> scorer.add_hypothesis("H1", reproducibility=0.9)
            >>> scorer.add_hypothesis("H2", reproducibility=0.3)
            >>> top = scorer.get_top_hypotheses(1)
            >>> top[0]["text"]
            "H1"
        """
        candidates = self.hypotheses
        if not include_pruned:
            candidates = [h for h in self.hypotheses if not h.get("pruned", False)]

        sorted_hypotheses = sorted(
            candidates, key=lambda h: h["score"], reverse=True
        )
        return sorted_hypotheses[:limit]

    def get_hypothesis(self, hypothesis_id: str) -> Optional[Dict[str, Any]]:
        """Get a hypothesis by ID.

        Args:
            hypothesis_id: The hypothesis ID.

        Returns:
            The hypothesis data, or None if not found.
        """
        for h in self.hypotheses:
            if h["id"] == hypothesis_id:
                return h
        return None

    def clear(self) -> None:
        """Clear all hypotheses.

        Examples:
            >>> scorer = HypothesisScorer()
            >>> scorer.add_hypothesis("H1")
            >>> scorer.clear()
            >>> len(scorer.hypotheses)
            0
        """
        self.hypotheses.clear()
        self._confidence_tracker.reset()

    def set_prior(self, hypothesis: str, prior: float) -> None:
        """Set the Bayesian prior probability for a hypothesis.

        Args:
            hypothesis: The hypothesis name/description.
            prior: Prior probability (0.0 to 1.0).

        Raises:
            ValueError: If prior is not between 0 and 1.

        Examples:
            >>> scorer = HypothesisScorer()
            >>> scorer.set_prior("Database timeout", 0.3)
        """
        self._confidence_tracker.set_prior(hypothesis, prior)

    def update(
        self, hypothesis: str, evidence_supports: bool, likelihood_ratio: float
    ) -> None:
        """Update hypothesis confidence using Bayes' rule.

        Args:
            hypothesis: The hypothesis name/description.
            evidence_supports: Whether evidence supports the hypothesis.
            likelihood_ratio: P(E|H) / P(E|~H), must be positive.

        Raises:
            ValueError: If likelihood_ratio is not positive.

        Examples:
            >>> scorer = HypothesisScorer()
            >>> scorer.set_prior("API timeout", 0.5)
            >>> scorer.update("API timeout", evidence_supports=True, likelihood_ratio=2.0)
        """
        self._confidence_tracker.update(hypothesis, likelihood_ratio, evidence_supports)

    def get_confidence(self, hypothesis: str) -> float:
        """Get the current confidence (posterior probability) for a hypothesis.

        Args:
            hypothesis: The hypothesis name/description.

        Returns:
            The current posterior probability, or 0.0 if not set.

        Examples:
            >>> scorer = HypothesisScorer()
            >>> scorer.set_prior("Network issue", 0.4)
            >>> scorer.get_confidence("Network issue")
            0.4
        """
        return self._confidence_tracker.get_posterior(hypothesis)

    def rank(self, hypotheses: List[str]) -> List[str]:
        """Rank hypotheses by combined score and confidence.

        Uses the weighted scoring formula:
        Reproducibility(0.3) * Recency(0.2) * Impact(0.5)

        Combined score = weighted_score * confidence

        Args:
            hypotheses: List of hypothesis names to rank.

        Returns:
            List of hypothesis names sorted by combined score (descending).

        Examples:
            >>> scorer = HypothesisScorer()
            >>> scorer.set_prior("H1", 0.9)
            >>> scorer.add_hypothesis("H1", reproducibility=0.9, recency=0.8, impact=0.7)
            >>> scorer.set_prior("H2", 0.3)
            >>> scorer.add_hypothesis("H2", reproducibility=0.5, recency=0.6, impact=0.4)
            >>> scorer.rank(["H1", "H2"])
            ["H1", "H2"]
        """
        def combined_score(hyp_name: str) -> float:
            """Calculate combined score from weighted factors and confidence."""
            # Find the hypothesis in the list
            hyp_data = None
            for h in self.hypotheses:
                if h["text"] == hyp_name:
                    hyp_data = h
                    break

            if not hyp_data:
                return 0.0

            weighted_score = hyp_data["score"]
            confidence = self.get_confidence(hyp_name)

            return weighted_score * confidence

        # Sort by combined score descending, then by name for tie-breaking
        return sorted(
            hypotheses,
            key=lambda h: (combined_score(h), h),
            reverse=True
        )

    def get_viable_hypotheses(self) -> List[Dict[str, Any]]:
        """Get hypotheses that meet the pruning threshold.

        Returns only hypotheses with score >= pruning_threshold.

        Returns:
            List of viable hypotheses sorted by score (descending).

        Examples:
            >>> scorer = HypothesisScorer(pruning_threshold=0.6)
            >>> scorer.add_hypothesis("H1", reproducibility=0.9, prior=0.8, evidence_likelihood=0.9)
            >>> scorer.add_hypothesis("H2", reproducibility=0.3, prior=0.2, evidence_likelihood=0.3)
            >>> viable = scorer.get_viable_hypotheses()
            >>> len(viable)
            1
        """
        return [h for h in self.hypotheses if not h.get("pruned", False)]

    def get_pruned_hypotheses(self) -> List[Dict[str, Any]]:
        """Get hypotheses that were pruned (score < threshold).

        Returns:
            List of pruned hypotheses sorted by score (descending).

        Examples:
            >>> scorer = HypothesisScorer(pruning_threshold=0.6)
            >>> scorer.add_hypothesis("H1", reproducibility=0.3, prior=0.2, evidence_likelihood=0.3)
            >>> pruned = scorer.get_pruned_hypotheses()
            >>> len(pruned)
            1
        """
        return [h for h in self.hypotheses if h.get("pruned", False)]

    def calculate_bayesian_likelihood(
        self,
        prior: float,
        evidence_likelihood: float,
    ) -> float:
        """Calculate Bayesian likelihood: P(evidence|H) * prior.

        Args:
            prior: Prior probability P(H) (0.0 to 1.0).
            evidence_likelihood: P(evidence|H), likelihood of evidence given H (0.0 to 1.0).

        Returns:
            The Bayesian likelihood score.

        Raises:
            ValueError: If inputs are not between 0 and 1.

        Examples:
            >>> scorer = HypothesisScorer()
            >>> scorer.calculate_bayesian_likelihood(0.7, 0.8)
            0.56
        """
        if not (0.0 <= prior <= 1.0):
            raise ValueError(f"prior must be between 0 and 1, got {prior}")
        if not (0.0 <= evidence_likelihood <= 1.0):
            raise ValueError(f"evidence_likelihood must be between 0 and 1, got {evidence_likelihood}")

        return evidence_likelihood * prior

    # Evidence Tiering Integration (Task #988)

    def add_evidence_to_hypothesis(
        self,
        hypothesis_id: str,
        source_type: str,
        description: str,
        citation: str = "",
    ) -> None:
        """Add evidence source to a hypothesis and update its confidence ceiling.

        Args:
            hypothesis_id: The ID of the hypothesis.
            source_type: Type of evidence (e.g., "failing_test", "stack_trace").
            description: Description of the evidence.
            citation: Optional citation/reference for the evidence.

        Raises:
            ValueError: If hypothesis_id not found.

        Examples:
            >>> scorer = HypothesisScorer()
            >>> hyp_id = scorer.add_hypothesis("Database timeout")
            >>> scorer.add_evidence_to_hypothesis(
            ...     hyp_id,
            ...     "failing_test",
            ...     "Test times out after 30s"
            ... )
        """
        from .evidence_tier import classify_evidence

        hypothesis = self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")

        # Initialize evidence list if not present
        if "evidence_sources" not in hypothesis:
            hypothesis["evidence_sources"] = []

        # Add the evidence source
        evidence = classify_evidence(source_type, description, citation)
        hypothesis["evidence_sources"].append(evidence)

        # Recalculate confidence ceiling
        from .evidence_tier import get_confidence_ceiling
        hypothesis["confidence_ceiling"] = get_confidence_ceiling(
            hypothesis["evidence_sources"]
        )

    def get_confidence_ceiling(self, hypothesis_id: str) -> float:
        """Get the confidence ceiling based on evidence tiering.

        Args:
            hypothesis_id: The ID of the hypothesis.

        Returns:
            The confidence ceiling (0.0 to 1.0), or 1.0 if no evidence.

        Examples:
            >>> scorer = HypothesisScorer()
            >>> hyp_id = scorer.add_hypothesis("Database timeout")
            >>> scorer.add_evidence_to_hypothesis(hyp_id, "speculation", "Maybe timeout")
            >>> scorer.get_confidence_ceiling(hyp_id)
            0.5
        """
        hypothesis = self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return 1.0

        return hypothesis.get("confidence_ceiling", 1.0)

    def apply_evidence_ceiling(
        self, hypothesis_id: str, confidence: float
    ) -> float:
        """Apply evidence tier ceiling to a confidence value.

        Args:
            hypothesis_id: The ID of the hypothesis.
            confidence: The proposed confidence level.

        Returns:
            The confidence capped at the evidence tier ceiling.

        Examples:
            >>> scorer = HypothesisScorer()
            >>> hyp_id = scorer.add_hypothesis("Database timeout")
            >>> scorer.add_evidence_to_hypothesis(hyp_id, "speculation", "Maybe timeout")
            >>> scorer.apply_evidence_ceiling(hyp_id, 0.9)
            0.5
        """
        ceiling = self.get_confidence_ceiling(hypothesis_id)
        return min(confidence, ceiling)

    def get_capped_confidence(self, hypothesis: str) -> float:
        """Get confidence capped by evidence tier ceiling.

        This combines the Bayesian posterior confidence with the evidence
        tier ceiling to produce the final "capped" confidence.

        Args:
            hypothesis: The hypothesis name/description.

        Returns:
            The capped confidence (0.0 to 1.0).

        Examples:
            >>> scorer = HypothesisScorer()
            >>> hyp_id = scorer.add_hypothesis("Database timeout", prior=0.9)
            >>> scorer.add_evidence_to_hypothesis(hyp_id, "speculation", "Maybe timeout")
            >>> scorer.get_capped_confidence("Database timeout")
            0.5
        """
        # Find the hypothesis
        hyp_data = None
        for h in self.hypotheses:
            if h["text"] == hypothesis:
                hyp_data = h
                break

        if not hyp_data:
            return 0.0

        raw_confidence = self.get_confidence(hypothesis)
        ceiling = hyp_data.get("confidence_ceiling", 1.0)

        return min(raw_confidence, ceiling)

    def rank_with_evidence_tiers(
        self, hypotheses: List[str]
    ) -> List[str]:
        """Rank hypotheses with evidence-tier-capped confidence.

        Similar to rank(), but applies evidence tier ceilings to the
        confidence values before ranking.

        Args:
            hypotheses: List of hypothesis names to rank.

        Returns:
            List of hypothesis names sorted by capped score (descending).

        Examples:
            >>> scorer = HypothesisScorer()
            >>> h1 = scorer.add_hypothesis("H1", prior=0.9)
            >>> scorer.add_evidence_to_hypothesis(h1, "speculation", "Maybe")
            >>> h2 = scorer.add_hypothesis("H2", prior=0.7)
            >>> scorer.add_evidence_to_hypothesis(h2, "failing_test", "Test fails")
            >>> scorer.rank_with_evidence_tiers(["H1", "H2"])
            ['H2', 'H1']  # H2 ranks higher due to better evidence tier
        """
        def capped_score(hyp_name: str) -> float:
            """Calculate score with evidence tier ceiling applied."""
            # Find the hypothesis
            hyp_data = None
            for h in self.hypotheses:
                if h["text"] == hyp_name:
                    hyp_data = h
                    break

            if not hyp_data:
                return 0.0

            weighted_score = hyp_data["score"]
            capped_confidence = self.get_capped_confidence(hyp_name)

            return weighted_score * capped_confidence

        return sorted(
            hypotheses,
            key=lambda h: (capped_score(h), h),
            reverse=True
        )

    def get_evidence_summary(self, hypothesis_id: str) -> str:
        """Get a formatted summary of evidence for a hypothesis.

        Args:
            hypothesis_id: The ID of the hypothesis.

        Returns:
            A formatted string showing evidence and their tiers.

        Examples:
            >>> scorer = HypothesisScorer()
            >>> hyp_id = scorer.add_hypothesis("Database timeout")
            >>> scorer.add_evidence_to_hypothesis(hyp_id, "failing_test", "Test fails")
            >>> print(scorer.get_evidence_summary(hyp_id))
        """
        from .evidence_tier import format_evidence_summary

        hypothesis = self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return "Hypothesis not found"

        sources = hypothesis.get("evidence_sources", [])
        if not sources:
            return "No evidence collected"

        return format_evidence_summary(sources)

    def is_verification_ready(self, hypothesis_id: str) -> bool:
        """Check if a hypothesis has sufficient evidence for verification.

        Per /evidence-tiers: "High-stakes decisions require Tier 1 or 2"

        Args:
            hypothesis_id: The ID of the hypothesis.

        Returns:
            True if hypothesis has Tier 1 or 2 evidence.

        Examples:
            >>> scorer = HypothesisScorer()
            >>> hyp_id = scorer.add_hypothesis("Database timeout")
            >>> scorer.add_evidence_to_hypothesis(hyp_id, "user_report", "User says slow")
            >>> scorer.is_verification_ready(hyp_id)
            False
            >>> scorer.add_evidence_to_hypothesis(hyp_id, "failing_test", "Test fails")
            >>> scorer.is_verification_ready(hyp_id)
            True
        """
        from .evidence_tier import EvidenceTier

        hypothesis = self.get_hypothesis(hypothesis_id)
        if not hypothesis:
            return False

        sources = hypothesis.get("evidence_sources", [])
        if not sources:
            return False

        # Check if any source is Tier 1 or 2
        for source in sources:
            if source.tier in (EvidenceTier.TIER_1, EvidenceTier.TIER_2):
                return True

        return False
