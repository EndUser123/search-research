#!/usr/bin/env python3

from __future__ import annotations


# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

# Import auto-logging decorator
from __lib.hook_base import hook_main

"""
PreToolUse Git Safety Hook - "Did we forget anything?"

Checks before git commits to catch common omissions:
- Untracked test files
- Modified config files
- Changed dependencies
- Large or suspicious files

This hook RETURNS INFO to the LLM, asking "Did we forget anything?"
It does NOT block the commit - it just prompts reflection.
"""

import json
import re
import sys
import time
from pathlib import Path

from performance_tracker import track_hook_performance

# Worktree helper imports with fallback for ImportError
try:
    from __lib.worktree_helper import (
        get_current_worktree,
        is_cross_worktree_access,
        validate_git_command_for_worktree,
    )
    WORKTREE_HELPER_AVAILABLE = True
except ImportError:
    WORKTREE_HELPER_AVAILABLE = False

# Pre-compiled regex pattern for test path detection
TEST_PATH_PATTERN = re.compile(r'^tests?/', re.IGNORECASE)

# Test file exemption
try:
    from __lib.test_detection import is_test_file_operation
except ImportError:
    def is_test_file_operation(file_path: str) -> bool:
        import os
        path_lower = file_path.lower()
        return bool(TEST_PATH_PATTERN.search(path_lower) or 'test' in path_lower.split(os.sep))

# Files that often get forgotten
FORGETTABLE_PATTERNS = [
    # Config files
    ".env",
    ".env.example",
    "pytest.ini",
    "pyproject.toml",
    "setup.cfg",
    "package.json",
    "tsconfig.json",
    ".gitignore",

    # Documentation
    "README.md",
    "CHANGELOG.md",
    "README",
    "docs/",
]

# Patterns that should prompt extra caution
SUSPICIOUS_PATTERNS = [
    ("secrets", [".env", ".key", ".pem", "credentials.json", "secrets", "passwords", "tokens"]),
    ("large files", [".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar", ".gz", ".db", ".sqlite"]),
    ("build artifacts", ["node_modules/", "__pycache__/", ".pyc", ".o", ".so", ".dll", ".exe"]),
]

# Directories/files to never flag as suspicious (safe lists)
SAFE_PATTERNS = [
    "test_", "_test.py", "/tests/", "/test/", "mock", "fixture", "fake",
    "schema", "database", "config",
]

def ensure_fresh_index(repo_root: Path | None = None) -> None:
    """
    Remove stale .git/index.lock files (main + worktrees) if older than 30 seconds.

    This prevents "index.lock exists" errors when:
    - Background processes were killed mid-git-operation
    - System crashes during git operations
    - Network issues stall git processes

    When in a worktree, prioritizes cleaning that worktree's lock.
    Also checks all other worktree locks at .git/worktrees/*/index.lock

    Args:
        repo_root: Path to git repository root. Defaults to current directory.
    """
    if repo_root is None:
        # Find git repository root by traversing up from current directory
        repo_root = Path.cwd()
        while repo_root != repo_root.parent and not (repo_root / ".git").exists():
            repo_root = repo_root.parent

    # List of lock paths to check (main + worktrees)
    lock_paths = [repo_root / ".git" / "index.lock"]

    # Check if we're in a worktree by looking for the .git file
    # If so, add that worktree's lock first (highest priority)
    cwd = Path.cwd()
    git_file = cwd / ".git"
    if git_file.exists() and git_file.is_file():
        # This is a worktree - the .git file contains the path to the worktree metadata
        try:
            gitdir_line = git_file.read_text().strip()
            if gitdir_line.startswith("gitdir:"):
                gitdir = gitdir_line.split(":", 1)[1].strip()
                worktree_lock = Path(gitdir) / "index.lock"
                if worktree_lock.exists():
                    lock_paths.insert(0, worktree_lock)  # Insert at beginning (highest priority)
        except (OSError, PermissionError):
            pass

    # Add all worktree lock directories from main repo
    worktrees_dir = repo_root / ".git" / "worktrees"
    if worktrees_dir.exists():
        lock_paths.extend(worktrees_dir.glob("*/index.lock"))

    for lock_path in lock_paths:
        if not lock_path.exists():
            continue

        # Check lock age
        lock_age = time.time() - lock_path.stat().st_mtime

        # Only remove if lock is stale (> 30 seconds old) and empty (0 bytes)
        # Legitimate git operations complete much faster than this
        # Non-empty locks may be held by active processes
        try:
            is_empty = lock_path.stat().st_size == 0
        except (OSError, PermissionError):
            is_empty = False

        if lock_age > 30 and is_empty:
            try:
                lock_path.unlink()
            except (OSError, PermissionError):
                # If we can't remove it, that's fine - let the actual git command fail
                pass

def run_git_cmd(cmd: list[str]) -> tuple[str, str, int]:
    """Run git command and return stdout, stderr, exit code."""
    import subprocess
    import sys
    # Insert --no-optional-locks after 'git' to prevent index.lock creation
    # This allows hooks to run read-only git commands without blocking actual git operations
    if len(cmd) > 0 and cmd[0] == "git":
        cmd = ["git", "--no-optional-locks"] + cmd[1:]
    # Add CREATE_NO_WINDOW on Windows to prevent console flash
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, creationflags=creation_flags)
    return result.stdout, result.stderr, result.returncode

def get_git_status() -> dict:
    """Get git status information."""
    status = {
        "staged_files": [],
        "modified_files": [],
        "untracked_files": [],
        "branch": "",
    }

    # Get current branch
    stdout, _, _ = run_git_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    status["branch"] = stdout.strip()

    # Get staged files
    stdout, _, _ = run_git_cmd(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"])
    status["staged_files"] = [f for f in stdout.strip().split("\n") if f]

    # Get modified but unstaged files
    stdout, _, _ = run_git_cmd(["git", "diff", "--name-only"])
    status["modified_files"] = [f for f in stdout.strip().split("\n") if f]

    # Get untracked files
    stdout, _, _ = run_git_cmd(["git", "ls-files", "--others", "--exclude-standard"])
    status["untracked_files"] = [f for f in stdout.strip().split("\n") if f]

    return status

def check_forgettables(files: list[str]) -> dict[str, list[str]]:
    """Check if files match forgettable patterns."""
    found = {}

    for file_path in files:
        lower_path = file_path.lower()

        for pattern in FORGETTABLE_PATTERNS:
            if pattern.lower() in lower_path:
                category = pattern.strip("/.")
                if category not in found:
                    found[category] = []
                found[category].append(file_path)
                break

    return found

def check_suspicious(files: list[str]) -> dict[str, list[str]]:
    """Check for suspicious file patterns."""
    found = {}

    for file_path in files:
        lower_path = file_path.lower()

        # Skip safe patterns (test files, mocks, fixtures, schemas, databases)
        if any(safe in lower_path for safe in SAFE_PATTERNS):
            continue

        for category, patterns in SUSPICIOUS_PATTERNS:
            for pattern in patterns:
                if pattern.lower() in lower_path:
                    if category not in found:
                        found[category] = []
                    found[category].append(file_path)
                    break

    return found

def check_untracked_tests(untracked: list[str]) -> list[str]:
    """Find untracked test files."""
    test_patterns = ["test_", "_test.py", "/tests/", "/test/"]
    tests = []

    for file_path in untracked:
        lower_path = file_path.lower()
        if any(p in lower_path for p in test_patterns):
            tests.append(file_path)

    return tests

def format_check_message(checks: dict) -> str:
    """Format check results into a message."""
    if not checks:
        return ""

    lines = ["\n🤔 Did we forget anything?"]
    lines.append("-" * 40)

    for category, files in checks.items():
        lines.append(f"\n  {category}:")
        for f in files:
            lines.append(f"    - {f}")

    lines.append("-" * 40)
    lines.append("Review these before committing. If everything looks good, proceed.")
    lines.append("")

    return "\n".join(lines)

def check_worktree_cross_contamination(
    tool_name: str,
    tool_input: dict,
    input_data: dict
) -> dict:
    """Check git commands and Edit/Write operations for cross-worktree boundary violations.

    Validates git commands that operate on files (restore, checkout, etc.)
    and Edit/Write operations targeting files outside the current worktree.

    Args:
        tool_name: Name of the tool being called (e.g., "Bash", "Edit", "Write")
        tool_input: Input parameters for the tool
        input_data: Full hook input data (for accessing bypass flags)

    Returns:
        Dict with:
        - 'continue': False if operation should be blocked, True otherwise
        - 'reason': Explanation of why operation was blocked (if blocked)
        - 'decision': 'block' or 'allow'

    Bypass flag:
        Set '--allow-cross-worktree' in user message to bypass this check.
    """
    # Only check Bash (git commands) and Edit/Write operations
    if tool_name not in ("Bash", "Edit", "Write"):
        return {"continue": True, "decision": "allow"}

    # Check for bypass flag in user message
    user_message = input_data.get("user_message", "")
    if "--allow-cross-worktree" in user_message:
        return {"continue": True, "decision": "allow", "reason": "Cross-worktree check bypassed"}

    # Check if worktree helper is available
    if not WORKTREE_HELPER_AVAILABLE:
        # Worktree helper not available - allow command (fail open)
        return {"continue": True, "decision": "allow", "reason": "Worktree helper unavailable"}

    # Handle Edit/Write operations
    if tool_name in ("Edit", "Write"):
        file_path = tool_input.get("file_path", "")
        if not file_path:
            return {"continue": True, "decision": "allow"}

        # TEST FILE EXEMPTION: test files can write anywhere
        if is_test_file_operation(file_path):
            return {"continue": True, "decision": "allow"}

        try:
            cwd = Path.cwd().resolve()
            worktree = get_current_worktree(cwd)
            if is_cross_worktree_access(cwd, file_path, worktree):
                return {
                    "continue": False,
                    "reason": f"\n❌ CROSS-WORKTREE WRITE: '{file_path}' is outside current worktree ({worktree})\n\nTo bypass: Add --allow-cross-worktree to your message.",
                    "decision": "block"
                }
        except (ValueError, RuntimeError):
            # Can't determine worktree - allow (fail open)
            pass

        return {"continue": True, "decision": "allow"}

    # Handle Bash (git commands)
    command = tool_input.get("command", "")

    # Only check git commands that operate on files
    if not command.startswith("git "):
        return {"continue": True, "decision": "allow"}

    # Validate command for worktree violations
    try:
        validation = validate_git_command_for_worktree(command)

        if not validation["valid"]:
            # Cross-worktree access detected
            violations = validation.get("violations", [])
            current_worktree = validation.get("current_worktree", "unknown")

            reason_parts = [
                f"❌ CROSS-WORKTREE ACCESS: {len(violations)} file(s) outside current worktree ({current_worktree})",
            ]

            for violation in violations:
                reason_parts.append(f"  • {violation}")

            reason_parts.extend([
                "",
                "To bypass: Add --allow-cross-worktree to your message",
            ])

            return {
                "continue": False,
                "decision": "block",
                "reason": "\n".join(reason_parts)
            }

    except (ValueError, RuntimeError) as e:
        # Worktree detection failed - allow command (fail open)
        return {
            "continue": True,
            "decision": "allow",
            "reason": f"Worktree detection failed: {e}"
        }

    # No violations - allow command
    return {"continue": True, "decision": "allow"}

def suggest_git_restore(
    tool_name: str,
    tool_input: dict,
    input_data: dict
) -> dict:
    """Suggest modern 'git restore' instead of legacy 'git checkout --'.

    Detects patterns like 'git checkout -- file' and suggests the modern
    'git restore file' alternative, which is clearer and purpose-built.

    Args:
        tool_name: Name of the tool being called (e.g., "Bash")
        tool_input: Input parameters for the tool
        input_data: Full hook input data (for accessing bypass flags)

    Returns:
        Dict with:
        - 'continue': True (advisory only, never blocks)
        - 'reason': Suggestion to use git restore (if pattern detected)
        - 'additionalContext': Context to inject into the conversation

    Bypass flag:
        Set '--allow-legacy-checkout' in user message to suppress this suggestion.
    """
    # Only check Bash tools running git commands
    if tool_name != "Bash":
        return {"continue": True, "decision": "allow"}

    # Check for bypass flag in user message
    user_message = input_data.get("user_message", "")
    if "--allow-legacy-checkout" in user_message:
        return {"continue": True, "decision": "allow", "reason": "Legacy checkout suggestion suppressed"}

    command = tool_input.get("command", "")

    # Check for legacy checkout pattern: git checkout -- <file>
    # Match: git checkout -- file1 file2 ...
    checkout_pattern = re.compile(r'git\s+checkout\s+--\s+(.+)$')
    match = checkout_pattern.match(command)

    # Also check: git checkout <commit> -- <file>
    checkout_commit_pattern = re.compile(r'git\s+checkout\s+\S+\s+--\s+(.+)$')
    if not match:
        match = checkout_commit_pattern.match(command)

    if match:
        # Legacy pattern detected - extract files
        files_part = match.group(1).strip()

        # Build concise suggestion
        files = files_part.split()
        restore_cmd = f"git restore {' '.join(files)}"

        suggestion_parts = [
            "💡 Use 'git restore' instead of 'git checkout --'",
            "",
            f"Suggested: {restore_cmd}",
            "",
            "Why: Purpose-built for restoring files, safer than checkout",
            "",
            "To suppress: Add --allow-legacy-checkout to your message",
        ]

        return {
            "continue": True,
            "decision": "allow",
            "reason": "\n".join(suggestion_parts),
            "additionalContext": "\n".join(suggestion_parts)
        }

    # No legacy pattern detected
    return {"continue": True, "decision": "allow"}

@track_hook_performance("PreToolUse")
@hook_main
def main():
    # Read input from stdin
    input_data = json.loads(sys.stdin.read())

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # WORKTREE CROSS-CONTAMINATION CHECK
    # Blocks git operations AND Edit/Write targeting files outside current worktree
    worktree_check = check_worktree_cross_contamination(tool_name, tool_input, input_data)
    if not worktree_check.get("continue", True):
        # Block the operation
        output = {
            "allowed": False,
            "reason": worktree_check.get("reason", "Cross-worktree access detected"),
            "decision": worktree_check.get("decision", "block")
        }
        print(json.dumps(output))
        return 2  # Exit code 2 = block

    # GIT RESTORE SUGGESTION (Component 2, Task 2)
    # Suggests modern 'git restore' instead of legacy 'git checkout --'
    restore_suggestion = suggest_git_restore(tool_name, tool_input, input_data)
    if restore_suggestion.get("additionalContext"):
        # Add suggestion to output (advisory, doesn't block)
        # We'll merge this with the main output later
        pass  # Suggestion handled via additionalContext in final output

    # Only check git commit commands
    if tool_name != "Bash":
        print(json.dumps({"decision": "approve"}))
        return 0

    command = tool_input.get("command", "")

    # Check if this is a git commit
    is_git_commit = (
        "git commit" in command or
        "git merge" in command or
        ("sl" in command and ("commit" in command or "amend" in command))
    )

    # If not a git commit but we have a restore suggestion, show it
    if not is_git_commit:
        if restore_suggestion.get("additionalContext"):
            # Show the suggestion even for non-commit commands
            print(json.dumps({
                "allowed": True,
                "additionalContext": restore_suggestion["additionalContext"]
            }))
            return 0
        else:
            print(json.dumps({"decision": "approve"}))
            return 0

    # Clean up stale index.lock before running any git commands
    ensure_fresh_index()

    # Get git status
    status = get_git_status()

    # Collect things we might have forgotten
    forgettables = {}

    # Check staged files for forgettables
    staged_forgettables = check_forgettables(status["staged_files"])
    if staged_forgettables:
        forgettables["Staged"] = staged_forgettables

    # Check modified but unstaged files (did we forget to stage?)
    if status["modified_files"]:
        forgettables["Modified (not staged)"] = status["modified_files"][:5]

    # Check for untracked tests
    untracked_tests = check_untracked_tests(status["untracked_files"])
    if untracked_tests:
        forgettables["Untracked tests"] = untracked_tests

    # Check for suspicious files
    all_files = status["staged_files"] + status["modified_files"] + status["untracked_files"]
    suspicious = check_suspicious(all_files)
    if suspicious:
        forgettables["Suspicious"] = suspicious

    # Format message
    message = format_check_message(forgettables)

    output = {
        "allowed": True,
        "branch": status["branch"],
        "staged_count": len(status["staged_files"]),
        "modified_count": len(status["modified_files"]),
        "untracked_count": len(status["untracked_files"]),
        "checks": forgettables,
        "message": message,
    }

    # Add git restore suggestion if available (from earlier check)
    if restore_suggestion.get("additionalContext"):
        output["additionalContext"] = restore_suggestion["additionalContext"]

    print(json.dumps(output))
    return 0

if __name__ == "__main__":
    sys.exit(main())
