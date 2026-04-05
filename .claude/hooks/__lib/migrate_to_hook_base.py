#!/usr/bin/env python3
"""
Hook Migration Script - Add @hook_main decorator to hooks.

Features:
- AST-based transformation (preserves formatting where possible)
- Pre-migration syntax verification
- Post-migration functional verification
- Dry-run mode for safety
- Rollback on failure
- Skip already-migrated hooks

Usage:
    python migrate_to_hook_base.py --dry-run           # Preview changes
    python migrate_to_hook_base.py --migrate           # Apply changes
    python migrate_to_hook_base.py --verify-only       # Check current state
    python migrate_to_hook_base.py --migrate --file X  # Migrate single file
"""
from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = HOOKS_DIR / ".migration_backup"

# Hooks to skip (already migrated, special cases, or not applicable)
SKIP_HOOKS = {
    # Already migrated
    "PreToolUse_file_lock.py",
    "PostToolUse_router.py",
    # Has finally block - manual migration done
    "Stop_router.py",
    # Infrastructure files (not hooks)
    "cc_diagnostic_logger.py",
    "file_lock_manager.py",
    "hook_tracker.py",
    "buffered_logger.py",
    "terminal_detection.py",
    "tool_sequence_manager.py",
    # Test files
    "test_hook_decorator.py",
}

# Directories to skip
SKIP_DIRS = {
    "__lib",
    "__pycache__",
    ".archive",
    "tests",
    "logs",
    "data",
    "session_data",
    ".state",
    ".locks",
    ".migration_backup",
    "posttooluse",  # Package with __init__.py
    "investigation-ledger",  # Subdirectory hooks
    "damage-control",
    "checkpoint",
    "anti_sycophancy",
}


@dataclass
class MigrationResult:
    file: Path
    status: str  # "migrated", "skipped", "failed", "already_done"
    message: str
    lines_added: int = 0
    lines_removed: int = 0
    transformations: list[str] = None

    def __post_init__(self):
        if self.transformations is None:
            self.transformations = []


def is_hook_file(path: Path) -> bool:
    """Check if file is a hook that should be migrated."""
    if not path.is_file() or path.suffix != ".py":
        return False
    if path.name in SKIP_HOOKS:
        return False
    if path.name.startswith("__"):
        return False
    # Check parent directories
    for parent in path.relative_to(HOOKS_DIR).parents:
        if parent.name in SKIP_DIRS:
            return False
    return True


def check_already_migrated(content: str) -> bool:
    """Check if hook already has @hook_main decorator."""
    return "@hook_main" in content or "from __lib.hook_base import" in content


def check_has_main_function(content: str) -> bool:
    """Check if file has a main() function."""
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                return True
        return False
    except SyntaxError:
        return False


def check_syntax(path: Path) -> tuple[bool, str]:
    """Verify Python syntax is valid."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            capture_output=True,
            timeout=10
        )
        if result.returncode == 0:
            return True, "OK"
        return False, result.stderr.decode()[:200]
    except Exception as e:
        return False, str(e)


def verify_hook_runs(path: Path) -> tuple[bool, str]:
    """Verify hook can execute without crashing."""
    try:
        # Run with empty input - should exit cleanly
        result = subprocess.run(
            [sys.executable, str(path)],
            input=b"{}",
            capture_output=True,
            timeout=5,
            env={
                **dict(__import__("os").environ),
                "CC_DIAGNOSTICS_DIR": "P:/.claude/hooks/logs/diagnostics"
            }
        )
        # Exit code 0 is success, hook should output valid JSON
        stdout = result.stdout.decode().strip()
        if result.returncode == 0:
            # Verify output is valid JSON
            if stdout:
                try:
                    json.loads(stdout)
                    return True, "OK"
                except json.JSONDecodeError:
                    return False, f"Invalid JSON output: {stdout[:100]}"
            return True, "OK (no output)"
        return False, f"Exit code {result.returncode}: {result.stderr.decode()[:100]}"
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def transform_hook(content: str) -> str:
    """Transform hook to use @hook_main decorator."""
    lines = content.split("\n")
    new_lines = []

    # Track state
    found_imports = False
    added_import = False
    in_main = False
    main_indent = ""
    try_depth = 0
    found_main_try = False
    skip_outer_try_except = False
    main_def_found = False
    main_body_start = False
    added_stdin_parse = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Find import section (after docstring, before code)
        if not added_import and stripped.startswith(("import ", "from ")):
            found_imports = True

        # Add our import after last import
        if found_imports and not added_import:
            # Check if next non-empty line is not an import
            next_non_empty = ""
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip():
                    next_non_empty = lines[j].strip()
                    break

            if not next_non_empty.startswith(("import ", "from ")):
                new_lines.append(line)
                # Add import and blank line
                new_lines.append("")
                new_lines.append("# Import auto-logging decorator")
                # Determine correct import path based on file location
                new_lines.append("from __lib.hook_base import hook_main")
                added_import = True
                i += 1
                continue

        # Find main() function definition
        if stripped.startswith("def main("):
            in_main = True
            main_def_found = True
            main_indent = line[:len(line) - len(line.lstrip())]
            # Add decorator before def main
            new_lines.append(f"{main_indent}@hook_main")
            new_lines.append(line)
            i += 1
            continue

        # Inside main(), detect outer try block pattern
        if in_main and not found_main_try:
            if stripped == "try:":
                # Check if this is the outer try wrapping most of main()
                # Look ahead for except Exception pattern at end
                found_main_try = True
                try_depth = 1
                i += 1
                continue  # Skip the try: line

        # Track try depth when we found the outer try
        if found_main_try:
            if stripped == "try:":
                try_depth += 1
            elif stripped.startswith("except") and try_depth == 1:
                # Check if it's a generic except Exception handler (not specific)
                if "except Exception" in stripped or "except:" == stripped:
                    # This is the outer except - skip it and its block
                    skip_outer_try_except = True
                    i += 1
                    continue
                # Otherwise it's a specific handler - preserve it
                try_depth -= 1
            elif stripped.startswith(("except", "finally")):
                if try_depth > 1:
                    try_depth -= 1

        # Skip lines in outer except block
        if skip_outer_try_except:
            # Detect end of except block (next line at main indent level)
            if line and not line[0].isspace():
                skip_outer_try_except = False
                in_main = False
            elif stripped and not stripped.startswith((" ", "\t")) and main_indent and line.startswith(main_indent) and not line.startswith(main_indent + " "):
                skip_outer_try_except = False
                in_main = False
            else:
                i += 1
                continue

        # Add set_hook_context and stdin parsing at start of main body
        if in_main and main_def_found and not added_stdin_parse:
            # First non-empty line after def main is the start of body
            if stripped and not line.startswith(main_indent):
                # Not in main anymore
                in_main = False
            elif stripped and (line.startswith(main_indent + "    ") or line.startswith(main_indent + "\t")):
                # This is the first line of main's body
                main_body_start = True
                # Add set_hook_context call
                new_lines.append(f"{main_indent}    # Set hook context for error tracking")
                new_lines.append(f"{main_indent}    import json")
                new_lines.append(f"{main_indent}    set_hook_context()")
                new_lines.append(f"{main_indent}    ")
                new_lines.append(f"{main_indent}    # Parse stdin JSON input")
                new_lines.append(f"{main_indent}    hook_input = json.loads(sys.stdin.read())")
                new_lines.append(f"{main_indent}    ")
                added_stdin_parse = True
                # Now add the current line (dedented if it was in try block)
                if found_main_try and line.startswith("        "):
                    new_lines.append(line[4:])
                else:
                    new_lines.append(line)
                i += 1
                continue

        # Dedent lines that were inside the try block
        if found_main_try and in_main and main_body_start and line.startswith("        "):
            # Remove one level of indentation (4 spaces)
            new_lines.append(line[4:])
        else:
            new_lines.append(line)

        i += 1

    # If we didn't find imports at all, add at top after docstring
    if not added_import:
        result = []
        added = False
        for line in new_lines:
            result.append(line)
            if not added and line.strip() == '"""' and len(result) > 1:
                result.append("")
                result.append("from __lib.hook_base import hook_main")
                result.append("")
                added = True
        if not added:
            # No docstring, add at very top
            result = ["from __lib.hook_base import hook_main", ""] + new_lines
        new_lines = result

    return "\n".join(new_lines)


def migrate_hook(path: Path, dry_run: bool = True) -> MigrationResult:
    """Migrate a single hook file."""
    try:
        content = path.read_text(encoding="utf-8")

        # Check if already migrated
        if check_already_migrated(content):
            return MigrationResult(path, "already_done", "Already has @hook_main", 0, 0, [])

        # Check if has main() function
        if not check_has_main_function(content):
            return MigrationResult(path, "skipped", "No main() function", 0, 0, [])

        # Pre-migration syntax check
        ok, msg = check_syntax(path)
        if not ok:
            return MigrationResult(path, "failed", f"Pre-migration syntax error: {msg}", 0, 0, [])

        # Transform
        new_content = transform_hook(content)

        # Calculate transformation metrics
        original_lines = content.split("\n")
        new_lines = new_content.split("\n")
        lines_added = len(new_lines) - len(original_lines)
        lines_removed = max(0, len(original_lines) - len(new_lines))

        # Track what transformations were applied
        transformations = []
        if "from __lib.hook_base import hook_main" in new_content and "from __lib.hook_base import hook_main" not in content:
            transformations.append("added_hook_main_import")
        if "@hook_main" in new_content and "@hook_main" not in content:
            transformations.append("added_hook_main_decorator")
        if "set_hook_context()" in new_content and "set_hook_context()" not in content:
            transformations.append("added_set_hook_context")
        if "json.loads(sys.stdin.read())" in new_content and "json.loads(sys.stdin.read())" not in content:
            transformations.append("added_stdin_parsing")
        if "except Exception" not in new_content and "except Exception" in content:
            transformations.append("removed_generic_exception_handler")

        if dry_run:
            # Show diff preview
            return MigrationResult(
                path,
                "would_migrate",
                "Would add @hook_main decorator",
                lines_added,
                lines_removed,
                transformations
            )

        # Backup original
        BACKUP_DIR.mkdir(exist_ok=True)
        backup_path = BACKUP_DIR / path.name
        shutil.copy2(path, backup_path)

        # Write transformed content
        path.write_text(new_content, encoding="utf-8")

        # Post-migration syntax check
        ok, msg = check_syntax(path)
        if not ok:
            # Rollback
            shutil.copy2(backup_path, path)
            return MigrationResult(path, "failed", f"Post-migration syntax error (rolled back): {msg}", 0, 0, [])

        # Functional verification
        ok, msg = verify_hook_runs(path)
        if not ok:
            # Rollback
            shutil.copy2(backup_path, path)
            return MigrationResult(path, "failed", f"Post-migration run failed (rolled back): {msg}", 0, 0, [])

        return MigrationResult(
            path,
            "migrated",
            "Successfully migrated",
            lines_added,
            lines_removed,
            transformations
        )

    except Exception as e:
        return MigrationResult(path, "failed", str(e), 0, 0, [])


def find_hooks() -> list[Path]:
    """Find all hook files that need migration."""
    hooks = []
    for path in HOOKS_DIR.glob("*.py"):
        if is_hook_file(path):
            hooks.append(path)
    return sorted(hooks)


def main():
    parser = argparse.ArgumentParser(description="Migrate hooks to use @hook_main decorator")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--migrate", action="store_true", help="Apply migration")
    parser.add_argument("--verify-only", action="store_true", help="Check current migration state")
    parser.add_argument("--file", type=str, help="Migrate single file")
    args = parser.parse_args()

    if not any([args.dry_run, args.migrate, args.verify_only]):
        parser.print_help()
        return

    # Find hooks
    if args.file:
        hooks = [HOOKS_DIR / args.file]
    else:
        hooks = find_hooks()

    print(f"Found {len(hooks)} hook files to process\n")

    # Process
    results = {
        "migrated": [],
        "already_done": [],
        "skipped": [],
        "failed": [],
        "would_migrate": [],
    }

    for hook in hooks:
        if args.verify_only:
            content = hook.read_text(encoding="utf-8")
            if check_already_migrated(content):
                result = MigrationResult(hook, "already_done", "Has @hook_main")
            elif check_has_main_function(content):
                result = MigrationResult(hook, "would_migrate", "Needs migration")
            else:
                result = MigrationResult(hook, "skipped", "No main()")
        else:
            result = migrate_hook(hook, dry_run=args.dry_run)

        results[result.status].append(result)

        # Print status
        status_icons = {
            "migrated": "✅",
            "already_done": "✓",
            "skipped": "⏭",
            "failed": "❌",
            "would_migrate": "📝",
        }
        icon = status_icons.get(result.status, "?")
        print(f"{icon} {result.file.name}: {result.message}")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Migrated:      {len(results['migrated'])}")
    print(f"  Already done:  {len(results['already_done'])}")
    print(f"  Skipped:       {len(results['skipped'])}")
    print(f"  Would migrate: {len(results['would_migrate'])}")
    print(f"  Failed:        {len(results['failed'])}")

    if results['failed']:
        print("\n❌ FAILURES:")
        for r in results['failed']:
            print(f"  - {r.file.name}: {r.message}")


if __name__ == "__main__":
    main()
