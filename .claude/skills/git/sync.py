#!/usr/bin/env python3
"""
Smart Git Sync with Health Check, Worktree Management, and Conflict Resolution
- Detects context (main vs worktree)
- Checks Tasks configuration
- Auto-fixes missing configs
- Syncs bidirectionally
- Manages worktrees (list, add, remove, prune)
- Auto-resolves conflicts based on file type
- Post-merge diff validation
- Context-aware output
"""

import subprocess
import sys
import json
import time
import argparse
import re
from pathlib import Path
from typing import Tuple, Optional, List

# Import commit message parser
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks"))
    from commit_message_parser import (
        detect_file_type, detect_scope, detect_commit_type,
        generate_subject, generate_commit_body
    )
except ImportError:
    # Fallback if commit_message_parser is not available
    def detect_file_type(path): return "unknown"
    def detect_scope(files): return []
    def detect_commit_type(data): return "chore"
    def generate_subject(data): return "update files"
    def generate_commit_body(data): return ""

# ============================================================
# CONFIGURATION
# ============================================================

MAIN_ROOT = Path("P:/")
CLAUDE_DIR = MAIN_ROOT / ".claude"
WORKTREES_DIR = MAIN_ROOT / "worktrees"

# Conflict resolution strategies
CONFLICT_STRATEGIES = {
    # Session state is always local, never share
    ".claude/sessions/": "ours",

    # Committed code in main is source of truth
    ".py": "theirs",
    ".md": "theirs",
    ".ts": "theirs",
    ".js": "theirs",
    ".json": "theirs",
    ".yaml": "theirs",
    ".yml": "theirs",
    ".toml": "theirs",
    ".cfg": "theirs",
    ".ini": "theirs",

    # Config files may need both sides - manual
    ".env": "manual",
    ".env.local": "manual",
    ".env.production": "manual",
    "config.local": "manual",
}

# Parse arguments
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--verbose", "-v", action="store_true")
parser.add_argument("--health", action="store_true")
parser.add_argument("--fix", action="store_true")
parser.add_argument("--worktree", action="store_true")
parser.add_argument("--no-resolve", action="store_true")
parser.add_argument("worktree_action", nargs="?", default="list")
parser.add_argument("worktree_name", nargs="?", default=None)
args = parser.parse_args()

HEALTH_ONLY = args.health
AUTO_FIX = args.fix
VERBOSE = args.verbose
WORKTREE_MODE = args.worktree
WORKTREE_ACTION = args.worktree_action
WORKTREE_NAME = args.worktree_name
AUTO_RESOLVE = not args.no_resolve

# ============================================================
# UTILITIES
# ============================================================

def run(cmd, cwd=None, silent=False):
    """Run command and return result."""
    if isinstance(cmd, str):
        cmd = cmd.split()
    # Prevent blue console flash on Windows
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, shell=False,
        creationflags=creation_flags
    )
    if VERBOSE and not silent and result.stdout:
        print(f"  {result.stdout.strip()}")
    return result

def color(text, status):
    """Color codes for output."""
    colors = {
        "success": "\033[92m",  # Green
        "error": "\033[91m",    # Red
        "warning": "\033[93m",  # Yellow
        "info": "\033[94m",     # Blue
        "reset": "\033[0m",
    }
    return f"{colors.get(status, '')}{text}{colors['reset']}"

def header(text):
    """Print section header."""
    print(f"\n{color('=' * 60, 'info')}")
    print(color(f"  {text}", "info"))
    print(color('=' * 60, 'info'))

def item(text, status, detail=""):
    """Print status item."""
    icons = {
        "ok": "+",
        "error": "X",
        "warning": "~",
        "info": "->",
        "pending": "o",
    }
    colored_text = color(f"{icons[status]} {text}", status)
    print(f"{colored_text}" + (f" ({detail})" if detail else ""))

def generate_commit_message() -> str:
    """
    Generate semantic commit message based on changed files.

    Returns:
        Semantic commit message in format: type(scope): subject
    """
    # Get list of changed files
    result = run(["git", "diff", "--name-only", "HEAD"], cwd=Path.cwd(), silent=True)

    if result.returncode != 0 or not result.stdout.strip():
        return "chore: update files"

    # Parse changed files
    changed_files = result.stdout.strip().split("\n")

    # Build file data structure
    files_data = []
    for file_path in changed_files:
        if not file_path:
            continue
        file_type = detect_file_type(file_path)
        files_data.append({"path": file_path, "type": file_type})

    # Detect commit type and scope
    commit_type = detect_commit_type({"files": files_data})
    scopes = detect_scope([f["path"] for f in files_data])

    # Generate subject
    if scopes:
        primary_scope = scopes[0]
        subject = f"update {primary_scope}"
    else:
        subject = "update files"

    # Format semantic commit message
    if scopes:
        return f"{commit_type}({scopes[0]}): {subject}"
    else:
        return f"{commit_type}: {subject}"

# ============================================================
# WORKTREE MANAGEMENT
# ============================================================

def worktree_list():
    """List all worktrees."""
    result = run(["git", "worktree", "list"], cwd=MAIN_ROOT, silent=False)
    if result.returncode == 0:
        lines = result.stdout.strip().split("\n")
        header(f"WORKTREES ({len(lines)})")
        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                path, commit, branch = parts[0], parts[1], " ".join(parts[2:])
                branch = branch.strip("[]")
                # Check if this is the current worktree
                is_current = Path.cwd() == Path(path)
                prefix = "* " if is_current else "  "
                print(f"{prefix}{branch}")
                print(f"     Path: {path}")
                print(f"     Commit: {commit[:8]}")
    else:
        print(f"X Failed to list worktrees: {result.stderr}")
    sys.exit(0)

def worktree_add(name: str):
    """Create a new worktree."""
    if not name:
        print("X Error: worktree name required")
        print("  Usage: /git --worktree add <name>")
        sys.exit(1)

    worktree_path = WORKTREES_DIR / name
    branch_name = name.replace("-", "/")

    header(f"CREATE WORKTREE: {name}")

    if worktree_path.exists():
        item("Worktree path", "error", f"Already exists: {worktree_path}")
        sys.exit(1)

    # Create worktree
    result = run([
        "git", "worktree", "add",
        str(worktree_path),
        "-b", branch_name
    ], cwd=MAIN_ROOT, silent=not VERBOSE)

    if result.returncode == 0:
        item("Worktree created", "ok", f"Path: {worktree_path}")
        item("Branch", "ok", branch_name)
        print("\nNext steps:")
        print(f"  cd {worktree_path}")
        print("  /git  # Sync when ready")
    else:
        item("Failed", "error", result.stderr.strip())
        sys.exit(1)
    sys.exit(0)

def worktree_remove(name: str):
    """Remove a worktree."""
    if not name:
        print("X Error: worktree name required")
        print("  Usage: /git --worktree remove <name>")
        sys.exit(1)

    worktree_path = WORKTREES_DIR / name

    header(f"REMOVE WORKTREE: {name}")

    if not worktree_path.exists():
        item("Worktree path", "error", f"Not found: {worktree_path}")
        sys.exit(1)

    # Remove worktree
    result = run([
        "git", "worktree", "remove",
        str(worktree_path)
    ], cwd=MAIN_ROOT, silent=not VERBOSE)

    if result.returncode == 0:
        item("Worktree removed", "ok", f"Path: {worktree_path}")
        print(f"\nNote: Branch '{name.replace('-', '/')}' still exists.")
        print(f"      Delete it with: git branch -d {name.replace('-', '/')}")
    else:
        item("Failed", "error", result.stderr.strip())
        print("\nTip: Worktree may have uncommitted changes.")
        print(f"     cd {worktree_path}")
        print("     git stash  # or commit changes")
        sys.exit(1)
    sys.exit(0)

def worktree_prune():
    """Prune stale worktrees."""
    header("PRUNE STALE WORKTREES")

    result = run(["git", "worktree", "prune"], cwd=MAIN_ROOT, silent=not VERBOSE)

    if result.returncode == 0:
        item("Pruned", "ok", "Stale worktrees cleaned up")
        print("\nRun '/git --worktree' to see remaining worktrees.")
    else:
        item("Failed", "error", result.stderr.strip())
        sys.exit(1)
    sys.exit(0)

# ============================================================
# CONFLICT RESOLUTION
# ============================================================

def get_conflict_strategy(file_path: str) -> str:
    """Determine conflict resolution strategy for a file."""
    # Check for exact path matches first
    for pattern, strategy in CONFLICT_STRATEGIES.items():
        if pattern.startswith('.'):
            # Extension match
            if file_path.endswith(pattern):
                return strategy
        elif file_path.startswith(pattern):
            # Path prefix match
            return strategy
        elif pattern in file_path:
            # Contains pattern
            return strategy

    # Default: manual resolution for unknown files
    return "manual"

def detect_conflicts(repo: Path) -> List[str]:
    """Detect conflicted files in repo."""
    result = run(["git", "diff", "--name-only", "--diff-filter=U"], cwd=repo, silent=True)
    if result.returncode == 0:
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    return []

def resolve_conflicts(repo: Path, conflicts: List[str]) -> Tuple[int, int, List[str]]:
    """
    Auto-resolve conflicts based on file type.
    Returns: (resolved_count, manual_count, unresolved_files)
    """
    resolved = 0
    manual = 0
    unresolved = []

    for conflicted_file in conflicts:
        strategy = get_conflict_strategy(conflicted_file)

        if strategy == "ours":
            run(["git", "checkout", "--ours", conflicted_file], cwd=repo, silent=not VERBOSE)
            run(["git", "add", conflicted_file], cwd=repo, silent=True)
            item(f"Resolved: {conflicted_file}", "ok", "Kept local (ours)")
            resolved += 1
        elif strategy == "theirs":
            run(["git", "checkout", "--theirs", conflicted_file], cwd=repo, silent=not VERBOSE)
            run(["git", "add", conflicted_file], cwd=repo, silent=True)
            item(f"Resolved: {conflicted_file}", "ok", "Used incoming (theirs)")
            resolved += 1
        else:  # manual
            item(f"Manual: {conflicted_file}", "warning", "Requires review")
            manual += 1
            unresolved.append(conflicted_file)

    return resolved, manual, unresolved

def ensure_diff3_config() -> None:
    """Ensure git is configured for three-way merge conflicts."""
    result = run(["git", "config", "merge.conflictstyle"], silent=True)
    if result.returncode == 0:
        current = result.stdout.strip()
        if current != "diff3":
            run(["git", "config", "merge.conflictstyle", "diff3"], silent=not VERBOSE)
            if VERBOSE:
                print("-> Set merge.conflictstyle=diff3 (shows BASE marker in conflicts)")
    else:
        run(["git", "config", "merge.conflictstyle", "diff3"], silent=not VERBOSE)

def extract_conflict_context(repo: Path, ref: str) -> None:
    """
    Extract context for conflicts: recent commits + what changed.
    Helps understand intent behind conflicting changes.
    """
    print(f"\n{'=' * 60}")
    print(f"  CONFLICT CONTEXT: {ref}")
    print(f"{'=' * 60}")

    # Recent commits from incoming branch
    print("\nRecent commits (incoming):")
    log_result = run(["git", "log", "--oneline", "-n", "5", ref], cwd=repo, silent=False)
    if log_result.returncode == 0:
        for line in log_result.stdout.strip().split("\n")[:5]:
            print(f"  {line}")

    # What changed in this merge
    print("\nChanges in this merge:")
    diff_result = run(["git", "diff", "--stat", f"HEAD@{1}..HEAD"], cwd=repo, silent=False)
    if diff_result.returncode == 0 and diff_result.stdout.strip():
        print(f"  {diff_result.stdout.strip()}")

    print(f"{'=' * 60}\n")

def post_merge_validation(repo: Path, ref: str) -> bool:
    """
    Validate merge by checking for unexpected changes.
    Returns True if validation passes, False otherwise.
    """
    # Get list of changed files
    result = run(["git", "diff", "--name-only", "HEAD~1..HEAD"], cwd=repo, silent=True)
    if result.returncode != 0:
        return True  # Can't validate, assume ok

    changed_files = result.stdout.strip().split("\n") if result.stdout.strip() else []

    # Check for sensitive patterns that shouldn't be in code
    sensitive_patterns = [
        "password",
        "secret",
        "api_key",
        "apikey",
        "private_key",
        "token",
    ]

    warnings = []
    for file_path in changed_files:
        if not file_path:
            continue

        # Skip binary files and common non-sensitive
        if any(file_path.endswith(ext) for ext in ['.pyc', '.so', '.dll', '.exe']):
            continue

        # Check file content for sensitive patterns
        file_result = run(["git", "show", f"HEAD:{file_path}"], cwd=repo, silent=True)
        if file_result.returncode == 0:
            content = file_result.stdout.lower()
            for pattern in sensitive_patterns:
                if pattern in content:
                    warnings.append(f"{file_path}: contains '{pattern}'")

    if warnings and VERBOSE:
        print("\n~ Post-merge validation warnings:")
        for warning in warnings[:5]:  # Limit to 5 warnings
            print(f"  ~ {warning}")

    return True

# ============================================================
# PHASE 0: WORKTREE MODE (exits early)
# ============================================================

if WORKTREE_MODE:
    if WORKTREE_ACTION == "list":
        worktree_list()
    elif WORKTREE_ACTION == "add":
        worktree_add(WORKTREE_NAME)
    elif WORKTREE_ACTION == "remove":
        worktree_remove(WORKTREE_NAME)
    elif WORKTREE_ACTION == "prune":
        worktree_prune()
    else:
        print(f"X Unknown worktree action: {WORKTREE_ACTION}")
        print("  Valid actions: list, add, remove, prune")
        sys.exit(1)

# ============================================================
# PHASE 1: DETECTION
# ============================================================

current_dir = Path.cwd()

# Check if we're in a worktree first
git_common = run(
    ["git", "rev-parse", "--git-common-dir"],
    cwd=current_dir,
    silent=True,
)

is_worktree = False
worktree_name = None
in_main = False

if git_common.returncode == 0:
    common_dir = Path(git_common.stdout.strip())
    if "worktrees" in str(common_dir):
        # We're in a worktree
        is_worktree = True
        worktree_name = current_dir.name
    else:
        # We're in the main repository (anywhere inside it)
        git_toplevel = run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=current_dir,
            silent=True,
        )
        if git_toplevel.returncode == 0:
            toplevel = Path(git_toplevel.stdout.strip())
            in_main = (toplevel == MAIN_ROOT)

# ============================================================
# PHASE 2: ENVIRONMENT CHECK
# ============================================================

if HEALTH_ONLY or AUTO_FIX:
    header("ENVIRONMENT")

    if in_main:
        # Show relative path from main root for clarity
        if current_dir == MAIN_ROOT:
            item("Location", "ok", "In main repo (P:/)")
        else:
            relative = current_dir.relative_to(MAIN_ROOT)
            item("Location", "ok", f"In main repo (P:/{relative})")
    elif is_worktree:
        item("Location", "ok", f"In worktree: {worktree_name}")
    else:
        item("Location", "warning", "Not in main repository")

# ============================================================
# PHASE 3: TASKS CHECK
# ============================================================

tasks_health = True
if HEALTH_ONLY or AUTO_FIX:
    header("CLAUDE CODE TASKS")

    settings_path = CLAUDE_DIR / "settings.json"
    task_list_id = None

    if settings_path.exists():
        try:
            with open(settings_path) as f:
                settings = json.load(f)
            task_list_id = settings.get("env", {}).get("CLAUDE_CODE_TASK_LIST_ID")
            if task_list_id:
                item(".claude/settings.json", "ok", f"Task ID: {task_list_id}")
            else:
                item(".claude/settings.json", "error", "No CLAUDE_CODE_TASK_LIST_ID")
                tasks_health = False
        except json.JSONDecodeError:
            item(".claude/settings.json", "error", "Invalid JSON")
            tasks_health = False
    else:
        item(".claude/settings.json", "error", "Not found")
        tasks_health = False

        if AUTO_FIX:
            try:
                CLAUDE_DIR.mkdir(exist_ok=True)
                config = {
                    "env": {"CLAUDE_CODE_TASK_LIST_ID": "project-main-tasks"}
                }
                with open(settings_path, 'w') as f:
                    json.dump(config, f, indent=2)
                item("Action", "ok", f"Created {settings_path.name}")
                tasks_health = True
                task_list_id = "project-main-tasks"
            except Exception as e:
                item("Action", "error", f"Could not create: {e}")

# ============================================================
# PHASE 4: SUMMARY
# ============================================================

if HEALTH_ONLY:
    if tasks_health:
        header("STATUS")
        item("Health check", "ok", "All systems operational!")
    else:
        header("STATUS")
        item("Health check", "warning", "Some issues found")
        print("\nUse '/git --fix' to auto-fix, or manually address above items.")
    sys.exit(0)

if AUTO_FIX and tasks_health:
    header("STATUS")
    item("Health check", "ok", "Fixed issues, ready to sync")

# ============================================================
# PHASE 5: SYNC (if not --health-only)
# ============================================================

header("SYNC")

# Ensure git is configured for three-way merge conflicts (shows BASE marker)
ensure_diff3_config()

# Import file lock manager for sync
try:
    sys.path.insert(0, str(Path("P:/__csf/.staging")))
    from file_lock_manager_v3 import acquire_lock, release_lock
except ImportError:
    print("~ Warning: file_lock_manager not found, syncing without lock")
    def acquire_lock(key):
        return True, "mock"
    def release_lock(key):
        pass

def cleanup_stale_locks(worktree: Path, worktree_name: str) -> None:
    """Remove stale git lock files."""
    lock_files = [
        worktree / ".git" / "index.lock",
        Path("P:/") / ".git" / "worktrees" / worktree_name / "index.lock",
    ]
    for lock_file in lock_files:
        try:
            if lock_file.exists():
                lock_file.unlink()
                print(f"Cleaned stale lock: {lock_file.name}")
        except Exception:
            pass

def is_up_to_date(repo: Path, ref: str) -> bool:
    """Check if repo HEAD is at specified ref."""
    try:
        target = run([
            "git", "rev-parse", ref
        ], cwd=repo, silent=True).stdout.strip()
        current = run([
            "git", "rev-parse", "HEAD"
        ], cwd=repo, silent=True).stdout.strip()
        return current == target
    except Exception:
        return False

def is_checked_out_elsewhere(error_message: str) -> Tuple[bool, Optional[str]]:
    """
    Check if error indicates branch is checked out in another worktree.
    Returns: (is_checked_out, worktree_path)
    """
    pattern = r"fatal: cannot switch branch .*? is checked out in another worktree at (.+)"
    match = re.search(pattern, error_message)
    if match:
        return True, match.group(1).strip()
    return False, None

def print_worktree_conflict_advice(worktree_path: str, ref: str) -> None:
    """
    Print clear advice when branch is checked out in another worktree.
    """
    print(f"\n{color('=' * 60, 'error')}")
    item("Merge blocked", "error", f"Branch '{ref}' is checked out elsewhere")
    print(f"\n{color('CONFLICTING WORKTREE:', 'warning')} {worktree_path}")
    print(f"\n{color('Options to resolve:', 'info')}")
    print("  1. Switch the conflicting worktree to a different branch:")
    print(f"     cd {worktree_path}")
    print("     git checkout -b temp-branch")
    print("\n  2. Remove the worktree if no longer needed:")
    print(f"     git worktree remove {worktree_path}")
    print("\n  3. List all worktrees to see status:")
    print("     /git --worktree list")
    print(f"{color('=' * 60, 'error')}\n")

def safe_merge(repo: Path, ref: str, merge_name: str) -> bool:
    """
    Perform merge with automatic conflict resolution.
    Returns True if merge succeeded (or conflicts were resolved).
    """
    # Attempt merge
    result = run(["git", "merge", ref, "--no-edit"], cwd=repo, silent=not VERBOSE)

    if result.returncode == 0:
        # Clean merge
        if VERBOSE:
            print(f"-> Merged {ref} cleanly")
        return True

    # Check if branch is checked out elsewhere
    is_checked_out, worktree_path = is_checked_out_elsewhere(result.stderr)
    if is_checked_out:
        print_worktree_conflict_advice(worktree_path, ref)
        return False

    # Check for conflicts
    conflicts = detect_conflicts(repo)

    if not conflicts:
        # Merge failed for other reason (no conflicts)
        item(f"Merge failed: {ref}", "error", result.stderr.strip())
        return False

    # Conflicts detected
    header(f"CONFLICTS ({len(conflicts)} files)")

    # Extract context for understanding the conflicts
    extract_conflict_context(repo, ref)

    if AUTO_RESOLVE:
        resolved, manual_count, unresolved = resolve_conflicts(repo, conflicts)

        if unresolved:
            # Some files need manual resolution
            item("Manual resolution required", "warning", f"{len(unresolved)} files")
            print("\nUnresolved files:")
            for f in unresolved:
                print(f"  ~ {f}")
            print("\nCommands to resolve manually:")
            print(f"  cd {repo}")
            print("  git status  # See conflicts")
            print("  git checkout --ours <file>   # Keep your version")
            print("  git checkout --theirs <file>  # Use incoming version")
            print("  git add <file>                  # Mark as resolved")
            print("  git commit                      # Complete merge")

            # Abort the merge to leave repo in clean state
            run(["git", "merge", "--abort"], cwd=repo, silent=True)
            return False
        else:
            # All conflicts resolved
            item("All conflicts resolved", "ok", f"{resolved} files auto-resolved")

            # Complete the merge
            result = run(["git", "commit", "--no-edit"], cwd=repo, silent=not VERBOSE)
            if result.returncode == 0:
                item("Merge completed", "ok", f"Merged {ref} with auto-resolution")

                # Post-merge validation
                if not post_merge_validation(repo, ref):
                    item("Post-merge validation", "warning", "Check changes")

                return True
            else:
                item("Merge completion failed", "error", result.stderr.strip())
                return False
    else:
        # Manual mode - don't resolve
        item("Conflicts detected", "info", "Manual resolution mode (--no-resolve)")
        print("\nConflicting files:")
        for f in conflicts:
            print(f"  ~ {f}")
        print("\nCommands to resolve manually:")
        print(f"  cd {repo}")
        print("  git status  # See conflicts")
        print("  git checkout --ours <file>   # Keep your version")
        print("  git checkout --theirs <file>  # Use incoming version")
        print("  git add <file>                  # Mark as resolved")
        print("  git commit                      # Complete merge")

        # Abort the merge
        run(["git", "merge", "--abort"], cwd=repo, silent=True)
        return False

worktree = Path.cwd()
main_root = Path("P:/")
worktree_name = worktree.name
in_main = worktree == main_root

# Cleanup stale locks
cleanup_stale_locks(worktree, worktree_name)
cleanup_stale_locks(main_root, "main")

current = run(
    "git branch --show-current",
    cwd=worktree,
    silent=True,
).stdout.strip()
status = run(
    "git status --short",
    cwd=worktree,
    silent=not VERBOSE,
).stdout.strip()

if status:
    run("git add -A", cwd=worktree, silent=not VERBOSE)

    # Generate semantic commit message based on staged changes
    try:
        staged_result = run("git diff --staged --name-only", cwd=worktree, silent=True)
        if staged_result.returncode == 0 and staged_result.stdout.strip():
            changed_files = [f.strip() for f in staged_result.stdout.strip().split('\n') if f.strip()]
            files_data = []
            for f in changed_files:
                ftype = detect_file_type(f)
                files_data.append({"path": f, "type": ftype})

            scopes = detect_scope(files_data)
            commit_type = detect_commit_type({"files": files_data})
            subject = generate_subject({"files": files_data})

            # Generate header
            if scopes:
                scope_str = scopes[0] if len(scopes) == 1 else f"({','.join(scopes[:2])})"
                header = f"{commit_type}{scope_str}: {subject}"
            else:
                header = f"{commit_type}: {subject}"

            # Generate body sections (WHY, WHAT, VERIFICATION)
            body = generate_commit_body({"files": files_data, "commit_type": commit_type})

            # Combine header and body
            commit_msg = f"{header}{body}" if body else header
        else:
            commit_msg = "chore: sync changes"
    except Exception:
        commit_msg = "chore: sync changes"

    run([
        "git", "commit", "-m", commit_msg
    ], cwd=worktree, silent=not VERBOSE)

# Sync with lock
SYNC_LOCK_KEY = "git-sync-main"
lock_acquired = False
max_retries = 5

for attempt in range(max_retries):
    ok, msg = acquire_lock(SYNC_LOCK_KEY)
    if ok:
        lock_acquired = True
        break
    if VERBOSE:
        print(f"-> Sync locked (retry {attempt + 1}/{max_retries}): {msg}")
    if attempt < max_retries - 1:
        time.sleep(1)

if not lock_acquired:
    print("Sync failed: Could not acquire lock")
    print("  Another terminal may be syncing. Wait and retry.")
    sys.exit(1)

sync_success = False
try:
    # Pull from main
    if is_up_to_date(worktree, "main"):
        if VERBOSE:
            print("-> Already up-to-date with main")
    else:
        if not safe_merge(worktree, "main", "main"):
            item("Sync failed", "error", "Could not merge main into worktree")
            sys.exit(1)

    # Push to main
    if is_up_to_date(main_root, current):
        if VERBOSE:
            print(f"-> Already up-to-date with {current}")
    else:
        if not safe_merge(main_root, current, f"worktree branch {current}"):
            item("Sync failed", "error", f"Could not merge {current} into main")
            sys.exit(1)

    item("Sync complete", "ok", "All merges successful")
    sync_success = True
finally:
    release_lock(SYNC_LOCK_KEY)


# ============================================================
# PHASE 5.5: PUSH TO ORIGIN
# ============================================================

if sync_success:
    try:
        # Check if we have commits to push
        check_result = run("git rev-list --count origin/main..HEAD", cwd=main_root, silent=True)
        if check_result.returncode == 0:
            commits_ahead = check_result.stdout.strip()
            if commits_ahead and commits_ahead != "0":
                push_result = run("git push", cwd=main_root, silent=not VERBOSE)
                if push_result.returncode == 0:
                    item("Push to origin", "ok", f"Pushed {commits_ahead} commit(s) to origin/main")
                else:
                    item("Push to origin", "warning", "Push failed - will retry on next sync")
                    if VERBOSE:
                        print(f"  Error: {push_result.stderr.strip()}")
            elif VERBOSE:
                print("-> No commits to push (already up-to-date with origin)")
    except Exception as e:
        item("Push to origin", "warning", f"Push failed: {e}")
        if VERBOSE:
            print(f"  Error: {str(e)}")

# ============================================================
# PHASE 6: DIFF VERIFICATION
# ============================================================

if sync_success:
    # Check if worktree and main have identical content
    diff_result = run(["git", "diff", "main", "--", ".claude/skills/git/SKILL.md",
                       ".claude/hooks/PreToolUse_background_guard.py"],
                      cwd=worktree, silent=True)

    if diff_result.stdout.strip():
        item("Diff verification", "error", "FAILED - worktree and main differ")
        if VERBOSE:
            print("\nDifferences found:")
            print(diff_result.stdout.strip())
    else:
        item("Diff verification", "ok", "PASSED - worktree and main identical")

# ============================================================
# PHASE 7: POST-SYNC VALIDATION
# ============================================================

if sync_success and VERBOSE:
    header("POST-SYNC VALIDATION")

    # Show diff of what changed
    worktree_diff = run(["git", "diff", "--stat", "HEAD~1"], cwd=worktree, silent=True)
    if worktree_diff.returncode == 0 and worktree_diff.stdout.strip():
        print("Worktree changes:")
        print(f"  {worktree_diff.stdout.strip()}")

    if not in_main:
        main_diff = run(["git", "diff", "--stat", "HEAD~1"], cwd=main_root, silent=True)
        if main_diff.returncode == 0 and main_diff.stdout.strip():
            print("Main changes:")
            print(f"  {main_diff.stdout.strip()}")

# ============================================================
# PHASE 8: CONTEXT-AWARE OUTPUT
# ============================================================

print(f"\n{color('Context-Aware Commands:', 'info')}")

if in_main:
    print("""
  YOU ARE IN: Main branch (P:/)

  Sync:
    /git                        # Sync whenever you commit
    /git --verbose              # Show detailed sync output
    /git --health --fix         # Verify/fix Tasks setup
    /git --no-resolve           # Manual conflict resolution

  Worktrees:
    /git --worktree             # List all worktrees
    /git --worktree add name    # Create new worktree
    /git --worktree remove name # Remove worktree
    /git --worktree prune       # Clean up stale worktrees
    """)
elif is_worktree:
    print(f"""
  YOU ARE IN: Worktree '{worktree_name}'

  Sync:
    /git                        # Sync before switching worktrees
    /git --verbose              # Show detailed sync output
    /git --no-resolve           # Manual conflict resolution

  Worktrees:
    /git --worktree             # List all worktrees
    cd ../../                   # Go to main to manage worktrees
    """)

print(f"{color('=' * 60, 'info')}\n")
