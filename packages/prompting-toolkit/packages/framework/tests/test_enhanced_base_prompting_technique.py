#!/usr/bin/env python3
"""
Unit tests for enhanced_base_prompting_technique module.

Tests for enhanced base prompting technique with extended capabilities.
"""


from prompting_framework.enhanced_base_prompting_technique import (
    EnhancedCapability,
    EnhancedPromptingTechnique,
    TechniqueEnhancement,
)


class TestEnhancedCapability:
    """Test EnhancedCapability enum."""

    def test_all_capabilities_defined(self):
        """Verify all expected capabilities are defined."""
        expected_capabilities = [
            "multi_modal",
            "tool_use",
            "code_execution",
            "external_api",
            "memory_management",
            "context_tracking",
        ]
        actual_values = [c.value for c in EnhancedCapability]
        for expected in expected_capabilities:
            assert expected in actual_values


class TestTechniqueEnhancement:
    """Test TechniqueEnhancement dataclass."""

    def test_create_enhancement(self):
        """Create a technique enhancement."""
        enhancement = TechniqueEnhancement(
            enhancement_type=EnhancedCapability.TOOL_USE,
            description="Ability to use external tools",
            enabled=True,
            configuration={
                "allowed_tools": ["calculator", "search"],
                "max_tool_calls": 5,
            },
        )
        assert enhancement.enhancement_type == EnhancedCapability.TOOL_USE
        assert enhancement.enabled is True

    def test_enhancement_disabled(self):
        """Create disabled enhancement."""
        enhancement = TechniqueEnhancement(
            enhancement_type=EnhancedCapability.CODE_EXECUTION,
            description="Code execution capability",
            enabled=False,
            configuration={},
        )
        assert enhancement.enabled is False


class TestEnhancedPromptingTechnique:
    """Test EnhancedPromptingTechnique class."""

    def test_create_enhanced_technique(self):
        """Create enhanced prompting technique."""
        technique = EnhancedPromptingTechnique(
            technique_name="enhanced_cot",
            base_technique="chain_of_thought",
            capabilities=[
                EnhancedCapability.TOOL_USE,
                EnhancedCapability.MEMORY_MANAGEMENT,
            ],
        )
        assert technique.technique_name == "enhanced_cot"
        assert len(technique.capabilities) == 2

    def test_has_capability_true(self):
        """Check if technique has capability."""
        technique = EnhancedPromptingTechnique(
            technique_name="multi_modal",
            base_technique="zero_shot",
            capabilities=[EnhancedCapability.MULTI_MODAL],
        )
        assert technique.has_capability(EnhancedCapability.MULTI_MODAL)

    def test_has_capability_false(self):
        """Check if technique lacks capability."""
        technique = EnhancedPromptingTechnique(
            technique_name="basic",
            base_technique="zero_shot",
            capabilities=[],
        )
        assert not technique.has_capability(EnhancedCapability.CODE_EXECUTION)

    def test_enable_capability(self):
        """Enable a capability for technique."""
        technique = EnhancedPromptingTechnique(
            technique_name="extensible",
            base_technique="few_shot",
            capabilities=[],
        )
        technique.enable_capability(EnhancedCapability.CONTEXT_TRACKING)
        assert technique.has_capability(EnhancedCapability.CONTEXT_TRACKING)

    def test_disable_capability(self):
        """Disable a capability for technique."""
        technique = EnhancedPromptingTechnique(
            technique_name="reducible",
            base_technique="self_refine",
            capabilities=[EnhancedCapability.MEMORY_MANAGEMENT],
        )
        technique.disable_capability(EnhancedCapability.MEMORY_MANAGEMENT)
        assert not technique.has_capability(EnhancedCapability.MEMORY_MANAGEMENT)
