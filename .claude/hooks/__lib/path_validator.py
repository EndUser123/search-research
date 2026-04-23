#!/usr/bin/env python3
from __future__ import annotations

"""
Path Validator Module v3.0
==========================
Config-driven path validation for directory structure enforcement.

Single Source of Truth: P:\\.claude\\hooks\\config\\directory_policy.json

Features:
- Runtime path validation for hooks
- CLI validation mode for on-demand checks
- Auto-generation of documentation from features.config
- Suggestion engine for blocked paths

Usage:
    # As module (hook integration)
    from path_validator import PathValidator
    pv = PathValidator()
    result = pv.validate_file_operation(path)

    # CLI validation
    python path_validator.py --validate
    python path_validator.py --validate P:\\__csf

    # Export documentation
    python path_validator.py --export-markdown > CANONICAL_STRUCTURE.md
    python path_validator.py --export-json > policy_export.json
"""

import argparse
import fnmatch
import json
import os
import subprocess  # For git ls-files check in _is_git_tracked()
import sys
import threading
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if PROJECT_ROOT.name == "__lib":  # Handle nested lib case
    PROJECT_ROOT = PROJECT_ROOT.parent
hooks_dir = Path(__file__).resolve().parent
from typing import Any

# import features.performance tracking (Phase 2, Task 3: TSK-251225-HooksOpt-0822)
from .hook_cache import measure_performance


class DirectoryPolicy:
    """
    Loads and provides access to directory policy configuration.
    Single source of truth for all path validation rules.
    """

    DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config/directory_policy.json"

    def __init__(self, config_path: Path | None = None):
        """
        Initialize policy from features.config file.

        Args:
            config_path: Path to policy JSON file (uses default if not specified)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Policy config not found: {self.config_path}", file=sys.stderr)
            print("   Using built-in defaults", file=sys.stderr)
            return self._get_defaults()
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in policy config: {e}", file=sys.stderr)
            return self._get_defaults()

    def _get_defaults(self) -> dict[str, Any]:
        """Return minimal defaults if config cannot be loaded."""
        return {
            "workspace_root": {
                "required_directories": [
                    {"path": ".claude", "purpose": "Claude Code runtime"},
                    {"path": "__csf", "purpose": "CSF framework"},
                    {"path": "projects", "purpose": "Project work"},
                ],
                "allowed_config_files": ["pyproject.toml", ".gitignore", ".env"],
                "allowed_system_directories": [".git", ".github", ".vscode"],
                "ignored_cache_directories": ["__pycache__", ".venv"],
            },
            "claude_directory": {
                "allowed_subdirectories": [
                    {"path": "commands", "purpose": "Slash commands"},
                    {"path": "hooks", "purpose": "Runtime hooks"},
                ],
                "allowed_root_files": ["settings.json"],
                "sensitive_patterns": ["hooks/**/*.py"],
            },
            "csf_nip_directory": {
                "allowed_subdirectories": [
                    {"path": "src", "purpose": "Source code"},
                    {"path": "tests", "purpose": "Tests"},
                ],
                "allowed_root_files": ["pyproject.toml"],
                "blocked_root_patterns": [],
            },
            "module_filename_patterns": {"patterns": []},
            "protected_system_paths": {"paths": ["/"]},
        }

    @property
    def version(self) -> str:
        return self._config.get("_meta", {}).get("version", "unknown")

    @property
    def updated(self) -> str:
        return self._config.get("_meta", {}).get("updated", "unknown")

    # Workspace root accessors
    def get_required_directories(self) -> list[dict[str, str]]:
        return self._config.get("workspace_root", {}).get("required_directories", [])

    def get_required_directories_for_root(self, root_path: str) -> list[dict[str, str]]:
        """
        Get required directories for a specific root path.
        Detects which policy section to use based on the root being validated.

        Args:
            root_path: The root path being validated (e.g., "P:/", "P:/__csf/")

        Returns:
            List of required directory dicts for that root
        """
        from pathlib import Path

        # Normalize root path for comparison
        normalized_root = Path(root_path).as_posix().lower().rstrip("/")

        # If validating __csf/ as its own root, use csf_nip_root policy
        if normalized_root.endswith("p:/__csf") or normalized_root.endswith("__csf"):
            return self._config.get("csf_nip_root", {}).get("required_directories", [])

        # Default to workspace_root policy (for P:/ and other roots)
        return self._config.get("workspace_root", {}).get("required_directories", [])

    def get_allowed_config_files(self) -> list[str]:
        return self._config.get("workspace_root", {}).get("allowed_config_files", [])

    def get_allowed_system_directories(self) -> list[str]:
        return self._config.get("workspace_root", {}).get("allowed_system_directories", [])

    def get_ignored_cache_directories(self) -> list[str]:
        return self._config.get("workspace_root", {}).get("ignored_cache_directories", [])

    # Claude directory accessors
    def get_claude_allowed_subdirs(self) -> list[dict[str, str]]:
        return self._config.get("claude_directory", {}).get("allowed_subdirectories", [])

    def get_claude_root_files(self) -> list[str]:
        return self._config.get("claude_directory", {}).get("allowed_root_files", [])

    def get_claude_sensitive_patterns(self) -> list[str]:
        return self._config.get("claude_directory", {}).get("sensitive_patterns", [])

    # CSF NIP directory accessors
    def get_csf_allowed_subdirs(self) -> list[dict[str, str]]:
        return self._config.get("csf_nip_directory", {}).get("allowed_subdirectories", [])

    def get_csf_root_files(self) -> list[str]:
        return self._config.get("csf_nip_directory", {}).get("allowed_root_files", [])

    def get_csf_blocked_patterns(self) -> list[dict[str, str]]:
        return self._config.get("csf_nip_directory", {}).get("blocked_root_patterns", [])

    # Other accessors
    def get_module_patterns(self) -> list[str]:
        return self._config.get("module_filename_patterns", {}).get("patterns", [])

    def get_protected_paths(self) -> list[str]:
        return self._config.get("protected_system_paths", {}).get("paths", [])

    def get_allowed_external_paths(self) -> dict[str, list[str]]:
        """
        Get external paths allowed for development operations.

        Returns:
            Dictionary with 'patterns' and 'exact_paths' keys containing
            whitelisted external paths outside P:/ workspace.
        """
        external_config = self._config.get("allowed_external_paths", {})
        return {
            "patterns": external_config.get("patterns", []),
            "exact_paths": external_config.get("exact_paths", []),
        }

    def get_full_config(self) -> dict[str, Any]:
        return self._config


class PathValidator:
    """
    Validates file paths against directory policy.
    Config-driven implementation using DirectoryPolicy.
    """

    def __init__(self, config_path: Path | None = None):
        """
        Initialize path validator with policy configuration.

        Args:
            config_path: Optional path to policy config (uses default if not specified)
        """
        self.policy = DirectoryPolicy(config_path)
        self._build_validation_rules()

    def _build_validation_rules(self) -> None:
        """Build validation rule sets from policy config."""
        # Protected roots (lowercase for case-insensitive matching)
        self.protected_roots = ["p:/", "c:/", "/"]

        # Protected system paths
        self.protected_patterns = [p.lower() for p in self.policy.get_protected_paths()]

        # Blocked root patterns for __csf
        self.blocked_root_patterns = [
            p["pattern"].lower() for p in self.policy.get_csf_blocked_patterns()
        ]

        # Blocked root patterns for workspace_root (P:/)
        self.workspace_blocked_root_patterns = self.policy._config.get("workspace_root", {}).get(
            "blocked_root_patterns", []
        )

        # Allowed root patterns for workspace_root (P:/) - default deny
        self.workspace_allowed_root_patterns = self.policy._config.get("workspace_root", {}).get(
            "allowed_root_patterns", []
        )

        # Build suggestion map for blocked patterns
        self.blocked_pattern_suggestions = {
            p["pattern"].lower(): p.get("suggestion", ".staging/{filename}")
            for p in self.policy.get_csf_blocked_patterns()
        }

        # Development files (workspace root config files)
        self.development_files = [f"p:/{f}".lower() for f in self.policy.get_allowed_config_files()]
        # Add __csf root files
        self.development_files.extend(
            [f"p:/__csf/{f}".lower() for f in self.policy.get_csf_root_files()]
        )

        # Module filename patterns (for misplaced module detection)
        self.module_filename_patterns = [p.lower() for p in self.policy.get_module_patterns()]

        # Claude allowed subdirectories
        self.claude_allowed_subdirs = [
            f"p:/.claude/{d['path']}".lower() for d in self.policy.get_claude_allowed_subdirs()
        ]

        # Pre-compute normalized subdirs with trailing slashes (efficiency)
        self.claude_allowed_subdirs_normalized = [
            pattern if pattern.endswith("/") else pattern + "/"
            for pattern in self.claude_allowed_subdirs
        ]

        # Claude allowed root files
        self.claude_root_files = [
            f"p:/.claude/{f}".lower() for f in self.policy.get_claude_root_files()
        ]

        # Pre-compute allowed .md files from config (single source of truth)
        self.allowed_claude_root_md = frozenset(
            {f.lower() for f in self.policy.get_claude_root_files() if f.lower().endswith(".md")}
        )

        # Claude sensitive patterns
        self.claude_sensitive_patterns = [
            p.lower() for p in self.policy.get_claude_sensitive_patterns()
        ]

        # Safe patterns (all allowed write locations)
        self.safe_patterns = []

        # Add Claude subdirs
        self.safe_patterns.extend(self.claude_allowed_subdirs)

        # Add system directories
        for d in self.policy.get_allowed_system_directories():
            self.safe_patterns.append(f"p:/{d}".lower())

        # Add CSF NIP subdirs
        for d in self.policy.get_csf_allowed_subdirs():
            self.safe_patterns.append(f"p:/__csf/{d['path']}".lower())

        # Add projects directory
        self.safe_patterns.append("p:/projects")

    def normalize_path(self, path: str | Path) -> str:
        """Normalize path for cross-platform compatibility.

        Handles:
        - Backslash to forward slash
        - Git Bash /x/ to x:/ conversion (e.g., /p/ -> p:/)
        - Lowercase normalization
        - Path objects (converted to string)
        """
        # Convert Path objects to string
        path_str = str(path) if isinstance(path, Path) else path
        normalized = path_str.replace("\\", "/").lower()

        # Git Bash on Windows: /p/ means P:/ drive
        # Pattern: /x/... where x is a single letter -> x:/...
        if len(normalized) >= 3 and normalized[0] == "/" and normalized[2] == "/":
            drive_letter = normalized[1]
            if drive_letter.isalpha():
                normalized = f"{drive_letter}:{normalized[2:]}"

        return normalized

    @measure_performance
    def is_path_safe(self, file_path: str, project_dir: str | None = None) -> tuple[bool, str]:
        """
        Validate if a path is safe for writing.

        Args:
            file_path: The file path to validate
            project_dir: Optional project directory for bounds checking

        Returns:
            Tuple of (is_safe, violation_type)
        """
        if not file_path:
            return True, "NO_PATH"

        normalized_path = self.normalize_path(file_path)

        # Convert normalized path back to Windows format for Path operations
        # e.g., "p:/__csf/tests" -> "P:/__csf/tests"
        windows_path = normalized_path
        if len(normalized_path) >= 2 and normalized_path[1] == ":":
            windows_path = normalized_path[0].upper() + normalized_path[1:]

        # Get absolute path for validation
        try:
            abs_path = Path(windows_path).resolve()
            abs_path_str = self.normalize_path(str(abs_path))
        except Exception:
            return False, "INVALID_PATH"

        # SECURITY: Check symlink escapes
        if self._is_symlink_escape(windows_path, abs_path_str):
            return False, "SYMLINK_ESCAPE"

        # Check Claude restricted paths (user-only directories)
        is_restricted, suggestion = self._is_claude_restricted_path(abs_path_str)
        if is_restricted:
            return False, f"RESTRICTED_PATH: {suggestion}"

        # BLOCKLIST CHECK - HIGHEST PRIORITY
        if self._is_blocked_pattern(abs_path_str):
            return False, "BLOCKED_PATTERN"

        # WORKSPACE ROOT BLOCKED PATTERNS CHECK (default deny with allowlist)
        if self._is_workspace_blocked_pattern(file_path, abs_path_str):
            return False, "BLOCKED_ROOT_PATTERN"

        # Check development files (allowed root config files)
        if self._is_development_file(abs_path_str):
            return True, "DEVELOPMENT_FILE"

        # Check .claude safe root config files
        if self._is_safe_claude_config(abs_path_str):
            return True, "SAFE_CLAUDE_CONFIG"

        # Check .claude sensitive paths after safe root config allowlist.
        # Exception: Bypass during active hook development session
        if abs_path_str.startswith("p:/.claude/") and self._is_claude_sensitive_path(abs_path_str):
            if not self._is_hook_development_session(abs_path_str):
                return False, "CLAUDE_SENSITIVE_EDIT"

        # Check .claude root files
        if self._is_claude_root_file(abs_path_str):
            return True, "CLAUDE_ROOT_FILE"

        # Check .claude subdirectories
        if abs_path_str.startswith("p:/.claude/"):
            if abs_path_str.startswith("p:/.claude/skills/"):
                if self._is_misplaced_module(abs_path_str):
                    return False, "MISPLACED_MODULE"

            for safe_pattern in self.claude_allowed_subdirs_normalized:
                if abs_path_str.startswith(safe_pattern):
                    return True, "SAFE_SUBDIRECTORY"
            return False, "CLAUDE_SENSITIVE_EDIT"

        # Check protected patterns first
        # Also strip drive prefix and leading slash to handle patterns like "nonexistent/path"
        # that should match "P:/nonexistent/path"
        path_without_drive = abs_path_str
        if len(abs_path_str) >= 3 and abs_path_str[1] == ":":
            path_without_drive = abs_path_str[2:]  # Strip "X:" prefix
        path_without_drive = path_without_drive.replace("\\", "/").lower().lstrip("/")

        for pattern in self.protected_patterns:
            # Check both full path and path without drive prefix
            if abs_path_str.startswith(pattern) or path_without_drive.startswith(pattern):
                return False, "PROTECTED_DIRECTORY_WRITE"

        # EFFICIENCY: Allow edits to existing files (user knows what they're doing)
        if abs_path.exists():
            return True, "EXISTING_FILE_EDIT"

        # EFFICIENCY: Allow edits to git-tracked files (already in project)
        if self._is_git_tracked(file_path):
            return True, "GIT_TRACKED_FILE"

        # Check other safe patterns
        for safe_pattern in self.safe_patterns:
            if abs_path_str.startswith(safe_pattern):
                return True, "SAFE_SUBDIRECTORY"

        # Check if this is a config file at a project root (worktree support)
        if self._is_project_root_file(abs_path_str):
            return True, "PROJECT_ROOT_FILE"

        # Check root-level writes
        if self._is_root_level_write(abs_path_str):
            return False, "ROOT_LEVEL_WRITE"

        # Check project directory bounds
        if project_dir:
            normalized_project_dir = self.normalize_path(project_dir)
            is_project_dir_protected = any(
                normalized_project_dir.rstrip("/") == root.rstrip("/")
                for root in self.protected_roots
            )
            if not is_project_dir_protected:
                if not abs_path_str.startswith(normalized_project_dir):
                    return False, "OUTSIDE_PROJECT_WRITE"

        # Check protected roots
        for root in self.protected_roots:
            try:
                root_path = Path(root)
                if abs_path.is_relative_to(root_path):
                    if abs_path.parent == root_path:
                        return False, "ROOT_DIRECTORY_WRITE"
            except ValueError:
                continue

        # SECURITY: Block unauthorized directories at P:/ root
        # Only allow: .claude, __csf, projects, and allowed_system_directories
        if abs_path_str.startswith("p:/"):
            # Extract the first directory component after p:/
            remainder = abs_path_str[3:]  # Remove "p:/"
            if "/" in remainder:
                first_dir = remainder.split("/")[0]
            else:
                first_dir = remainder

            # Build allowlist from policy
            allowed_root_dirs = set()
            # Required directories (legacy schema: [{path, purpose}])
            for d in self.policy.get_required_directories():
                allowed_root_dirs.add(d["path"].lower())
            # Fallback: allowed_root_patterns schema (config file uses this instead)
            # [{pattern, reason}] - pattern is the directory name
            if not allowed_root_dirs:
                for entry in self.policy._config.get("workspace_root", {}).get("allowed_root_patterns", []):
                    allowed_root_dirs.add(entry["pattern"].lower())
            # System directories
            for d in self.policy.get_allowed_system_directories():
                allowed_root_dirs.add(d.lower())
            # Cache directories (allowed to exist)
            for d in self.policy.get_ignored_cache_directories():
                allowed_root_dirs.add(d.lower())
            # Also allow tmp and backups
            allowed_root_dirs.update({"tmp", "backups"})

            # Check if first directory is allowed
            if first_dir and first_dir not in allowed_root_dirs:
                # Check if it's an allowed config file
                if not self._is_development_file(abs_path_str):
                    return False, "UNAUTHORIZED_ROOT_DIRECTORY"

        return True, "ALLOWED"

    @measure_performance
    def validate_file_operation(
        self, file_path: str, project_dir: str | None = None, enhanced: bool = False
    ) -> dict:
        """
        Comprehensive validation for file operations.

        Args:
            file_path: The file path to validate
            project_dir: Optional project directory for bounds checking
            enhanced: If True, include worktree context detection (CKS-enhanced)

        Returns:
            Dictionary with validation results and optionally worktree context
        """
        is_safe, violation_type = self.is_path_safe(file_path, project_dir)

        result = {
            "file_path": file_path,
            "is_safe": is_safe,
            "violation_type": violation_type,
            "normalized_path": self.normalize_path(file_path),
        }

        if file_path.upper().startswith("P:/"):
            result["is_p_drive"] = True
            result["relative_path"] = file_path[3:]
        else:
            result["is_p_drive"] = False
            result["relative_path"] = file_path

        # Add suggestion for blocked patterns
        if violation_type == "BLOCKED_PATTERN":
            result["suggestion"] = self.get_path_suggestion(file_path)

        # Enhanced mode: Add worktree context detection
        if enhanced:
            worktree_context = self.detect_worktree_context(file_path, "validation")
            result["worktree_context"] = worktree_context

            # Add high-risk alert if applicable
            if worktree_context.get("risk_score", 0) > 0.85:
                result["high_risk_alert"] = True
                result["prevention_guidance"] = worktree_context.get("prevention_guidance")

        return result

    def get_path_suggestion(self, file_path: str) -> str:
        """Get suggested correct path for a blocked file."""
        normalized = self.normalize_path(file_path)
        filename = normalized.split("/")[-1]

        for pattern, suggestion_template in self.blocked_pattern_suggestions.items():
            if fnmatch.fnmatch(filename, pattern):
                # If suggestion is already a complete action (Move to, Delete), don't prepend path
                formatted = suggestion_template.format(filename=filename)
                if formatted.startswith(("Move to", "Delete", "move to", "delete")):
                    return formatted
                return f"P:/__csf/{formatted}"

        return f"P:/__csf/.staging/{filename}"

    def _is_blocked_pattern(self, path: str) -> bool:
        """Check if path matches a blocked pattern at __csf root."""
        if not path.startswith("p:/__csf/"):
            return False

        remainder = path[len("p:/__csf/") :]

        # Check for blocked directory patterns (ending with /) vs file patterns
        for blocked in self.blocked_root_patterns:
            if blocked.endswith("/"):
                # Directory pattern - check if path starts with this pattern
                # e.g., ".claude/" blocks "__csf/.claude/skills/..."
                if remainder.startswith(blocked.rstrip("/").lower()):
                    return True
            else:
                # File pattern - only check root-level files
                if "/" in remainder:
                    continue
                if fnmatch.fnmatch(remainder, blocked):
                    return True

        return False

    def _is_workspace_blocked_pattern(
        self, original_path: str, normalized_path: str | None = None
    ) -> bool:
        """Check if path is blocked at workspace root (P:/).

        Uses DEFAULT DENY with allowlist - only paths in allowed_root_patterns are allowed.
        All other paths at P:/ root are blocked.

        Args:
            original_path: Original file path before normalization (preserves P: corruption)
            normalized_path: Normalized path (optional, for consistency checks)

        Returns:
            True if path is blocked, False if allowed
        """

        def is_allowed(remainder: str) -> bool:
            """Helper to check if remainder is in the allowlist."""
            for pattern_info in self.workspace_allowed_root_patterns:
                pattern = pattern_info["pattern"].rstrip("/")
                # Allow if: remainder equals pattern OR starts with pattern/
                # This allows P:/__csf, P:/__csf/, and P:/__csf/anything
                remainder_lower = remainder.lower()
                pattern_lower = pattern.lower()
                if remainder_lower == pattern_lower or remainder_lower.startswith(
                    f"{pattern_lower}/"
                ):
                    return True
            return False

        # Check blocked patterns first (explicit blocks override allowlist)
        remainder = original_path[3:] if original_path.startswith("P:/") else normalized_path[3:]
        for blocked in self.workspace_blocked_root_patterns:
            blocked_lower = blocked["pattern"].lower().rstrip("/")
            remainder_lower = remainder.lower()
            if remainder_lower == blocked_lower or remainder_lower.startswith(blocked_lower + "/"):
                return True

        # Check the ORIGINAL path first (before Windows normalization)
        # This catches "P:/P:corrupted.py" style paths
        if original_path.startswith("P:/"):
            remainder = original_path[3:]  # Remove "P:/"
            if not is_allowed(remainder):
                return True

        # Also check normalized path
        if normalized_path is None:
            normalized_path = self.normalize_path(original_path)

        if normalized_path.startswith("p:/"):
            remainder = normalized_path[3:]
            if not is_allowed(remainder):
                return True

        return False

    def _is_development_file(self, path: str) -> bool:
        """Check if path matches a legitimate development file."""
        return path in self.development_files

    def _is_claude_root_file(self, path: str) -> bool:
        """Check if path is an allowed .claude root file."""
        return path in self.claude_root_files

    def _is_safe_claude_config(self, path: str) -> bool:
        """Allow safe config-like files at .claude root."""
        if not path.startswith("p:/.claude/"):
            return False

        relative = path.removeprefix("p:/.claude/")
        if not relative or "/" in relative:
            return False

        # Normalize once (efficiency: avoid duplicate .lower() calls)
        relative_lower = relative.lower()

        protected_files = {"settings.json", "settings.local.json"}
        if relative_lower in protected_files:
            return False

        safe_dotfiles = {".claudeignore", ".rgignore", ".editorconfig"}
        safe_extensions = {".yaml", ".yml", ".toml", ".ini", ".cfg", ".txt"}
        _, ext = os.path.splitext(relative)
        ext_lower = ext.lower()  # Pre-compute to avoid duplicate .lower() calls

        if ext_lower == ".md":
            return True

        return relative_lower in safe_dotfiles or ext_lower in safe_extensions

    def _is_hook_development_session(self, path: str) -> bool:
        """Check if there's an active hook development session that bypasses consent.

        During active hook development (30-minute window), edits to .claude/hooks/
        bypass the normal consent requirement to reduce friction.

        Returns:
            True if active hook development session exists, False otherwise
        """
        if not path.startswith("p:/.claude/hooks/"):
            return False

        # Check for session marker file
        # Pattern: hook_dev_session_{session_id}.json
        try:
            hooks_dir = Path(__file__).resolve().parent.parent
            session_data_dir = hooks_dir / "session_data"

            # Try to get session_id from environment first
            session_id = os.environ.get("CLAUDE_SESSION_ID", "")
            if not session_id:
                return False

            marker_file = session_data_dir / f"hook_dev_session_{session_id}.json"

            if not marker_file.exists():
                return False

            # Check if session is still valid (30-minute window)
            data = json.loads(marker_file.read_text(encoding="utf-8"))
            start_time = data.get("start_time", 0)
            current_time = time.time()

            # Session expires after 30 minutes (1800 seconds)
            if current_time - start_time > 1800:
                # Clean up expired session
                marker_file.unlink(missing_ok=True)
                return False

            return True

        except (json.JSONDecodeError, OSError, KeyError):
            # If marker file is corrupted or unreadable, don't bypass
            return False

    def _is_claude_sensitive_path(self, path: str) -> bool:
        """Match .claude relative path against sensitive patterns."""
        if not path.startswith("p:/.claude/"):
            return False

        relative = path.removeprefix("p:/.claude/")
        if not relative:
            return False

        for pattern in self.claude_sensitive_patterns:
            normalized_pattern = pattern.removeprefix("p:/.claude/").lower()
            if fnmatch.fnmatch(relative, normalized_pattern):
                return True
            # Treat /**/ as zero-or-more dirs for fnmatch compatibility.
            if "/**/" in normalized_pattern:
                alt_pattern = normalized_pattern.replace("/**/", "/")
                if fnmatch.fnmatch(relative, alt_pattern):
                    return True
            if normalized_pattern.startswith("**/"):
                alt_pattern = normalized_pattern[3:]
                if fnmatch.fnmatch(relative, alt_pattern):
                    return True
            if normalized_pattern.startswith("*/"):
                alt_pattern = normalized_pattern[2:]
                if fnmatch.fnmatch(relative, alt_pattern):
                    return True
            if normalized_pattern.startswith("hooks/**/*.") and relative.startswith("hooks/"):
                ext = normalized_pattern.split("*.", 1)[-1]
                if relative.endswith(f".{ext}"):
                    return True
            if (
                normalized_pattern.startswith("hooks/**/*.py")
                and relative.startswith("hooks/")
                and relative.endswith(".py")
            ):
                return True
        return False

    def _is_symlink_escape(self, original_path: str, resolved_path: str) -> bool:
        """Check if a symlink resolves outside its apparent directory."""
        original_normalized = self.normalize_path(original_path)

        if original_normalized.startswith("p:/.claude/"):
            # Allow skill aliases under .claude/skills to resolve into trusted
            # workspace roots (e.g., junctions to packaged skills).
            if original_normalized.startswith("p:/.claude/skills/"):
                trusted_skill_targets = (
                    "p:/.claude/skills/",
                    "p:/packages/",
                    "p:/projects/",
                )
                if any(resolved_path.startswith(prefix) for prefix in trusted_skill_targets):
                    return False
            if not resolved_path.startswith("p:/.claude/"):
                return True

        if original_normalized.startswith("p:/__csf/"):
            if not resolved_path.startswith("p:/__csf/"):
                return True

        if original_normalized.startswith("p:/projects/"):
            if not resolved_path.startswith("p:/projects/"):
                return True

        return False

    def _is_claude_restricted_path(self, path: str) -> tuple[bool, str | None]:
        """Check if path is in Claude's restricted paths list.

        These paths are reserved for user-authored content. Claude should not
        write to them without explicit user consent.

        Returns:
            Tuple of (is_restricted, suggested_alternative)
        """
        restricted = self.policy._config.get("claude_restricted_paths", {}).get("paths", [])
        normalized = self.normalize_path(path)

        for entry in restricted:
            pattern = entry.get("path", "").lower()
            if not pattern.endswith("/"):
                pattern = pattern + "/"

            if normalized.startswith(f"p:/{pattern}"):
                suggestion = entry.get("suggested_alternative", ".claude/docs/")
                return True, suggestion

        return False, None

    def _is_git_tracked(self, file_path: str) -> bool:
        """Check if a file is tracked by git in the repository."""
        try:
            file_dir = Path(file_path).parent
            CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", str(file_path)],
                cwd=file_dir,
                capture_output=True,
                text=True,
                timeout=2,
                creationflags=CREATE_NO_WINDOW,
            )
            return bool(result.stdout.strip())
        except Exception:
            return False

    def _is_root_level_write(self, path: str) -> bool:
        """
        Check if this is a write directly at a protected root level.

        Only blocks writes where the PARENT directory is a protected root,
        not all writes under that root (which would block everything).
        """
        from pathlib import PurePosixPath

        # Extract parent directory
        p = PurePosixPath(path)
        parent = str(p.parent).lower().rstrip("/") + "/"

        # Check if parent IS a protected root (not just starts with)
        for root in self.protected_roots:
            if parent == root:
                return True
        return False

    def _is_project_root_file(self, path: str) -> bool:
        """
        Check if path is a config file at the root of a project under P:/projects/.

        Detects git repositories (worktrees or regular) and allows standard
        config files at their root level.
        """
        # Must be under p:/projects/
        if not path.startswith("p:/projects/"):
            return False

        # Extract the path relative to p:/projects/
        rel_path = path[len("p:/projects/") :]
        parts = rel_path.split("/")

        # Need at least project_name/filename
        if len(parts) < 2:
            return False

        # Check if this is at the root of a project (only one level deep in project)
        # e.g., p:/projects/my-project/file.md -> parts = ["my-project", "file.md"]
        # e.g., p:/projects/my-project/src/file.py -> parts = ["my-project", "src", "file.py"]

        # Find the project root by looking for .git
        project_name = parts[0]
        potential_project_root = f"P:/projects/{project_name}"

        # Check if this directory is a git repo (regular or worktree)
        git_dir = os.path.join(potential_project_root, ".git")
        is_git_repo = os.path.exists(git_dir)  # Works for both file (worktree) and directory

        if not is_git_repo:
            return False

        # Check if file is at project root (exactly 2 parts: project_name/filename)
        if len(parts) == 2:
            filename = parts[1]
            # Allow common project config files at project root
            allowed_project_root_patterns = [
                ".claude-*.md",  # Claude worktree configs
                ".claude*.md",  # Claude configs
                "CLAUDE.md",  # Claude project config
                "claude.md",
                "README.md",
                "README.rst",
                "LICENSE",
                "LICENSE.md",
                "CHANGELOG.md",
                "CONTRIBUTING.md",
                ".gitignore",
                ".gitattributes",
                ".editorconfig",
                "pyproject.toml",
                "setup.py",
                "setup.cfg",
                "package.json",
                "Cargo.toml",
                "go.mod",
                "Makefile",
                "Dockerfile",
                "docker-compose.yml",
                "docker-compose.yaml",
                ".env",
                ".env.example",
                "requirements.txt",
                "requirements-dev.txt",
            ]

            for pattern in allowed_project_root_patterns:
                if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                    return True

        return False

    def _is_misplaced_module(self, path: str) -> bool:
        """Check if a .py file in .claude/skills/ is a misplaced module."""
        if not path.endswith(".py"):
            return False

        if not path.startswith("p:/.claude/skills/"):
            return False

        filename = path.split("/")[-1]

        for pattern in self.module_filename_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    # ========== Worktree Context Detection Methods ==========

    def detect_worktree_context(self, file_path: str, operation_type: str) -> dict[str, Any]:
        """
        Detect worktree context and capture patterns for CKS storage.
        Returns worktree context information and stores patterns to CKS.

        Performance: <10ms deterministic check

        Args:
            file_path: The file path being validated
            operation_type: Type of operation (e.g., "write", "read", "delete")

        Returns:
            Dictionary with worktree context information including:
            - is_worktree_operation: Whether this is a worktree-related operation
            - current_worktree: Detected current worktree (if any)
            - risk_score: Computed risk score (0.0-1.0)
            - risk_indicators: List of detected risk patterns
            - prevention_guidance: Suggested prevention strategies (if high risk)
        """
        context = {
            "file_path": file_path,
            "operation_type": operation_type,
            "is_worktree_operation": False,
            "current_worktree": None,
            "risk_score": 0.0,
            "risk_indicators": [],
            "prevention_guidance": None,
            "timestamp": datetime.now().isoformat(),
        }

        # Fast path: non-P: drive operations are not worktree-related
        if not file_path.upper().startswith("P:/"):
            return context

        try:
            # Detect if we're in a git worktree
            worktree_info = self._detect_current_worktree(file_path)
            context["is_worktree_operation"] = worktree_info["is_worktree"]
            context["current_worktree"] = worktree_info.get("worktree_name")

            # Always analyze risk patterns for P: drive paths (not just worktrees)
            # Risk patterns exist regardless of worktree status
            risk_analysis = self._analyze_worktree_risk(file_path)
            context["risk_score"] = risk_analysis["risk_score"]
            context["risk_indicators"] = risk_analysis["indicators"]

            # Generate prevention guidance for medium and high-risk scenarios
            if risk_analysis["risk_score"] >= 0.5:  # Lowered from 0.7, use >= to include 0.5
                context["prevention_guidance"] = self._generate_prevention_guidance(
                    file_path, worktree_info, risk_analysis
                )

                # Asynchronously store pattern to CKS for future learning
                self._store_worktree_pattern_async(context)

        except Exception as e:
            # Graceful degradation - worktree detection failure should not break validation
            context["risk_indicators"].append(f"worktree_detection_error: {str(e)}")

        return context

    def _detect_current_worktree(self, file_path: str) -> dict[str, Any]:
        """
        Detect if current operation is in a git worktree and identify which one.

        Performance: <5ms

        Returns:
            Dictionary with:
            - is_worktree: Boolean indicating if in a worktree
            - worktree_name: Name of the worktree (if detected)
            - worktree_path: Path to the worktree root
        """
        result = {"is_worktree": False, "worktree_name": None, "worktree_path": None}

        try:
            # Convert to absolute path
            abs_path = Path(file_path).resolve()

            # Walk up directory tree looking for .git file (worktree marker) or .git directory (regular repo)
            current = abs_path
            max_levels = 5  # Don't search too far up

            for _ in range(max_levels):
                git_file = current / ".git"
                git_dir = current / ".git"

                # Worktree: .git is a file containing "gitdir: <path>"
                if git_file.is_file():
                    try:
                        content = git_file.read_text().strip()
                        if content.startswith("gitdir:"):
                            result["is_worktree"] = True
                            result["worktree_path"] = str(current)

                            # Extract worktree name from path
                            # e.g., "P:/projects/yt-fts-alt-platforms" -> "yt-fts-alt-platforms"
                            path_parts = current.parts
                            if len(path_parts) > 0:
                                result["worktree_name"] = path_parts[-1]
                            break
                    except Exception:
                        pass

                # Regular git repository (not a worktree)
                elif git_dir.is_dir():
                    # This is a regular git repo, not a worktree
                    result["is_worktree"] = False
                    result["worktree_path"] = str(current)
                    break

                # Move up one directory
                if current.parent == current:  # Reached root
                    break
                current = current.parent

        except Exception:
            # Graceful degradation on any error
            pass

        return result

    def _analyze_worktree_risk(self, file_path: str) -> dict[str, Any]:
        """
        Analyze potential worktree confusion risks based on path patterns.
        Detects patterns like "alt-platforms" confusion scenarios.

        Performance: <5ms pattern analysis

        Returns:
            Dictionary with:
            - risk_score: Float from 0.0 (low risk) to 1.0 (high risk)
            - indicators: List of detected risk patterns
            - similar_incidents: List of similar historical incidents (if known)
        """
        result = {"risk_score": 0.0, "indicators": [], "similar_incidents": []}

        try:
            normalized_path = self.normalize_path(file_path).lower()

            # Risk Pattern 1: Similar naming indicators (yt-fts-alt-platforms scenario)
            confusion_patterns = [
                "alt-",
                "alt_",
                "-alt",
                "_alt",
                "platform",
                "platforms",
                "backup",
                "-backup",
                "_backup",
                "test",
                "-test",
                "_test",
                "temp",
                "-temp",
                "_temp",
                "old",
                "-old",
                "_old",
                "v2",
                "-v2",
                "_v2",
                "copy",
                "-copy",
                "_copy",
            ]

            path_parts = normalized_path.split("/")
            for part in path_parts:
                for pattern in confusion_patterns:
                    if pattern in part:
                        result["indicators"].append(f"similar_naming: {pattern} detected in {part}")
                        result["risk_score"] += 0.15

            # Risk Pattern 2: Multiple project directories
            if "projects/" in normalized_path:
                # Extract project name
                if "/projects/" in normalized_path:
                    proj_start = normalized_path.index("/projects/") + len("/projects/")
                    proj_parts = normalized_path[proj_start:].split("/")
                    if len(proj_parts) > 0:
                        project_name = proj_parts[0]
                        # Check for risk indicators in project name
                        if any(
                            p in project_name
                            for p in ["alt", "backup", "test", "temp", "old", "v2", "copy"]
                        ):
                            result["indicators"].append(f"project_naming_risk: {project_name}")
                            risk_boost = (
                                0.25  # Increased from 0.20 to push backup patterns over 0.5
                            )
                            result["risk_score"] += risk_boost

                            # Extra boost for "backup" which is commonly confusing
                            if "backup" in project_name:
                                result["risk_score"] += 0.10  # Additional boost for backup

            # Risk Pattern 3: Operations in project root without explicit verification
            if normalized_path.count("/") <= 3 and normalized_path.startswith("p:/projects/"):
                result["indicators"].append("root_level_operation: high navigation risk")
                result["risk_score"] += 0.10

            # Cap risk score at 1.0
            result["risk_score"] = min(result["risk_score"], 1.0)

            # Known historical incidents
            if "alt-platforms" in normalized_path or "alt_platforms" in normalized_path:
                result["similar_incidents"].append("yt-fts-alt-platforms confusion (2024-12)")
                result["risk_score"] = max(result["risk_score"], 0.85)  # Elevate risk significantly

        except Exception:
            # Graceful degradation
            result["indicators"].append("risk_analysis_error: pattern matching failed")

        return result

    def _generate_prevention_guidance(
        self, file_path: str, worktree_info: dict, risk_analysis: dict
    ) -> str:
        """
        Generate specific prevention guidance based on CKS patterns and historical incidents.

        Returns:
            User-friendly prevention guidance message
        """
        guidance_parts = []

        worktree_name = worktree_info.get("worktree_name", "unknown")
        risk_score = risk_analysis["risk_score"]

        # Header based on risk level
        if risk_score >= 0.85:
            guidance_parts.append("🚨 HIGH RISK: Worktree confusion likely")
        elif risk_score >= 0.7:
            guidance_parts.append("⚠️ MEDIUM RISK: Worktree confusion possible")
        else:
            guidance_parts.append("ℹ️ Information: Worktree operation detected")

        # Current worktree context
        guidance_parts.append(f"Current worktree: {worktree_name}")

        # Risk indicators
        if risk_analysis["indicators"]:
            guidance_parts.append("Detected risk patterns:")
            for indicator in risk_analysis["indicators"][:3]:  # Limit to top 3
                guidance_parts.append(f"  - {indicator}")

        # Prevention strategies
        guidance_parts.append("Prevention strategies:")
        guidance_parts.append("  1. Verify current worktree: `git worktree list`")
        guidance_parts.append("  2. Confirm intended target before operations")
        guidance_parts.append("  3. Use full paths to avoid ambiguity")

        # Historical incidents reference
        if risk_analysis["similar_incidents"]:
            guidance_parts.append(f"Similar incident: {risk_analysis['similar_incidents'][0]}")

        return "\n".join(guidance_parts)

    def _store_worktree_pattern_async(self, context: dict[str, Any]) -> None:
        """
        Asynchronously store worktree patterns to CKS using existing bridge.
        Non-blocking operation with error handling.

        This runs in a background thread to avoid blocking the main validation flow.
        """

        def store_pattern():
            try:
                # import features.cks bridge here to avoid circular import
                # This is executed in background thread, so import cost is acceptable
                import os
                import sys

                # Path to CKS bridge
                cks_bridge_path = "P:/__csf/src/features/core_utils/claude_code_cks_bridge.py"

                if not os.path.exists(cks_bridge_path):
                    return  # CKS bridge not available, skip storage

                # Add to path if needed
                bridge_dir = os.path.dirname(cks_bridge_path)
                if bridge_dir not in sys.path:
                    sys.path.insert(0, bridge_dir)

                # Import and use CKS bridge
                # Note: This is a simplified integration - full implementation would use
                # the actual CKS bridge API for storing worktree patterns
                # For now, we'll use a simple file-based fallback

                pattern_storage_dir = PROJECT_ROOT / "__csf" / ".speckit/memory/worktree_patterns"
                pattern_storage_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pattern_file = pattern_storage_dir / f"pattern_{timestamp}.json"

                pattern_data = {
                    "type": "worktree_confusion_pattern",
                    "context": context,
                    "stored_at": timestamp,
                }

                with open(pattern_file, "w") as f:
                    json.dump(pattern_data, f, indent=2)

            except Exception:
                # Silent failure - pattern storage should never break validation
                pass

        # Run in background thread for non-blocking operation
        thread = threading.Thread(target=store_pattern, daemon=True)
        thread.start()


class DirectoryValidator:
    """
    Validates actual directory structure against policy.
    Used for on-demand validation via CLI.
    """

    def __init__(self, policy: DirectoryPolicy | None = None):
        self.policy = policy or DirectoryPolicy()

    def validate_workspace(self, root_path: str = "P:/") -> dict[str, Any]:
        """
        Validate workspace structure against policy.

        Returns:
            Dictionary with validation results
        """
        root = Path(root_path)
        results = {
            "timestamp": datetime.now().isoformat(),
            "policy_version": self.policy.version,
            "root_path": str(root),
            "required_directories": [],
            "violations": [],
            "warnings": [],
            "summary": {},
        }

        # Check required directories
        for req_dir in self.policy.get_required_directories_for_root(root_path):
            dir_path = root / req_dir["path"]
            exists = dir_path.exists() and dir_path.is_dir()
            results["required_directories"].append(
                {"path": req_dir["path"], "purpose": req_dir["purpose"], "exists": exists}
            )
            if not exists:
                results["violations"].append(
                    {
                        "type": "MISSING_REQUIRED_DIRECTORY",
                        "path": str(dir_path),
                        "message": f"Required directory missing: {req_dir['path']}",
                    }
                )

        # Check for prohibited items at root
        self._check_root_violations(root, results)

        # Check __csf internal structure
        if (root / "__csf").exists():
            self._check_csf_nip_structure(root / "__csf", results)

        # Check .claude structure
        if (root / ".claude").exists():
            self._check_claude_structure(root / ".claude", results)

        # Generate summary
        results["summary"] = {
            "required_dirs_present": sum(1 for d in results["required_directories"] if d["exists"]),
            "required_dirs_total": len(results["required_directories"]),
            "violation_count": len(results["violations"]),
            "warning_count": len(results["warnings"]),
            "compliant": len(results["violations"]) == 0,
        }

        return results

    def _check_root_violations(self, root: Path, results: dict) -> None:
        """Check for prohibited items at workspace root (both files AND directories)."""
        # Skip workspace_root blocked patterns when validating __csf/ as its own root
        # (data/, logs/, etc. are legitimate subdirectories of __csf/)
        normalized_root = str(root).lower().rstrip("/")
        if normalized_root.endswith("p:/__csf") or normalized_root.endswith("__csf"):
            return

        # Check blocked root patterns from policy (for both files AND directories)
        blocked_patterns = self.policy._config.get("workspace_root", {}).get(
            "blocked_root_patterns", []
        )

        for item in root.iterdir():
            item_name = item.name
            item_type = "dir" if item.is_dir() else "file"

            # Check against blocked patterns
            for pattern_info in blocked_patterns:
                pattern = pattern_info["pattern"]
                # Remove trailing slash from pattern for matching
                pattern = pattern.rstrip("/")

                # Match item name against pattern (works for both files and directories)
                if fnmatch.fnmatch(item_name.lower(), pattern.lower()):
                    # Determine violation type based on what we found
                    if item_type == "dir":
                        violation_type = "BLOCKED_ROOT_DIRECTORY"
                    else:
                        violation_type = "BLOCKED_ROOT_FILE"

                    results["violations"].append(
                        {
                            "type": violation_type,
                            "path": str(item),
                            "message": pattern_info["reason"],
                            "suggestion": pattern_info.get(
                                "suggestion", f"Move to __csf/.staging/{item_name}"
                            ),
                        }
                    )
                    break  # Only match first pattern

    def _check_csf_nip_structure(self, csf_path: Path, results: dict) -> None:
        """Check __csf internal structure for blocked files AND directories."""
        # Get allowed files to exclude from blocked pattern matching
        allowed_files = [f.lower() for f in self.policy.get_csf_root_files()]
        allowed_dirs = [d["path"].lower() for d in self.policy.get_csf_allowed_subdirs()]

        # Check for blocked patterns at root (both files and directories)
        for item in csf_path.iterdir():
            item_name = item.name.lower()
            item_type = "dir" if item.is_dir() else "file"

            # Skip if explicitly allowed
            if item_type == "file" and item_name in allowed_files:
                continue
            if item_type == "dir" and item_name in allowed_dirs:
                continue

            for pattern_info in self.policy.get_csf_blocked_patterns():
                pattern = pattern_info["pattern"].lower()

                # Match directory names or filenames against pattern
                # Directory patterns end with '/', file patterns don't
                if fnmatch.fnmatch(item_name, pattern.rstrip("/").lower()):
                    suggestion = pattern_info.get("suggestion", ".staging/{filename}")

                    # Determine violation type based on what we found
                    if item_type == "dir":
                        violation_type = "BLOCKED_ROOT_DIRECTORY"
                    else:
                        violation_type = "BLOCKED_ROOT_FILE"

                    results["violations"].append(
                        {
                            "type": violation_type,
                            "path": str(item),
                            "message": pattern_info["reason"],
                            "suggestion": f"__csf/{suggestion.format(filename=item.name)}",
                        }
                    )
                    break

    def _check_claude_structure(self, claude_path: Path, results: dict) -> None:
        """Check .claude internal structure."""
        allowed_subdirs = [d["path"].lower() for d in self.policy.get_claude_allowed_subdirs()]
        allowed_files = [f.lower() for f in self.policy.get_claude_root_files()]

        for item in claude_path.iterdir():
            if item.is_dir():
                if item.name.lower() not in allowed_subdirs:
                    results["warnings"].append(
                        {
                            "type": "UNKNOWN_CLAUDE_SUBDIR",
                            "path": str(item),
                            "message": f"Unexpected directory in .claude/: {item.name}",
                        }
                    )
            elif item.is_file():
                if item.name.lower() not in allowed_files:
                    results["warnings"].append(
                        {
                            "type": "UNKNOWN_CLAUDE_FILE",
                            "path": str(item),
                            "message": f"Unexpected file in .claude/: {item.name}",
                        }
                    )


class CleanupPromptGenerator:
    """
    Generates structured prompts for LLM-assisted cleanup of policy violations.
    """

    def __init__(self, policy: DirectoryPolicy | None = None):
        self.policy = policy or DirectoryPolicy()
        self.validator = DirectoryValidator(self.policy)

    def generate_cleanup_prompt(self, root_path: str = "P:/", max_files: int = 50) -> str:
        """
        Generate a structured prompt for LLM to review and clean up violations.

        Args:
            root_path: Root path to validate
            max_files: Maximum number of files to include in prompt

        Returns:
            Structured prompt string for LLM consumption
        """
        results = self.validator.validate_workspace(root_path)
        violations = results["violations"][:max_files]

        if not violations:
            return "# No Violations Found\n\nThe workspace is compliant with directory policy. No cleanup needed."

        lines = [
            "# Directory Structure Cleanup Task",
            "",
            "## Context",
            "",
            f"Policy Version: {results['policy_version']}",
            f"Violations Found: {len(results['violations'])}",
            f"Files Listed Below: {len(violations)}",
            "",
            "You are tasked with cleaning up files that violate the directory structure policy.",
            "For each file, you must determine whether to **MOVE** or **DELETE** it.",
            "",
            "## Review Criteria",
            "",
            "For each file, evaluate:",
            "",
            "### 1. Reference Analysis",
            '- Is this file imported by other Python files? (`grep -r "from <module>" P:/__csf/src/`)',
            "- Is it referenced in any configuration files?",
            "- Are there any hardcoded paths pointing to this file?",
            "",
            "### 2. Content Value",
            "- Does the file contain unique, non-trivial code or data?",
            "- Is it a duplicate of something already in the correct location?",
            "- Was it a temporary/scratch file that served its purpose?",
            "",
            "### 3. Recency & Activity",
            "- When was the file last modified? (`stat <file>`)",
            "- Is it part of an active development effort?",
            "- Has it been superseded by newer work?",
            "",
            "### 4. Test Coverage",
            "- If it's a test file, does it test code that still exists?",
            "- Are the tests passing? (`pytest <file> -v`)",
            "- Is there already test coverage for this functionality in `tests/`?",
            "",
            "### 5. Documentation Value",
            "- If it's a report/doc, is the information still relevant?",
            "- Has it been incorporated into official documentation?",
            "",
            "## Decision Framework",
            "",
            "```",
            "MOVE if:",
            "  - File is referenced by other code",
            "  - Contains unique, valuable content",
            "  - Recently modified (< 30 days) and part of active work",
            "  - Tests that cover existing functionality",
            "",
            "DELETE if:",
            "  - No references found anywhere",
            "  - Duplicate of existing file in correct location",
            "  - Temporary/scratch file (names like test_*, fix_*, simple_*)",
            "  - Old reports superseded by newer versions",
            "  - Tests for code that no longer exists",
            "  - Last modified > 30 days with no references",
            "```",
            "",
            "## Files to Review",
            "",
        ]

        # Group violations by type
        by_type: dict[str, list[dict]] = {}
        for v in violations:
            vtype = v["type"]
            if vtype not in by_type:
                by_type[vtype] = []
            by_type[vtype].append(v)

        file_num = 1
        for vtype, vlist in by_type.items():
            lines.append(f"### {vtype.replace('_', ' ').title()}")
            lines.append("")

            for v in vlist:
                filepath = v["path"]
                filename = Path(filepath).name
                suggestion = v.get("suggestion", "Unknown")
                reason = v.get("message", "Policy violation")

                lines.append(f"#### File {file_num}: `{filename}`")
                lines.append("")
                lines.append(f"- **Full Path**: `{filepath}`")
                lines.append(f"- **Violation**: {reason}")
                lines.append(f"- **Suggested Location**: `{suggestion}`")
                lines.append("")
                lines.append("**Analysis Commands:**")
                lines.append("```bash")
                lines.append("# Check references")

                if filename.endswith(".py"):
                    module_name = filename[:-3]
                    lines.append(
                        f"grep -r \"{module_name}\" P:/__csf/src/ --include='*.py' | head -10"
                    )
                    lines.append(
                        f"grep -r \"from.*{module_name}\" P:/__csf/ --include='*.py' | head -10"
                    )
                elif filename.endswith(".json"):
                    lines.append(
                        f"grep -r \"{filename}\" P:/__csf/ --include='*.py' --include='*.md' | head -10"
                    )
                else:
                    lines.append(f'grep -r "{filename}" P:/__csf/ | head -10')

                lines.append("")
                lines.append("# Check file age and size")
                lines.append(f'stat "{filepath}"')

                if filename.endswith(".py"):
                    lines.append("")
                    lines.append("# Quick content preview")
                    lines.append(f'head -30 "{filepath}"')

                    if filename.startswith("test_"):
                        lines.append("")
                        lines.append("# Run tests to check if they pass")
                        lines.append(
                            f"pytest \"{filepath}\" -v --tb=short 2>/dev/null || echo 'Tests failed or errored'"
                        )

                lines.append("```")
                lines.append("")
                lines.append(
                    "**Decision**: [ ] MOVE to suggested location  [ ] DELETE  [ ] SKIP (needs manual review)"
                )
                lines.append("")
                lines.append("**Reasoning**: _Fill in after analysis_")
                lines.append("")
                lines.append("---")
                lines.append("")
                file_num += 1

        # Execution section
        lines.extend(
            [
                "## Execution Plan",
                "",
                "After reviewing all files, execute the cleanup:",
                "",
                "### Files to Move",
                "```bash",
                "# Template - fill in after review",
                "# mkdir -p P:/__csf/tests/",
                '# mv "P:/__csf/test_example.py" "P:/__csf/tests/test_example.py"',
                "```",
                "",
                "### Files to Delete",
                "```bash",
                "# Template - fill in after review",
                '# rm "P:/__csf/old_scratch_file.py"',
                "```",
                "",
                "### Verification",
                "```bash",
                "# After cleanup, verify compliance",
                "python P:\\.claude\\hooks\\path_validator.py --validate",
                "```",
                "",
                "## Important Notes",
                "",
                "1. **Backup first**: Run `sl status` and `sl commit -m 'pre-cleanup checkpoint'` before making changes",
                "2. **Batch by confidence**: Process obvious deletions first, then moves, then uncertain files",
                "3. **Test after moves**: If moving test files, run `pytest` to ensure imports still work",
                "4. **Update imports**: If a file is moved, update any files that import from it",
            ]
        )

        return "\n".join(lines)


class DocumentationGenerator:
    """
    Generates documentation from policy configuration.
    """

    def __init__(self, policy: DirectoryPolicy | None = None):
        self.policy = policy or DirectoryPolicy()

    def generate_markdown(self) -> str:
        """Generate canonical directory structure documentation."""
        lines = [
            "# Canonical P:\\ Directory Structure",
            "",
            f"**Version:** {self.policy.version}",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "**Source:** `P:\\.claude\\hooks\\config\\directory_policy.json`",
            "**Enforced By:** `P:\\.claude\\hooks\\deny_root_write.py`",
            "",
            "> ⚠️ This file is auto-generated. Edit `directory_policy.json` instead.",
            "",
            "---",
            "",
            "## P:\\ Root (Minimal)",
            "",
            "```",
            "P:\\",
        ]

        # Required directories
        for req_dir in self.policy.get_required_directories_for_root(root_path):
            lines.append(f"├── {req_dir['path']}/".ljust(25) + f"# {req_dir['purpose']}")

        # System directories
        for sys_dir in self.policy.get_allowed_system_directories():
            lines.append(f"├── {sys_dir}/".ljust(25) + "# (system)")

        lines.append("└── [config files]".ljust(25) + "# pyproject.toml, .env, etc.")
        lines.append("```")
        lines.append("")

        # Required directories table
        lines.append("### Required Directories")
        lines.append("")
        lines.append("| Directory | Purpose |")
        lines.append("|-----------|---------|")
        for req_dir in self.policy.get_required_directories_for_root(root_path):
            lines.append(f"| `{req_dir['path']}/` | {req_dir['purpose']} |")
        lines.append("")

        # Allowed config files
        lines.append("### Allowed Root Config Files")
        lines.append("")
        lines.append("```")
        config_files = self.policy.get_allowed_config_files()
        # Group by category
        lines.append(", ".join(config_files[:10]))
        if len(config_files) > 10:
            lines.append(", ".join(config_files[10:20]))
        if len(config_files) > 20:
            lines.append(", ".join(config_files[20:]))
        lines.append("```")
        lines.append("")

        # __csf structure
        lines.append("---")
        lines.append("")
        lines.append("## P:\\__csf\\ Structure")
        lines.append("")
        lines.append("```")
        lines.append("P:\\__csf\\")
        for subdir in self.policy.get_csf_allowed_subdirs():
            lines.append(f"├── {subdir['path']}/".ljust(25) + f"# {subdir['purpose']}")
        lines.append("```")
        lines.append("")

        # Blocked patterns
        lines.append("### Blocked Root Patterns")
        lines.append("")
        lines.append("Files matching these patterns are **blocked** at `__csf/` root:")
        lines.append("")
        lines.append("| Pattern | Reason | Move To |")
        lines.append("|---------|--------|---------|")
        for pattern in self.policy.get_csf_blocked_patterns():
            lines.append(
                f"| `{pattern['pattern']}` | {pattern['reason']} | `{pattern['suggestion']}` |"
            )
        lines.append("")

        # .claude structure
        lines.append("---")
        lines.append("")
        lines.append("## P:\\.claude\\ Structure")
        lines.append("")
        lines.append("```")
        lines.append("P:\\.claude\\")
        for subdir in self.policy.get_claude_allowed_subdirs():
            lines.append(f"├── {subdir['path']}/".ljust(25) + f"# {subdir['purpose']}")
        lines.append("```")
        lines.append("")

        # Validation command
        lines.append("---")
        lines.append("")
        lines.append("## Validation")
        lines.append("")
        lines.append("```bash")
        lines.append("# Validate workspace structure")
        lines.append("python P:\\.claude\\hooks\\path_validator.py --validate")
        lines.append("")
        lines.append("# Export updated documentation")
        lines.append(
            "python P:\\.claude\\hooks\\path_validator.py --export-markdown > docs/CANONICAL.md"
        )
        lines.append("```")

        return "\n".join(lines)

    def generate_json_export(self) -> str:
        """Export policy as formatted JSON."""
        return json.dumps(self.policy.get_full_config(), indent=2)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Directory policy validator and documentation generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate workspace structure
  python path_validator.py --validate
  python path_validator.py --validate P:\\__csf

  # Check if a specific path is allowed
  python path_validator.py --check-path "P:\\__csf\\test_foo.py"

  # Generate documentation from features.config
  python path_validator.py --export-markdown > CANONICAL.md
  python path_validator.py --export-json > policy.json

  # Generate LLM cleanup prompt for violations
  python path_validator.py --generate-cleanup-prompt
  python path_validator.py --generate-cleanup-prompt --max-files 20
  python path_validator.py --generate-cleanup-prompt > cleanup_task.md
        """,
    )

    parser.add_argument(
        "--validate",
        nargs="?",
        const="P:/",
        metavar="PATH",
        help="Validate directory structure (default: P:/)",
    )
    parser.add_argument(
        "--export-markdown", action="store_true", help="Export canonical structure as markdown"
    )
    parser.add_argument(
        "--export-json", action="store_true", help="Export policy configuration as JSON"
    )
    parser.add_argument(
        "--check-path", metavar="PATH", help="Check if a specific path would be allowed"
    )
    parser.add_argument("--config", metavar="FILE", help="Use custom policy config file")
    parser.add_argument("--quiet", action="store_true", help="Minimal output (exit code only)")
    parser.add_argument(
        "--generate-cleanup-prompt",
        nargs="?",
        const="P:/",
        metavar="PATH",
        help="Generate LLM prompt for reviewing and cleaning up violations",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=50,
        metavar="N",
        help="Maximum files to include in cleanup prompt (default: 50)",
    )

    args = parser.parse_args()

    # Load custom config if specified
    config_path = Path(args.config) if args.config else None

    # Handle --validate
    if args.validate is not None:
        policy = DirectoryPolicy(config_path)
        validator = DirectoryValidator(policy)
        results = validator.validate_workspace(args.validate)

        if args.quiet:
            sys.exit(0 if results["summary"]["compliant"] else 1)

        print("=== Directory Structure Validation ===")
        print(f"Policy Version: {results['policy_version']}")
        print(f"Root: {results['root_path']}")
        print()

        # Required directories
        print("Required Directories:")
        for req_dir in results["required_directories"]:
            status = "✅" if req_dir["exists"] else "❌"
            print(f"  {status} {req_dir['path']}/")
        print()

        # Violations
        if results["violations"]:
            print(f"❌ Violations ({len(results['violations'])}):")
            for v in results["violations"]:
                print(f"  • {v['type']}: {v['path']}")
                print(f"    {v['message']}")
                if "suggestion" in v:
                    print(f"    → Move to: {v['suggestion']}")
            print()

        # Warnings
        if results["warnings"]:
            print(f"⚠️ Warnings ({len(results['warnings'])}):")
            for w in results["warnings"]:
                print(f"  • {w['message']}")
            print()

        # Summary
        summary = results["summary"]
        print("Summary:")
        print(
            f"  Required dirs: {summary['required_dirs_present']}/{summary['required_dirs_total']}"
        )
        print(f"  Violations: {summary['violation_count']}")
        print(f"  Warnings: {summary['warning_count']}")
        print(f"  Status: {'✅ COMPLIANT' if summary['compliant'] else '❌ NON-COMPLIANT'}")

        sys.exit(0 if summary["compliant"] else 1)

    # Handle --export-markdown
    if args.export_markdown:
        policy = DirectoryPolicy(config_path)
        generator = DocumentationGenerator(policy)
        print(generator.generate_markdown())
        sys.exit(0)

    # Handle --export-json
    if args.export_json:
        policy = DirectoryPolicy(config_path)
        generator = DocumentationGenerator(policy)
        print(generator.generate_json_export())
        sys.exit(0)

    # Handle --check-path
    if args.check_path:
        policy = DirectoryPolicy(config_path)
        validator = PathValidator(config_path)
        result = validator.validate_file_operation(args.check_path)

        if args.quiet:
            sys.exit(0 if result["is_safe"] else 1)

        status = "✅ ALLOWED" if result["is_safe"] else "❌ BLOCKED"
        print(f"{status}: {args.check_path}")
        print(f"  Reason: {result['violation_type']}")
        if "suggestion" in result:
            print(f"  Suggestion: {result['suggestion']}")

        sys.exit(0 if result["is_safe"] else 1)

    # Handle --generate-cleanup-prompt
    if args.generate_cleanup_prompt is not None:
        policy = DirectoryPolicy(config_path)
        generator = CleanupPromptGenerator(policy)
        prompt = generator.generate_cleanup_prompt(
            root_path=args.generate_cleanup_prompt, max_files=args.max_files
        )
        print(prompt)
        sys.exit(0)

    # No arguments - show help
    parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
