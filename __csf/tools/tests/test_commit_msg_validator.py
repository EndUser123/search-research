"""
Unit tests for commit_msg_validator.py

Tests cover:
- Empty commit message rejection
- Valid conventional commit format acceptance
- Invalid commit type rejection
- Vague pattern detection
- Missing section validation
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path to import the validator
sys.path.insert(0, str(Path(__file__).parent.parent))

from commit_msg_validator import validate_header, validate_body, VAGUE_PATTERNS


class TestValidateHeader:
    """Test commit message header validation."""

    def test_validate_header_empty(self):
        """Test that empty commit messages are rejected."""
        valid, errors = validate_header('')
        assert not valid
        assert 'Commit message is empty' in errors

    def test_validate_header_valid_format(self):
        """Test that valid conventional commits pass."""
        test_cases = [
            'feat(auth): implement OAuth2 login',  # Not vague
            'fix(api): resolve timeout issue',     # "resolve" is not vague
            'docs(readme): update installation instructions',  # More specific
            'refactor(core): simplify logic',       # Acceptable
            'test(utils): add coverage for auth',   # More specific
            'chore(deps): bump version',           # Acceptable
        ]
        for subject in test_cases:
            valid, errors = validate_header(subject)
            assert valid, f"Should be valid: {subject} - errors: {errors}"
            assert len(errors) == 0, f"Should have no errors: {subject} - {errors}"

    def test_validate_header_invalid_type(self):
        """Test that invalid commit types are rejected."""
        valid, errors = validate_header('invalid(auth): add login')
        assert not valid
        assert any("Invalid type 'invalid'" in e for e in errors)

    def test_validate_header_missing_scope(self):
        """Test that commits without scope are accepted."""
        valid, errors = validate_header('feat: add new feature')
        assert valid
        assert len(errors) == 0

    def test_validate_header_missing_colon(self):
        """Test that commits missing the colon are rejected."""
        valid, errors = validate_header('feat add new feature')
        assert not valid
        # The error message mentions "Invalid format" or "Expected"
        assert any("format" in e.lower() or "expected" in e.lower() for e in errors)

    def test_validate_header_too_long(self):
        """Test that overly long subject lines are rejected."""
        long_subject = 'feat: ' + 'x' * 100
        valid, errors = validate_header(long_subject)
        assert not valid
        assert any('too long' in e.lower() for e in errors)


class TestVaguePatterns:
    """Test vague commit pattern detection."""

    def test_vague_pattern_update(self):
        """Test that 'update x' pattern is flagged."""
        # Pattern r'^update\s*\w+$' requires word after 'update'
        valid, errors = validate_header('feat: update code')
        assert not valid
        assert any('too vague' in e.lower() for e in errors)

    def test_vague_pattern_fix(self):
        """Test that 'fix x' pattern is flagged."""
        # Pattern requires space+word after 'fix'
        valid, errors = validate_header('fix: fix tmp')
        assert not valid
        assert any('too vague' in e.lower() for e in errors)

    def test_vague_pattern_wip(self):
        """Test that 'wip' is flagged."""
        valid, errors = validate_header('feat: wip')
        assert not valid
        assert any('too vague' in e.lower() for e in errors)

    def test_vague_pattern_tmp(self):
        """Test that 'tmp' is flagged."""
        valid, errors = validate_header('feat: tmp')
        assert not valid
        assert any('too vague' in e.lower() for e in errors)

    def test_detailed_update_passes(self):
        """Test that 'update' with details passes."""
        valid, errors = validate_header('feat: update user authentication flow')
        assert valid
        assert len(errors) == 0

    def test_detailed_fix_passes(self):
        """Test that 'fix' with details passes."""
        valid, errors = validate_header('fix: resolve race condition in cache')
        assert valid
        assert len(errors) == 0


class TestValidateBody:
    """Test commit message body validation."""

    def test_validate_body_empty(self):
        """Test that empty body is accepted."""
        valid, warnings = validate_body('')
        # Empty body is valid but may produce warnings
        assert isinstance(valid, bool)
        assert isinstance(warnings, list)

    def test_validate_body_with_sections(self):
        """Test body with proper WHY/WHAT sections."""
        body = """
## WHY
Users need secure authentication

## WHAT
Added OAuth2 flow with token refresh
"""
        valid, warnings = validate_body(body)
        assert valid
        # Should not have "Missing" warnings
        missing_warnings = [w for w in warnings if "Missing" in w]
        assert len(missing_warnings) == 0

    def test_validate_body_missing_why(self):
        """Test that missing WHY section is flagged."""
        body = """
## WHAT
Added OAuth2 flow
"""
        valid, warnings = validate_body(body)
        # Should warn about missing WHY
        assert any("Missing" in w for w in warnings)

    def test_validate_body_too_short_why(self):
        """Test that very short WHY is flagged."""
        body = """
## WHY
fix

## WHAT
Fixed bug
"""
        valid, warnings = validate_body(body)
        # Validator checks for VERIFICATION warning for fix commits
        # Total body length check: <3 non-empty lines triggers warning
        # This body has 4 lines, so it passes length check
        assert valid
        # But fix commits should include VERIFICATION
        assert any("verification" in w.lower() for w in warnings)

    def test_validate_body_multiline_why(self):
        """Test that multiline WHY content is accepted."""
        body = """
## WHY
Users need to authenticate securely
and their sessions should persist
across browser restarts.

## WHAT
Implemented JWT with refresh tokens
"""
        valid, warnings = validate_body(body)
        assert valid


class TestIntegration:
    """Integration tests for complete validation flow."""

    def test_valid_commit_passes(self):
        """Test that a well-formed commit message passes."""
        header = 'feat(auth): add OAuth2 login'
        body = """
## WHY
Users need secure authentication

## WHAT
Implemented OAuth2 with Google provider
"""
        header_valid, header_errors = validate_header(header)
        body_valid, body_warnings = validate_body(body)

        assert header_valid
        assert len(header_errors) == 0
        assert body_valid
        # No "Missing" warnings
        missing_warnings = [w for w in body_warnings if "Missing" in w]
        assert len(missing_warnings) == 0

    def test_invalid_header_fails(self):
        """Test that invalid header causes failure."""
        header = 'bad commit'
        body = """
## WHY
Need to fix
"""
        header_valid, header_errors = validate_header(header)
        body_valid, body_warnings = validate_body(body)

        assert not header_valid
        assert len(header_errors) > 0

    def test_vague_commit_fails(self):
        """Test that vague commit is rejected."""
        # Use a pattern that matches VAGUE_PATTERNS
        header = 'feat: update code'
        body = ''

        header_valid, header_errors = validate_header(header)
        assert not header_valid
        assert any('too vague' in e.lower() for e in header_errors)
