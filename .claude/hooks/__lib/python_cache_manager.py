#!/usr/bin/env python3
"""
Smart Python bytecode cache manager for development workflows.

Auto-clears __pycache__ before editable installs to prevent stale .pyc issues.
Part of Python DX Improvement Tools implementation (see P:/.claude/plan.md)

Integrated with:
- Observability layer (dx_tools_observability) for metrics and health checks
- File locking (dx_tools_locking) for multi-terminal safety
"""

import subprocess
import sys
from pathlib import Path

# Import observability and locking (graceful fallback if unavailable)
try:
    from dx_tools_observability import get_metrics
    OBSERVABILITY_AVAILABLE = True
except ImportError:
    OBSERVABILITY_AVAILABLE = False

try:
    from dx_tools_locking import with_cache_lock
    LOCKING_AVAILABLE = True
except ImportError:
    LOCKING_AVAILABLE = False
    # Fallback: no-op decorator
    def with_cache_lock(package_path, timeout=60):
        def decorator(func):
            return func
        return decorator


def _clear_package_cache_impl(package_path: Path | str) -> dict:
    """Internal implementation of cache clearing (without locking).

    Args:
        package_path: Path to package directory

    Returns:
        dict with keys: cleared_count, paths_cleared, errors
    """
    # Start performance timer
    if OBSERVABILITY_AVAILABLE:
        metrics = get_metrics()
        metrics.start_timer("cache_clear")

    pkg_path = Path(package_path).resolve()

    if not pkg_path.exists():
        # Record error metrics
        if OBSERVABILITY_AVAILABLE:
            metrics.record_event("cache", "error", 1)
            metrics.end_timer("cache_clear")

        return {
            "cleared_count": 0,
            "paths_cleared": [],
            "errors": [f"Path not found: {pkg_path}"]
        }

    cleared = []
    errors = []

    # Clear __pycache__ directories
    for pycache in pkg_path.rglob("__pycache__"):
        try:
            subprocess.run(
                ["rm", "-rf", str(pycache)],
                check=True,
                capture_output=True
            )
            cleared.append(str(pycache))
        except subprocess.CalledProcessError as e:
            errors.append(f"Failed to remove {pycache}: {e}")

    # Clear .pyc files
    for pyc_file in pkg_path.rglob("*.pyc"):
        try:
            pyc_file.unlink()
            cleared.append(str(pyc_file))
        except OSError as e:
            errors.append(f"Failed to remove {pyc_file}: {e}")

    # Record metrics
    if OBSERVABILITY_AVAILABLE:
        if errors:
            metrics.record_event("cache", "error", len(errors))
        if cleared:
            metrics.record_event("cache", "cleared", len(cleared))

        # End performance timer
        duration_ms = metrics.end_timer("cache_clear")

    return {
        "cleared_count": len(cleared),
        "paths_cleared": cleared,
        "errors": errors
    }


def clear_package_cache(package_path: Path | str) -> dict:
    """Clear __pycache__ and .pyc files from a package directory.

    Public interface with file locking for multi-terminal safety.

    Args:
        package_path: Path to package directory (e.g., P:/packages/reflect-system)

    Returns:
        dict with keys: cleared_count, paths_cleared, errors
    """
    if LOCKING_AVAILABLE:
        # Use locking wrapper
        @with_cache_lock(str(package_path))
        def _locked_clear():
            return _clear_package_cache_impl(package_path)

        return _locked_clear()
    else:
        # No locking available, call directly
        return _clear_package_cache_impl(package_path)


def pre_install_cache_clean(package_path: Path | str) -> bool:
    """Auto-clear cache before pip install -e.

    Args:
        package_path: Path to package directory

    Returns:
        True if cache was cleared (or no cache to clear), False on errors
    """
    result = clear_package_cache(package_path)

    if result["errors"]:
        for err in result["errors"]:
            print(f"[cache_manager] ERROR: {err}", file=sys.stderr)
        return False

    if result["cleared_count"] > 0:
        print(f"[cache_manager] ✓ Cleared {result['cleared_count']} cache items from {package_path}")

    return True
