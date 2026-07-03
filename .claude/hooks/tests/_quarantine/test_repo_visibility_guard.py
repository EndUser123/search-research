#!/usr/bin/env python3
"""Tests for repository visibility guard hook."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from PreToolUse_repo_visibility_guard import (
    detect_visibility_change,
    is_allowed_public_path,
    is_protected_path,
    run,
)


class TestPathValidation:
    """Test path validation logic."""

    def test_protected_path_p_drive(self):
        """P: drive is protected."""
        assert is_protected_path("P:/")
        assert is_protected_path("P:/some/repo")
        assert is_protected_path("P:\\some\\repo")

    def test_protected_path_case_insensitive(self):
        """Path matching is case-insensitive."""
        assert is_protected_path("p:/")
        assert is_protected_path("P:/REPO")

    def test_non_protected_paths(self):
        """Other drives are not protected."""
        assert not is_protected_path("C:/")
        assert not is_protected_path("D:/repo")
        assert not is_protected_path("/home/user/repo")

    def test_allowed_public_path_packages(self):
        """packages/ folder can be public."""
        assert is_allowed_public_path("P:/packages/")
        assert is_allowed_public_path("P:/packages/some-repo")
        assert is_allowed_public_path("P:\\packages\\repo")

    def test_allowed_public_path_case_insensitive(self):
        """Allowed path matching is case-insensitive."""
        assert is_allowed_public_path("P:/PACKAGES/")
        assert is_allowed_public_path("p:/packages/repo")

    def test_non_allowed_public_paths(self):
        """Paths outside packages/ are not allowed to be public."""
        assert not is_allowed_public_path("P:/other/")
        assert not is_allowed_public_path("P:/src/")
        assert not is_allowed_public_path("C:/packages/")


class TestVisibilityChangeDetection:
    """Test detection of visibility change commands."""

    def test_detect_gh_cli_public(self):
        """Detect GitHub CLI public visibility change."""
        is_change, visibility = detect_visibility_change(
            "gh repo edit owner/repo --visibility public"
        )
        assert is_change
        assert visibility == "public"

    def test_detect_gh_cli_private(self):
        """Detect GitHub CLI private visibility change."""
        is_change, visibility = detect_visibility_change(
            "gh repo edit owner/repo --visibility private"
        )
        assert is_change
        assert visibility == "private"

    def test_detect_gh_cli_case_insensitive(self):
        """Detection is case-insensitive."""
        is_change, visibility = detect_visibility_change(
            "GH REPO EDIT owner/repo --VISIBILITY PUBLIC"
        )
        assert is_change
        assert visibility == "public"

    def test_detect_curl_api_call(self):
        """Detect curl API calls that change visibility."""
        is_change, visibility = detect_visibility_change(
            'curl -X PATCH api.github.com/repos/owner/repo -d \'{"visibility":"public"}\''
        )
        assert is_change
        assert visibility == "public"

    def test_detect_wget_api_call(self):
        """Detect wget API calls that change visibility."""
        is_change, visibility = detect_visibility_change(
            'wget --method=PATCH api.github.com/repos/owner/repo --body-data=\'{"visibility":"private"}\''
        )
        assert is_change
        assert visibility == "private"

    def test_detect_powershell_api_call(self):
        """Detect PowerShell Invoke-WebRequest calls."""
        is_change, visibility = detect_visibility_change(
            'Invoke-WebRequest -Method Patch -Uri "api.github.com/repos/owner/repo" -Body \'{"visibility":"public"}\''
        )
        assert is_change
        assert visibility == "public"

    def test_non_visibility_commands(self):
        """Don't flag non-visibility commands."""
        test_commands = [
            "gh repo view owner/repo",
            "git status",
            "curl https://api.github.com/users/octocat",
            "gh auth status",
            "echo 'hello'",
        ]
        for cmd in test_commands:
            is_change, visibility = detect_visibility_change(cmd)
            assert not is_change
            assert visibility is None


class TestHookBlockingLogic:
    """Test the main hook blocking logic."""

    def make_hook_input(self, command: str) -> dict:
        """Create hook input data structure."""
        return {
            "tool_name": "Bash",
            "tool_input": {
                "command": command
            }
        }

    def test_blocks_p_drive_public_visibility(self, monkeypatch):
        """Block P: drive repos from being made public."""
        # Mock get_current_repo_path to return P:/ drive path
        monkeypatch.setattr(
            "PreToolUse_repo_visibility_guard.get_current_repo_path",
            lambda: "P:/my-private-repo"
        )

        data = self.make_hook_input("gh repo edit owner/repo --visibility public")
        result = run(data)

        assert result is not None
        assert result["decision"] == "block"
        assert "visibility change blocked" in result["reason"].lower()
        assert "P: drive" in result["reason"]

    def test_allows_packages_public_visibility(self, monkeypatch):
        """Allow packages/ repos to be made public."""
        monkeypatch.setattr(
            "PreToolUse_repo_visibility_guard.get_current_repo_path",
            lambda: "P:/packages/my-public-lib"
        )

        data = self.make_hook_input("gh repo edit owner/repo --visibility public")
        result = run(data)

        assert result is None  # Allow

    def test_allows_private_visibility_all_paths(self, monkeypatch):
        """Allow all repos to be made private (safe operation)."""
        monkeypatch.setattr(
            "PreToolUse_repo_visibility_guard.get_current_repo_path",
            lambda: "P:/sensitive-repo"
        )

        data = self.make_hook_input("gh repo edit owner/repo --visibility private")
        result = run(data)

        assert result is None  # Allow

    def test_bypass_flag(self, monkeypatch):
        """Respect --allow-visibility-change bypass flag."""
        monkeypatch.setattr(
            "PreToolUse_repo_visibility_guard.get_current_repo_path",
            lambda: "P:/sensitive-repo"
        )

        data = self.make_hook_input(
            "gh repo edit owner/repo --visibility public --allow-visibility-change"
        )
        result = run(data)

        assert result is None  # Allow due to bypass flag

    def test_non_git_commands_allowed(self):
        """Don't block non-git commands."""
        data = self.make_hook_input("echo 'hello world'")
        result = run(data)

        assert result is None  # Allow

    def test_unknown_repo_path_allowed(self, monkeypatch):
        """Allow when repo path can't be determined (fail-open)."""
        monkeypatch.setattr(
            "PreToolUse_repo_visibility_guard.get_current_repo_path",
            lambda: None
        )

        data = self.make_hook_input("gh repo edit owner/repo --visibility public")
        result = run(data)

        assert result is None  # Allow (fail-open)


class TestHookIntegration:
    """Integration tests with actual hook execution."""

    def test_hook_executes_successfully(self):
        """Hook can be executed via Python subprocess."""
        hook_path = HOOKS_DIR / "PreToolUse_repo_visibility_guard.py"

        test_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "gh repo edit owner/repo --visibility public"
            }
        }

        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should not crash (exit 0 or 2 are both valid)
        assert result.returncode in (0, 2)

    def test_hook_blocks_with_correct_output(self, monkeypatch):
        """Hook outputs correct JSON block message."""
        monkeypatch.setenv("REPO_VISIBILITY_GUARD_ENABLED", "true")
        monkeypatch.setattr(
            "PreToolUse_repo_visibility_guard.get_current_repo_path",
            lambda: "P:/sensitive-repo"
        )

        hook_path = HOOKS_DIR / "PreToolUse_repo_visibility_guard.py"

        test_input = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "gh repo edit owner/repo --visibility public"
            }
        }

        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Should block (exit code 2)
        assert result.returncode == 2

        # Should output valid JSON
        output = json.loads(result.stdout)
        assert output["decision"] == "block"
        assert "visibility change blocked" in output["reason"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
