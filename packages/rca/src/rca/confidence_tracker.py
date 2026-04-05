"""Confidence Tracker for rca Tier 1.

Implements Bayesian probability updates for hypothesis confidence tracking.
"""

from typing import Dict, List, Optional


class ConfidenceTracker:
    """Tracks hypothesis confidence using Bayesian updates.

    Maintains prior and posterior probabilities for hypotheses,
    allowing for evidence-based confidence updates using Bayes' rule.

    Attributes:
        priors: Dictionary mapping hypothesis names to prior probabilities.
        posteriors: Dictionary mapping hypothesis names to posterior probabilities.

    Examples:
        >>> tracker = ConfidenceTracker()
        >>> tracker.set_prior("Database timeout", 0.5)
        >>> tracker.update("Database timeout", likelihood_ratio=2.0, evidence_supports=True)
        >>> tracker.get_posterior("Database timeout")
        0.667
    """

    def __init__(self) -> None:
        """Initialize the confidence tracker."""
        self.priors: Dict[str, float] = {}
        self.posteriors: Dict[str, float] = {}

    def set_prior(self, hypothesis: str, prior: float) -> None:
        """Set the prior probability for a hypothesis.

        Setting a new prior resets the posterior to the new prior value.

        Args:
            hypothesis: The hypothesis name.
            prior: Prior probability (0.0 to 1.0).

        Raises:
            ValueError: If prior is not between 0 and 1.
        """
        if not 0.0 <= prior <= 1.0:
            raise ValueError(f"prior must be between 0 and 1, got {prior}")
        self.priors[hypothesis] = prior
        # Reset posterior to the new prior
        self.posteriors[hypothesis] = prior

    def get_prior(self, hypothesis: str) -> float:
        """Get the prior probability for a hypothesis.

        Args:
            hypothesis: The hypothesis name.

        Returns:
            The prior probability, or 0.0 if not set.
        """
        return self.priors.get(hypothesis, 0.0)

    def get_posterior(self, hypothesis: str) -> float:
        """Get the current posterior probability for a hypothesis.

        Args:
            hypothesis: The hypothesis name.

        Returns:
            The posterior probability, or 0.0 if not set.
        """
        return self.posteriors.get(hypothesis, 0.0)

    def update(
        self, hypothesis: str, likelihood_ratio: float, evidence_supports: bool = True
    ) -> float:
        """Update hypothesis confidence using Bayes' rule.

        Args:
            hypothesis: The hypothesis name.
            likelihood_ratio: P(E|H) / P(E|~H), must be positive.
                LR > 1: evidence supports hypothesis (increases confidence)
                LR < 1: evidence refutes hypothesis (decreases confidence)
                LR = 1: neutral evidence (no change)
            evidence_supports: Whether evidence supports the hypothesis.
                Ignored (LR already encodes direction).

        Returns:
            The updated posterior probability.

        Raises:
            ValueError: If likelihood_ratio is not positive.

        Examples:
            >>> tracker = ConfidenceTracker()
            >>> tracker.set_prior("H1", 0.5)
            >>> # P(H|E) = (LR * P(H)) / (LR * P(H) + P(~H))
            >>> tracker.update("H1", likelihood_ratio=2.0, evidence_supports=True)
            0.667
        """
        if likelihood_ratio <= 0:
            raise ValueError(f"likelihood_ratio must be positive, got {likelihood_ratio}")

        # Get current probability (posterior if exists, else prior)
        current = self.posteriors.get(hypothesis, self.priors.get(hypothesis, 0.0))

        # Bayes' rule: P(H|E) = (LR * P(H)) / (LR * P(H) + P(~H))
        # where P(~H) = 1 - P(H)
        # The likelihood_ratio already encodes whether evidence supports or refutes
        posterior = (likelihood_ratio * current) / (
            likelihood_ratio * current + (1 - current)
        )

        self.posteriors[hypothesis] = posterior
        return posterior

    def reset(self) -> None:
        """Reset all posteriors, clearing all updates."""
        self.posteriors.clear()

    def batch_update(
        self, evidence: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """Update multiple hypotheses with evidence.

        Args:
            evidence: Dictionary mapping hypothesis names to evidence dicts
                     with 'likelihood_ratio' and 'supports' keys.

        Returns:
            Dictionary of updated posteriors.
        """
        results = {}
        for hypothesis, ev in evidence.items():
            likelihood_ratio = ev.get("likelihood_ratio", 1.0)
            supports = ev.get("supports", True)
            results[hypothesis] = self.update(hypothesis, likelihood_ratio, supports)
        return results

    def normalize(self, hypotheses: List[str]) -> Dict[str, float]:
        """Normalize posteriors so they sum to 1.0.

        Useful when comparing competing hypotheses.

        Args:
            hypotheses: List of hypothesis names to normalize.

        Returns:
            Dictionary of normalized posteriors.
        """
        total = sum(self.posteriors.get(h, 0.0) for h in hypotheses)
        if total == 0:
            return {h: 0.0 for h in hypotheses}

        return {h: self.posteriors.get(h, 0.0) / total for h in hypotheses}
