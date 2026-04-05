
"""
Hooks Library Package

Shared utilities and base classes for Claude Code hooks.

This package contains reusable modules that are imported by multiple hooks,
preventing code duplication and providing consistent behavior across the
hook system.
"""

from .path_utils import (
    get_relative_to_workspace,
    is_claude_path,
    is_csf_nip_path,
    is_projects_path,
    is_workspace_path,
    normalize_path,
    normalize_path_preserve_case,
    to_windows_path,
)

__all__ = [
    "normalize_path",
    "normalize_path_preserve_case",
    "to_windows_path",
    "is_workspace_path",
    "is_csf_nip_path",
    "is_claude_path",
    "is_projects_path",
    "get_relative_to_workspace",
]
