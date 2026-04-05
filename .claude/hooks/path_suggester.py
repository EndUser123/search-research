#!/usr/bin/env python3
from __future__ import annotations

"""
Path Suggester Module
=====================
Provides intelligent path suggestions for optimal file placement.

Consolidated from P:\\__csf\\.claude\\hooks\\ to P:\\.claude\\hooks\\
"""

from pathlib import Path
from typing import Any


class PathSuggester:
    """
    Provides intelligent path suggestions for file placement.
    """

    def __init__(self):
        """Initialize path suggester."""
        self._smart_router = None

    def suggest_appropriate_location(
        self,
        file_path: str,
        content_preview: str = "",
        context: dict[str, Any] | None = None,
        verbose: bool = True,
    ) -> str | None:
        """
        Suggest the most appropriate location for a file.

        Args:
            file_path: The current file path
            content_preview: Optional content preview for better analysis
            context: Additional context for routing decision
            verbose: Whether to print verbose output

        Returns:
            Suggested optimal path or None if no suggestion available
        """
        return self._fallback_suggestion(file_path, verbose)

    def get_directory_mapping(self) -> dict[str, str]:
        """Get mapping of file patterns to suggested directories."""
        return {
            "**/*.py": "P:/__csf/src",
            "**/*.js": "P:/__csf/src",
            "**/*.ts": "P:/__csf/src",
            "**/test_*.py": "P:/tests",
            "**/*_test.py": "P:/tests",
            "**/*.md": "P:/docs",
            "**/*.rst": "P:/docs",
            "pyproject.toml": "P:/",
            "requirements*.txt": "P:/",
            ".env*": "P:/",
        }

    def _fallback_suggestion(self, file_path: str, verbose: bool = True) -> str | None:
        """Provide fallback suggestions based on file patterns."""
        import fnmatch

        if not file_path.startswith("P:/"):
            return None

        filename = Path(file_path).name
        directory_mapping = self.get_directory_mapping()

        if filename in directory_mapping:
            suggested = directory_mapping[filename] + "/" + filename
            if suggested != file_path:
                if verbose:
                    self._print_routing_suggestion(file_path, suggested)
                return suggested

        for pattern, target_dir in directory_mapping.items():
            if fnmatch.fnmatch(filename, pattern):
                if "__csf" in file_path and not target_dir.endswith("__csf"):
                    if target_dir == "P:/__csf/src":
                        target_dir = "P:/__csf/src"
                    elif target_dir == "P:/tests":
                        target_dir = "P:/__csf/tests"
                    elif target_dir == "P:/docs":
                        target_dir = "P:/__csf/docs"

                suggested = target_dir + "/" + filename
                if suggested != file_path:
                    if verbose:
                        self._print_routing_suggestion(file_path, suggested)
                    return suggested

        return None

    def _print_routing_suggestion(self, original_path: str, suggested_path: str) -> None:
        """Log routing suggestion to hook event log."""
        norm_original = original_path.replace("\\", "/")
        norm_suggested = suggested_path.replace("\\", "/")

        display_original = norm_original[3:] if norm_original.startswith("P:/") else norm_original
        display_suggested = norm_suggested[3:] if norm_suggested.startswith("P:/") else norm_suggested

        log_hook_event(
            "path_suggester",
            "info",
            f"Path allowed: {display_original}, Suggested: {display_suggested}"
        )

    def handle_special_cases(
        self,
        file_path: str,
        validation_result: dict[str, Any],
        verbose: bool = True,
    ) -> bool:
        """
        Handle special cases for path validation.

        NOTE: This method should ONLY return True for paths that have already
        been validated as safe by PathValidator. Do NOT allow paths based solely
        on drive letter or other broad criteria.

        Args:
            file_path: The file path to check
            validation_result: Result from PathValidator
            verbose: Whether to print verbose output

        Returns:
            True if special case was handled (and path is safe), False otherwise
        """
        # SECURITY FIX: Removed unconditional is_p_drive check that was
        # bypassing all security validation. The is_p_drive flag indicates
        # the drive, not safety. Safety is determined by PathValidator.
        #
        # Previous buggy code:
        #   if validation_result.get("is_p_drive", False):
        #       return True  # <-- This allowed ALL P:/ writes!

        # Only allow if PathValidator already marked it as safe AND it's a
        # recognized safe violation type (development file, claude root file, etc.)
        if not validation_result.get("is_safe", False):
            return False  # PathValidator says unsafe - don't override

        # For paths validated as safe, provide informational logging
        violation_type = validation_result.get("violation_type", "")

        if violation_type == "DEVELOPMENT_FILE":
            if verbose:
                log_hook_event(
                    "path_suggester",
                    "info",
                    f"Development file allowed: {file_path}"
                )
            return True

        if violation_type == "CLAUDE_ROOT_FILE":
            if verbose:
                log_hook_event(
                    "path_suggester",
                    "info",
                    f"Claude root file allowed: {file_path}"
                )
            return True

        if violation_type == "SAFE_SUBDIRECTORY":
            if verbose:
                rel_path = validation_result.get('relative_path', file_path)
                log_hook_event(
                    "path_suggester",
                    "info",
                    f"Safe subdirectory allowed: {rel_path}"
                )
            return True

        if self._is_claude_system_file(file_path):
            if verbose:
                log_hook_event(
                    "path_suggester",
                    "info",
                    f"Claude system file allowed: {file_path.replace(chr(92), '/')}"
                )
            return True

        return False

    def _is_claude_system_file(self, file_path: str) -> bool:
        """Check if path is a legitimate Claude Code system file."""
        normalized_path = file_path.replace("\\", "/")

        system_patterns = [
            ".claude/skills/",
            ".claude/hooks/",
        ]

        for pattern in system_patterns:
            if normalized_path.startswith(pattern):
                return True

        return False
