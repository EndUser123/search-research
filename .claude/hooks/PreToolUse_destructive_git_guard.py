#!/usr/bin/env python3
"""
PreToolUse: Git Safety Guard

Prevents inappropriate git usage by blocking:
1. Destructive operations (data loss)
2. File/folder creation operations (git is not a file system tool)

Requires explicit confirmation with --i-understand-irreversible flag.

Protects both local git operations and GitHub CLI (gh) operations.
"""

import json
import sys


def check_bash_command(command: str) -> dict | None:
    """Check if bash command is destructive git or GitHub operation."""
    cmd_start = command.strip().split()[0].lower() if command.strip().split() else ""

    if cmd_start == "git":
        return check_git_command(command.strip())
    elif cmd_start == "gh":
        return check_gh_command(command.strip())

    return None


def check_git_command(command: str) -> dict | None:
    """Check if command is destructive or inappropriate local git operation."""
    if not command.startswith("git"):
        return None

    # Parse git command
    parts = command.split()
    if len(parts) < 2:
        return None

    git_subcommand = parts[1].lower()

    # Destructive operations (data loss)
    DESTRUCTIVE_OPS = {
        "reset": {
            "danger_flags": ["--hard"],
            "description": "Discard all uncommitted changes in working directory",
            "severity": "CRITICAL",
            "category": "destructive"
        },
        "clean": {
            "danger_flags": ["-f", "-fd", "-fXd", "-fxd"],
            "description": "Delete untracked files",
            "severity": "HIGH",
            "category": "destructive"
        },
        "stash": {
            "danger_subcommands": {"drop", "clear"},
            "description": "Permanently delete stash entries",
            "severity": "HIGH",
            "category": "destructive"
        },
        "rebase": {
            "danger_flags": ["--onto"],
            "description": "Rewrite git history (potential data loss)",
            "severity": "MEDIUM",
            "category": "destructive"
        }
    }

    # Creation operations (git should not be used as file system tool)
    CREATIVE_OPS = {
        "worktree": {
            "danger_subcommands": {"add"},
            "description": "Create new git worktree directory",
            "severity": "HIGH",
            "category": "creative",
            "alternative": "Use /git worktree command or create worktree via Claude Code worktree feature"
        },
        "init": {
            "description": "Initialize new git repository (creates .git directory)",
            "severity": "HIGH",
            "category": "creative",
            "alternative": "Use 'git init' in terminal directly if you truly need a new repo"
        },
        "clone": {
            "description": "Clone repository (creates directory)",
            "severity": "HIGH",
            "category": "creative",
            "alternative": "Use gh repo clone or clone in terminal directly"
        }
    }

    # Branch creation is special - it's sometimes okay but requires explicit intent
    BRANCH_OPS = {
        "checkout": {
            "danger_flags": ["-b"],
            "description": "Create and checkout new branch",
            "severity": "MEDIUM",
            "category": "creative",
            "alternative": "Use /git workflow or git switch -c explicitly"
        }
    }

    # Check all operation types
    all_ops = {**DESTRUCTIVE_OPS, **CREATIVE_OPS, **BRANCH_OPS}

    if git_subcommand not in all_ops:
        return None

    op_config = all_ops[git_subcommand]

    # Check if dangerous flags are present
    if "danger_flags" in op_config:
        has_danger_flag = any(flag in command for flag in op_config["danger_flags"])
        if not has_danger_flag:
            return None
    elif "danger_subcommands" in op_config:
        if len(parts) < 3 or parts[2].lower() not in op_config["danger_subcommands"]:
            return None

    # Extract target for better warning messages
    target = ""
    if git_subcommand == "worktree" and len(parts) >= 4:
        target = parts[3]  # git worktree add <path> <branch>
    elif git_subcommand == "clone" and len(parts) >= 3:
        target = parts[2]  # git clone <url>
    elif git_subcommand == "checkout" and "-b" in command:
        # Find the branch name after -b
        try:
            b_idx = parts.index("-b")
            if b_idx + 1 < len(parts):
                target = parts[b_idx + 1]
        except ValueError:
            pass
    elif git_subcommand == "init" and len(parts) >= 3:
        target = parts[2]  # git init <directory>

    return {
        "command": command.strip(),
        "subcommand": git_subcommand,
        "severity": op_config["severity"],
        "description": op_config["description"],
        "category": op_config["category"],
        "alternative": op_config.get("alternative", ""),
        "target": target,
        "operation_type": "git"
    }


def check_gh_command(command: str) -> dict | None:
    """Check if command is destructive GitHub CLI operation."""
    if not command.startswith("gh"):
        return None

    # Parse gh command
    parts = command.split()
    if len(parts) < 2:
        return None

    gh_subcommand = parts[1].lower()

    # Destructive GitHub CLI operations
    DESTRUCTIVE_GH_OPS = {
        "repo": {
            "danger_subcommands": {"delete"},
            "description": "Permanently delete GitHub repository",
            "severity": "CRITICAL"
        },
        "api": {
            "danger_flags": ["--method DELETE", "--method=DELETE"],
            "description": "DELETE request to GitHub API (destructive operation)",
            "severity": "HIGH"
        },
        "org": {
            "danger_subcommands": {"delete"},
            "description": "Permanently delete GitHub organization",
            "severity": "CRITICAL"
        },
        "release": {
            "danger_subcommands": {"delete"},
            "description": "Permanently delete GitHub release",
            "severity": "HIGH"
        },
        "gist": {
            "danger_subcommands": {"delete"},
            "description": "Permanently delete GitHub gist",
            "severity": "MEDIUM"
        }
    }

    if gh_subcommand not in DESTRUCTIVE_GH_OPS:
        return None

    op_config = DESTRUCTIVE_GH_OPS[gh_subcommand]

    # Check if dangerous flags are present
    if "danger_flags" in op_config:
        has_danger_flag = any(flag in command for flag in op_config["danger_flags"])
        if not has_danger_flag:
            return None
    elif "danger_subcommands" in op_config:
        if len(parts) < 3 or parts[2].lower() not in op_config["danger_subcommands"]:
            return None

    # Extract target for better warning messages
    target = ""
    if gh_subcommand in ("repo", "org", "release", "gist") and len(parts) >= 4:
        # Format: gh <subcommand> <delete> <target>
        target = parts[3]
    elif gh_subcommand == "api" and "--method" in command:
        # Try to extract API endpoint
        api_idx = parts.index("api") if "api" in parts else -1
        if api_idx >= 0 and api_idx + 1 < len(parts):
            endpoint = parts[api_idx + 1]
            target = f"endpoint: {endpoint}"

    return {
        "command": command.strip(),
        "subcommand": gh_subcommand,
        "severity": op_config["severity"],
        "description": op_config["description"],
        "target": target,
        "operation_type": "github"
    }

def get_affected_files(command: str) -> list[str]:
    """Get list of files that would be affected by the command."""
    import subprocess

    try:
        # Get list of modified/untracked files from current directory
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return []

        affected = []
        for line in result.stdout.strip().split("\n"):
            if line:
                # Parse porcelain output: XY filename
                status = line[:2]
                filepath = line[3:]
                if filepath:
                    affected.append(f"{status} {filepath}")

        return affected
    except Exception:
        return []

def main():
    # Read command from stdin
    input_data = json.loads(sys.stdin.read())
    # PreToolUse protocol: command is nested under tool_input
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")

    # Check if this is a protected git or GitHub command
    danger_info = check_bash_command(command)
    if not danger_info:
        sys.exit(0)  # Allow safe commands

    # Get affected files (for destructive git operations only)
    affected_files = []
    if danger_info.get("operation_type") == "git" and danger_info.get("category") == "destructive":
        affected_files = get_affected_files(command)

    # Build warning message
    severity_icon = {
        "CRITICAL": "☢️",
        "HIGH": "⚠️",
        "MEDIUM": "⚡"
    }

    operation_type_label = "GIT" if danger_info.get("operation_type") == "git" else "GITHUB CLI"
    category_label = danger_info.get("category", "unknown").upper()

    # Build concise warning message
    if danger_info.get("category") == "creative":
        # Creation operations
        alternative = danger_info.get('alternative', 'Use appropriate file system tools')
        warning = f"❌ {danger_info['description']}\n\nBetter alternative: {alternative}\n\nTo proceed: {danger_info['command']} --i-understand-irreversible"
    else:
        # Destructive operations
        if danger_info.get("operation_type") == "git":
            # Git destructive operations
            if danger_info['subcommand'] == 'reset' and 'reset --hard' in command:
                # Special message for reset --hard with path-scoped example
                warning = f"❌ {danger_info['description']}\n\nSafe usage: git reset --hard <commit> -- -- <file-path>\n\nTo proceed: {danger_info['command']} --i-understand-irreversible"
            else:
                warning = f"❌ {danger_info['description']}\n\nTo proceed: {danger_info['command']} --i-understand-irreversible"
        else:
            # GitHub CLI operations
            warning = f"❌ {danger_info['description']}\n\nTo proceed: {danger_info['command']} --i-understand-irreversible"

    # Check for explicit approval
    if "--i-understand-irreversible" not in command and "DESTROY_ALL" not in command:
        # Print blocking reason to stdout (PreToolUse standard)
        block_msg = (
            f"{warning}\n"
            "❌ BLOCKED: Missing explicit approval flag --i-understand-irreversible\n"
            "Add this flag to confirm you understand this operation."
        )
        print(json.dumps({"decision": "block", "reason": block_msg, "blocking_hook": "PreToolUse_destructive_git_guard.py"}))
        sys.exit(2)

    # Check for scope specification (pathspec) - only for destructive git operations
    if danger_info.get("operation_type") == "git" and danger_info.get("category") == "destructive":
        if "--" not in command and danger_info["severity"] == "CRITICAL":
            # Claude Code treats stderr as hook error - silence warnings
            pass

    sys.exit(0)


def run(data: dict) -> dict | None:
    """In-process execution entry point for PreToolUse router.

    Returns block dict or None (allow).
    """
    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        return None

    danger_info = check_bash_command(command)
    if not danger_info:
        return None

    # Check for explicit approval
    if "--i-understand-irreversible" in command or "DESTROY_ALL" in command:
        return None

    # Build concise block message
    if danger_info.get("category") == "creative":
        alternative = danger_info.get('alternative', 'Use appropriate file system tools')
        block_msg = f"❌ {danger_info['description']}\n\nBetter alternative: {alternative}\n\nTo proceed: {danger_info['command']} --i-understand-irreversible"
    else:
        # Destructive operations
        if danger_info.get("operation_type") == "git":
            if danger_info['subcommand'] == 'reset' and 'reset --hard' in command:
                block_msg = f"❌ {danger_info['description']}\n\nSafe usage: git reset --hard <commit> -- -- <file-path>\n\nTo proceed: {danger_info['command']} --i-understand-irreversible"
            else:
                block_msg = f"❌ {danger_info['description']}\n\nTo proceed: {danger_info['command']} --i-understand-irreversible"
        else:
            block_msg = f"❌ {danger_info['description']}\n\nTo proceed: {danger_info['command']} --i-understand-irreversible"

    return {
        "decision": "block",
        "reason": block_msg,
        "blocking_hook": "PreToolUse_destructive_git_guard.py",
    }


if __name__ == "__main__":
    main()
