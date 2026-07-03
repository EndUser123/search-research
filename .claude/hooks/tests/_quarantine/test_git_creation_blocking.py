#!/usr/bin/env python3
"""Tests for git creation operation blocking.

Tests that git commands creating files/folders are blocked with explicit approval.
"""

import json
import subprocess
import sys
from pathlib import Path

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PreToolUse_destructive_git_guard import check_bash_command


def test_git_worktree_add_blocked():
    """Test that git worktree add is detected as creative operation."""
    result = check_bash_command("git worktree add ../feature-branch feature-branch")
    assert result is not None
    assert result["operation_type"] == "git"
    assert result["subcommand"] == "worktree"
    assert result["category"] == "creative"
    assert result["severity"] == "HIGH"
    print("✅ Test passed: git worktree add is blocked")


def test_git_init_blocked():
    """Test that git init is detected as creative operation."""
    result = check_bash_command("git init new-repo")
    assert result is not None
    assert result["operation_type"] == "git"
    assert result["subcommand"] == "init"
    assert result["category"] == "creative"
    assert result["severity"] == "HIGH"
    print("✅ Test passed: git init is blocked")


def test_git_clone_blocked():
    """Test that git clone is detected as creative operation."""
    result = check_bash_command("git clone https://github.com/user/repo.git")
    assert result is not None
    assert result["operation_type"] == "git"
    assert result["subcommand"] == "clone"
    assert result["category"] == "creative"
    assert result["severity"] == "HIGH"
    print("✅ Test passed: git clone is blocked")


def test_git_checkout_new_branch_blocked():
    """Test that git checkout -b (new branch) is detected as creative operation."""
    result = check_bash_command("git checkout -b feature-new-stuff")
    assert result is not None
    assert result["operation_type"] == "git"
    assert result["subcommand"] == "checkout"
    assert result["category"] == "creative"
    assert result["severity"] == "MEDIUM"
    print("✅ Test passed: git checkout -b is blocked")


def test_git_checkout_existing_branch_not_blocked():
    """Test that git checkout (existing branch) is allowed."""
    result = check_bash_command("git checkout main")
    assert result is None
    print("✅ Test passed: git checkout (existing branch) is allowed")


def test_git_reset_hard_still_blocked():
    """Test that git reset --hard is still detected as destructive."""
    result = check_bash_command("git reset --hard HEAD")
    assert result is not None
    assert result["operation_type"] == "git"
    assert result["subcommand"] == "reset"
    assert result["category"] == "destructive"
    assert result["severity"] == "CRITICAL"
    print("✅ Test passed: git reset --hard still blocked")


def test_destructive_operations_have_correct_category():
    """Test that all destructive operations have 'destructive' category."""
    destructive_commands = [
        "git reset --hard HEAD",
        "git clean -f",
        "git stash drop stash@{0}",
    ]

    for cmd in destructive_commands:
        result = check_bash_command(cmd)
        assert result is not None, f"Command should be detected: {cmd}"
        assert result["category"] == "destructive", f"Command should be destructive: {cmd}"
        print(f"✅ {cmd} has correct 'destructive' category")


def test_creative_operations_have_correct_category():
    """Test that all creative operations have 'creative' category."""
    creative_commands = [
        ("git worktree add ../feature-branch feature-branch", "worktree"),
        ("git init new-repo", "init"),
        ("git clone https://github.com/user/repo.git", "clone"),
        ("git checkout -b new-branch", "checkout"),
    ]

    for cmd, subcommand in creative_commands:
        result = check_bash_command(cmd)
        assert result is not None, f"Command should be detected: {cmd}"
        assert result["category"] == "creative", f"Command should be creative: {cmd}"
        assert result["subcommand"] == subcommand, f"Subcommand should match: {cmd}"
        print(f"✅ {cmd} has correct 'creative' category")


def test_target_extraction():
    """Test that targets are correctly extracted for creative operations."""
    # Worktree target
    result = check_bash_command("git worktree add ../feature-branch feature-branch")
    assert result["target"] == "../feature-branch"

    # Clone target
    result = check_bash_command("git clone https://github.com/user/repo.git")
    assert result["target"] == "https://github.com/user/repo.git"

    # Init target
    result = check_bash_command("git init new-directory")
    assert result["target"] == "new-directory"

    # Checkout branch target
    result = check_bash_command("git checkout -b new-feature-branch")
    assert result["target"] == "new-feature-branch"

    print("✅ Test passed: Targets are correctly extracted")


def test_hook_blocks_worktree_without_approval():
    """Test that hook blocks git worktree add without approval flag."""
    hook_input = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "git worktree add ../feature-branch feature-branch"
        }
    }

    hook_path = Path(__file__).resolve().parent.parent / "PreToolUse_destructive_git_guard.py"
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        timeout=5
    )

    # Should exit with code 2 (blocked)
    assert result.returncode == 2

    # Should mention GIT IS NOT A FILE SYSTEM TOOL
    output = json.loads(result.stdout)
    assert output["decision"] == "block"
    assert "GIT IS NOT A FILE SYSTEM TOOL" in output["reason"]
    assert "worktree" in output["reason"].lower()

    print("✅ Test passed: Hook blocks git worktree add with appropriate message")


def test_hook_blocks_clone_with_alternative():
    """Test that hook provides alternative for git clone."""
    hook_input = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "git clone https://github.com/user/repo.git"
        }
    }

    hook_path = Path(__file__).resolve().parent.parent / "PreToolUse_destructive_git_guard.py"
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        timeout=5
    )

    # Should exit with code 2 (blocked)
    assert result.returncode == 2

    # Should provide alternative
    output = json.loads(result.stdout)
    assert output["decision"] == "block"
    assert "gh repo clone" in output["reason"] or "terminal" in output["reason"].lower()

    print("✅ Test passed: Hook provides alternative for git clone")


def test_hook_allows_with_approval_flag():
    """Test that hook allows creative operations with approval flag."""
    hook_input = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "git worktree add ../feature-branch feature-branch --i-understand-irreversible"
        }
    }

    hook_path = Path(__file__).resolve().parent.parent / "PreToolUse_destructive_git_guard.py"
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        timeout=5
    )

    # Should exit with code 0 (allowed)
    assert result.returncode == 0

    print("✅ Test passed: Hook allows creative operations with approval flag")


if __name__ == "__main__":
    print("Running git creation blocking tests...\n")

    # Unit tests
    test_git_worktree_add_blocked()
    test_git_init_blocked()
    test_git_clone_blocked()
    test_git_checkout_new_branch_blocked()
    test_git_checkout_existing_branch_not_blocked()
    test_git_reset_hard_still_blocked()

    test_destructive_operations_have_correct_category()
    test_creative_operations_have_correct_category()
    test_target_extraction()

    # Integration tests
    test_hook_blocks_worktree_without_approval()
    test_hook_blocks_clone_with_alternative()
    test_hook_allows_with_approval_flag()

    print("\n✅ All creation blocking tests passed!")
