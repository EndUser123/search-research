"""
Test EnhancementResult schema in schemas.py.
"""

import pytest
from schemas import EnhancementResult


class TestEnhancementResult:
    def test_required_fields(self):
        result = EnhancementResult(clarified_intent="test intent", missing_details=["detail1"])
        assert result.clarified_intent == "test intent"
        assert result.missing_details == ["detail1"]

    def test_optional_fields_defaults(self):
        result = EnhancementResult(clarified_intent="test", missing_details=[])
        assert result.analysis is None
        assert result.safety_flags == []
        assert result.estimated_tokens == 0

    def test_all_fields_populated(self):
        result = EnhancementResult(
            clarified_intent="delete the database",
            missing_details=["target database name"],
            analysis="high-impact verb without explicit target",
            safety_flags=["high-impact verb: delete database"],
            estimated_tokens=42,
        )
        assert result.clarified_intent == "delete the database"
        assert "target database name" in result.missing_details
        assert "high-impact verb: delete database" in result.safety_flags
        assert result.estimated_tokens == 42

    def test_empty_missing_details_allowed(self):
        result = EnhancementResult(clarified_intent="what is refactoring?", missing_details=[])
        assert result.missing_details == []

    def test_pydantic_field_descriptors(self):
        """Verify Pydantic v2 Field descriptors are applied."""
        result = EnhancementResult(
            clarified_intent="x",
            missing_details=["y"],
            safety_flags=["flag"],
            estimated_tokens=100,
        )
        # All fields should be properly typed and accessible
        assert isinstance(result.clarified_intent, str)
        assert isinstance(result.missing_details, list)
        assert isinstance(result.safety_flags, list)
        assert isinstance(result.estimated_tokens, int)

    def test_model_dump(self):
        """Verify model_dump produces a serializable dict for JSON persistence."""
        result = EnhancementResult(
            clarified_intent="test",
            missing_details=["detail"],
            safety_flags=["flag"],
            estimated_tokens=10,
        )
        dumped = result.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["clarified_intent"] == "test"
        assert dumped["estimated_tokens"] == 10

    def test_model_validate_roundtrip(self):
        """model_dump → model_validate produces an equal EnhancementResult."""
        original = EnhancementResult(
            clarified_intent="delete the database",
            missing_details=["target database name"],
            analysis="high-impact verb without explicit target",
            safety_flags=["high-impact verb: delete database"],
            estimated_tokens=42,
            inferred_subject="the database",
            confidence=0.75,
        )
        roundtripped = EnhancementResult.model_validate(original.model_dump())
        assert roundtripped.clarified_intent == original.clarified_intent
        assert roundtripped.missing_details == original.missing_details
        assert roundtripped.analysis == original.analysis
        assert roundtripped.safety_flags == original.safety_flags
        assert roundtripped.estimated_tokens == original.estimated_tokens
        assert roundtripped.inferred_subject == original.inferred_subject
        assert roundtripped.confidence == original.confidence

    def test_extra_field_ignored_by_default(self):
        """Pydantic V2 in default mode silently ignores extra fields (extra='ignore')."""
        # This documents current Pydantic V2 behaviour: extra fields do not raise.
        # The schema is intentionally permissive; strictness is enforced at the hook layer.
        result = EnhancementResult(
            clarified_intent="x",
            missing_details=[],
            safety_flags=[],
            estimated_tokens=0,
        )
        dumped = result.model_dump()
        dumped["extra_field"] = "ignored"
        # Should not raise — extra fields are ignored by default in Pydantic V2.
        recovered = EnhancementResult.model_validate(dumped)
        assert recovered.clarified_intent == "x"

    def test_confidence_out_of_range_raises(self):
        """Pydantic V2 raises ValidationError on confidence outside [0, 1].

        (Pydantic V2 does NOT silently coerce ge/le violations — it validates
        strictly. This test guards against accidental change to that contract.)
        """
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            EnhancementResult(clarified_intent="x", missing_details=[], confidence=1.5)
        with pytest.raises(ValidationError):
            EnhancementResult(clarified_intent="x", missing_details=[], confidence=-0.5)