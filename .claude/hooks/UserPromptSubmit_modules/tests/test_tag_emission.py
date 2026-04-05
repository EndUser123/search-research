"""Test unified tag emission standard for cognitive & reasoning systems.

Tests for tag_emission.py module:
- Tag format validation
- Tag emission functions
- Tag aggregation
- Integration with unified detection results
- Backward compatibility
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent.parent / "UserPromptSubmit_modules"
sys.path.insert(0, str(HOOKS_DIR))

from tag_emission import (
    TAG_2ST,
    TAG_COG,
    TAG_GRA,
    TAG_MAS,
    TAG_PERF,
    TAG_QUESTIONING,
    TAG_SEQ,
    TAG_SYNERGY,
    TAG_THINK,
    Tag,
    TagCollection,
    emit_detection_tags,
    emit_tag,
    emit_tags,
    parse_legacy_tag,
    validate_tag,
)


class TestTagValidation:
    """Verify tag format validation."""

    def test_valid_tag_formats(self):
        """Valid tag formats should pass validation."""
        # Uppercase letters
        assert validate_tag("COG") is True
        assert validate_tag("SEQ") is True
        assert validate_tag("MAS") is True

        # Numbers
        assert validate_tag("2ST") is True
        assert validate_tag("TAG123") is True

        # Underscore
        assert validate_tag("COG_TEST") is True
        assert validate_tag("MY_TAG_123") is True

    def test_invalid_tag_formats(self):
        """Invalid tag formats should fail validation."""
        # Lowercase
        assert validate_tag("cog") is False
        assert validate_tag("Seq") is False

        # Hyphen
        assert validate_tag("COG-TEST") is False

        # Space
        assert validate_tag("COG TEST") is False

        # Special characters
        assert validate_tag("COG.TEST") is False
        assert validate_tag("COG@TEST") is False

        # Empty
        assert validate_tag("") is False


class TestTagDataclass:
    """Verify Tag dataclass behavior."""

    def test_tag_creation_without_content(self):
        """Tag without content should format correctly."""
        tag = Tag(tag_type="COG")
        assert tag.format() == "[COG]"

    def test_tag_creation_with_content(self):
        """Tag with content should format correctly."""
        tag = Tag(tag_type="COG", content="Assumption Surfacing")
        assert tag.format() == "[COG] Assumption Surfacing"

    def test_tag_with_metadata(self):
        """Tag with metadata should store metadata correctly."""
        tag = Tag(tag_type="PERF", content="0.15ms", metadata={"mean": "0.11ms"})
        assert tag.tag_type == "PERF"
        assert tag.content == "0.15ms"
        assert tag.metadata == {"mean": "0.11ms"}
        assert tag.format() == "[PERF] 0.15ms"

    def test_tag_validates_on_creation(self):
        """Tag should validate format on creation."""
        # Valid tag
        Tag(tag_type="COG")  # Should not raise

        # Invalid tag (lowercase)
        with pytest.raises(ValueError, match="Invalid tag type"):
            Tag(tag_type="cog")

        # Invalid tag (hyphen)
        with pytest.raises(ValueError, match="Invalid tag type"):
            Tag(tag_type="COG-TEST")

    def test_tag_is_frozen(self):
        """Tag dataclass should be immutable (frozen=True)."""
        from dataclasses import FrozenInstanceError

        tag = Tag(tag_type="COG")

        with pytest.raises(FrozenInstanceError):  # Frozen dataclass doesn't allow assignment
            tag.tag_type = "SEQ"


class TestTagCollection:
    """Verify TagCollection behavior."""

    def test_empty_collection(self):
        """Empty collection should format to empty string."""
        collection = TagCollection(tags=[])
        assert collection.format() == ""

    def test_single_tag(self):
        """Collection with single tag should format correctly."""
        collection = TagCollection(tags=[Tag(tag_type="COG")])
        assert collection.format() == "[COG]"

    def test_multiple_tags_default_separator(self):
        """Multiple tags should use space separator by default."""
        collection = TagCollection(
            tags=[
                Tag(tag_type="COG", content="Assumption Surfacing"),
                Tag(tag_type="SEQ"),
                Tag(tag_type="THINK", content="debug_rca"),
            ]
        )
        assert collection.format() == "[COG] Assumption Surfacing [SEQ] [THINK] debug_rca"

    def test_multiple_tags_custom_separator(self):
        """Multiple tags should use custom separator when specified."""
        collection = TagCollection(tags=[Tag(tag_type="COG"), Tag(tag_type="SEQ")], separator=" | ")
        assert collection.format() == "[COG] | [SEQ]"

    def test_add_tag(self):
        """add_tag should return new collection with added tag."""
        collection = TagCollection(tags=[Tag(tag_type="COG")])
        new_collection = collection.add_tag(Tag(tag_type="SEQ"))

        # Original unchanged (frozen dataclass)
        assert collection.format() == "[COG]"

        # New collection has both tags
        assert new_collection.format() == "[COG] [SEQ]"

    def test_filter_by_type(self):
        """filter_by_type should return tags of specified type."""
        collection = TagCollection(
            tags=[
                Tag(tag_type="COG", content="A"),
                Tag(tag_type="COG", content="B"),
                Tag(tag_type="SEQ"),
            ]
        )

        cog_tags = collection.filter_by_type("COG")
        assert len(cog_tags) == 2
        assert cog_tags[0].content == "A"
        assert cog_tags[1].content == "B"

        seq_tags = collection.filter_by_type("SEQ")
        assert len(seq_tags) == 1

        # No tags of this type
        perf_tags = collection.filter_by_type("PERF")
        assert len(perf_tags) == 0


class TestEmitTag:
    """Verify emit_tag function."""

    def test_emit_tag_without_content(self):
        """emit_tag without content should return tag only."""
        result = emit_tag("COG")
        assert result == "[COG]"

    def test_emit_tag_with_content(self):
        """emit_tag with content should return tag + content."""
        result = emit_tag("COG", "Assumption Surfacing")
        assert result == "[COG] Assumption Surfacing"

    def test_emit_tag_with_metadata(self):
        """emit_tag with metadata should ignore metadata in formatting."""
        result = emit_tag("PERF", "0.15ms", {"mean": "0.11ms"})
        assert result == "[PERF] 0.15ms"

    def test_emit_tag_invalid_format_raises(self):
        """emit_tag with invalid tag type should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid tag type"):
            emit_tag("cog")  # lowercase

        with pytest.raises(ValueError, match="Invalid tag type"):
            emit_tag("COG-TEST")  # hyphen


class TestEmitTags:
    """Verify emit_tags function."""

    def test_emit_tags_string(self):
        """emit_tags with string should return single tag."""
        result = emit_tags("COG")
        assert result == "[COG]"

    def test_emit_tags_tuple(self):
        """emit_tags with tuple should return tag with content."""
        result = emit_tags(("COG", "Assumption Surfacing"))
        assert result == "[COG] Assumption Surfacing"

    def test_emit_tags_tuple_none_content(self):
        """emit_tags with tuple and None content should return tag only."""
        result = emit_tags(("COG", None))
        assert result == "[COG]"

    def test_emit_tags_list_of_tuples(self):
        """emit_tags with list of tuples should return multiple tags."""
        result = emit_tags(
            [
                ("COG", "Assumption Surfacing"),
                ("SEQ", None),
                ("THINK", "debug_rca"),
            ]
        )
        assert result == "[COG] Assumption Surfacing [SEQ] [THINK] debug_rca"

    def test_emit_tags_list_of_tag_objects(self):
        """emit_tags with list of Tag objects should return multiple tags."""
        result = emit_tags(
            [
                Tag(tag_type="COG", content="Assumption Surfacing"),
                Tag(tag_type="SEQ"),
                Tag(tag_type="THINK", content="debug_rca"),
            ]
        )
        assert result == "[COG] Assumption Surfacing [SEQ] [THINK] debug_rca"

    def test_emit_tags_custom_separator(self):
        """emit_tags should use custom separator when specified."""
        result = emit_tags(
            [
                ("COG", None),
                ("SEQ", None),
            ],
            separator=" | ",
        )
        assert result == "[COG] | [SEQ]"

    def test_emit_tags_invalid_item_type(self):
        """emit_tags with invalid item type should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid tag item"):
            emit_tags([123])  # Invalid item type

    def test_emit_tags_invalid_tag_type(self):
        """emit_tags with invalid tag type in list should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid tag type"):
            emit_tags([("cog", None)])  # lowercase


class TestEmitDetectionTags:
    """Verify emit_detection_tags function (integration with unified_detection)."""

    def test_no_detection_results(self):
        """Empty detection results should return empty string."""
        result = emit_detection_tags()
        assert result == ""

    def test_cognitive_frameworks_only(self):
        """Cognitive frameworks should emit [COG] tag."""
        result = emit_detection_tags(matched_frameworks=["assumption_surfacing"])
        assert "[COG]" in result
        assert "Assumption Surfacing" in result

    def test_multiple_frameworks_formatted(self):
        """Multiple frameworks should be formatted with title case."""
        result = emit_detection_tags(
            matched_frameworks=["assumption_surfacing", "outcome_anchoring"]
        )
        assert "[COG]" in result
        assert "Assumption Surfacing" in result
        assert "Outcome Anchoring" in result

    def test_reasoning_modes(self):
        """Reasoning modes should emit appropriate tags."""
        # Sequential
        result = emit_detection_tags(matched_modes=["sequential"])
        assert "[SEQ]" in result

        # Multi-agent
        result = emit_detection_tags(matched_modes=["multi_agent"])
        assert "[MAS]" in result

        # Graph
        result = emit_detection_tags(matched_modes=["graph"])
        assert "[GRA]" in result

        # Two-stage
        result = emit_detection_tags(matched_modes=["two_stage"])
        assert "[2ST]" in result

    def test_multiple_reasoning_modes(self):
        """Multiple reasoning modes should emit multiple tags."""
        result = emit_detection_tags(matched_modes=["sequential", "multi_agent"])
        assert "[SEQ]" in result
        assert "[MAS]" in result

    def test_think_profiles(self):
        """Think profiles should emit [THINK] tag."""
        result = emit_detection_tags(matched_profiles=["debug_rca"])
        assert "[THINK]" in result
        assert "debug_rca" in result

    def test_multiple_think_profiles(self):
        """Multiple think profiles should be comma-separated."""
        result = emit_detection_tags(matched_profiles=["debug_rca", "tradeoff_decision"])
        assert "[THINK]" in result
        assert "debug_rca" in result
        assert "tradeoff_decision" in result

    def test_synergy_candidates(self):
        """Synergy candidates should emit [SYNERGY] tag."""
        result = emit_detection_tags(synergy_candidates=[("assumption_surfacing", "sequential")])
        assert "[SYNERGY]" in result
        assert "assumption_surfacing+sequential" in result

    def test_synergy_candidates_multiple(self):
        """Multiple synergies should show first 3 + count."""
        result = emit_detection_tags(
            synergy_candidates=[
                ("assumption_surfacing", "sequential"),
                ("socratic_decomposition", "multi_agent"),
                ("outcome_anchoring", "two_stage"),
                ("inversion_prompting", "graph"),
            ]
        )
        assert "[SYNERGY]" in result
        assert "assumption_surfacing+sequential" in result
        assert "socratic_decomposition+multi_agent" in result
        assert "outcome_anchoring+two_stage" in result
        assert "(+1 more)" in result  # 4th synergy

    def test_performance_timing(self):
        """Performance timing should emit [PERF] tag."""
        result = emit_detection_tags(timing_ms=0.15)
        assert "[PERF]" in result
        assert "0.15ms" in result

    def test_performance_timing_formatting(self):
        """Performance timing should be formatted to 2 decimal places."""
        result = emit_detection_tags(timing_ms=0.152345)
        assert "[PERF]" in result
        assert "0.15ms" in result  # Rounded to 2 decimals

    def test_questioning_patterns(self):
        """Questioning patterns should emit [QUESTIONING] tag."""
        result = emit_detection_tags(questioning_patterns=["arbitrary_threshold"])
        assert "[QUESTIONING]" in result
        assert "arbitrary_threshold" in result

    def test_questioning_patterns_multiple(self):
        """Multiple questioning patterns should show first 3 + count."""
        result = emit_detection_tags(
            questioning_patterns=[
                "arbitrary_threshold",
                "shared_state",
                "over_engineering",
                "swiss_cheese",
            ]
        )
        assert "[QUESTIONING]" in result
        assert "arbitrary_threshold" in result
        assert "shared_state" in result
        assert "over_engineering" in result
        assert "(+1 more)" in result  # 4th pattern

    def test_comprehensive_detection(self):
        """Comprehensive detection should emit all tags."""
        result = emit_detection_tags(
            matched_frameworks=["assumption_surfacing"],
            matched_modes=["sequential"],
            matched_profiles=["debug_rca"],
            synergy_candidates=[("assumption_surfacing", "sequential")],
            timing_ms=0.15,
            questioning_patterns=["arbitrary_threshold"],
        )
        # All tags present
        assert "[COG]" in result
        assert "[SEQ]" in result
        assert "[THINK]" in result
        assert "[SYNERGY]" in result
        assert "[PERF]" in result
        assert "[QUESTIONING]" in result
        # Content present
        assert "Assumption Surfacing" in result
        assert "debug_rca" in result
        assert "0.15ms" in result
        assert "arbitrary_threshold" in result


class TestBackwardCompatibility:
    """Verify backward compatibility with legacy tag parsing."""

    def test_parse_legacy_tag_with_content(self):
        """Legacy tag with content should parse correctly."""
        result = parse_legacy_tag("[COG] Assumption Surfacing")
        assert result == ("COG", "Assumption Surfacing")

    def test_parse_legacy_tag_without_content(self):
        """Legacy tag without content should parse correctly."""
        result = parse_legacy_tag("[SEQ]")
        assert result == ("SEQ", None)

    def test_parse_legacy_tag_multiple_words_content(self):
        """Legacy tag with multiple words in content should parse correctly."""
        result = parse_legacy_tag("[COG] Assumption Surfacing, Outcome Anchoring")
        assert result == ("COG", "Assumption Surfacing, Outcome Anchoring")

    def test_parse_legacy_tag_invalid_format(self):
        """Invalid legacy tag format should return None."""
        # Missing brackets
        assert parse_legacy_tag("COG") is None

        # Wrong bracket position
        assert parse_legacy_tag("COG]") is None
        assert parse_legacy_tag("[COG") is None

        # Lowercase tag type (invalid - only uppercase allowed in brackets)
        result = parse_legacy_tag("[cog] test")
        # parse_legacy_tag is a lenient parser, it only parses uppercase tags
        assert result is None  # Lowercase tag_type doesn't match [A-Z0-9_]+ pattern


class TestTagConstants:
    """Verify tag constants are defined correctly."""

    def test_cognitive_framework_tag(self):
        """TAG_COG should be 'COG'."""
        assert TAG_COG == "COG"

    def test_reasoning_mode_tags(self):
        """Reasoning mode tags should be defined."""
        assert TAG_SEQ == "SEQ"
        assert TAG_MAS == "MAS"
        assert TAG_GRA == "GRA"  # Graph mode (was missing)
        assert TAG_2ST == "2ST"

    def test_new_tags(self):
        """New tags should be defined."""
        assert TAG_THINK == "THINK"
        assert TAG_SYNERGY == "SYNERGY"
        assert TAG_PERF == "PERF"
        assert TAG_QUESTIONING == "QUESTIONING"


class TestAcceptanceCriteria:
    """Acceptance tests for T-003 requirements."""

    def test_all_tags_documented_in_docstring(self):
        """All tags should be documented in module docstring."""
        import tag_emission

        docstring = tag_emission.__doc__
        assert docstring is not None
        # Framework-specific cognitive tags (replaced [COG])
        assert "[ASUM]" in docstring  # Assumption Surfacing
        assert "[SOC]" in docstring  # Socratic Decomposition
        assert "[CAL]" in docstring  # Calibrated Confidence
        # Reasoning mode tags
        assert "[SEQ]" in docstring
        assert "[MAS]" in docstring
        # Other tags
        assert "[THINK]" in docstring
        assert "[SYNERGY]" in docstring
        assert "[PERF]" in docstring
        assert "[QUESTIONING]" in docstring

    def test_tag_format_validation_no_spaces(self):
        """Tag format should not allow spaces within brackets."""
        # Valid: No spaces within brackets
        assert validate_tag("ASUM_TEST") is True

        # Invalid: Space within tag type would be caught by regex
        # But we test that formatted tags don't have internal spaces
        tag = Tag(tag_type="ASUM", content="Test Content")
        formatted = tag.format()
        # Spaces only after bracket, not within
        assert formatted == "[ASUM] Test Content"

    def test_tag_format_consistent_casing(self):
        """Tag format should enforce uppercase casing."""
        # Valid: Uppercase
        assert validate_tag("COG") is True
        assert validate_tag("TAG_123") is True

        # Invalid: Lowercase
        assert validate_tag("cog") is False
        assert validate_tag("Tag") is False

        # Invalid: Mixed case
        assert validate_tag("Cog") is False

    def test_backward_compatible_old_tags_still_parse(self):
        """Old tags should still be parseable."""
        # Framework-specific tags (new system)
        result = parse_legacy_tag("[ASUM] Assumption Surfacing")
        assert result is not None
        assert result[0] == "ASUM"

        # [SEQ], [MAS], [2ST] tags (existing)
        for tag in ["[SEQ]", "[MAS]", "[2ST]"]:
            result = parse_legacy_tag(tag)
            assert result is not None
            assert result[0] in ["SEQ", "MAS", "2ST"]

    def test_tag_emission_in_additional_context_format(self):
        """Tags should be formatted for HookResult.additionalContext."""
        # Single tag
        tag = emit_tag("ASUM", "Assumption Surfacing")
        assert tag == "[ASUM] Assumption Surfacing"

        # Multiple tags
        tags = emit_tags(
            [
                ("ASUM", "Assumption Surfacing"),
                ("SEQ", None),
                ("THINK", "debug_rca"),
            ]
        )
        assert "[ASUM] Assumption Surfacing" in tags
        assert "[SEQ]" in tags
        assert "[THINK] debug_rca" in tags
