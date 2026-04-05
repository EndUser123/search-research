"""Tests for hypothesis_scorer module.

Tests for hypothesis scoring, ranking, pruning, and evidence tier integration.
"""

import pytest

from rca.hypothesis_scorer import HypothesisScorer


class TestHypothesisScorerInit:
    """Test HypothesisScorer initialization."""

    def test_default_initialization(self):
        """Scorer can be created with defaults."""
        scorer = HypothesisScorer()

        assert scorer.pruning_threshold == 0.6
        assert len(scorer.hypotheses) == 0

    def test_custom_pruning_threshold(self):
        """Custom pruning threshold can be set."""
        scorer = HypothesisScorer(pruning_threshold=0.7)

        assert scorer.pruning_threshold == 0.7

    def test_custom_weights(self):
        """Custom weights can be provided."""
        scorer = HypothesisScorer(
            weights={
                "reproducibility_weight": 0.5,
                "recency_weight": 0.3,
                "impact_weight": 0.2,
            }
        )

        assert scorer.weights["reproducibility"] == 0.5
        assert scorer.weights["recency"] == 0.3
        assert scorer.weights["impact"] == 0.2

    def test_default_weights_from_spec(self):
        """Default weights match specification."""
        scorer = HypothesisScorer()

        # Spec: Reproducibility(0.3) * Recency(0.2) * Impact(0.5)
        assert scorer.weights["reproducibility"] == 0.3
        assert scorer.weights["recency"] == 0.2
        assert scorer.weights["impact"] == 0.5


class TestAddHypothesis:
    """Test adding hypotheses."""

    def test_add_simple_hypothesis(self):
        """Simple hypothesis can be added."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis("Database timeout")

        assert hyp_id == "hyp_0"
        assert len(scorer.hypotheses) == 1
        assert scorer.hypotheses[0]["text"] == "Database timeout"

    def test_add_multiple_hypotheses(self):
        """Multiple hypotheses get unique IDs."""
        scorer = HypothesisScorer()

        id1 = scorer.add_hypothesis("H1")
        id2 = scorer.add_hypothesis("H2")
        id3 = scorer.add_hypothesis("H3")

        assert id1 == "hyp_0"
        assert id2 == "hyp_1"
        assert id3 == "hyp_2"

    def test_hypothesis_with_custom_factors(self):
        """Hypothesis can have custom scoring factors."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis(
            "API timeout",
            reproducibility=0.9,
            recency=0.8,
            impact=0.7,
            prior=0.6,
            evidence_likelihood=0.8,
        )

        hyp = scorer.get_hypothesis(hyp_id)

        assert hyp["reproducibility"] == 0.9
        assert hyp["recency"] == 0.8
        assert hyp["impact"] == 0.7
        assert hyp["prior"] == 0.6
        assert hyp["evidence_likelihood"] == 0.8

    def test_hypothesis_score_calculation(self):
        """Hypothesis score is calculated correctly."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis(
            "Test",
            reproducibility=0.9,
            recency=0.8,
            impact=0.7,
            prior=0.5,
            evidence_likelihood=0.6,
        )

        hyp = scorer.get_hypothesis(hyp_id)

        # Factor score: 0.9^0.3 * 0.8^0.2 * 0.7^0.5
        # Bayesian likelihood: 0.6 * 0.5 = 0.3
        # Final score: (factor_score + 0.3) / 2
        assert hyp["score"] > 0
        assert hyp["score"] <= 1.0
        assert hyp["bayesian_likelihood"] == 0.3

    def test_pruned_flag_low_score(self):
        """Low score hypotheses are marked pruned."""
        scorer = HypothesisScorer(pruning_threshold=0.6)
        hyp_id = scorer.add_hypothesis(
            "Weak hypothesis",
            reproducibility=0.1,
            recency=0.1,
            impact=0.1,
            prior=0.1,
            evidence_likelihood=0.1,
        )

        hyp = scorer.get_hypothesis(hyp_id)

        assert hyp["pruned"] is True

    def test_pruned_flag_high_score(self):
        """High score hypotheses are not pruned."""
        scorer = HypothesisScorer(pruning_threshold=0.6)
        hyp_id = scorer.add_hypothesis(
            "Strong hypothesis",
            reproducibility=0.9,
            recency=0.9,
            impact=0.9,
            prior=0.9,
            evidence_likelihood=0.9,
        )

        hyp = scorer.get_hypothesis(hyp_id)

        assert hyp["pruned"] is False


class TestGetTopHypotheses:
    """Test retrieving top hypotheses."""

    def test_get_top_single(self):
        """Get single top hypothesis."""
        scorer = HypothesisScorer()
        scorer.add_hypothesis("H1", reproducibility=0.9)
        scorer.add_hypothesis("H2", reproducibility=0.5)

        top = scorer.get_top_hypotheses(1)

        assert len(top) == 1
        assert top[0]["text"] == "H1"

    def test_get_top_multiple(self):
        """Get multiple top hypotheses."""
        scorer = HypothesisScorer()
        scorer.add_hypothesis("H1", reproducibility=0.9)
        scorer.add_hypothesis("H2", reproducibility=0.7)
        scorer.add_hypothesis("H3", reproducibility=0.5)
        scorer.add_hypothesis("H4", reproducibility=0.3)

        top = scorer.get_top_hypotheses(3)

        assert len(top) == 3
        assert top[0]["text"] == "H1"
        assert top[1]["text"] == "H2"
        assert top[2]["text"] == "H3"

    def test_get_top_excludes_pruned(self):
        """Pruned hypotheses are excluded by default."""
        scorer = HypothesisScorer(pruning_threshold=0.6)
        scorer.add_hypothesis("Strong", reproducibility=0.9, prior=0.9, evidence_likelihood=0.9)
        scorer.add_hypothesis("Weak", reproducibility=0.1, prior=0.1, evidence_likelihood=0.1)

        top = scorer.get_top_hypotheses(10)

        assert len(top) == 1
        assert top[0]["text"] == "Strong"

    def test_get_top_includes_pruned(self):
        """Pruned hypotheses can be included."""
        scorer = HypothesisScorer(pruning_threshold=0.6)
        scorer.add_hypothesis("Strong", reproducibility=0.9, prior=0.9, evidence_likelihood=0.9)
        scorer.add_hypothesis("Weak", reproducibility=0.1, prior=0.1, evidence_likelihood=0.1)

        top = scorer.get_top_hypotheses(10, include_pruned=True)

        assert len(top) == 2

    def test_get_top_sorted_by_score(self):
        """Hypotheses are sorted by score descending."""
        scorer = HypothesisScorer()
        scorer.add_hypothesis("Low", reproducibility=0.3)
        scorer.add_hypothesis("High", reproducibility=0.9)
        scorer.add_hypothesis("Mid", reproducibility=0.6)

        top = scorer.get_top_hypotheses(10)

        scores = [h["score"] for h in top]
        assert scores == sorted(scores, reverse=True)


class TestGetHypothesis:
    """Test retrieving specific hypotheses."""

    def test_get_existing_hypothesis(self):
        """Get existing hypothesis by ID."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis("Test")

        hyp = scorer.get_hypothesis(hyp_id)

        assert hyp is not None
        assert hyp["text"] == "Test"

    def test_get_nonexistent_hypothesis(self):
        """Getting nonexistent hypothesis returns None."""
        scorer = HypothesisScorer()

        hyp = scorer.get_hypothesis("invalid_id")

        assert hyp is None


class TestClear:
    """Test clearing hypotheses."""

    def test_clear_all(self):
        """Clear removes all hypotheses."""
        scorer = HypothesisScorer()
        scorer.add_hypothesis("H1")
        scorer.add_hypothesis("H2")
        scorer.add_hypothesis("H3")

        scorer.clear()

        assert len(scorer.hypotheses) == 0

    def test_clear_multiple_times(self):
        """Clear can be called multiple times."""
        scorer = HypothesisScorer()
        scorer.add_hypothesis("H1")

        scorer.clear()
        scorer.clear()

        assert len(scorer.hypotheses) == 0


class TestBayesianUpdates:
    """Test Bayesian confidence updates."""

    def test_set_prior(self):
        """Prior can be set for hypothesis."""
        scorer = HypothesisScorer()
        scorer.set_prior("Database timeout", 0.3)

        confidence = scorer.get_confidence("Database timeout")

        assert confidence == 0.3

    def test_update_with_supporting_evidence(self):
        """Supporting evidence increases confidence."""
        scorer = HypothesisScorer()
        scorer.set_prior("H1", 0.5)
        scorer.update("H1", evidence_supports=True, likelihood_ratio=2.0)

        confidence = scorer.get_confidence("H1")

        assert confidence > 0.5

    def test_update_with_refuting_evidence(self):
        """Refuting evidence decreases confidence."""
        scorer = HypothesisScorer()
        scorer.set_prior("H1", 0.8)
        scorer.update("H1", evidence_supports=False, likelihood_ratio=0.5)

        confidence = scorer.get_confidence("H1")

        assert confidence < 0.8

    def test_get_confidence_nonexistent(self):
        """Nonexistent hypothesis returns 0.0."""
        scorer = HypothesisScorer()

        confidence = scorer.get_confidence("nonexistent")

        assert confidence == 0.0


class TestRank:
    """Test hypothesis ranking."""

    def test_rank_by_combined_score(self):
        """Rank hypotheses by combined score and confidence."""
        scorer = HypothesisScorer()
        scorer.set_prior("H1", 0.9)
        scorer.add_hypothesis("H1", reproducibility=0.9, recency=0.8, impact=0.7)

        scorer.set_prior("H2", 0.3)
        scorer.add_hypothesis("H2", reproducibility=0.5, recency=0.6, impact=0.4)

        ranked = scorer.rank(["H1", "H2"])

        assert ranked[0] == "H1"
        assert ranked[1] == "H2"

    def test_rank_with_tie(self):
        """Ties are broken by hypothesis name."""
        scorer = HypothesisScorer()
        scorer.set_prior("A", 0.5)
        scorer.add_hypothesis("A", reproducibility=0.5)

        scorer.set_prior("B", 0.5)
        scorer.add_hypothesis("B", reproducibility=0.5)

        ranked = scorer.rank(["B", "A"])

        # With equal scores, should sort alphabetically (reverse)
        assert ranked == ["B", "A"]


class TestViableAndPruned:
    """Test viable and pruned hypothesis filtering."""

    def test_get_viable_hypotheses(self):
        """Get only hypotheses meeting threshold."""
        scorer = HypothesisScorer(pruning_threshold=0.6)
        scorer.add_hypothesis("Viable", reproducibility=0.9, prior=0.9, evidence_likelihood=0.9)
        scorer.add_hypothesis("Pruned", reproducibility=0.1, prior=0.1, evidence_likelihood=0.1)

        viable = scorer.get_viable_hypotheses()

        assert len(viable) == 1
        assert viable[0]["text"] == "Viable"

    def test_get_pruned_hypotheses(self):
        """Get only pruned hypotheses."""
        scorer = HypothesisScorer(pruning_threshold=0.6)
        scorer.add_hypothesis("Viable", reproducibility=0.9, prior=0.9, evidence_likelihood=0.9)
        scorer.add_hypothesis("Pruned", reproducibility=0.1, prior=0.1, evidence_likelihood=0.1)

        pruned = scorer.get_pruned_hypotheses()

        assert len(pruned) == 1
        assert pruned[0]["text"] == "Pruned"


class TestCalculateBayesianLikelihood:
    """Test Bayesian likelihood calculation."""

    def test_basic_calculation(self):
        """Basic likelihood calculation."""
        scorer = HypothesisScorer()
        result = scorer.calculate_bayesian_likelihood(0.7, 0.8)

        assert result == 0.56

    def test_zero_prior(self):
        """Zero prior produces zero likelihood."""
        scorer = HypothesisScorer()
        result = scorer.calculate_bayesian_likelihood(0.0, 0.8)

        assert result == 0.0

    def test_zero_evidence_likelihood(self):
        """Zero evidence likelihood produces zero."""
        scorer = HypothesisScorer()
        result = scorer.calculate_bayesian_likelihood(0.7, 0.0)

        assert result == 0.0

    def test_both_one(self):
        """Both 1.0 produces 1.0."""
        scorer = HypothesisScorer()
        result = scorer.calculate_bayesian_likelihood(1.0, 1.0)

        assert result == 1.0

    def test_raises_on_invalid_prior(self):
        """Invalid prior raises ValueError."""
        scorer = HypothesisScorer()

        with pytest.raises(ValueError):
            scorer.calculate_bayesian_likelihood(1.5, 0.5)

        with pytest.raises(ValueError):
            scorer.calculate_bayesian_likelihood(-0.1, 0.5)

    def test_raises_on_invalid_evidence_likelihood(self):
        """Invalid evidence likelihood raises ValueError."""
        scorer = HypothesisScorer()

        with pytest.raises(ValueError):
            scorer.calculate_bayesian_likelihood(0.5, 1.5)

        with pytest.raises(ValueError):
            scorer.calculate_bayesian_likelihood(0.5, -0.1)


class TestEvidenceTierIntegration:
    """Test evidence tier integration."""

    def test_add_evidence_to_hypothesis(self):
        """Evidence can be added to hypothesis."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis("Database timeout")

        scorer.add_evidence_to_hypothesis(
            hyp_id,
            "failing_test",
            "Test times out after 30s",
        )

        hyp = scorer.get_hypothesis(hyp_id)

        assert "evidence_sources" in hyp
        assert len(hyp["evidence_sources"]) == 1

    def test_add_multiple_evidence_sources(self):
        """Multiple evidence sources can be added."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis("Database timeout")

        scorer.add_evidence_to_hypothesis(hyp_id, "failing_test", "Test fails")
        scorer.add_evidence_to_hypothesis(hyp_id, "stack_trace", "Trace shows timeout")

        hyp = scorer.get_hypothesis(hyp_id)

        assert len(hyp["evidence_sources"]) == 2

    def test_confidence_ceiling_updated(self):
        """Confidence ceiling is updated when evidence added."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis("Database timeout")

        scorer.add_evidence_to_hypothesis(hyp_id, "speculation", "Maybe timeout")

        hyp = scorer.get_hypothesis(hyp_id)

        assert "confidence_ceiling" in hyp
        assert hyp["confidence_ceiling"] < 1.0

    def test_get_confidence_ceiling(self):
        """Get confidence ceiling for hypothesis."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis("Database timeout")

        scorer.add_evidence_to_hypothesis(hyp_id, "speculation", "Maybe")

        ceiling = scorer.get_confidence_ceiling(hyp_id)

        assert 0.0 <= ceiling <= 1.0

    def test_get_confidence_ceiling_no_evidence(self):
        """No evidence returns ceiling of 1.0."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis("Database timeout")

        ceiling = scorer.get_confidence_ceiling(hyp_id)

        assert ceiling == 1.0

    def test_apply_evidence_ceiling(self):
        """Confidence is capped at evidence ceiling."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis("Database timeout")

        scorer.add_evidence_to_hypothesis(hyp_id, "speculation", "Maybe")

        capped = scorer.apply_evidence_ceiling(hyp_id, 0.9)

        assert capped < 0.9  # Should be capped by speculation tier

    def test_get_capped_confidence(self):
        """Get confidence capped by evidence tier."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis("Database timeout", prior=0.9)

        scorer.add_evidence_to_hypothesis(hyp_id, "speculation", "Maybe")

        capped = scorer.get_capped_confidence("Database timeout")

        assert capped < 0.9  # Should be capped

    def test_rank_with_evidence_tiers(self):
        """Rank with evidence tier ceilings applied."""
        scorer = HypothesisScorer()

        h1 = scorer.add_hypothesis("H1", prior=0.9)
        scorer.add_evidence_to_hypothesis(h1, "speculation", "Maybe")

        h2 = scorer.add_hypothesis("H2", prior=0.7)
        scorer.add_evidence_to_hypothesis(h2, "failing_test", "Test fails")

        ranked = scorer.rank_with_evidence_tiers(["H1", "H2"])

        # H2 should rank higher despite lower prior (better evidence tier)
        assert ranked[0] == "H2"

    def test_get_evidence_summary(self):
        """Get formatted evidence summary."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis("Database timeout")

        scorer.add_evidence_to_hypothesis(hyp_id, "failing_test", "Test fails")

        summary = scorer.get_evidence_summary(hyp_id)

        assert "evidence" in summary.lower() or len(summary) > 0

    def test_get_evidence_summary_no_evidence(self):
        """No evidence returns appropriate message."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis("Database timeout")

        summary = scorer.get_evidence_summary(hyp_id)

        assert "no evidence" in summary.lower()

    def test_is_verification_ready(self):
        """Check if hypothesis has Tier 1 or 2 evidence."""
        scorer = HypothesisScorer()
        hyp_id = scorer.add_hypothesis("Database timeout")

        # Tier 3 evidence - not ready
        scorer.add_evidence_to_hypothesis(hyp_id, "user_report", "User says slow")
        assert not scorer.is_verification_ready(hyp_id)

        # Add Tier 1 evidence - now ready
        scorer.add_evidence_to_hypothesis(hyp_id, "failing_test", "Test fails")
        assert scorer.is_verification_ready(hyp_id)


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_scorer_rank(self):
        """Ranking empty list returns empty list."""
        scorer = HypothesisScorer()

        ranked = scorer.rank([])

        assert ranked == []

    def test_invalid_hypothesis_id(self):
        """Invalid hypothesis ID raises error."""
        scorer = HypothesisScorer()

        with pytest.raises(ValueError):
            scorer.add_evidence_to_hypothesis("invalid", "failing_test", "Test")

    def test_get_hypothesis_nonexistent_for_evidence(self):
        """Get evidence for nonexistent hypothesis returns not found."""
        scorer = HypothesisScorer()

        summary = scorer.get_evidence_summary("invalid")

        assert "not found" in summary.lower()
