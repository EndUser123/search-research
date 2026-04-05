#!/usr/bin/env python3
"""
Tests for Simplified Edit Verification (Reflexion Verifier)

Tests the simplified security-only verification:
- old_string removal check (security)
- Skip verification for non-code files
- Edge cases (empty strings)
"""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from posttooluse.reflexion_verifier import ReflexionVerifier


class TestSimplifiedEditVerification:
    """Test simplified Edit verification with security-only check."""

    def test_old_string_not_removed_fails_verification(self):
        """
        old_string check should remain exact match (security).
        Even if old_string has escape sequences, it must be fully removed.
        """
        hook = ReflexionVerifier()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_file = f.name
            # File still has old_string
            f.write('def hello():\n    pass\n')

        try:
            tool_input = {
                "file_path": test_file,
                "old_string": 'def hello():\n    pass\n',
                "new_string": 'def hello():\n    print("world")\n'
            }

            actual_content = Path(test_file).read_text()
            result = hook._verify_edit_operation(test_file, tool_input, actual_content)

            # Should FAIL - old_string still present (security check)
            assert result is not None
            assert result["type"] == "EDIT_VERIFICATION_FAILED"
            assert "old_string still present" in result["message"]
            assert result["severity"] == "HIGH"

        finally:
            Path(test_file).unlink()

    def test_empty_strings_skip_verification(self):
        """
        Empty old_string or new_string should skip verification.
        """
        hook = ReflexionVerifier()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            test_file = f.name
            f.write('def hello():\n    pass\n')

        try:
            # Empty old_string
            tool_input = {
                "file_path": test_file,
                "old_string": "",
                "new_string": 'def hello():\n    print("world")\n'
            }

            actual_content = Path(test_file).read_text()
            result = hook._verify_edit_operation(test_file, tool_input, actual_content)

            # Should skip (return None)
            assert result is None

        finally:
            Path(test_file).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
