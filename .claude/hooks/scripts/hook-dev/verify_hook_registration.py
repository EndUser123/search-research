#!/usr/bin/env python3
"""
Hook Registration Verification Script

Checks for duplicate hook registrations that can cause runtime errors.

This script detects:
1. Hooks registered in both TOOL_HOOKS (PreToolUse.py) and settings.json subprocess
2. Duplicate entries within settings.json

Usage:
    python P:/.claude/hooks/scripts/verify_hook_registration.py

Exit codes:
    0: No issues found
    1: Duplicate registration detected
    2: Error running script
"""

import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def extract_hook_registrations(pretooluse_path: Path) -> Tuple[Dict[str, List[str]], Set[str]]:
    """Extract TOOL_HOOKS and IN_PROCESS_HOOKS from PreToolUse.py.

    Returns:
        - tool_hooks: dict mapping tool names to lists of hook filenames
        - in_process_hooks: set of hook filenames in IN_PROCESS_HOOKS
    """
    try:
        content = pretooluse_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"ERROR: {pretooluse_path} not found", file=sys.stderr)
        sys.exit(2)

    # Parse the Python file to extract hook registrations
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"ERROR: Could not parse {pretooluse_path}: {e}", file=sys.stderr)
        sys.exit(2)

    tool_hooks = {}
    in_process_hooks = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                target_id = None
                if isinstance(target, ast.Name):
                    target_id = target.id
                elif isinstance(target, ast.Subscript):
                    # Handle assignments like IN_PROCESS_HOOKS["key"] = value
                    if isinstance(target.value, ast.Name) and target.value.id == "IN_PROCESS_HOOKS":
                        if isinstance(target.slice, ast.Constant):
                            target_id = "IN_PROCESS_HOOKS"

                if target_id == "TOOL_HOOKS":
                    # Extract the dictionary
                    if isinstance(node.value, ast.Dict):
                        for key, value in zip(node.value.keys, node.value.values):
                            if isinstance(key, ast.Constant):
                                tool_name = key.value
                                hook_list = []

                                if isinstance(value, ast.List):
                                    for elt in value.elts:
                                        if isinstance(elt, ast.Constant):
                                            hook_list.append(elt.value)

                                tool_hooks[tool_name] = hook_list

                elif target_id == "IN_PROCESS_HOOKS":
                    # Extract IN_PROCESS_HOOKS dictionary
                    if isinstance(node.value, ast.Dict):
                        for key, value in zip(node.value.keys, node.value.values):
                            if isinstance(key, ast.Constant):
                                in_process_hooks.add(key.value)

    return tool_hooks, in_process_hooks


def extract_subprocess_hooks(settings_path: Path) -> List[str]:
    """Extract subprocess hook commands from settings.json PreToolUse section.

    Returns a list of hook filenames (not full command paths).
    """
    try:
        content = settings_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"ERROR: {settings_path} not found", file=sys.stderr)
        sys.exit(2)

    try:
        settings = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse {settings_path}: {e}", file=sys.stderr)
        sys.exit(2)

    # Extract PreToolUse hooks
    pretooluse_hooks = settings.get("hooks", {}).get("PreToolUse", [])
    hook_files = []

    for entry in pretooluse_hooks:
        for hook in entry.get("hooks", []):
            command = hook.get("command", "")
            # Extract hook filename from command like "python P:/.claude/hooks/hook_name.py"
            match = re.search(r'PreToolUse_[\w-]+\.py|[\w-]+\.py', command)
            if match:
                hook_file = match.group(0)
                hook_files.append(hook_file)

    return hook_files


def find_duplicates_within_list(hook_list: List[str]) -> Set[str]:
    """Find duplicate entries within a list."""
    seen = set()
    duplicates = set()

    for hook in hook_list:
        if hook in seen:
            duplicates.add(hook)
        seen.add(hook)

    return duplicates


def main() -> None:
    # Paths
    hooks_dir = Path("P:/.claude/hooks")
    pretooluse_path = hooks_dir / "PreToolUse.py"
    settings_path = Path("P:/.claude/settings.json")

    # Extract registrations
    print("Checking hook registrations...")
    print(f"  Reading: {pretooluse_path}")
    tool_hooks, in_process_hooks = extract_hook_registrations(pretooluse_path)

    print(f"  Reading: {settings_path}")
    subprocess_hooks = extract_subprocess_hooks(settings_path)

    # Collect all hooks from TOOL_HOOKS
    all_tool_hooks: Set[str] = set()
    for hooks in tool_hooks.values():
        all_tool_hooks.update(hooks)

    print(f"\n  Found {len(all_tool_hooks)} hooks in TOOL_HOOKS")
    print(f"  Found {len(in_process_hooks)} hooks in IN_PROCESS_HOOKS")
    print(f"  Found {len(subprocess_hooks)} hooks in settings.json PreToolUse")

    # Check 1: Hooks in both IN_PROCESS_HOOKS and settings.json
    # This is the real duplicate - in-process hooks should NOT also be subprocess
    print("\n[CHECK 1] Hooks in both IN_PROCESS_HOOKS and settings.json subprocess:")
    print("  (This is the real duplicate - in-process hooks should NOT also be subprocess)")
    duplicates = in_process_hooks.intersection(subprocess_hooks)

    if duplicates:
        print("  ⚠️  DUPLICATES FOUND:")
        for hook in sorted(duplicates):
            print(f"    - {hook}")
            print(f"      IN_PROCESS_HOOKS: Yes")
            print(f"      subprocess: Yes (in settings.json)")

            # Show which tools use this hook
            in_tools = [tool for tool, hooks in tool_hooks.items() if hook in hooks]
            if in_tools:
                print(f"      Used by tools: {', '.join(in_tools)}")

        print("\n  This can cause 'No stderr output' errors when the subprocess version")
        print("  runs after the in-process version and exits code 2 without stderr.")
        print("\n  Fix: Remove the subprocess entry from settings.json. The hook will")
        print("       run in-process via IN_PROCESS_HOOKS.")
    else:
        print("  ✅ No duplicates found")

    # Check 1b: Hooks in TOOL_HOOKS that are also in settings.json
    # This is informational only - hooks can be dispatched via TOOL_HOOKS AND run as subprocess
    print("\n[CHECK 1b] Hooks in TOOL_HOOKS also registered as subprocess (informational):")
    tool_hook_overlaps = all_tool_hooks.intersection(subprocess_hooks) - in_process_hooks
    if tool_hook_overlaps:
        print("  ℹ️  Found hooks in both TOOL_HOOKS and subprocess (not in IN_PROCESS_HOOKS):")
        for hook in sorted(tool_hook_overlaps):
            in_tools = [tool for tool, hooks in tool_hooks.items() if hook in hooks]
            print(f"    - {hook}")
            print(f"      TOOL_HOOKS: {', '.join(in_tools)}")
            print(f"      subprocess: Yes (intentional, runs twice)")
        print("\n  This is expected behavior - these hooks run both in-process (via TOOL_HOOKS)")
        print("  and as subprocess (via settings.json).")
    else:
        print("  ℹ️  No additional overlaps found")

    # Check 2: Duplicates within settings.json
    print("\n[CHECK 2] Duplicate entries within settings.json:")
    settings_duplicates = find_duplicates_within_list(subprocess_hooks)

    if settings_duplicates:
        print("  ⚠️  DUPLICATES FOUND:")
        for hook in sorted(settings_duplicates):
            count = subprocess_hooks.count(hook)
            print(f"    - {hook} (appears {count} times)")
        print("\n  Fix: Remove duplicate entries from settings.json")
    else:
        print("  ✅ No duplicates found")

    # Exit with appropriate code
    if duplicates or settings_duplicates:
        print("\n❌ VERIFICATION FAILED: Duplicate registrations detected")
        sys.exit(1)
    else:
        print("\n✅ VERIFICATION PASSED: No duplicate registrations found")
        sys.exit(0)


if __name__ == "__main__":
    main()
