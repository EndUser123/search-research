#!/usr/bin/env python3
"""
Unit tests for verbalized_sampling_technique module.

Tests for Verbalized Sampling technique implementation.
"""


from prompting_framework.verbalized_sampling_technique import (
    SampledResponse,
    SamplingResult,
    SamplingStrategy,
    VerbalizedReasoning,
)


class TestSamplingStrategy:
    """Test SamplingStrategy enum."""

    def test_all_strategies_defined(self):
        """Verify all expected strategies are defined."""
        expected_strategies = [
            "temperature_sampling",
            "top_k_sampling",
            "top_p_sampling",
            "beam_search",
            "diverse_beam_search",
        ]
        actual_values = [s.value for s in SamplingStrategy]
        for expected in expected_strategies:
            assert expected in actual_values

    def test_temperature_sampling_value(self):
        """Temperature sampling has correct value."""
        assert SamplingStrategy.TEMPERATURE_SAMPLING.value == "temperature_sampling"

    def test_top_k_sampling_value(self):
        """Top-k sampling has correct value."""
        assert SamplingStrategy.TOP_K_SAMPLING.value == "top_k_sampling"

    def test_top_p_sampling_value(self):
        """Top-p sampling has correct value."""
        assert SamplingStrategy.TOP_P_SAMPLING.value == "top_p_sampling"


class TestVerbalizedReasoning:
    """Test VerbalizedReasoning dataclass."""

    def test_create_reasoning(self):
        """Create verbalized reasoning."""
        reasoning = VerbalizedReasoning(
            reasoning_steps=[
                "First, I need to understand the problem",
                "Then, I'll consider possible solutions",
                "Finally, I'll choose the best approach",
            ],
            confidence_level=0.85,
            reasoning_type="step_by_step",
            intermediate_conclusions=[
                "Problem is well-defined",
                "Multiple viable solutions exist",
            ],
        )
        assert len(reasoning.reasoning_steps) == 3
        assert reasoning.confidence_level == 0.85
        assert reasoning.reasoning_type == "step_by_step"

    def test_reasoning_with_defaults(self):
        """Create reasoning with default values."""
        reasoning = VerbalizedReasoning(
            reasoning_steps=["Single step"],
            confidence_level=0.7,
        )
        assert reasoning.reasoning_type == ""
        assert reasoning.intermediate_conclusions == []

    def test_multiple_reasoning_steps(self):
        """Create reasoning with many steps."""
        steps = [f"Step {i}: Analyze aspect {i}" for i in range(1, 11)]
        reasoning = VerbalizedReasoning(
            reasoning_steps=steps,
            confidence_level=0.9,
            reasoning_type="comprehensive",
        )
        assert len(reasoning.reasoning_steps) == 10


class TestSampledResponse:
    """Test SampledResponse dataclass."""

    def test_create_response(self):
        """Create a sampled response."""
        response = SampledResponse(
            response_id="sample_1",
            response_text="This is a sampled response",
            sampling_parameters={"temperature": 0.8, "top_p": 0.9},
            reasoning=VerbalizedReasoning(
                reasoning_steps=["Reasoning step"],
                confidence_level=0.75,
            ),
            quality_score=0.8,
            diversity_score=0.7,
        )
        assert response.response_id == "sample_1"
        assert response.quality_score == 0.8
        assert response.diversity_score == 0.7

    def test_response_with_high_quality(self):
        """Create high quality response."""
        response = SampledResponse(
            response_id="high_quality",
            response_text="Excellent response",
            sampling_parameters={},
            reasoning=VerbalizedReasoning(
                reasoning_steps=["Thorough reasoning"],
                confidence_level=0.95,
            ),
            quality_score=0.95,
            diversity_score=0.6,
        )
        assert response.quality_score > 0.9

    def test_response_with_high_diversity(self):
        """Create high diversity response."""
        response = SampledResponse(
            response_id="diverse",
            response_text="Unique perspective",
            sampling_parameters={"temperature": 1.5},
            reasoning=VerbalizedReasoning(
                reasoning_steps=["Creative reasoning"],
                confidence_level=0.7,
            ),
            quality_score=0.7,
            diversity_score=0.95,
        )
        assert response.diversity_score > 0.9


class TestSamplingResult:
    """Test SamplingResult dataclass."""

    def test_create_result(self):
        """Create a sampling result."""
        samples = [
            SampledResponse(
                response_id="s1",
                response_text="Response 1",
                sampling_parameters={},
                reasoning=VerbalizedReasoning(
                    reasoning_steps=["Reasoning"],
                    confidence_level=0.8,
                ),
                quality_score=0.8,
                diversity_score=0.7,
            )
        ]

        result = SamplingResult(
            original_prompt="Generate options",
            sampling_strategy=SamplingStrategy.TEMPERATURE_SAMPLING,
            sampling_parameters={"temperature": 0.7, "num_samples": 5},
            samples_generated=samples,
            best_sample_id="s1",
            aggregation_method="best_quality",
            execution_time=2.5,
            success=True,
        )
        assert result.sampling_strategy == SamplingStrategy.TEMPERATURE_SAMPLING
        assert len(result.samples_generated) == 1

    def test_result_multiple_samples(self):
        """Create result with multiple samples."""
        samples = [
            SampledResponse(
                response_id=f"sample_{i}",
                response_text=f"Response {i}",
                sampling_parameters={},
                reasoning=VerbalizedReasoning(
                    reasoning_steps=[f"Reasoning {i}"],
                    confidence_level=0.7 + i * 0.05,
                ),
                quality_score=0.7 + i * 0.05,
                diversity_score=0.6 + i * 0.1,
            )
            for i in range(1, 6)
        ]

        result = SamplingResult(
            original_prompt="Generate diverse responses",
            sampling_strategy=SamplingStrategy.DIVERSE_BEAM_SEARCH,
            sampling_parameters={"num_beams": 5},
            samples_generated=samples,
            best_sample_id="sample_5",
            aggregation_method="highest_quality",
            execution_time=5.0,
            success=True,
        )
        assert len(result.samples_generated) == 5

    def test_result_failure(self):
        """Handle failed sampling."""
        result = SamplingResult(
            original_prompt="Test prompt",
            sampling_strategy=SamplingStrategy.TEMPERATURE_SAMPLING,
            sampling_parameters={},
            samples_generated=[],
            best_sample_id="",
            aggregation_method="",
            execution_time=0.5,
            success=False,
            error_message="Sampling failed due to API error",
        )
        assert result.success is False
        assert result.error_message == "Sampling failed due to API error"


class TestSamplingStrategies:
    """Test different sampling strategies."""

    def test_beam_search_strategy(self):
        """Beam search strategy value."""
        assert SamplingStrategy.BEAM_SEARCH.value == "beam_search"

    def test_diverse_beam_search_strategy(self):
        """Diverse beam search strategy value."""
        assert SamplingStrategy.DIVERSE_BEAM_SEARCH.value == "diverse_beam_search"


class TestVerbalizedReasoningTypes:
    """Test different reasoning types."""

    def test_step_by_step_reasoning(self):
        """Step-by-step reasoning type."""
        reasoning = VerbalizedReasoning(
            reasoning_steps=["Step 1", "Step 2", "Step 3"],
            confidence_level=0.8,
            reasoning_type="step_by_step",
        )
        assert reasoning.reasoning_type == "step_by_step"

    def test_chain_of_thought_reasoning(self):
        """Chain of thought reasoning type."""
        reasoning = VerbalizedReasoning(
            reasoning_steps=["Thinking through this"],
            confidence_level=0.85,
            reasoning_type="chain_of_thought",
        )
        assert reasoning.reasoning_type == "chain_of_thought"

    def test_analytical_reasoning(self):
        """Analytical reasoning type."""
        reasoning = VerbalizedReasoning(
            reasoning_steps=["Analyzing components"],
            confidence_level=0.75,
            reasoning_type="analytical",
        )
        assert reasoning.reasoning_type == "analytical"


class TestQualityAndDiversityScoring:
    """Test quality and diversity scoring."""

    def test_high_quality_low_diversity(self):
        """Response with high quality but low diversity."""
        response = SampledResponse(
            response_id="safe",
            response_text="Standard response",
            sampling_parameters={"temperature": 0.3},
            reasoning=VerbalizedReasoning(
                reasoning_steps=["Standard reasoning"],
                confidence_level=0.9,
            ),
            quality_score=0.95,
            diversity_score=0.4,
        )
        assert response.quality_score > response.diversity_score

    def test_low_quality_high_diversity(self):
        """Response with low quality but high diversity."""
        response = SampledResponse(
            response_id="creative",
            response_text="Unusual response",
            sampling_parameters={"temperature": 1.8},
            reasoning=VerbalizedReasoning(
                reasoning_steps=["Creative reasoning"],
                confidence_level=0.5,
            ),
            quality_score=0.6,
            diversity_score=0.95,
        )
        assert response.diversity_score > response.quality_score

    def test_balanced_scores(self):
        """Response with balanced quality and diversity."""
        response = SampledResponse(
            response_id="balanced",
            response_text="Balanced response",
            sampling_parameters={"temperature": 1.0},
            reasoning=VerbalizedReasoning(
                reasoning_steps=["Balanced reasoning"],
                confidence_level=0.75,
            ),
            quality_score=0.75,
            diversity_score=0.75,
        )
        assert abs(response.quality_score - response.diversity_score) < 0.1


class TestEdgeCases:
    """Test edge cases for verbalized sampling."""

    def test_empty_reasoning(self):
        """Handle response with minimal reasoning."""
        response = SampledResponse(
            response_id="minimal",
            response_text="Direct answer",
            sampling_parameters={},
            reasoning=VerbalizedReasoning(
                reasoning_steps=[],
                confidence_level=0.5,
            ),
            quality_score=0.6,
            diversity_score=0.5,
        )
        assert len(response.reasoning.reasoning_steps) == 0

    def test_single_sample_result(self):
        """Handle result with single sample."""
        sample = SampledResponse(
            response_id="only",
            response_text="Only response",
            sampling_parameters={},
            reasoning=VerbalizedReasoning(
                reasoning_steps=["Quick reasoning"],
                confidence_level=0.7,
            ),
            quality_score=0.7,
            diversity_score=0.5,
        )

        result = SamplingResult(
            original_prompt="Simple question",
            sampling_strategy=SamplingStrategy.TEMPERATURE_SAMPLING,
            sampling_parameters={"num_samples": 1},
            samples_generated=[sample],
            best_sample_id="only",
            aggregation_method="only_option",
            execution_time=1.0,
            success=True,
        )
        assert len(result.samples_generated) == 1

    def test_confidence_bounds(self):
        """Confidence level should be between 0 and 1."""
        reasoning = VerbalizedReasoning(
            reasoning_steps=["Test"],
            confidence_level=0.85,
        )
        assert 0.0 <= reasoning.confidence_level <= 1.0

    def test_scores_bounds(self):
        """Quality and diversity scores should be between 0 and 1."""
        response = SampledResponse(
            response_id="test",
            response_text="Test",
            sampling_parameters={},
            reasoning=VerbalizedReasoning(
                reasoning_steps=["Test"],
                confidence_level=0.5,
            ),
            quality_score=0.8,
            diversity_score=0.7,
        )
        assert 0.0 <= response.quality_score <= 1.0
        assert 0.0 <= response.diversity_score <= 1.0
