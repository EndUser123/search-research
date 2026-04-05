"""Centralized path normalization utilities."""

from __future__ import annotations

import os
from pathlib import Path


def normalize_project_path(path: str | Path, project_root: str | Path | None = None) -> Path:
    """Normalize a path relative to project root.

    Args:
        path: Absolute or relative path
        project_root: Project root directory (defaults to P:/)

    Returns:
        Normalized absolute Path object
    """
    if project_root is None:
        project_root = Path(os.environ.get("PROJECT_ROOT", "P:/"))
    else:
        project_root = Path(project_root)

    path = Path(path)
    if not path.is_absolute():
        path = project_root / path

    return path.resolve()


def get_hooks_dir() -> Path:
    """Get the hooks directory path.

    Returns:
        Absolute Path to hooks directory
    """
    return Path(__file__).resolve().parent.parent


def get_state_dir() -> Path:
    """Get the state directory path.

    Returns:
        Absolute Path to state directory
    """
    base = Path(os.environ.get("PROJECT_ROOT", "P:/"))
    return base / ".claude" / "state"


def get_benchmarks_dir() -> Path:
    """Get the benchmarks directory path.

    Returns:
        Absolute Path to benchmarks directory
    """
    hooks_dir = get_hooks_dir()
    return hooks_dir / ".benchmarks"
