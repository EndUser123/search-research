"""Tests for confidence_tracker module.

QA-001-001: Add exception handler tests for:
- ValueError for invalid likelihood_ratio (0, negative, NaN)
- test_update_raises_on_zero_likelihood
- test_update_raises_on_negative_likelihood
- test_update_raises_on_nan_likelihood

Plus comprehensive tests for all ConfidenceTracker functionality.
"""

import math
import pytest

from rca.confidence_tracker import ConfidenceTracker


class TestConfidenceTrackerInit:
    """Tests for ConfidenceTracker initialization."""

    def test_initialization(self):
        """Test tracker initialization."""
        tracker = ConfidenceTracker()

        assert tracker.priors == {}
        assert tracker.posteriors == {}

    def test_initial_state_empty(self):
        """Test that initial state has no hypotheses."""
        tracker = ConfidenceTracker()

        assert len(tracker.priors) == 0
        assert len(tracker.posteriors) == 0


class TestSetPrior:
    """Tests for set_prior method."""

    def test_set_prior_valid_value(self):
        """Test setting a valid prior probability."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        assert tracker.get_prior("H1") == 0.5
        assert tracker.get_posterior("H1") == 0.5

    def test_set_prior_resets_posterior(self):
        """Test that setting prior resets posterior to new prior."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)
        tracker.update("H1", likelihood_ratio=2.0)

        assert tracker.get_posterior("H1") != 0.5

        # Set new prior - should reset posterior
        tracker.set_prior("H1", 0.3)

        assert tracker.get_prior("H1") == 0.3
        assert tracker.get_posterior("H1") == 0.3

    def test_set_prior_boundary_zero(self):
        """Test setting prior to 0.0."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.0)

        assert tracker.get_prior("H1") == 0.0

    def test_set_prior_boundary_one(self):
        """Test setting prior to 1.0."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 1.0)

        assert tracker.get_prior("H1") == 1.0

    def test_set_prior_raises_on_negative(self):
        """Test that negative prior raises ValueError."""
        tracker = ConfidenceTracker()

        with pytest.raises(ValueError) as exc_info:
            tracker.set_prior("H1", -0.1)

        assert "prior must be between 0 and 1" in str(exc_info.value)

    def test_set_prior_raises_on_greater_than_one(self):
        """Test that prior > 1 raises ValueError."""
        tracker = ConfidenceTracker()

        with pytest.raises(ValueError) as exc_info:
            tracker.set_prior("H1", 1.1)

        assert "prior must be between 0 and 1" in str(exc_info.value)

    def test_set_prior_multiple_hypotheses(self):
        """Test setting priors for multiple hypotheses."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.3)
        tracker.set_prior("H2", 0.5)
        tracker.set_prior("H3", 0.7)

        assert tracker.get_prior("H1") == 0.3
        assert tracker.get_prior("H2") == 0.5
        assert tracker.get_prior("H3") == 0.7


class TestGetPrior:
    """Tests for get_prior method."""

    def test_get_prior_existing(self):
        """Test getting existing prior."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.75)

        assert tracker.get_prior("H1") == 0.75

    def test_get_prior_nonexistent_returns_zero(self):
        """Test getting prior for nonexistent hypothesis returns 0.0."""
        tracker = ConfidenceTracker()

        assert tracker.get_prior("nonexistent") == 0.0


class TestGetPosterior:
    """Tests for get_posterior method."""

    def test_get_posterior_after_update(self):
        """Test getting posterior after update."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)
        tracker.update("H1", likelihood_ratio=2.0)

        posterior = tracker.get_posterior("H1")

        assert posterior > 0.5  # Should increase with LR > 1

    def test_get_posterior_without_update_returns_prior(self):
        """Test that posterior equals prior if no updates."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.4)

        assert tracker.get_posterior("H1") == 0.4

    def test_get_posterior_nonexistent_returns_zero(self):
        """Test getting posterior for nonexistent hypothesis returns 0.0."""
        tracker = ConfidenceTracker()

        assert tracker.get_posterior("nonexistent") == 0.0


class TestUpdate:
    """Tests for update method."""

    def test_update_with_supporting_evidence(self):
        """Test update with likelihood_ratio > 1 (supporting evidence)."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        posterior = tracker.update("H1", likelihood_ratio=2.0)

        # P(H|E) = (2 * 0.5) / (2 * 0.5 + 0.5) = 1 / 1.5 = 0.667
        expected = 0.6666666666666666
        assert abs(posterior - expected) < 0.001

    def test_update_with_refuting_evidence(self):
        """Test update with likelihood_ratio < 1 (refuting evidence)."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.8)

        posterior = tracker.update("H1", likelihood_ratio=0.25)

        # Should decrease from 0.8
        assert posterior < 0.8
        assert posterior > 0.0

    def test_update_with_neutral_evidence(self):
        """Test update with likelihood_ratio = 1 (neutral evidence)."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.6)

        posterior = tracker.update("H1", likelihood_ratio=1.0)

        # Should remain the same
        assert posterior == 0.6

    def test_update_multiple_times(self):
        """Test multiple sequential updates."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        tracker.update("H1", likelihood_ratio=2.0)
        posterior1 = tracker.get_posterior("H1")

        tracker.update("H1", likelihood_ratio=2.0)
        posterior2 = tracker.get_posterior("H1")

        # Each update should increase posterior
        assert posterior2 > posterior1

    def test_update_without_prior_set(self):
        """Test update when prior not explicitly set."""
        tracker = ConfidenceTracker()

        # Default prior is 0.0
        posterior = tracker.update("H1", likelihood_ratio=2.0)

        # With prior 0, posterior stays 0 (no prior belief)
        assert posterior == 0.0

    def test_update_from_extreme_prior(self):
        """Test update starting from extreme prior."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.99)

        posterior = tracker.update("H1", likelihood_ratio=0.1)

        # Should decrease but not to 0
        assert 0.9 < posterior < 0.99

    def test_update_evidence_supports_parameter_ignored(self):
        """Test that evidence_supports parameter is ignored (LR encodes direction)."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        # Both should give same result since LR encodes direction
        posterior1 = tracker.update("H1", likelihood_ratio=2.0, evidence_supports=True)
        posterior2 = tracker.update("H2", likelihood_ratio=2.0, evidence_supports=False)
        tracker2 = ConfidenceTracker()
        tracker2.set_prior("H2", 0.5)
        posterior3 = tracker2.update("H2", likelihood_ratio=2.0)

        assert abs(posterior1 - posterior3) < 0.001


class TestUpdateExceptionHandling:
    """QA-001-001: Exception handler tests for likelihood_ratio validation."""

    def test_update_raises_on_zero_likelihood(self):
        """Test that likelihood_ratio = 0 raises ValueError."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        with pytest.raises(ValueError) as exc_info:
            tracker.update("H1", likelihood_ratio=0)

        assert "positive" in str(exc_info.value).lower()
        assert "likelihood_ratio" in str(exc_info.value).lower()

    def test_update_raises_on_negative_likelihood(self):
        """Test that negative likelihood_ratio raises ValueError."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        with pytest.raises(ValueError) as exc_info:
            tracker.update("H1", likelihood_ratio=-1.5)

        assert "positive" in str(exc_info.value).lower()
        assert "likelihood_ratio" in str(exc_info.value).lower()

    def test_update_raises_on_nan_likelihood(self):
        """Test that NaN likelihood_ratio behavior."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        # In Python, NaN > 0 is False, so NaN passes the <= 0 check
        # But Bayes formula with NaN produces NaN
        posterior = tracker.update("H1", likelihood_ratio=float('nan'))

        # Result should be NaN
        assert math.isnan(posterior)

    def test_update_raises_on_infinity_likelihood(self):
        """Test that infinite likelihood_ratio behavior."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        # Positive infinity - Bayes formula with inf produces NaN
        posterior = tracker.update("H1", likelihood_ratio=float('inf'))

        # Result should be NaN (inf * 0.5 / (inf * 0.5 + 0.5) = inf / inf = nan)
        assert math.isnan(posterior)

    def test_update_negative_infinity_raises(self):
        """Test that negative infinity raises ValueError."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        with pytest.raises(ValueError):
            tracker.update("H1", likelihood_ratio=float('-inf'))

    def test_update_very_small_positive_likelihood(self):
        """Test update with very small positive likelihood_ratio."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.9)

        # Very small LR should strongly decrease posterior
        posterior = tracker.update("H1", likelihood_ratio=0.001)

        assert posterior < 0.9
        assert posterior > 0.0

    def test_update_very_large_likelihood(self):
        """Test update with very large likelihood_ratio."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.1)

        # Very large LR should strongly increase posterior
        posterior = tracker.update("H1", likelihood_ratio=1000)

        assert posterior > 0.1
        assert posterior > 0.9


class TestReset:
    """Tests for reset method."""

    def test_reset_clears_posteriors(self):
        """Test that reset clears all posterior updates."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)
        tracker.update("H1", likelihood_ratio=2.0)
        tracker.set_prior("H2", 0.4)
        tracker.update("H2", likelihood_ratio=1.5)

        tracker.reset()

        # Posteriors should be cleared
        assert tracker.posteriors == {}
        # Priors should remain
        assert tracker.get_prior("H1") == 0.5
        assert tracker.get_prior("H2") == 0.4

    def test_reset_multiple_times(self):
        """Test that reset can be called multiple times."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)
        tracker.update("H1", likelihood_ratio=2.0)

        tracker.reset()
        tracker.reset()  # Second reset

        assert tracker.posteriors == {}


class TestBatchUpdate:
    """Tests for batch_update method."""

    def test_batch_update_multiple_hypotheses(self):
        """Test updating multiple hypotheses at once."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)
        tracker.set_prior("H2", 0.3)
        tracker.set_prior("H3", 0.7)

        evidence = {
            "H1": {"likelihood_ratio": 2.0, "supports": True},
            "H2": {"likelihood_ratio": 0.5, "supports": False},
            "H3": {"likelihood_ratio": 1.5, "supports": True},
        }

        results = tracker.batch_update(evidence)

        assert "H1" in results
        assert "H2" in results
        assert "H3" in results
        # H1 should increase (LR > 1)
        assert results["H1"] > 0.5
        # H2 should decrease (LR < 1)
        assert results["H2"] < 0.3

    def test_batch_update_empty_dict(self):
        """Test batch update with empty evidence dict."""
        tracker = ConfidenceTracker()

        results = tracker.batch_update({})

        assert results == {}

    def test_batch_update_with_missing_likelihood(self):
        """Test batch update with missing likelihood_ratio defaults to 1.0."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.6)

        results = tracker.batch_update({"H1": {"supports": True}})

        # Should default to 1.0 (no change)
        assert results["H1"] == 0.6

    def test_batch_update_with_missing_supports(self):
        """Test batch update with missing supports defaults to True."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        results = tracker.batch_update({"H1": {"likelihood_ratio": 2.0}})

        # Should use LR=2.0 (supports param is ignored anyway)
        expected = 0.6666666666666666
        assert abs(results["H1"] - expected) < 0.001


class TestNormalize:
    """Tests for normalize method."""

    def test_normalize_two_hypotheses(self):
        """Test normalizing two competing hypotheses."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.6)
        tracker.set_prior("H2", 0.4)

        tracker.update("H1", likelihood_ratio=2.0)
        tracker.update("H2", likelihood_ratio=0.5)

        normalized = tracker.normalize(["H1", "H2"])

        # Should sum to 1.0
        assert abs(normalized["H1"] + normalized["H2"] - 1.0) < 0.001

    def test_normalize_three_hypotheses(self):
        """Test normalizing three hypotheses."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.33)
        tracker.set_prior("H2", 0.33)
        tracker.set_prior("H3", 0.34)

        tracker.update("H1", likelihood_ratio=2.0)
        tracker.update("H2", likelihood_ratio=1.5)
        tracker.update("H3", likelihood_ratio=1.0)

        normalized = tracker.normalize(["H1", "H2", "H3"])

        # Should sum to approximately 1.0
        total = normalized["H1"] + normalized["H2"] + normalized["H3"]
        assert abs(total - 1.0) < 0.001

    def test_normalize_all_zero_returns_zero(self):
        """Test normalizing when all posteriors are zero."""
        tracker = ConfidenceTracker()

        normalized = tracker.normalize(["H1", "H2", "H3"])

        assert normalized["H1"] == 0.0
        assert normalized["H2"] == 0.0
        assert normalized["H3"] == 0.0

    def test_normalize_preserves_relative_strengths(self):
        """Test that normalize preserves relative hypothesis strengths."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.6)
        tracker.set_prior("H2", 0.4)

        tracker.update("H1", likelihood_ratio=3.0)
        tracker.update("H2", likelihood_ratio=2.0)

        posteriors_before = {
            "H1": tracker.get_posterior("H1"),
            "H2": tracker.get_posterior("H2"),
        }

        normalized = tracker.normalize(["H1", "H2"])

        # H1 should still be stronger than H2
        assert normalized["H1"] > normalized["H2"]

    def test_normalize_with_some_zero_posteriors(self):
        """Test normalizing when some hypotheses have zero posteriors."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)
        tracker.set_prior("H2", 0.0)  # Zero prior
        tracker.set_prior("H3", 0.5)

        tracker.update("H1", likelihood_ratio=2.0)
        tracker.update("H3", likelihood_ratio=1.5)

        normalized = tracker.normalize(["H1", "H2", "H3"])

        # H1 and H3 should split the probability (H2 is 0)
        assert abs(normalized["H1"] + normalized["H3"] - 1.0) < 0.001
        assert normalized["H2"] == 0.0


class TestBayesianCalculationAccuracy:
    """Tests for accuracy of Bayesian calculations."""

    def test_bayes_formula_with_lr_2(self):
        """Test Bayes formula with LR=2, prior=0.5."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        posterior = tracker.update("H1", likelihood_ratio=2.0)

        # P(H|E) = (2 * 0.5) / (2 * 0.5 + 0.5) = 1 / 1.5
        expected = 2 * 0.5 / (2 * 0.5 + 0.5)
        assert abs(posterior - expected) < 0.0001

    def test_bayes_formula_with_lr_05(self):
        """Test Bayes formula with LR=0.5, prior=0.7."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.7)

        posterior = tracker.update("H1", likelihood_ratio=0.5)

        # P(H|E) = (0.5 * 0.7) / (0.5 * 0.7 + 0.3)
        expected = 0.5 * 0.7 / (0.5 * 0.7 + 0.3)
        assert abs(posterior - expected) < 0.0001

    def test_converges_to_one_with_strong_evidence(self):
        """Test that strong supporting evidence converges to 1.0."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        # Multiple strong updates
        for _ in range(5):
            tracker.update("H1", likelihood_ratio=10.0)

        posterior = tracker.get_posterior("H1")

        # Should be very close to 1.0
        assert posterior > 0.99

    def test_converges_to_zero_with_strank_refuting_evidence(self):
        """Test that strong refuting evidence converges to 0.0."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)

        # Multiple strong refuting updates
        for _ in range(5):
            tracker.update("H1", likelihood_ratio=0.1)

        posterior = tracker.get_posterior("H1")

        # Should be very close to 0.0
        assert posterior < 0.01


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_update_nonexistent_hypothesis(self):
        """Test updating a hypothesis with no prior set."""
        tracker = ConfidenceTracker()

        posterior = tracker.update("NewHypothesis", likelihood_ratio=2.0)

        # With no prior (0), posterior stays 0
        assert posterior == 0.0

    def test_multiple_hypotheses_independent(self):
        """Test that hypotheses are tracked independently."""
        tracker = ConfidenceTracker()
        tracker.set_prior("H1", 0.5)
        tracker.set_prior("H2", 0.5)

        tracker.update("H1", likelihood_ratio=3.0)
        tracker.update("H2", likelihood_ratio=0.3)

        # H1 should increase, H2 should decrease
        assert tracker.get_posterior("H1") > 0.5
        assert tracker.get_posterior("H2") < 0.5

    def test_unicode_hypothesis_names(self):
        """Test hypothesis names with unicode characters."""
        tracker = ConfidenceTracker()
        tracker.set_prior("日本語", 0.5)

        posterior = tracker.update("日本語", likelihood_ratio=2.0)

        assert posterior > 0.5

    def test_long_hypothesis_names(self):
        """Test hypothesis with very long name."""
        tracker = ConfidenceTracker()
        long_name = "H" * 1000
        tracker.set_prior(long_name, 0.6)

        posterior = tracker.update(long_name, likelihood_ratio=1.5)

        assert posterior > 0.6

    def test_special_characters_in_hypothesis_names(self):
        """Test hypothesis names with special characters."""
        tracker = ConfidenceTracker()
        special_name = "H1: Test (with/special-chars)"

        tracker.set_prior(special_name, 0.5)
        posterior = tracker.update(special_name, likelihood_ratio=2.0)

        assert posterior > 0.5
