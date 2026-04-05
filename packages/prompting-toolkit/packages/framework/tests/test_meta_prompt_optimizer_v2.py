#!/usr/bin/env python3
"""
Unit tests for meta_prompt_optimizer module (hook package).

Tests for meta prompt optimization in hook package.
"""


from prompting_framework.meta_prompt_optimizer import (
    EnhancementSuggestion,
    OptimizationOptions,
    PromptEnhancement,
)


class TestPromptEnhancement:
    """Test PromptEnhancement dataclass."""

    def test_create_enhancement(self):
        """Create a prompt enhancement."""
        enhancement = PromptEnhancement(
            original_prompt="Write code",
            enhanced_prompt="Write a Python function that validates user input using regular expressions",
            enhancement_type="specificity",
            confidence=0.9,
        )
        assert enhancement.enhancement_type == "specificity"
        assert enhancement.confidence == 0.9

    def test_enhancement_with_suggestions(self):
        """Enhancement with suggestions."""
        enhancement = PromptEnhancement(
            original_prompt="Help me",
            enhanced_prompt="Help me debug this authentication issue where users with expired tokens can still access protected routes",
            enhancement_type="context",
            confidence=0.85,
            suggestions=[
                "Add specific error details",
                "Include affected routes",
                "Mention token type",
            ],
        )
        assert len(enhancement.suggestions) == 3


class TestEnhancementSuggestion:
    """Test EnhancementSuggestion dataclass."""

    def test_create_suggestion(self):
        """Create an enhancement suggestion."""
        suggestion = EnhancementSuggestion(
            suggestion_type="add_context",
            description="Add more context about the problem",
            priority="high",
            example="Instead of 'fix it', use 'fix the authentication bug in the login module'",
        )
        assert suggestion.suggestion_type == "add_context"
        assert suggestion.priority == "high"

    def test_suggestion_priority_levels(self):
        """Test all priority levels."""
        priorities = ["low", "medium", "high", "critical"]
        for priority in priorities:
            suggestion = EnhancementSuggestion(
                suggestion_type="test",
                description="Test suggestion",
                priority=priority,
                example="",
            )
            assert suggestion.priority == priority


class TestOptimizationOptions:
    """Test OptimizationOptions dataclass."""

    def test_create_options(self):
        """Create optimization options."""
        options = OptimizationOptions(
            target_audience="developers",
            max_length=500,
            preserve_style=False,
            add_examples=True,
            improve_clarity=True,
            add_constraints=True,
        )
        assert options.target_audience == "developers"
        assert options.add_examples is True

    def test_minimal_options(self):
        """Minimal optimization options."""
        options = OptimizationOptions(
            target_audience="general",
        )
        assert options.max_length == 0
        assert options.preserve_style is False


class TestEnhancementTypes:
    """Test different enhancement types."""

    def test_specificity_enhancement(self):
        """Specificity enhancement type."""
        enhancement = PromptEnhancement(
            original_prompt="Create a function",
            enhanced_prompt="Create a Python async function that fetches user data from PostgreSQL",
            enhancement_type="specificity",
            confidence=0.8,
        )
        assert enhancement.enhancement_type == "specificity"

    def test_context_enhancement(self):
        """Context enhancement type."""
        enhancement = PromptEnhancement(
            original_prompt="Optimize this",
            enhanced_prompt="Optimize this database query for the user_profiles table to reduce execution time under 100ms",
            enhancement_type="context",
            confidence=0.85,
        )
        assert enhancement.enhancement_type == "context"

    def test_clarity_enhancement(self):
        """Clarity enhancement type."""
        enhancement = PromptEnhancement(
            original_prompt="do stuff",
            enhanced_prompt="Implement user registration with email verification and password reset functionality",
            enhancement_type="clarity",
            confidence=0.9,
        )
        assert enhancement.enhancement_type == "clarity"


class TestEdgeCases:
    """Test edge cases for optimization."""

    def test_no_improvement_needed(self):
        """Handle prompt that needs no improvement."""
        enhancement = PromptEnhancement(
            original_prompt="Write a Python function that sorts a list of dictionaries by the 'date' key in descending order using the lambda function",
            enhanced_prompt="Write a Python function that sorts a list of dictionaries by the 'date' key in descending order using the lambda function",
            enhancement_type="none",
            confidence=1.0,
        )
        assert enhancement.enhancement_type == "none"

    def test_very_long_prompt(self):
        """Handle very long prompts."""
        long_text = "Analyze this " + "very " * 100 + "complex system"
        enhancement = PromptEnhancement(
            original_prompt=long_text,
            enhanced_prompt=long_text,
            enhancement_type="compression",
            confidence=0.7,
        )
        assert len(enhancement.original_prompt) > 500

    def test_empty_enhancement(self):
        """Handle empty enhancement."""
        enhancement = PromptEnhancement(
            original_prompt="",
            enhanced_prompt="",
            enhancement_type="empty",
            confidence=0.0,
        )
        assert enhancement.original_prompt == ""


class TestOptimizationScenarios:
    """Test various optimization scenarios."""

    def test_vague_to_specific(self):
        """Optimize vague prompt to specific."""
        enhancement = PromptEnhancement(
            original_prompt="fix it",
            enhanced_prompt="Fix the SQL injection vulnerability in the user authentication module where user input is concatenated directly into the query string",
            enhancement_type="specificity",
            confidence=0.95,
            suggestions=[
                "Add module name",
                "Specify vulnerability type",
                "Include technical details",
            ],
        )
        assert enhancement.confidence > 0.9

    def test_adding_technical_context(self):
        """Add technical context to prompt."""
        enhancement = PromptEnhancement(
            original_prompt="Write a web scraper",
            enhanced_prompt="Write a Python web scraper using BeautifulSoup and requests that respects robots.txt, implements rate limiting with 1 second delays, and handles HTTP errors with retry logic",
            enhancement_type="context",
            confidence=0.9,
        )
        assert "BeautifulSoup" in enhancement.enhanced_prompt
        assert "robots.txt" in enhancement.enhanced_prompt
