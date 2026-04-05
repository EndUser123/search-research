"""
Centralized subprocess helper with CREATE_NO_WINDOW for Windows.

This module prevents the blue console flash on Windows by automatically
adding the CREATE_NO_WINDOW flag to all subprocess calls.

Usage:
    from .subprocess_helper import run, Popen

    # run() replaces subprocess.run()
    result = run(['git', 'status'], capture_output=True)

    # Popen() replaces subprocess.Popen()
    proc = Popen(['python', 'script.py'], stdout=subprocess.PIPE)
"""

from __future__ import annotations

import subprocess
import sys

# Default flags for Windows
DEFAULT_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def run(
    args,
    **kwargs
) -> subprocess.CompletedProcess:
    """
    subprocess.run() wrapper with automatic CREATE_NO_WINDOW on Windows.

    Automatically adds creationflags if not already specified.
    All other parameters passed through to subprocess.run().
    """
    # Add CREATE_NO_WINDOW on Windows if not already specified
    if sys.platform == "win32" and "creationflags" not in kwargs:
        kwargs["creationflags"] = DEFAULT_FLAGS

    return subprocess.run(args, **kwargs)


def Popen(
    args,
    **kwargs
) -> subprocess.Popen:
    """
    subprocess.Popen() wrapper with automatic CREATE_NO_WINDOW on Windows.

    Automatically adds creationflags if not already specified.
    All other parameters passed through to subprocess.Popen().
    """
    # Add CREATE_NO_WINDOW on Windows if not already specified
    if sys.platform == "win32" and "creationflags" not in kwargs:
        kwargs["creationflags"] = DEFAULT_FLAGS

    return subprocess.Popen(args, **kwargs)


# For backwards compatibility, also export as run_subprocess
run_subprocess = run
