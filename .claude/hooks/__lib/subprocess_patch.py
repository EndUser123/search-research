"""
Monkey-patch subprocess to automatically add CREATE_NO_WINDOW on Windows.

Uses a proper subclass so asyncio.windows_utils can still subclass Popen.

    from .subprocess_patch import patch_subprocess_context
    with patch_subprocess_context():
        subprocess.run(["cmd", ...])  # CREATE_NO_WINDOW applied automatically
"""

import subprocess
import sys
from contextlib import contextmanager

_original_popen = subprocess.Popen


class _NoWindowPopen(_original_popen):
    """Popen subclass that adds CREATE_NO_WINDOW on Windows."""

    def __init__(self, *args, **kwargs):
        if sys.platform == "win32" and "creationflags" not in kwargs:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        super().__init__(*args, **kwargs)


def patch_subprocess():
    """Patch subprocess to prevent blue console flashes on Windows."""
    subprocess.Popen = _NoWindowPopen


def unpatch_subprocess():
    """Restore original subprocess.Popen (for testing)."""
    subprocess.Popen = _original_popen


@contextmanager
def patch_subprocess_context():
    """Context manager for scoped subprocess patching with automatic cleanup."""
    if sys.platform != "win32":
        yield
        return

    saved = subprocess.Popen
    try:
        subprocess.Popen = _NoWindowPopen
        yield
    finally:
        subprocess.Popen = saved
