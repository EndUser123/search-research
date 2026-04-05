#!/usr/bin/env python3
"""
Unit tests for meta_prompt_optimizer module.

Tests for meta-prompt optimization functionality.
"""


from prompting_framework.meta_prompt_optimizer import (
    MetaPromptConfig,
    OptimizationCriterion,
    OptimizationResult,
    PromptTemplate,
)


class TestOptimizationCriterion:
    """Test OptimizationCriterion enum."""

    def test_all_criteria_defined(self):
        """Verify all expected criteria are defined."""
        expected_criteria = [
            "clarity",
            "specificity",
            "context",
            "constraints",
            "output_format",
            "token_efficiency",
        ]
        actual_values = [c.value for c in OptimizationCriterion]
        for expected in expected_criteria:
            assert expected in actual_values


class TestPromptTemplate:
    """Test PromptTemplate dataclass."""

    def test_create_template(self):
        """Create a prompt template."""
        template = PromptTemplate(
            template_id="template_1",
            name="Code Generation Template",
            description="Template for generating code",
            template_text="Write a function to {task} using {language}",
            variables=["task", "language"],
            category="code_generation",
            version="1.0",
        )
        assert template.template_id == "template_1"
        assert len(template.variables) == 2

    def test_template_with_defaults(self):
        """Create template with default values."""
        template = PromptTemplate(
            template_id="simple",
            name="Simple Template",
            description="A simple template",
            template_text="Hello {name}",
            variables=["name"],
        )
        assert template.category == ""
        assert template.version == ""

    def test_template_multiple_variables(self):
        """Create template with multiple variables."""
        template = PromptTemplate(
            template_id="complex",
            name="Complex Template",
            description="Template with many variables",
            template_text="Create a {type} for {purpose} with {style} in {language}",
            variables=["type", "purpose", "style", "language"],
        )
        assert len(template.variables) == 4


class TestMetaPromptConfig:
    """Test MetaPromptConfig dataclass."""

    def test_create_config(self):
        """Create meta-prompt configuration."""
        config = MetaPromptConfig(
            optimization_criteria=[
                OptimizationCriterion.CLARITY,
                OptimizationCriterion.SPECIFICITY,
            ],
            target_audience="developers",
            max_tokens=1000,
            output_format="structured",
            enable_examples=True,
        )
        assert len(config.optimization_criteria) == 2
        assert config.target_audience == "developers"

    def test_config_with_all_criteria(self):
        """Config with all optimization criteria."""
        config = MetaPromptConfig(
            optimization_criteria=list(OptimizationCriterion),
            target_audience="general",
            max_tokens=2000,
            output_format="conversational",
            enable_examples=True,
            enable_chain_of_thought=True,
        )
        assert len(config.optimization_criteria) > 5

    def test_config_minimal(self):
        """Minimal configuration."""
        config = MetaPromptConfig(
            optimization_criteria=[OptimizationCriterion.CLARITY],
        )
        assert config.target_audience == ""
        assert config.max_tokens == 0
        assert config.enable_examples is False


class TestOptimizationResult:
    """Test OptimizationResult dataclass."""

    def test_create_result_success(self):
        """Create successful optimization result."""
        result = OptimizationResult(
            original_prompt="Write code",
            optimized_prompt="Write a Python function that sorts a list of integers in ascending order",
            improvements={
                "specificity": 0.8,
                "clarity": 0.6,
                "context": 0.9,
            },
            overall_improvement=0.77,
            success=True,
            optimization_time=1.5,
            suggestions=[
                "Add specific requirements",
                "Include context about use case",
                "Specify language",
            ],
        )
        assert result.success is True
        assert len(result.original_prompt) < len(result.optimized_prompt)
        assert result.overall_improvement == 0.77

    def test_create_result_failure(self):
        """Create failed optimization result."""
        result = OptimizationResult(
            original_prompt="Help",
            optimized_prompt="Help",  # No improvement
            improvements={},
            overall_improvement=0.0,
            success=False,
            optimization_time=0.5,
            error_message="Prompt too vague to optimize",
        )
        assert result.success is False
        assert result.error_message == "Prompt too vague to optimize"

    def test_result_with_multiple_suggestions(self):
        """Result with multiple improvement suggestions."""
        result = OptimizationResult(
            original_prompt="Do this",
            optimized_prompt="Please implement a user authentication system with JWT tokens",
            improvements={
                "specificity": 0.9,
                "clarity": 0.7,
            },
            overall_improvement=0.8,
            success=True,
            optimization_time=1.0,
            suggestions=[
                "Add specific action verb",
                "Include technical details",
                "Specify expected outcome",
                "Add security considerations",
            ],
        )
        assert len(result.suggestions) == 4


class TestOptimizationCriteria:
    """Test different optimization criteria."""

    def test_clarity_criterion(self):
        """Clarity optimization criterion."""
        assert OptimizationCriterion.CLARITY.value == "clarity"

    def test_specificity_criterion(self):
        """Specificity optimization criterion."""
        assert OptimizationCriterion.SPECIFICITY.value == "specificity"

    def test_context_criterion(self):
        """Context optimization criterion."""
        assert OptimizationCriterion.CONTEXT.value == "context"

    def test_constraints_criterion(self):
        """Constraints optimization criterion."""
        assert OptimizationCriterion.CONSTRAINTS.value == "constraints"

    def test_output_format_criterion(self):
        """Output format optimization criterion."""
        assert OptimizationCriterion.OUTPUT_FORMAT.value == "output_format"

    def test_token_efficiency_criterion(self):
        """Token efficiency optimization criterion."""
        assert OptimizationCriterion.TOKEN_EFFICIENCY.value == "token_efficiency"


class TestTemplateCategories:
    """Test different template categories."""

    def test_code_generation_category(self):
        """Code generation template."""
        template = PromptTemplate(
            template_id="code_gen",
            name="Code Generator",
            description="Generate code snippets",
            template_text="Write {language} code to {task}",
            variables=["language", "task"],
            category="code_generation",
        )
        assert template.category == "code_generation"

    def test_analysis_category(self):
        """Analysis template."""
        template = PromptTemplate(
            template_id="analysis",
            name="Analyzer",
            description="Analyze text",
            template_text="Analyze the following {content_type}: {content}",
            variables=["content_type", "content"],
            category="analysis",
        )
        assert template.category == "analysis"

    def test_explanation_category(self):
        """Explanation template."""
        template = PromptTemplate(
            template_id="explain",
            name="Explainer",
            description="Explain concepts",
            template_text="Explain {concept} in simple terms",
            variables=["concept"],
            category="explanation",
        )
        assert template.category == "explanation"


class TestEdgeCases:
    """Test edge cases for meta-prompt optimization."""

    def test_empty_template(self):
        """Handle empty template."""
        template = PromptTemplate(
            template_id="empty",
            name="Empty",
            description="Empty template",
            template_text="",
            variables=[],
        )
        assert template.template_text == ""
        assert len(template.variables) == 0

    def test_template_no_variables(self):
        """Handle template with no variables."""
        template = PromptTemplate(
            template_id="static",
            name="Static",
            description="Static template",
            template_text="This is a static prompt with no variables",
            variables=[],
        )
        assert len(template.variables) == 0

    def test_zero_improvement(self):
        """Handle optimization with no improvement."""
        result = OptimizationResult(
            original_prompt="Already optimized prompt",
            optimized_prompt="Already optimized prompt",
            improvements={},
            overall_improvement=0.0,
            success=True,
            optimization_time=0.1,
            suggestions=[],
        )
        assert result.overall_improvement == 0.0
        assert len(result.suggestions) == 0

    def test_perfect_improvement(self):
        """Handle perfect optimization score."""
        result = OptimizationResult(
            original_prompt="bad",
            optimized_prompt="Excellent, detailed, well-structured prompt with all necessary context",
            improvements={
                "specificity": 1.0,
                "clarity": 1.0,
                "context": 1.0,
            },
            overall_improvement=1.0,
            success=True,
            optimization_time=2.0,
            suggestions=[],
        )
        assert result.overall_improvement == 1.0

    def test_zero_optimization_time(self):
        """Handle cached optimization result."""
        result = OptimizationResult(
            original_prompt="test",
            optimized_prompt="optimized test",
            improvements={"clarity": 0.5},
            overall_improvement=0.5,
            success=True,
            optimization_time=0.0,  # From cache
        )
        assert result.optimization_time == 0.0


class TestImprovementScenarios:
    """Test various improvement scenarios."""

    def test_vague_to_specific(self):
        """Improvement from vague to specific."""
        result = OptimizationResult(
            original_prompt="fix it",
            optimized_prompt="Fix the authentication bug in the login module where users with expired tokens are still able to access protected routes",
            improvements={
                "specificity": 0.95,
                "clarity": 0.7,
                "context": 0.9,
            },
            overall_improvement=0.85,
            success=True,
            optimization_time=1.5,
            suggestions=["Added specific module and bug description"],
        )
        assert result.improvements["specificity"] > 0.9

    def test_generic_to_contextualized(self):
        """Improvement from generic to contextualized."""
        result = OptimizationResult(
            original_prompt="Write a function",
            optimized_prompt="Write a Python function using async/await that fetches user data from a PostgreSQL database and handles connection errors gracefully",
            improvements={
                "context": 0.95,
                "specificity": 0.85,
                "clarity": 0.7,
            },
            overall_improvement=0.83,
            success=True,
            optimization_time=2.0,
            suggestions=["Added language, pattern, and error handling context"],
        )
        assert result.improvements["context"] > 0.9

    def test_adding_constraints(self):
        """Improvement by adding constraints."""
        result = OptimizationResult(
            original_prompt="Create a web scraper",
            optimized_prompt="Create a Python web scraper that respects robots.txt, limits requests to 1 per second, uses caching, and handles errors with retries",
            improvements={
                "constraints": 0.9,
                "clarity": 0.7,
                "specificity": 0.8,
            },
            overall_improvement=0.8,
            success=True,
            optimization_time=1.8,
            suggestions=["Added rate limiting, caching, and error handling constraints"],
        )
        assert result.improvements["constraints"] > 0.8
