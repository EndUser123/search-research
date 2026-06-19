"""Unit tests for permission pair detection and recovery."""

import json
import pytest
from pathlib import Path

from __lib.permission_recovery import (
    find_matching_read_permission,
    generate_write_pattern,
    validate_proposed_permission,
    _path_matches_pattern,
)


@pytest.fixture
def sample_settings():
    """Sample settings.json with allowlist permissions."""
    return {
        "allowlist": [
            "Read(P:/.claude/.staging/**)",
            "Read(P:/.data/**)",
            "Write(P:/.claude/.artifacts/**)",
            "Read(P:/packages/**)",
        ]
    }


class TestPathMatching:
    """Test path pattern matching logic."""

    def test_exact_match(self):
        assert _path_matches_pattern("P:/.claude/test.txt", "P:/.claude/test.txt")

    def test_wildcard_match(self):
        assert _path_matches_pattern("P:/.claude/.staging/file.yaml", "P:/.claude/.staging/**")

    def test_directory_prefix_match(self):
        assert _path_matches_pattern("P:/packages/abc/test.py", "P:/packages/**")

    def test_no_match_different_path(self):
        assert not _path_matches_pattern("P:/other/file.txt", "P:/.claude/**")


class TestFindMatchingReadPermission:
    """Test detection of Read permissions corresponding to Write paths."""

    def test_finds_exact_match(self, sample_settings):
        write_path = "P:/.claude/.staging/config.yaml"
        result = find_matching_read_permission(write_path, sample_settings)
        assert result == "Read(P:/.claude/.staging/**)"

    def test_finds_wildcard_match(self, sample_settings):
        write_path = "P:/packages/something/file.txt"
        result = find_matching_read_permission(write_path, sample_settings)
        assert result == "Read(P:/packages/**)"

    def test_no_match_when_write_already_exists(self, sample_settings):
        write_path = "P:/.claude/.artifacts/output.txt"
        result = find_matching_read_permission(write_path, sample_settings)
        assert result is None

    def test_no_match_for_unauthorized_path(self, sample_settings):
        write_path = "P:/forbidden/file.txt"
        result = find_matching_read_permission(write_path, sample_settings)
        assert result is None


class TestGenerateWritePattern:
    """Test Write permission pattern generation."""

    def test_converts_read_to_write(self):
        read_perm = "Read(P:/.claude/.staging/**)"
        result = generate_write_pattern(read_perm)
        assert result == "Write(P:/.claude/.staging/**)"

    def test_handles_nested_paths(self):
        read_perm = "Read(P:/packages/.claude-marketplace/**)"
        result = generate_write_pattern(read_perm)
        assert result == "Write(P:/packages/.claude-marketplace/**)"


class TestValidateProposedPermission:
    """Test security validation of proposed Write permissions."""

    def test_safe_pattern_approved(self):
        safe_perm = "Write(P:/.claude/.staging/**)"
        is_safe, msg = validate_proposed_permission(safe_perm)
        assert is_safe
        assert msg == "Permission safe"

    def test_dangerous_parent_wildcard_rejected(self):
        dangerous_perm = "Write(../**)"
        is_safe, msg = validate_proposed_permission(dangerous_perm)
        assert not is_safe
        assert "DANGEROUS" in msg

    def test_dangerous_root_drive_rejected(self):
        dangerous_perm = "Write(C:/*)"
        is_safe, msg = validate_proposed_permission(dangerous_perm)
        assert not is_safe
        assert "DANGEROUS" in msg

    def test_dangerous_double_wildcard_rejected(self):
        dangerous_perm = "Write(**)"
        is_safe, msg = validate_proposed_permission(dangerous_perm)
        assert not is_safe
        assert "DANGEROUS" in msg

    def test_safe_package_wildcard_approved(self):
        safe_perm = "Write(P:/packages/skill/**)"
        is_safe, msg = validate_proposed_permission(safe_perm)
        assert is_safe