#!/usr/bin/env python3
"""Hook file integrity validator.

Detects common hook file issues:
- Truncated functions (empty @hook_main bodies)
- Missing function calls (hook defined but does nothing)
- Syntax errors (prevents deployment)

Run after hook edits to validate integrity before deployment.
"""

import ast
import sys
from pathlib import Path


def validate_hook_file(hook_path: Path) -> tuple[bool, str]:
    """Validate hook file has complete, parseable structure.

    Returns:
        (is_valid, message): Validation result with descriptive message
    """
    try:
        source = hook_path.read_text()
        tree = ast.parse(source)
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Failed to read file: {e}"

    # Find @hook_main decorated function
    hook_main_found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Check for @hook_main decorator
            for decorator in node.decorator_list:
                decorator_name = None
                if isinstance(decorator, ast.Name):
                    decorator_name = decorator.id
                elif isinstance(decorator, ast.Attribute):
                    decorator_name = decorator.attr

                if decorator_name == "hook_main":
                    hook_main_found = True

                    # Check function body has substance
                    if len(node.body) <= 1:
                        return False, f"@hook_main function '{node.name}' appears truncated (empty body)"

                    # Check for at least one function call or return statement
                    has_calls = any(isinstance(n, ast.Call) for n in ast.walk(node))
                    has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
                    has_raise = any(isinstance(n, ast.Raise) for n in ast.walk(node))

                    if not (has_calls or has_return or has_raise):
                        return False, f"@hook_main function '{node.name}' has no function calls or return statements"

                    # Check function actually does something (not just pass)
                    statements = [n for n in node.body if not isinstance(n, (ast.Pass, ast.Expr, ast.Return))]
                    if len(statements) == 0:
                        return False, f"@hook_main function '{node.name}' contains only pass/return statements"

    if not hook_main_found:
        return False, "No @hook_main decorated function found"

    return True, "OK"


def validate_all_hooks(hooks_dir: Path) -> list[tuple[str, str]]:
    """Validate all hook files in directory.

    Returns:
        List of (filename, error_message) for failed validations
    """
    issues = []

    for hook_file in hooks_dir.glob("*.py"):
        # Skip __lib, test files, and hidden files
        if hook_file.name.startswith("_") or hook_file.name.startswith("."):
            continue
        if hook_file.name.endswith("_test.py"):
            continue

        is_valid, msg = validate_hook_file(hook_file)
        if not is_valid:
            issues.append((hook_file.name, msg))

    return issues


if __name__ == "__main__":
    hooks_dir = Path(__file__).resolve().parent.parent

    if len(sys.argv) > 1:
        # Validate specific file
        hook_path = Path(sys.argv[1])
        if not hook_path.is_absolute():
            hook_path = hooks_dir / hook_path

        valid, msg = validate_hook_file(hook_path)
        if valid:
            print(f"✅ {hook_path.name}: {msg}")
            sys.exit(0)
        else:
            print(f"❌ {hook_path.name}: {msg}")
            sys.exit(1)
    else:
        # Validate all hooks
        issues = validate_all_hooks(hooks_dir)

        if issues:
            print("❌ HOOK VALIDATION FAILED")
            for filename, msg in issues:
                print(f"  - {filename}: {msg}")
            sys.exit(1)
        else:
            print("✅ All hooks validated")
            sys.exit(0)
