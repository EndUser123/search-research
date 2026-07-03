#!/usr/bin/env python3
"""PreToolUse gate to verify Python imports in packages/ directory.

Purpose: Prevent broken imports like the handoff package had (42 broken imports
after core/ → scripts/ migration). Catches import errors at edit time, not during
hook execution when it's too late.

Detection: Write/Edit operations on *.py files in packages/*/ subdirectories
Verification: Attempts to import the module to verify all imports resolve
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration
PACKAGES_ROOT = Path(__file__).resolve().parents[2] / "packages"
ENABLED_ENV = "PACKAGE_IMPORT_VERIFICATION_ENABLED"  # default: true
BYPASS_FLAG = "--allow-broken-imports"


def _is_package_python_file(file_path: str) -> bool:
    """Check if file is a Python file in packages/ directory."""
    path = Path(file_path).resolve()

    # Must be in packages/ subdirectory
    try:
        path.relative_to(PACKAGES_ROOT)
    except ValueError:
        return False

    # Must be a .py file
    return path.suffix == ".py"


def _get_package_root(file_path: Path) -> Path | None:
    """Find the package root (directory containing the module)."""
    path = file_path.resolve()

    # Try to find package root by looking for common markers
    for parent in [path] + list(path.parents):
        # Stop at packages/ root
        try:
            parent.relative_to(PACKAGES_ROOT)
        except ValueError:
            continue

        # Check if this could be a package root
        if (parent / "scripts").exists() or (parent / "hooks").exists() or (parent / "__init__.py").exists():
            return parent

        # Check if we're at the package directory level
        if (parent.parent == PACKAGES_ROOT):
            return parent

    return None


def _verify_imports(package_root: Path, file_path: Path, content: str | None = None) -> tuple[bool, str]:
    """Verify that Python imports work for the given file.

    Returns:
        (success, error_message)
    """
    # For non-existent files (Write operations), verify imports from content
    if not file_path.exists() and content:
        return _verify_imports_from_content(content, package_root)

    # Determine import path relative to package root
    try:
        rel_path = file_path.relative_to(package_root)
    except ValueError:
        return True, ""  # File not under package root

    # Convert file path to module path
    module_path = str(rel_path.with_suffix("")).replace("\\", ".").replace("/", ".")

    # Skip __init__ files at root level (they're package exports)
    if module_path == "__init__":
        return True, ""

    # Remove leading __init__ for nested packages
    if module_path.startswith(".__init__"):
        module_path = module_path.replace(".__init__", "", 1)
        if module_path.startswith("."):
            module_path = module_path[1:]

    # Build verification command
    # We test by trying to import the module in an isolated Python process
    test_script = f"""
import sys
from pathlib import Path

import logging as _li
_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)



# Add package root to path
package_root = Path(r"{package_root}")
if str(package_root) not in sys.path:
    sys.path.insert(0, str(package_root))

# Add scripts/ to path if it exists (for packages with scripts/ structure)
if (package_root / "scripts").exists():
    sys.path.insert(0, str(package_root / "scripts"))

# Add hooks/ to path if it exists at root
if (package_root / "hooks").exists():
    sys.path.insert(0, str(package_root / "hooks"))

# Try to import the target module
try:
    import {module_path}
    print("✅ OK")
except ImportError as e:
            _logger.debug(f"❌ ImportError: {{e}}",)    sys.exit(1)
except Exception as e:
    # Module loaded but has runtime errors - that's OK for import checking
    print(f"⚠️  Runtime error (imports OK): {{e}}")
"""

    try:
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            timeout=10,  # 10 second timeout for import testing
            cwd=str(package_root),
        )

        if result.returncode == 0:
            return True, ""
        else:
            # Check if it's just a runtime error (imports are actually OK)
            if "Runtime error (imports OK)" in result.stdout:
                return True, ""

            error_msg = result.stderr or result.stdout
            return False, f"Import verification failed: {error_msg.strip()}"

    except subprocess.TimeoutExpired:
        return False, "Import verification timed out (10s limit)"
    except Exception as e:
        # On any exception, allow the operation (fail open)
        logger.warning(f"Package import verification error: {e}")
        return True, ""


def _verify_imports_from_content(content: str, package_root: Path) -> tuple[bool, str]:
    """Verify imports by parsing Python content and checking each import.

    For new files (Write operations), we parse the AST and verify each import
    can be resolved from the package root.

    Returns:
        (success, error_message)
    """
    import ast
    import importlib

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    # Prepare sys.path for import testing
    sys.path.insert(0, str(package_root))
    if (package_root / "scripts").exists():
        sys.path.insert(0, str(package_root / "scripts"))
    if (package_root / "hooks").exists():
        sys.path.insert(0, str(package_root / "hooks"))

    errors = []

    for node in ast.walk(tree):
        try:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    try:
                        importlib.import_module(alias.name)
                    except ImportError as e:
                        errors.append(f"Cannot import {alias.name}: {e}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    try:
                        importlib.import_module(node.module)
                    except ImportError as e:
                        errors.append(f"Cannot import from {node.module}: {e}")
        except Exception as e:
            logger.warning(f"Import check error: {e}")

    # Clean up sys.path
    sys.path = [p for p in sys.path if str(p) not in [
        str(package_root), str(package_root / "scripts"), str(package_root / "hooks")
    ]]

    if errors:
        return False, "; ".join(errors)
    return True, ""


def run(data: dict) -> dict | None:
    """PreToolUse gate to verify package imports.

    Blocks Write/Edit operations on Python files in packages/ if imports are broken.
    """
    # Check if enabled
    import os
    if os.environ.get(ENABLED_ENV, "true").lower() == "false":
        return None  # Disabled

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only check Write and Edit operations
    if tool_name not in ("Write", "Edit"):
        return None

    file_path = tool_input.get("file_path", "")
    if not file_path:
        return None

    # Check if this is a package Python file
    if not _is_package_python_file(file_path):
        return None

    # Check for bypass flag in user message
    transcript = data.get("transcript", [])
    user_message = ""
    if transcript and len(transcript) > 0:
        user_message = transcript[-1].get("content", "")

    if BYPASS_FLAG in user_message:
        return None  # User explicitly allowed

    path = Path(file_path).resolve()
    package_root = _get_package_root(path)

    if not package_root:
        # Can't determine package root - allow operation
        return None

    # Get content for Write operations (for Edit, content is in tool_input)
    content = None
    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        content = tool_input.get("content", "")

    # Verify imports
    success, error_msg = _verify_imports(package_root, path, content)

    if not success:
        return {
            "continue": False,
            "reason": (
                f"⛔ BROKEN IMPORTS DETECTED\n\n"
                f"The file {file_path} has broken imports:\n\n"
                f"{error_msg}\n\n"
                f"This would cause ModuleNotFoundError during execution.\n"
                f"Fix the imports before writing this file.\n\n"
                f"To bypass: Add {BYPASS_FLAG} to your message"
            )
        }

    # Imports are OK, allow the operation
    return None


if __name__ == "__main__":
    # Check if we're being called as a hook (stdin JSON) or from command line
    import sys

    # Hook mode: JSON input via stdin
    if not sys.stdin.isatty():
        import json
        try:
            input_text = sys.stdin.read().strip()
            if input_text:
                data = json.loads(input_text)
                result = run(data)
                if result:
                    print(json.dumps(result))
                    sys.exit(2 if not result.get("continue", True) else 0)
                else:
                    print("{}")
                    sys.exit(0)
        except json.JSONDecodeError:
            # If JSON parsing fails, fall through to command-line mode
            pass

    # Test mode: command-line arguments
    import argparse

    parser = argparse.ArgumentParser(description="Verify package imports")
    parser.add_argument("file_path", help="Path to Python file to verify")
    args = parser.parse_args()

    path = Path(args.file_path).resolve()
    package_root = _get_package_root(path)

    if not package_root:
        print(f"❌ Cannot determine package root for {path}")
        sys.exit(1)

    success, error_msg = _verify_imports(package_root, path)

    if success:
        print(f"✅ Imports OK for {path}")
        sys.exit(0)
    else:
        print(f"❌ {error_msg}")
        sys.exit(1)
