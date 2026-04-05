#!/usr/bin/env python3
"""
PreToolUse Hook: Python Import Validator

Validates Python code before edits to catch missing import errors early.
Checks syntax and detects missing imports for common modules.

Configuration:
    PYTHON_IMPORT_VALIDATOR_ENABLED=true to enable (default)
    PYTHON_IMPORT_VALIDATOR_VERBOSE=true for detailed output
"""

from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

# Configuration
ENABLED = os.environ.get("PYTHON_IMPORT_VALIDATOR_ENABLED", "true").lower() in ("1", "true", "yes")
VERBOSE = os.environ.get("PYTHON_IMPORT_VALIDATOR_VERBOSE", "false").lower() in ("1", "true", "yes")

# Critical imports that must be present
CRITICAL_IMPORTS = {
    "logging", "pathlib", "json", "re", "sys", "os",
    "datetime", "time", "subprocess",
}

# Python builtins (don't need import)
BUILTINS = {
    "__name__", "__file__", "__doc__", "__package__",
    "abs", "all", "any", "bool", "dict", "enumerate", "filter",
    "float", "int", "len", "list", "map", "max", "min", "range",
    "set", "str", "sum", "tuple", "type", "zip",
}


def is_hook_directory(file_path: str) -> bool:
    """Check if file is in hooks directory."""
    try:
        path = Path(file_path).resolve()
        hooks_dir = Path(__file__).resolve().parent
        return hooks_dir in path.parents or path.parent == hooks_dir
    except Exception:
        return False


def validate_syntax(content: str) -> tuple[bool, str | None]:
    """Validate Python syntax.

    Returns:
        (is_valid, error_message)
    """
    try:
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Parse error: {e}"


def extract_imports(tree: ast.AST) -> set[str]:
    """Extract imported module names from AST.

    Returns:
        Set of imported module names
    """
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Get top-level module name
                name = alias.name.split(".")[0]
                imports.add(name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # Get top-level module name
                name = node.module.split(".")[0]
                imports.add(name)

    return imports


def extract_used_names(tree: ast.AST) -> set[str]:
    """Extract used names from AST (excluding function/class definitions).

    Returns:
        Set of used names
    """
    used = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            # Only track Name nodes that are being used (not defined)
            # We'll filter definitions later
            used.add(node.id)

    # Remove names that are defined (function parameters, variables)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Remove function/class name from used set
            used.discard(node.name)

            # Remove parameter names
            for arg in ast.walk(node.args):
                if isinstance(arg, ast.arg):
                    used.discard(arg.arg)

        elif isinstance(node, ast.Assign):
            # Remove assignment targets
            for target in node.targets:
                if isinstance(target, ast.Name):
                    used.discard(target.id)
                elif isinstance(target, ast.Tuple):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            used.discard(elt.id)

    return used


def detect_missing_imports(imports: set[str], used: set[str]) -> set[str]:
    """Detect used names that aren't imported.

    Args:
        imports: Set of imported module names
        used: Set of used names

    Returns:
        Set of missing imports
    """
    # Remove builtins from used set
    used_non_builtin = used - BUILTINS

    # Find names that are used but not imported
    missing = used_non_builtin - imports

    # Filter out common false positives
    false_positives = {
        "self", "cls", "super", "None", "True", "False",
        "Exception", "BaseException",
    }
    missing -= false_positives

    return missing


def is_critical_missing_import(name: str) -> bool:
    """Check if missing import is critical.

    Args:
        name: Import name

    Returns:
        True if critical, False otherwise
    """
    return name in CRITICAL_IMPORTS


def main() -> int:
    """Main entry point."""
    if not ENABLED:
        print(json.dumps({"continue": True}))
        return 0

    try:
        input_text = sys.stdin.read().strip()
        if not input_text:
            print(json.dumps({"continue": True}))
            return 0

        data = json.loads(input_text)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return 0

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        print(json.dumps({"continue": True}))
        return 0

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Skip non-Python files
    if not file_path.endswith(".py"):
        print(json.dumps({"continue": True}))
        return 0

    # Skip non-hook directories
    if not is_hook_directory(file_path):
        print(json.dumps({"continue": True}))
        return 0

    # Get content to validate
    if tool_name == "Write":
        content = tool_input.get("content", "")
    else:  # Edit
        content = tool_input.get("content", "")

    if not content:
        print(json.dumps({"continue": True}))
        return 0

    # Validate syntax
    is_valid, error = validate_syntax(content)
    if not is_valid:
        print(json.dumps({
            "continue": False,
            "reason": f"Python syntax error: {error}",
        }))
        return 2

    # Parse and check imports
    try:
        tree = ast.parse(content)
        imports = extract_imports(tree)
        used = extract_used_names(tree)
        missing = detect_missing_imports(imports, used)

        if missing:
            # Separate critical and non-critical missing imports
            critical_missing = {m for m in missing if is_critical_missing_import(m)}
            non_critical_missing = missing - critical_missing

            if critical_missing:
                # Block edit for critical missing imports
                missing_str = ", ".join(sorted(critical_missing))
                print(json.dumps({
                    "continue": False,
                    "reason": f"Missing critical imports: {missing_str}. Please add imports before editing.",
                }))
                return 2

            elif non_critical_missing and VERBOSE:
                # Warn but allow for non-critical missing imports
                missing_str = ", ".join(sorted(non_critical_missing))
                print(json.dumps({
                    "continue": True,
                    "warning": f"Possible missing imports: {missing_str}. Verify these are available.",
                }))
                return 0

        # All checks passed
        print(json.dumps({"continue": True}))
        return 0

    except Exception:
        # Fail open on unexpected errors
        print(json.dumps({"continue": True}))
        return 0


if __name__ == "__main__":
    sys.exit(main())
