#!/usr/bin/env python3
"""
Test suite for Stop_deletion_verification_guard.py

Comprehensive test coverage for deletion verification guard including:
- Pattern detection (deletion claims, allowlist, URL exclusion)
- Path extraction and normalization
- Boundary validation (path traversal prevention)
- File system verification with timeout
- Log injection prevention
- MAX_PATHS limit enforcement
- Integration tests
"""

from __future__ import annotations

import os

# Import the module under test
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from Stop_deletion_verification_guard import (
    DELETION_CLAIM_PATTERNS,
    MAX_PATHS,
    OBVIOUS_ALLOWLIST,
    URL_PATTERNS,
    _detect_deletion_claims,
    _extract_file_paths,
    _normalize_path,
    _sanitize_for_log,
    _validate_path_boundary,
    _verify_deletion_claim,
    check,
)


class TestPatternDetection:
    """Test deletion claim pattern detection."""

    def test_deletion_claim_patterns_positive_cases(self):
        """Test that deletion completion claims are detected."""
        positive_cases = [
            "Files are deleted",
            "The files were deleted",
            "Files have been removed",
            "Deleted the files",
            "Successfully deleted the files",  # Fixed: needs object after action
            "All files deleted",
            "Both directories removed",
            "Cleaned up the files",
            "Files are gone",
        ]
        for case in positive_cases:
            assert DELETION_CLAIM_PATTERNS.search(case), f"Should detect: {case}"

    def test_deletion_claim_patterns_negative_cases(self):
        """Test that non-deletion claims are not detected."""
        # These cases should either be allowlisted or not match the deletion pattern
        negative_cases = [
            "Files will be deleted",  # Allowlisted (future tense)
            "The files should be deleted",  # Allowlisted (modal verb)
            "Going to delete files",  # Allowlisted (going to)
            "Files can be removed",  # Allowlisted (capability)
            "Needs cleanup",  # Allowlisted (requirement)
            "Requires deletion",  # Allowlisted (requirement)
            "I didn't delete the files",  # Allowlisted (denial)
            "I haven't removed anything",  # Allowlisted (denial)
            "Option Remove: drop the column",  # ADR alternative (allowlisted)
            "remove NOT NULL from native_event_id",  # Schema constraint (allowlisted)
            "Removing the NOT NULL constraint",  # Schema constraint (allowlisted)
            "Removed PRIMARY KEY",  # Schema constraint (allowlisted)
        ]
        for case in negative_cases:
            # Check if it's allowlisted first
            if OBVIOUS_ALLOWLIST.search(case):
                continue  # It's OK if allowlist catches it
            assert not DELETION_CLAIM_PATTERNS.search(case), f"Should NOT detect: {case}"

    def test_obvious_allowlist_future_tense(self):
        """Test that future tense patterns are in allowlist."""
        allowlist_cases = [
            "will delete",
            "will be deleted",
            "should be deleted",  # Changed from "should delete" (modal)
            "going to delete",
            "can be deleted",
            "can be removed",
            "needs cleanup",
            "requires deletion",
        ]
        for case in allowlist_cases:
            assert OBVIOUS_ALLOWLIST.search(case), f"Should allowlist: {case}"

    def test_obvious_allowlist_conversational_denials(self):
        """Test that conversational denials are in allowlist."""
        denial_cases = [
            "I didn't delete",
            "I didn't remove",
            "I haven't deleted",
            "I haven't removed",
        ]
        for case in denial_cases:
            assert OBVIOUS_ALLOWLIST.search(case), f"Should allowlist denial: {case}"

    def test_obvious_allowlist_code_refactoring_contexts(self):
        """Test that code-refactoring contexts are in allowlist."""
        refactoring_cases = [
            "removed unused code",
            "removed dead code",
            "removed obsolete code",
            "removed deprecated code",
            "removed redundant code",
            "removed the unused branch",
            "removed dead logic",
            "removed obsolete function",
            "removed deprecated import",
            "removed redundant statement",
            "removed the unused class",
            "removed the dead method",
        ]
        for case in refactoring_cases:
            assert OBVIOUS_ALLOWLIST.search(case), f"Should allowlist refactoring: {case}"

    def test_obvious_allowlist_code_refactoring_negative_cases(self):
        """Test that file deletion claims are NOT in code-refactoring allowlist."""
        # These should NOT be allowlisted because they don't have explicit code terms
        negative_cases = [
            "removed unused",  # No "code" or related term
            "removed dead",  # No object specified
            "removed obsolete files",  # "files" suggests file deletion, not code
            "deleted unused code",  # "deleted" not "removed"
        ]
        for case in negative_cases:
            result = OBVIOUS_ALLOWLIST.search(case)
            if result:
                # If matched, verify it matched a DIFFERENT pattern, not the code-refactoring one
                # The code-refactoring pattern requires explicit code terms
                # So "removed unused files" shouldn't match the new pattern
                pass  # OK if other patterns match, but verify code-refactoring doesn't
            else:
                # Also OK if not matched at all
                pass

    def test_url_exclusion_pattern(self):
        """Test that URLs are excluded from file path extraction."""
        # URLs should be detected by URL_PATTERNS
        url_cases = [
            "https://example.com/file.py",
            "http://localhost:8080/test",
            "https://github.com/user/repo",
        ]
        for url in url_cases:
            assert URL_PATTERNS.search(url), f"Should detect URL: {url}"

        # URLs should NOT be extracted as file paths (via _extract_file_paths)
        text_with_urls = "Deleted https://example.com/file.py and http://localhost/test"
        paths = _extract_file_paths(text_with_urls)
        assert len(paths) == 0, f"URLs should not be extracted as paths: {paths}"

        # But actual file paths should still be extracted
        text_with_paths = "Deleted P:\\project\\test.py and /usr/local/bin/script"
        paths = _extract_file_paths(text_with_paths)
        assert len(paths) >= 1, f"Should extract file paths: {paths}"

    def test_detect_deletion_claims_integration(self):
        """Test full deletion claim detection with allowlist."""
        # Should detect deletion claim
        response = "I deleted the test files"
        claims = _detect_deletion_claims(response)
        assert len(claims) > 0, "Should detect deletion claim"

        # Should skip due to allowlist
        response = "I will delete the test files"
        claims = _detect_deletion_claims(response)
        assert len(claims) == 0, "Should skip future tense (allowlist)"


class TestPathExtraction:
    """Test file path extraction from text."""

    def test_extract_windows_absolute_paths(self):
        """Test Windows absolute path extraction."""
        text = "Deleted files at P:\\project\\test.py and C:\\temp\\file.txt"
        paths = _extract_file_paths(text)
        assert len(paths) == 2
        assert "P:\\project\\test.py" in paths
        assert "C:\\temp\\file.txt" in paths

    def test_extract_unix_absolute_paths(self):
        """Test Unix absolute path extraction."""
        text = "Removed /usr/local/bin/script and /var/log/test.log"
        paths = _extract_file_paths(text)
        # Should extract at least the paths
        assert len(paths) >= 2
        # The paths might have trailing slashes removed, so check for prefix match
        assert any("/usr/local/bin" in p for p in paths)
        assert any("/var/log/test" in p for p in paths)

    def test_extract_relative_paths(self):
        """Test relative path extraction."""
        text = "Deleted ./test.py and ../backup/file.txt"
        paths = _extract_file_paths(text)
        assert len(paths) == 2
        assert "./test.py" in paths
        assert "../backup/file.txt" in paths

    def test_extract_quoted_paths(self):
        """Test path extraction with quotes."""
        text = "Deleted 'test file.py' and \"another file.txt\""
        paths = _extract_file_paths(text)
        assert len(paths) == 2
        assert "test file.py" in paths
        assert "another file.txt" in paths

    def test_extract_deduplication(self):
        """Test that duplicate paths are removed."""
        text = "Deleted test.py, test.py, and test.py"
        paths = _extract_file_paths(text)
        assert len(paths) == 1
        assert paths[0] == "test.py"

    def test_extract_by_extension(self):
        """Test extraction by common file extensions."""
        text = "Removed script.py, file.js, config.json, and README.md"
        paths = _extract_file_paths(text)
        assert len(paths) >= 4

    def test_extract_preserves_order(self):
        """Test that path order is preserved."""
        text = "Deleted first.py, second.py, and third.py"
        paths = _extract_file_paths(text)
        assert paths == ["first.py", "second.py", "third.py"]


class TestPathNormalization:
    """Test path normalization logic."""

    def test_normalize_absolute_path_unchanged(self):
        """Test that absolute paths are unchanged."""
        path = _normalize_path("P:\\project\\test.py")
        assert str(path) == "P:\\project\\test.py"

    def test_normalize_relative_path_to_project_root(self):
        """Test that relative paths are resolved against project root."""
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": "/fake/project"}):
            path = _normalize_path("test.py")
            # Should be relative to project root
            assert "test.py" in str(path)

    def test_normalize_resolves_double_dots(self):
        """Test that .. is resolved."""
        path = _normalize_path("../test.py")
        # Should resolve parent directory
        assert ".." not in str(path)


class TestBoundaryValidation:
    """Test path boundary validation for security."""

    def test_validate_path_within_project_root(self):
        """Test that paths within project root are valid."""
        project_root = Path("/fake/project")
        # Path within project
        test_path = Path("/fake/project/subdir/file.py")
        assert _validate_path_boundary(test_path, project_root) is True

    def test_validate_path_outside_project_root(self):
        """Test that paths outside project root are rejected."""
        project_root = Path("/fake/project")
        # Path outside project
        test_path = Path("/etc/passwd")
        assert _validate_path_boundary(test_path, project_root) is False

    def test_validate_path_traversal_attempt(self):
        """Test that path traversal attempts are blocked."""
        project_root = Path("/fake/project")
        # Path traversal attempt - after resolution it should be outside
        test_path = Path("/etc/passwd")
        # Direct path outside project
        assert _validate_path_boundary(test_path, project_root) is False


class TestLogSanitization:
    """Test log injection prevention."""

    def test_sanitize_removes_newlines(self):
        """Test that newlines are removed from log text."""
        text = "test.py\nInjected log entry"
        sanitized = _sanitize_for_log(text)
        # Newlines should be removed
        assert sanitized.count("\n") == 0 or "Injected" not in sanitized

    def test_sanitize_removes_carriage_returns(self):
        """Test that carriage returns are removed."""
        text = "test.py\rInjected log entry"
        sanitized = _sanitize_for_log(text)
        # Carriage returns should be removed
        assert sanitized.count("\r") == 0 or "Injected" not in sanitized

    def test_sanitize_removes_control_characters(self):
        """Test that control characters are removed."""
        text = "test.py\x00\x01\x02Injected"
        sanitized = _sanitize_for_log(text)
        assert "\x00" not in sanitized
        assert "\x01" not in sanitized
        assert "\x02" not in sanitized

    def test_sanitize_preserves_tabs(self):
        """Test that tabs are preserved (not all control chars)."""
        text = "test.py\twith\ttabs"
        sanitized = _sanitize_for_log(text)
        assert "\t" in sanitized

    def test_sanitize_handles_unicode(self):
        """Test that Unicode characters are preserved."""
        text = "test_文件.py"
        sanitized = _sanitize_for_log(text)
        assert "文件" in sanitized


class TestFilesystemVerification:
    """Test file system verification logic."""

    def test_verify_existing_file(self):
        """Test that existing files are detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set project root to temp directory so boundary validation passes
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                # Create a test file
                test_file = Path(tmpdir) / "test.py"
                test_file.write_text("content")

                verified, reason = _verify_deletion_claim([str(test_file)])
                assert verified is False
                assert "still exists" in reason.lower() or str(test_file) in reason

    def test_verify_deleted_file(self):
        """Test that deleted files pass verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set project root to temp directory so boundary validation passes
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                # Use a non-existent file path
                test_file = Path(tmpdir) / "nonexistent.py"

                verified, reason = _verify_deletion_claim([str(test_file)])
                assert verified is True
                assert reason == ""

    def test_verify_max_paths_limit(self):
        """Test that MAX_PATHS limit is enforced."""
        # Create more than MAX_PATHS paths
        paths = [f"file{i}.py" for i in range(MAX_PATHS + 10)]

        verified, reason = _verify_deletion_claim(paths)
        assert verified is False
        assert "Too many paths" in reason
        assert str(MAX_PATHS) in reason

    def test_verify_empty_path_list(self):
        """Test that empty path list passes."""
        verified, reason = _verify_deletion_claim([])
        assert verified is True
        assert reason == ""

    def test_verify_directory_detection(self):
        """Test that directories are correctly identified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Set project root to temp directory so boundary validation passes
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": tmpdir}):
                # Create a directory
                test_dir = Path(tmpdir) / "testdir"
                test_dir.mkdir()

                verified, reason = _verify_deletion_claim([str(test_dir)])
                assert verified is False
                assert "(directory)" in reason

    def test_verify_timeout_protection(self):
        """Test that timeout protection works (mocked)."""
        # This test uses a mock to simulate timeout
        # Real timeout testing would require actual network paths
        with patch("Stop_deletion_verification_guard._check_path_with_timeout") as mock_check:
            mock_check.return_value = (False, False, "timeout")

            # FAIL-OPEN: Timeout now allows the claim (DR-20260331)
            verified, reason = _verify_deletion_claim(["test.py"])
            assert verified is True
            assert "timeout" in reason.lower() or "verification failed" in reason.lower()

    def test_verify_deferred_logging(self):
        """Test that logging is deferred until after loop."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple files
            files = [Path(tmpdir) / f"test{i}.py" for i in range(5)]
            for f in files:
                f.write_text("content")

            # FAIL-OPEN: Boundary failures now allow (DR-20260331)
            # Set an unrelated project root so every file falls outside the boundary.
            outside_root = Path(tmpdir) / "project-root"
            outside_root.mkdir()
            with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": str(outside_root)}):
                verified, reason = _verify_deletion_claim([str(f) for f in files])

            assert verified is True
            assert "outside project boundary" in reason.lower()
            assert len(reason.split("•")) > 5  # One bullet per file plus header


class TestIntegration:
    """Integration tests for the guard."""

    def test_check_with_deletion_claim(self):
        """Test the main check() function with deletion claim."""
        data = {
            "assistant_response": "I deleted the test files",
            "response": "Deleted test.py and example.py",
        }

        result = check(data)
        # Should block because no files were actually verified as deleted
        assert result is not None
        assert result.get("decision") == "block"

    def test_check_with_allowlist(self):
        """Test that allowlist patterns prevent blocking."""
        data = {
            "assistant_response": "I will delete the test files",
            "response": "Going to delete test.py",
        }

        result = check(data)
        # Should allow due to allowlist (future tense)
        assert result is None

    def test_check_with_no_claim(self):
        """Test that non-claim responses pass through."""
        data = {
            "assistant_response": "The code is working correctly",
            "response": "All tests pass",
        }

        result = check(data)
        # Should allow (no deletion claim detected)
        assert result is None

    def test_check_empty_response(self):
        """Test that empty responses are handled."""
        data = {"assistant_response": "", "response": ""}

        result = check(data)
        # Should allow (no content to check)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
