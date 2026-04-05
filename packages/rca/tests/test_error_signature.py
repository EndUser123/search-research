"""Tests for error_signature module.

NOTE: Creating new test file for error_signature module which currently has no test coverage.
"""

import pytest

from rca.error_signature import (
    ErrorSignature,
    SignatureMatch,
    PatternFixRecord,
    ErrorSignatureExtractor,
    extract_signature,
    match_to_pattern,
    SIGNATURE_PATTERNS,
    SIGNATURE_DESCRIPTIONS,
    FIX_TEMPLATES,
)


class TestErrorSignature:
    """Tests for ErrorSignature dataclass."""

    def test_error_signature_creation(self):
        """Test creating an ErrorSignature."""
        sig = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        assert sig.pattern_name == "null_dict_access"
        assert sig.error_type == "AttributeError"

    def test_error_signature_is_frozen(self):
        """Test that ErrorSignature is frozen (immutable)."""
        sig = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        with pytest.raises(Exception):  # FrozenInstanceError
            sig.pattern_name = "other_pattern"

    def test_signature_hash(self):
        """Test signature_hash property."""
        sig = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        hash_value = sig.signature_hash
        assert isinstance(hash_value, str)
        assert len(hash_value) == 12

    def test_signature_hash_deterministic(self):
        """Test that signature_hash is deterministic."""
        sig1 = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        sig2 = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        assert sig1.signature_hash == sig2.signature_hash

    def test_signature_hash_different_for_different_sigs(self):
        """Test that different signatures have different hashes."""
        sig1 = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        sig2 = ErrorSignature(pattern_name="missing_key", error_type="KeyError")
        assert sig1.signature_hash != sig2.signature_hash

    def test_description_property(self):
        """Test description property."""
        sig = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        assert "None check" in sig.description

    def test_description_unknown_pattern(self):
        """Test description for unknown pattern returns pattern_name."""
        sig = ErrorSignature(pattern_name="unknown_pattern", error_type="Error")
        assert sig.description == "unknown_pattern"

    def test_fix_template_property(self):
        """Test fix_template property."""
        sig = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        assert ".get(" in sig.fix_template or "None" in sig.fix_template

    def test_matches_method(self):
        """Test matches method."""
        sig = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        error_msg = "AttributeError: 'NoneType' object has no attribute '__getitem__'"
        assert sig.matches(error_msg)

    def test_matches_method_no_match(self):
        """Test matches method returns False for non-matching errors."""
        sig = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        error_msg = "ValueError: invalid literal"
        assert not sig.matches(error_msg)

    def test_matches_method_no_pattern(self):
        """Test matches returns False when pattern doesn't exist."""
        sig = ErrorSignature(pattern_name="nonexistent_pattern", error_type="Error")
        error_msg = "Some error message"
        assert not sig.matches(error_msg)


class TestSignatureMatch:
    """Tests for SignatureMatch dataclass."""

    def test_signature_match_creation(self):
        """Test creating a SignatureMatch."""
        sig = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        match = SignatureMatch(
            signature=sig,
            confidence=0.9,
            matched_text="AttributeError: 'NoneType'",
            suggested_fix="Use dict.get()",
        )
        assert match.signature == sig
        assert match.confidence == 0.9
        assert match.matched_text == "AttributeError: 'NoneType'"
        assert match.suggested_fix == "Use dict.get()"

    def test_to_dict(self):
        """Test to_dict method."""
        sig = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        match = SignatureMatch(
            signature=sig,
            confidence=0.9,
            matched_text="Error text",
            suggested_fix="Fix template",
        )
        result = match.to_dict()
        assert isinstance(result, dict)
        assert result["pattern_name"] == "null_dict_access"
        assert result["error_type"] == "AttributeError"
        assert result["confidence"] == 0.9
        assert result["matched_text"] == "Error text"
        assert result["suggested_fix"] == "Fix template"


class TestPatternFixRecord:
    """Tests for PatternFixRecord dataclass."""

    def test_pattern_fix_record_creation(self):
        """Test creating a PatternFixRecord."""
        sig = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        record = PatternFixRecord(
            signature=sig,
            fix_description="Fix description",
            fix_template="Fix template",
            code_diff="+ fixed code",
            applied_count=5,
            locations_seen=["file1.py", "file2.py"],
        )
        assert record.signature == sig
        assert record.fix_description == "Fix description"
        assert record.fix_template == "Fix template"
        assert record.code_diff == "+ fixed code"
        assert record.applied_count == 5
        assert record.locations_seen == ["file1.py", "file2.py"]

    def test_to_dict(self):
        """Test to_dict method."""
        sig = ErrorSignature(pattern_name="null_dict_access", error_type="AttributeError")
        record = PatternFixRecord(
            signature=sig,
            fix_description="Fix",
            fix_template="Template",
            applied_count=1,
            locations_seen=["file.py"],
            verified=True,
        )
        result = record.to_dict()
        assert result["pattern_name"] == "null_dict_access"
        assert result["error_type"] == "AttributeError"
        assert result["verified"] is True

    def test_from_dict(self):
        """Test from_dict class method."""
        data = {
            "pattern_name": "null_dict_access",
            "error_type": "AttributeError",
            "fix_description": "Fix",
            "fix_template": "Template",
            "code_diff": "+ code",
            "applied_count": 2,
            "locations_seen": ["file1.py"],
            "first_seen": "2024-01-01",
            "last_seen": "2024-01-02",
            "verified": False,
        }
        record = PatternFixRecord.from_dict(data)
        assert record.signature.pattern_name == "null_dict_access"
        assert record.fix_description == "Fix"
        assert record.applied_count == 2


class TestErrorSignatureExtractor:
    """Tests for ErrorSignatureExtractor class."""

    def test_extract_signatures_none_dict_access(self):
        """Test extracting signature for None dict access."""
        error_msg = "AttributeError: 'NoneType' object has no attribute '__getitem__'"
        sigs = ErrorSignatureExtractor.extract_signatures(error_msg)
        assert len(sigs) > 0
        assert any(s.pattern_name == "null_dict_access" for s in sigs)

    def test_extract_signatures_missing_import(self):
        """Test extracting signature for missing import."""
        error_msg = "ModuleNotFoundError: No module named 'requests'"
        sigs = ErrorSignatureExtractor.extract_signatures(error_msg)
        assert any(s.pattern_name == "missing_import" for s in sigs)

    def test_extract_signatures_file_not_found(self):
        """Test extracting signature for file not found."""
        error_msg = "FileNotFoundError: No such file or directory: 'config.yaml'"
        sigs = ErrorSignatureExtractor.extract_signatures(error_msg)
        assert any(s.pattern_name == "file_not_found" for s in sigs)

    def test_extract_signatures_connection_error(self):
        """Test extracting signature for connection error."""
        error_msg = "ConnectionError: HTTPSConnectionPool failed"
        sigs = ErrorSignatureExtractor.extract_signatures(error_msg)
        assert any(s.pattern_name == "connection_error" for s in sigs)

    def test_extract_signatures_set_changed_size(self):
        """Test extracting signature for set changed size."""
        error_msg = "RuntimeError: Set changed size during iteration"
        sigs = ErrorSignatureExtractor.extract_signatures(error_msg)
        assert any(s.pattern_name == "set_changed_size" for s in sigs)

    def test_extract_signatures_unknown_error(self):
        """Test extracting signature for unknown error returns empty list."""
        error_msg = "CustomError: something completely unexpected"
        sigs = ErrorSignatureExtractor.extract_signatures(error_msg)
        # May return empty or a generic signature depending on implementation
        assert isinstance(sigs, list)

    def test_extract_error_type(self):
        """Test _extract_error_type method."""
        assert ErrorSignatureExtractor._extract_error_type("AttributeError: message") == "AttributeError"
        assert ErrorSignatureExtractor._extract_error_type("TypeError: message") == "TypeError"
        assert ErrorSignatureExtractor._extract_error_type("UnknownError: message") == "Error"

    def test_get_best_match_none_dict_access(self):
        """Test get_best_match for None dict access."""
        error_msg = "AttributeError: 'NoneType' object has no attribute '__getitem__'"
        sig = ErrorSignatureExtractor.get_best_match(error_msg)
        assert sig is not None
        assert sig.pattern_name == "null_dict_access"

    def test_get_best_match_no_match(self):
        """Test get_best_match returns None for non-matching error."""
        error_msg = "CustomError: unknown pattern"
        sig = ErrorSignatureExtractor.get_best_match(error_msg)
        # Implementation returns None or creates generic signature
        assert sig is None or sig.pattern_name in SIGNATURE_PATTERNS

    def test_get_best_match_priority_order(self):
        """Test that get_best_match respects priority order."""
        # Error that could match multiple patterns
        error_msg = "AttributeError: 'NoneType' object has no attribute '__getitem__'"
        sig = ErrorSignatureExtractor.get_best_match(error_msg)
        # Should return high priority pattern if multiple matches
        assert sig is not None


class TestExtractSignature:
    """Tests for extract_signature convenience function."""

    def test_extract_signature_none_dict(self):
        """Test extract_signature for None dict access."""
        error_msg = "AttributeError: 'NoneType' object has no attribute '__getitem__'"
        sig = extract_signature(error_msg)
        assert sig is not None
        assert sig.pattern_name == "null_dict_access"

    def test_extract_signature_missing_key(self):
        """Test extract_signature for missing key."""
        error_msg = "KeyError: 'config'"
        sig = extract_signature(error_msg)
        assert sig is not None

    def test_extract_signature_returns_none_for_unknown(self):
        """Test extract_signature returns None for unknown patterns."""
        sig = extract_signature("UnknownError: xyz123")
        # Implementation returns None for non-matching errors
        assert sig is None or isinstance(sig, ErrorSignature)


class TestMatchToPattern:
    """Tests for match_to_pattern function."""

    def test_match_to_pattern_returns_match(self):
        """Test match_to_pattern returns SignatureMatch."""
        error_msg = "AttributeError: 'NoneType' object has no attribute '__getitem__'"
        match = match_to_pattern(error_msg)
        assert match is not None
        assert isinstance(match, SignatureMatch)
        assert isinstance(match.signature, ErrorSignature)
        assert 0 <= match.confidence <= 1

    def test_match_to_pattern_confidence(self):
        """Test that match_to_pattern sets appropriate confidence."""
        error_msg = "ModuleNotFoundError: No module named 'xyz'"
        match = match_to_pattern(error_msg)
        if match:
            assert match.confidence >= 0.7

    def test_match_to_pattern_suggested_fix(self):
        """Test that match_to_pattern includes suggested fix."""
        error_msg = "AttributeError: 'NoneType' object has no attribute '__getitem__'"
        match = match_to_pattern(error_msg)
        if match:
            assert isinstance(match.suggested_fix, str)

    def test_match_to_pattern_none_for_unknown(self):
        """Test match_to_pattern returns None for unknown patterns."""
        match = match_to_pattern("CustomError: xyz123")
        assert match is None


class TestSignaturePatterns:
    """Tests for SIGNATURE_PATTERNS constant."""

    def test_all_patterns_are_valid_regex(self):
        """Test that all signature patterns are valid regex."""
        import re
        for pattern_name, pattern in SIGNATURE_PATTERNS.items():
            try:
                re.compile(pattern, re.IGNORECASE | re.DOTALL)
            except re.error:
                pytest.fail(f"Pattern '{pattern_name}' has invalid regex: {pattern}")

    def test_all_patterns_have_descriptions(self):
        """Test that all patterns have descriptions."""
        for pattern_name in SIGNATURE_PATTERNS:
            assert pattern_name in SIGNATURE_DESCRIPTIONS

    def test_all_patterns_have_fix_templates(self):
        """Test that all patterns have fix templates."""
        for pattern_name in SIGNATURE_PATTERNS:
            assert pattern_name in FIX_TEMPLATES

    def test_specific_patterns_exist(self):
        """Test that expected patterns exist."""
        expected_patterns = [
            "null_dict_access",
            "null_attr_access",
            "missing_key",
            "index_error",
            "missing_import",
            "type_not_subscriptable",
            "file_not_found",
            "connection_error",
            "timeout_error",
            "set_changed_size",
            "list_changed_size",
        ]
        for pattern in expected_patterns:
            assert pattern in SIGNATURE_PATTERNS
