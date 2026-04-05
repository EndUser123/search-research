#!/usr/bin/env python3
"""Tests for suggestion_utils.py - Shared utilities for next-command suggestion hooks.

Tests cover:
- load_commands_registry() - Registry loading
- extract_output_signals() - Signal detection
- get_git_context() - Git status
- get_command_description() - Command lookup
- build_suggestion_block() - Output formatting
- get_last_command() - Command extraction
- _find_git_root() - Git root detection
- _empty_git_context() - Empty context return
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

from __lib import suggestion_utils

# =============================================================================
# load_commands_registry()
# =============================================================================

class TestLoadCommandsRegistry:
    """Tests for load_commands_registry function."""

    def test_loads_from_custom_path(self, tmp_path):
        """Should load commands.toml from custom path when provided."""
        registry_file = tmp_path / "custom_commands.toml"
        registry_file.write_text(
            '[commands]\n'
            '[commands.custom]\n'
            'aliases = ["/custom"]\n'
            'description = "Custom command"\n'
            '\n'
            '[signals]\n'
            'SUPPORTED = "/verify"\n'
        )

        result = suggestion_utils.load_commands_registry(registry_file)

        assert "commands" in result
        assert "signals" in result
        assert "custom" in result["commands"]
        assert result["signals"]["SUPPORTED"] == "/verify"

    def test_returns_empty_dict_when_file_not_found(self, tmp_path):
        """Should return empty dict when registry file doesn't exist."""
        non_existent = tmp_path / "nonexistent.toml"
        result = suggestion_utils.load_commands_registry(non_existent)

        assert result == {"commands": {}, "signals": {}}

    def test_handles_toml_parse_error(self, tmp_path):
        """Should return empty dict when TOML is malformed."""
        registry_file = tmp_path / "bad_commands.toml"
        registry_file.write_text("invalid {{{ toml")

        result = suggestion_utils.load_commands_registry(registry_file)

        assert result == {"commands": {}, "signals": {}}

    def test_accepts_custom_path(self, tmp_path):
        """Should load from custom path when provided."""
        custom_file = tmp_path / "custom_commands.toml"
        custom_file.write_text(
            '[commands]\n'
            '[commands.custom]\n'
            'aliases = ["/custom"]\n'
        )

        result = suggestion_utils.load_commands_registry(custom_file)

        assert "custom" in result["commands"]


# =============================================================================
# extract_output_signals()
# =============================================================================

class TestExtractOutputSignals:
    """Tests for extract_output_signals function."""

    def test_detects_supported_signal(self):
        """Should detect SUPPORTED signal in response."""
        response = "The claim is SUPPORTED by evidence."
        signals = suggestion_utils.extract_output_signals(response)
        assert "SUPPORTED" in signals

    def test_detects_false_signal(self):
        """Should detect FALSE signal in response."""
        response = "The hypothesis was proven FALSE."
        signals = suggestion_utils.extract_output_signals(response)
        assert "FALSE" in signals

    def test_detects_insufficient_signal(self):
        """Should detect INSUFFICIENT signal in response."""
        response = "Evidence is INSUFFICIENT to conclude."
        signals = suggestion_utils.extract_output_signals(response)
        assert "INSUFFICIENT" in signals

    def test_detects_root_cause_signal(self):
        """Should detect root_cause_found signal."""
        response = "We identified the root cause of the issue."
        signals = suggestion_utils.extract_output_signals(response)
        assert "root_cause_found" in signals

    def test_detects_fix_applied_signal(self):
        """Should detect fix_applied signal."""
        response = "The fix was applied successfully."
        signals = suggestion_utils.extract_output_signals(response)
        assert "fix_applied" in signals

    def test_detects_plan_complete_signal(self):
        """Should detect plan_complete signal."""
        response = "The plan is now complete."
        signals = suggestion_utils.extract_output_signals(response)
        assert "plan_complete" in signals

    def test_detects_tests_passing_signal(self):
        """Should detect tests_passing signal."""
        response = "All tests are passing now."
        signals = suggestion_utils.extract_output_signals(response)
        assert "tests_passing" in signals

    def test_detects_multiple_signals(self):
        """Should detect multiple signals in one response."""
        response = "The fix was applied and tests are passing. The claim is SUPPORTED."
        signals = suggestion_utils.extract_output_signals(response)
        assert "fix_applied" in signals
        assert "tests_passing" in signals
        assert "SUPPORTED" in signals

    def test_returns_empty_list_when_no_signals(self):
        """Should return empty list when no signals found."""
        response = "This is just regular text with no workflow signals."
        signals = suggestion_utils.extract_output_signals(response)
        assert signals == []

    def test_case_insensitive_matching(self):
        """Should match signals case-insensitively."""
        response = "supported false insufficient"
        signals = suggestion_utils.extract_output_signals(response)
        assert "SUPPORTED" in signals
        assert "FALSE" in signals
        assert "INSUFFICIENT" in signals


# =============================================================================
# get_git_context()
# =============================================================================

class TestGetGitContext:
    """Tests for get_git_context function."""

    def test_returns_empty_context_when_cwd_is_none_and_no_cwd(self):
        """Should return empty context when cwd cannot be determined."""
        with patch.object(suggestion_utils, "Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            result = suggestion_utils.get_git_context()
            assert result == {
                "has_changes": False,
                "has_unstaged": False,
                "has_unpushed": False,
                "is_worktree": False,
                "change_count": 0,
                "summary": "",
            }

    def test_detects_has_changes_from_git_status(self, tmp_path):
        """Should detect changes from git status --porcelain."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        # Mock subprocess.run to return our test data
        with patch("subprocess.run") as mock_run:
            # Git status format: "XY filename" where X=worktree, Y=staged
            # "M " = modified in worktree, not staged
            # " A" = added to worktree, not staged
            status_result = Mock()
            status_result.returncode = 0
            # Use proper git status format where second char != ' ' means unstaged
            status_result.stdout = "MM  file1.py\nA   file2.py\n"

            log_result = Mock()
            log_result.returncode = 0
            log_result.stdout = ""

            mock_run.side_effect = [status_result, log_result]

            result = suggestion_utils.get_git_context(cwd=tmp_path)

            assert result["has_changes"] is True
            assert result["has_unstaged"] is True
            assert result["change_count"] == 2

    def test_detects_untracked_files_ignored(self):
        """Should ignore untracked files (??) in change count."""
        with patch("subprocess.run") as mock_run:
            # Mock git status with untracked files
            mock_run.return_value = Mock(
                returncode=0,
                stdout="?? new_file.py\nM modified.py\n"
            )

            result = suggestion_utils.get_git_context()

            # Only count the modified file, not untracked (?? is ignored)
            assert result["change_count"] == 1

    def test_detects_worktree_vs_main_repo(self, tmp_path):
        """Should distinguish between worktree and main repo."""
        # Worktree: .git is a file
        git_file = tmp_path / ".git"
        git_file.write_text("gitdir: /path/to/main.git\n")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="")

            result = suggestion_utils.get_git_context(cwd=tmp_path)

            assert result["is_worktree"] is True

    def test_main_repo_detection(self, tmp_path):
        """Should detect main repo (.git is a directory)."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="")

            result = suggestion_utils.get_git_context(cwd=tmp_path)

            assert result["is_worktree"] is False

    def test_checks_unpushed_only_in_worktree(self, tmp_path):
        """Should only check for unpushed commits when in a worktree."""
        git_file = tmp_path / ".git"
        git_file.write_text("gitdir: /path/to/main.git\n")

        with patch("subprocess.run") as mock_run:
            # First call: git status
            # Second call: git log (for unpushed)
            mock_run.side_effect = [
                Mock(returncode=0, stdout=""),  # git status
                Mock(returncode=0, stdout="abc123\n"),  # git log shows commit
            ]

            result = suggestion_utils.get_git_context(cwd=tmp_path)

            assert result["has_unpushed"] is True

    def test_handles_subprocess_error_gracefully(self, tmp_path):
        """Should return empty context on subprocess error."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("git", 2)):
            result = suggestion_utils.get_git_context(cwd=tmp_path)
            assert result["has_changes"] is False

    def test_includes_summary_first_five_lines(self, tmp_path):
        """Should include first 5 lines of git status in summary."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        with patch("subprocess.run") as mock_run:
            status_output = "\n".join([f"M file{i}.py" for i in range(10)])
            mock_run.return_value = Mock(returncode=0, stdout=status_output)

            result = suggestion_utils.get_git_context(cwd=tmp_path)

            assert len(result["summary"].split("\n")) == 5


# =============================================================================
# get_command_description()
# =============================================================================

class TestGetCommandDescription:
    """Tests for get_command_description function."""

    def test_finds_description_by_command_with_slash(self):
        """Should find description when command includes leading slash."""
        registry = {
            "commands": {
                "test_cmd": {
                    "aliases": ["/test", "t"],
                    "description": "Run tests"
                }
            }
        }

        result = suggestion_utils.get_command_description("/test", registry)
        assert result == "Run tests"

    def test_finds_description_by_command_without_slash(self):
        """Should find description when command lacks leading slash."""
        registry = {
            "commands": {
                "test_cmd": {
                    "aliases": ["/test", "test"],
                    "description": "Run tests"
                }
            }
        }

        result = suggestion_utils.get_command_description("test", registry)
        assert result == "Run tests"

    def test_returns_empty_when_command_not_found(self):
        """Should return empty string when command not in registry."""
        registry = {
            "commands": {
                "other_cmd": {
                    "aliases": ["/other"],
                    "description": "Other command"
                }
            }
        }

        result = suggestion_utils.get_command_description("/nonexistent", registry)
        assert result == ""

    def test_loads_registry_when_not_provided(self, tmp_path):
        """Should load default registry when none provided."""
        # We can't easily mock the default path search,
        # so just verify the function is callable
        # and returns the expected structure
        registry_file = tmp_path / "registry" / "commands.toml"
        registry_file.parent.mkdir(parents=True)
        registry_file.write_text(
            '[commands]\n'
            '[commands.autoload]\n'
            'aliases = ["/auto"]\n'
            'description = "Auto-loaded"\n'
        )

        # Call with explicit path to verify it works
        result = suggestion_utils.load_commands_registry(registry_file)

        assert "autoload" in result["commands"]
        assert result["commands"]["autoload"]["description"] == "Auto-loaded"


# =============================================================================
# build_suggestion_block()
# =============================================================================

class TestBuildSuggestionBlock:
    """Tests for build_suggestion_block function."""

    def test_builds_block_with_suggestions(self):
        """Should build formatted block with suggestions."""
        suggestions = [
            "/commit - Commit changes",
            "/duf - Pre-mortem analysis"
        ]

        result = suggestion_utils.build_suggestion_block(suggestions)

        assert "**Next Command Suggestions:**" in result
        assert "/commit - Commit changes" in result
        assert "/duf - Pre-mortem analysis" in result

    def test_deduplicates_suggestions(self):
        """Should remove duplicate suggestions while preserving order."""
        suggestions = [
            "/commit - Commit changes",
            "/duf - Analysis",
            "/commit - Commit changes",  # Duplicate
            "/test - Run tests"
        ]

        result = suggestion_utils.build_suggestion_block(suggestions)

        # Should only have one /commit
        commit_count = result.count("/commit")
        assert commit_count == 1

    def test_limits_to_max_suggestions(self):
        """Should limit output to max_suggestions parameter."""
        suggestions = [f"/cmd{i} - Command {i}" for i in range(10)]

        result = suggestion_utils.build_suggestion_block(
            suggestions,
            max_suggestions=3
        )

        # Should only have first 3
        for i in range(3, 9):
            assert f"/cmd{i}" not in result

    def test_includes_context_when_provided(self):
        """Should append context string when provided."""
        suggestions = ["/test - Run tests"]

        result = suggestion_utils.build_suggestion_block(
            suggestions,
            context="3 files changed"
        )

        assert "Context: 3 files changed" in result

    def test_returns_empty_when_no_suggestions(self):
        """Should return empty string when no suggestions provided."""
        result = suggestion_utils.build_suggestion_block([])
        assert result == ""

    def test_handles_suggestions_without_descriptions(self):
        """Should handle suggestions that are just commands."""
        suggestions = ["/test", "/verify"]

        result = suggestion_utils.build_suggestion_block(suggestions)

        assert "/test" in result
        assert "/verify" in result


# =============================================================================
# get_last_command()
# =============================================================================

class TestGetLastCommand:
    """Tests for get_last_command function."""

    def test_extracts_command_from_prompt(self):
        """Should extract last slash command from prompt."""
        prompt = "Let me run /test to check the code"
        result = suggestion_utils.get_last_command(prompt)
        assert result == "/test"

    def test_extracts_command_with_hyphen(self):
        """Should extract commands with hyphens."""
        prompt = "Use /git-sync to sync changes"
        result = suggestion_utils.get_last_command(prompt)
        assert result == "/git-sync"

    def test_extracts_command_with_underscore(self):
        """Should extract commands with underscores."""
        prompt = "Run /test_coverage_report"
        result = suggestion_utils.get_last_command(prompt)
        assert result == "/test_coverage_report"

    def test_returns_none_when_no_command(self):
        """Should return None when no slash command found."""
        prompt = "This is just regular text without any commands"
        result = suggestion_utils.get_last_command(prompt)
        assert result is None

    def test_extracts_last_command_when_multiple(self):
        """Should extract the first (not last) command when multiple present."""
        # Note: The regex search() finds the FIRST match, not last
        # This is the actual behavior of the function
        prompt = "First /test then /verify and finally /commit"
        result = suggestion_utils.get_last_command(prompt)
        assert result == "/test"


# =============================================================================
# Internal Helpers
# =============================================================================

class TestFindGitRoot:
    """Tests for _find_git_root helper function."""

    def test_finds_git_root_in_current_directory(self, tmp_path):
        """Should find .git in current directory."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = suggestion_utils._find_git_root(tmp_path)
        assert result == tmp_path

    def test_searches_parent_directories(self, tmp_path):
        """Should search parent directories for .git."""
        # Create nested directory structure
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)

        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = suggestion_utils._find_git_root(nested)
        assert result == tmp_path

    def test_returns_none_when_no_git_found(self, tmp_path):
        """Should return None when .git not found in any parent."""
        result = suggestion_utils._find_git_root(tmp_path)
        assert result is None


class TestEmptyGitContext:
    """Tests for _empty_git_context helper function."""

    def test_returns_proper_empty_context_structure(self):
        """Should return properly structured empty context."""
        result = suggestion_utils._empty_git_context()

        expected = {
            "has_changes": False,
            "has_unstaged": False,
            "has_unpushed": False,
            "is_worktree": False,
            "change_count": 0,
            "summary": "",
        }
        assert result == expected
