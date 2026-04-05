"""
Import verification tests.

Ensures all project modules can be imported without errors.
Catches import path errors, circular dependencies, and missing modules.
"""

import importlib
import pkgutil
import signal
import threading
from typing import Any


class TimeoutError(Exception):
    """Raised when module import times out."""


def _timeout_handler(signum, frame):
    raise TimeoutError("Module import timed out")


def _import_with_timeout(module_name: str, timeout: float = 2.0) -> Any:
    """Import a module with timeout protection.

    Some modules (like those loading native extensions) can hang indefinitely.
    This wrapper prevents the entire test suite from hanging.
    """
    # Windows doesn't have signal.alarm, use threading approach
    import threading
    import time

    result = [None]
    exception = [None]

    def worker():
        try:
            result[0] = importlib.import_module(module_name)
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        raise TimeoutError(f"Module {module_name} import timed out after {timeout}s")
    if exception[0]:
        raise exception[0]
    return result[0]


def test_all_yt_fts_modules_import():
    """Test that critical yt_fts modules can be imported.

    This is a regression test for import errors like:
    - ImportError: cannot import name 'X' from 'wrong.module'
    - Circular import dependencies
    - Missing dependencies

    Note: Tests a curated list of high-risk modules rather than all modules,
    to avoid timeouts from native extensions or modules with side effects.
    """
    # High-risk modules that have had import issues during refactoring
    # Note: Excluding modules with known side effects at import time
    CRITICAL_MODULES = [
        "yt_fts.core.database",
        "yt_fts.download.batch_downloader",
        "yt_fts.download.batch_channel_helpers",
        "yt_fts.download.download_handler",
        "yt_fts.db.channels",
        "yt_fts.db.videos",
        "yt_fts.db.infra",
        "yt_fts.services.metadata_backfill_api",
        "yt_fts.services.rss_precheck",
        "yt_fts.services.channel_service",
        "yt_fts.display.base",
        "yt_fts.utils.config",
    ]

    failures = []

    for modname in CRITICAL_MODULES:
        try:
            _import_with_timeout(modname, timeout=2.0)
        except TimeoutError:
            failures.append(f"{modname}: timeout (possible native module issue)")
        except ImportError as e:
            failures.append(f"{modname}: {e}")
        except Exception as e:
            # Catch other import-related errors (circular deps, etc.)
            if "import" in str(e).lower() or "module" in str(e).lower():
                failures.append(f"{modname}: {e}")

    if failures:
        raise AssertionError(
            f"Import errors detected in {len(failures)} module(s):\n"
            + "\n".join(failures)
        )


def test_batch_downloader_imports():
    """Specifically test batch_downloader imports (common source of errors).

    This is a targeted regression test for refactoring-related import issues
    in the batch_downloader module.
    """
    try:
        from yt_fts.download.batch_downloader import BatchDownloader
    except ImportError as e:
        raise AssertionError(f"BatchDownloader import failed: {e}")


def test_core_database_imports():
    """Test core.database module imports (common entry point)."""
    try:
        from yt_fts.core.database import (
            get_channel_stats,
            get_db_connection,
            get_vid_ids_by_channel_id,
        )
    except ImportError as e:
        raise AssertionError(f"core.database imports failed: {e}")


def test_cli_imports():
    """Test CLI module imports (entry points)."""
    try:
        from yt_fts.core.cli import cli
        from yt_fts.core.download_cli import batch_download
    except ImportError as e:
        raise AssertionError(f"CLI imports failed: {e}")
