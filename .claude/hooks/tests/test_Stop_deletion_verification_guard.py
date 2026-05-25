#!/usr/bin/env python3
"""Tests for Stop_deletion_verification_guard.py."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

# Load directly from the cc-aca-epistemic plugin (not the delegation wrapper)
_PLUGIN_HOOK = Path("P:/packages/cc-aca-epistemic/hooks/stop/Stop_deletion_verification_guard.py")
_spec = importlib.util.spec_from_file_location("Stop_deletion_verification_guard", _PLUGIN_HOOK)
_mod = importlib.util.module_from_spec(_spec)
# Plugin bootstrap needs __lib on sys.path
_lib = Path("P:/packages/cc-aca-epistemic/__lib")
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
_spec.loader.exec_module(_mod)

DELETION_CLAIM_PATTERNS = _mod.DELETION_CLAIM_PATTERNS
FILE_PATH_PATTERNS = _mod.FILE_PATH_PATTERNS
OBVIOUS_ALLOWLIST = _mod.OBVIOUS_ALLOWLIST
_sanitize_for_log = _mod._sanitize_for_log
_validate_path_boundary = _mod._validate_path_boundary
_extract_file_paths = _mod._extract_file_paths
_normalize_path = _mod._normalize_path
_check_path_with_timeout = _mod._check_path_with_timeout
_verify_deletion_claim = _mod._verify_deletion_claim
_detect_deletion_claims = _mod._detect_deletion_claims
check = _mod.check
run = _mod.run


class TestSanitizeForLog:
    """Tests for _sanitize_for_log helper."""

    def test_normal_text_preserved(self):
        """Normal text is preserved."""
        text = "Hello, World! File path: C:\\test\\file.py"
        result = _sanitize_for_log(text)
        assert "Hello" in result
        assert "World" in result

    def test_newlines_removed(self):
        """Newlines and carriage returns are removed."""
        text = "Line1\nLine2\rLine3\r\nLine4"
        result = _sanitize_for_log(text)
        assert "\n" not in result
        assert "\r" not in result

    def test_control_chars_removed(self):
        """Control characters are removed."""
        text = "Text\x00with\x07control\x1Fchars"
        result = _sanitize_for_log(text)
        assert "\x00" not in result
        assert "\x07" not in result
        assert "\x1f" not in result


class TestValidatePathBoundary:
    """Tests for _validate_path_boundary helper."""

    def test_path_within_boundary(self, monkeypatch, tmp_path):
        """Path within project root returns True."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        test_file = project_root / "test.txt"
        test_file.write_text("test")

        result = _validate_path_boundary(test_file, project_root)
        assert result is True

    def test_path_outside_boundary(self, monkeypatch, tmp_path):
        """Path outside project root returns False."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        outside_path = tmp_path / "outside" / "file.txt"
        outside_path.parent.mkdir()
        outside_path.write_text("test")

        result = _validate_path_boundary(outside_path, project_root)
        assert result is False

    def test_path_traversal_attempt(self, monkeypatch, tmp_path):
        """Path traversal attempt returns False."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        traversal_path = project_root / ".." / "outside" / "file.txt"
        traversal_path.parent.mkdir(parents=True)
        traversal_path.write_text("test")

        result = _validate_path_boundary(traversal_path, project_root)
        assert result is False


class TestExtractFilePaths:
    """Tests for _extract_file_paths helper."""

    def test_windows_absolute_path(self):
        """Extracts Windows absolute paths."""
        text = "Deleted P:\\test\\file.py and C:\\Users\\test.txt"
        paths = _extract_file_paths(text)
        assert any("file.py" in p for p in paths)
        assert any("test.txt" in p for p in paths)

    def test_quoted_filenames(self):
        """Extracts quoted filenames."""
        text = 'Deleted "test file.py" and \'old.js\''
        paths = _extract_file_paths(text)
        assert any("test file.py" in p or "file.py" in p for p in paths)
        assert any("old.js" in p for p in paths)

    def test_urls_excluded(self):
        """URLs are not extracted as file paths."""
        text = "See https://example.com/path/file.py and http://test.com/file.txt"
        paths = _extract_file_paths(text)
        # URLs should not be extracted
        assert not any("https://" in p for p in paths)
        assert not any("http://" in p for p in paths)

    def test_deduplication(self):
        """Duplicate paths are removed."""
        text = "Deleted file.py and also file.py"
        paths = _extract_file_paths(text)
        file_py_count = sum(1 for p in paths if "file.py" in p)
        assert file_py_count == 1


class TestDetectDeletionClaims:
    """Tests for _detect_deletion_claims helper."""

    def test_past_tense_deleted(self):
        """Past tense 'deleted' pattern is detected."""
        response = "The files were deleted successfully."
        claims = _detect_deletion_claims(response)
        assert len(claims) > 0

    def test_successfully_deleted(self):
        """'Successfully deleted' pattern is detected."""
        response = "I have successfully deleted the test files."
        claims = _detect_deletion_claims(response)
        assert len(claims) > 0

    def test_all_files_deleted(self):
        """'All files deleted' pattern is detected."""
        response = "All files deleted from the directory."
        claims = _detect_deletion_claims(response)
        assert len(claims) > 0

    def test_future_tense_allowlisted(self):
        """Future tense is allowlisted and not detected."""
        response = "I will delete the files later."
        claims = _detect_deletion_claims(response)
        assert len(claims) == 0

    def test_should_be_deleted_allowlisted(self):
        """'Should be deleted' is allowlisted."""
        response = "These files should be deleted for security."
        claims = _detect_deletion_claims(response)
        assert len(claims) == 0

    def test_can_be_deleted_allowlisted(self):
        """'Can be deleted' is allowlisted."""
        response = "Old files can be deleted to save space."
        claims = _detect_deletion_claims(response)
        assert len(claims) == 0

    def test_passive_voice_allowlisted(self):
        """Passive voice patterns are allowlisted."""
        response = "The temp files should be cleaned up."
        claims = _detect_deletion_claims(response)
        assert len(claims) == 0

    def test_i_didnt_delete_allowlisted(self):
        """'I didn't delete' conversational denial is allowlisted."""
        response = "I didn't delete those files."
        claims = _detect_deletion_claims(response)
        assert len(claims) == 0

    def test_i_havent_deleted_allowlisted(self):
        """'I haven't deleted' conversational denial is allowlisted."""
        response = "I haven't deleted anything yet."
        claims = _detect_deletion_claims(response)
        assert len(claims) == 0

    def test_no_claim_returns_empty(self):
        """No deletion claim returns empty list."""
        response = "The code looks good."
        claims = _detect_deletion_claims(response)
        assert claims == []

    def test_removed_reference_allowlisted(self):
        """'Removed the reference' is a code/doc change, not filesystem deletion."""
        response = "Removed the `type: 'prompt'` reference from hook_external_llm_policy.md"
        claims = _detect_deletion_claims(response)
        assert claims == []

    def test_removed_the_mention_allowlisted(self):
        """'Removed the mention' is a doc change, not filesystem deletion."""
        response = "Removed the mention of the deprecated API."
        claims = _detect_deletion_claims(response)
        assert claims == []

    def test_removed_the_usage_allowlisted(self):
        """'Removed the usage' is a code change, not filesystem deletion."""
        response = "Removed the usage of the old helper function."
        claims = _detect_deletion_claims(response)
        assert claims == []

    def test_removed_the_call_allowlisted(self):
        """'Removed the call' is a code change, not filesystem deletion."""
        response = "Removed the call to the deprecated method."
        claims = _detect_deletion_claims(response)
        assert claims == []

    def test_removed_the_import_allowlisted(self):
        """'Removed the import' is a code change, not filesystem deletion."""
        response = "Removed the import statement from the module."
        claims = _detect_deletion_claims(response)
        assert claims == []

    def test_removed_the_dependency_allowlisted(self):
        """'Removed the dependency' is a code change, not filesystem deletion."""
        response = "Removed the dependency on the external library."
        claims = _detect_deletion_claims(response)
        assert claims == []

    def test_removed_the_statement_allowlisted(self):
        """'Removed the statement' is a code change, not filesystem deletion."""
        response = "Removed the statement that was causing the error."
        claims = _detect_deletion_claims(response)
        assert claims == []

    def test_removed_the_variable_allowlisted(self):
        """'Removed the variable' is a code change, not filesystem deletion."""
        response = "Removed the variable from the function scope."
        claims = _detect_deletion_claims(response)
        assert claims == []

    def test_removed_the_assertion_allowlisted(self):
        """'Removed the assertion' is a code change, not filesystem deletion."""
        response = "Removed the assertion that was failing intermittently."
        claims = _detect_deletion_claims(response)
        assert claims == []

    def test_removed_file_still_detected(self):
        """Real filesystem deletion claim still detected (no regression)."""
        response = "Removed the placeholder at /tmp/test.txt"
        claims = _detect_deletion_claims(response)
        assert len(claims) > 0


class TestCheckPathWithTimeout:
    """Tests for _check_path_with_timeout helper."""

    def test_existing_file(self, tmp_path):
        """Existing file returns (True, False, '')."""
        test_file = tmp_path / "exists.txt"
        test_file.write_text("test")
        exists, is_dir, error = _check_path_with_timeout(test_file)
        assert exists is True
        assert is_dir is False
        assert error == ""

    def test_existing_directory(self, tmp_path):
        """Existing directory returns (True, True, '')."""
        test_dir = tmp_path / "subdir"
        test_dir.mkdir()
        exists, is_dir, error = _check_path_with_timeout(test_dir)
        assert exists is True
        assert is_dir is True
        assert error == ""

    def test_nonexistent_file(self, tmp_path):
        """Non-existent file returns (False, False, '')."""
        test_file = tmp_path / "does_not_exist.txt"
        exists, is_dir, error = _check_path_with_timeout(test_file)
        assert exists is False
        assert is_dir is False
        assert error == ""


class TestVerifyDeletionClaim:
    """Tests for _verify_deletion_claim helper."""

    def test_all_files_deleted_returns_true(self, monkeypatch, tmp_path):
        """When all files don't exist, returns (True, '')."""
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
        paths = [str(tmp_path / "deleted1.txt"), str(tmp_path / "deleted2.txt")]
        result, reason = _verify_deletion_claim(paths)
        assert result is True
        assert reason == ""

    def test_file_still_exists_returns_false(self, monkeypatch, tmp_path):
        """When file still exists, returns (False, reason)."""
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
        existing_file = tmp_path / "still_here.txt"
        existing_file.write_text("test")
        paths = [str(existing_file)]
        result, reason = _verify_deletion_claim(paths)
        assert result is False
        assert "still exist" in reason.lower() or "still_here" in reason.lower()

    def test_too_many_paths_returns_error(self, monkeypatch, tmp_path):
        """When too many paths, returns error."""
        paths = [f"path{i}.txt" for i in range(25)]
        result, reason = _verify_deletion_claim(paths)
        assert result is False
        assert "Too many paths" in reason


class TestCheck:
    """Tests for check() main function."""

    def test_empty_response_returns_none(self):
        """Empty response returns None (allow)."""
        data = {"assistant_response": ""}
        result = check(data)
        assert result is None

    def test_no_deletion_claim_returns_none(self):
        """No deletion claim returns None (allow)."""
        data = {"assistant_response": "The code looks good today."}
        result = check(data)
        assert result is None

    def test_verified_deletion_returns_none(self, monkeypatch, tmp_path):
        """Verified deletion claim returns None (allow)."""
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
        # File doesn't exist so deletion is "verified"
        data = {
            "assistant_response": f"Deleted {tmp_path / 'nonexistent.txt'} successfully."
        }
        result = check(data)
        assert result is None

    def test_unverified_deletion_blocks(self, monkeypatch, tmp_path):
        """Unverified deletion claim returns block dict."""
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
        # Create a file that exists
        existing_file = tmp_path / "still_here.txt"
        existing_file.write_text("test")
        data = {
            "assistant_response": f"Files were deleted: {existing_file}"
        }
        result = check(data)
        assert result is not None
        assert result.get("decision") == "block"
        assert "Stop_deletion_verification_guard" in result.get("blocking_hook", "")


class TestRun:
    """Tests for run() wrapper function."""

    def test_check_returns_block_dict(self, monkeypatch, tmp_path):
        """When check() returns block dict, run() formats for Stop_router."""
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
        existing_file = tmp_path / "still_here.txt"
        existing_file.write_text("test")
        data = {
            "assistant_response": f"Deleted {existing_file}."
        }
        result = run(data)
        assert result is not None
        assert result.get("block") is True
        assert "reason" in result

    def test_no_block_returns_none(self):
        """When no deletion claim, returns None."""
        data = {"assistant_response": "Everything looks good."}
        result = run(data)
        assert result is None
