#!/usr/bin/env python3
"""Optimal location inference for files in workspace.

Determines where files SHOULD live based on type/purpose:
- Python imports from .claude/hooks/ → belongs in .claude/hooks/
- JSON referenced as "per-project config" → root is optimal
- Hidden directories → categorize as cache/config/violation

This prevents whitelist bypass by answering "is this OPTIMAL?" not just "is this allowed?".
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def infer_optimal_location(
    file_path: str,
    project_root: str = "P:/",
    hooks_dir: str = ".claude/hooks",
    session_data_dir: str = ".claude/state/session_data",
) -> dict[str, Any]:
    """Infer the optimal location for a file based on its type and usage.

    Args:
        file_path: Path to the file to analyze
        project_root: Root of the project (default: P:/)
        hooks_dir: Directory containing hook files
        session_data_dir: Directory for session data files

    Returns:
        Dict with keys:
        - current_location: Where the file is now
        - optimal_location: Where the file should be
        - reason: Why this location is optimal
        - category: File category (python_module, config, cache, data, etc.)
        - action: Suggested action (move, keep, investigate)
    """
    path = Path(file_path)
    filename = path.name

    # Get file category
    category = _get_file_category(file_path)

    # Determine optimal location based on category
    if category == "python_module":
        return _infer_python_module_location(file_path, project_root, hooks_dir)
    elif category == "config":
        return _infer_config_location(file_path, project_root)
    elif category == "cache":
        return _infer_cache_location(file_path, project_root)
    elif category == "data":
        return _infer_data_location(file_path, project_root, session_data_dir)
    else:
        return {
            "current_location": file_path,
            "optimal_location": file_path,  # Unknown, keep where it is
            "reason": "Unknown file type, cannot determine optimal location",
            "category": category,
            "action": "keep",
        }


def _get_file_category(file_path: str) -> str:
    """Categorize a file by extension and name patterns.

    Args:
        file_path: Path to the file

    Returns:
        Category: python_module, config, cache, data, unknown
    """
    path = Path(file_path)

    # Python modules
    if path.suffix.lower() in (".py", ".pyi"):
        # Check if it's imported by hooks
        if _is_hook_imported_module(file_path):
            return "python_module"
        return "python_module"  # Could be utility, treat as python

    # Config files
    if path.suffix.lower() in (".toml", ".cfg", ".ini", ".json", ".yaml", ".yml", ".lock"):
        return "config"

    # Cache files (by extension or name)
    if path.name.startswith(".cache") or path.suffix.lower() in (".pyc", ".pyo"):
        return "cache"

    # Cache and config directories (by name, regardless of existence)
    # Check both hidden directories and special cache directory names
    dir_name = path.name.lower()
    if dir_name in ("__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"):
        return "cache"
    if dir_name in (".git", ".vscode", ".idea"):
        return "config"

    # Data files (JSON evidence, session data)
    if path.suffix.lower() == ".json":
        if "evidence" in path.parts or "session" in path.parts:
            return "data"

    # Hidden directories (only if actually exists on disk)
    if path.name.startswith(".") and path.is_dir():
        return _categorize_hidden_directory(file_path)

    return "unknown"


def _is_hook_imported_module(file_path: str) -> bool:
    """Check if a Python file is imported by any hook.

    Args:
        file_path: Path to the Python file

    Returns:
        True if the file appears to be imported by hooks
    """
    # For now, use heuristic: files in workspace root that are .py
    # and match hook import patterns
    path = Path(file_path)

    # Check if it's in root (not in .claude/)
    parts = path.parts
    if ".claude" in parts:
        return False  # Already in hooks directory

    # Check if it looks like a hook module
    # Common patterns: *_gate.py, *_validator.py, Stop_*.py
    hook_patterns = [
        r".*_gate\.py$",
        r".*_validator\.py$",
        r"Stop_.*\.py$",
        r"recursive_.*\.py$",
        r"pre.*\.py$",
        r"post.*\.py$",
    ]

    filename = path.name
    for pattern in hook_patterns:
        if re.match(pattern, filename, re.IGNORECASE):
            return True

    return False


def _categorize_hidden_directory(dir_path: str) -> str:
    """Categorize a hidden directory by its name and contents.

    Args:
        dir_path: Path to the hidden directory

    Returns:
        Category: cache, config, data, violation, unknown
    """
    path = Path(dir_path)
    name = path.name.lower()

    # Known cache directories
    if name in ("__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"):
        return "cache"

    # Known config directories
    if name in (".git", ".vscode", ".idea"):
        return "config"

    # Known data directories
    if "evidence" in name:
        return "data"
    if "session" in name or "state" in name:
        return "data"

    # Unknown hidden directory - may need investigation
    return "violation"  # Conservative: flag for review


def _infer_python_module_location(
    file_path: str,
    project_root: str,
    hooks_dir: str,
) -> dict[str, Any]:
    """Infer optimal location for a Python module.

    Args:
        file_path: Path to the Python file
        project_root: Root of the project
        hooks_dir: Directory containing hook files

    Returns:
        Dict with optimal location and reasoning
    """
    path = Path(file_path)
    filename = path.name

    # If it's imported by hooks, belongs in hooks/
    if _is_hook_imported_module(file_path):
        optimal = f"{hooks_dir}/{filename}"
        return {
            "current_location": file_path,
            "optimal_location": optimal,
            "reason": f"Python module imported by hooks (e.g., Stop.py imports {filename})",
            "category": "python_module",
            "action": "move",
        }

    # Check if it's a setup/build script
    if filename in ("setup.py", "setup_ext.py", "conftest.py"):
        return {
            "current_location": file_path,
            "optimal_location": file_path,  # Root is fine for setup scripts
            "reason": "Python setup/build scripts belong in workspace root",
            "category": "python_module",
            "action": "keep",
        }

    # Default for other Python modules
    return {
        "current_location": file_path,
        "optimal_location": file_path,
        "reason": "Python module location is acceptable",
        "category": "python_module",
        "action": "keep",
    }


def _infer_config_location(
    file_path: str,
    project_root: str,
) -> dict[str, Any]:
    """Infer optimal location for a config file.

    Args:
        file_path: Path to the config file
        project_root: Root of the project

    Returns:
        Dict with optimal location and reasoning
    """
    path = Path(file_path)
    filename = path.name

    # Check if it's a per-project config
    per_project_configs = [
        ".behavior_gates_blacklist.json",
        ".env.local",
        ".env.project",
    ]

    if filename in per_project_configs:
        return {
            "current_location": file_path,
            "optimal_location": file_path,  # Root is optimal
            "reason": "Per-project configuration file belongs in workspace root",
            "category": "config",
            "action": "keep",
        }

    # Other configs might belong in .claude/ or root
    # For now, be conservative
    return {
        "current_location": file_path,
        "optimal_location": file_path,
        "reason": "Config file location is acceptable",
        "category": "config",
        "action": "keep",
    }


def _infer_cache_location(
    file_path: str,
    project_root: str,
) -> dict[str, Any]:
    """Infer optimal location for a cache file.

    Args:
        file_path: Path to the cache file
        project_root: Root of the project

    Returns:
        Dict with optimal location and reasoning
    """
    return {
        "current_location": file_path,
        "optimal_location": file_path,
        "reason": "Cache files can be in their current location",
        "category": "cache",
        "action": "keep",
    }


def _infer_data_location(
    file_path: str,
    project_root: str,
    session_data_dir: str,
) -> dict[str, Any]:
    """Infer optimal location for a data file.

    Args:
        file_path: Path to the data file
        project_root: Root of the project
        session_data_dir: Directory for session data

    Returns:
        Dict with optimal location and reasoning
    """
    path = Path(file_path)
    filename = path.name

    # Check if it's hidden data directory
    if filename.startswith(".") and path.is_dir():
        # Check canonical location
        canonical = f"{project_root}/{session_data_dir}/{filename}"
        return {
            "current_location": file_path,
            "optimal_location": canonical,
            "reason": f"Hidden data directory should be in {session_data_dir}/ per directory_policy.json",
            "category": "data",
            "action": "move",
        }

    return {
        "current_location": file_path,
        "optimal_location": file_path,
        "reason": "Data file location is acceptable",
        "category": "data",
        "action": "keep",
    }


# Self-test
if __name__ == "__main__":
    print("Running location_optimizer.py self-test...")

    # Test 1: Stop_behavior_gates.py (should be in .claude/hooks/)
    print("\nTest 1: Stop_behavior_gates.py optimal location")
    result = infer_optimal_location("P:/Stop_behavior_gates.py")
    print(f"  Current: {result['current_location']}")
    print(f"  Optimal: {result['optimal_location']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Action: {result['action']}")

    # Test 2: .behavior_gates_blacklist.json (root is optimal)
    print("\nTest 2: .behavior_gates_blacklist.json optimal location")
    result = infer_optimal_location("P:/.behavior_gates_blacklist.json")
    print(f"  Current: {result['current_location']}")
    print(f"  Optimal: {result['optimal_location']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Action: {result['action']}")

    # Test 3: .evidence/ directory (should be in session_data/)
    print("\nTest 3: .evidence/ directory optimal location")
    result = infer_optimal_location("P:/.evidence")
    print(f"  Current: {result['current_location']}")
    print(f"  Optimal: {result['optimal_location']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Action: {result['action']}")

    # Test 4: setup.py (root is acceptable)
    print("\nTest 4: setup.py optimal location")
    result = infer_optimal_location("P:/setup.py")
    print(f"  Current: {result['current_location']}")
    print(f"  Optimal: {result['optimal_location']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Action: {result['action']}")

    print("\nSelf-test complete.")
