#!/usr/bin/env python3
"""
Unified Path Classifier for PreToolUse Hooks
============================================

Consolidates path classification logic to avoid redundant pattern matching
and file existence checks across multiple hooks.

Benefits:
- Single pass path classification per operation
- Cached file existence checks
- Shared exemption pattern results
- Reduced subprocess overhead

Usage:
    from path_classifier import classify_path, get_cached_classification

    # First call: performs full classification
    classification = classify_path(file_path, data)

    # Subsequent calls: returns cached result from data dict
    cached = get_cached_classification(file_path, data)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

# Pre-compiled exemption patterns (shared across hooks)
# These patterns indicate files that don't require planning or special treatment
EXEMPTION_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in [
    r"__init__\.py$",           # Package markers
    r"conftest\.py$",           # Pytest fixtures
    r".*\.md$",                 # Documentation
    r".*\.txt$",                # Text files
    r".*\.json$",               # Config files
    r".*\.yaml$",               # Config files
    r".*\.yml$",                # Config files
    r".*\.toml$",               # Config files
    r".*\.ini$",                # Config files
    r"\.env\..*$",              # Environment example files (.env.example, .env.local, etc.)
    r"tests?/.*",               # Test directories
    r".*/test_.*\.py$",         # Test files
    r".*/.*_test\.py$",         # Test files
    r".*/lib/.*",               # Library files (implementation details)
    r".*/.*/.*gate\.py$",       # Gate files (validators)
    r".*/.*/.*validator\.py$",  # Validator files
    r".*/.*/.*utils?\.py$",     # Utility/helper files
    r".*/__lib__/.*",           # Private library modules
    r".*/templates/.*",         # Template files
])

# Hook files (NEVER exempt - require planning for governance)
HOOK_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in [
    r"\.claude/hooks/.*",       # All hook files
])

# .claude internal paths (skill libraries, internal implementation)
# NOTE: Hook files are NOT exempt - they require planning for governance
CLAUDE_INTERNAL_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in [
    r"\.claude/skills/[^/]+/lib/.*",        # Skill internal libraries
    r"\.claude/skills/[^/]+/templates/.*",  # Skill templates
    r"\.claude/skills/[^/]+/validators/.*", # Skill validators
    r"\.claude/skills/[^/]+/gates/.*",      # Skill gates
    r"\.claude/skills/[^/]+/utils/.*",      # Skill utilities
    # CRITICAL: .claude/hooks/ is NOT exempt - hooks require planning
])

# Security-sensitive patterns (require extra caution)
SECURITY_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in [
    r"\.env",                   # Environment files
    r"secrets?",                # Secret files
    r"credentials?",            # Credential files
    r"password",                # Password files
    r"\.key$",                  # Key files
    r"\.pem$",                  # Certificate files
])


def classify_path(file_path: str, data: dict[str, Any]) -> dict[str, Any]:
    """
    Classify a file path once, cache result in data dict for reuse.

    Args:
        file_path: The file path to classify
        data: Hook data dict (used for caching between hooks)

    Returns:
        Classification dict with keys:
        - path: original file path
        - exists: bool (file exists on disk)
        - is_test: bool (test file detection)
        - is_exempt: bool (exempt from plan requirement)
        - is_claude_internal: bool (.claude internal file)
        - is_security_sensitive: bool (requires extra caution)
        - is_new: bool (file doesn't exist or is empty)
        - extension: str (file extension)
        - directory: str (containing directory)
    """
    # Check cache first
    cache_key = "_path_classification_cache"
    if cache_key in data:
        cache = data[cache_key]
        if file_path in cache:
            return cache[file_path]

    # Initialize cache if needed
    if cache_key not in data:
        data[cache_key] = {}

    # Perform classification
    path = Path(file_path)

    # File existence check (expensive - do once)
    exists = path.exists()
    is_new = not exists or (exists and path.stat().st_size == 0)

    # Extension
    extension = path.suffix.lower()

    # Directory
    directory = str(path.parent)

    # Test file detection (use existing module if available)
    is_test = False
    try:
        from __csf.__lib.test_detection import is_test_file_operation
        is_test = is_test_file_operation(file_path)
    except ImportError:
        # Fallback: simple pattern check
        test_patterns = [
            r"^tests?/", r"^test/", r".*/test_.*\.py$", r".*_test\.py$"
        ]
        normalized = file_path.replace("\\", "/")
        is_test = any(re.search(p, normalized, re.IGNORECASE) for p in test_patterns)

    # Hook file check (CRITICAL: hook files NEVER exempt - require planning for governance)
    is_hook_file = any(p.search(file_path) for p in HOOK_PATTERNS)

    # Exemption check (config files, docs, tests, etc.) - but NEVER for hook files
    is_exempt = not is_hook_file and any(p.search(file_path) for p in EXEMPTION_PATTERNS)

    # .claude internal check
    is_claude_internal = any(p.search(file_path) for p in CLAUDE_INTERNAL_PATTERNS)

    # Security sensitive check
    is_security_sensitive = any(p.search(file_path) for p in SECURITY_PATTERNS)

    classification = {
        "path": file_path,
        "exists": exists,
        "is_test": is_test,
        "is_exempt": is_exempt,
        "is_hook_file": is_hook_file,
        "is_claude_internal": is_claude_internal,
        "is_security_sensitive": is_security_sensitive,
        "is_new": is_new,
        "extension": extension,
        "directory": directory,
    }

    # Cache the result
    data[cache_key][file_path] = classification

    return classification


def get_cached_classification(file_path: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """
    Get cached path classification without recomputing.

    Args:
        file_path: The file path to look up
        data: Hook data dict containing cache

    Returns:
        Classification dict if cached, None otherwise
    """
    cache_key = "_path_classification_cache"
    cache = data.get(cache_key, {})
    return cache.get(file_path)


def clear_cache(data: dict[str, Any]) -> None:
    """
    Clear the path classification cache.

    Use this between operations or when cache becomes stale.
    """
    cache_key = "_path_classification_cache"
    if cache_key in data:
        del data[cache_key]


# Convenience functions for specific classification aspects

def is_test_file(file_path: str, data: dict[str, Any]) -> bool:
    """Check if file is a test file (cached)."""
    classification = classify_path(file_path, data)
    return classification["is_test"]


def is_exempt_path(file_path: str, data: dict[str, Any]) -> bool:
    """Check if file is exempt from planning requirements (cached)."""
    classification = classify_path(file_path, data)
    return classification["is_exempt"]


def file_exists(file_path: str, data: dict[str, Any]) -> bool:
    """Check if file exists (cached)."""
    classification = classify_path(file_path, data)
    return classification["exists"]


def is_new_file(file_path: str, data: dict[str, Any]) -> bool:
    """Check if file is new (doesn't exist or is empty) (cached)."""
    classification = classify_path(file_path, data)
    return classification["is_new"]


def is_claude_internal(file_path: str, data: dict[str, Any]) -> bool:
    """Check if file is .claude internal (cached)."""
    classification = classify_path(file_path, data)
    return classification["is_claude_internal"]


def is_security_sensitive(file_path: str, data: dict[str, Any]) -> bool:
    """Check if file is security-sensitive (cached)."""
    classification = classify_path(file_path, data)
    return classification["is_security_sensitive"]


def is_hook_file(file_path: str, data: dict[str, Any] | None = None) -> bool:
    """
    Check if path is a hook file (requires planning for governance).

    Hook files are governance infrastructure and should always require planning.

    Args:
        file_path: The file path to check
        data: Optional hook data dict for cache lookup

    Returns:
        True if the file is a hook file, False otherwise
    """
    # Use cached value if available
    if data:
        cached = get_cached_classification(file_path, data)
        if cached:
            return cached.get("is_hook_file", False)

    # Fallback to pattern check
    return bool(re.search(r"\.claude/hooks/.*", file_path, re.IGNORECASE))


def requires_planning(file_path: str, data: dict[str, Any]) -> bool:
    """
    Check if file operation requires planning.

    Returns True if:
    - File is NOT exempt (config, docs, tests)
    - File is NOT a .claude internal file (skill libs, templates)
    - File is NOT a test file

    Hook files ALWAYS require planning (governance).
    """
    # Hook files always require planning (use cache)
    if is_hook_file(file_path, data):
        return True

    # Check cache
    classification = classify_path(file_path, data)

    # If exempt or internal, no planning needed
    if classification["is_exempt"] or classification["is_claude_internal"]:
        return False

    # Test files don't require planning
    if classification["is_test"]:
        return False

    # Everything else requires planning
    return True
