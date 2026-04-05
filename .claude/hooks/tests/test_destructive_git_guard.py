#!/usr/bin/env python3
"""Tests for PreToolUse_destructive_git_guard.py

Tests cover both local git operations and GitHub CLI (gh) destructive operations.
"""

import json
import subprocess
import sys
from pathlib import Path

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PreToolUse_destructive_git_guard import check_bash_command


def test_git_reset_hard_blocked():
    """Test that git reset --hard is detected as destructive."""
    result = check_bash_command("git reset --hard HEAD")
    assert result is not None
    assert result["operation_type"] == "git"
    assert result["subcommand"] == "reset"
    assert result["severity"] == "CRITICAL"
    print("✅ Test passed: git reset --hard is detected")


def test_git_reset_soft_not_blocked():
    """Test that git reset --soft is NOT considered destructive."""
    result = check_bash_command("git reset --soft HEAD")
    assert result is None
    print("✅ Test passed: git reset --soft is allowed")


def test_gh_repo_delete_blocked():
    """Test that gh repo delete is detected as destructive."""
    result = check_bash_command("gh repo delete EndUser123/portfolio-media")
    assert result is not None
    assert result["operation_type"] == "github"
    assert result["subcommand"] == "repo"
    assert result["severity"] == "CRITICAL"
    assert result["target"] == "EndUser123/portfolio-media"
    print("✅ Test passed: gh repo delete is detected")


def test_gh_api_delete_blocked():
    """Test that gh api with DELETE method is detected as destructive."""
    result = check_bash_command("gh api repos/EndUser123/portfolio-media --method DELETE")
    assert result is not None
    assert result["operation_type"] == "github"
    assert result["subcommand"] == "api"
    assert result["severity"] == "HIGH"
    print("✅ Test passed: gh api DELETE is detected")


def test_gh_api_get_not_blocked():
    """Test that gh api GET requests are NOT considered destructive."""
    result = check_bash_command("gh api repos/EndUser123/portfolio-media")
    assert result is None
    print("✅ Test passed: gh api GET is allowed")


def test_gh_org_delete_blocked():
    """Test that gh org delete is detected as destructive."""
    result = check_bash_command("gh org delete test-org")
    assert result is not None
    assert result["operation_type"] == "github"
    assert result["subcommand"] == "org"
    assert result["severity"] == "CRITICAL"
    print("✅ Test passed: gh org delete is detected")


def test_gh_release_delete_blocked():
    """Test that gh release delete is detected as destructive."""
    result = check_bash_command("gh release delete v1.0.0")
    assert result is not None
    assert result["operation_type"] == "github"
    assert result["subcommand"] == "release"
    assert result["severity"] == "HIGH"
    print("✅ Test passed: gh release delete is detected")


def test_gh_gist_delete_blocked():
    """Test that gh gist delete is detected as destructive."""
    result = check_bash_command("gh gist delete abc123")
    assert result is not None
    assert result["operation_type"] == "github"
    assert result["subcommand"] == "gist"
    assert result["severity"] == "MEDIUM"
    print("✅ Test passed: gh gist delete is detected")


def test_gh_repo_view_not_blocked():
    """Test that gh repo view is NOT considered destructive."""
    result = check_bash_command("gh repo view EndUser123/portfolio-media")
    assert result is None
    print("✅ Test passed: gh repo view is allowed")


def test_gh_repo_delete_with_approval_flag():
    """Test that gh repo delete with approval flag contains the flag."""
    result = check_bash_command(
        "gh repo delete EndUser123/portfolio-media --i-understand-irreversible"
    )
    assert result is not None
    assert result["operation_type"] == "github"
    # The hook should detect it, but the run() function will allow it with the flag
    assert "--i-understand-irreversible" in result["command"]
    print("✅ Test passed: gh repo delete with approval flag is detected")


def test_bash_command_routing():
    """Test that check_bash_command correctly routes to git or gh functions."""
    git_result = check_bash_command("git reset --hard HEAD")
    assert git_result["operation_type"] == "git"

    gh_result = check_bash_command("gh repo delete test-repo")
    assert gh_result["operation_type"] == "github"

    none_result = check_bash_command("echo hello")
    assert none_result is None

    print("✅ Test passed: check_bash_command routing works correctly")


def test_hook_integration():
    """Test that the hook blocks gh repo delete without approval flag."""
    # Prepare hook input
    hook_input = {
        "tool_name": "Bash",
        "tool_input": {"command": "gh repo delete EndUser123/portfolio-media"},
    }

    # Run hook via subprocess
    hook_path = Path(__file__).resolve().parent.parent / "PreToolUse_destructive_git_guard.py"
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Should exit with code 2 (blocked)
    assert result.returncode == 2

    # Should output JSON with block decision
    output = json.loads(result.stdout)
    assert output["decision"] == "block"
    assert "Permanently delete GitHub repository" in output["reason"]
    assert "portfolio-media" in output["reason"]
    assert "--i-understand-irreversible" in output["reason"]

    print("✅ Test passed: Hook blocks gh repo delete without approval flag")


def test_hook_allows_with_approval_flag():
    """Test that the hook allows gh repo delete with approval flag."""
    # Prepare hook input
    hook_input = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "gh repo delete EndUser123/portfolio-media --i-understand-irreversible"
        },
    }

    # Run hook via subprocess
    hook_path = Path(__file__).resolve().parent.parent / "PreToolUse_destructive_git_guard.py"
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Should exit with code 0 (allowed)
    assert result.returncode == 0

    print("✅ Test passed: Hook allows gh repo delete with approval flag")


if __name__ == "__main__":
    print("Running destructive git guard tests...\n")

    # Unit tests
    test_git_reset_hard_blocked()
    test_git_reset_soft_not_blocked()
    test_gh_repo_delete_blocked()
    test_gh_api_delete_blocked()
    test_gh_api_get_not_blocked()
    test_gh_org_delete_blocked()
    test_gh_release_delete_blocked()
    test_gh_gist_delete_blocked()
    test_gh_repo_view_not_blocked()
    test_gh_repo_delete_with_approval_flag()
    test_bash_command_routing()

    # Integration tests
    test_hook_integration()
    test_hook_allows_with_approval_flag()

    print("\n✅ All tests passed!")
