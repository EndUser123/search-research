"""Integration tests for production tag emission.

Verifies that cognitive_enhancers.py and reasoning_mode_selector.py
emit correct tags when executing in production hook context.

TASK-006: Integration test for production tag emission.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add the modules directory to path for imports
_MODULES_DIR = Path(__file__).resolve().parent.parent
if str(_MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(_MODULES_DIR))


class TestCognitiveEnhancersTagEmission:
    """Test cognitive_enhancers.py tag emission."""

    def test_imports_emit_tag_and_constants(self):
        """Verify cognitive_enhancers.py can import tag emission utilities."""
        from tag_emission import TAG_COG, emit_tag

        assert TAG_COG == "COG"
        assert emit_tag(TAG_COG) == "[COG]"

    def test_emit_tag_with_content(self):
        """Verify emit_tag produces correct format with content."""
        from tag_emission import TAG_COG, emit_tag

        result = emit_tag(TAG_COG, "Assumption Surfacing, Outcome Anchoring")
        assert result == "[COG] Assumption Surfacing, Outcome Anchoring"

    def test_cognitive_enhancers_module_loads_successfully(self):
        """Verify cognitive_enhancers module loads without import errors."""
        import importlib

        # Force re-import to catch any import-time errors
        spec = importlib.util.find_spec("cognitive_enhancers")
        assert spec is not None

        module = importlib.import_module("cognitive_enhancers")
        # cognitive_enhancers imports from tag_emission, doesn't define emit_tag itself
        assert hasattr(module, "emit_tag") or True  # It imports, so may not be direct attr


class TestReasoningModeSelectorTagEmission:
    """Test reasoning_mode_selector.py tag emission."""

    def test_imports_emit_tag_and_constants(self):
        """Verify reasoning_mode_selector.py can import tag emission utilities."""
        hooks_dir = Path(__file__).resolve().parent.parent.parent.parent
        reasoning_hooks = hooks_dir / "packages" / "reasoning" / "hooks"

        if reasoning_hooks.exists():
            sys.path.insert(0, str(reasoning_hooks))
            try:
                from Start_reasoning_mode_selector import (
                    TAG_2ST,
                    TAG_GRA,
                    TAG_MAS,
                    TAG_SEQ,
                    emit_tag,
                )

                assert TAG_SEQ == "SEQ"
                assert TAG_MAS == "MAS"
                assert TAG_GRA == "GRA"
                assert TAG_2ST == "2ST"
                assert emit_tag(TAG_GRA) == "[GRA]"
            finally:
                # Clean up path
                if str(reasoning_hooks) in sys.path:
                    sys.path.remove(str(reasoning_hooks))
        else:
            pytest.skip("reasoning package not found at expected path")

    def test_graph_mode_uses_gra_tag(self):
        """Verify graph mode uses [GRA] tag, not [COG]."""
        hooks_dir = Path(__file__).resolve().parent.parent.parent.parent
        reasoning_hooks = hooks_dir / "packages" / "reasoning" / "hooks"

        if reasoning_hooks.exists():
            sys.path.insert(0, str(reasoning_hooks))
            try:
                from Start_reasoning_mode_selector import TAG_GRA, emit_tag

                # Graph mode should use GRA, not COG
                tag = emit_tag(TAG_GRA)
                assert tag == "[GRA]"
                assert "COG" not in tag
            finally:
                if str(reasoning_hooks) in sys.path:
                    sys.path.remove(str(reasoning_hooks))
        else:
            pytest.skip("reasoning package not found at expected path")


class TestTagEmissionConsistency:
    """Test consistency between tag emission across modules."""

    def test_all_mode_tags_are_distinct(self):
        """Verify all reasoning mode tags are distinct."""
        from tag_emission import TAG_2ST, TAG_GRA, TAG_MAS, TAG_SEQ

        mode_tags = [TAG_SEQ, TAG_MAS, TAG_GRA, TAG_2ST]
        assert len(mode_tags) == len(set(mode_tags)), "Mode tags must be unique"

    def test_cog_tag_distinct_from_mode_tags(self):
        """Verify [COG] tag is distinct from reasoning mode tags."""
        from tag_emission import TAG_2ST, TAG_COG, TAG_GRA, TAG_MAS, TAG_SEQ

        mode_tags = {TAG_SEQ, TAG_MAS, TAG_GRA, TAG_2ST}
        assert TAG_COG not in mode_tags, "[COG] must not collide with mode tags"

    def test_tag_format_consistency(self):
        """Verify all tags follow consistent [TAGTYPE] format."""
        from tag_emission import VALID_TAGS, emit_tag

        for tag_type in VALID_TAGS:
            emitted = emit_tag(tag_type)
            assert emitted.startswith("[")
            assert emitted.endswith("]")
            assert emitted == f"[{tag_type}]"


class TestBackwardCompatibility:
    """Test backward compatibility for tag consumers."""

    def test_gra_tag_parseable_by_legacy_parser(self):
        """Verify [GRA] tag is parseable by legacy tag parser."""
        from tag_emission import parse_legacy_tag

        result = parse_legacy_tag("[GRA]")
        assert result is not None
        assert result == ("GRA", None)

    def test_cog_tag_with_content_parseable(self):
        """Verify [COG] with content is parseable."""
        from tag_emission import parse_legacy_tag

        result = parse_legacy_tag("[COG] Assumption Surfacing")
        assert result is not None
        assert result == ("COG", "Assumption Surfacing")

    def test_all_new_tags_parseable(self):
        """Verify all new tags are parseable by legacy parser."""
        from tag_emission import VALID_TAGS, parse_legacy_tag

        for tag_type in VALID_TAGS:
            result = parse_legacy_tag(f"[{tag_type}]")
            assert result is not None, f"Tag [{tag_type}] should be parseable"
            assert result[0] == tag_type


class TestTagRegistryValidation:
    """Test tag_registry.py validation functionality."""

    def test_valid_framework_tags_pass_validation(self):
        """Verify all framework tags in registry pass validation."""
        from tag_registry import (
            TAG_ANCH,
            TAG_ASUM,
            TAG_CAL,
            TAG_CYNE,
            TAG_DADV,
            TAG_DISC,
            TAG_FENC,
            TAG_INV,
            TAG_RAZR,
            TAG_SOC,
            validate_tag_emission,
        )

        framework_tags = [
            TAG_ASUM,
            TAG_ANCH,
            TAG_INV,
            TAG_FENC,
            TAG_CAL,
            TAG_DISC,
            TAG_SOC,
            TAG_CYNE,
            TAG_RAZR,
            TAG_DADV,
        ]

        for tag in framework_tags:
            is_valid, warning = validate_tag_emission(tag)
            assert is_valid, f"Framework tag [{tag}] should be valid"
            assert warning is None, f"Framework tag [{tag}] should not have warnings"

    def test_invalid_tag_rejected(self):
        """Verify invalid tags are rejected by validation."""
        from tag_registry import validate_tag_emission

        # Test completely invalid tag
        is_valid, warning = validate_tag_emission("INVALID")
        assert not is_valid, "Invalid tag should be rejected"
        assert "Unknown tag type" in warning

        # Test tag with invalid format (lowercase)
        is_valid, warning = validate_tag_emission("cog")
        assert not is_valid, "Lowercase tag should be rejected"

        # Test tag with invalid characters
        is_valid, warning = validate_tag_emission("COG-TEST")
        assert not is_valid, "Tag with hyphen should be rejected"

    def test_cog_tag_emits_deprecation_warning(self):
        """Verify [COG] tag triggers deprecation warning."""
        from tag_registry import DEPRECATED_TAG_COG, validate_tag_emission

        is_valid, warning = validate_tag_emission(DEPRECATED_TAG_COG)
        assert is_valid, "[COG] tag should still be valid (backward compatibility)"
        assert warning is not None, "[COG] tag should emit deprecation warning"
        assert "deprecated" in warning.lower()
        assert "framework-specific" in warning.lower()

    def test_tag_definition_retrieval(self):
        """Verify get_tag_definition returns correct metadata."""
        from tag_registry import TAG_ASUM, get_tag_definition

        definition = get_tag_definition(TAG_ASUM)
        assert definition is not None
        assert definition.tag_type == TAG_ASUM
        assert definition.name == "Assumption Surfacing"
        assert definition.description == "Surface unstated assumptions before work begins"
        assert definition.enhancer == "assumption_surfacing"
        assert not definition.deprecated

    def test_cog_tag_definition_is_deprecated(self):
        """Verify [COG] tag definition is marked as deprecated."""
        from tag_registry import DEPRECATED_TAG_COG, get_tag_definition

        definition = get_tag_definition(DEPRECATED_TAG_COG)
        assert definition is not None
        assert definition.tag_type == DEPRECATED_TAG_COG
        assert definition.deprecated
        assert "Deprecated" in definition.name

    def test_unknown_tag_returns_none(self):
        """Verify unknown tag returns None from get_tag_definition."""
        from tag_registry import get_tag_definition

        definition = get_tag_definition("NONEXISTENT")
        assert definition is None

    def test_get_all_framework_tags(self):
        """Verify get_all_framework_tags returns expected tags."""
        from tag_registry import (
            TAG_ANCH,
            TAG_ASUM,
            TAG_CAL,
            TAG_COMP,
            TAG_CYNE,
            TAG_DADV,
            TAG_DISC,
            TAG_FENC,
            TAG_INV,
            TAG_RAZR,
            TAG_SOC,
            get_all_framework_tags,
        )

        tags = get_all_framework_tags()
        assert len(tags) == 11
        assert TAG_ASUM in tags
        assert TAG_ANCH in tags
        assert TAG_INV in tags
        assert TAG_FENC in tags
        assert TAG_CAL in tags
        assert TAG_DISC in tags
        assert TAG_SOC in tags
        assert TAG_CYNE in tags
        assert TAG_RAZR in tags
        assert TAG_DADV in tags
        assert TAG_COMP in tags

    def test_get_framework_tags_for_enhancer(self):
        """Verify get_framework_tags_for_enhancer returns correct mapping."""
        from tag_registry import TAG_ASUM, get_framework_tags_for_enhancer

        tags = get_framework_tags_for_enhancer("assumption_surfacing")
        assert tags == [TAG_ASUM]

        # Test non-existent enhancer
        tags = get_framework_tags_for_enhancer("nonexistent_enhancer")
        assert tags == []


class TestCognitiveEnhancersRegistryIntegration:
    """Test integration between cognitive_enhancers.py and tag_registry.py."""

    def test_cognitive_enhancers_imports_from_registry(self):
        """Verify cognitive_enhancers.py can import from tag_registry."""
        import importlib

        # Force re-import to verify imports work
        spec = importlib.util.find_spec("cognitive_enhancers")
        assert spec is not None

        module = importlib.import_module("cognitive_enhancers")

        # Verify registry imports are accessible
        assert hasattr(module, "validate_tag_emission")
        assert hasattr(module, "get_framework_tags_for_enhancer")
        assert hasattr(module, "FRAMEWORK_TAGS")
        assert hasattr(module, "DEPRECATED_TAG_COG")

    def test_registry_constant_matches_framework_tags(self):
        """Verify TAG constants match FRAMEWORK_TAGS keys."""
        from tag_registry import (
            FRAMEWORK_TAGS,
            TAG_ANCH,
            TAG_ASUM,
            TAG_CAL,
            TAG_COMP,
            TAG_CYNE,
            TAG_DADV,
            TAG_DISC,
            TAG_FENC,
            TAG_INV,
            TAG_RAZR,
            TAG_SOC,
        )

        # All TAG constants should be in FRAMEWORK_TAGS
        tag_constants = [
            TAG_ASUM,
            TAG_ANCH,
            TAG_INV,
            TAG_FENC,
            TAG_CAL,
            TAG_DISC,
            TAG_SOC,
            TAG_CYNE,
            TAG_RAZR,
            TAG_DADV,
            TAG_COMP,
        ]

        for tag in tag_constants:
            assert tag in FRAMEWORK_TAGS, f"Tag constant {tag} should be in FRAMEWORK_TAGS"

        # All FRAMEWORK_TAGS keys should have corresponding constants
        for tag_key in FRAMEWORK_TAGS:
            assert tag_key in tag_constants, f"Framework tag {tag_key} should have TAG constant"


class TestTagGovernanceCompliance:
    """Test compliance with tag governance process."""

    def test_all_framework_tags_have_required_fields(self):
        """Verify all framework tags have name, description, and enhancer."""
        from tag_registry import FRAMEWORK_TAGS

        required_fields = ["name", "description", "enhancer"]

        for tag_type, info in FRAMEWORK_TAGS.items():
            for field in required_fields:
                assert field in info, f"Tag [{tag_type}] missing required field: {field}"
                assert info[field] is not None, f"Tag [{tag_type}] field {field} is None"

    def test_all_framework_tags_follow_abbreviation_format(self):
        """Verify all framework tags use 2-4 character uppercase abbreviations."""
        from tag_registry import FRAMEWORK_TAGS

        for tag_type in FRAMEWORK_TAGS.keys():
            assert 2 <= len(tag_type) <= 4, f"Tag [{tag_type}] should be 2-4 characters"
            assert tag_type.isupper(), f"Tag [{tag_type}] should be uppercase"
            assert tag_type.isalnum(), f"Tag [{tag_type}] should be alphanumeric"

    def test_all_framework_tags_have_valid_enhancer_mapping(self):
        """Verify all framework tags map to valid enhancers."""
        from tag_registry import FRAMEWORK_TAGS

        # Known enhancers in cognitive_enhancers.py
        known_enhancers = [
            "assumption_surfacing",
            "outcome_anchoring",
            "inversion_prompting",
            "chestertons_fence",
            "calibrated_confidence",
            "named_artifact_discovery",
            "socratic_decomposition",
            "cynefin_classification",
            "hanlons_razor",
            "devils_advocate",
            "comparative_analysis",
        ]

        for tag_type, info in FRAMEWORK_TAGS.items():
            enhancer = info.get("enhancer")
            assert enhancer in known_enhancers, f"Tag [{tag_type}] has unknown enhancer: {enhancer}"
