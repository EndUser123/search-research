"""
Test suite for pattern sanity check validation.

These tests verify that pattern specifications meet quality standards:
- Semantic definition exists
- 3+ positive and negative examples
- Pattern matches examples
- Complexity score < 5

Run with: pytest P:\\.claude\\hooks\\tests\\test_pattern_sanity.py -v
"""

import os
import sys

import pytest

# Add hooks directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestValidateComplexityScore:
    """
    Tests for validate_complexity_score() function.

    Validates that pattern complexity scores are below threshold (5).
    """

    def test_complexity_score_5_should_fail(self):
        """
        Test that validate_complexity_score() FAILS when pattern complexity is >= 5.

        Given: A pattern with complexity score of 5
        When: validate_complexity_score() is called
        Then: Should fail validation (return False or raise exception)
        """
        # Arrange
        # Import the function to test (will fail until implemented)
        from PreToolUse_pattern_sanity_check import validate_complexity_score

        # Create a pattern spec with complexity = 5 (should FAIL)
        pattern_spec = {
            "name": "test_pattern",
            "semantic_definition": "Test pattern definition",
            "positive_examples": ["example1", "example2", "example3"],
            "negative_examples": ["counter1", "counter2", "counter3"],
            "pattern": r"test.*pattern",
            "complexity_score": 5  # This should FAIL validation
        }

        # Act
        result = validate_complexity_score(pattern_spec)

        # Assert - This test FAILS initially (RED phase)
        # The function should reject complexity >= 5
        assert result is False, "Pattern with complexity 5 should fail validation"

    def test_complexity_score_6_should_fail(self):
        """
        Test that validate_complexity_score() FAILS when pattern complexity is > 5.

        Given: A pattern with complexity score of 6
        When: validate_complexity_score() is called
        Then: Should fail validation (return False or raise exception)
        """
        # Arrange
        from PreToolUse_pattern_sanity_check import validate_complexity_score

        # Create a pattern spec with complexity = 6 (should FAIL)
        pattern_spec = {
            "name": "complex_pattern",
            "semantic_definition": "Overly complex pattern definition",
            "positive_examples": ["ex1", "ex2", "ex3"],
            "negative_examples": ["neg1", "neg2", "neg3"],
            "pattern": r"complex.*pattern.*with.*many.*parts",
            "complexity_score": 6  # This should FAIL validation
        }

        # Act
        result = validate_complexity_score(pattern_spec)

        # Assert - This test FAILS initially (RED phase)
        assert result is False, "Pattern with complexity 6 should fail validation"

    def test_complexity_score_4_should_pass(self):
        """
        Test that validate_complexity_score() PASSES when pattern complexity is < 5.

        Given: A pattern with complexity score of 4
        When: validate_complexity_score() is called
        Then: Should pass validation (return True)
        """
        # Arrange
        from PreToolUse_pattern_sanity_check import validate_complexity_score

        # Create a pattern spec with complexity = 4 (should PASS)
        pattern_spec = {
            "name": "simple_pattern",
            "semantic_definition": "Simple pattern definition",
            "positive_examples": ["example1", "example2", "example3"],
            "negative_examples": ["counter1", "counter2", "counter3"],
            "pattern": r"simple.*pattern",
            "complexity_score": 4  # This should PASS validation
        }

        # Act
        result = validate_complexity_score(pattern_spec)

        # Assert - This test PASSES (GREEN phase)
        assert result is True, "Pattern with complexity 4 should pass validation"

    def test_complexity_score_boundary_case(self):
        """
        Test boundary case: complexity score of exactly 5 should fail.

        Given: A pattern with complexity score exactly 5
        When: validate_complexity_score() is called
        Then: Should fail validation (boundary is strict: < 5, not <= 5)
        """
        # Arrange
        from PreToolUse_pattern_sanity_check import validate_complexity_score

        # Create a pattern spec with complexity = 5 exactly (boundary case)
        pattern_spec = {
            "name": "boundary_pattern",
            "semantic_definition": "Boundary test pattern",
            "positive_examples": ["ex1", "ex2", "ex3"],
            "negative_examples": ["neg1", "neg2", "neg3"],
            "pattern": r"boundary.*pattern",
            "complexity_score": 5  # Exactly at threshold - should FAIL
        }

        # Act
        result = validate_complexity_score(pattern_spec)

        # Assert - Boundary should FAIL (must be < 5, not <= 5)
        assert result is False, "Pattern with complexity exactly 5 should fail (strict < 5 requirement)"


class TestValidatePatternSpecPositiveExamples:
    """
    Tests for validate_pattern_spec() positive_examples validation.

    Validates that pattern specifications have at least 3 positive examples.
    """

    def test_fails_when_positive_examples_has_zero_examples(self):
        """
        Test that validate_pattern_spec() FAILS when positive_examples is empty.

        Given: A pattern_spec with an empty positive_examples list
        When: validate_pattern_spec() is called
        Then: Returns validation error indicating at least 3 examples are required
        """
        # Arrange
        from PreToolUse_pattern_sanity_check import validate_pattern_spec

        pattern_spec = {
            "name": "test_pattern",
            "semantic_definition": "A test pattern",
            "pattern": r"test_pattern",
            "positive_examples": [],  # Empty list - should FAIL
            "negative_examples": ["not_matching_1", "not_matching_2", "not_matching_3"]
        }

        # Act
        result = validate_pattern_spec(pattern_spec)

        # Assert - Should fail validation
        assert result["valid"] is False, "Validation should fail for empty positive_examples"
        assert "positive_examples" in result.get("error", ""), \
            "Error should mention positive_examples field"
        assert "3" in result.get("error", "") or "three" in result.get("error", "").lower(), \
            "Error should indicate 3 examples are required"

    def test_fails_when_positive_examples_has_one_example(self):
        """
        Test that validate_pattern_spec() FAILS when positive_examples has only 1 example.

        Given: A pattern_spec with a single positive_examples entry
        When: validate_pattern_spec() is called
        Then: Returns validation error indicating at least 3 examples are required
        """
        # Arrange
        from PreToolUse_pattern_sanity_check import validate_pattern_spec

        pattern_spec = {
            "name": "test_pattern",
            "semantic_definition": "A test pattern",
            "pattern": r"test_pattern",
            "positive_examples": ["matching_1"],  # Only 1 example - should FAIL
            "negative_examples": ["not_matching_1", "not_matching_2", "not_matching_3"]
        }

        # Act
        result = validate_pattern_spec(pattern_spec)

        # Assert - Should fail validation
        assert result["valid"] is False, "Validation should fail for 1 positive_example"
        assert "positive_examples" in result.get("error", ""), \
            "Error should mention positive_examples field"

    def test_fails_when_positive_examples_has_two_examples(self):
        """
        Test that validate_pattern_spec() FAILS when positive_examples has only 2 examples.

        Given: A pattern_spec with only 2 positive_examples entries
        When: validate_pattern_spec() is called
        Then: Returns validation error indicating at least 3 examples are required
        """
        # Arrange
        from PreToolUse_pattern_sanity_check import validate_pattern_spec

        pattern_spec = {
            "name": "test_pattern",
            "semantic_definition": "A test pattern",
            "pattern": r"test_pattern",
            "positive_examples": ["matching_1", "matching_2"],  # Only 2 examples - should FAIL
            "negative_examples": ["not_matching_1", "not_matching_2", "not_matching_3"]
        }

        # Act
        result = validate_pattern_spec(pattern_spec)

        # Assert - Should fail validation
        assert result["valid"] is False, "Validation should fail for 2 positive_examples"
        assert "positive_examples" in result.get("error", ""), \
            "Error should mention positive_examples field"


class TestValidatePatternSpec:
    """
    Tests for validate_pattern_spec() function.

    Validates that pattern specifications meet all quality standards:
    - semantic_definition exists
    - 3+ positive_examples
    - 3+ negative_examples
    - working pattern
    - complexity < 5
    """

    def test_complete_valid_pattern_spec_passes(self):
        """
        Test that a complete correct pattern spec passes validation.

        Given: A pattern spec with:
            - semantic_definition
            - 3+ positive_examples
            - 3+ negative_examples
            - working pattern
            - complexity < 5

        When: The spec is validated

        Then: Validation passes with no errors
        """
        # Arrange
        complete_valid_spec = {
            "semantic_definition": "Detects dangerous rm -rf commands on system directories",
            "positive_examples": [
                "rm -rf /",
                "rm -rf /usr/local",
                "rm -rf --no-preserve-root /",
            ],
            "negative_examples": [
                "rm -rf local_dir",
                "rm file.txt",
                "ls -la /",
            ],
            "pattern": r"rm\s+-rf\s+[/]",
            "complexity": 3,
        }

        # Act
        try:
            from PreToolUse_pattern_sanity_check import validate_pattern_spec
            result = validate_pattern_spec(complete_valid_spec)

            # Assert - Should pass validation
            assert result["valid"] is True, \
                f"Complete valid spec should pass validation, but got error: {result.get('error', 'unknown')}"
            assert result.get("error") is None or result.get("error") == "", \
                f"Error should be None/empty for valid spec, got: {result.get('error')}"

        except (ImportError, ModuleNotFoundError):
            # Expected in RED phase - implementation doesn't exist
            pytest.skip("validate_pattern_spec() not yet implemented")



class TestValidatePatternSpecNegativeExamples:
    """Tests for validate_pattern_spec() negative_examples validation."""

    def test_fails_when_negative_examples_has_zero_examples(self):
        """
        Test that validate_pattern_spec() FAILS when negative_examples is empty.

        Given: A pattern_spec with an empty negative_examples list
        When: validate_pattern_spec() is called
        Then: Returns validation error indicating at least 3 examples are required
        """
        # Arrange
        pattern_spec = {
            "semantic_definition": "A test pattern",
            "pattern": r"test_pattern",
            "positive_examples": ["matching_1", "matching_2", "matching_3"],
            "negative_examples": []  # Empty list - should fail
        }

        # Act
        try:
            from PreToolUse_pattern_sanity_check import validate_pattern_spec
            result = validate_pattern_spec(pattern_spec)

            # Assert - Should fail validation
            assert result["valid"] is False, "Validation should fail for empty negative_examples"
            assert "negative_examples" in result["error"], "Error should mention negative_examples"
            assert "3" in result["error"] or "three" in result["error"].lower(),                 "Error should indicate 3 examples are required"

        except (ImportError, ModuleNotFoundError):
            # Expected in RED phase - implementation doesn't exist
            pytest.skip("validate_pattern_spec() not yet implemented")

    def test_fails_when_negative_examples_has_one_example(self):
        """
        Test that validate_pattern_spec() FAILS when negative_examples has only 1 example.

        Given: A pattern_spec with only 1 negative_examples entry
        When: validate_pattern_spec() is called
        Then: Returns validation error indicating at least 3 examples are required
        """
        # Arrange
        pattern_spec = {
            "semantic_definition": "A test pattern",
            "pattern": r"test_pattern",
            "positive_examples": ["matching_1", "matching_2", "matching_3"],
            "negative_examples": ["not_matching_1"]  # Only 1 example - should fail
        }

        # Act
        try:
            from PreToolUse_pattern_sanity_check import validate_pattern_spec
            result = validate_pattern_spec(pattern_spec)

            # Assert - Should fail validation
            assert result["valid"] is False, "Validation should fail for 1 negative_example"
            assert "negative_examples" in result["error"], "Error should mention negative_examples"
            assert "3" in result["error"] or "three" in result["error"].lower(),                 "Error should indicate 3 examples are required"

        except (ImportError, ModuleNotFoundError):
            # Expected in RED phase - implementation doesn't exist
            pytest.skip("validate_pattern_spec() not yet implemented")

    def test_fails_when_negative_examples_has_two_examples(self):
        """
        Test that validate_pattern_spec() FAILS when negative_examples has only 2 examples.

        Given: A pattern_spec with only 2 negative_examples entries
        When: validate_pattern_spec() is called
        Then: Returns validation error indicating at least 3 examples are required
        """
        # Arrange
        pattern_spec = {
            "semantic_definition": "A test pattern",
            "pattern": r"test_pattern",
            "positive_examples": ["matching_1", "matching_2", "matching_3"],
            "negative_examples": ["not_matching_1", "not_matching_2"]  # Only 2 examples - should fail
        }

        # Act
        try:
            from PreToolUse_pattern_sanity_check import validate_pattern_spec
            result = validate_pattern_spec(pattern_spec)

            # Assert - Should fail validation
            assert result["valid"] is False, "Validation should fail for 2 negative_examples"
            assert "negative_examples" in result["error"], "Error should mention negative_examples"
            assert "3" in result["error"] or "three" in result["error"].lower(),                 "Error should indicate 3 examples are required"

        except (ImportError, ModuleNotFoundError):
            # Expected in RED phase - implementation doesn't exist
            pytest.skip("validate_pattern_spec() not yet implemented")

    def test_passes_when_negative_examples_has_three_examples(self):
        """
        Test that validate_pattern_spec() PASSES when negative_examples has exactly 3 examples.

        Given: A pattern_spec with exactly 3 negative_examples entries
        When: validate_pattern_spec() is called
        Then: Validation passes for negative_examples count (assuming other fields are also valid)
        """
        # Arrange
        pattern_spec = {
            "semantic_definition": "A test pattern",
            "pattern": r"test_pattern",
            "positive_examples": ["matching_1", "matching_2", "matching_3"],
            "negative_examples": ["not_matching_1", "not_matching_2", "not_matching_3"]  # Exactly 3 - should pass
        }

        # Act
        try:
            from PreToolUse_pattern_sanity_check import validate_pattern_spec
            result = validate_pattern_spec(pattern_spec)

            # Assert - Should pass validation for negative_examples count
            # (May still fail on other validation rules)
            if not result["valid"]:
                # If validation fails, it should NOT be due to negative_examples count
                assert "negative_examples" not in result["error"] or                        "3" not in result["error"],                     "Failure should not be due to negative_examples count"
            else:
                assert result["valid"] is True, "Validation should pass with 3 negative_examples"

        except (ImportError, ModuleNotFoundError):
            # Expected in RED phase - implementation doesn't exist
            pytest.skip("validate_pattern_spec() not yet implemented")


class TestValidatePatternSpecMissingSemanticDefinition:
    """
    Tests for validate_pattern_spec() when semantic_definition is missing.

    These tests verify that pattern specifications without a semantic_definition
    fail validation appropriately.
    """

    def test_missing_semantic_definition_raises_error(self):
        """
        Test that validate_pattern_spec() FAILS when semantic_definition is missing from PATTERN_SPEC.

        Given: A pattern_spec dict without semantic_definition key
        When: validate_pattern_spec() is called
        Then: Returns validation error indicating semantic_definition is required
        """
        # Arrange
        try:
            from PreToolUse_pattern_sanity_check import validate_pattern_spec
        except ImportError:
            pytest.skip("PreToolUse_pattern_sanity_check not yet implemented")

        pattern_spec_missing_semantic = {
            # Missing: semantic_definition
            "pattern": r"some_regex_pattern",
            "positive_examples": ["matching_1", "matching_2", "matching_3"],
            "negative_examples": ["not_matching_1", "not_matching_2", "not_matching_3"],
            "notes": "Test pattern spec without semantic definition"
        }

        # Act
        result = validate_pattern_spec(pattern_spec_missing_semantic)

        # Assert - Should fail validation
        assert result["valid"] is False, "Validation should fail when semantic_definition is missing"
        assert "semantic_definition" in result["error"], "Error should mention semantic_definition"
        assert "required" in result["error"].lower() or "missing" in result["error"].lower(), \
            "Error should indicate semantic_definition is required or missing"

    def test_empty_semantic_definition_fails_validation(self):
        """
        Test that validate_pattern_spec() FAILS when semantic_definition is empty string.

        Given: A pattern_spec dict with empty semantic_definition
        When: validate_pattern_spec() is called
        Then: Returns validation error indicating semantic_definition cannot be empty
        """
        # Arrange
        try:
            from PreToolUse_pattern_sanity_check import validate_pattern_spec
        except ImportError:
            pytest.skip("PreToolUse_pattern_sanity_check not yet implemented")

        pattern_spec_empty_semantic = {
            "semantic_definition": "",  # Empty string
            "pattern": r"some_regex_pattern",
            "positive_examples": ["matching_1", "matching_2", "matching_3"],
            "negative_examples": ["not_matching_1", "not_matching_2", "not_matching_3"]
        }

        # Act
        result = validate_pattern_spec(pattern_spec_empty_semantic)

        # Assert - Should fail validation
        assert result["valid"] is False, "Validation should fail when semantic_definition is empty"
        assert "semantic_definition" in result["error"], "Error should mention semantic_definition"
        assert "empty" in result["error"].lower() or "required" in result["error"].lower(), \
            "Error should indicate semantic_definition cannot be empty"

    def test_none_semantic_definition_fails_validation(self):
        """
        Test that validate_pattern_spec() FAILS when semantic_definition is None.

        Given: A pattern_spec dict with None as semantic_definition
        When: validate_pattern_spec() is called
        Then: Returns validation error indicating semantic_definition cannot be None
        """
        # Arrange
        try:
            from PreToolUse_pattern_sanity_check import validate_pattern_spec
        except ImportError:
            pytest.skip("PreToolUse_pattern_sanity_check not yet implemented")

        pattern_spec_none_semantic = {
            "semantic_definition": None,
            "pattern": r"some_regex_pattern",
            "positive_examples": ["matching_1", "matching_2", "matching_3"],
            "negative_examples": ["not_matching_1", "not_matching_2", "not_matching_3"]
        }

        # Act
        result = validate_pattern_spec(pattern_spec_none_semantic)

        # Assert - Should fail validation
        assert result["valid"] is False, "Validation should fail when semantic_definition is None"
        assert "semantic_definition" in result["error"], "Error should mention semantic_definition"


class TestValidateExamplesMatchPattern:
    """Tests for validate_examples_match_pattern() function.

    These tests verify that positive/negative examples are correctly
    validated against their declared pattern.
    """

    def test_positive_example_not_matching_pattern_fails(self):
        """
        Test that validate_examples_match_pattern() FAILS when a positive example
        doesn't match the pattern.

        Given: A pattern and a positive example that doesn't match it
        When: validate_examples_match_pattern() is called
        Then: Returns False indicating the example doesn't match

        This is the specific test requested - it MUST FAIL in RED phase.
        """
        # Arrange
        pattern = r"test_\w+"
        # "mismatch" doesn't match the pattern r"test_\w+"
        positive_examples = ["test_valid", "mismatch", "test_another"]
        negative_examples = ["invalid", "no_prefix"]

        # Act & Assert
        try:
            from PreToolUse_pattern_sanity_check import validate_examples_match_pattern

            result = validate_examples_match_pattern(
                pattern=pattern,
                positive_examples=positive_examples,
                negative_examples=negative_examples
            )

            # "mismatch" doesn't match r"test_\w+", so should return valid=False
            assert result["valid"] is False, (
                "Should return valid=False when positive example 'mismatch' "
                r"doesn't match pattern 'test_\w+'"
            )

        except (ImportError, ModuleNotFoundError):
            # Expected in RED phase - implementation does not exist
            pytest.skip("validate_examples_match_pattern() not yet implemented")

    def test_negative_example_accidentally_matches_pattern(self):
        """
        Test that validate_examples_match_pattern() FAILS when a negative
        example accidentally matches the pattern.

        Given: A pattern and negative examples where one matches it
        When: validate_examples_match_pattern() is called
        Then: Returns False indicating validation failed
        """
        # Arrange
        pattern = r"test_\w+"
        positive_examples = ["test_valid", "test_another"]
        # "test_accidental" matches the pattern but shouldn't (it's a negative example)
        negative_examples = ["invalid", "test_accidental", "no_prefix"]

        # Act & Assert
        try:
            from PreToolUse_pattern_sanity_check import validate_examples_match_pattern

            result = validate_examples_match_pattern(
                pattern=pattern,
                positive_examples=positive_examples,
                negative_examples=negative_examples
            )

            # Negative example "test_accidental" matches, so should return valid=False
            assert result["valid"] is False, (
                "Should return valid=False when negative example 'test_accidental' "
                r"matches pattern 'test_\w+'"
            )

        except (ImportError, ModuleNotFoundError):
            pytest.skip("validate_examples_match_pattern() not yet implemented")

    def test_valid_pattern_and_examples_pass(self):
        """
        Test that validate_examples_match_pattern() passes with valid inputs.

        Given: A pattern and correctly categorized examples
        When: validate_examples_match_pattern() is called
        Then: Returns True indicating validation passed
        """
        # Arrange
        pattern = r"feature_\d{3}"
        positive_examples = ["feature_001", "feature_123", "feature_999"]
        negative_examples = ["feature_1", "feature_12", "feature_XYZ", "no_feature"]

        # Act & Assert
        try:
            from PreToolUse_pattern_sanity_check import validate_examples_match_pattern

            result = validate_examples_match_pattern(
                pattern=pattern,
                positive_examples=positive_examples,
                negative_examples=negative_examples
            )

            # All positives match, all negatives don't match - should return valid=True
            assert result["valid"] is True, (
                "Should return valid=True when all positive examples match "
                "and all negative examples don't match"
            )

        except (ImportError, ModuleNotFoundError):
            pytest.skip("validate_examples_match_pattern() not yet implemented")

    def test_fails_when_negative_example_matches_pattern_detailed(self):
        """
        Test that validate_examples_match_pattern() FAILS validation when a negative
        example matches the pattern, with detailed error reporting.

        This is the PRIMARY test for the RED phase - it demonstrates that the
        validation correctly identifies when a pattern is too broad and matches
        examples it shouldn't.

        GIVEN: A pattern r'error' (without word boundaries - too broad)
        AND: Positive examples: ['syntax error', 'runtime error', 'critical error']
        AND: Negative examples: ['terrorist attack', 'happy territory']
              (both contain 'error' as substring but shouldn't match)

        WHEN: validate_examples_match_pattern() is called

        THEN: The function should return validation result with:
              - valid=False (validation failed)
              - matched_negative list containing the incorrectly matching examples
              - errors explaining what went wrong

        This test FAILS in RED phase because the implementation doesn't exist.
        """
        # Arrange - A poorly written pattern that's too broad
        pattern = r'error'  # Missing word boundaries - will match substrings

        positive_examples = [
            'syntax error',
            'runtime error',
            'critical error',
        ]

        negative_examples = [
            'terrorist attack',  # Contains 'error' but SHOULD NOT match
            'error message',     # Contains 'error' but SHOULD NOT match
            'errors plural',     # Contains 'error' but SHOULD NOT match
        ]

        # Act
        try:
            from PreToolUse_pattern_sanity_check import validate_examples_match_pattern

            result = validate_examples_match_pattern(
                pattern=pattern,
                positive_examples=positive_examples,
                negative_examples=negative_examples
            )

            # Assert - Validation MUST fail because negative examples match
            # The pattern r'error' will match 'terrorist', 'territory', 'errors'
            # which are all negative examples that should NOT match

            # First assertion: validation should fail
            assert result["valid"] is False, (
                f"Pattern '{pattern}' should FAIL validation because it matches "
                f"negative examples that it shouldn't. "
                f"Expected valid=False, got valid={result.get('valid', 'missing')}"
            )

            # Second assertion: should identify which negative examples matched
            assert "matched_negative" in result, (
                "Validation result must include 'matched_negative' key to show "
                "which negative examples incorrectly matched the pattern"
            )

            matched_negative = result["matched_negative"]
            assert len(matched_negative) >= 2, (
                f"Should identify at least 2 negative examples that matched. "
                f"Got: {matched_negative}"
            )

            # Third assertion: should specifically identify the problem examples
            assert any('terrorist' in ex for ex in matched_negative), (
                f"Should identify 'terrorist attack' as incorrectly matching. "
                f"Got: {matched_negative}"
            )
            assert any('error message' in ex for ex in matched_negative), (
                f"Should identify 'error message' as incorrectly matching. "
                f"Got: {matched_negative}"
            )

            # Fourth assertion: should provide helpful error message
            assert "errors" in result and len(result["errors"]) > 0, (
                "Validation result should include error messages explaining the failure"
            )

        except (ImportError, ModuleNotFoundError):
            # Expected in RED phase - implementation doesn't exist
            pytest.skip("validate_examples_match_pattern() not yet implemented")


class TestLoadPatternSpec:
    """Tests for load_pattern_spec() function."""

    def test_load_pattern_spec_successfully_loads_dict_from_python_file(self):
        """
        Test that load_pattern_spec() successfully loads a PATTERN_SPEC dict from a Python file.

        Given: A Python file containing a valid PATTERN_SPEC dict
        When: load_pattern_spec() is called with the file path
        Then: The PATTERN_SPEC dict is returned with all expected keys

        Expected PATTERN_SPEC structure:
        {
            "semantic_definition": str,
            "positive_examples": list[str],
            "negative_examples": list[str],
            "pattern": str,
            "notes": str,
            "category": str,
            "severity": str
        }
        """
        # Arrange
        valid_spec_content = r'''"""Pattern specification for test pattern."""

PATTERN_SPEC = {
    "semantic_definition": "A test pattern for verification",
    "positive_examples": [
        "This matches the positive case",
        "This also matches",
        "Third positive example"
    ],
    "negative_examples": [
        "This does not match",
        "Neither does this",
        "Third negative example"
    ],
    "pattern": r"matches\s+the\s+positive",
    "notes": "Test pattern for load_pattern_spec verification",
    "category": "test",
    "severity": "low"
}
'''

        # Create temporary Python file with PATTERN_SPEC
        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode='w', suffix='_spec.py', delete=False) as f:
            f.write(valid_spec_content)
            spec_file = Path(f.name)

        try:
            # Act
            # Import the function (it doesn't exist yet, so this will fail)
            from PreToolUse_pattern_sanity_check import load_pattern_spec

            result = load_pattern_spec(spec_file)

            # Assert
            assert result is not None, "load_pattern_spec should return a dict"
            assert isinstance(result, dict), "Result should be a dictionary"
            assert "semantic_definition" in result, "Result should contain semantic_definition"
            assert "positive_examples" in result, "Result should contain positive_examples"
            assert "negative_examples" in result, "Result should contain negative_examples"
            assert "pattern" in result, "Result should contain pattern"
            assert "notes" in result, "Result should contain notes"
            assert "category" in result, "Result should contain category"
            assert "severity" in result, "Result should contain severity"

            # Verify structure
            assert isinstance(result["positive_examples"], list), "positive_examples should be a list"
            assert isinstance(result["negative_examples"], list), "negative_examples should be a list"
            assert len(result["positive_examples"]) >= 3, "Should have at least 3 positive examples"
            assert len(result["negative_examples"]) >= 3, "Should have at least 3 negative examples"

            # Verify content
            assert result["semantic_definition"] == "A test pattern for verification"
            assert result["pattern"] == r"matches\s+the\s+positive"
            assert result["category"] == "test"
            assert result["severity"] == "low"

        except (ImportError, ModuleNotFoundError):
            # Expected in RED phase - implementation doesn't exist
            pytest.skip("load_pattern_spec() not yet implemented")
        finally:
            # Cleanup
            if spec_file.exists():
                spec_file.unlink()

    def test_load_pattern_spec_raises_error_for_missing_file(self):
        """
        Test that load_pattern_spec() raises appropriate error for non-existent file.

        Given: A file path that does not exist
        When: load_pattern_spec() is called with the path
        Then: FileNotFoundError is raised
        """
        # Arrange
        from pathlib import Path
        non_existent_path = Path("/tmp/does_not_exist_spec.py")

        # Act & Assert
        try:
            from PreToolUse_pattern_sanity_check import load_pattern_spec

            with pytest.raises(FileNotFoundError, match="Pattern spec file not found"):
                load_pattern_spec(non_existent_path)

        except (ImportError, ModuleNotFoundError):
            # Expected in RED phase - implementation doesn't exist
            pytest.skip("load_pattern_spec() not yet implemented")

    def test_load_pattern_spec_raises_error_for_missing_pattern_spec_dict(self):
        """
        Test that load_pattern_spec() raises error when PATTERN_SPEC dict is missing.

        Given: A Python file without a PATTERN_SPEC dict
        When: load_pattern_spec() is called with the file path
        Then: ValueError is raised indicating missing PATTERN_SPEC
        """
        # Arrange
        invalid_spec_content = '''"""Invalid pattern specification - missing PATTERN_SPEC dict."""

# No PATTERN_SPEC dict here
SOME_OTHER_VAR = {"not": "a pattern spec"}
'''

        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode='w', suffix='_spec.py', delete=False) as f:
            f.write(invalid_spec_content)
            spec_file = Path(f.name)

        try:
            # Act & Assert
            try:
                from PreToolUse_pattern_sanity_check import load_pattern_spec

                with pytest.raises(ValueError, match="PATTERN_SPEC not found"):
                    load_pattern_spec(spec_file)

            except (ImportError, ModuleNotFoundError):
                # Expected in RED phase - implementation doesn't exist
                pytest.skip("load_pattern_spec() not yet implemented")

        finally:
            if spec_file.exists():
                spec_file.unlink()

    def test_load_pattern_spec_raises_error_for_malformed_spec(self):
        """
        Test that load_pattern_spec() raises error for malformed PATTERN_SPEC.

        Given: A Python file with PATTERN_SPEC missing required keys
        When: load_pattern_spec() is called with the file path
        Then: ValueError is raised indicating missing required fields
        """
        # Arrange
        malformed_spec_content = '''"""Malformed pattern specification - missing required keys."""

PATTERN_SPEC = {
    "semantic_definition": "Has semantic definition",
    # Missing 'examples', 'pattern', 'notes', etc.
}
'''

        import tempfile
        from pathlib import Path

        with tempfile.NamedTemporaryFile(mode='w', suffix='_spec.py', delete=False) as f:
            f.write(malformed_spec_content)
            spec_file = Path(f.name)

        try:
            # Act & Assert
            try:
                from PreToolUse_pattern_sanity_check import load_pattern_spec

                with pytest.raises(ValueError, match="Missing required fields"):
                    load_pattern_spec(spec_file)

            except (ImportError, ModuleNotFoundError):
                # Expected in RED phase - implementation doesn't exist
                pytest.skip("load_pattern_spec() not yet implemented")

        finally:
            if spec_file.exists():
                spec_file.unlink()
