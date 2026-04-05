#!/usr/bin/env python3
"""
Shared path normalization utilities for hooks.

All hooks should import normalize_path from here to ensure consistent
handling of Git Bash paths (/p/ -> p:/) and Windows backslashes.
"""

from typing import Optional


def normalize_path(path: str) -> str:
    """
    Normalize path for cross-platform compatibility.
    
    Handles:
    - Backslash to forward slash conversion
    - Git Bash /x/ to x:/ conversion (e.g., /p/ -> p:/)
    - Lowercase normalization
    
    Args:
        path: Raw path string from any source
        
    Returns:
        Normalized lowercase path with forward slashes and proper drive letter
    """
    if not path:
        return ""

    normalized = path.replace("\\", "/").lower()

    # Git Bash on Windows: /p/ means P:/ drive
    # Pattern: /x/... where x is a single letter -> x:/...
    if len(normalized) >= 3 and normalized[0] == '/' and normalized[2] == '/':
        drive_letter = normalized[1]
        if drive_letter.isalpha():
            normalized = f"{drive_letter}:{normalized[2:]}"

    return normalized


def normalize_path_preserve_case(path: str) -> str:
    """
    Normalize path without lowercasing (for display or when case matters).
    
    Args:
        path: Raw path string
        
    Returns:
        Normalized path with forward slashes and proper drive letter, original case
    """
    if not path:
        return ""

    normalized = path.replace("\\", "/")

    # Git Bash on Windows: /p/ means P:/ drive
    if len(normalized) >= 3 and normalized[0] == '/' and normalized[2] == '/':
        drive_letter = normalized[1]
        if drive_letter.isalpha():
            normalized = f"{drive_letter.upper()}:{normalized[2:]}"

    return normalized


def to_windows_path(normalized_path: str) -> str:
    """
    Convert normalized path back to Windows format for Path operations.
    
    Args:
        normalized_path: Path already processed by normalize_path()
        
    Returns:
        Path with uppercase drive letter suitable for Path() operations
    """
    if len(normalized_path) >= 2 and normalized_path[1] == ':':
        return normalized_path[0].upper() + normalized_path[1:]
    return normalized_path


def is_workspace_path(path: str) -> bool:
    """
    Check if path is within the P:/ workspace.
    
    Handles both Windows (P:/) and Git Bash (/p/) formats.
    
    Args:
        path: Raw path string
        
    Returns:
        True if path is within P:/ workspace
    """
    normalized = normalize_path(path)
    return normalized.startswith("p:/")


def is_csf_nip_path(path: str) -> bool:
    """
    Check if path is within P:/__csf/.
    
    Args:
        path: Raw path string
        
    Returns:
        True if path is within __csf directory
    """
    normalized = normalize_path(path)
    return normalized.startswith("p:/__csf/")


def is_claude_path(path: str) -> bool:
    """
    Check if path is within P:/.claude/.
    
    Args:
        path: Raw path string
        
    Returns:
        True if path is within .claude directory
    """
    normalized = normalize_path(path)
    return normalized.startswith("p:/.claude/")


def is_projects_path(path: str) -> bool:
    """
    Check if path is within P:/projects/.
    
    Args:
        path: Raw path string
        
    Returns:
        True if path is within projects directory
    """
    normalized = normalize_path(path)
    return normalized.startswith("p:/projects/")


def get_relative_to_workspace(path: str) -> Optional[str]:
    """
    Get path relative to P:/ workspace.

    Args:
        path: Raw path string

    Returns:
        Path without P:/ prefix, or None if not a workspace path
    """
    normalized = normalize_path(path)
    if normalized.startswith("p:/"):
        return normalized[3:]  # Remove "p:/"
    return None


# ----------------------------------------------------------------------
# D6: Canonical path normalization for LLM Behavioral Integrity plan
# ----------------------------------------------------------------------


def canonical_path(path: str) -> str:
    """
    Return the canonical, normalized absolute path using os.path.realpath().

    D6 invariant: All file path comparisons MUST use this function to ensure
    consistent path representation regardless of:
    - Trailing slashes
    - Forward/backward slashes on Windows
    - Short vs long filename forms
    - Symlink resolution
    - Relative path components (., ..)

    Args:
        path: File or directory path (relative or absolute)

    Returns:
        Canonical absolute path string

    Example:
        >>> canonical_path("foo/bar/../baz")
        'C:\\Users\\name\\project\\foo\\baz'

        >>> canonical_path("./foo//bar/")
        'C:\\Users\\name\\project\\foo\\bar'
    """
    if not path:
        return ""

    import os

    try:
        # realpath() resolves symlinks and normalizes the path
        # abspath() ensures we have an absolute path
        return os.path.realpath(os.path.abspath(str(path)))
    except (OSError, ValueError, TypeError):
        # Fallback: just normalize to absolute path
        try:
            return os.path.abspath(str(path))
        except (OSError, ValueError, TypeError):
            return str(path)


def paths_are_same(a: str, b: str) -> bool:
    """
    Compare two paths for equality after canonical normalization.

    Args:
        a: First path
        b: Second path

    Returns:
        True if both paths resolve to the same canonical path

    Example:
        >>> paths_are_same("foo/bar", "./foo/bar")
        True

        >>> paths_are_same("C:\\\\Users\\\\foo", "c:\\\\users\\\\foo")
        True (on case-insensitive systems)
    """
    return canonical_path(a) == canonical_path(b)
