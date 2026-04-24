#!/usr/bin/env python3
"""
PreToolUse Git Auto-Stage Hook v1.0
====================================

Runs BEFORE rm, del, rmdir, Remove-Item, or move commands.
Auto-stages target files to git so they survive in git history
even after deletion.

Philosophy: Prevention > Recovery. A file in git history is
never truly lost. Auto-staging before deletion means /recover's
git source always has the latest committed state.

Behavior:
  - Detects deletion/move commands (rm, del, Remove-Item, move, mv)
  - Identifies target files
  - Runs: git add <target> for tracked files
  - Exits 0 (allow) — does NOT block the deletion
  - Advisory output shows what was staged

Windows support: rm, del, rmdir, Remove-Item, move, mv all handled.
Unix support: rm, del, rmdir (via MSYS2/Git Bash on Windows).

Exit codes:
  0 = allowed (staged or nothing to stage)
  2 = blocked (only if critical error, not for normal operation)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from __lib.hook_base import hook_main


# =============================================================================
# CONFIGURATION
# =============================================================================

FILE_THRESHOLD = 100  # Max files to stage in one operation (safety limit)

# Patterns for deletion/move commands
DELETE_PATTERNS = [
    # Unix (Git Bash on Windows)
    r"\brm\s+",  # rm -rf, rm -r, etc.
    r"\bdel\s+",  # del /f /q
    r"\brmdir\s+",  # rmdir /s
    # PowerShell
    r"\bRemove-Item\s+",  # Remove-Item -Path X -Recurse
    r"\brm\s+",  # rm alias in PowerShell
    # Move (source gets deleted/overwritten)
    r"\bmove\s+",  # move oldpath newpath
    r"\bmv\s+",  # mv oldpath newpath
    r"\brename\s+",  # rename oldpath newpath
    # Copy then delete (move semantics)
    r"\bcp\s+.*\s+.*&&\s*rm\s+",  # cp + rm (move semantics)
]

COMPILED_DELETE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in DELETE_PATTERNS]

# Directories that are always safe to skip (build artifacts, caches)
SKIP_PATTERNS = [
    r"__pycache__",
    r"node_modules",
    r"\.git/",
    r"\.pyc$",
    r"\bdist\b",
    r"\bbuild\b",
    r"\.tmp\b",
    r"\.backup\b",
    r"\bvenv\b",
    r"\benv\b",
    r"\.mypy_cache\b",
    r"\.pytest_cache",
    r"\.ruff_cache",
    r"\.hypothesis",
]

SKIP_COMPILED = [re.compile(p, re.IGNORECASE) for p in SKIP_PATTERNS]

# Files to never stage (safety)
NEVER_STAGE_PATTERNS = [
    r"\.env$",
    r"\.key$",
    r"\.pem$",
    r"secrets",
    r"credentials",
    r"password",
    r"\.token",
]

NEVER_STAGE_COMPILED = [re.compile(p, re.IGNORECASE) for p in NEVER_STAGE_PATTERNS]


# =============================================================================
# HELPERS
# =============================================================================


def run_git_cmd(cmd: list[str], cwd: str | None = None) -> tuple[str, str, int]:
    """Run git command and return stdout, stderr, exit code."""
    import sys as _sys

    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=cwd,
        creationflags=creation_flags,
    )
    return result.stdout, result.stderr, result.returncode


def find_git_root(start_path: Path | None = None) -> Path | None:
    """Find the git repository root."""
    if start_path is None:
        start_path = Path.cwd()

    repo_root = start_path
    while repo_root != repo_root.parent and not (repo_root / ".git").exists():
        repo_root = repo_root.parent

    if (repo_root / ".git").exists():
        return repo_root
    return None


def is_tracked_by_git(file_path: Path, git_root: Path) -> bool:
    """Check if a file is tracked by git (staged or committed)."""
    rel_path = file_path.relative_to(git_root) if file_path.is_relative_to(git_root) else file_path

    # Check if file is in the index (staged)
    stdout, _, rc = run_git_cmd(["git", "ls-files", "--stage", "--", str(rel_path)], cwd=str(git_root))
    if rc == 0 and stdout.strip():
        return True

    # Check if file is in HEAD (committed)
    stdout, _, rc = run_git_cmd(["git", "ls-tree", "-r", "--name-only", "HEAD", "--", str(rel_path)], cwd=str(git_root))
    if rc == 0 and stdout.strip():
        return True

    return False


def should_skip_path(path_str: str) -> bool:
    """Check if path should be skipped (safe directories)."""
    for pattern in SKIP_COMPILED:
        if pattern.search(path_str):
            return True
    return False


def should_never_stage(path_str: str) -> bool:
    """Check if path should never be auto-staged (secrets)."""
    for pattern in NEVER_STAGE_COMPILED:
        if pattern.search(path_str):
            return True
    return False


def extract_delete_targets(command: str) -> list[str]:
    """Extract target paths from a deletion/move command.

    Returns list of target paths (may be empty).
    """
    targets = []

    # PowerShell: Remove-Item -Path <path> or Remove-Item <path>
    ps_match = re.search(r"\bRemove-Item\s+(?:-(?:Path|LiteralPath|Force|Recurse)\s+)*([^\s;|]+)", command, re.IGNORECASE)
    if ps_match:
        path = ps_match.group(1).strip().strip("\"'")
        if path and not path.startswith("-"):
            targets.append(path)
        # Also check for -Path parameter value
        path_param = re.search(r"-Path\s+([^\s;|]+)", command, re.IGNORECASE)
        if path_param:
            p = path_param.group(1).strip().strip("\"'")
            if p and not p.startswith("-"):
                if p not in targets:
                    targets.append(p)

    # move, mv, rename
    move_match = re.search(r"\b(?:move|mv|rename)\s+([^\s]+)\s+([^\s]+)", command, re.IGNORECASE)
    if move_match:
        targets.append(move_match.group(1).strip().strip("\"'"))

    # rm, del, rmdir patterns
    for pattern in COMPILED_DELETE_PATTERNS:
        match = pattern.search(command)
        if match:
            rest = command[match.end() :].strip()
            parts = rest.split()
            for part in parts:
                cleaned = part.strip().strip("\"'")
                if cleaned and not cleaned.startswith("-") and cleaned not in ("\\", "/"):
                    if should_skip_path(cleaned):
                        continue
                    targets.append(cleaned)

    return targets


def auto_stage_files(targets: list[str], git_root: Path) -> tuple[list[str], list[str], list[str]]:
    """Stage files to git.

    Returns:
        (staged, skipped, errors)
        - staged: files successfully staged
        - skipped: files skipped (not tracked or skipped)
        - errors: files that failed to stage
    """
    staged = []
    skipped = []
    errors = []

    for target in targets[:FILE_THRESHOLD]:  # Safety limit
        try:
            path = Path(target).resolve()

            # Check for secret files — never stage
            if should_never_stage(str(path)):
                skipped.append(f"(secrets) {target}")
                continue

            # Check if path exists
            if not path.exists():
                skipped.append(f"(not found) {target}")
                continue

            # Check if tracked
            if not is_tracked_by_git(path, git_root):
                skipped.append(f"(not tracked) {target}")
                continue

            # Stage the file
            stdout, stderr, rc = run_git_cmd(["git", "add", "--", str(path)], cwd=str(git_root))

            if rc == 0:
                staged.append(str(path))
            else:
                errors.append(f"{target}: {stderr[:100]}")

        except Exception as e:
            errors.append(f"{target}: {str(e)}")

    return staged, skipped, errors


# =============================================================================
# HOOK LOGIC
# =============================================================================


def run(data: dict) -> dict | None:
    """In-process execution entry point.

    Returns:
        - None: allow (no deletion detected or nothing to stage)
        - dict with additionalContext: allow with advisory output
        - dict with decision=block: block (critical error)
    """
    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        return None

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        return None

    # Check if bypass is set
    if os.environ.get("GIT_AUTO_STAGE_BYPASS", "0") == "1":
        return None
    if re.search(r"\bGIT_AUTO_STAGE_BYPASS\s*=\s*1\b", command):
        return None

    # Detect deletion/move command
    is_deletion = any(pattern.search(command) for pattern in COMPILED_DELETE_PATTERNS)
    if not is_deletion:
        return None

    # Extract targets
    targets = extract_delete_targets(command)
    if not targets:
        return None

    # Find git root
    git_root = find_git_root()
    if not git_root:
        return None  # Not in a git repo — nothing to stage

    # Auto-stage
    staged, skipped, errors = auto_stage_files(targets, git_root)

    # Build advisory output
    if not staged:
        return None  # Nothing to stage — allow silently

    lines = ["\n🔧 Git Auto-Stage (pre-deletion safety net):"]
    lines.append(f"   Staged {len(staged)} file(s) to git before deletion")

    if skipped:
        skipped_sample = skipped[:5]
        lines.append(f"   Skipped: {', '.join(s.get('target', s) for s in skipped_sample[:3])}")
        if len(skipped) > 5:
            lines.append(f"   ... and {len(skipped) - 5} more")

    if errors:
        lines.append(f"   ⚠️ Errors staging {len(errors)} file(s): {errors[0]}")

    lines.append("")

    return {
        "decision": "allow",
        "additionalContext": "\n".join(lines),
    }


# =============================================================================
# SUBPROCESS ENTRY POINT
# =============================================================================


@hook_main
def main() -> int:
    """Subprocess entry point."""
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        return 0

    result = run(data)
    if result and result.get("decision") == "block":
        print(json.dumps(result), file=sys.stderr)
        return 2

    if result and result.get("additionalContext"):
        print(json.dumps({
            "allowed": True,
            "additionalContext": result["additionalContext"],
        }))
    else:
        print(json.dumps({"allowed": True}))

    return 0


if __name__ == "__main__":
    sys.exit(main())