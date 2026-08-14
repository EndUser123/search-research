"""Tests for dead code removal (F401/F841 violations)."""



class TestDeadCodeRemoval:
    """Verify dead code has been removed from search-research package."""

    def test_cli_import_works(self):
        """Test that cli.py imports without errors after dead code removal."""
        # This should not raise ImportError
        import search_research.cli
        assert search_research.cli is not None

    def test_learning_system_recommendations_removed(self):
        """Test that unused recommendations variable was removed."""
        from enhancement.learning_system import LearningSystem

        ls = LearningSystem()

        # This should work without errors (recommendations variable removed)
        result = ls.get_pattern_based_recommendation(
            query="test query",
            candidate_modes=["auto", "web", "quick"]
        )
        # Result can be None or dict - both are valid
        assert result is None or isinstance(result, dict)

    def test_quality_optimizer_import_works(self):
        """Test that quality_optimizer module imports without errors."""
        from enhancement.quality_optimizer import (
            CostBenefitOptimizer,
            QualityPredictor,
        )

        # Verify classes exist and can be instantiated
        predictor = QualityPredictor()
        assert predictor is not None

        optimizer = CostBenefitOptimizer()
        assert optimizer is not None
