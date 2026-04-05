#!/usr/bin/env python3
"""Type-based validator for directory policy enforcement.

Validates that file types match whitelist category expectations:
- .py files should not be in config whitelist (they're modules, not configs)
- .md files should not be in Python-specific lists
- Config whitelists should only contain configuration file types

This prevents whitelist bypass from allowing incorrectly classified files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# File extension patterns by category
CONFIG_FILE_EXTENSIONS = {
    ".toml",  # pyproject.toml, tox.ini (parsed as TOML)
    ".cfg",  # setup.cfg, pytest.ini, mypy.ini
    ".ini",  # tox.ini, pytest.ini, mypy.ini
    ".json",  # pyrightconfig.json, ruff.toml, .flake8
    ".txt",  # requirements*.txt
    ".md",  # CLAUDE.md, README.md
    ".yaml",  # .pre-commit-config.yaml
    ".yml",  # (same as yaml)
    ".lock",  # poetry.lock, uv.lock, pdm.lock
    ".example",  # .env.example
    ".rc",  # various rc files (.editorconfig, .prettierrc)
}

# Python-specific file extensions (should only be in Python lists)
PYTHON_FILE_EXTENSIONS = {
    ".py",
    ".pyi",
    ".pyc",
    ".pyo",
    ".pyw",
}

# Documentation file extensions
DOC_FILE_EXTENSIONS = {
    ".md",
    ".rst",
    ".txt",
}

# Cache/artifact file patterns (generally allowed anywhere)
CACHE_FILE_PATTERNS = {
    ".cache",
    ".pyc",
    ".pyo",
    "__pycache__",
}


class TypeValidationError:
    """Type validation error with details."""

    def __init__(
        self,
        file_path: str,
        whitelist_name: str,
        expected_type: str,
        actual_type: str,
        suggestion: str,
    ):
        self.file_path = file_path
        self.whitelist_name = whitelist_name
        self.expected_type = expected_type
        self.actual_type = actual_type
        self.suggestion = suggestion

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "whitelist": self.whitelist_name,
            "expected_type": self.expected_type,
            "actual_type": self.actual_type,
            "suggestion": self.suggestion,
            "error_type": "TYPE_MISMATCH",
        }

    def __str__(self) -> str:
        return (
            f"TYPE_MISMATCH: {self.file_path} in {self.whitelist_name}\n"
            f"  Expected: {self.expected_type}\n"
            f"  Actual: {self.actual_type}\n"
            f"  Suggestion: {self.suggestion}"
        )


def get_file_category(file_path: str) -> str:
    """Categorize a file by its extension.

    Args:
        file_path: Path to file

    Returns:
        Category name: "config", "python", "doc", "cache", "unknown"
    """
    path = Path(file_path)

    # Check for cache patterns FIRST (cache takes priority over source categories)
    # Cache extensions like .pyc, .pyo should be categorized as cache, not python
    if path.name in CACHE_FILE_PATTERNS:
        return "cache"

    # Also check cache extensions explicitly
    if path.suffix.lower() in (".pyc", ".pyo"):
        return "cache"

    # Check by extension (excluding cache extensions)
    if path.suffix.lower() in PYTHON_FILE_EXTENSIONS:
        return "python"

    if path.suffix.lower() in DOC_FILE_EXTENSIONS:
        return "doc"

    if path.suffix.lower() in CONFIG_FILE_EXTENSIONS:
        return "config"

    # Check for specific patterns by name
    if path.name.startswith(".") and path.name.endswith("rc"):
        return "config"  # .editorconfig, .prettierrc

    # Default: unknown
    return "unknown"


def _is_package_setup_file(file_path: str) -> bool:
    """Check if a setup.py is a package setup file (has setuptools/distutils imports).

    Args:
        file_path: Path to the setup.py file

    Returns:
        True if this is a package setup.py (has setuptools/distutils), False otherwise
    """
    from pathlib import Path

    path = Path(file_path)

    # Check if file exists
    if not path.is_file():
        return False

    # Try to read file content
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False

    # Check for package setup indicators (setuptools/distutils imports)
    package_indicators = [
        "from setuptools import",
        "from distutils import",
        "import setuptools",
        "import distutils",
        "from setuptools.command",
        "from distutils.command",
    ]

    content_lower = content.lower()
    for indicator in package_indicators:
        if indicator.lower() in content_lower:
            return True

    return False


def validate_config_whitelist_entries(
    whitelist_name: str,
    whitelist_entries: list[str],
) -> list[TypeValidationError]:
    """Validate that config whitelist only contains configuration files.

    Detects Python modules (.py files) incorrectly placed in config whitelist.

    Args:
        whitelist_name: Name of the whitelist (e.g., "allowed_config_files")
        whitelist_entries: List of file patterns from whitelist

    Returns:
        List of TypeValidationError objects (empty if valid)
    """
    errors = []

    for entry in whitelist_entries:
        # Skip wildcard patterns (they're intentionally broad)
        if "*" in entry or "?" in entry or "[" in entry:
            continue

        # Check if this entry looks like a Python file
        if entry.endswith(".py"):
            # Special case: setup.py is a valid package configuration file
            # if it contains setuptools/distutils imports
            if entry.endswith("setup.py"):
                if _is_package_setup_file(entry):
                    continue  # setup.py with setuptools is valid in config whitelist

            errors.append(
                TypeValidationError(
                    file_path=entry,
                    whitelist_name=whitelist_name,
                    expected_type="config file",
                    actual_type="Python module (.py)",
                    suggestion=(
                        f"Remove '{entry}' from {whitelist_name} and "
                        f"move to .claude/hooks/ or appropriate module location."
                    ),
                )
            )

    return errors


def validate_python_whitelist_entries(
    whitelist_name: str,
    whitelist_entries: list[str],
) -> list[TypeValidationError]:
    """Validate that Python whitelists only contain Python-related files.

    Detects non-Python files (configs, docs) incorrectly placed in Python lists.

    Args:
        whitelist_name: Name of the whitelist
        whitelist_entries: List of file patterns from whitelist

    Returns:
        List of TypeValidationError objects (empty if valid)
    """
    errors = []

    for entry in whitelist_entries:
        # Skip wildcard patterns
        if "*" in entry or "?" in entry or "[" in entry:
            continue

        # Get file extension
        path = Path(entry)
        ext = path.suffix.lower()

        # Check if it's NOT a Python file
        if ext and ext not in PYTHON_FILE_EXTENSIONS:
            # Determine what category it actually is
            category = get_file_category(entry)

            if category == "config":
                errors.append(
                    TypeValidationError(
                        file_path=entry,
                        whitelist_name=whitelist_name,
                        expected_type="Python file",
                        actual_type=f"config file ({ext})",
                        suggestion=(
                            f"Config files don't belong in Python whitelist. "
                            f"Move '{entry}' to config whitelist or remove entirely."
                        ),
                    )
                )
            elif category == "doc":
                errors.append(
                    TypeValidationError(
                        file_path=entry,
                        whitelist_name=whitelist_name,
                        expected_type="Python file",
                        actual_type=f"documentation file ({ext})",
                        suggestion=(
                            f"Documentation files don't belong in Python whitelist. "
                            f"Move '{entry}' to docs/ or remove entirely."
                        ),
                    )
                )

    return errors


def validate_all_policy_types(
    policy_path: str = "P:/.claude/hooks/config/directory_policy.json",
) -> dict[str, list[TypeValidationError] | list[str]]:
    """Validate all whitelist type constraints in directory_policy.json.

    Args:
        policy_path: Path to directory_policy.json

    Returns:
        Dict mapping whitelist names to lists of validation errors
    """
    all_errors = {}

    try:
        with open(policy_path) as f:
            policy = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return {"error": [f"Failed to load policy: {e}"]}

    # Validate workspace_root.allowed_config_files
    workspace_root = policy.get("workspace_root", {})
    allowed_config = workspace_root.get("allowed_config_files", [])

    if allowed_config:
        config_errors = validate_config_whitelist_entries(
            "workspace_root.allowed_config_files", allowed_config
        )
        if config_errors:
            all_errors["workspace_root.allowed_config_files"] = config_errors

    # Note: Add more whitelist validations here as needed
    # For example, Python-specific lists, documentation lists, etc.

    return all_errors


def check_file_type_violations(
    file_path: str,
    policy_path: str = "P:/.claude/hooks/config/directory_policy.json",
) -> list[dict]:
    """Check if a specific file violates type-based whitelist rules.

    This is used during violation detection to catch files that are in
    whitelists but shouldn't be (e.g., .py file in config whitelist).

    Args:
        file_path: Path to check
        policy_path: Path to directory_policy.json

    Returns:
        List of violation dictionaries (empty if no violations)
    """
    violations = []

    try:
        with open(policy_path) as f:
            policy = json.load(f)
    except (OSError, json.JSONDecodeError):
        return violations

    path_obj = Path(file_path)
    filename = path_obj.name

    # Check if file is in allowed_config_files whitelist
    workspace_root = policy.get("workspace_root", {})
    allowed_config = workspace_root.get("allowed_config_files", [])

    if filename in allowed_config:
        # File is whitelisted - check if it's actually a config file
        category = get_file_category(file_path)

        if category == "python":
            violations.append(
                {
                    "type": "TYPE_MISMATCH_CONFIG_WHITELIST",
                    "rule": "TYPE_MISMATCH",
                    "path": file_path,
                    "message": (
                        f"Python file '{filename}' is in allowed_config_files "
                        f"whitelist but is a Python module, not a config file"
                    ),
                    "suggestion": (
                        f"Remove '{filename}' from allowed_config_files whitelist "
                        f"and move to .claude/hooks/ (it's imported by Stop.py)"
                    ),
                }
            )

    return violations


# Self-test
if __name__ == "__main__":
    import sys

    # Test cases
    print("Running type_validator.py self-test...")

    # Test 1: Stop_behavior_gates.py in config whitelist (SHOULD FAIL)
    print("\nTest 1: Validate config whitelist with .py file")
    test_whitelist = ["pyproject.toml", "Stop_behavior_gates.py", "README.md"]
    errors = validate_config_whitelist_entries("test_allowed_config", test_whitelist)
    for error in errors:
        print(f"  ERROR: {error}")

    # Test 2: Python whitelist with config file (SHOULD FAIL)
    print("\nTest 2: Validate Python whitelist with config file")
    test_py_whitelist = ["module.py", "config.toml"]
    py_errors = validate_python_whitelist_entries("test_python_files", test_py_whitelist)
    for error in py_errors:
        print(f"  ERROR: {error}")

    # Test 3: Check actual Stop_behavior_gates.py file
    print("\nTest 3: Check Stop_behavior_gates.py for type violations")
    test_file = "P:/Stop_behavior_gates.py"
    violations = check_file_type_violations(test_file)
    for v in violations:
        print(f"  VIOLATION: {v['message']}")

    print(f"\nSelf-test complete. Exit code: {1 if (errors or py_errors or violations) else 0}")
    sys.exit(1 if (errors or py_errors or violations) else 0)
