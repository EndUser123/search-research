"""Test cognitive_enhancers hook behavior.

Verifies that:
1. Frameworks are emitted for appropriate prompts
2. Visible tag tokens are not surfaced to the LLM
3. Empty result for non-actionable prompts
"""

from UserPromptSubmit_modules.base import HookContext
from UserPromptSubmit_modules.cognitive_enhancers import cognitive_enhancers


class TestCognitiveEnhancersBasic:
    """Test basic cognitive enhancers functionality."""

    def test_implementation_prompt_emits_frameworks(self):
        """Test that implementation prompts emit appropriate frameworks."""
        context = HookContext(
            prompt="Implement a new feature for user authentication",
            data={},  # No unified_detection_result needed
        )

        result = cognitive_enhancers(context)

        # Should emit implementation frameworks
        assert result.context is not None
        assert "[ASUM]" not in result.context
        assert "[ANCH]" not in result.context
        assert "Assumption Surfacing" in result.context
        assert "Outcome Anchoring" in result.context

    def test_diagnostic_prompt_emits_frameworks(self):
        """Test that diagnostic prompts emit appropriate frameworks."""
        context = HookContext(
            prompt="Diagnose why the API is returning 500 errors",
            data={},
        )

        result = cognitive_enhancers(context)

        # Should emit diagnostic frameworks
        assert result.context is not None
        assert "[CAL]" not in result.context
        assert "Calibrated Confidence" in result.context

    def test_decomposition_prompt_emits_socratic(self):
        """Test that long vague prompts trigger Socratic Decomposition."""
        # Use a very long, vague prompt to trigger decomposition
        long_vague_prompt = (
            "I have this very complex and complicated system that I need to understand "
            "and it has many different parts and components and I'm not really sure where to start "
            "or how to approach it and I need help breaking it down into manageable pieces that I can "
            "understand and work with systematically and effectively"
        )

        context = HookContext(
            prompt=long_vague_prompt,
            data={},
        )

        result = cognitive_enhancers(context)

        # Should emit Socratic Decomposition
        assert result.context is not None
        assert "[SOC]" not in result.context
        assert "Socratic Decomposition" in result.context

    def test_empty_result_for_simple_prompt(self):
        """Test that simple prompts return empty result."""
        context = HookContext(
            prompt="hello world",
            data={},
        )

        result = cognitive_enhancers(context)

        # Simple non-actionable prompt should return empty
        assert result.is_empty()
        assert result.context is None

    def test_framework_specific_tags_are_hidden(self):
        """Test that framework names are surfaced without tag tokens."""
        context = HookContext(
            prompt="Implement feature with proper safety checks",
            data={},
        )

        result = cognitive_enhancers(context)

        # Check visible output - should not contain tag tokens
        assert result.context is not None
        assert "[COG]" not in result.context
        assert "[ASUM]" not in result.context
        assert "[ANCH]" not in result.context
        assert "[INV]" not in result.context
        assert "Assumption Surfacing" in result.context or "Outcome Anchoring" in result.context or "Inversion Prompting" in result.context

    def test_multiple_framework_tags_emitted(self):
        """Test that multiple frameworks emit multiple tags."""
        context = HookContext(
            prompt="Design and implement this feature carefully",
            data={},
        )

        result = cognitive_enhancers(context)

        # Should have multiple framework names
        assert result.context is not None
        text = str(result.context) if result.context else ""
        names = [
            "Assumption Surfacing",
            "Outcome Anchoring",
            "Inversion Prompting",
            "Chesterton's Fence",
            "Calibrated Confidence",
            "Named Artifact Discovery",
            "Socratic Decomposition",
            "Cynefin Classification",
            "Hanlon's Razor",
            "Devil's Advocate",
        ]
        matched = [name for name in names if name in text]
        assert len(matched) >= 2, f"Expected at least 2 framework names, got {matched}"
