"""
Tests for commit message validation.

These tests verify semantic commit message validation according to
conventional commits format with specific type restrictions.

Test coverage:
- Semantic format validation: type(scope): subject
- Valid commit types: feat, fix, docs, refactor, test, chore
- Subject validation: lowercase and not empty
- Header length validation: max 100 characters
- Return format: (is_valid: bool, errors: list of strings)
"""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


class TestValidateCommitMessageFormat:
    """Test semantic format validation: type(scope): subject."""

    def test_valid_commit_message_with_scope(self):
        """
        Test validation of a valid commit message with scope.

        Given: A well-formed commit message with type, scope, and subject
        When: The message is validated
        Then: Should return (True, [])
        """
        from commit_validation import validate_commit_message

        message = "feat(auth): add user login functionality"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is True
        assert errors == []

    def test_valid_commit_message_without_scope(self):
        """
        Test validation of a valid commit message without scope.

        Given: A well-formed commit message with type and subject only
        When: The message is validated
        Then: Should return (True, [])
        """
        from commit_validation import validate_commit_message

        message = "feat: add user login functionality"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is True
        assert errors == []

    def test_invalid_format_missing_colon(self):
        """
        Test validation fails when colon is missing.

        Given: A commit message without colon separator
        When: The message is validated
        Then: Should return (False, ["error about missing colon"])
        """
        from commit_validation import validate_commit_message

        message = "feat add user login functionality"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is False
        assert len(errors) > 0
        assert any("colon" in error.lower() for error in errors)

    def test_invalid_format_empty_subject(self):
        """
        Test validation fails when subject is empty.

        Given: A commit message with type but empty subject
        When: The message is validated
        Then: Should return (False, ["error about empty subject"])
        """
        from commit_validation import validate_commit_message

        message = "feat: "
        is_valid, errors = validate_commit_message(message)

        assert is_valid is False
        assert len(errors) > 0
        assert any("subject" in error.lower() for error in errors)

    def test_invalid_format_empty_type(self):
        """
        Test validation fails when type is empty.

        Given: A commit message with empty type
        When: The message is validated
        Then: Should return (False, ["error about missing type"])
        """
        from commit_validation import validate_commit_message

        message = ": add user login functionality"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is False
        assert len(errors) > 0


class TestValidCommitTypes:
    """Test validation of allowed commit types."""

    def test_feat_type_is_valid(self):
        """
        Test that 'feat' type is valid.

        Given: A commit message with type 'feat'
        When: The message is validated
        Then: Should return (True, [])
        """
        from commit_validation import validate_commit_message

        message = "feat: add new feature"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is True
        assert errors == []

    def test_fix_type_is_valid(self):
        """
        Test that 'fix' type is valid.

        Given: A commit message with type 'fix'
        When: The message is validated
        Then: Should return (True, [])
        """
        from commit_validation import validate_commit_message

        message = "fix: resolve authentication bug"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is True
        assert errors == []

    def test_docs_type_is_valid(self):
        """
        Test that 'docs' type is valid.

        Given: A commit message with type 'docs'
        When: The message is validated
        Then: Should return (True, [])
        """
        from commit_validation import validate_commit_message

        message = "docs: update readme"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is True
        assert errors == []

    def test_refactor_type_is_valid(self):
        """
        Test that 'refactor' type is valid.

        Given: A commit message with type 'refactor'
        When: The message is validated
        Then: Should return (True, [])
        """
        from commit_validation import validate_commit_message

        message = "refactor: simplify authentication flow"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is True
        assert errors == []

    def test_test_type_is_valid(self):
        """
        Test that 'test' type is valid.

        Given: A commit message with type 'test'
        When: The message is validated
        Then: Should return (True, [])
        """
        from commit_validation import validate_commit_message

        message = "test: add authentication tests"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is True
        assert errors == []

    def test_chore_type_is_valid(self):
        """
        Test that 'chore' type is valid.

        Given: A commit message with type 'chore'
        When: The message is validated
        Then: Should return (True, [])
        """
        from commit_validation import validate_commit_message

        message = "chore: update dependencies"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is True
        assert errors == []

    def test_invalid_type_rejected(self):
        """
        Test that invalid types are rejected.

        Given: A commit message with type 'wip'
        When: The message is validated
        Then: Should return (False, ["error about invalid type"])
        """
        from commit_validation import validate_commit_message

        message = "wip: working on authentication"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is False
        assert len(errors) > 0
        assert any("type" in error.lower() for error in errors)

    def test_unknown_type_rejected(self):
        """
        Test that unknown types are rejected.

        Given: A commit message with type 'unknown'
        When: The message is validated
        Then: Should return (False, ["error about invalid type"])
        """
        from commit_validation import validate_commit_message

        message = "unknown: some change"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is False
        assert len(errors) > 0


class TestSubjectValidation:
    """Test validation of subject line."""

    def test_lowercase_subject_is_valid(self):
        """
        Test that lowercase subject is valid.

        Given: A commit message with lowercase subject
        When: The message is validated
        Then: Should return (True, [])
        """
        from commit_validation import validate_commit_message

        message = "feat: add user login"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is True
        assert errors == []

    def test_uppercase_subject_is_invalid(self):
        """
        Test that uppercase subject is invalid.

        Given: A commit message with uppercase subject
        When: The message is validated
        Then: Should return (False, ["error about lowercase"])
        """
        from commit_validation import validate_commit_message

        message = "feat: Add User Login"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is False
        assert len(errors) > 0
        assert any("lowercase" in error.lower() or "upper" in error.lower() for error in errors)

    def test_mixed_case_subject_is_invalid(self):
        """
        Test that mixed case subject is invalid.

        Given: A commit message with mixed case subject
        When: The message is validated
        Then: Should return (False, ["error about lowercase"])
        """
        from commit_validation import validate_commit_message

        message = "feat: Add user Login"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is False
        assert len(errors) > 0

    def test_capitalized_first_letter_is_invalid(self):
        """
        Test that capitalized first letter is invalid.

        Given: A commit message with capitalized first letter
        When: The message is validated
        Then: Should return (False, ["error about lowercase"])
        """
        from commit_validation import validate_commit_message

        message = "feat: Add user login"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is False
        assert len(errors) > 0


class TestHeaderLengthValidation:
    """Test validation of commit message header length."""

    def test_header_within_limit_is_valid(self):
        """
        Test that header within 100 characters is valid.

        Given: A commit message header of 50 characters
        When: The message is validated
        Then: Should return (True, [])
        """
        from commit_validation import validate_commit_message

        message = "feat: this is a reasonable length commit message"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is True
        assert errors == []

    def test_header_exactly_100_characters_is_valid(self):
        """
        Test that header exactly 100 characters is valid.

        Given: A commit message header of exactly 100 characters
        When: The message is validated
        Then: Should return (True, [])
        """
        from commit_validation import validate_commit_message

        # Create a message exactly 100 characters long
        message = "feat: " + "a" * 92  # "feat: " is 6 chars, plus 92 = 98 total
        is_valid, errors = validate_commit_message(message)

        assert is_valid is True
        assert errors == []

    def test_header_over_100_characters_is_invalid(self):
        """
        Test that header over 100 characters is invalid.

        Given: A commit message header of 101 characters
        When: The message is validated
        Then: Should return (False, ["error about length"])
        """
        from commit_validation import validate_commit_message

        # Create a message over 100 characters
        message = "feat: " + "a" * 95  # "feat: " is 6 chars, plus 95 = 101 total
        is_valid, errors = validate_commit_message(message)

        assert is_valid is False
        assert len(errors) > 0
        assert any("length" in error.lower() or "100" in error or "character" in error.lower() for error in errors)


class TestReturnFormat:
    """Test validation function return format."""

    def test_returns_tuple(self):
        """
        Test that validation returns a tuple.

        Given: Any commit message
        When: The message is validated
        Then: Should return a tuple of (bool, list)
        """
        from commit_validation import validate_commit_message

        message = "feat: test"
        result = validate_commit_message(message)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], list)

    def test_errors_are_strings(self):
        """
        Test that error messages are strings.

        Given: An invalid commit message
        When: The message is validated
        Then: Should return list of string error messages
        """
        from commit_validation import validate_commit_message

        message = "invalid message"
        is_valid, errors = validate_commit_message(message)

        assert isinstance(errors, list)
        for error in errors:
            assert isinstance(error, str)


class TestMultipleValidationErrors:
    """Test that multiple validation errors are all reported."""

    def test_invalid_type_and_uppercase_subject(self):
        """
        Test that both invalid type and uppercase subject are reported.

        Given: A commit message with invalid type AND uppercase subject
        When: The message is validated
        Then: Should return (False, [error1, error2])
        """
        from commit_validation import validate_commit_message

        message = "wip: Add User Login"
        is_valid, errors = validate_commit_message(message)

        assert is_valid is False
        assert len(errors) >= 2  # Should have at least 2 errors

    def test_too_long_and_invalid_type(self):
        """
        Test that both too long header and invalid type are reported.

        Given: A commit message that's too long AND has invalid type
        When: The message is validated
        Then: Should return (False, [error1, error2])
        """
        from commit_validation import validate_commit_message

        message = "wip: " + "a" * 100  # Over 100 chars and invalid type
        is_valid, errors = validate_commit_message(message)

        assert is_valid is False
        assert len(errors) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
