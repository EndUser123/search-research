#!/usr/bin/env python3
"""Path sanitization utilities for hook operations.

Provides shell metacharacter validation and hook name validation to prevent
injection attacks when constructing file paths for hook operations.

Usage:
    from __lib.path_sanitizer import sanitize_hook_path, validate_hook_name

    safe_path = sanitize_hook_path(user_provided_path)
    safe_name = validate_hook_name(hook_name)
"""

from __future__ import annotations

import re
from pathlib import Path

_HOOK_UNSAFEChars = re.compile(r'[;&|`$\n\r]')
_HOOK_NAME_VALID = re.compile(r'^\w+$')


def sanitize_hook_path(path: Path) -> Path:
    """Reject paths with shell metacharacters before file operations.

    Shell metacharacters in paths used by subprocess calls or shell expansions
    can cause injection vulnerabilities. This function validates that a path
    contains no unsafe characters before allowing file operations.

    Args:
        path: Path to validate

    Returns:
        The resolved Path if safe

    Raises:
        ValueError: If path contains shell metacharacters
    """
    path_str = str(path)
    if _HOOK_UNSAFEChars.search(path_str):
        raise ValueError(f"Unsafe path characters: {path_str!r}")
    return path.resolve()


def validate_hook_name(name: str) -> str:
    """Ensure hook name is alphanumeric plus underscore only.

    Hook names are used to construct file paths (hook_name.py, __pycache__/hook_name.pyc).
    Strict validation prevents path traversal and injection attacks.

    Args:
        name: Hook name to validate

    Returns:
        The validated name

    Raises:
        ValueError: If name contains anything other than word characters
    """
    if not _HOOK_NAME_VALID.match(name):
        raise ValueError(f"Invalid hook name: {name!r}")
    return name